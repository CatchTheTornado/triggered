import logging

from ..core import Action, TriggerContext
from ..models import get_model
from ..registry import register_action

logger = logging.getLogger(__name__)


@register_action("ai_agent")
class AIAgentAction(Action):
    """Action that invokes an AI model with given prompt and tools."""

    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        model_name: str = self.config.get("model", "local")
        prompt: str = self.config["prompt"]
        tools = self.config.get("tools", [])

        model = get_model(model_name)
        rendered_prompt = prompt.format(**ctx.data)

        # For now, we simply call the model and log the result.
        response = await model.ainvoke(rendered_prompt, tools=tools)
        logger.info("AI Agent response: %s", response)

        # Optionally pass result downstream? Could set ctx.data["result"] 