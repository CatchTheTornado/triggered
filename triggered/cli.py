import json
from pathlib import Path

import typer
import uvicorn
from rich import print

from .core import TriggerAction


app = typer.Typer(help="Triggered CLI")

TRIGGER_DIR = Path("triggers")
TRIGGER_DIR.mkdir(exist_ok=True)


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


if __name__ == "__main__":  # pragma: no cover
    app() 