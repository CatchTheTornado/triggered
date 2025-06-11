### Available Components

#### Triggers

1. AI Trigger (`ai`)
   - Uses language models to evaluate conditions
   - Configurable prompts and tools
   - Supports various LLM providers through LiteLLM
   - Example config:
   ```json
   {
     "trigger": {
       "type": "ai",
       "config": {
         "name": "my_trigger",
         "prompt": "Your condition here",
         "interval": 60,
         "tools": ["random_number"],
         "model": "openai/gpt-4",  // optional, defaults to ollama/llama3.1
         "api_base": "https://api.openai.com/v1"  // optional, defaults to http://localhost:11434
       }
     }
   }
   ```

   To use OpenAI models:
   ```json
   {
     "trigger": {
       "type": "ai",
       "config": {
         "name": "my_trigger",
         "prompt": "Your condition here",
         "model": "openai/gpt-4",  // or gpt-3.5-turbo
         "api_base": "https://api.openai.com/v1",
         "tools": ["random_number"]
       }
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
     "trigger": {
       "type": "webhook",
       "config": {
         "name": "my_webhook",
         "path": "/webhook",
         "auth_key": "your-secret-key"
       }
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
     "trigger": {
       "type": "folder-monitor",
       "config": {
         "name": "my_folder_monitor",
         "path": "/path/to/watch",
         "patterns": ["*.txt", "*.log"],
         "events": ["created", "modified", "deleted"],
         "recursive": true
       }
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
     "trigger": {
       "type": "cron",
       "config": {
         "name": "my_cron_trigger",
         "schedule": "0 9 * * *",  # Run at 9 AM every day
         "timezone": "UTC"
       }
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
     "action": {
       "type": "shell-command",
       "config": {
         "name": "my_command",
         "command": "echo 'Hello, ${name}!'"
       }
     }
   }
   ```

2. TypeScript Script Action (`typescript-script`)
   - Runs TypeScript scripts
   - Supports Node.js environment
   - Example config:
   ```json
   {
     "action": {
       "type": "typescript-script",
       "config": {
         "name": "my_script",
         "path": "scripts/my-script.ts"
       }
     }
   }
   ```

3. AI Action (`ai`)
   - Uses language models to generate responses
   - Supports variable substitution in prompts
   - Example config:
   ```json
   {
     "action": {
       "type": "ai",
       "config": {
         "name": "my-ai-action",
         "prompt": "Analyze the file '${data.filename}' in ${ENV_NAME} environment. The file was ${data.event} and should be processed with priority ${priority}.",
         "model": "openai/gpt-4",  // optional, defaults to ollama/llama3.1
         "api_base": "https://api.openai.com/v1",  // optional, defaults to http://localhost:11434
         "tools": ["tool1", "tool2"]  // optional, list of tools
       }
     },
     "params": {
       "priority": "high"
     }
   }
   ```

   The prompt supports variable substitution from:
   - Environment variables (e.g., `${ENV_NAME}`)
   - Global parameters (e.g., `${priority}`)
   - Trigger data (e.g., `${filename}`, `${event}`)

#### Tools

1. Random Number Tool
   - Generates random numbers
   - Configurable range
   - Example usage in AI trigger:
   ```json
   {
     "trigger": {
       "type": "ai",
       "config": {
         "name": "random-trigger",
         "prompt": "Generate a random number between 1 and 100",
         "tools": ["random_number"]
       }
     }
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
