#### Custom Tools

To use custom tools, you need to:

1. Create a Python module with your tool implementation:
```python
# my_tools.py
from typing import Optional
from pydantic import BaseModel
from triggered.tools import Tool

# Define input schema for your tool
class WeatherToolInput(BaseModel):
    city: str
    country: Optional[str] = None
    units: str = "metric"

class WeatherTool(Tool):
    name = "weather"
    description = "Get current weather for a city"
    args_schema = WeatherToolInput

    async def execute(self, city: str, country: Optional[str] = None, units: str = "metric"):
        # Your tool implementation here
        return {
            "temperature": 25,
            "conditions": "sunny",
            "humidity": 60
        }
```

2. Create an `__init__.py` file in your tools directory to expose your tools:
```python
# tools/__init__.py
from .my_tools import WeatherTool

# List of tools to be automatically registered
__all__ = ["WeatherTool"]
```

3. Specify the path to your module in the configuration:
```json
{
  "trigger": {
    "type": "ai",
    "config": {
      "name": "custom-tools",
      "prompt": "Your prompt here",
      "custom_tools_path": "./path/to/your/tools.py",
      "tools": ["weather"]
    }
  }
}
```

4. Or use the tools directory structure for auto-discovery:
```
my_project/
├── tools/
│   ├── __init__.py
│   ├── weather_tool.py
│   └── other_tools.py
```

The `__init__.py` file should import and expose all your tools:
```python
# tools/__init__.py
from .weather_tool import WeatherTool
from .other_tools import OtherTool

# List of tools to be automatically registered
__all__ = [
    "WeatherTool",
    "OtherTool"
]
```

Your tools will be automatically discovered and registered when:
1. They are in the `tools` directory and properly exposed in `__init__.py`
2. They inherit from the `Tool` base class
3. They define a `name`, `description`, and `args_schema`
4. They implement the `execute` method

You can also manually register tools using the registry:
```python
from triggered.registry import register_tool
from .my_tools import WeatherTool

register_tool("weather", WeatherTool)
```

Tool Best Practices:
1. Always define an input schema using Pydantic models
2. Use descriptive names and descriptions
3. Handle errors gracefully
4. Document any required parameters
5. Use type hints for better IDE support
6. Keep tools focused and single-purpose
7. Use async/await for I/O operations

Example of a more complex tool with error handling:
```python
from typing import Optional, List
from pydantic import BaseModel, Field
from triggered.tools import Tool

class SearchToolInput(BaseModel):
    query: str
    max_results: int = Field(default=5, ge=1, le=20)
    filters: Optional[List[str]] = None

class SearchTool(Tool):
    name = "search"
    description = "Search for information with optional filters"
    args_schema = SearchToolInput

    async def execute(
        self,
        query: str,
        max_results: int = 5,
        filters: Optional[List[str]] = None
    ):
        try:
            # Your search implementation here
            results = await self._perform_search(query, max_results, filters)
            return {
                "results": results,
                "count": len(results),
                "query": query
            }
        except Exception as e:
            return {
                "error": str(e),
                "query": query
            }

    async def _perform_search(self, query: str, max_results: int, filters: Optional[List[str]]):
        # Implementation details
        pass
```
