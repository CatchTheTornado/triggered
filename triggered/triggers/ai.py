import asyncio
from typing import Dict, Any

from ..core import Trigger, TriggerContext
from ..registry import register_trigger
from ..models import get_model


@register_trigger("ai")
class AITrigger(Trigger):
    """Trigger that uses an AI model to decide when to fire.

    The config must include:
    - prompt: str
    - model: str (optional, default "local")
    - interval: int seconds between evaluations (default 60)
    - tools: list (optional)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.prompt: str = config["prompt"]
        self.model_name: str = config.get("model", "local")
        self.interval: int = int(config.get("interval", 60))
        self.model = get_model(self.model_name)
        self.tools = config.get("tools", [])

    async def watch(self, queue_put):
        while True:
            decision = await self._evaluate()
            if decision:
                ctx = TriggerContext(
                    trigger_name=self.name,
                    data={"decision": decision},
                )
                await queue_put(ctx)
            await asyncio.sleep(self.interval)

    async def _evaluate(self):
        # Very naive implementation: We ask the model to answer yes/no.
        prompt = (
            f"{self.prompt}\n"
            "Answer with yes or no only."
        )
        response = await self.model.ainvoke(prompt)
        decision = response.strip().lower().startswith("y")
        return decision 