from typing import Dict, Any
from pydantic import BaseModel

from triggered.tools import Tool

class ConfigDemoInput(BaseModel):
    """Input schema for config demo tool."""
    key: str = "Configuration key to retrieve"

class ConfigDemoTool(Tool):
    """Tool that demonstrates configuration usage."""
    
    name = "config_demo"
    description = "Retrieves a value from the configuration context"
    args_schema = ConfigDemoInput

    async def execute(self, key: str, ctx) -> Dict[str, Any]:
        """Get a value from the configuration context.
        
        Args:
            key: The configuration key to retrieve
            ctx: The trigger context containing configuration
            
        Returns:
            Dict containing the configuration value
        """
        value = ctx.config.options.get(key, "Not found")
        return {
            "key": key,
            "value": value
        } 