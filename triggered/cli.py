import json
from pathlib import Path
import asyncio
from typing import Optional, Dict, Any
import os

from enum import Enum
import typer
import uvicorn
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax
from pydantic import BaseModel

from .core import TriggerAction, TriggerDefinition, ActionDefinition
from .registry import get_trigger, get_action
from .config_schema import get_trigger_config_schema, get_action_config_schema
from .logging_config import (
    setup_logging, LOGS_DIR, set_log_level, 
    log_trigger_check, log_action_start, log_action_result,
    log_telemetry, log_result_details, console
)


# ---------------------------------------------------------------------------
# Typer app setup
# ---------------------------------------------------------------------------

app = typer.Typer(help="Triggered CLI")
logger = setup_logging()

EXAMPLES_DIR = Path(os.getenv("TRIGGERED_EXAMPLES_PATH", "examples"))
EXAMPLES_DIR.mkdir(exist_ok=True)

TRIGGER_ACTIONS_DIR = Path(os.getenv("TRIGGERED_TRIGGER_ACTIONS_PATH", "trigger_actions"))
TRIGGER_ACTIONS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Global options
# ---------------------------------------------------------------------------

def log_level_callback(value: str):
    """Callback for log level option."""
    if value:
        try:
            set_log_level(value)
        except ValueError as e:
            raise typer.BadParameter(str(e))
    return value


# ---------------------------------------------------------------------------
# Models for interactive prompts
# ---------------------------------------------------------------------------

class TriggerConfig(BaseModel):
    type: str
    config: Dict[str, Any]

class ActionConfig(BaseModel):
    type: str
    config: Dict[str, Any]


# ---------------------------------------------------------------------------
# Paths & helpers
# ---------------------------------------------------------------------------

def get_available_trigger_types() -> list[str]:
    """Get list of available trigger types."""
    from .registry import TRIGGER_REGISTRY
    return list(TRIGGER_REGISTRY.keys())

def get_available_action_types() -> list[str]:
    """Get list of available action types."""
    from .registry import ACTION_REGISTRY
    return list(ACTION_REGISTRY.keys())

def get_available_tool_types() -> list[str]:
    """Get list of available tool types."""
    from .registry import TOOL_REGISTRY
    return list(TOOL_REGISTRY.keys())

def get_python_files_completion():
    """Get list of Python files for tab completion."""
    return [str(f.relative_to(Path.cwd())) for f in Path.cwd().rglob("*.py")]

def prompt_for_custom_tools() -> Optional[str]:
    """Prompt for custom tools path with validation and re-ask if invalid."""
    while True:
        custom_tools_path = Prompt.ask(
            "Path to custom tools Python file (optional, press Enter to skip)",
            default="",
            show_default=False
        )
        
        if not custom_tools_path:
            return None
            
        path = Path(custom_tools_path).expanduser().resolve()
        if not path.exists():
            console.print(f"[red]Error: File not found: {path}[/red]")
            if not Confirm.ask("Would you like to try again?"):
                return None
            continue
            
        if not path.is_file():
            console.print(f"[red]Error: Not a file: {path}[/red]")
            if not Confirm.ask("Would you like to try again?"):
                return None
            continue
            
        if path.suffix != '.py':
            console.print(f"[red]Error: Not a Python file: {path}[/red]")
            if not Confirm.ask("Would you like to try again?"):
                return None
            continue
            
        return str(path)

def display_loaded_actions():
    """Display and log loaded actions in a nice table format."""
    from .registry import ACTION_REGISTRY, TRIGGER_REGISTRY
    
    # Create table for actions
    action_table = Table(title="Loaded Actions", show_header=True, header_style="bold magenta")
    action_table.add_column("Type", style="cyan")
    action_table.add_column("Description", style="green")
    
    # Create table for triggers
    trigger_table = Table(title="Loaded Triggers", show_header=True, header_style="bold magenta")
    trigger_table.add_column("Type", style="cyan")
    trigger_table.add_column("Description", style="green")
    
    # Add actions to table
    for action_type in sorted(ACTION_REGISTRY.keys()):
        action_cls = ACTION_REGISTRY[action_type]
        description = action_cls.__doc__ or f"{action_type.capitalize()} action"
        action_table.add_row(action_type, description)
    
    # Add triggers to table
    for trigger_type in sorted(TRIGGER_REGISTRY.keys()):
        trigger_cls = TRIGGER_REGISTRY[trigger_type]
        description = trigger_cls.__doc__ or f"{trigger_type.capitalize()} trigger"
        trigger_table.add_row(trigger_type, description)
    
    # Display tables
    console.print(action_table)
    console.print(trigger_table)
    
    # Log as simple list
    logger.info("Loaded actions: " + ", ".join(sorted(ACTION_REGISTRY.keys())))
    logger.info("Loaded triggers: " + ", ".join(sorted(TRIGGER_REGISTRY.keys())))

def get_available_trigger_actions():
    """Get list of available trigger-action JSON files."""
    return list(TRIGGER_ACTIONS_DIR.glob("*.json")) + list(EXAMPLES_DIR.glob("*.json"))

def get_json_completion():
    """Get list of JSON files for tab completion."""
    files = get_available_trigger_actions()
    return [str(f.relative_to(Path.cwd())) for f in files]

def display_loaded_trigger_actions():
    """Display and log loaded trigger-action JSON files in a table format."""
    if not TRIGGER_ACTIONS_DIR.exists():
        console.print("[yellow]No triggers directory found.[/yellow]")
        logger.info("No triggers directory found")
        return

    triggers = get_available_trigger_actions()
    if not triggers:
        console.print("[yellow]No trigger files found.[/yellow]")
        logger.info("No trigger files found")
        return

    # Create table for trigger files
    trigger_actions_table = Table(title="Available Trigger-Action Entries", show_header=True, header_style="bold magenta")
    trigger_actions_table.add_column("File", style="cyan")
    trigger_actions_table.add_column("Trigger Type", style="green")
    trigger_actions_table.add_column("Action Type", style="blue")
    trigger_actions_table.add_column("Name", style="yellow")
    
    # Add trigger files to table
    for trigger in sorted(triggers):
        try:
            data = json.loads(trigger.read_text())
            trigger_actions_table.add_row(
                trigger.name,
                data.get("trigger", {}).get("type", "Unknown"),
                data.get("action", {}).get("type", "Unknown"),
                data.get("trigger", {}).get("config", {}).get("name", "Unnamed")
            )
        except Exception as e:
            trigger_actions_table.add_row(
                trigger.name,
                "[red]Error[/red]",
                "[red]Error[/red]",
                f"[red]Failed to load: {str(e)}[/red]"
            )
    
    # Display table
    console.print(trigger_actions_table)
    
    # Log as simple list
    logger.info("Loaded trigger files: " + ", ".join(t.name for t in sorted(triggers)))

def get_trigger_schema(trigger_type: str) -> Dict[str, Any]:
    """Get schema for trigger type."""
    trigger_cls = get_trigger(trigger_type)
    # Get the config parameters from the __init__ method
    init_params = trigger_cls.__init__.__annotations__
    if 'config' in init_params:
        # Return a basic schema based on the config parameter type
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                # Add other common properties based on trigger type
            }
        }
    return {}

def get_action_schema(action_type: str) -> Dict[str, Any]:
    """Get schema for action type."""
    action_cls = get_action(action_type)
    # Get the config parameters from the __init__ method
    init_params = action_cls.__init__.__annotations__
    if 'config' in init_params:
        # Return a basic schema based on the config parameter type
        return {
            "type": "object",
            "properties": {
                # Add common properties based on action type
            }
        }
    return {}

def interactive_config_from_schema(schema, title: str) -> Dict[str, Any]:
    """Interactive prompt for configuration based on schema."""
    config = {}
    
    console.print(Panel(title, style="bold blue"))
    
    for field in schema.fields:
        if field.type == "string":
            value = Prompt.ask(
                field.description,
                default=str(field.default) if field.default is not None else None,
                show_default=field.default is not None
            )
            config[field.name] = value
        elif field.type == "integer":
            value = Prompt.ask(
                field.description,
                default=str(field.default) if field.default is not None else None,
                show_default=field.default is not None
            )
            config[field.name] = int(value)
        elif field.type == "array":
            if Confirm.ask(f"Add {field.description.lower()}?"):
                items = []
                while True:
                    if field.choices:
                        item = Prompt.ask(
                            f"Select {field.description.lower()} item",
                            choices=field.choices
                        )
                    else:
                        item = Prompt.ask(f"Enter {field.description.lower()} item")
                    items.append(item)
                    if not Confirm.ask("Add another?"):
                        break
                config[field.name] = items
            else:
                config[field.name] = field.default or []
    
    return config

def print_app_title():
    """Print the application title with Rich formatting."""
    title = Text("Triggered", style="bold blue")
    subtitle = Text("AI-powered triggers and actions", style="italic cyan")
    console.print(Panel(
        Text.assemble(title, "\n", subtitle),
        border_style="blue",
        padding=(1, 2)
    ))
    display_loaded_trigger_actions()

def display_available_tools(custom_tools_path: Optional[str] = None):
    """Display and log available tools in a nice table format."""
    from .registry import TOOL_REGISTRY
    from .tools import load_tools_from_module
    
    # Load custom tools if path provided
    if custom_tools_path:
        try:
            load_tools_from_module(custom_tools_path)
            console.print(f"[green]Loaded custom tools from: {custom_tools_path}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to load custom tools: {str(e)}[/red]")
            if not Confirm.ask("Would you like to try a different file?"):
                return
            new_path = prompt_for_custom_tools()
            if new_path:
                display_available_tools(new_path)
            return
    
    # Create table for tools
    tool_table = Table(title="Available Tools", show_header=True, header_style="bold magenta")
    tool_table.add_column("Type", style="cyan")
    tool_table.add_column("Description", style="green")
    tool_table.add_column("Source", style="yellow")
    tool_table.add_column("Input Schema", style="blue")
    
    # Add tools to table
    for tool_type in sorted(TOOL_REGISTRY.keys()):
        tool_cls = TOOL_REGISTRY[tool_type]
        description = tool_cls.description
        schema = tool_cls.args_schema.model_json_schema()
        source = "Custom" if custom_tools_path and tool_type in TOOL_REGISTRY else "Built-in"
        tool_table.add_row(
            tool_type,
            description,
            source,
            json.dumps(schema.get("properties", {}), indent=2)
        )
    
    # Display table
    console.print(tool_table)
    
    # Log as simple list
    logger.info("Available tools: " + ", ".join(sorted(TOOL_REGISTRY.keys())))

@app.command("add")
def add_trigger(
    trigger_type: Optional[str] = typer.Option(None, help="Type of trigger"),
    action_type: Optional[str] = typer.Option(None, help="Type of action"),
    trigger_config_path: Optional[Path] = typer.Option(None, help="Path to trigger JSON config"),
    action_config_path: Optional[Path] = typer.Option(None, help="Path to action JSON config"),
    log_level: str = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        callback=log_level_callback,
    ),
):
    """Create a new trigger-action file from configs or interactively."""
    print_app_title()
    
    # Interactive mode if no arguments provided
    if not any([trigger_type, action_type, trigger_config_path, action_config_path]):
        console.print(Panel("Interactive Trigger Creation", style="bold yellow"))
        
        # Select trigger type
        trigger_types = get_available_trigger_types()
        trigger_table = Table(title="Available Trigger Types", show_header=True, header_style="bold magenta")
        trigger_table.add_column("Type", style="cyan")
        trigger_table.add_column("Description", style="green")
        for t in trigger_types:
            trigger_table.add_row(t, f"{t.capitalize()} trigger")
        console.print(trigger_table)
        
        trigger_type = Prompt.ask(
            "Select trigger type",
            choices=trigger_types,
            default=trigger_types[0]
        )
        
        # Select action type
        action_types = get_available_action_types()
        action_table = Table(title="Available Action Types", show_header=True, header_style="bold magenta")
        action_table.add_column("Type", style="cyan")
        action_table.add_column("Description", style="green")
        for t in action_types:
            action_table.add_row(t, f"{t.capitalize()} action")
        console.print(action_table)
        
        action_type = Prompt.ask(
            "Select action type",
            choices=action_types,
            default=action_types[0]
        )
        
        # Show available tools if AI trigger or action is selected
        if trigger_type == "ai" or action_type == "ai_agent":
            custom_tools_path = prompt_for_custom_tools()
            display_available_tools(custom_tools_path)
        
        # Get configurations interactively using schemas
        trigger_schema = get_trigger_config_schema(trigger_type)
        action_schema = get_action_config_schema(action_type)
        
        trigger_config = interactive_config_from_schema(
            trigger_schema,
            f"Configuring {trigger_type} trigger"
        )
        action_config = interactive_config_from_schema(
            action_schema,
            f"Configuring {action_type} action"
        )
    else:
        # Non-interactive mode
        if not all([trigger_type, action_type, trigger_config_path, action_config_path]):
            console.print("[red]Error: All arguments are required in non-interactive mode[/red]")
            return
            
        trigger_config = json.loads(trigger_config_path.read_text())
        action_config = json.loads(action_config_path.read_text())

    # Create and save trigger
    ta = TriggerAction(
        trigger=TriggerDefinition(type=trigger_type, config=trigger_config),
        action=ActionDefinition(type=action_type, config=action_config),
    )
    file_path = TRIGGER_ACTIONS_DIR / f"{ta.id}.json"
    file_path.write_text(
        json.dumps(ta.dict(), indent=2),
    )
    console.print(
        Panel(
            f"[bold green]Created trigger file:[/bold green] {file_path}\n"
            f"Auth key: {ta.auth_key}",
            title="Success",
            border_style="green"
        )
    )

class ServerMode(str, Enum):
    standalone = "standalone"
    distributed = "distributed"

@app.command()
def start(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind the server to"
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind the server to"
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload on code changes"
    ),
    mode: ServerMode = typer.Option(
        "standalone",
        "--mode",
        "-m",
        help="Startup mode: 'standalone' (default) or 'distributed' (with Celery worker)"
    ),
    log_level: str = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        callback=log_level_callback,
    ),
):
    """Start the Triggered server with optional Celery worker."""
    print_app_title()
    
    # Create a panel for startup information
    startup_info = Panel(
        Text.assemble(
            Text("Triggered Server", style="bold blue"),
            "\n\n",
            Text("Server Configuration:", style="bold yellow"),
            "\n",
            Text("🌐 Host: ", style="cyan"),
            Text(host, style="green"),
            "\n",
            Text("🔌 Port: ", style="cyan"),
            Text(str(port), style="green"),
            "\n",
            Text("🔄 Auto-reload: ", style="cyan"),
            Text(str(reload), style="green"),
            "\n\n",
            Text("Available Modes:", style="bold yellow"),
            "\n",
            Text("🚀 standalone (default): ", style="cyan"),
            Text("Single process mode - everything runs in one process", style="green"),
            "\n",
            Text("⚡️ distributed: ", style="cyan"),
            Text("Multi-process mode with separate Celery worker", style="green"),
            "\n\n",
            Text("Current Mode: ", style="bold yellow"),
            Text(mode, style="bold green"),
            "\n\n",
            Text("To switch modes:", style="bold yellow"),
            "\n",
            Text("  triggered start --mode standalone", style="cyan"),
            "\n",
            Text("  triggered start --mode distributed", style="cyan"),
            "\n\n",
            Text("Note: ", style="bold yellow"),
            Text("In 'distributed' mode, you need to run the worker in a separate terminal:", style="green"),
            "\n",
            Text("  triggered worker", style="cyan")
        ),
        title="Startup Information",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(startup_info)
    
    if mode == ServerMode.distributed:
        # In distributed mode, show instructions for worker
        console.print("\n[yellow]Please run the worker in a separate terminal:[/yellow]")
        console.print("  [cyan]triggered worker[/cyan]")
    
    # Start the server in both modes
    console.print(f"\n[bold blue]Starting server in {mode.value} mode...[/bold blue]")
    os.environ["TRIGGERED_START_WORKER"] = "false"
    uvicorn.run(
        "triggered.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@app.command()
def ls(
    log_level: str = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        callback=log_level_callback,
    ),
):
    """List all available triggers in the triggers directory."""
    print_app_title()
    
    if not TRIGGER_ACTIONS_DIR.exists():
        console.print("[yellow]No triggers directory found.[/yellow]")
        return

    triggers = list(TRIGGER_ACTIONS_DIR.glob("*.json"))
    if not triggers:
        console.print("[yellow]No triggers found.[/yellow]")
        return

    trigger_table = Table(title="Available Triggers", show_header=True, header_style="bold magenta")
    trigger_table.add_column("Name", style="cyan")
    trigger_table.add_column("Type", style="green")
    trigger_table.add_column("Action", style="blue")
    
    for trigger in sorted(triggers):
        data = json.loads(trigger.read_text())
        trigger_table.add_row(
            trigger.stem,
            data["trigger_type"],
            data["action_type"]
        )
    
    console.print(trigger_table)


# ---------------------------------------------------------------------------
# run-trigger command
# ---------------------------------------------------------------------------


@app.command("run")
def run_trigger_once(
    path: str = typer.Argument(
        None,
        help="Path to the trigger-action JSON file",
        autocompletion=get_json_completion,
    ),
    log_level: str = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        callback=log_level_callback,
    ),
):
    """Execute a trigger-action JSON definition one time.

    The path can be either absolute or relative to the trigger_actions directory.
    Example:
        triggered run trigger_actions/ai-ps.json
        triggered run ai-ps.json
    """
    if not path:
        console.print("[red]Error: Missing required argument 'path'[/red]")
        console.print("\n[bold]Usage:[/bold]")
        console.print("  triggered run <path>")
        console.print("\n[bold]Arguments:[/bold]")
        console.print("  path    Path to the trigger-action JSON file")
        console.print("\n[bold]Examples:[/bold]")
        console.print("  triggered run trigger_actions/ai-ps.json")
        console.print("  triggered run ai-ps.json")
        console.print("\n[bold]Available JSON files:[/bold]")
        display_loaded_trigger_actions()
        raise typer.Exit(1)

    print_app_title()
    
    # Convert string path to Path object
    path_obj = Path(path)
    
    # First try TRIGGER_ACTIONS_DIR
    if not path_obj.is_absolute():
        dest_path = TRIGGER_ACTIONS_DIR / path_obj
        if dest_path.exists():
            console.print(f"[bold blue]Running trigger from trigger_actions:[/bold blue] {dest_path}")
            asyncio.run(_execute_ta_once(dest_path))
            return

    # Then try EXAMPLES_DIR
    if not path_obj.is_absolute():
        dest_path = EXAMPLES_DIR / path_obj
        if dest_path.exists():
            console.print(f"[bold blue]Running trigger from examples:[/bold blue] {dest_path}")
            asyncio.run(_execute_ta_once(dest_path))
            return

    # If we get here, the file wasn't found in either location
    console.print(f"[red]Error: Trigger-action entry not found: {path_obj}[/red]")
    console.print(f"Checked in:")
    console.print(f"  - {TRIGGER_ACTIONS_DIR}")
    console.print(f"  - {EXAMPLES_DIR}")
    console.print("\n[bold]Available JSON files:[/bold]")
    display_loaded_trigger_actions()
    raise typer.Exit(1)


# ---------------------------------------------------------------------------
# internal helper
# ---------------------------------------------------------------------------


async def _execute_ta_once(ta_path: Path):
    """Load a TriggerAction JSON file and execute once synchronously."""
    from .registry import get_trigger
    from .core import TriggerAction

    data = json.loads(ta_path.read_text())
    ta = TriggerAction.model_validate(data)  # type: ignore[attr-defined]

    trigger_cls = get_trigger(ta.trigger.type)
    trigger = trigger_cls(ta.trigger.config)

    ctx = None
    if hasattr(trigger, "check"):
        # Create context with configuration
        ctx = await trigger.check()
        if ctx:
            ctx.params.update(ta.params)
    
    if ctx is None:
        log_trigger_check(ta.trigger.config.get("name", "Unknown"), False, "Trigger not fired")
        return

    triggered = ctx.data.get("trigger", False)
    reason = ctx.data.get("reason", "No reason provided")
    log_trigger_check(ta.trigger.config.get("name", "Unknown"), triggered, reason)
        
    if triggered:
        await ta.execute_action(ctx)


@app.command("check")
def check_components(
    log_level: str = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        callback=log_level_callback,
    ),
):
    """Display available triggers, actions, and their configurations."""
    print_app_title()
    display_loaded_actions()
    display_loaded_trigger_actions()


@app.command()
def worker():
    """Start the Celery worker for processing trigger actions."""
    from .queue import app as celery_app
    from .logging_config import setup_logging
    
    setup_logging()
    logger.info("Starting Celery worker...")
    
    # Start the Celery worker
    celery_app.worker_main(['worker', '--loglevel=INFO', '--pool=solo', '-Q', 'triggered'])

@app.command()
def enable(
    path: str = typer.Argument(
        None,
        help="Path to the trigger-action JSON file",
        autocompletion=get_json_completion,
    ),
    log_level: str = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        callback=log_level_callback,
    ),
):
    """Enable a trigger by moving it from disabled_trigger_actions to trigger_actions."""
    if not path:
        console.print("[red]Error: Missing required argument 'path'[/red]")
        console.print("\n[bold]Usage:[/bold]")
        console.print("  triggered enable <path>")
        raise typer.Exit(1)

    print_app_title()
    
    # Convert string path to Path object
    path_obj = Path(path)
    disabled_dir = Path("disabled_trigger_actions")
    
    # Check if file exists in disabled directory
    if not path_obj.is_absolute():
        source_path = disabled_dir / path_obj
        if not source_path.exists():
            console.print(f"[red]Error: Trigger not found in disabled directory: {path_obj}[/red]")
            raise typer.Exit(1)
            
        # Move file to trigger_actions directory
        dest_path = TRIGGER_ACTIONS_DIR / path_obj.name
        try:
            source_path.rename(dest_path)
            console.print(f"[green]Successfully enabled trigger: {path_obj.name}[/green]")
            logger.info(f"Enabled trigger: {path_obj.name}")
        except Exception as e:
            console.print(f"[red]Error enabling trigger: {str(e)}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[red]Error: Please provide a relative path[/red]")
        raise typer.Exit(1)

@app.command()
def disable(
    path: str = typer.Argument(
        None,
        help="Path to the trigger-action JSON file",
        autocompletion=get_json_completion,
    ),
    log_level: str = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        callback=log_level_callback,
    ),
):
    """Disable a trigger by moving it from trigger_actions to disabled_trigger_actions."""
    if not path:
        console.print("[red]Error: Missing required argument 'path'[/red]")
        console.print("\n[bold]Usage:[/bold]")
        console.print("  triggered disable <path>")
        raise typer.Exit(1)

    print_app_title()
    
    # Convert string path to Path object
    path_obj = Path(path)
    disabled_dir = Path("disabled_trigger_actions")
    
    # First try TRIGGER_ACTIONS_DIR
    if not path_obj.is_absolute():
        source_path = TRIGGER_ACTIONS_DIR / path_obj
        if source_path.exists():
            # Move file to disabled directory
            dest_path = disabled_dir / path_obj.name
            try:
                source_path.rename(dest_path)
                console.print(f"[green]Successfully disabled trigger: {path_obj.name}[/green]")
                logger.info(f"Disabled trigger: {path_obj.name}")
                return
            except Exception as e:
                console.print(f"[red]Error disabling trigger: {str(e)}[/red]")
                raise typer.Exit(1)

    # Then try EXAMPLES_DIR
    if not path_obj.is_absolute():
        source_path = EXAMPLES_DIR / path_obj
        if source_path.exists():
            # Move file to disabled directory
            dest_path = disabled_dir / path_obj.name
            try:
                source_path.rename(dest_path)
                console.print(f"[green]Successfully disabled trigger: {path_obj.name}[/green]")
                logger.info(f"Disabled trigger: {path_obj.name}")
                return
            except Exception as e:
                console.print(f"[red]Error disabling trigger: {str(e)}[/red]")
                raise typer.Exit(1)

    # If we get here, the file wasn't found
    console.print(f"[red]Error: Trigger not found: {path_obj}[/red]")
    console.print(f"Checked in:")
    console.print(f"  - {TRIGGER_ACTIONS_DIR}")
    console.print(f"  - {EXAMPLES_DIR}")
    raise typer.Exit(1)

if __name__ == "__main__":  # pragma: no cover
    app() 