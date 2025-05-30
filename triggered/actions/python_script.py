import asyncio
import logging
from pathlib import Path

from ..core import Action, TriggerContext
from ..registry import register_action

logger = logging.getLogger(__name__)


@register_action("python_script")
class PythonScriptAction(Action):
    """Action that runs a Python script file."""

    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        script_path = Path(self.config["path"]).expanduser().resolve()
        logger.info("Executing python script: %s", script_path)
        proc = await asyncio.create_subprocess_exec(
            "python",
            str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        logger.info("Script stdout: %s", stdout.decode())
        if stderr:
            logger.error("Script stderr: %s", stderr.decode()) 