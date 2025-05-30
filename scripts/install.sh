#!/usr/bin/env bash
# Triggered – one-shot installer & launcher
#
# USAGE
#   ./scripts/install.sh           # install with redis
#   NO_REDIS=1 ./scripts/install.sh  # use in-process broker (memory://)
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
cd "$PROJECT_ROOT"

# 1. Ensure Poetry -----------------------------------------------------------
if ! command -v poetry >/dev/null 2>&1; then
  echo "[+] Installing Poetry…"
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Download local LLM model ------------------------------------------------
# 2. Local LLM download is handled automatically by llama_cpp via
#    Llama.from_pretrained (see triggered/models). Keeping this section empty
#    to avoid unnecessary manual downloads; override via environment if you
#    still want to pre-download:

echo "[=] Model will be auto-downloaded on first use via llama_cpp"

# 3. Install Python dependencies -------------------------------------------
echo "[+] Installing Python dependencies via Poetry…"
poetry install --extras "local-model"

# 4. (Optional) Install & start Redis ---------------------------------------
if [ "${NO_REDIS:-0}" != "1" ]; then
  if ! command -v redis-server >/dev/null 2>&1; then
    echo "[+] Installing Redis…"
    if command -v brew >/dev/null 2>&1; then
      brew install redis
    elif command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update && sudo apt-get install -y redis-server
    else
      echo "[!] Package manager not recognised. Please install Redis manually or rerun with NO_REDIS=1."
      exit 1
    fi
  fi
  echo "[+] Starting Redis in background…"
  redis-server --daemonize yes
  export BROKER_URL="redis://localhost:6379/0"
else
  echo "[=] Using in-process memory broker (NO_REDIS=1)"
  export BROKER_URL="memory://"
fi

# 5. Launch Triggered services ---------------------------------------------
echo "[+] Launching Triggered API server (http://localhost:8000)…"
poetry run triggered server &
SERVER_PID=$!

echo "[+] Launching Celery worker…"
poetry run celery -A triggered.queue worker --loglevel=info &
WORKER_PID=$!

# Trap Ctrl+C / SIGTERM and kill children
trap 'echo "[+] Shutting down Triggered…"; kill $SERVER_PID $WORKER_PID; exit 0' INT TERM

cat <<EOF

[✓] Triggered is up & running!
    API docs:    http://localhost:8000/docs
    Server PID:  $SERVER_PID
    Worker PID:  $WORKER_PID

Press Ctrl+C in this window to stop both services.

EOF

# Wait indefinitely so the script remains in foreground
wait 