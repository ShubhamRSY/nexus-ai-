#!/usr/bin/env bash
# SELinux-safe systemd setup for Nexus on Oracle Linux 9.
#
# Usage on VM:
#   bash scripts/setup-nexus-systemd-oraclelinux.sh
#
# Notes:
# - Runs Nexus as the current user (opc by default)
# - Binds only to 127.0.0.1:8001 (fronted by Caddy)

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

APP_USER="${SUDO_USER:-opc}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo:"
  echo "  sudo bash scripts/setup-nexus-systemd-oraclelinux.sh"
  exit 1
fi

if [[ ! -x "$ROOT/.venv/bin/python3.12" ]]; then
  echo "Missing venv at $ROOT/.venv. Create it first on the VM."
  exit 1
fi

# Ensure SELinux tooling exists (best-effort)
dnf install -y policycoreutils-python-utils >/dev/null 2>&1 || true

# Allow systemd to execute venv binaries under /home
if command -v chcon >/dev/null 2>&1; then
  chcon -R -t bin_t "$ROOT/.venv/bin" || true
fi

tee /etc/systemd/system/nexus.service >/dev/null <<EOF
[Unit]
Description=Nexus AI Ops
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$ROOT
Environment=PATH=$ROOT/.venv/bin:/usr/bin
ExecStart=$ROOT/.venv/bin/python3.12 -m uvicorn src.main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now nexus.service
systemctl status nexus.service --no-pager

echo ""
echo "Nexus systemd service enabled."
echo "Logs: sudo journalctl -u nexus -n 80 --no-pager"

