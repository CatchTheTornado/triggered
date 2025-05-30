from __future__ import annotations

import abc
import datetime as _dt
import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TriggerContext(BaseModel):
    """Runtime information passed from Trigger to Action."""

    trigger_name: str
    fired_at: _dt.datetime = Field(default_factory=_dt.datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)


class Trigger(abc.ABC):
    """Base class for all triggers."""

    name: str

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", self.__class__.__name__)

    @abc.abstractmethod
    async def watch(self, queue_put) -> None:  # noqa: D401
        """Continuously watch for trigger events and schedule actions.

        Parameters
        ----------
        queue_put: Callable[[TriggerContext], Awaitable[None]]
            Coroutine used to enqueue a fired trigger.
        """

    # Optionally synchronous check for cron/time triggers
    async def check(self) -> Optional[TriggerContext]:  # noqa: D401
        """Return TriggerContext if fired in this tick, else None."""
        return None


class Action(abc.ABC):
    """Base class for all actions."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abc.abstractmethod
    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        """Execute action logic."""


class TriggerAction(BaseModel):
    """Configuration entity representing a Trigger + Action pair."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    auth_key: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trigger_type: str
    trigger_config: Dict[str, Any]
    action_type: str
    action_config: Dict[str, Any]

    def instantiate(self):
        from .registry import get_trigger, get_action  # lazy import

        trigger_cls = get_trigger(self.trigger_type)
        action_cls = get_action(self.action_type)
        return trigger_cls(self.trigger_config), action_cls(self.action_config) 