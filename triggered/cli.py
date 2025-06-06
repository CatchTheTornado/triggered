import json
from pathlib import Path
import asyncio

import typer
import uvicorn
from rich import print

from .core import TriggerAction


# ---------------------------------------------------------------------------
# Typer app setup
# ---------------------------------------------------------------------------

app = typer.Typer(help="Triggered CLI")

TRIGGER_DIR = Path("triggers")
TRIGGER_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Paths & helpers
# ---------------------------------------------------------------------------


@app.command()
def add_trigger(
    trigger_type: str = typer.Option(..., prompt=True),
    action_type: str = typer.Option(..., prompt=True),
    trigger_config_path: Path = typer.Option(
        ..., prompt="Path to trigger JSON config",
    ),
    action_config_path: Path = typer.Option(
        ..., prompt="Path to action JSON config",
    ),
):
    """Create a new trigger-action file from configs."""
    trigger_config = json.loads(trigger_config_path.read_text())
    action_config = json.loads(action_config_path.read_text())

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
    print(
        f"[bold green]Created trigger file:[/bold green] {file_path}\n"
        f"Auth key: {ta.auth_key}",
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