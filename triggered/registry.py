from typing import Dict, Type, Callable, Any, Union, Optional

from .core import Trigger, Action
from .tools import Tool

TRIGGER_REGISTRY: Dict[str, Type[Trigger]] = {}
ACTION_REGISTRY: Dict[str, Type[Action]] = {}
TOOL_REGISTRY: Dict[str, Type[Tool]] = {}


def register_trigger(name: Optional[str] = None, trigger_cls: Optional[Type[Trigger]] = None) -> Union[Callable[[Type[Trigger]], Type[Trigger]], None]:
    """Register a trigger class. Can be used as a decorator or direct function call.
    
    When used as a decorator:
        @register_trigger("trigger_name")
        class MyTrigger(Trigger):
            pass
            
    When used as a function:
        register_trigger("trigger_name", MyTrigger)
    """
    def decorator(cls: Type[Trigger]) -> Type[Trigger]:
        TRIGGER_REGISTRY[name] = cls
        return cls
        
    if trigger_cls is None:
        return decorator
    else:
        TRIGGER_REGISTRY[name] = trigger_cls
        return None


def register_action(name: Optional[str] = None, action_cls: Optional[Type[Action]] = None) -> Union[Callable[[Type[Action]], Type[Action]], None]:
    """Register an action class. Can be used as a decorator or direct function call.
    
    When used as a decorator:
        @register_action("action_name")
        class MyAction(Action):
            pass
            
    When used as a function:
        register_action("action_name", MyAction)
    """
    def decorator(cls: Type[Action]) -> Type[Action]:
        ACTION_REGISTRY[name] = cls
        return cls
        
    if action_cls is None:
        return decorator
    else:
        ACTION_REGISTRY[name] = action_cls
        return None


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