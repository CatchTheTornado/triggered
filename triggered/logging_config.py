import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
import json
from rich.syntax import Syntax

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
    "telemetry": "magenta",
    "trigger": "bold cyan",
    "action": "bold green"
}))

# Create logger
logger = logging.getLogger("triggered")

def log_telemetry(message: str):
    """Log telemetry message."""
    logger.debug(f"LLM raw: {message}")

def log_result_details(result: Any):
    """Log result details with Rich formatting."""
    if result:
        # Display nicely formatted result in console
        console.print(Syntax(json.dumps(result, indent=2), "json", theme="monokai"))
        # Log to file
        logger.info(f"Result details: {json.dumps(result, indent=2)}")

def log_action_result(action_name: str, result: Any = None, error: str = None):
    """Log a formatted action result message."""
    if error:
        # Display error in console with Rich formatting
        console.print(f"[red]Action {action_name} ❌ Failed: {error}[/red]")
        # Log to file
        logger.error(f"Action {action_name} ❌ Failed: {error}")
    else:
        # Display success in console with Rich formatting
        console.print(f"[green]Action {action_name} ✓ Completed: {result}[/green]")
        # Log to file
        logger.info(f"Action {action_name} ✓ Completed: {result}")

def log_trigger_check(trigger_name: str, triggered: bool, reason: str = None):
    """Log a formatted trigger check result."""
    status = "✓ TRIGGERED" if triggered else "✗ SKIPPED"
    # Display in console with Rich formatting
    console.print(f"[cyan]Trigger {trigger_name} {status}: {reason}[/cyan]")
    # Log to file
    logger.info(f"Trigger {trigger_name} {status}: {reason}")

def log_action_start(action_name: str):
    """Log a formatted action start message."""
    # Display in console with Rich formatting
    console.print(f"[green]Action {action_name} 🚀 Starting[/green]")
    # Log to file
    logger.info(f"Action {action_name} 🚀 Starting")

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
    
    # Configure specific loggers
    loggers = {
        "triggered": numeric_level,
        "uvicorn": numeric_level,
        "fastapi": numeric_level,
        "LiteLLM": logging.ERROR,  # Always set LiteLLM to ERROR
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
        rich_tracebacks=True,
        markup=True  # Enable markup in console output
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
        "LiteLLM": logging.ERROR,  # Always set LiteLLM to ERROR
    }

    for logger_name, level in loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.propagate = True

    # Set initial log level from environment
    set_log_level(log_level)

    return logger 