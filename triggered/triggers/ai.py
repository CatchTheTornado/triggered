import asyncio
import json
import logging
from typing import Any, Dict, Optional
from ..core import Trigger, TriggerContext
from ..models import get_model
from ..tools import get_tools, load_tools_from_module
from ..registry import register_trigger

logger = logging.getLogger(__name__)


@register_trigger("ai")
class AITrigger(Trigger):
    """Trigger that uses AI to make decisions."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config.get("name", "ai_trigger"))
        self.model = get_model(model=config.get("model"), api_base=config.get("api_base"))
        self.interval = config.get("interval", 60)
        self.prompt = config.get("prompt", "")
        self.tools = get_tools(config.get("tools", []))
        custom_tools_path = config.get("custom_tools_path")
        if custom_tools_path:
            load_tools_from_module(custom_tools_path)

    async def check(self) -> Optional[TriggerContext]:
        """Check if the trigger condition is met."""
        try:
            response = await self.model.ainvoke(self.prompt, tools=self.tools)
            try:
                obj = json.loads(response)
                if obj and obj.get("trigger"):
                    return TriggerContext(data=obj)
            except json.JSONDecodeError:
                logger.error("Failed to parse model response as JSON: %s", response)
        except Exception as e:
            logger.error("Error checking AI trigger: %s", str(e))
        return None

    async def watch(self) -> None:
        """Watch for trigger conditions."""
        while True:
            try:
                ctx = await self.check()
                if ctx is not None:
                    yield ctx
            except Exception as e:
                logger.error("Error in AI trigger watch loop: %s", str(e))
            await asyncio.sleep(self.interval) 