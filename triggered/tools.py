from typing import Dict, Type, Any
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
    """Base input schema for tools."""
    pass


class CurrentDateInput(ToolInput):
    """Input schema for CurrentDateTool."""
    pass


class WeatherInput(ToolInput):
    """Input schema for WeatherTool."""
    city: str = Field(
        ...,
        description="The name of the city to check weather for"
    )


class RandomNumberInput(ToolInput):
    """Input schema for RandomNumberTool."""
    min_value: int = Field(
        1,
        description="Minimum value (inclusive)"
    )
    max_value: int = Field(
        100,
        description="Maximum value (inclusive)"
    )


class BaseTool:
    """Base class for all tools."""
    name: str
    description: str
    args_schema: Type[BaseModel]

    async def _run(self, **kwargs) -> str:
        raise NotImplementedError


class CurrentDateTool(BaseTool):
    name: str = "currentdate"
    description: str = "Returns the current date in YYYY-MM-DD format"
    args_schema: Type[BaseModel] = CurrentDateInput

    async def _run(self) -> str:
        return _dt.datetime.now(_dt.UTC).strftime("%Y-%m-%d")


class WeatherTool(BaseTool):
    name: str = "weather"
    description: str = (
        "Returns the current weather conditions for a given city"
    )
    args_schema: Type[BaseModel] = WeatherInput

    async def _run(self, city: str) -> str:
        # Using OpenWeatherMap API as an example
        # You'll need to set OPENWEATHER_API_KEY environment variable
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "Error: OPENWEATHER_API_KEY not set"

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        url = f"{base_url}?q={city}&appid={api_key}&units=metric"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                data = response.json()
                if response.status_code == 200:
                    weather = data["weather"][0]["main"].lower()
                    temp = data["main"]["temp"]
                    return f"{weather} {temp}°C"
                else:
                    return f"Error: {data.get('message', 'Unknown error')}"
            except Exception as e:
                return f"Error fetching weather: {str(e)}"


class RandomNumberTool(BaseTool):
    name: str = "random_number"
    description: str = "Generates a random number within a specified range"
    args_schema: Type[BaseModel] = RandomNumberInput

    async def _run(self, min_value: int = 1, max_value: int = 100) -> str:
        try:
            number = random.randint(min_value, max_value)
            return str(number)
        except Exception as e:
            return f"Error generating random number: {str(e)}"


# Available tool classes that can be instantiated
AVAILABLE_TOOLS: Dict[str, Type[BaseTool]] = {
    "currentdate": CurrentDateTool,
    "weather": WeatherTool,
    "random_number": RandomNumberTool
}


def register_tool(tool_type: str, tool_class: Type[BaseTool]) -> None:
    """Register a new tool type at runtime.
    
    Parameters
    ----------
    tool_type : str
        The type identifier for the tool
    tool_class : Type[BaseTool]
        The tool class to register
    """
    if not issubclass(tool_class, BaseTool):
        raise ValueError("Tool class must inherit from BaseTool")
    
    AVAILABLE_TOOLS[tool_type] = tool_class
    logger.info("Registered new tool type: %s", tool_type)


def load_tools_from_module(module_path: str) -> None:
    """Load tool classes from a Python module.
    
    Parameters
    ----------
    module_path : str
        Path to the Python module containing tool classes
    """
    try:
        spec = importlib.util.spec_from_file_location(
            "tools_module", 
            module_path
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {module_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find all BaseTool subclasses in the module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTool) and 
                    obj != BaseTool):
                register_tool(obj.name, obj)
    except Exception as e:
        logger.error(
            "Failed to load tools from module %s: %s", 
            module_path, 
            e
        )
        raise


def create_tool(config: Dict[str, Any]) -> BaseTool:
    """Create a tool instance from configuration.
    
    Parameters
    ----------
    config : Dict[str, Any]
        Tool configuration dictionary
        
    Returns
    -------
    BaseTool
        Instantiated tool
    """
    tool_type = config.get("type")
    if not tool_type:
        raise ValueError("Tool configuration must include 'type'")
        
    tool_class = AVAILABLE_TOOLS.get(tool_type)
    if not tool_class:
        raise ValueError(f"Unknown tool type: {tool_type}")
        
    return tool_class()


def get_tools(tool_configs: list[Dict[str, Any]]) -> Dict[str, BaseTool]:
    """Create tool instances from configuration list."""
    tools = {}
    for config in tool_configs:
        tool = create_tool(config)
        tools[tool.name] = tool
    return tools


def get_ollama_tools(tool_configs: list[Dict[str, Any]]) -> list:
    """Convert configured tools to Ollama format."""
    tools = []
    for config in tool_configs:
        tool = create_tool(config)
        tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema.model_json_schema()
            }
        })
    return tools 