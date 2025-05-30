import asyncio
import datetime as _dt
from typing import Dict, Any

from croniter import croniter

from ..core import Trigger, TriggerContext
from ..registry import register_trigger


@register_trigger("cron")
class CronTrigger(Trigger):
    """Trigger that fires according to a crontab expression."""

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