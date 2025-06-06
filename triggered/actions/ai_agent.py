import logging

from ..core import Action, TriggerContext
from ..models import get_model
from ..registry import register_action
from ..config_schema import ConfigSchema, ConfigField

logger = logging.getLogger(__name__)


@register_action("ai_agent")
class AIAgentAction(Action):
    """Action that invokes an AI model with given prompt and tools."""

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="model",
                type="string",
                description="Model to use",
                default="local",
                required=False
            ),
            ConfigField(
                name="prompt",
                type="string",
                description="AI prompt with variables like {var}",
                required=True
            ),
            ConfigField(
                name="tools",
                type="array",
                description="List of tools to use",
                default=[],
                required=False
            )
        ])

    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        model_name: str = self.config.get("model", "local")
        prompt: str = self.config["prompt"]
        tools = self.config.get("tools", [])

        model = get_model(model_name)
        rendered_prompt = prompt.format(**ctx.data)

        # Call the model with tools (conversion is now handled in the model)
        response = await model.ainvoke(rendered_prompt, tools=tools)
        logger.info("AI Agent response: %s", response)

        # Store the result in the context for downstream actions
        ctx.data["result"] = response

        # Optionally pass result downstream? Could set ctx.data["result"] 