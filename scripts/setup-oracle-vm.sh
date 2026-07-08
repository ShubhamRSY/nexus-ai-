#!/usr/bin/env bash
# One-shot Nexus setup for Oracle Linux 9 (E2.1.Micro).
# Paste this entire script into Oracle's browser Instance Console terminal.
#
# Before running:
#   1. DuckDNS: point yourname.duckdns.org → your VM public IP
#   2. Replace DOMAIN below with your DuckDNS name
#
# Usage (as opc on the VM):
#   curl -fsSL https://raw.githubusercontent.com/ShubhamRSY/voice-agents/main/scripts/setup-oracle-vm.sh | sudo bash -s -- yourname.duckdns.org
# Or paste and run locally:
#   sudo bash setup-oracle-vm.sh yourname.duckdns.org

set -euo pipefail

DOMAIN="${1:-}"
if [[ -z "$DOMAIN" ]]; then
  echo "Usage: sudo bash setup-oracle-vm.sh yourname.duckdns.org"
  exit 1
fi

DOMAIN="${DOMAIN#https://}"
DOMAIN="${DOMAIN#http://}"
DOMAIN="${DOMAIN%%/*}"

echo "=== Nexus setup for ${DOMAIN} ==="

# ── Swap (critical on 1GB RAM) ───────────────────────────────
if ! swapon --show | grep -q /swapfile; then
  echo "→ Adding 2GB swap..."
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# ── Firewall ───────────────────────────────────────────────────
echo "→ Opening firewall ports..."
if command -v firewall-cmd >/dev/null; then
  firewall-cmd --permanent --add-service=ssh
  firewall-cmd --permanent --add-port=80/tcp
  firewall-cmd --permanent --add-port=443/tcp
  firewall-cmd --reload
fi

# ── Docker ─────────────────────────────────────────────────────
if ! command -v docker >/dev/null; then
  echo "→ Installing Docker..."
  dnf install -y dnf-plugins-core git curl openssl
  dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
fi

# Run remaining steps as opc
SETUP_USER="${SUDO_USER:-opc}"
echo "→ Deploying as user: ${SETUP_USER}"

sudo -u "$SETUP_USER" bash <<DEPLOY
set -euo pipefail
cd ~

if [[ ! -d voice-agents ]]; then
  echo "→ Cloning repository..."
  git clone https://github.com/ShubhamRSY/voice-agents.git
fi

cd voice-agents
export DOMAIN="${DOMAIN}"
export OPENAI_API_KEY=""
export NONINTERACTIVE=1

bash scripts/deploy-public.sh

DEPLOY

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Setup finished — wait 2 min for HTTPS certificate       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Website: https://${DOMAIN}"
echo "  Health:  https://${DOMAIN}/api/v1/health"
echo ""
echo "  Register admin:"
echo "  curl -X POST https://${DOMAIN}/api/v1/auth/register \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"you@example.com\",\"password\":\"Pass123!\",\"name\":\"Admin\",\"tenant_name\":\"My Co\"}'"
echo ""
