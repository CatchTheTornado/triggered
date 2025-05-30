import asyncio
import logging
import os

from celery import Celery

from .core import TriggerAction, TriggerContext
from .registry import get_action

logger = logging.getLogger(__name__)

# Allow opting out of external message broker.  If the env var BROKER_URL is
# unset, fall back to the in-process ``memory://`` broker so Redis is optional.

broker_url = os.getenv("BROKER_URL", "memory://")
# For small local installs the RPC backend works without extra services.
backend_url = os.getenv("BACKEND_URL", "rpc://")

app = Celery(
    "triggered",
    broker=broker_url,
    backend=backend_url,
)


@app.task(name="triggered.execute_action")
def execute_action(ta_dict: dict, ctx_dict: dict):  # noqa: D401
    """Celery task that instantiates and executes an Action."""
    ta = TriggerAction.model_validate(ta_dict)  # type: ignore[attr-defined]
    ctx = TriggerContext.model_validate(ctx_dict)  # type: ignore[attr-defined]
    action_cls = get_action(ta.action_type)
    action = action_cls(ta.action_config)

    # Run action synchronously within celery worker event loop
    asyncio.run(action.execute(ctx)) 