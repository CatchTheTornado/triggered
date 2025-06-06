# Triggered

A runtime engine that executes user-defined actions based on various triggers, including time-based, filesystem events, and AI checks.

## Features

- Cron-style triggers for time-based execution
- Filesystem event triggers for file/directory monitoring
- AI-driven triggers using LiteLLM with local Ollama models
- Extensible architecture for new trigger and action types
- FastAPI server for management APIs
- Built-in tools for AI triggers (weather, current date, etc.)
- Support for custom tools via Python modules

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
$ poetry install
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

## AI-Driven Triggers

AI triggers use language models to make decisions based on natural language prompts. They can be configured with various tools to enhance their capabilities.

### Basic Example

```json
{
  "type": "ai",
  "name": "process-check",
  "prompt": "Is there a process named 'nginx' running?",
  "model": "local",
  "interval": 60
}
```

### Using Built-in Tools

AI triggers can use built-in tools to access external information. Here's an example using the weather tool:

```json
{
  "type": "ai",
  "name": "weather-check",
  "prompt": "Is it cloudy in London?",
  "model": "local",
  "interval": 300,
  "tools": [
    {
      "type": "weather",
      "name": "weather"
    }
  ]
}
```

Available built-in tools:
- `weather`: Get current weather conditions for a city
- `currentdate`: Get the current date in YYYY-MM-DD format

### Custom Tools

You can extend the system with custom tools in two ways:

1. **JSON Configuration**
   Add tool configurations to your trigger's JSON:

   ```json
   {
     "type": "ai",
     "name": "custom-tool-example",
     "prompt": "Use my custom tool",
     "model": "local",
     "tools": [
       {
         "type": "my_custom_tool",
         "name": "my_tool",
         "config": {
           "param1": "value1"
         }
       }
     ]
   }
   ```

2. **Python Module**
   Create a Python module with your custom tools and specify its path:

   ```json
   {
     "type": "ai",
     "name": "custom-tools-example",
     "prompt": "Use my custom tools",
     "model": "local",
     "custom_tools_path": "path/to/my_tools.py"
   }
   ```

## Using LiteLLM with Local Ollama

The project uses LiteLLM to interact with local Ollama models. By default, it uses the `llama2` model running on `localhost:11434`. You can configure this using environment variables:

```bash
# Optional - defaults shown
export LITELLM_MODEL="ollama/llama2"  # Default model
export LITELLM_API_BASE="http://localhost:11434"  # Default API base
```

Make sure you have Ollama installed and running locally. You can install it following the instructions at [ollama.ai](https://ollama.ai).

To use a different model, first pull it with Ollama:
```bash
ollama pull llama2  # or any other model you want to use
```

Then update the `LITELLM_MODEL` environment variable to match the model name.

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

## License

MIT 