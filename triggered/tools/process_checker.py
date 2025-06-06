import psutil
from typing import Dict, Any

from ..tools import Tool

class ProcessCheckerTool(Tool):
    """Tool for checking if a specific process is running."""
    
    name = "process_checker"
    description = "Checks if a specific process is running by name"

    async def execute(self, process_name: str, **kwargs) -> Dict[str, Any]:
        """Check if a process is running.
        
        Args:
            process_name: Name of the process to check (e.g., "Code" for VS Code)
            
        Returns:
            Dict containing:
                - running: bool indicating if process is running
                - count: number of matching processes
                - details: list of process details
        """
        matching_processes = []
        
        for proc in psutil.process_iter(['name', 'pid', 'create_time']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    matching_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'create_time': proc.info['create_time']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return {
            'running': len(matching_processes) > 0,
            'count': len(matching_processes),
            'details': matching_processes
        } 