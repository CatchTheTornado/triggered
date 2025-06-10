import asyncio
import logging
import os

from celery import Celery

from .core import TriggerAction, TriggerContext
from .registry import get_action
from .logging_config import log_action_start, log_action_result, log_result_details, logger, setup_logging

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
    # Set up logging for the Celery worker
    setup_logging()
    
    ta = TriggerAction.model_validate(ta_dict)  # type: ignore[attr-defined]
    ctx = TriggerContext.model_validate(ctx_dict)  # type: ignore[attr-defined]

    # Run action synchronously within celery worker event loop
    return asyncio.run(ta.execute_action(ctx)) 