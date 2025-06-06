from typing import Dict, Type, Callable, Any

from .core import Trigger, Action
from .tools import Tool

TRIGGER_REGISTRY: Dict[str, Type[Trigger]] = {}
ACTION_REGISTRY: Dict[str, Type[Action]] = {}
TOOL_REGISTRY: Dict[str, Type[Tool]] = {}


def register_trigger(name: str, trigger_cls: Type[Trigger]) -> None:
    """Register a trigger class."""
    TRIGGER_REGISTRY[name] = trigger_cls


def register_action(name: str, action_cls: Type[Action]) -> None:
    """Register an action class."""
    ACTION_REGISTRY[name] = action_cls


def register_tool(name: str, tool_cls: Type[Tool]) -> None:
    """Register a tool class."""
    TOOL_REGISTRY[name] = tool_cls


def get_trigger(name: str) -> Type[Trigger]:
    """Get a trigger class by name."""
    if name not in TRIGGER_REGISTRY:
        raise ValueError(f"Unknown trigger type: {name}")
    return TRIGGER_REGISTRY[name]


def get_action(name: str) -> Type[Action]:
    """Get an action class by name."""
    if name not in ACTION_REGISTRY:
        raise ValueError(f"Unknown action type: {name}")
    return ACTION_REGISTRY[name]


def get_tool(name: str) -> Type[Tool]:
    """Get a tool class by name."""
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool type: {name}")
    return TOOL_REGISTRY[name] 