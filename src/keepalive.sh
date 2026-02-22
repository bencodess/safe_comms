#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

while true; do
  ./start.sh
  code=$?
  echo "[KEEPALIVE] start.sh exited with code $code"
  echo "[KEEPALIVE] restarting in 3 seconds..."
  sleep 3
done
