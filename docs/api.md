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

### Webhook Examples

Here's an example of a webhook trigger that generates a random number and includes the webhook payload in the response:

```json
{
  "trigger": {
    "type": "webhook",
    "config": {
      "name": "webhook-random",
      "path": "/webhook/random",
      "auth_key": "your-secret-key"
    }
  },
  "action": {
    "type": "ai",
    "config": {
      "name": "random-with-payload",
      "prompt": "Generate a random number between 1 and 100 using the random_number tool. Then include this message from the webhook payload: ${payload}. Format your response as: 'Random number: X. Message: Y'",
      "model": "openai/gpt-4o",
      "api_base": "https://api.openai.com/v1",
      "tools": ["random_number"]
    }
  }
}
```

To test this webhook, you can use curl:

```bash
curl -X POST http://localhost:8000/webhook/random \
  -H "Content-Type: application/json" \
  -H "X-Auth-Key: your-secret-key" \
  -d '{
    "payload": "Hello from webhook!"
  }'
```

The AI action will:
1. Generate a random number using the `random_number` tool
2. Include the message from the webhook payload
3. Return a response like: "Random number: 42. Message: Hello from webhook!"

The webhook trigger passes the entire request body as `payload` in the trigger data, which can be accessed in the AI prompt using `${payload}`.
