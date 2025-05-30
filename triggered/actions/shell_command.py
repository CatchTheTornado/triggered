import asyncio
import logging

from ..core import Action, TriggerContext
from ..registry import register_action

logger = logging.getLogger(__name__)


@register_action("shell")
class ShellCommandAction(Action):
    """Action that runs a shell command. In production this should run
    inside a sandboxed container. Here we simply spawn a subprocess.

    Config keys:
    - command: str
    """

    async def execute(self, ctx: TriggerContext) -> dict:  # noqa: D401
        command: str = self.config["command"].format(**ctx.data)
        logger.info("Executing shell command: %s", command)
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        logger.info("Shell stdout: %s", stdout.decode())
        if stderr:
            logger.error("Shell stderr: %s", stderr.decode())
        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "returncode": proc.returncode,
        } 