#!/usr/bin/env bash
# OpsPilot — ECS deploy script
# Run as root (or with sudo) on a fresh Ubuntu 22.04 ECS instance.
# Usage: bash deploy.sh

set -euo pipefail

REPO_URL="https://github.com/horacenjoroge/opspilot-agent.git"
APP_DIR="/opt/opspilot"

echo "==> Installing Docker..."
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
systemctl enable docker
systemctl start docker

echo "==> Cloning repo..."
if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR" && git pull
else
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "==> Checking .env..."
if [ ! -f "$APP_DIR/.env" ]; then
  echo ""
  echo "ERROR: No .env found at $APP_DIR/.env"
  echo "Copy your .env file to the server first:"
  echo "  scp .env root@<ECS_IP>:/opt/opspilot/.env"
  echo "Then re-run this script."
  exit 1
fi

echo "==> Building and starting containers..."
cd "$APP_DIR"
docker compose -f deployment/docker-compose.prod.yml up --build -d

echo ""
echo "==> Done. OpsPilot is running."
echo "    Health check: curl http://localhost/health"
echo "    Dashboard:    http://$(curl -s ifconfig.me)/"
