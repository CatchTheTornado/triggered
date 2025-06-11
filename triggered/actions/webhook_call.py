from typing import Any

import httpx

from ..core import Action, TriggerContext, BaseConfig
from ..registry import register_action
from ..config_schema import ConfigSchema, ConfigField
from pydantic import Field


class WebhookCallConfig(BaseConfig):
    """Configuration model for webhook call action."""
    url: str = Field(description="Destination URL for the webhook call (supports ${var} substitution)")
    payload: dict = Field(default_factory=dict, description="Payload template with variables like ${var}")
    headers: dict = Field(default_factory=dict, description="HTTP headers with variables like ${var}")


@register_action("webhook_call")
class WebhookCallAction(Action):
    """Action that performs an HTTP POST to a configured URL.

    Config keys:
    - url: str, destination (supports ${var} substitution)
    - payload: dict | str (optional) with template variables like ${var}
    - headers: dict (optional) with template variables like ${var}

    Variable substitution:
    - ${paramName} - from trigger-action params
    - ${dataName} - from trigger data
    - ${ENV_VAR} - from environment variables
    """
    config_model = WebhookCallConfig

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="url",
                type="string",
                description="Destination URL for the webhook call (supports ${var} substitution)",
                required=True
            ),
            ConfigField(
                name="payload",
                type="object",
                description="Payload template with variables like ${var}",
                required=False
            ),
            ConfigField(
                name="headers",
                type="object",
                description="HTTP headers with variables like ${var}",
                required=False
            )
        ])

    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        # Substitute variables in URL
        url = self._substitute_vars(self.config.url, ctx)
        
        # Substitute variables in headers
        headers = self._substitute_vars(self.config.headers, ctx)
        
        # Handle payload - if it's a string "${data}", use the entire trigger data
        if isinstance(self.config.payload, str) and self.config.payload == "${data}":
            payload = ctx.data
        else:
            payload = self._substitute_vars(self.config.payload, ctx)

        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=headers)

    def _substitute_vars(self, value: Any, ctx: TriggerContext) -> Any:
        """Substitute variables in a value using context data, params, and env vars.
        
        Supports:
        - ${paramName} - from trigger-action params
        - ${dataName} - from trigger data
        - ${ENV_VAR} - from environment variables
        """
        if isinstance(value, str):
            # First resolve environment variables
            value = ctx.resolve_env_vars(value)
            
            # Then resolve params and data
            try:
                return value.format(**ctx.params, **ctx.data)
            except KeyError as e:
                # If a variable is not found, keep the original ${var} in the string
                return value
            
        if isinstance(value, dict):
            return {k: self._substitute_vars(v, ctx) for k, v in value.items()}
        if isinstance(value, list):
            return [self._substitute_vars(v, ctx) for v in value]
        return value 