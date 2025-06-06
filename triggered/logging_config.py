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

def setup_logging():
    """Configure logging to both file and console with Rich formatting."""
    # File handler for raw logs
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
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
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
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

    return console 