import json
from pathlib import Path
import asyncio
from typing import Optional, Dict, Any

import typer
import uvicorn
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from pydantic import BaseModel

from .core import TriggerAction
from .registry import get_trigger, get_action
from .config_schema import get_trigger_config_schema, get_action_config_schema


# ---------------------------------------------------------------------------
# Typer app setup
# ---------------------------------------------------------------------------

app = typer.Typer(help="Triggered CLI")
console = Console()

TRIGGER_DIR = Path("triggers")
TRIGGER_DIR.mkdir(exist_ok=True)


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

@app.command("add")
def add_trigger(
    trigger_type: Optional[str] = typer.Option(None, help="Type of trigger"),
    action_type: Optional[str] = typer.Option(None, help="Type of action"),
    trigger_config_path: Optional[Path] = typer.Option(None, help="Path to trigger JSON config"),
    action_config_path: Optional[Path] = typer.Option(None, help="Path to action JSON config"),
):
    """Create a new trigger-action file from configs or interactively."""
    
    # Interactive mode if no arguments provided
    if not any([trigger_type, action_type, trigger_config_path, action_config_path]):
        console.print(Panel("Interactive Trigger Creation", style="bold yellow"))
        
        # Select trigger type
        trigger_types = get_available_trigger_types()
        trigger_table = Table(title="Available Trigger Types")
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
        action_table = Table(title="Available Action Types")
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
        trigger_type=trigger_type,
        trigger_config=trigger_config,
        action_type=action_type,
        action_config=action_config,
    )
    file_path = TRIGGER_DIR / f"{ta.id}.json"
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


@app.command()
def server(
    host: str = "0.0.0.0",  # noqa: WPS110
    port: int = 8000,
    reload: bool = False,
):
    """Run FastAPI server."""
    uvicorn.run("triggered.server:app", host=host, port=port, reload=reload)


@app.command()
def ls():
    """List all available triggers in the triggers directory."""
    if not TRIGGER_DIR.exists():
        print("[yellow]No triggers directory found.[/yellow]")
        return

    triggers = list(TRIGGER_DIR.glob("*.json"))
    if not triggers:
        print("[yellow]No triggers found.[/yellow]")
        return

    print("[bold]Available triggers:[/bold]")
    for trigger in sorted(triggers):
        print(f"  • {trigger.name}")


# ---------------------------------------------------------------------------
# run-trigger command
# ---------------------------------------------------------------------------


@app.command("run")
def run_trigger_once(path: str = typer.Argument(...)):
    """Execute a trigger-action JSON definition one time.

    The path can be either absolute or relative to the triggers directory.
    Example:
        triggered run triggers/ai-ps.json
        triggered run ai-ps.json
    """
    # Convert string path to Path object
    path_obj = Path(path)
    
    # If path is relative and doesn't start with 'triggers/', look in triggers directory
    if not path_obj.is_absolute() and not str(path_obj).startswith('triggers/'):
        path_obj = TRIGGER_DIR / path_obj

    if not path_obj.exists():
        print(f"[red]Error: Trigger file not found: {path_obj}[/red]")
        return

    asyncio.run(_execute_ta_once(path_obj))


# ---------------------------------------------------------------------------
# internal helper
# ---------------------------------------------------------------------------


async def _execute_ta_once(ta_path: Path):
    """Load a TriggerAction JSON file and execute once synchronously."""

    from .registry import get_trigger, get_action
    from .core import TriggerAction

    data = json.loads(ta_path.read_text())
    ta = TriggerAction.model_validate(data)  # type: ignore[attr-defined]

    trigger_cls = get_trigger(ta.trigger_type)
    action_cls = get_action(ta.action_type)

    trigger = trigger_cls(ta.trigger_config)
    action = action_cls(ta.action_config)

    ctx = None
    if hasattr(trigger, "check"):
        ctx = await trigger.check()
    
    if ctx is None:
        print("Trigger not fired")
        return

    if not ctx.data.get("trigger", False):
        reason = ctx.data.get("reason", "No reason provided")
        print("Trigger skipped –", reason)
        print("LLM raw:", ctx.data.get("raw", ""))
        return

    print("Reason:", ctx.data.get("reason", ""))
    print("LLM raw:", ctx.data.get("raw", ""))
    result = await action.execute(ctx)
    if result:
        print("Result:")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":  # pragma: no cover
    app() 