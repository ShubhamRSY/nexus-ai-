#!/usr/bin/env bash
# Set up daily backups for Nexus (SQLite + Chroma) via systemd timer.
#
# Usage (on VM):
#   bash scripts/setup-backup-timer.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

sudo tee /etc/systemd/system/nexus-backup.service >/dev/null <<EOF
[Unit]
Description=Nexus backup (SQLite + Chroma)

[Service]
Type=oneshot
User=${SUDO_USER:-opc}
WorkingDirectory=$ROOT
Environment=BACKUP_DIR=$ROOT/backups
Environment=BACKUP_RETENTION_DAYS=14
ExecStart=$ROOT/scripts/backup.sh
EOF

sudo tee /etc/systemd/system/nexus-backup.timer >/dev/null <<'EOF'
[Unit]
Description=Run Nexus backup daily

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=1800

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now nexus-backup.timer
sudo systemctl status nexus-backup.timer --no-pager

echo ""
echo "Backup timer enabled."
echo "Check last run with: sudo journalctl -u nexus-backup.service -n 80 --no-pager"

