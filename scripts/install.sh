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

# 3. Install Python dependencies -------------------------------------------
echo "[+] Installing Python dependencies via Poetry…"
poetry install --extras "local-model"

# 3b. Install shell completion -------------------------------------------
echo "[+] Installing shell completion…"

# Detect shell
CURRENT_SHELL=$(basename "$SHELL")
case "$CURRENT_SHELL" in
    "zsh")
        echo "[+] Installing Zsh completion…"
        mkdir -p ~/.zsh/completion
        poetry run triggered --show-completion zsh > ~/.zsh/completion/_triggered
        
        # Add completion to zshrc if not already present
        if ! grep -q "~/.zsh/completion" ~/.zshrc; then
            echo '\nfpath=(~/.zsh/completion $fpath)\nautoload -U compinit\ncompinit' >> ~/.zshrc
            echo "[+] Added completion configuration to ~/.zshrc"
        fi
        ;;
    "bash")
        echo "[+] Installing Bash completion…"
        mkdir -p ~/.local/share/bash-completion/completions
        poetry run triggered --show-completion bash > ~/.local/share/bash-completion/completions/triggered
        
        # Add completion to bashrc if not already present
        if ! grep -q "bash-completion" ~/.bashrc; then
            echo '\n# Enable bash completion\nif [ -f /usr/share/bash-completion/bash_completion ]; then\n    . /usr/share/bash-completion/bash_completion\nelif [ -f /etc/bash_completion ]; then\n    . /etc/bash_completion\nfi' >> ~/.bashrc
            echo "[+] Added completion configuration to ~/.bashrc"
        fi
        ;;
    "fish")
        echo "[+] Installing Fish completion…"
        mkdir -p ~/.config/fish/completions
        poetry run triggered --show-completion fish > ~/.config/fish/completions/triggered.fish
        echo "[+] Added completion to ~/.config/fish/completions/triggered.fish"
        ;;
    *)
        echo "[!] Shell completion not supported for $CURRENT_SHELL"
        echo "[!] Supported shells: zsh, bash, fish"
        ;;
esac

if [ "$CURRENT_SHELL" = "zsh" ] || [ "$CURRENT_SHELL" = "bash" ]; then
    echo "[!] Please run 'source ~/.${CURRENT_SHELL}rc' or restart your terminal to enable completion"
fi

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
  export TRIGGERED_BROKER_URL="redis://localhost:6379/0"
else
  echo "[=] Using in-process memory broker (NO_REDIS=1)"
  export TRIGGERED_BROKER_URL="memory://"
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

echo "[=] Model will be auto-downloaded on first use via llama_cpp"

# 2b. Ensure Ollama ---------------------------------------------------------
if ! command -v ollama >/dev/null 2>&1; then
  echo "[+] Installing Ollama…"
  if command -v brew >/dev/null 2>&1; then
    brew install ollama
  elif command -v apt-get >/dev/null 2>&1; then
    curl -fsSL https://ollama.com/install.sh | sh
  else
    echo "[!] Cannot install Ollama automatically. Please install it manually."
  fi
fi

# Start Ollama daemon if not running
if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "[+] Starting Ollama daemon…"
  nohup ollama serve > /dev/null 2>&1 &
  sleep 3
fi

OLLAMA_MODEL=${OLLAMA_MODEL:-"llama3.1"}
echo "[+] Pulling Ollama model $OLLAMA_MODEL…"
ollama pull "$OLLAMA_MODEL" || true 