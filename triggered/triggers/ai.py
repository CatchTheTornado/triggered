import asyncio
import json
import logging
from typing import Any, Dict, Optional
from ..core import Trigger, TriggerContext
from ..models import get_model
from ..tools import get_tools, load_tools_from_module

logger = logging.getLogger(__name__)


class AITrigger(Trigger):
    """Trigger that uses AI to make decisions."""

    def __init__(
        self,
        name: str,
        model: str | None = None,
        api_base: str | None = None,
        interval: int = 60,
        prompt: str = "",
        tools: list[Dict[str, Any]] | None = None,
        custom_tools_path: str | None = None,
        **kwargs
    ) -> None:
        super().__init__(name)
        self.model = get_model(model=model, api_base=api_base, **kwargs)
        self.interval = interval
        self.prompt = prompt
        self.tools = get_tools(tools or [])
        
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