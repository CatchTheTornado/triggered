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
    # This should be implemented to return actual trigger types from registry
    return ["ai", "cron", "webhook", "folder"]

def get_available_action_types() -> list[str]:
    """Get list of available action types."""
    # This should be implemented to return actual action types from registry
    return ["shell", "webhook_call", "ai_agent", "python_script", "typescript_script"]

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

def interactive_trigger_config(trigger_type: str) -> Dict[str, Any]:
    """Interactive prompt for trigger configuration."""
    config = {}
    
    console.print(Panel(f"Configuring {trigger_type} trigger", style="bold blue"))
    
    if trigger_type == "ai":
        config["name"] = Prompt.ask("Trigger name")
        config["model"] = Prompt.ask("Model", default="ollama/llama3.1")
        config["api_base"] = Prompt.ask("API base", default="http://localhost:11434")
        config["interval"] = int(Prompt.ask("Check interval (seconds)", default="60"))
        config["prompt"] = Prompt.ask("AI prompt")
        config["tools"] = []
        if Confirm.ask("Add tools?"):
            while True:
                tool_type = Prompt.ask("Tool type", choices=["random_number"])
                config["tools"].append({"type": tool_type})
                if not Confirm.ask("Add another tool?"):
                    break
    elif trigger_type == "cron":
        config["name"] = Prompt.ask("Trigger name")
        config["expression"] = Prompt.ask("Cron schedule (e.g. '*/5 * * * *')")
    elif trigger_type == "webhook":
        config["name"] = Prompt.ask("Trigger name")
        config["route"] = Prompt.ask("Webhook path", default="/webhook")
    elif trigger_type == "folder":
        config["name"] = Prompt.ask("Trigger name")
        config["path"] = Prompt.ask("Folder to monitor")
        config["interval"] = int(Prompt.ask("Check interval (seconds)", default="5"))
        config["patterns"] = Prompt.ask("File patterns (comma-separated)", default="*")
    
    return config

def interactive_action_config(action_type: str) -> Dict[str, Any]:
    """Interactive prompt for action configuration."""
    config = {}
    
    console.print(Panel(f"Configuring {action_type} action", style="bold green"))
    
    if action_type == "shell":
        config["command"] = Prompt.ask("Shell command to execute")
    elif action_type == "webhook_call":
        config["url"] = Prompt.ask("HTTP URL")
        config["payload"] = Prompt.ask("Payload template (optional)", default="{}")
        config["headers"] = {}
        if Confirm.ask("Add headers?"):
            while True:
                key = Prompt.ask("Header name")
                value = Prompt.ask("Header value")
                config["headers"][key] = value
                if not Confirm.ask("Add another header?"):
                    break
    elif action_type == "ai_agent":
        config["model"] = Prompt.ask("Model name", default="ollama/llama3.1")
        config["prompt"] = Prompt.ask("AI prompt")
        config["tools"] = []
        if Confirm.ask("Add tools?"):
            while True:
                tool_type = Prompt.ask("Tool type", choices=["random_number"])
                config["tools"].append({"type": tool_type})
                if not Confirm.ask("Add another tool?"):
                    break
    elif action_type == "python_script":
        config["path"] = Prompt.ask("Path to Python script")
    elif action_type == "typescript_script":
        config["path"] = Prompt.ask("Path to TypeScript script")
    
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
        
        # Get configurations interactively
        trigger_config = interactive_trigger_config(trigger_type)
        action_config = interactive_action_config(action_type)
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