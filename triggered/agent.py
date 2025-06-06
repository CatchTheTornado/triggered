import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path

from .models import get_model
from .tools import get_tools, load_tools_from_module

logger = logging.getLogger(__name__)


class Agent:
    """Agent that uses an AI model to execute tasks.

    The config must include:
    - model: str (optional, default "ollama/llama3.1")
    - tools: list of tool configurations (optional)
    - custom_tools_path: str (optional) path to Python module with custom tools
    """

    def __init__(self, config: Dict[str, Any]):
        self.model_name: str = config.get("model", "ollama/llama3.1")
        self.model = get_model(model=self.model_name)
        self.tool_configs = config.get("tools", [])
        
        # Load custom tools if specified
        custom_tools_path = config.get("custom_tools_path")
        if custom_tools_path:
            try:
                load_tools_from_module(custom_tools_path)
            except Exception as e:
                logger.error(f"Failed to load custom tools: {e}")
                raise

    async def execute(self, prompt: str) -> Dict[str, Any]:
        """Execute a task using the AI model.

        Args:
            prompt: The prompt to send to the model.

        Returns:
            Dict containing the model's response and any tool outputs.
        """
        # Call the model with tools (conversion is now handled in the model)
        response = await self.model.ainvoke(prompt, tools=self.tool_configs)
        return {"response": response} 