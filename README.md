# Triggered

Triggered is a runtime engine similar to cron, but designed for the AI era. It executes user-defined Actions when their associated Triggers fire. Triggers may be time-based, filesystem events, incoming webhooks, or arbitrarily complex AI checks powered by local or cloud language models.

## Features

* Cron-style time triggers, folder monitoring, and webhook listeners
* AI triggers that evaluate arbitrary prompts against multiple models (default: a local `phi-4-mini` compatible model via `llama-cpp-python`)
* Extensible registry for new Trigger and Action types
* JSON-based, schema-validated TriggerAction definitions stored as standalone files
* Asynchronous, multi-process execution queue powered by Celery
* FastAPI server exposing management and observability APIs
* Typer CLI for creating new triggers from the terminal
* Structured logging and tracing via OpenTelemetry

## Installation

```bash
# Clone repository
$ git clone https://github.com/yourname/triggered.git
$ cd triggered

# Option 1 – One-shot helper script (recommended)
$ chmod +x scripts/install.sh
$ ./scripts/install.sh           # full setup (installs Redis if missing)

# Option 1b – Lightweight (no Redis)
$ NO_REDIS=1 ./scripts/install.sh  # uses Celery's in-memory broker

# Option 2 – Manual Poetry install
$ poetry install --extras "local-model"
```

The installer will:
1. Ensure Poetry is present
2. Install all Python dependencies
3. (Optionally) install & start Redis, or fall back to an in-process `memory://` broker when `NO_REDIS=1` is set
4. Start the FastAPI API server and a Celery worker

The first time an AI trigger/action runs, the required GGUF model is automatically pulled from Hugging Face via `llama-cpp-python`.

Press `Ctrl-C` in the install-script terminal at any time and it will shut down both the API server and Celery worker for you (the script now traps the signal and kills the background PIDs automatically).

## Quick start

```bash
# Launch the server in one terminal
$ poetry run triggered server

# In another terminal, start the worker processing queue
$ poetry run celery -A triggered.queue worker --loglevel=info
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Project layout

```
triggered/
├── actions/        # Built-in Action strategies
├── triggers/       # Built-in Trigger strategies
├── cli.py          # Typer command-line interface
├── core.py         # Trigger, Action, TriggerAction base classes
├── registry.py     # Global registries & decorators
├── queue.py        # Celery app & tasks
└── server.py       # FastAPI application
```

## License
MIT 

## Example: AI-driven process listing

The snippet below adds a trigger that asks a local LLM every minute whether it should list running processes.  When the model answers **yes** the Shell action executes `ps axu`.

Save as `triggers/ai-ps.json` (or POST to `/triggers`).  The runtime will pick it up automatically on startup.

```jsonc
{
  "trigger_type": "ai",
  "trigger_config": {
    "prompt": "Answer ONLY yes or no. Should I list running processes?",
    "model": "local",
    "interval": 60
  },
  "action_type": "shell",
  "action_config": {
    "command": "ps axu"
  }
}
```

You'll see the command output in the Celery worker logs each time the AI decides to fire.

### Run a Trigger once from the CLI

To execute any trigger-action JSON once without starting the server/worker pair:

```bash
# inside project root
poetry run triggered run-trigger triggers/ai-ps.json
```

The CLI loads the file, performs the AI check, and runs the associated action immediately, printing any logs to the console. 