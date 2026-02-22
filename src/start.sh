#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

print_banner() {
  cat <<'BANNER'
   ____        __      ______
  / __/____ _ / /_ ___/ ____/___   __ _  ____ ___   _____
 _\ \ / __ `// __// _  /   / __ \ /  ' \/ __ `__ \ / ___/
/___// /_/ // /_ /  __/___/ /_/ // /|  / / / / / /(__  )
     \__,_/ \__/ \___/\____/\____//_/ |_/_/ /_/ /_//____/
BANNER
}

log_info() {
  printf '[INFO] %s\n' "$1"
}

log_ok() {
  printf '[ OK ] %s\n' "$1"
}

log_warn() {
  printf '[WARN] %s\n' "$1"
}

install_requirements_file() {
  local req_file="$1"
  if [[ -f "$req_file" ]]; then
    log_info "Installing dependencies from $req_file"
    pip install -r "$req_file"
    log_ok "Installed $req_file"
  else
    log_warn "Skipped missing $req_file"
  fi
}

ensure_keepalive_script() {
  local keepalive_path="$SCRIPT_DIR/keepalive.sh"
  if [[ -f "$keepalive_path" ]]; then
    chmod +x "$keepalive_path"
    log_ok "keepalive.sh already exists"
    return
  fi

  cat > "$keepalive_path" <<'KEEPALIVE'
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
KEEPALIVE

  chmod +x "$keepalive_path"
  log_ok "Generated keepalive.sh"
}

print_banner
log_info "Project root: $ROOT_DIR"
ensure_keepalive_script

if [[ ! -d ".venv" ]]; then
  log_info "Creating virtual environment (.venv)"
  python3 -m venv .venv
  log_ok "Virtual environment created"
else
  log_ok "Virtual environment already exists"
fi

source .venv/bin/activate
log_ok "Virtual environment activated"

log_info "Upgrading pip/setuptools/wheel"
pip install --upgrade pip setuptools wheel
log_ok "Base tooling upgraded"

install_requirements_file "requirements.txt"
install_requirements_file "requirements-ai.txt"

if [[ -f ".env" ]]; then
  log_info "Loading environment from .env"
  set -a
  source .env
  set +a
  log_ok "Environment loaded"
else
  log_warn ".env not found (continuing)"
fi

log_ok "Fully installed. Starting API server..."
exec uvicorn main:app --host 127.0.0.1 --port 8000 --reload
