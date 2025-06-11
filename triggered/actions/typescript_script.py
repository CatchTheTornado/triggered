import asyncio
import logging
import json
import os
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
    
    The script should export a default function that receives trigger data, params, and env.
    Example:
    ```typescript
    interface TriggerData {
        trigger: boolean;
        reason: string;
    }
    
    interface ScriptContext {
        data: TriggerData;
        params: Record<string, any>;
        env: Record<string, string>;
    }
    
    export default function(context: ScriptContext) {
        console.log(`Triggered: ${context.data.trigger}`);
        console.log(`Params: ${JSON.stringify(context.params)}`);
        console.log(`Env: ${JSON.stringify(context.env)}`);
    }
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

    async def execute(self, ctx: TriggerContext) -> dict:  # noqa: D401
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
        
        # Create a temporary file with the script context
        context_file = script_path.parent / "script_context.json"
        with open(context_file, "w") as f:
            json.dump({
                "data": ctx.data,
                "params": ctx.params,
                "env": dict(os.environ)
            }, f)
        
        # Create a tsconfig.json file
        tsconfig_file = script_path.parent / "tsconfig.json"
        with open(tsconfig_file, "w") as f:
            json.dump({
                "compilerOptions": {
                    "target": "ES2020",
                    "module": "CommonJS",
                    "moduleResolution": "node",
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True,
                    "strict": True,
                    "types": ["node"]
                }
            }, f, indent=2)
        
        # Create a wrapper script that loads the context and runs the main script
        wrapper_script = script_path.parent / "wrapper.ts"
        with open(wrapper_script, "w") as f:
            f.write("""
/// <reference types="node" />

// Load script context
const context = require('./script_context.json');
console.log('Debug - Script context:', JSON.stringify(context, null, 2));

// Run the main script with context
const script = require('./%s');
if (typeof script.default === 'function') {
    script.default(context);
} else {
    console.error('Script must export a default function that accepts context');
    process.exit(1);
}
""" % script_path.name)
        
        # Build docker command (assumes docker is installed and daemon running)
        docker_cmd = (
            "docker run --rm "
            f"-v {script_path.parent}:/app "
            "-w /app node:20-alpine "
            "sh -c \""
            "npm install -g ts-node typescript @types/node && "
            "export PATH=$PATH:/usr/local/bin && "
            "ts-node --project tsconfig.json wrapper.ts"
            "\""
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
                logger.info("TypeScript stderr: %s", stderr.decode())
            
            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "returncode": proc.returncode,
            }
        finally:
            # Clean up the temporary files
            if context_file.exists():
                context_file.unlink()
            if wrapper_script.exists():
                wrapper_script.unlink()
            if tsconfig_file.exists():
                tsconfig_file.unlink() 