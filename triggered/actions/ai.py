import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..core import Action, TriggerContext
from ..registry import register_action
from ..config_schema import ConfigSchema, ConfigField
from ..models import get_model
from ..tools import get_tools, load_tools_from_module

logger = logging.getLogger(__name__)

class AIConfig(BaseModel):
    """Configuration for AI action."""
    name: str
    prompt: str
    model: str = "openai/gpt-4o"
    api_base: str = "https://api.openai.com/v1"
    tools: list = []
    custom_tools_path: Optional[str] = None

@register_action("ai")
class AIAction(Action):
    """Action that uses AI to generate responses."""

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="name",
                type="string",
                description="Action name",
                required=True
            ),
            ConfigField(
                name="prompt",
                type="string",
                description="AI prompt (can use ${var} for variable substitution from env vars, params, or trigger data)",
                required=True
            ),
            ConfigField(
                name="model",
                type="string",
                description="Model to use",
                default="openai/gpt-4o",
                required=False
            ),
            ConfigField(
                name="api_base",
                type="string",
                description="API base URL",
                default="",
                required=False
            ),
            ConfigField(
                name="tools",
                type="array",
                description="List of tools to use",
                default=[],
                required=False
            ),
            ConfigField(
                name="custom_tools_path",
                type="string",
                description="Path to custom tools module",
                required=False
            )
        ])

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.config = AIConfig(**config)
        self.model = get_model(model=self.config.model, api_base=self.config.api_base)
        self.tools = get_tools(self.config.tools)
        if self.config.custom_tools_path:
            load_tools_from_module(self.config.custom_tools_path)

    async def execute(self, ctx: TriggerContext) -> Dict[str, Any]:
        """Execute the AI action with the given context."""
        try:
            # Replace variables in the prompt with context data
            prompt = self.config.prompt
            
            # Replace environment variables
            prompt = ctx.resolve_env_vars(prompt)
            
            # Replace params from config
            for key, value in ctx.params.items():
                prompt = prompt.replace(f"${{{key}}}", str(value))
            
            # Replace trigger data
            for key, value in ctx.data.items():
                prompt = prompt.replace(f"${{{key}}}", str(value))

            # Call the model
            response = await self.model.ainvoke(prompt, tools=self.config.tools)
            logger.info(f"AI response: {response}")
            return {"response": response}
        except Exception as e:
            logger.error(f"Error executing AI action: {str(e)}")
            return {"error": str(e)} 