import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
try:
    from opentelemetry import trace  # type: ignore
    from opentelemetry.instrumentation.fastapi import (  # type: ignore
        FastAPIInstrumentor,
    )
    from opentelemetry.sdk.resources import Resource  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import (  # type: ignore
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
except ImportError:  # pragma: no cover
    trace = None  # type: ignore
    FastAPIInstrumentor = None  # type: ignore
    Resource = None  # type: ignore
    TracerProvider = None  # type: ignore
    BatchSpanProcessor = ConsoleSpanExporter = None  # type: ignore

from .core import TriggerAction
from .queue import app as celery_app, execute_action
from .registry import get_trigger
from .logging_config import logger

TRIGGER_ACTIONS_DIR = Path(os.getenv("TRIGGERED_TRIGGER_ACTIONS_PATH", "trigger_actions"))
TRIGGER_ACTIONS_DIR.mkdir(parents=True, exist_ok=True)

# Environment variable to control whether to start the Celery worker
START_WORKER = os.getenv("TRIGGERED_START_WORKER", "true").lower() == "true"

app = FastAPI(title="Triggered Runtime Engine")

# Setup OpenTelemetry console exporter (for demo)
if trace and FastAPIInstrumentor:
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider = TracerProvider(
        resource=Resource.create({"service.name": "triggered"}),
    )
    provider.add_span_processor(
        processor,
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
    tracer = trace.get_tracer(__name__)
else:
    tracer = None

# In-memory store of recent events
RECENT_EVENTS: List[Dict] = []

# Store the worker process
worker_process: Optional[subprocess.Popen] = None


class RuntimeManager:
    def __init__(self):
        self.trigger_actions: List[TriggerAction] = []
        self._watcher_tasks: List[asyncio.Task] = []
        self._queue: asyncio.Queue = asyncio.Queue()

    async def start(self):
        self._load_from_disk()
        await self._spawn_watchers()
        asyncio.create_task(self._dispatcher())

    def _load_from_disk(self):
        # First check TRIGGER_ACTIONS_DIR
        for file in TRIGGER_ACTIONS_DIR.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                # type: ignore[attr-defined]
                ta = TriggerAction.model_validate(
                    data,
                )
                ta.filename = file.name  # Store the filename
                self.trigger_actions.append(ta)
            except Exception as exc:  # noqa: WPS420
                logger.error("Failed to load trigger file %s: %s", file, exc)

        # Then check EXAMPLES_DIR for any files not already loaded
        EXAMPLES_DIR = Path(os.getenv("TRIGGERED_EXAMPLES_PATH", "examples"))
        if EXAMPLES_DIR.exists():
            for file in EXAMPLES_DIR.glob("*.json"):
                try:
                    data = json.loads(file.read_text())
                    # type: ignore[attr-defined]
                    ta = TriggerAction.model_validate(
                        data,
                    )
                    # Only add if not already loaded from TRIGGER_ACTIONS_DIR
                    if not any(existing.id == ta.id for existing in self.trigger_actions):
                        ta.filename = file.name  # Store the filename
                        self.trigger_actions.append(ta)
                except Exception as exc:  # noqa: WPS420
                    logger.error("Failed to load example file %s: %s", file, exc)

    async def _spawn_watchers(self):
        for ta in self.trigger_actions:
            trigger_cls = get_trigger(ta.trigger.type)
            trigger = trigger_cls(ta.trigger.config)
            task = asyncio.create_task(
                trigger.watch(
                    lambda ctx, ta=ta: self._queue.put((ta, ctx)),
                ),
            )
            self._watcher_tasks.append(task)

            # Dynamically mount FastAPI route for webhook triggers
            if hasattr(trigger, "route") and hasattr(trigger, "enqueue"):
                route_path = getattr(trigger, "route")

                async def _handler(request: Request, tg=trigger):  # noqa: D401
                    payload = await request.json()
                    await tg.enqueue(payload)
                    return {"status": "queued"}

                # Avoid re-registering the same path
                existing_paths = {r.path for r in app.router.routes}
                if route_path not in existing_paths:
                    app.post(route_path)(_handler)

    async def _dispatcher(self):
        while True:
            ta, ctx = await self._queue.get()
            RECENT_EVENTS.append(
                {
                    "id": ta.id,
                    "time": ctx.fired_at.isoformat(),
                },
            )
            # Log that we're dispatching the action
            logger.info(f"Dispatching action for trigger-action {ta.filename or ta.id}")
            # Execute the action asynchronously
            try:
                task = execute_action.apply_async(
                    args=[
                        ta.model_dump(mode="json"),
                        ctx.model_dump(mode="json"),
                    ],
                    queue='triggered'
                )
                logger.info(f"Action task scheduled with ID: {task.id}")
            except Exception as e:
                logger.error(f"Failed to schedule action task: {str(e)}", exc_info=True)

    def add_trigger_action(self, ta: TriggerAction):
        file_path = TRIGGER_ACTIONS_DIR / f"{ta.id}.json"
        file_path.write_text(
            json.dumps(
                ta.model_dump(mode="json"),
                indent=2,
            ),
        )
        ta.filename = file_path.name  # Store the filename
        self.trigger_actions.append(ta)
        # Start watcher for this trigger
        trigger_cls = get_trigger(ta.trigger.type)
        trigger = trigger_cls(ta.trigger.config)
        task = asyncio.create_task(
            trigger.watch(
                lambda ctx, ta=ta: self._queue.put((ta, ctx)),
            ),
        )
        self._watcher_tasks.append(task)


runtime = RuntimeManager()


def start_celery_worker():
    """Start the Celery worker in a separate process."""
    global worker_process
    
    # Get the path to the current Python interpreter
    python_executable = sys.executable
    
    # Get the path to the current module
    module_path = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the command to start the Celery worker
    cmd = [
        python_executable,
        "-m",
        "celery",
        "-A",
        f"{os.path.basename(module_path)}.queue",
        "worker",
        "--loglevel=INFO",
        "--concurrency=1",
        "--pool=solo",
        "-Q",
        "triggered",  # Explicitly specify the queue
        "--hostname",
        "triggered@%h"  # Give the worker a unique hostname
    ]
    
    # Start the worker process
    worker_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Start threads to forward worker output
    def forward_output(pipe, prefix):
        for line in pipe:
            logger.info(f"[Celery Worker] {line.strip()}")
    
    import threading
    threading.Thread(target=forward_output, args=(worker_process.stdout, "OUT"), daemon=True).start()
    threading.Thread(target=forward_output, args=(worker_process.stderr, "ERR"), daemon=True).start()
    
    return worker_process


def stop_celery_worker():
    """Stop the Celery worker process."""
    global worker_process
    if worker_process is not None:
        logger.info("Stopping Celery worker...")
        # Send SIGTERM to the worker process
        worker_process.terminate()
        try:
            # Wait for the process to terminate
            worker_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it doesn't terminate, force kill it
            logger.warning("Worker process did not terminate gracefully, forcing kill...")
            worker_process.kill()
            worker_process.wait()
        worker_process = None
        logger.info("Celery worker stopped")


@app.on_event("startup")
async def on_startup():
    # Start the Celery worker if enabled
    if START_WORKER:
        worker_process = start_celery_worker()
        logger.info("Started Celery worker")
    else:
        logger.info("Celery worker disabled - assuming it's running externally")
    
    # Start the runtime manager
    await runtime.start()
    logger.info("Started runtime manager")


@app.post("/trigger_actions")
async def create_trigger(req: Request):
    body = await req.json()
    try:
        # type: ignore[attr-defined]
        ta = TriggerAction.model_validate(
            body,
        )
    except Exception as exc:  # noqa: WPS420
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    runtime.add_trigger_action(ta)
    return {"id": ta.id, "auth_key": ta.auth_key}


@app.get("/trigger_actions/{trigger_id}")
async def get_trigger_info(trigger_id: str, auth: str):
    for ta in runtime.trigger_actions:
        if ta.id == trigger_id:
            if ta.auth_key != auth:
                raise HTTPException(status_code=403, detail="Invalid auth key")
            return ta.model_dump()
    raise HTTPException(status_code=404, detail="Trigger not found")


@app.get("/trigger_actions")
async def list_triggers():
    """List all registered triggers."""
    return [ta.model_dump() for ta in runtime.trigger_actions]


@app.delete("/trigger_actions/{trigger_id}")
async def delete_trigger(trigger_id: str, auth: str):
    """Delete a trigger by ID."""
    for i, ta in enumerate(runtime.trigger_actions):
        if ta.id == trigger_id:
            if ta.auth_key != auth:
                raise HTTPException(status_code=403, detail="Invalid auth key")
            
            # Remove the trigger file if it exists
            if ta.filename:
                file_path = TRIGGER_ACTIONS_DIR / ta.filename
                if file_path.exists():
                    file_path.unlink()
            
            # Remove from runtime
            runtime.trigger_actions.pop(i)
            return {"status": "deleted"}
    
    raise HTTPException(status_code=404, detail="Trigger not found")


@app.put("/trigger_actions/{trigger_id}")
async def update_trigger(trigger_id: str, auth: str, req: Request):
    """Update an existing trigger."""
    # First find the existing trigger
    existing_ta = None
    for ta in runtime.trigger_actions:
        if ta.id == trigger_id:
            if ta.auth_key != auth:
                raise HTTPException(status_code=403, detail="Invalid auth key")
            existing_ta = ta
            break
    
    if not existing_ta:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    # Get the new configuration
    body = await req.json()
    try:
        # type: ignore[attr-defined]
        new_ta = TriggerAction.model_validate(body)
    except Exception as exc:  # noqa: WPS420
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    # Ensure the ID matches
    if new_ta.id != trigger_id:
        raise HTTPException(status_code=400, detail="Trigger ID mismatch")
    
    # Update the file
    file_path = TRIGGER_ACTIONS_DIR / f"{new_ta.id}.json"
    file_path.write_text(
        json.dumps(
            new_ta.model_dump(mode="json"),
            indent=2,
        ),
    )
    
    # Update in runtime
    for i, ta in enumerate(runtime.trigger_actions):
        if ta.id == trigger_id:
            runtime.trigger_actions[i] = new_ta
            break
    
    return new_ta.model_dump()


@app.get("/events")
async def list_events(limit: int = 50):
    """List recent trigger events.
    
    Args:
        limit: Maximum number of events to return (default: 50)
    """
    return {
        "events": RECENT_EVENTS[-limit:],
        "total": len(RECENT_EVENTS),
        "limit": limit
    }


@app.get("/status")
async def get_status():
    """Get server status and health information."""
    return {
        "status": "running",
        "version": "1.0.0",  # TODO: Get from package version
        "uptime": "0:00:00",  # TODO: Calculate from startup time
        "worker": {
            "status": "running" if worker_process and worker_process.poll() is None else "stopped",
            "pid": worker_process.pid if worker_process else None
        },
        "triggers": {
            "total": len(runtime.trigger_actions),
            "active": len([ta for ta in runtime.trigger_actions if any(not t.done() for t in runtime._watcher_tasks)])
        },
        "queue": {
            "size": runtime._queue.qsize() if hasattr(runtime, "_queue") else 0
        }
    }


@app.post("/trigger_actions/{trigger_id}/run")
async def run_trigger(trigger_id: str, auth: str):
    """Manually run a trigger.
    
    This will execute the trigger's action immediately, bypassing the normal trigger conditions.
    """
    # Find the trigger
    trigger_ta = None
    for ta in runtime.trigger_actions:
        if ta.id == trigger_id:
            if ta.auth_key != auth:
                raise HTTPException(status_code=403, detail="Invalid auth key")
            trigger_ta = ta
            break
    
    if not trigger_ta:
        raise HTTPException(status_code=404, detail="Trigger not found")
    
    # Create a context for manual execution
    from datetime import datetime
    from .core import TriggerContext
    
    ctx = TriggerContext(
        fired_at=datetime.utcnow(),
        data={
            "manual": True,
            "reason": "Manually triggered via API"
        }
    )
    
    # Execute the action asynchronously
    try:
        task = execute_action.apply_async(
            args=[
                trigger_ta.model_dump(mode="json"),
                ctx.model_dump(mode="json"),
            ],
            queue='triggered'
        )
        logger.info(f"Manual trigger execution scheduled with task ID: {task.id}")
        
        return {
            "status": "scheduled",
            "task_id": task.id,
            "trigger_id": trigger_id,
            "timestamp": ctx.fired_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to schedule manual trigger execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute trigger: {str(e)}")


@app.on_event("shutdown")
async def on_shutdown():
    # Stop the Celery worker if we started it
    if START_WORKER:
        stop_celery_worker()
    
    # Stop the runtime manager
    for task in runtime._watcher_tasks:
        task.cancel()
    await asyncio.gather(*runtime._watcher_tasks, return_exceptions=True)
    logger.info("Runtime manager stopped") 