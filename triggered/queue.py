import asyncio
import logging
import os
import sys

from celery import Celery
from celery.signals import worker_process_init

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

# Configure Celery logging
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    worker_redirect_stdouts=False,  # Don't redirect stdout/stderr
    worker_redirect_stdouts_level='INFO',  # Log level for redirected output
)

@worker_process_init.connect
def setup_worker_logging(**kwargs):
    """Set up logging for each worker process."""
    setup_logging()

@app.task(name="triggered.execute_action")
def execute_action(ta_dict: dict, ctx_dict: dict):  # noqa: D401
    """Celery task that instantiates and executes an Action."""
    # Set up logging for the Celery worker
    setup_logging()
    
    # Ensure stdout/stderr are properly configured
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    ta = TriggerAction.model_validate(ta_dict)  # type: ignore[attr-defined]
    ctx = TriggerContext.model_validate(ctx_dict)  # type: ignore[attr-defined]

    # Run action synchronously within celery worker event loop
    try:
        result = asyncio.run(ta.execute_action(ctx))
        return result
    except Exception as e:
        logger.error(f"Action execution failed: {str(e)}")
        raise 