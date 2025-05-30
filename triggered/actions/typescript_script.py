import asyncio
import logging
from pathlib import Path

from ..core import Action, TriggerContext
from ..registry import register_action

logger = logging.getLogger(__name__)


@register_action("typescript_script")
class TypeScriptScriptAction(Action):
    """Action that runs a TypeScript script inside a Docker container."""

    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        script_path = Path(self.config["path"]).expanduser().resolve()
        logger.info("Executing TypeScript script in Docker: %s", script_path)
        # Build docker command (assumes docker is installed and daemon running)
        docker_cmd = (
            "docker run --rm "
            f"-v {script_path.parent}:/app "
            "-w /app node:20-alpine "
            "sh -c \"npm install -g ts-node typescript >/dev/null 2>&1 && "
            f"ts-node {script_path.name}\""
        )
        proc = await asyncio.create_subprocess_shell(
            docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        logger.info("TypeScript stdout: %s", stdout.decode())
        if stderr:
            logger.error("TypeScript stderr: %s", stderr.decode()) 