from typing import Dict, Type, Any, Optional, Union
import datetime as _dt
from pydantic import BaseModel, Field
import httpx
import os
import importlib.util
import inspect
import logging
import random

logger = logging.getLogger(__name__)


class ToolInput(BaseModel):
    """Base class for tool input schemas."""
    pass


class RandomNumberInput(ToolInput):
    """Input schema for RandomNumberTool."""
    min_value: int = Field(default=1, description="Minimum value (inclusive)")
    max_value: int = Field(default=10, description="Maximum value (inclusive)")


class Tool:
    """Base class for all tools."""
    name: str
    description: str
    args_schema: Type[ToolInput]

    def __init__(self):
        pass

    async def _call(self, **kwargs) -> Any:
        raise NotImplementedError


class RandomNumberTool(Tool):
    """Tool that generates random numbers."""
    name = "random_number"
    description = "Generate a random number between min_value and max_value (inclusive)"
    args_schema = RandomNumberInput

    async def _call(self, min_value: int = 1, max_value: int = 10) -> str:
        return str(random.randint(min_value, max_value))


# Registry of available tools
TOOL_REGISTRY: Dict[str, Type[Tool]] = {
    "random_number": RandomNumberTool,
}


def get_tools(tool_configs: list[Union[str, Dict[str, Any]]]) -> Dict[str, Tool]:
    """Get tool instances from configurations.
    
    Args:
        tool_configs: List of tool configurations. Each config can be either:
            - A string (tool type name)
            - A dictionary with at least a "type" key
    """
    tools = {}
    for config in tool_configs:
        if isinstance(config, str):
            tool_type = config
        else:
            tool_type = config.get("type")
            
        if tool_type not in TOOL_REGISTRY:
            logger.warning("Unknown tool type: %s", tool_type)
            continue
            
        tool_cls = TOOL_REGISTRY[tool_type]
        tools[tool_type] = tool_cls()
    return tools


def load_tools_from_module(module_path: str) -> None:
    """Load custom tools from a Python module."""
    try:
        spec = importlib.util.spec_from_file_location("custom_tools", module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Look for Tool subclasses in the module
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Tool) and obj != Tool:
                TOOL_REGISTRY[obj.name] = obj
                logger.info("Loaded custom tool: %s", obj.name)
    except Exception as e:
        logger.error("Failed to load custom tools from %s: %s", module_path, e)
        raise 