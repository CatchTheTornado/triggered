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

# Install runtime deps
$ poetry install --with local-model  # add --without local-model to skip local LLM support
```

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