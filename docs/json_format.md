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

#### Variable Substitution in Prompts

In AI actions and triggers, you can use variable substitution in prompts using the `${var}` syntax. Variables can come from three sources:

1. Environment Variables:
```json
{
  "action": {
    "type": "ai",
    "config": {
      "prompt": "Check if the API key ${API_KEY} is valid"
    }
  }
}
```

2. Global Parameters:
```json
{
  "action": {
    "type": "ai",
    "config": {
      "prompt": "Analyze the file ${filename}"
    }
  },
  "params": {
    "filename": "example.txt"
  }
}
```

3. Trigger Data:
```json
{
  "trigger": {
    "type": "folder-monitor",
    "config": {
      "path": "/tmp"
    }
  },
  "action": {
    "type": "ai",
    "config": {
      "prompt": "Based on the filename '${data.filename}', analyze what this file might be used for. The file was ${data.event} at path ${data.filepath}."
    }
  }
}
```

Variables are resolved in the following order:
1. Environment variables (e.g., `${API_KEY}`)
2. Global parameters from the config (e.g., `${filename}`)
3. Trigger data (e.g., `${data.filename}`)

#### Trigger Configuration

Each trigger type has its own configuration format:

1. AI Trigger:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "name": "my-ai-trigger",
      "prompt": "Your AI prompt here (supports ${var} substitution)",
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


### Variable Substitution in AI Prompts

AI triggers and actions support variable substitution in prompts using the `${var}` syntax. Variables can come from three sources:

1. Environment Variables:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "prompt": "Check if the API key ${API_KEY} is valid"
    }
  }
}
```

2. Global Parameters:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "prompt": "Analyze the file ${filename}"
    }
  },
  "params": {
    "filename": "example.txt"
  }
}
```

3. Trigger Data (for AI actions):
```json
{
  "trigger": {
    "type": "folder-monitor",
    "config": {
      "path": "/tmp"
    }
  },
  "action": {
    "type": "ai",
    "config": {
      "prompt": "Based on the filename '${data.filename}', analyze what this file might be used for. The file was ${data.event} at path ${data.filepath}."
    }
  }
}
```

Variables are resolved in the following order:
1. Environment variables (e.g., `${API_KEY}`)
2. Global parameters from the config (e.g., `${filename}`)
3. Trigger data passed to the action (e.g., `${filename}`)

Example with all types of variables:
```json
{
  "trigger": {
    "type": "folder-monitor",
    "config": {
      "path": "/tmp"
    }
  },
  "action": {
    "type": "ai",
    "config": {
      "prompt": "Analyze file '${filename}' in ${ENV_NAME} environment. The file was ${data.event} and should be processed with priority ${priority}."
    }
  },
  "params": {
    "priority": "high"
  }
}
```

### Webhook Call Action Variables

The webhook call action supports variable substitution in URLs, headers, and payloads. Variables can be referenced using the `${varName}` syntax and are resolved in the following order:

1. Environment variables: `${ENV_VAR:-default}`
   - Use `:-` to specify a default value if the environment variable is not set
   - Example: `http://${WEBHOOK_HOST:-localhost}:${WEBHOOK_PORT:-8000}/webhook`

2. Trigger-action parameters: `${paramName}`
   - Parameters defined in the `params` section of the configuration
   - Example: `${AUTH_KEY}`

3. Trigger data: `${dataName}`
   - Data from the trigger context
   - Example: `${trigger_name}`, `${data.message}`

You can use variables in:
- URL: `"url": "http://${HOST}/webhook/${ENDPOINT}"`
- Headers: `"headers": { "X-Auth-Key": "${AUTH_KEY}" }`
- Payload: 
  - Forward entire trigger data: `"payload": "${data}"`
  - Forward specific fields: `"payload": { "message": "${data.message}" }`
  - Mix with static content: `"payload": { "status": "success", "data": "${data}" }`

Example configuration:
```json
{
  "action": {
    "type": "webhook_call",
    "config": {
      "url": "http://${WEBHOOK_HOST:-localhost}:${WEBHOOK_PORT:-8000}/webhook",
      "headers": {
        "Content-Type": "application/json",
        "X-Auth-Key": "${AUTH_KEY:-default-key}",
        "X-Trigger-Name": "${trigger_name}"
      },
      "payload": "${data}"
    }
  },
  "params": {
    "AUTH_KEY": "your-secret-key"
  }
}
```
