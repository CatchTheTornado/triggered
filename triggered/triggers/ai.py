import asyncio
from typing import Dict, Any
from jinja2 import Template
import json
import os
from pathlib import Path
import logging

from ..core import Trigger, TriggerContext
from ..registry import register_trigger
from ..models import get_model

logger = logging.getLogger(__name__)


@register_trigger("ai")
class AITrigger(Trigger):
    """Trigger that uses an AI model to decide when to fire.

    The config must include:
    - prompt: str
    - model: str (optional, default "local")
    - interval: int seconds between evaluations (default 60)
    - tools: list (optional)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name: str = config.get("model", "local")
        self.interval: int = int(config.get("interval", 60))
        self.model = get_model(self.model_name)
        self.tools = config.get("tools", [])
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

    async def _evaluate(self):
        # Render prompt with Jinja2
        template = Template(self.template_source)
        prompt_vars = {**self.prompt_vars, **os.environ}
        prompt = template.render(**prompt_vars)

        response = await self.model.ainvoke(prompt)

        def _strip_fences(text: str) -> str:
            txt = text.strip()
            if txt.startswith("```") and txt.endswith("```"):
                # remove leading and trailing backticks
                txt = txt.strip("`")
                # drop optional language tag on first line
                if txt.startswith("json"):
                    txt = txt[len("json"):]
                # strip again newlines and remaining backticks
                txt = txt.strip()
                if txt.endswith("```"):
                    txt = txt[:-3]
            return txt.strip()

        clean_response = _strip_fences(response)

        try:
            obj = json.loads(clean_response)
            obj["raw"] = response
            return obj  # includes raw
        except Exception:  # noqa: WPS420
            logger.warning("AI response not JSON: %s", response)
            return {
                "trigger": False,
                "reason": "invalid JSON",
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