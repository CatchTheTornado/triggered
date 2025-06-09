import psutil
from typing import Dict, Any
from pydantic import BaseModel

from triggered.tools import Tool
from triggered.registry import register_tool

class ProcessCheckerInput(BaseModel):
    """Input schema for process checker tool."""
    process_name: str = "Name of the process to check"

class ProcessCheckerTool(Tool):
    """Tool for checking if a specific process is running."""
    
    name = "process_checker"
    description = "Checks if a specific process is running"
    args_schema = ProcessCheckerInput

    async def _call(self, process_name: str) -> Dict[str, Any]:
        """Check if a process is running.
        
        Args:
            process_name: Name of the process to check
            
        Returns:
            Dict containing process status information
        """
        for proc in psutil.process_iter(['name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return {
                        "running": True,
                        "process_name": proc.info['name'],
                        "pid": proc.pid
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return {
            "running": False,
            "process_name": process_name
        }

# Register the tool
register_tool("process_checker", ProcessCheckerTool) 