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
from ..models import get_model, OllamaModel
from ..tools import get_tools, get_ollama_tools, load_tools_from_module

logger = logging.getLogger(__name__)


@register_trigger("ai")
class AITrigger(Trigger):
    """Trigger that uses an AI model to decide when to fire.

    The config must include:
    - prompt: str
    - model: str (optional, default "local")
    - interval: int seconds between evaluations (default 60)
    - tools: list of tool configurations (optional)
    - custom_tools_path: str (optional) path to Python module with custom tools
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name: str = config.get("model", "local")
        self.interval: int = int(config.get("interval", 60))
        self.model = get_model(self.model_name)
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
            "{{ custom_prompt }}\n\n"
            "Respond ONLY with JSON in the following schema:\n\n"
            "{ \"trigger\": <true|false>, "
            "\"reason\": \"<short explanation>\" }"
        )

        if "prompt_template_file" in config:
            self.template_source = (
                Path(config["prompt_template_file"]).read_text()
            )
        elif "prompt_template" in config:
            self.template_source = config["prompt_template"]
        else:
            self.template_source = DEFAULT_TEMPLATE

        # Variables injected into template (merge env later)
        self.prompt_vars = config.get("prompt_vars", {})

        # inline prompt becomes default custom_prompt variable
        inline_prompt = config.get("prompt", "")
        self.prompt_vars.setdefault("custom_prompt", inline_prompt)

    async def watch(self, queue_put):
        while True:
            decision_obj = await self._evaluate()
            if decision_obj and decision_obj.get("trigger"):
                ctx = TriggerContext(
                    trigger_name=self.name,
                    data={
                        "reason": decision_obj.get("reason", ""),
                        "trigger": True,
                        "raw": decision_obj.get("raw", ""),
                    },
                )
                await queue_put(ctx)
            await asyncio.sleep(self.interval)

    def _extract_json(self, text: str) -> str | None:
        """Extract JSON from text, handling various formats and positions.
        
        Parameters
        ----------
        text : str
            The text to extract JSON from
            
        Returns
        -------
        str | None
            The extracted JSON string or None if no valid JSON found
        """
        # First try to find JSON in code blocks
        code_block_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
        code_matches = re.findall(code_block_pattern, text)
        if code_matches:
            return code_matches[0].strip()

        # Then try to find any JSON object in the text
        json_pattern = r"(\{[\s\S]*?\})"
        json_matches = re.findall(json_pattern, text)
        
        for match in json_matches:
            try:
                # Try to parse as JSON to validate
                json.loads(match)
                return match.strip()
            except json.JSONDecodeError:
                continue
                
        return None

    async def _evaluate(self):
        # Render prompt with Jinja2
        env = Environment()
        env.globals.update(get_tools(self.tool_configs))
        template = env.from_string(self.template_source)
        prompt_vars = {**self.prompt_vars, **os.environ}
        prompt = template.render(**prompt_vars)

        # Convert tools to Ollama format if using Ollama model
        tools = None
        if isinstance(self.model, OllamaModel):
            tools = get_ollama_tools(self.tool_configs)
        
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
        if obj.get("trigger"):
            return TriggerContext(
                trigger_name=self.name,
                data=obj,
            )
        return None 