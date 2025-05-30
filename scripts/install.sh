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
MODEL_DIR="models"
MODEL_FILE="phi-4-mini.gguf"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"
MODEL_URL="https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2-mini.gguf"

mkdir -p "$MODEL_DIR"
if [ ! -f "$MODEL_PATH" ]; then
  echo "[+] Downloading local model to $MODEL_PATH… (≈400 MB)"
  curl -L "$MODEL_URL" -o "$MODEL_PATH"
else
  echo "[=] Model already present: $MODEL_PATH"
fi

# 3. Install Python dependencies -------------------------------------------
echo "[+] Installing Python dependencies via Poetry…"
poetry install --with local-model

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

cat <<EOF

[✓] Triggered is up & running!
    API docs:    http://localhost:8000/docs
    Server PID:  $SERVER_PID
    Worker PID:  $WORKER_PID

To stop services:
    kill $SERVER_PID $WORKER_PID
EOF 