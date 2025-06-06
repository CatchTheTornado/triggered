import os
import importlib
import inspect
from pathlib import Path
from typing import Type, Dict, Any

from .core import Trigger, Action
from .tools import Tool
from .registry import register_trigger, register_action, register_tool

def get_module_path(env_var: str, default: str) -> str:
    """Get module path from environment variable or use default."""
    return os.getenv(env_var, default)

def discover_components(module_path: str, base_class: Type) -> Dict[str, Type]:
    """Discover and register components from a module path."""
    components = {}
    try:
        module = importlib.import_module(module_path)
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, base_class) and 
                obj != base_class and 
                hasattr(obj, 'name')):
                components[obj.name] = obj
    except ImportError:
        pass
    return components

def discover_triggers() -> Dict[str, Type[Trigger]]:
    """Discover and register trigger components."""
    module_path = get_module_path('TRIGGERED_TRIGGERS_MODULE', 'triggered.triggers')
    return discover_components(module_path, Trigger)

def discover_actions() -> Dict[str, Type[Action]]:
    """Discover and register action components."""
    module_path = get_module_path('TRIGGERED_ACTIONS_MODULE', 'triggered.actions')
    return discover_components(module_path, Action)

def discover_tools() -> Dict[str, Type[Tool]]:
    """Discover and register tool components."""
    module_path = get_module_path('TRIGGERED_TOOLS_MODULE', 'triggered.tools')
    return discover_components(module_path, Tool)

def register_discovered_components():
    """Discover and register all components."""
    # Discover and register triggers
    for name, trigger_cls in discover_triggers().items():
        register_trigger(name, trigger_cls)
    
    # Discover and register actions
    for name, action_cls in discover_actions().items():
        register_action(name, action_cls)
    
    # Discover and register tools
    for name, tool_cls in discover_tools().items():
        register_tool(name, tool_cls) 