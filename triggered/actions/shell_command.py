import asyncio
import logging

from ..core import Action, TriggerContext, BaseConfig
from ..registry import register_action
from ..config_schema import ConfigSchema, ConfigField
from pydantic import Field

logger = logging.getLogger(__name__)


class ShellCommandConfig(BaseConfig):
    """Configuration model for shell command action."""
    command: str = Field(description="Shell command to execute (can use {var} for variable substitution)")


@register_action("shell")
class ShellCommandAction(Action):
    """Action that runs a shell command. In production this should run
    inside a sandboxed container. Here we simply spawn a subprocess.

    Config keys:
    - command: str
    """
    config_model = ShellCommandConfig

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="command",
                type="string",
                description="Shell command to execute (can use {var} for variable substitution)",
                required=True
            )
        ])

    async def execute(self, ctx: TriggerContext) -> dict:  # noqa: D401
        command: str = self.config.command.format(**ctx.data)
        logger.debug("Executing shell command: %s", command)
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stderr:
            logger.error("Shell stderr: %s", stderr.decode())
        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "returncode": proc.returncode,
        } 