# 🚀 Triggered

**Crontab on AI steroids with an API**. Use AI prompts and tools, time-tables, file-system watchers to trigger actions you like, when it's suitable. Super easy to use and manage ⚡️

<div align="center">
  <img src=".readme_assets/0.png" alt="Triggered Hero Image" width="800"/>
</div>

<div align="center">
  <table>
    <tr>
      <td align="center">
        <img src=".readme_assets/1.png" alt="Triggered CLI" width="400"/>
        <br/>
        <em>Interactive CLI for creating and managing triggers</em>
      </td>
      <td align="center">
        <img src=".readme_assets/2.png" alt="Triggered Dashboard" width="400"/>
        <br/>
        <em>Running AI triggers from CLI or via Web API</em>
      </td>
    </tr>
  </table>
</div>

## ✨ Features

- 🤖 AI-powered triggers that can monitor and react to various conditions
- ⚡️ Flexible action system for executing tasks when triggers fire
- 🌐 FastAPI server for managing triggers and handling webhooks
- 🖥️ Rich CLI interface with interactive trigger creation
- 📝 Comprehensive logging system with both console and file output
- 🔌 Support for various trigger types (e.g., AI-based, webhook-based)
- 🛠️ Support for various action types (e.g., shell commands, TypeScript scripts)
- 🔍 Auto-discovery of custom components
- 🧩 Pluggable architecture for easy extension


## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/CatchTheTornado/triggered.git
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
- Currently loaded trigger-action JSON files from enabled_trigger_actions and example_trigger_actions directories

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
- `TRIGGERED_TRIGGER_ACTIONS_PATH`: Set the path for enabled trigger definitions (default: "enabled_trigger_actions")
- `TRIGGERED_EXAMPLES_PATH`: Set the path for example trigger definitions (default: "example_trigger_actions")
- `TRIGGERED_TRIGGERS_MODULE`: Set the Python module path for trigger implementations (default: "triggered.triggers")
- `TRIGGERED_ACTIONS_MODULE`: Set the Python module path for action implementations (default: "triggered.actions")
- `TRIGGERED_TOOLS_MODULE`: Set the Python module path for tool implementations (default: "triggered.tools")
- `TRIGGERED_DATA_DIR`: Set the path for data storage (default: "data")
- `TRIGGERED_BROKER_URL`: Set the Celery broker URL (default: "sqla+sqlite:///data/celery.sqlite")
- `TRIGGERED_BACKEND_URL`: Set the Celery backend URL (default: "db+sqlite:///data/celery_results.sqlite")

### Message Broker Configuration

By default, Triggered uses SQLite as both the message broker and result backend. This requires no external dependencies and works out of the box. However, you can configure it to use other backends like Redis or RabbitMQ for better performance in production environments.

#### Required Dependencies

The following Python packages are required for different message brokers:

1. SQLite (Default) - requires `sqlalchemy`
2. Redis - requires `redis`
3. RabbitMQ - requires `amqp`

All required dependencies are automatically installed when you install the project using Poetry:
```bash
poetry install
```

#### Available Backends

1. SQLite (Default)
   ```bash
   # Default configuration - no additional setup required
   export TRIGGERED_BROKER_URL="sqla+sqlite:///data/celery.sqlite"
   export TRIGGERED_BACKEND_URL="db+sqlite:///data/celery_results.sqlite"
   ```

2. Redis
   ```bash
   # Install Redis
   # macOS:
   brew install redis
   brew services start redis
   
   # Ubuntu/Debian:
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   
   # Configure Triggered to use Redis
   export TRIGGERED_BROKER_URL="redis://localhost:6379/0"
   export TRIGGERED_BACKEND_URL="redis://localhost:6379/1"
   ```

3. RabbitMQ
   ```bash
   # Install RabbitMQ
   # macOS:
   brew install rabbitmq
   brew services start rabbitmq
   
   # Ubuntu/Debian:
   sudo apt-get install rabbitmq-server
   sudo systemctl start rabbitmq-server
   
   # Configure Triggered to use RabbitMQ
   export TRIGGERED_BROKER_URL="amqp://guest:guest@localhost:5672//"
   export TRIGGERED_BACKEND_URL="rpc://"
   ```

4. Memory (Not recommended for production)
   ```bash
   # In-memory broker (not shared between processes)
   export TRIGGERED_BROKER_URL="memory://"
   export TRIGGERED_BACKEND_URL="rpc://"
   ```

#### Backend Comparison

| Backend  | Pros | Cons |
|----------|------|------|
| SQLite   | - No external dependencies<br>- Works out of the box<br>- Persistent storage<br>- Shared between processes | - Not suitable for high concurrency<br>- Slower than Redis/RabbitMQ |
| Redis    | - Fast and reliable<br>- Good for high concurrency<br>- Built-in result backend | - Requires Redis installation<br>- External dependency |
| RabbitMQ | - Enterprise-grade reliability<br>- Advanced routing features<br>- Good for complex setups | - Requires RabbitMQ installation<br>- More complex setup |
| Memory   | - Fastest for single process<br>- No setup required | - Not shared between processes<br>- Data lost on restart |

#### Production Recommendations

For production environments, we recommend:

1. Small to Medium Scale:
   - Use Redis as both broker and backend
   - Provides good performance and reliability
   - Simple setup and maintenance

2. Large Scale:
   - Use RabbitMQ as broker
   - Use Redis as backend
   - Provides best scalability and reliability

3. Development/Testing:
   - Use default SQLite configuration
   - No additional setup required
   - Good for local development

#### Troubleshooting

If you encounter issues with task execution:

1. Check broker connection:
   ```bash
   # For Redis
   redis-cli ping
   
   # For RabbitMQ
   rabbitmqctl status
   ```

2. Check Celery worker status:
   ```bash
   celery -A triggered.queue status
   ```

3. Monitor task execution:
   ```bash
   celery -A triggered.queue events
   ```

4. Check logs:
   ```bash
   tail -f logs/triggered.log
   ```

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
       "tools": ["random_number"],
       "model": "openai/gpt-4",  // optional, defaults to ollama/llama3.1
       "api_base": "https://api.openai.com/v1"  // optional, defaults to http://localhost:11434
     }
   }
   ```

   To use OpenAI models:
   ```json
   {
     "trigger_type": "ai",
     "trigger_config": {
       "name": "my_trigger",
       "prompt": "Your condition here",
       "model": "openai/gpt-4",  // or gpt-3.5-turbo
       "api_base": "https://api.openai.com/v1",
       "tools": ["random_number"]
     }
   }
   ```
   Note: Make sure to set your OpenAI API key in the environment variable `OPENAI_API_KEY`.

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
   - Must be saved in the file set in `custom_tools_path` config variable in the `trigger_action` JSON file.
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

enabled_trigger_actions/  # Active trigger definitions
example_trigger_actions/  # Example trigger definitions
disabled_trigger_actions/ # Disabled trigger definitions
```

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

### JSON Configuration Format

The configuration is defined in JSON format with the following structure:

```json
{
  "trigger": {
    "type": "<trigger_type>",
    "config": {
      // Trigger-specific configuration
    }
  },
  "action": {
    "type": "<action_type>",
    "config": {
      // Action-specific configuration
    }
  },
  "params": {
    // Global parameters accessible to both trigger and action
  }
}
```

#### Trigger Configuration

Each trigger type has its own configuration format:

1. AI Trigger:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "name": "my-ai-trigger",
      "prompt": "Your AI prompt here",
      "model": "ollama/llama3.1",  // optional, defaults to ollama/llama3.1
      "api_base": "http://localhost:11434",  // optional, defaults to http://localhost:11434
      "interval": 60,  // optional, check interval in seconds
      "tools": ["tool1", "tool2"],  // optional, list of tools
      "custom_tools_path": "./path/to/tools.py"  // optional, path to custom tools
    }
  }
}
```

2. Webhook Trigger:
```json
{
  "trigger": {
    "type": "webhook",
    "config": {
      "name": "my-webhook",
      "path": "/webhook",
      "auth_key": "your-secret-key",
      "methods": ["POST", "GET"]  // optional, defaults to ["POST"]
    }
  }
}
```

3. Folder Monitor Trigger:
```json
{
  "trigger": {
    "type": "folder-monitor",
    "config": {
      "name": "my-folder-monitor",
      "path": "/path/to/watch",
      "patterns": ["*.txt", "*.log"],  // optional, defaults to ["*"]
      "events": ["created", "modified", "deleted"],  // optional, defaults to all events
      "recursive": true  // optional, defaults to false
    }
  }
}
```

4. Cron Trigger:
```json
{
  "trigger": {
    "type": "cron",
    "config": {
      "name": "my-cron",
      "schedule": "0 9 * * *",  // cron expression
      "timezone": "UTC"  // optional, defaults to system timezone
    }
  }
}
```

#### Action Configuration

Each action type has its own configuration format:

1. Shell Command Action:
```json
{
  "action": {
    "type": "shell",
    "config": {
      "name": "my-shell-action",
      "command": "echo 'Hello, ${name}!'",
      "cwd": "/path/to/working/dir",  // optional, defaults to current directory
      "timeout": 30  // optional, command timeout in seconds
    }
  }
}
```

2. TypeScript Script Action:
```json
{
  "action": {
    "type": "typescript-script",
    "config": {
      "name": "my-ts-action",
      "path": "scripts/my-script.ts",
      "cwd": "/path/to/working/dir",  // optional, defaults to current directory
      "timeout": 30  // optional, script timeout in seconds
    }
  }
}
```

#### Global Parameters

The `params` section contains global parameters that are accessible to both trigger and action:

```json
{
  "params": {
    "param1": "value1",
    "param2": "value2",
    "nested": {
      "key": "value"
    }
  }
}
```

Parameters can be accessed in:
- Trigger context using `ctx.params.get('param1')`
- Action context using `ctx.params.get('param1')`
- Shell commands using `${param1}` syntax
- TypeScript scripts through the context object

Parameters also support environment variable binding:
```json
{
  "params": {
    "api_key": "${API_KEY}",
    "api_url": "${API_URL:-https://api.example.com}"  // with default value
  }
}
```

### Tool Configuration Formats

Tools can be configured in two different formats in your JSON configuration:

1. Simple String Format:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "name": "simple-tools",
      "prompt": "Your prompt here",
      "tools": ["random_number", "config_demo"]
    }
  }
}
```

2. Object Format with Type:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "name": "object-tools",
      "prompt": "Your prompt here",
      "tools": [
        {
          "type": "random_number"
        },
        {
          "type": "config_demo"
        }
      ]
    }
  }
}
```

Both formats are supported and will be automatically converted to the appropriate format internally. The object format is more flexible as it allows for additional configuration options to be added to each tool if needed in the future.

#### Custom Tools

To use custom tools, you need to:

1. Create a Python module with your tool implementation:
```python
# my_tools.py
from typing import Optional
from pydantic import BaseModel
from triggered.tools import Tool

# Define input schema for your tool
class WeatherToolInput(BaseModel):
    city: str
    country: Optional[str] = None
    units: str = "metric"

class WeatherTool(Tool):
    name = "weather"
    description = "Get current weather for a city"
    args_schema = WeatherToolInput

    async def execute(self, city: str, country: Optional[str] = None, units: str = "metric"):
        # Your tool implementation here
        return {
            "temperature": 25,
            "conditions": "sunny",
            "humidity": 60
        }
```

2. Create an `__init__.py` file in your tools directory to expose your tools:
```python
# tools/__init__.py
from .my_tools import WeatherTool

# List of tools to be automatically registered
__all__ = ["WeatherTool"]
```

3. Specify the path to your module in the configuration:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "name": "custom-tools",
      "prompt": "Your prompt here",
      "custom_tools_path": "./path/to/your/tools.py",
      "tools": ["weather"]
    }
  }
}
```

4. Or use the tools directory structure for auto-discovery:
```
my_project/
├── tools/
│   ├── __init__.py
│   ├── weather_tool.py
│   └── other_tools.py
```

The `__init__.py` file should import and expose all your tools:
```python
# tools/__init__.py
from .weather_tool import WeatherTool
from .other_tools import OtherTool

# List of tools to be automatically registered
__all__ = [
    "WeatherTool",
    "OtherTool"
]
```

Your tools will be automatically discovered and registered when:
1. They are in the `tools` directory and properly exposed in `__init__.py`
2. They inherit from the `Tool` base class
3. They define a `name`, `description`, and `args_schema`
4. They implement the `execute` method

You can also manually register tools using the registry:
```python
from triggered.registry import register_tool
from .my_tools import WeatherTool

register_tool("weather", WeatherTool)
```

Tool Best Practices:
1. Always define an input schema using Pydantic models
2. Use descriptive names and descriptions
3. Handle errors gracefully
4. Document any required parameters
5. Use type hints for better IDE support
6. Keep tools focused and single-purpose
7. Use async/await for I/O operations

Example of a more complex tool with error handling:
```python
from typing import Optional, List
from pydantic import BaseModel, Field
from triggered.tools import Tool

class SearchToolInput(BaseModel):
    query: str
    max_results: int = Field(default=5, ge=1, le=20)
    filters: Optional[List[str]] = None

class SearchTool(Tool):
    name = "search"
    description = "Search for information with optional filters"
    args_schema = SearchToolInput

    async def execute(
        self,
        query: str,
        max_results: int = 5,
        filters: Optional[List[str]] = None
    ):
        try:
            # Your search implementation here
            results = await self._perform_search(query, max_results, filters)
            return {
                "results": results,
                "count": len(results),
                "query": query
            }
        except Exception as e:
            return {
                "error": str(e),
                "query": query
            }

    async def _perform_search(self, query: str, max_results: int, filters: Optional[List[str]]):
        # Implementation details
        pass
```

## API Documentation

The server provides a RESTful API for managing triggers and actions. Here are the available endpoints with curl examples based on the included example triggers:

### List All Triggers

```bash
curl -X GET http://localhost:8000/triggers
```

Response:
```json
{
  "triggers": [
    {
      "id": "vscode-monitor",
      "filename": "vscode_monitor.json",
      "trigger": {
        "type": "ai",
        "config": {
          "model": "openai/gpt-4o",
          "api_base": "https://api.openai.com/v1",
          "name": "vscode-monitor",
          "prompt": "Check if VS Code (Code Helper process) is running. If it is, trigger the action. If not, don't trigger.",
          "custom_tools_path": "./example_trigger_actions/process_checker.py",
          "tools": ["process_checker"]
        }
      },
      "action": {
        "type": "shell",
        "config": {
          "command": "echo 'VS Code is running!'"
        }
      }
    }
  ]
}
```

### Get Trigger by ID

```bash
curl -X GET http://localhost:8000/triggers/vscode-monitor
```

Response:
```json
{
  "id": "vscode-monitor",
  "filename": "vscode_monitor.json",
  "trigger": {
    "type": "ai",
    "config": {
      "model": "openai/gpt-4o",
      "api_base": "https://api.openai.com/v1",
      "name": "vscode-monitor",
      "prompt": "Check if VS Code (Code Helper process) is running. If it is, trigger the action. If not, don't trigger.",
      "custom_tools_path": "./example_trigger_actions/process_checker.py",
      "tools": ["process_checker"]
    }
  },
  "action": {
    "type": "shell",
    "config": {
      "command": "echo 'VS Code is running!'"
    }
  }
}
```

### Add New Trigger

Example 1 - Random Number Trigger:
```bash
curl -X POST http://localhost:8000/triggers \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": {
      "type": "ai",
      "config": {
        "model": "openai/gpt-4o",
        "name": "random-trigger",
        "prompt": "Generate a random number between 1 and 10 using the tool provided. If it'\''s greater than 5, trigger the action.",
        "tools": ["random_number"]
      }
    },
    "action": {
      "type": "shell",
      "config": {
        "command": "echo '\''Random number was greater than 5!'\''"
      }
    }
  }'
```

Example 2 - Configuration Demo Trigger:
```bash
curl -X POST http://localhost:8000/triggers \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": {
      "type": "ai",
      "config": {
        "model": "ollama/llama3.1",
        "name": "config-demo",
        "prompt": "Check if the configuration is working",
        "custom_tools_path": "./example_trigger_actions/config_demo_tool.py",
        "tools": ["config_demo"]
      }
    },
    "action": {
      "type": "shell",
      "config": {
        "command": "echo '\''Configuration is working!'\''"
      }
    },
    "params": {
      "message": "Hello from configuration!"
    }
  }'
```

Response:
```json
{
  "id": "config-demo",
  "filename": "config_demo.json",
  "trigger": {
    "type": "ai",
    "config": {
      "model": "ollama/llama3.1",
      "name": "config-demo",
      "prompt": "Check if the configuration is working",
      "custom_tools_path": "./example_trigger_actions/config_demo_tool.py",
      "tools": ["config_demo"]
    }
  },
  "action": {
    "type": "shell",
    "config": {
      "command": "echo 'Configuration is working!'"
    }
  },
  "params": {
    "message": "Hello from configuration!"
  }
}
```

### Delete Trigger

```bash
curl -X DELETE http://localhost:8000/triggers/vscode-monitor
```

Response:
```json
{
  "message": "Trigger deleted successfully"
}
```

### Run Trigger Manually

```bash
curl -X POST http://localhost:8000/triggers/vscode-monitor/run
```

Response:
```json
{
  "message": "Trigger execution started",
  "task_id": "task-123"
}
```

### Get Trigger Execution Status

```bash
curl -X GET http://localhost:8000/triggers/vscode-monitor/status
```

Response:
```json
{
  "status": "completed",
  "result": {
    "success": true,
    "output": "VS Code is running!"
  }
}
```

### Webhook Endpoint

For webhook triggers, you can send POST requests to the webhook endpoint:

```bash
curl -X POST http://localhost:8000/webhook/vscode-monitor \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "process_name": "Code Helper",
      "is_running": true
    }
  }'
```

Response:
```json
{
  "message": "Webhook received",
  "task_id": "task-123"
}
```

### Health Check

```bash
curl -X GET http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Error Responses

The API returns standard HTTP status codes and error messages:

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

Common status codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error
```

## Running the Server

Triggered can be run in two different modes:

### Standalone Mode (Default)
This mode runs everything in a single process, which is simpler to set up and manage:

```bash
triggered start
# or explicitly
triggered start --mode standalone
```

This is the recommended mode for most use cases, especially during development.

### Distributed Mode
For production environments or when you need better scalability, you can run the server with a separate Celery worker:

Terminal 1 (Server):
```bash
triggered start --mode distributed
```

Terminal 2 (Worker):
```bash
triggered worker
```

The distributed mode requires a message broker (SQLite by default, but can be configured to use Redis or RabbitMQ).

### Server Configuration

The `start` command supports multiple configuration options:

```bash
triggered start [OPTIONS]

Options:
  --host, -h TEXT     Host to bind the server to [default: 0.0.0.0]
  --port, -p INTEGER  Port to bind the server to [default: 8000]
  --reload, -r        Enable auto-reload on code changes [default: False]
  --mode, -m TEXT     Startup mode: 'standalone' (default) or 'distributed' (with Celery worker)
  --log-level, -l     Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

Examples:
```bash
# Start with default settings (standalone mode)
triggered start

# Start with custom host and port
triggered start --host localhost --port 3000

# Start with auto-reload enabled
triggered start --reload

# Start in distributed mode with custom settings
triggered start --mode distributed --host localhost --port 3000 --reload
```

When starting the server, you'll see a nicely formatted panel showing:
- Server configuration (host, port, auto-reload)
- Available modes and their descriptions
- Current mode
- Instructions for switching modes
- Additional instructions for distributed mode

### Other Commands

```bash
# List all available triggers
triggered ls

# Run a specific trigger once
triggered run <path>

# Enable a disabled trigger
triggered enable <path>

# Disable a trigger
triggered disable <path>

# Check available components
triggered check

# Start the Celery worker (for distributed mode)
triggered worker
```

Each command supports the `--log-level` option for controlling logging verbosity.

#### Cron Expressions

The cron trigger supports both standard 5-field (minute-based) and extended 6-field (second-based) cron expressions:

1. Standard 5-field format (minute-based):
```
* * * * *  (minute hour day month weekday)
```

2. Extended 6-field format (second-based):
```
* * * * * *  (second minute hour day month weekday)
```

Examples:
- `*/20 * * * * *` - Run every 20 seconds
- `0 * * * * *` - Run at the start of every minute
- `0 0 * * * *` - Run at the start of every hour
- `0 0 0 * * *` - Run at midnight every day

For more details about second-based scheduling, see [croniter documentation](https://pypi.org/project/croniter/#about-second-repeats).

## License

MIT License
