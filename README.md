# Triggered

Triggered is a Python library for creating and managing AI-powered triggers and actions. It uses LiteLLM to interact with various LLM providers, with Ollama as the default model.

## Features

- AI-powered triggers that can make decisions based on prompts and tools
- Support for various LLM providers through LiteLLM
- Built-in tools for common tasks (random numbers, etc.)
- Custom tool support
- Shell command actions
- Cron-style scheduling
- Folder monitoring
- Webhook monitoring
- FastAPI server for managing triggers and handling webhooks

## Development Setup

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository:
```bash
git clone https://github.com/CatchTheTornado/triggered.git
cd triggered
```

3. Install dependencies using Poetry:
```bash
poetry install
```

4. Activate the Poetry environment:
```bash
source $(poetry env info --path)/bin/activate
```

5. Install the package in development mode:
```bash
poetry install
```

This will make the `triggered` command available in your shell.

## Quick Start

1. Install Ollama and pull the llama3.1 model:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.1
```

2. Create a trigger configuration file using the interactive CLI:
```bash
# Start interactive trigger creation
triggered add

# Or create from JSON configs
triggered add --trigger-type ai --action-type shell --trigger-config-path trigger.json --action-config-path action.json
```

The interactive mode will guide you through:
- Selecting trigger type (AI, Cron, Webhook, Folder)
- Selecting action type (Shell, Webhook Call, AI Agent, Python Script, TypeScript Script)
- Configuring trigger-specific settings
- Configuring action-specific settings

3. List available triggers:
```bash
triggered ls
```

4. Run the trigger:
```bash
# Using full path
triggered run triggers/my_trigger.json

# Or using just the filename (it will look in the triggers directory)
triggered run my_trigger.json
```

5. Start the server (for webhook triggers and trigger management):
```bash
# Start with default settings (host: 0.0.0.0, port: 8000)
triggered start

# Or customize host and port
triggered start --host localhost --port 3000

# Enable auto-reload during development
triggered start --reload
```

## Configuration

### AI Trigger

The AI trigger uses LiteLLM to interact with LLM providers. By default, it uses Ollama with the llama3.1 model.

```json
{
    "trigger_type": "ai",
    "trigger_config": {
        "name": "my_trigger",
        "model": "ollama/llama3.1",  // Default model
        "api_base": "http://localhost:11434",  // Default API base
        "interval": 60,  // Check every 60 seconds
        "prompt": "Your prompt here",
        "tools": [
            {
                "type": "random_number"
            }
        ],
        "custom_tools_path": "path/to/custom_tools.py"  // Optional
    }
}
```

### Environment Variables

You can configure the model and API base using environment variables:

```bash
export LITELLM_MODEL="ollama/llama3.1"  # Default model
export LITELLM_API_BASE="http://localhost:11434"  # Default API base
```

### Available Tools

- `random_number`: Generate random numbers
- Custom tools can be added by creating a Python module

## Examples

### Random Number Trigger

```json
{
    "trigger_type": "ai",
    "trigger_config": {
        "name": "random_number_trigger",
        "model": "ollama/llama3.1",
        "api_base": "http://localhost:11434",
        "interval": 60,
        "prompt": "Generate a random number between 1 and 10. Make the decision based on the number - if >=5 then trigger otherwise don't trigger",
        "tools": [
            {
                "type": "random_number"
            }
        ]
    },
    "action_type": "shell",
    "action_config": {
        "command": "echo 'Got a high number!'"
    }
}
```

## Development

1. Make sure you're in the Poetry environment:
```bash
source $(poetry env info --path)/bin/activate
```

2. Run tests:
```bash
poetry run pytest
```

3. Run a trigger:
```bash
triggered run triggers/random_trigger.json
```

## License

MIT 