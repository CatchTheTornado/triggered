import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple
from ..core import Trigger, TriggerContext
from ..models import get_model
from ..tools import get_tools, load_tools_from_module
from ..registry import register_trigger
from ..config_schema import ConfigSchema, ConfigField

logger = logging.getLogger(__name__)


def extract_json_from_response(response: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Extract JSON from a model response that might be wrapped in markdown or other formatting.
    Returns a tuple of (parsed_json, error_message).
    """
    try:
        # First try direct JSON parsing
        return json.loads(response), None
    except json.JSONDecodeError:
        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
        if not json_match:
            # If no markdown block found, try to find any JSON object
            json_match = re.search(r'\{[\s\S]*?\}', response)
        
        if json_match:
            try:
                json_str = json_match.group(1) if '```' in response else json_match.group(0)
                # Clean up the string
                json_str = re.sub(r'\s+', ' ', json_str)
                return json.loads(json_str), None
            except json.JSONDecodeError:
                return None, f"Failed to parse extracted JSON: {response}"
        return None, f"No valid JSON object found in response: {response}"


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
                default="openai/gpt-4o",
                required=True
            ),
            ConfigField(
                name="api_base",
                type="string",
                description="API base URL",
                default="",
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
            
            obj, error = extract_json_from_response(response)
            if error:
                logger.error(error)
                return TriggerContext(trigger_name=self.name, data={"trigger": False, "reason": f"Error parsing response: {error}"})
                
            if not isinstance(obj, dict) or "trigger" not in obj:
                error_msg = "Model response is not a valid JSON or missing 'trigger' field"
                logger.error(f"{error_msg}: {response}")
                return TriggerContext(trigger_name=self.name, data={"trigger": False, "reason": error_msg})
                
            # Always return a context, even when not triggered
            return TriggerContext(trigger_name=self.name, data=obj)
                
        except Exception as e:
            error_msg = f"Error checking AI trigger: {str(e)}"
            logger.error(error_msg)
            return TriggerContext(trigger_name=self.name, data={"trigger": False, "reason": error_msg})

    async def watch(self, queue_put) -> None:
        """Watch for trigger conditions."""
        while True:
            try:
                ctx = await self.check()
                if ctx is not None:
                    triggered = ctx.data.get("trigger", False)
                    reason = ctx.data.get("reason", "No reason provided")
                    if triggered:
                        await queue_put(ctx)
                    else:
                        logger.info(f"Trigger {self.name} not fired: {reason}")
            except Exception as e:
                logger.error("Error in AI trigger watch loop: %s", str(e))
            await asyncio.sleep(self.interval) 