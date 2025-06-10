import asyncio
import logging
import os
import sys
import socket
from pathlib import Path

from celery import Celery
from celery.signals import (
    worker_process_init,
    task_received,
    before_task_publish,
    after_task_publish,
    task_success,
    task_failure
)

from .core import TriggerAction, TriggerContext
from .registry import get_action
from .logging_config import log_action_start, log_action_result, log_result_details, logger, setup_logging

# Create data directory if it doesn't exist
data_dir = Path(os.getenv("TRIGGERED_DATA_DIR", "data"))
data_dir.mkdir(parents=True, exist_ok=True)

# Use SQLite as broker and backend
broker_url = f"sqla+sqlite:///{data_dir}/celery.sqlite"
backend_url = f"db+sqlite:///{data_dir}/celery_results.sqlite"

# Get hostname for worker identification
hostname = socket.gethostname()

app = Celery(
    "triggered",
    broker=broker_url,
    backend=backend_url,
)

# Configure Celery logging and task settings
app.conf.update(
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
    worker_redirect_stdouts=False,  # Don't redirect stdout/stderr
    worker_redirect_stdouts_level='INFO',  # Log level for redirected output
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_publish_retry=True,
    task_publish_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    },
    task_default_queue='triggered',
    task_queues={
        'triggered': {
            'exchange': 'triggered',
            'routing_key': 'triggered',
        }
    },
    task_routes={
        'triggered.execute_action': {
            'queue': 'triggered',
            'routing_key': 'triggered'
        }
    },
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=1,  # Restart worker after each task
    worker_send_task_events=True,  # Enable task events
    task_send_sent_event=True,  # Enable sent events
    worker_hostname=f'triggered@{hostname}',  # Set explicit hostname
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    task_ignore_result=False,  # Always store task results
    task_store_errors_even_if_ignored=True,  # Store errors even if result is ignored
    sqlalchemy_engine_options={
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }
)

@worker_process_init.connect
def setup_worker_logging(**kwargs):
    """Set up logging for each worker process."""
    setup_logging()
    logger.info(f"Celery worker process initialized on {hostname}")

@before_task_publish.connect
def before_task_publish_handler(sender=None, headers=None, **kwargs):
    """Log when a task is about to be published."""
    logger.info(f"Task about to be published: {sender} (ID: {headers.get('id')})")

@after_task_publish.connect
def after_task_publish_handler(sender=None, headers=None, **kwargs):
    """Log when a task has been published."""
    logger.info(f"Task published: {sender} (ID: {headers.get('id')})")

@task_received.connect
def task_received_handler(sender=None, request=None, **kwargs):
    """Log when a task is received by the worker."""
    logger.info(f"Task received: {request.name} (ID: {request.id})")

@task_success.connect
def task_success_handler(sender=None, **kwargs):
    """Log when a task completes successfully."""
    logger.info(f"Task succeeded: {sender.name} (ID: {sender.request.id})")

@task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    """Log when a task fails."""
    logger.error(f"Task failed: {sender.name} (ID: {sender.request.id}) - {str(exception)}", exc_info=True)

@app.task(name="triggered.execute_action", bind=True, queue='triggered', max_retries=3)
def execute_action(self, ta_dict: dict, ctx_dict: dict):  # noqa: D401
    """Celery task that instantiates and executes an Action."""
    # Set up logging for the Celery worker
    setup_logging()
    
    # Ensure stdout/stderr are properly configured
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    logger.info(f"Starting action execution in Celery worker (Task ID: {self.request.id})")
    
    try:
        ta = TriggerAction.model_validate(ta_dict)  # type: ignore[attr-defined]
        ctx = TriggerContext.model_validate(ctx_dict)  # type: ignore[attr-defined]

        # Run action synchronously within celery worker event loop
        result = asyncio.run(ta.execute_action(ctx))
        logger.info(f"Action execution completed successfully (Task ID: {self.request.id})")
        return result
    except Exception as e:
        logger.error(f"Action execution failed (Task ID: {self.request.id}): {str(e)}", exc_info=True)
        # Retry the task with exponential backoff
        retry_in = 2 ** self.request.retries  # Exponential backoff
        self.retry(exc=e, countdown=retry_in) 