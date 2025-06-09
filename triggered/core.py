from __future__ import annotations

import abc
import datetime as _dt
import os
import re
import uuid
from typing import Any, Dict, Optional, TypedDict

from pydantic import BaseModel, Field


class TriggerContext(BaseModel):
    """Runtime information passed from Trigger to Action."""

    trigger_name: str
    fired_at: _dt.datetime = Field(default_factory=_dt.datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)

    def resolve_env_vars(self, value: str) -> str:
        """Resolve environment variables in a string value.
        
        Args:
            value: String that may contain environment variables in ${VAR} format
            
        Returns:
            String with environment variables resolved
        """
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, f"${{{var_name}}}")
        
        return re.sub(r'\${([^}]+)}', replace_env_var, value)

    def get_param(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with environment variable resolution.
        
        Args:
            key: Parameter key
            default: Default value if parameter not found
            
        Returns:
            Parameter value with environment variables resolved if it's a string
        """
        value = self.params.get(key, default)
        if isinstance(value, str):
            return self.resolve_env_vars(value)
        return value


class Trigger(abc.ABC):
    """Base class for all triggers."""

    name: str

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", self.__class__.__name__)

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this trigger type."""
        from .config_schema import ConfigSchema, ConfigField
        return ConfigSchema(fields=[
            ConfigField(
                name="name",
                type="string",
                description="Trigger name",
                required=True
            )
        ])

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

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        from .config_schema import ConfigSchema
        return ConfigSchema(fields=[])

    @abc.abstractmethod
    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        """Execute action logic."""


class TriggerDefinition(BaseModel):
    """Definition of a trigger in a trigger-action pair."""
    type: str
    config: Dict[str, Any]


class ActionDefinition(BaseModel):
    """Definition of an action in a trigger-action pair."""
    type: str
    config: Dict[str, Any]


class TriggerAction(BaseModel):
    """Configuration entity representing a Trigger + Action pair."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    auth_key: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trigger: TriggerDefinition
    action: ActionDefinition
    params: Dict[str, Any] = Field(default_factory=dict)

    def instantiate(self):
        from .registry import get_trigger, get_action  # lazy import

        trigger_cls = get_trigger(self.trigger.type)
        action_cls = get_action(self.action.type)
        return trigger_cls(self.trigger.config), action_cls(self.action.config) 