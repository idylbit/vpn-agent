#!/bin/bash

set -euo pipefail

SSH_SERVER="ubuntuvm"
APP_DIR="/home/japheth/.vpn-agent"

sed "s|\${VPN_AGENT_DIR}|$APP_DIR|g" wg-agent.service.template.service > wg-agent.service

echo "Initializing"
ssh "$SSH_SERVER" "mkdir -p $APP_DIR"
rsync -avz --no-perms --no-owner --no-group \
  . \
  --exclude 'wg-agent.template.service' \
  --exclude 'deploy.sh' \
  "$SSH_SERVER:$APP_DIR/"

ssh "$SSH_SERVER" <<EOF
set -euo pipefail

echo "Verifying Python dependencies..."
sudo apt-get install -y python3-flask wireguard

cd "$APP_DIR"

echo "Updating systemd service file"
sudo mv wg-agent.service /etc/systemd/system/wg-agent.service

echo "Reloading deamon"
sudo systemctl daemon-reload

echo "Starting agent"
sudo systemctl enable --now wg-agent

echo "Status"
sudo systemctl status wg-agent

EOF

echo "Done."
