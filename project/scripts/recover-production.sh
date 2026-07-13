#!/usr/bin/env bash
# Recover Nexus on the production VM after reboot, OOM, or hung Caddy.
# Run ON THE SERVER from /opt/nexus/project:
#   bash scripts/recover-production.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT/deploy/docker/docker-compose.yml"
cd "$ROOT"

echo "==> Nexus production recovery"
echo "    path: $ROOT"

# 2GB swap helps 1GB VMs survive chat/RAG memory spikes
if ! swapon --show 2>/dev/null | grep -q .; then
  if [[ ! -f /swapfile ]]; then
    echo "==> Creating 2GB swapfile (one-time)..."
    sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
  fi
  echo "==> Enabling swap..."
  sudo swapon /swapfile 2>/dev/null || echo "WARN: could not enable swap"
fi

# 1GB VMs: one Gunicorn worker (also set in config/environment/.env)
export GUNICORN_WORKERS="${GUNICORN_WORKERS:-1}"

# System Caddy (systemd) conflicts with Docker Caddy on ports 80/443 — disable it.
if systemctl is-active --quiet caddy 2>/dev/null; then
  echo "==> Stopping system Caddy (conflicts with Docker Caddy)..."
  sudo systemctl stop caddy
fi
if systemctl is-enabled --quiet caddy 2>/dev/null; then
  echo "==> Disabling system Caddy on boot..."
  sudo systemctl disable caddy
fi

if sudo ss -tlnp 2>/dev/null | grep -q ':80 '; then
  if ! docker port docker-caddy-1 80/tcp >/dev/null 2>&1; then
    echo "ERROR: Port 80 in use but not by Docker Caddy. Run:"
    echo "  sudo ss -tlnp | grep ':80 '"
    exit 1
  fi
fi

echo "==> Pulling latest image (no build on VM)..."
git pull --ff-only || echo "WARN: git pull failed — continuing with local tree"
docker compose -f "$COMPOSE_FILE" pull nexus

echo "==> Starting stack..."
docker compose -f "$COMPOSE_FILE" up -d --force-recreate

# If Caddy started while port 80 was busy, it may have no host port mapping.
if ! docker port docker-caddy-1 80/tcp >/dev/null 2>&1; then
  echo "==> Recreating Caddy (fix missing port 80/443 mapping)..."
  docker compose -f "$COMPOSE_FILE" rm -sf caddy
  docker compose -f "$COMPOSE_FILE" up -d caddy
fi

echo "==> Waiting for health..."
for i in $(seq 1 30); do
  if docker exec docker-nexus-1 python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')" \
    >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo ""
echo "==> Nexus container health:"
docker exec docker-nexus-1 python -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').read().decode())" \
  || { echo "Nexus health check failed"; exit 1; }

echo ""
echo "==> Caddy ports:"
docker port docker-caddy-1 || true

echo ""
echo "==> Public edge (port 80 on VM):"
curl -sf http://127.0.0.1/api/v1/health | head -c 200 || {
  echo "WARN: curl http://127.0.0.1/api/v1/health failed"
  exit 1
}

echo ""
echo "OK — recovery complete. Test: https://yournexus.duckdns.org/landing"
