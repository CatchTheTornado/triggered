import os
import logging
from datetime import datetime
from pathlib import Path
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Create logs directory if it doesn't exist
LOGS_PATH = os.getenv("TRIGGERED_LOGS_PATH", "logs")
LOGS_DIR = Path(LOGS_PATH)
LOGS_DIR.mkdir(exist_ok=True)

# Create a log file with current date
LOG_FILE = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

# Rich console setup
console = Console(theme=Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "server": "blue",
    "telemetry": "magenta"
}))

def set_log_level(level: str):
    """Set the logging level for all handlers."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    # Update console handler level
    for handler in logging.getLogger().handlers:
        if isinstance(handler, RichHandler):
            handler.setLevel(numeric_level)
    
    # Update root logger level
    logging.getLogger().setLevel(numeric_level)
    
    # Update specific loggers
    loggers = {
        "triggered": numeric_level,
        "uvicorn": numeric_level,
        "fastapi": numeric_level,
    }
    
    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = True

def setup_logging():
    """Configure logging to both file and console with Rich formatting."""
    # Get log level from environment variable, default to INFO
    log_level = os.getenv("TRIGGERED_LOG_LEVEL", "INFO")
    
    # File handler for raw logs
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Rich console handler
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True
    )
    console_handler.setLevel(logging.INFO)  # Default to INFO for console

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers = {
        "triggered": logging.INFO,
        "uvicorn": logging.INFO,
        "fastapi": logging.INFO,
    }

    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = True

    # Set initial log level from environment
    set_log_level(log_level)

    return console 