import asyncio
import logging
import os

from celery import Celery

from .core import TriggerAction, TriggerContext
from .registry import get_action
from .logging_config import log_action_start, log_action_result, log_result_details

logger = logging.getLogger(__name__)

# Allow opting out of external message broker.  If the env var TRIGGERED_BROKER_URL is
# unset, fall back to the in-process ``memory://`` broker so Redis is optional.

broker_url = os.getenv("TRIGGERED_BROKER_URL", "memory://")
# For small local installs the RPC backend works without extra services.
backend_url = os.getenv("TRIGGERED_BACKEND_URL", "rpc://")

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
    action_cls = get_action(ta.action.type)
    action = action_cls(ta.action.config)

    # Log action start
    action_name = ta.action.config.get("name", ta.action.type)
    log_action_start(action_name)

    try:
        # Run action synchronously within celery worker event loop
        result = asyncio.run(action.execute(ctx))
        log_action_result(action_name, result)
        log_result_details(result)
        return result
    except Exception as e:
        log_action_result(action_name, error=str(e))
        raise 