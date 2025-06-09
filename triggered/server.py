import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List

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
from .queue import execute_action
from .registry import get_trigger

logger = logging.getLogger(__name__)

TRIGGER_ACTIONS_DIR = Path(os.getenv("TRIGGERED_TRIGGER_ACTIONS_PATH", "trigger_actions"))
TRIGGER_ACTIONS_DIR.mkdir(parents=True, exist_ok=True)

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
                        self.trigger_actions.append(ta)
                except Exception as exc:  # noqa: WPS420
                    logger.error("Failed to load example file %s: %s", file, exc)

    async def _spawn_watchers(self):
        for ta in self.trigger_actions:
            trigger_cls = get_trigger(ta.trigger_type)
            trigger = trigger_cls(ta.trigger_config)
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
            execute_action.delay(
                ta.model_dump(mode="json"),
                ctx.model_dump(mode="json"),
            )

    def add_trigger_action(self, ta: TriggerAction):
        file_path = TRIGGER_ACTIONS_DIR / f"{ta.id}.json"
        file_path.write_text(
            json.dumps(
                ta.model_dump(mode="json"),
                indent=2,
            ),
        )
        self.trigger_actions.append(ta)
        # Start watcher for this trigger
        trigger_cls = get_trigger(ta.trigger_type)
        trigger = trigger_cls(ta.trigger_config)
        task = asyncio.create_task(
            trigger.watch(
                lambda ctx, ta=ta: self._queue.put((ta, ctx)),
            ),
        )
        self._watcher_tasks.append(task)


runtime = RuntimeManager()


@app.on_event("startup")
async def on_startup():
    await runtime.start()


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


@app.get("/events")
async def list_events(limit: int = 50):
    return RECENT_EVENTS[-limit:] 