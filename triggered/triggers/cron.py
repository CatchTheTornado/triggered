import asyncio
import datetime as _dt
from typing import Dict, Any
import zoneinfo
import logging
from croniter import croniter

from ..core import Trigger, TriggerContext
from ..registry import register_trigger
from ..config_schema import ConfigSchema, ConfigField

logger = logging.getLogger(__name__)

@register_trigger("cron")
class CronTrigger(Trigger):
    """Trigger that fires according to a crontab expression.
    
    Supports both standard 5-field (minute-based) and extended 6-field (second-based) cron expressions:
    - 5 fields: "* * * * *" (minute hour day month weekday)
    - 6 fields: "* * * * * *" (second minute hour day month weekday)
    
    For second-based scheduling, use the 6-field format with seconds as the first field.
    Example: "*/20 * * * * *" runs every 20 seconds.
    
    See https://pypi.org/project/croniter/#about-second-repeats for more details.
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
                name="expression",
                type="string",
                description="Cron expression (e.g. '* * * * * *' for seconds, '* * * * *' for minutes)",
                required=True
            ),
            ConfigField(
                name="timezone",
                type="string",
                description="Timezone for cron expression (e.g. 'UTC')",
                default="UTC",
                required=False
            )
        ])

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.expr: str = config["expression"]  # e.g. "* * * * * *" for seconds
        self.timezone = zoneinfo.ZoneInfo(config.get("timezone", "UTC"))
        self._iter = croniter(self.expr, _dt.datetime.now(self.timezone))

    async def watch(self, queue_put):
        while True:
            now = _dt.datetime.now(self.timezone)
            next_time = self._iter.get_next(_dt.datetime)
            delay = (next_time - now).total_seconds()
            logger.info(f"Crontab - next running time: now: {now} next: {next_time}, delay: {delay}")
            if delay > 0:
                await asyncio.sleep(delay)
            ctx = TriggerContext(trigger_name=self.name)
            await queue_put(ctx) 