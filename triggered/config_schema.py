from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ConfigField(BaseModel):
    """Schema for a single configuration field."""
    name: str
    type: str
    description: str
    default: Optional[Any] = None
    required: bool = True
    choices: Optional[List[str]] = None

class ConfigSchema(BaseModel):
    """Schema for a complete configuration."""
    fields: List[ConfigField]

def get_trigger_config_schema(trigger_type: str) -> ConfigSchema:
    """Get configuration schema for a trigger type."""
    from .registry import get_trigger
    trigger_cls = get_trigger(trigger_type)
    if hasattr(trigger_cls, 'get_config_schema'):
        return trigger_cls.get_config_schema()
    return ConfigSchema(fields=[])

def get_action_config_schema(action_type: str) -> ConfigSchema:
    """Get configuration schema for an action type."""
    from .registry import get_action
    action_cls = get_action(action_type)
    if hasattr(action_cls, 'get_config_schema'):
        return action_cls.get_config_schema()
    return ConfigSchema(fields=[]) 