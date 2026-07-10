#!/bin/bash
# Automated backup script for Nexus production data.
# Usage:
#   ./scripts/backup.sh                    # Full backup to local ./backups/
#   ./scripts/backup.sh --s3-bucket my-bucket  # Upload to S3 as well
#   ./scripts/backup.sh --db-only              # Database only
#   ./scripts/backup.sh --chroma-only          # ChromaDB only
#
# Typically run via cron or the docker-compose backup service.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
S3_BUCKET=""
DB_ONLY=false
CHROMA_ONLY=false
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --s3-bucket) S3_BUCKET="$2"; shift 2 ;;
    --db-only) DB_ONLY=true; shift ;;
    --chroma-only) CHROMA_ONLY=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

mkdir -p "$BACKUP_DIR"

backup_postgres() {
  local dump_path="$BACKUP_DIR/nexus-pg-$TIMESTAMP.sql.gz"
  echo "==> Backing up PostgreSQL to $dump_path"

  if command -v pg_dump &>/dev/null && [ -n "${DATABASE_URL:-}" ]; then
    pg_dump "$DATABASE_URL" | gzip > "$dump_path"
  else
    echo "ERROR: pg_dump unavailable or DATABASE_URL not set. Skipping database backup."
    return 1
  fi

  echo "    => $(du -h "$dump_path" | cut -f1)"
}

backup_sqlite() {
  local sqlite_path="$ROOT/data/nexus.db"
  local out_path="$BACKUP_DIR/nexus-sqlite-$TIMESTAMP.db"
  if [ ! -f "$sqlite_path" ]; then
    echo "WARNING: SQLite DB not found at $sqlite_path. Skipping."
    return 1
  fi
  echo "==> Backing up SQLite from $sqlite_path to $out_path"
  cp -f "$sqlite_path" "$out_path"
  chmod 600 "$out_path" || true
  echo "    => $(du -h "$out_path" | cut -f1)"
}

backup_chroma() {
  local chroma_dir="${CHROMA_PERSIST_DIR:-$ROOT/data/chroma}"
  local archive_path="$BACKUP_DIR/nexus-chroma-$TIMESTAMP.tar.gz"

  if [ ! -d "$chroma_dir" ]; then
    echo "WARNING: ChromaDB directory not found at $chroma_dir. Skipping."
    return 1
  fi

  echo "==> Backing up ChromaDB from $chroma_dir to $archive_path"
  tar czf "$archive_path" -C "$(dirname "$chroma_dir")" "$(basename "$chroma_dir")"
  echo "    => $(du -h "$archive_path" | cut -f1)"
}

backup_config() {
  local archive_path="$BACKUP_DIR/nexus-config-$TIMESTAMP.tar.gz"
  echo "==> Backing up configuration to $archive_path"
  tar czf "$archive_path" \
    -C "$ROOT" \
    config/environment/.env \
    config/agents.yaml \
    2>/dev/null || true
  echo "    => $(du -h "$archive_path" | cut -f1)"
}

upload_to_s3() {
  if [ -z "$S3_BUCKET" ]; then
    return
  fi
  echo "==> Uploading to s3://$S3_BUCKET/nexus-backups/"
  aws s3 sync "$BACKUP_DIR" "s3://$S3_BUCKET/nexus-backups/" --exclude "*" \
    --include "nexus-*$TIMESTAMP*"
  echo "    => Upload complete"
}

cleanup_old() {
  echo "==> Cleaning up backups older than $BACKUP_RETENTION_DAYS days"
  find "$BACKUP_DIR" -name "nexus-*" -type f -mtime "+$BACKUP_RETENTION_DAYS" -delete
}

# ── Main ──────────────────────────────────────────────────────
echo "=========================================="
echo "  Nexus Backup — $TIMESTAMP"
echo "=========================================="

if [ "$DB_ONLY" = false ] && [ "$CHROMA_ONLY" = false ]; then
  # Backup whichever DB is in use.
  if [ -n "${DATABASE_URL:-}" ]; then
    backup_postgres || true
  else
    backup_sqlite || true
  fi
  backup_chroma || true
  backup_config
elif [ "$DB_ONLY" = true ]; then
  if [ -n "${DATABASE_URL:-}" ]; then
    backup_postgres || true
  else
    backup_sqlite || true
  fi
elif [ "$CHROMA_ONLY" = true ]; then
  backup_chroma || true
fi

upload_to_s3
cleanup_old

echo ""
echo "✅ Backup complete — $BACKUP_DIR"
echo "=========================================="
