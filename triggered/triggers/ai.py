import asyncio
import json
import logging
from typing import Any, Dict, Optional
from ..core import Trigger, TriggerContext
from ..models import get_model
from ..tools import get_tools, load_tools_from_module
from ..registry import register_trigger
from ..config_schema import ConfigSchema, ConfigField

logger = logging.getLogger(__name__)


@register_trigger("ai")
class AITrigger(Trigger):
    """Trigger that uses AI to make decisions."""

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this trigger type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="name",
                type="string",
                description="Trigger name",
                required=True
            ),
            ConfigField(
                name="model",
                type="string",
                description="Model to use",
                default="ollama/llama3.1",
                required=True
            ),
            ConfigField(
                name="api_base",
                type="string",
                description="API base URL",
                default="http://localhost:11434",
                required=True
            ),
            ConfigField(
                name="interval",
                type="integer",
                description="Check interval in seconds",
                default=60,
                required=True
            ),
            ConfigField(
                name="prompt",
                type="string",
                description="AI prompt",
                required=True
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
        self.model = get_model(model=config.get("model"), api_base=config.get("api_base"))
        self.interval = config.get("interval", 60)
        self.prompt = config.get("prompt", "")
        self.tool_configs = config.get("tools", [])
        self.tools = get_tools(self.tool_configs)
        custom_tools_path = config.get("custom_tools_path")
        if custom_tools_path:
            load_tools_from_module(custom_tools_path)

    async def check(self) -> Optional[TriggerContext]:
        """Check if the trigger condition is met."""
        try:
            general_instruction = "You are the decision maker if to run the user action or not. You must return a JSON response with the following schema: { \"trigger\": <true|false>, \"reason\": \"<short explanation why you made the decision>\" }. Always response in this and only this format. Use the tools if provided and suitable to make the decision. Here is the user defined criteria for you to consider:"
            full_prompt = f"{general_instruction}\n\n{self.prompt}"
            response = await self.model.ainvoke(full_prompt, tools=self.tool_configs)
            try:
                obj = json.loads(response)
                if not isinstance(obj, dict) or "trigger" not in obj:
                    logger.error("Model response is not a valid JSON or missing 'trigger' field: %s", response)
                    return None
                if obj.get("trigger"):
                    return TriggerContext(trigger_name=self.name, data=obj)
            except json.JSONDecodeError:
                logger.error("Failed to parse model response as JSON: %s", response)
        except Exception as e:
            logger.error("Error checking AI trigger: %s", str(e))
        return None

    async def watch(self, queue_put) -> None:
        """Watch for trigger conditions."""
        while True:
            try:
                ctx = await self.check()
                if ctx is not None:
                    await queue_put(ctx)
            except Exception as e:
                logger.error("Error in AI trigger watch loop: %s", str(e))
            await asyncio.sleep(self.interval) 