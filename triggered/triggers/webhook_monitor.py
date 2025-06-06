import asyncio
from typing import Dict, Any

from ..core import Trigger, TriggerContext
from ..registry import register_trigger
from ..config_schema import ConfigSchema, ConfigField


@register_trigger("webhook")
class WebHookMonitorTrigger(Trigger):
    """Trigger that fires when an HTTP webhook is received.

    This trigger does not listen on its own socket; instead, the FastAPI server
    injects events into its internal queue via :py:meth:`enqueue`.

    Config keys:
    - route: str, URL path (e.g. "/hooks/my-trigger")
    """

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
                name="route",
                type="string",
                description="URL path for the webhook (e.g. '/hooks/my-trigger')",
                required=False
            )
        ])

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.route: str = config.get("route", f"/hooks/{self.name}")
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def watch(self, queue_put):
        while True:
            payload = await self._queue.get()
            ctx = TriggerContext(
                trigger_name=self.name,
                data={"payload": payload},
            )
            await queue_put(ctx)

    async def enqueue(self, payload: Dict[str, Any]):
        """Called by external server when webhook event arrives."""
        await self._queue.put(payload) 