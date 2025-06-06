import asyncio
import logging
from typing import Dict, Any, Optional
import os
from litellm import completion, ModelResponse

logger = logging.getLogger(__name__)


class BaseModelAdapter:
    async def ainvoke(self, prompt: str, **kwargs):  # noqa: D401
        raise NotImplementedError


class DummyModel(BaseModelAdapter):
    async def ainvoke(self, prompt: str, **kwargs):  # noqa: D401
        await asyncio.sleep(0.1)
        logger.info("Dummy model received prompt: %s", prompt)
        return "yes"


class LiteLLMModel(BaseModelAdapter):
    """Adapter that uses LiteLLM to interact with various LLM providers."""

    def __init__(
        self,
        model: str | None = None,
        api_base: str | None = None,
        **kwargs
    ) -> None:
        self.model = model or os.getenv("LITELLM_MODEL", "ollama/llama3.1")
        self.api_base = api_base or os.getenv("LITELLM_API_BASE", "http://localhost:11434")
        self.kwargs = kwargs

    async def ainvoke(self, prompt: str, tools: list | None = None) -> str:
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # If tools are provided, add them to the system message
            if tools:
                system_message = {
                    "role": "system",
                    "content": "You have access to the following tools:",
                    "tools": tools
                }
                messages.insert(0, system_message)
            
            # Run the completion in a thread pool since it's sync
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: completion(
                    model=self.model,
                    messages=messages,
                    api_base=self.api_base,
                    **self.kwargs
                )
            )
            
            if not isinstance(response, ModelResponse):
                logger.error("Invalid response type from LiteLLM: %s", type(response))
                return "Error: Invalid response from model"
                
            if not response.choices:
                logger.error("No choices in LiteLLM response: %s", response)
                return "Error: No response from model"
                
            content = response.choices[0].message.content
            if not content:
                logger.error("No content in LiteLLM response: %s", response)
                return "Error: Empty response from model"
                
            return content
            
        except Exception as e:
            logger.error("LiteLLM API error: %s", str(e))
            return f"Error: {str(e)}"


# fallback detection
try:
    _test = os.getenv("DISABLE_LITELLM")  # to optionally skip
    _LITELLM_AVAILABLE = True if _test is None else False
except Exception:
    _LITELLM_AVAILABLE = False


_MODEL_CACHE: Dict[str, BaseModelAdapter] = {}


def get_model(
    model: str | None = None,
    api_base: str | None = None,
    **kwargs
) -> LiteLLMModel:
    """Get a configured LiteLLM model.
    
    Parameters
    ----------
    model : str | None
        Model name (e.g. "ollama/llama3.1"). Defaults to LITELLM_MODEL env var or "ollama/llama3.1"
    api_base : str | None
        API base URL. Defaults to LITELLM_API_BASE env var or "http://localhost:11434"
    **kwargs
        Additional arguments to pass to LiteLLM
        
    Returns
    -------
    LiteLLMModel
        Configured LiteLLM model instance
    """
    return LiteLLMModel(model=model, api_base=api_base, **kwargs) 