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

### Logging

The application uses a comprehensive logging system:
- Console output with Rich formatting and colors
- File logging in the `logs` directory (one file per day)
- Different log levels for different components
- Detailed logging of trigger checks and action executions

### Available Tools

#### Triggers

- `ai`: AI-based trigger that uses language models to evaluate conditions
- `webhook`: Webhook-based trigger that fires on HTTP requests

#### Actions

- `shell-command`: Execute shell commands
- `typescript-script`: Run TypeScript scripts

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