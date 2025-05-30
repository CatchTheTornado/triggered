import asyncio
import logging

from celery import Celery

from .core import TriggerAction, TriggerContext
from .registry import get_action

logger = logging.getLogger(__name__)

# Broker URL can be configured via env var; default to Redis
app = Celery(
    "triggered",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)


@app.task(name="triggered.execute_action")
def execute_action(ta_dict: dict, ctx_dict: dict):  # noqa: D401
    """Celery task that instantiates and executes an Action."""
    ta = TriggerAction.model_validate(ta_dict)
    ctx = TriggerContext.model_validate(ctx_dict)
    action_cls = get_action(ta.action_type)
    action = action_cls(ta.action_config)

    # Run action synchronously within celery worker event loop
    asyncio.run(action.execute(ctx)) 