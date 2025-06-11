from typing import Dict, Any
from pydantic import BaseModel

from triggered.tools import Tool
from triggered.core import TriggerContext

class ConfigDemoInput(BaseModel):
    """Input schema for config demo tool."""
    key: str = "Configuration key to retrieve"

class ConfigDemoTool(Tool):
    """Tool that demonstrates configuration usage."""
    
    name = "config_demo"
    description = "Retrieves a value from the configuration context"
    args_schema = ConfigDemoInput

    async def execute(self, key: str, ctx: TriggerContext) -> Dict[str, Any]:
        """Get a value from the configuration context.
        
        Args:
            key: The configuration key to retrieve
            ctx: The trigger context containing parameters
            
        Returns:
            Dict containing the configuration value
        """
        value = ctx.params.get(key, "Not found")
        return {
            "key": key,
            "value": value
        } 