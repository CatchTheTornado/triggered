from __future__ import annotations

import abc
import datetime as _dt
import os
import re
import uuid
from typing import Any, Dict, Optional, TypedDict, Type

from pydantic import BaseModel, Field, ValidationError


class BaseConfig(BaseModel):
    """Base configuration model for triggers and actions."""
    name: str = Field(description="Name of the trigger/action")


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
    config_model: Type[BaseConfig] = BaseConfig

    def __init__(self, config: Dict[str, Any]):
        self.config = self.config_model(**config)
        self.name = self.config.name

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

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> tuple[bool, str | None]:
        """Validate the configuration against the schema.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            cls.config_model(**config)
            return True, None
        except ValidationError as e:
            return False, str(e)

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

    config_model: Type[BaseConfig] = BaseConfig

    def __init__(self, config: Dict[str, Any]):
        self.config = self.config_model(**config)

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        from .config_schema import ConfigSchema
        return ConfigSchema(fields=[])

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> tuple[bool, str | None]:
        """Validate the configuration against the schema.
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            cls.config_model(**config)
            return True, None
        except ValidationError as e:
            return False, str(e)

    @abc.abstractmethod
    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        """Execute action logic."""


class TriggerDefinition(BaseModel):
    """Definition of a trigger in a trigger-action pair."""
    type: str
    config: Dict[str, Any]

    def validate(self) -> tuple[bool, str | None]:
        """Validate the trigger configuration."""
        from .registry import get_trigger
        trigger_cls = get_trigger(self.type)
        if not trigger_cls:
            return False, f"Unknown trigger type: {self.type}"
        return trigger_cls.validate_config(self.config)


class ActionDefinition(BaseModel):
    """Definition of an action in a trigger-action pair."""
    type: str
    config: Dict[str, Any]

    def validate(self) -> tuple[bool, str | None]:
        """Validate the action configuration."""
        from .registry import get_action
        action_cls = get_action(self.type)
        if not action_cls:
            return False, f"Unknown action type: {self.type}"
        return action_cls.validate_config(self.config)


class TriggerAction(BaseModel):
    """Configuration entity representing a Trigger + Action pair."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    auth_key: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trigger: TriggerDefinition
    action: ActionDefinition
    params: Dict[str, Any] = Field(default_factory=dict)

    def validate(self) -> tuple[bool, str | None]:
        """Validate the entire configuration."""
        # Validate trigger
        is_valid, error = self.trigger.validate()
        if not is_valid:
            return False, f"Invalid trigger configuration: {error}"
            
        # Validate action
        is_valid, error = self.action.validate()
        if not is_valid:
            return False, f"Invalid action configuration: {error}"
            
        return True, None

    def instantiate(self):
        from .registry import get_trigger, get_action  # lazy import

        trigger_cls = get_trigger(self.trigger.type)
        action_cls = get_action(self.action.type)
        return trigger_cls(self.trigger.config), action_cls(self.action.config) 