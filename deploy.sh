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

ssh -tt "$SSH_SERVER" <<EOF
set -euo pipefail

cd "\$HOME/$APP_DIR"

sudo python3 init.py

systemctl status vpnagent

EOF

echo "Done."
