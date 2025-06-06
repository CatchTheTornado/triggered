# Triggered

Triggered is a Python library for creating and managing AI-powered triggers and actions. It uses LiteLLM to interact with various LLM providers, with Ollama as the default model.

## Features

- AI-powered triggers that can make decisions based on prompts and tools
- Support for various LLM providers through LiteLLM
- Built-in tools for common tasks (weather, random numbers, etc.)
- Custom tool support
- Shell command actions
- Cron-style scheduling
- Folder monitoring
- Webhook monitoring

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

4. Activate the Poetry shell:
```bash
poetry shell
```

## Quick Start

1. Install Ollama and pull the llama3.1 model:
```bash
# Install Ollama from https://ollama.ai
ollama pull llama3.1
```

2. Create a trigger configuration file (e.g., `triggers/my_trigger.json`):
```json
{
    "trigger_type": "ai",
    "trigger_config": {
        "name": "my_trigger",
        "model": "ollama/llama3.1",
        "api_base": "http://localhost:11434",
        "interval": 60,
        "prompt": "Your prompt here",
        "tools": [
            {
                "type": "weather"
            }
        ]
    },
    "action_type": "shell",
    "action_config": {
        "command": "echo 'Action triggered!'"
    }
}
```

3. Run the trigger:
```bash
# Make sure you're in the Poetry shell
poetry run python -m triggered.cli run-trigger triggers/my_trigger.json
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
                "type": "weather"
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

- `weather`: Get current weather conditions
- `random_number`: Generate random numbers
- Custom tools can be added by creating a Python module

## Examples

### Weather Trigger

```json
{
    "trigger_type": "ai",
    "trigger_config": {
        "name": "cloudy_weather_trigger",
        "model": "ollama/llama3.1",
        "api_base": "http://localhost:11434",
        "interval": 300,
        "prompt": "Check if it's cloudy in {{ city }}. Use the weather tool to get current conditions. If the weather is cloudy, trigger the action.",
        "prompt_vars": {
            "city": "London"
        },
        "tools": [
            {
                "type": "weather"
            }
        ]
    },
    "action_type": "shell",
    "action_config": {
        "command": "echo 'It's cloudy in {{ city }}! Time to bring an umbrella.'"
    }
}
```

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

1. Make sure you're in the Poetry shell:
```bash
poetry shell
```

2. Run tests:
```bash
poetry run pytest
```

3. Run a trigger:
```bash
poetry run python -m triggered.cli run-trigger triggers/random_trigger.json
```

## License

MIT 