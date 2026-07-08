#!/usr/bin/env bash
# Install Docker Engine + Compose plugin on Ubuntu 22.04/24.04 (Oracle Cloud VM).
# Run on your VM as a regular user with sudo:
#   curl -fsSL https://raw.githubusercontent.com/ShubhamRSY/voice-agents/main/scripts/install-docker.sh | bash

set -euo pipefail

if [[ $EUID -eq 0 ]]; then
  echo "Run as your normal user (ubuntu), not root. Script uses sudo where needed."
  exit 1
fi

echo "→ Installing Docker..."
sudo apt-get update -qq
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -qq
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker "$USER"

echo ""
echo "✓ Docker installed."
echo "  Log out and SSH back in, then run: docker compose version"
echo ""
