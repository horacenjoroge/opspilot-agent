#!/usr/bin/env bash
# OpsPilot — ECS deploy script
# Run as root (or with sudo) on a fresh Ubuntu 22.04 ECS instance.
# Usage: bash deploy.sh

set -euo pipefail

REPO_URL="https://github.com/horacenjoroge/opspilot-agent.git"
APP_DIR="/opt/opspilot"

if command -v docker &> /dev/null; then
  echo "==> Docker already installed, skipping."
else
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
fi

echo "==> Cloning repo..."
if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR" && git pull origin main
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

echo "==> Waiting for backend to be ready..."
for i in $(seq 1 20); do
  if docker compose -f deployment/docker-compose.prod.yml exec -T backend curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "    Backend is up."
    break
  fi
  sleep 2
done

echo "==> Seeding admin user..."
docker compose -f deployment/docker-compose.prod.yml exec -T backend \
  python -m app.scripts.seed_admin \
  --email admin@opspilot.local \
  --password admin1234 \
  --name "OpsPilot Admin"

PUBLIC_IP=$(curl -sf ifconfig.me || echo "<your-ECS-IP>")
SITE_DOMAIN="${SITE_DOMAIN:-${PUBLIC_IP}.sslip.io}"
echo ""
echo "==> Done. OpsPilot is running."
echo "    Health check: curl http://localhost/health"
echo "    Dashboard:    https://${SITE_DOMAIN}/"
echo "    Login:        admin@opspilot.local / admin1234"
echo ""
echo "    NOTE: HTTPS requires TCP 443 open in the ECS security group."
