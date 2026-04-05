#!/bin/bash

set -euo pipefail

SSH_SERVER=$1
APP_DIR=".vpn-agent"

echo "Initializing"
ssh "$SSH_SERVER" "mkdir -p $APP_DIR"
rsync -avz --no-perms --no-owner --no-group \
  api \
  interface \
  .env \
  __init__.py \
  init.py \
  main.py \
  requirements.txt \
  wg-agent.template.service \
  "$SSH_SERVER:$APP_DIR/"

ssh -tt "$SSH_SERVER" <<EOF
set -euo pipefail

REMOTE_PATH="\$HOME/$APP_DIR"

cd "\$REMOTE_PATH"

echo "Updating systemd service file"
sed "s|\\\${VPN_AGENT_DIR}|\$REMOTE_PATH|g" wg-agent.template.service > wg-agent.service
sudo mv wg-agent.service /etc/systemd/system/wg-agent.service

echo "Reloading deamon"
sudo systemctl daemon-reload

echo "Starting agent"
sudo systemctl enable --now wg-agent

echo "Status"
sudo systemctl status wg-agent

EOF

echo "Done."
