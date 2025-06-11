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

