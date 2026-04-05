#!/bin/bash

set -euo pipefail

SSH_SERVER=$1
APP_DIR=".vpnagent"

echo "Initializing"
ssh "$SSH_SERVER" "mkdir -p $APP_DIR"
rsync -avz --no-perms --no-owner --no-group \
  api \
  interface \
  .env \
  __init__.py \
  setup.py \
  main.py \
  requirements.txt \
  "$SSH_SERVER:$APP_DIR/"

ssh -t "$SSH_SERVER" "sudo -v"

ssh "$SSH_SERVER" <<EOF
set -euo pipefail
sudo apt update && sudo apt install -y python3.13-venv
cd "\$HOME/$APP_DIR"
sudo python3 setup.py
systemctl status vpnagent

EOF

echo "Done."
