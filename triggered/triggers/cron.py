import asyncio
import datetime as _dt
from typing import Dict, Any

from croniter import croniter

from ..core import Trigger, TriggerContext
from ..registry import register_trigger
from ..config_schema import ConfigSchema, ConfigField


@register_trigger("cron")
class CronTrigger(Trigger):
    """Trigger that fires according to a crontab expression."""

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
                name="expression",
                type="string",
                description="Cron expression (e.g. '* * * * *')",
                required=True
            )
        ])

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.expr: str = config["expression"]  # e.g. "* * * * *"
        self._iter = croniter(self.expr, _dt.datetime.utcnow())

    async def watch(self, queue_put):
        while True:
            now = _dt.datetime.utcnow()
            next_time = self._iter.get_next(_dt.datetime)
            delay = (next_time - now).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            ctx = TriggerContext(trigger_name=self.name)
            await queue_put(ctx) 