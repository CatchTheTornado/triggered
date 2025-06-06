import asyncio
from typing import Dict, Any
from jinja2 import Environment
import json
import os
from pathlib import Path
import logging
import re

from ..core import Trigger, TriggerContext
from ..registry import register_trigger
from ..models import get_model
from ..tools import get_tools, get_litellm_tools, load_tools_from_module

logger = logging.getLogger(__name__)


@register_trigger("ai")
class AITrigger(Trigger):
    """Trigger that uses an AI model to decide when to fire.

    The config must include:
    - prompt: str
    - model: str (optional, default "ollama/llama3.1")
    - interval: int seconds between evaluations (default 60)
    - tools: list of tool configurations (optional)
    - custom_tools_path: str (optional) path to Python module with custom tools
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name: str = config.get("model", "ollama/llama3.1")
        self.interval: int = int(config.get("interval", 60))
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

        # Template source and variables -----------------------------------
        DEFAULT_TEMPLATE = (
            "Your role is to decide whether to trigger an action based on the user prompt:  <user-prompt> {{ custom_prompt }} </user-prompt>\n\n"
            "Respond ONLY with JSON in the following schema:\n\n"
            "{ \"trigger\": <true|false>, "
            "\"reason\": \"<short explanation why you made the decision>\" }"
        )

        self.template_source = config.get("template", DEFAULT_TEMPLATE)
        self.prompt_vars = config.get("prompt_vars", {})

    def _extract_json(self, text: str) -> str | None:
        """Extract JSON from text, handling various formats."""
        # Try to find JSON between triple backticks
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)

        # Try to find JSON between curly braces
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)

        return None

    async def _evaluate(self):
        # Render prompt with Jinja2
        env = Environment()
        env.globals.update(get_tools(self.tool_configs))
        template = env.from_string(self.template_source)
        prompt_vars = {**self.prompt_vars, **os.environ}
        prompt = template.render(**prompt_vars)

        # Convert tools to LiteLLM format
        tools = get_litellm_tools(self.tool_configs)
        
        response = await self.model.ainvoke(prompt, tools=tools)

        # Extract JSON from response
        json_str = self._extract_json(response)
        if not json_str:
            logger.warning("No valid JSON found in response: %s", response)
            return {
                "trigger": False,
                "reason": "no valid JSON found",
                "raw": response,
            }

        try:
            obj = json.loads(json_str)
            obj["raw"] = response
            return obj  # includes raw
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON: %s", e)
            return {
                "trigger": False,
                "reason": f"invalid JSON: {str(e)}",
                "raw": response,
            }

    async def check(self):  # noqa: D401
        """One-shot evaluation used by CLI run-trigger."""
        obj = await self._evaluate()
        if obj and obj.get("trigger"):
            return TriggerContext(
                trigger_name=self.name,
                data=obj,
            )
        return None

    async def watch(self):
        """Continuously evaluate the trigger at the specified interval."""
        while True:
            try:
                ctx = await self.check()
                if ctx is not None:
                    yield ctx
            except Exception as e:
                logger.error("Error in AI trigger evaluation: %s", e)
            await asyncio.sleep(self.interval) 