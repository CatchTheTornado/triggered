import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..core import Action, TriggerContext
from ..models import get_model
from ..registry import register_action
from ..tools import get_tools, load_tools_from_module
from ..config_schema import ConfigSchema, ConfigField
from ..logging_config import logger


class AIConfig(BaseModel):
    """Configuration for AI action."""
    name: str
    prompt: str
    model: str = "openai/gpt-4o"
    api_base: str = ""
    tools: list[str] = []
    custom_tools_path: Optional[str] = None


@register_action("ai")
class AIAction(Action):
    """Action that uses AI to execute tasks."""

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
                description="AI prompt",
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
        self.config_model = AIConfig(**config)
        self.model = get_model(
            model=self.config_model.model,
            api_base=self.config_model.api_base
        )
        self.tools = get_tools(self.config_model.tools)
        if self.config_model.custom_tools_path:
            load_tools_from_module(self.config_model.custom_tools_path)

    async def execute(self, ctx: TriggerContext) -> None:
        """Execute the AI action."""
        response = await self.model.ainvoke(
            self.config_model.prompt,
            tools=self.config_model.tools
        )
        logger.debug("AI Agent response: %s", response)

        # Store the result in the context for downstream actions
        return response

        # Optionally pass result downstream? Could set ctx.data["result"] 