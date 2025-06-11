import asyncio
import logging
import json
from pathlib import Path

from ..core import Action, TriggerContext, BaseConfig
from ..registry import register_action
from ..config_schema import ConfigSchema, ConfigField
from pydantic import Field

logger = logging.getLogger(__name__)


class TypeScriptScriptConfig(BaseConfig):
    """Configuration model for TypeScript script action."""
    path: str = Field(description="Path to the TypeScript script file (supports ${var} substitution)")


@register_action("typescript_script")
class TypeScriptScriptAction(Action):
    """Action that runs a TypeScript script inside a Docker container.
    
    The script can access trigger data through the global `triggerData` variable.
    Example:
    ```typescript
    interface TriggerData {
        number: number;
        message: string;
    }
    
    declare const triggerData: TriggerData;
    console.log(`Number: ${triggerData.number}`);
    ```
    """
    config_model = TypeScriptScriptConfig

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="path",
                type="string",
                description="Path to the TypeScript script file (supports ${var} substitution)",
                required=True
            )
        ])

    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        # First resolve environment variables
        script_path = ctx.resolve_env_vars(self.config.path)
        
        # Then resolve params and data
        try:
            script_path = script_path.format(**ctx.params, **ctx.data)
        except KeyError as e:
            # If a variable is not found, keep the original ${var} in the string
            logger.warning(f"Variable {e} not found in context")
            
        script_path = Path(script_path).expanduser().resolve()
        logger.debug("Executing TypeScript script in Docker: %s", script_path)
        
        # Create a temporary file with the trigger data
        trigger_data_file = script_path.parent / "trigger_data.json"
        with open(trigger_data_file, "w") as f:
            json.dump(ctx.data, f)
        
        # Create a wrapper script that loads the trigger data and runs the main script
        wrapper_script = script_path.parent / "wrapper.ts"
        with open(wrapper_script, "w") as f:
            f.write("""
// Load trigger data
const triggerData = require('./trigger_data.json');

// Run the main script
require('./%s');
""" % script_path.name)
        
        # Build docker command (assumes docker is installed and daemon running)
        docker_cmd = (
            "docker run --rm "
            f"-v {script_path.parent}:/app "
            "-w /app node:20-alpine "
            "sh -c \"npm install -g ts-node typescript >/dev/null 2>&1 && "
            f"ts-node wrapper.ts\""
        )
        
        try:
            proc = await asyncio.create_subprocess_shell(
                docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if stdout:
                logger.info("TypeScript stdout: %s", stdout.decode())
            if stderr:
                logger.error("TypeScript stderr: %s", stderr.decode())
            if proc.returncode != 0:
                raise RuntimeError(f"TypeScript script failed with return code {proc.returncode}")
        finally:
            # Clean up the temporary files
            if trigger_data_file.exists():
                trigger_data_file.unlink()
            if wrapper_script.exists():
                wrapper_script.unlink() 