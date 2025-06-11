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
