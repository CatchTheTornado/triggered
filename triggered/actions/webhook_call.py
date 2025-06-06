from typing import Any

import httpx

from ..core import Action, TriggerContext
from ..registry import register_action
from ..config_schema import ConfigSchema, ConfigField


@register_action("webhook_call")
class WebhookCallAction(Action):
    """Action that performs an HTTP POST to a configured URL.

    Config keys:
    - url: str, destination
    - payload: dict | str (optional) with template variables like ``{var}``
    - headers: dict (optional)
    """

    @classmethod
    def get_config_schema(cls) -> 'ConfigSchema':
        """Return the configuration schema for this action type."""
        return ConfigSchema(fields=[
            ConfigField(
                name="url",
                type="string",
                description="Destination URL for the webhook call",
                required=True
            ),
            ConfigField(
                name="payload",
                type="string",
                description="Payload template with variables like {var}",
                required=False
            ),
            ConfigField(
                name="headers",
                type="string",
                description="HTTP headers as JSON string",
                required=False
            )
        ])

    async def execute(self, ctx: TriggerContext) -> None:  # noqa: D401
        url: str = self.config["url"]
        payload_template = self.config.get("payload", {})
        headers = self.config.get("headers", {})

        payload = self._render_template(payload_template, ctx)

        async with httpx.AsyncClient() as client:
            await client.post(url, json=payload, headers=headers)

    def _render_template(self, tmpl: Any, ctx: TriggerContext):  # noqa: ANN001
        """Very naive Jinja-like variable substitution inside payload."""
        if isinstance(tmpl, str):
            return tmpl.format(**ctx.data)
        if isinstance(tmpl, dict):
            return {k: self._render_template(v, ctx) for k, v in tmpl.items()}
        if isinstance(tmpl, list):
            return [self._render_template(v, ctx) for v in tmpl]
        return tmpl 