# Triggered

A Python library for creating and managing AI-powered triggers and actions.

## Features

- AI-powered triggers that can monitor and react to various conditions
- Flexible action system for executing tasks when triggers fire
- FastAPI server for managing triggers and handling webhooks
- Rich CLI interface with interactive trigger creation
- Comprehensive logging system with both console and file output
- Support for various trigger types (e.g., AI-based, webhook-based)
- Support for various action types (e.g., shell commands, TypeScript scripts)
- Auto-discovery of custom components
- Pluggable architecture for easy extension

## Environment Variables

- `TRIGGERED_LOG_LEVEL`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `TRIGGERED_LOGS_PATH`: Set the path for log files (default: "logs")
- `TRIGGERED_TRIGGER_ACTIONS_PATH`: Set the path for trigger definitions (default: "trigger_actions")
- `TRIGGERED_EXAMPLES_PATH`: Set the path for example trigger definitions (default: "examples")
- `TRIGGERED_TRIGGERS_MODULE`: Set the Python module path for trigger implementations (default: "triggered.triggers")
- `TRIGGERED_ACTIONS_MODULE`: Set the Python module path for action implementations (default: "triggered.actions")
- `TRIGGERED_TOOLS_MODULE`: Set the Python module path for tool implementations (default: "triggered.tools")
- `TRIGGERED_BROKER_URL`: Set the Celery broker URL (default: "memory://")
- `TRIGGERED_BACKEND_URL`: Set the Celery backend URL (default: "rpc://")

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/triggered.git
cd triggered
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Quick Start

1. Create a trigger-action definition:
```bash
triggered add
```
This will start an interactive prompt to create a new trigger-action configuration.

2. Or create a trigger-action from JSON configs:
```bash
triggered add --trigger-type ai --action-type shell-command --trigger-config trigger.json --action-config action.json
```

3. List available triggers:
```bash
triggered ls
```

4. Check available components and loaded triggers:
```bash
triggered check
```
This command displays:
- Available trigger types and their descriptions
- Available action types and their descriptions
- Currently loaded trigger-action JSON files

5. Start the server:
```bash
triggered start
```
This will start the FastAPI server with default settings (host: 0.0.0.0, port: 8000).

You can customize the server settings:
```bash
triggered start --host localhost --port 3000
```

Enable auto-reload during development:
```bash
triggered start --reload
```

6. Run a trigger once:
```bash
triggered run triggers/your-trigger.json
```

## Configuration

### Environment Variables

- `TRIGGERED_LOG_LEVEL`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `TRIGGERED_LOGS_PATH`: Set the path for log files (default: "logs")
- `TRIGGERED_TRIGGER_ACTIONS_PATH`: Set the path for trigger definitions (default: "trigger_actions")
- `TRIGGERED_EXAMPLES_PATH`: Set the path for example trigger definitions (default: "examples")
- `TRIGGERED_TRIGGERS_MODULE`: Set the Python module path for trigger implementations (default: "triggered.triggers")
- `TRIGGERED_ACTIONS_MODULE`: Set the Python module path for action implementations (default: "triggered.actions")
- `TRIGGERED_TOOLS_MODULE`: Set the Python module path for tool implementations (default: "triggered.tools")
- `TRIGGERED_BROKER_URL`: Set the Celery broker URL (default: "memory://")
- `TRIGGERED_BACKEND_URL`: Set the Celery backend URL (default: "rpc://")

#### Parameter Environment Variable Binding

Parameters in trigger-action definitions support environment variable binding using the `${VAR}` syntax. This allows you to use environment variables in your configurations without hardcoding values.

Example:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "name": "env-demo",
      "prompt": "Check if the API key is valid"
    }
  },
  "action": {
    "type": "shell",
    "config": {
      "command": "echo 'Using API key: ${API_KEY}'"
    }
  },
  "params": {
    "api_key": "${API_KEY}",
    "api_url": "${API_URL:-https://api.example.com}"
  }
}
```

In this example:
- `${API_KEY}` will be replaced with the value of the `API_KEY` environment variable
- `${API_URL:-https://api.example.com}` uses a default value if `API_URL` is not set
- The values are resolved at runtime when the trigger or action is executed

You can access these parameters in your code using `ctx.get_param('param_name')`, which will automatically resolve any environment variables.

### Logging

The application uses a comprehensive logging system:
- Console output with Rich formatting and colors
- File logging in the `logs` directory (one file per day)
- Different log levels for different components
- Detailed logging of trigger checks and action executions

### Available Components

#### Triggers

1. AI Trigger (`ai`)
   - Uses language models to evaluate conditions
   - Configurable prompts and tools
   - Supports various LLM providers through LiteLLM
   - Example config:
   ```json
   {
     "trigger_type": "ai",
     "trigger_config": {
       "name": "my_trigger",
       "prompt": "Your condition here",
       "interval": 60,
       "tools": ["random_number"]
     }
   }
   ```

2. Webhook Trigger (`webhook`)
   - Fires on HTTP requests
   - Configurable endpoints and authentication
   - Example config:
   ```json
   {
     "trigger_type": "webhook",
     "trigger_config": {
       "name": "my_webhook",
       "path": "/webhook",
       "auth_key": "your-secret-key"
     }
   }
   ```

3. Folder Monitor Trigger (`folder-monitor`)
   - Monitors a directory for file changes
   - Supports file creation, modification, and deletion events
   - Configurable file patterns and event types
   - Example config:
   ```json
   {
     "trigger_type": "folder-monitor",
     "trigger_config": {
       "name": "my_folder_monitor",
       "path": "/path/to/watch",
       "patterns": ["*.txt", "*.log"],
       "events": ["created", "modified", "deleted"],
       "recursive": true
     }
   }
   ```

4. Cron Trigger (`cron`)
   - Schedule-based trigger using cron expressions
   - Supports standard cron syntax
   - Configurable timezone
   - Example config:
   ```json
   {
     "trigger_type": "cron",
     "trigger_config": {
       "name": "my_cron_trigger",
       "schedule": "0 9 * * *",  # Run at 9 AM every day
       "timezone": "UTC"
     }
   }
   ```

#### Actions

1. Shell Command Action (`shell-command`)
   - Executes shell commands
   - Supports variable substitution
   - Example config:
   ```json
   {
     "action_type": "shell-command",
     "action_config": {
       "name": "my_command",
       "command": "echo 'Hello, ${name}!'"
     }
   }
   ```

2. TypeScript Script Action (`typescript-script`)
   - Runs TypeScript scripts
   - Supports Node.js environment
   - Example config:
   ```json
   {
     "action_type": "typescript-script",
     "action_config": {
       "name": "my_script",
       "path": "scripts/my-script.ts"
     }
   }
   ```

#### Tools

1. Random Number Tool
   - Generates random numbers
   - Configurable range
   - Example usage in AI trigger:
   ```json
   {
     "type": "random_number",
     "min": 1,
     "max": 100
   }
   ```

2. Custom Tools
   - Can be added by creating a Python module
   - Must implement the Tool interface
   - Example implementation:
   ```python
   from triggered.tools import Tool

   class MyCustomTool(Tool):
       name = "my_tool"
       description = "My custom tool description"

       async def execute(self, **kwargs):
           # Tool implementation
           return result
   ```

### Creating Custom Components

#### Auto-Discovery of Components

The system automatically discovers and registers components from the following locations:
- `triggered/triggers/` - Custom trigger implementations
- `triggered/actions/` - Custom action implementations
- `triggered/tools/` - Custom tool implementations

You can override these paths using environment variables:
```bash
export TRIGGERED_TRIGGERS_MODULE="my_package.triggers"
export TRIGGERED_ACTIONS_MODULE="my_package.actions"
export TRIGGERED_TOOLS_MODULE="my_package.tools"
```

#### Adding a Custom Trigger

1. Create a new file in your triggers directory:
```python
from triggered.core import Trigger

class MyCustomTrigger(Trigger):
    name = "my-custom"  # This will be the trigger type
    description = "My custom trigger description"

    def __init__(self, config: dict):
        super().__init__(config)
        # Initialize your trigger

    async def check(self):
        # Implement trigger logic
        return TriggerContext(
            data={
                "trigger": True,  # or False
                "reason": "Trigger reason"
            }
        )
```

2. The trigger will be automatically discovered and registered.

#### Adding a Custom Action

1. Create a new file in your actions directory:
```python
from triggered.core import Action

class MyCustomAction(Action):
    name = "my-custom"  # This will be the action type
    description = "My custom action description"

    def __init__(self, config: dict):
        super().__init__(config)
        # Initialize your action

    async def execute(self, ctx):
        # Implement action logic
        return result
```

2. The action will be automatically discovered and registered.

#### Adding a Custom Tool

1. Create a new file in your tools directory:
```python
from triggered.tools import Tool

class MyCustomTool(Tool):
    name = "my_tool"
    description = "My custom tool description"

    async def execute(self, **kwargs):
        # Tool implementation
        return result
```

2. The tool will be automatically discovered and registered.

#### Manual Registration

If you prefer to register components manually or need more control, you can use the registration functions:

```python
from triggered.registry import register_trigger, register_action, register_tool

# Register a trigger
register_trigger("my-custom", MyCustomTrigger)

# Register an action
register_action("my-custom", MyCustomAction)

# Register a tool
register_tool("my-tool", MyCustomTool)
```

#### Component Structure

Your custom components directory should follow this structure:
```
my_components/
├── triggers/
│   ├── __init__.py
│   └── my_custom_trigger.py
├── actions/
│   ├── __init__.py
│   └── my_custom_action.py
└── tools/
    ├── __init__.py
    └── my_custom_tool.py
```

Each component should:
1. Inherit from the appropriate base class
2. Define a `name` and `description` class variable
3. Implement the required methods
4. Be placed in the correct directory

The system will automatically:
- Discover all components in the specified directories
- Register them with appropriate names
- Make them available in the CLI and API

## Development

### Project Structure

```
triggered/
├── actions/          # Action implementations
├── triggers/         # Trigger implementations
├── core.py          # Core trigger-action logic
├── registry.py      # Component registry
├── server.py        # FastAPI server
├── cli.py           # CLI interface
└── logging_config.py # Logging configuration
```

### Adding New Components

1. Create a new trigger or action class in the appropriate directory
2. Implement the required methods
3. Register the component in `registry.py`

### Testing

Run tests with pytest:
```bash
pytest
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run all checks:
```bash
pre-commit run --all-files
```

## License

MIT License 