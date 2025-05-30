from typing import Dict, Type, Any
import datetime as _dt
from pydantic import BaseModel, Field
import httpx
import os


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
        return _dt.datetime.utcnow().strftime("%Y-%m-%d")


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


# Available tool classes that can be instantiated
AVAILABLE_TOOLS: Dict[str, Type[BaseTool]] = {
    "currentdate": CurrentDateTool,
    "weather": WeatherTool
}


def create_tool(tool_config: Dict[str, Any]) -> BaseTool:
    """Create a tool instance from configuration."""
    tool_type = tool_config.get("type")
    if not tool_type or tool_type not in AVAILABLE_TOOLS:
        raise ValueError(f"Unknown tool type: {tool_type}")
    
    tool_cls = AVAILABLE_TOOLS[tool_type]
    return tool_cls()


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