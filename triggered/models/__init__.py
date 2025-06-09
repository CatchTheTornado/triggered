import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
import os
from litellm import completion, ModelResponse
from ..tools import TOOL_REGISTRY
import json

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
        self.api_base = api_base or os.getenv("LITELLM_API_BASE", "")
        self.kwargs = kwargs

    def _convert_tools_to_litellm_format(self, tool_configs: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Convert tool configurations to LiteLLM format."""
        tools = []
        for config in tool_configs:
            # Handle both string and object formats
            if isinstance(config, str):
                tool_type = config
            else:
                tool_type = config.get("type")
                
            if tool_type not in TOOL_REGISTRY:
                logger.warning("Unknown tool type: %s", tool_type)
                continue
                
            tool_cls = TOOL_REGISTRY[tool_type]
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_cls.name,
                    "description": tool_cls.description,
                    "parameters": tool_cls.args_schema.model_json_schema(),
                }
            })
        return tools

    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON from text content.
        
        Looks for JSON objects in the text, either as a complete JSON string
        or as a code block with JSON content.
        """
        # Try to parse the entire text as JSON first
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass

        # Look for JSON in code blocks
        import re
        # Match JSON in code blocks, handling multiline content
        json_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
        matches = re.findall(json_pattern, text)
        if matches:
            try:
                # Clean up the matched JSON string
                json_str = matches[0]
                # Remove any leading/trailing whitespace and newlines
                json_str = json_str.strip()
                # Parse to validate it's JSON
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                # If parsing fails, try to clean up the JSON string
                try:
                    # Remove any extra whitespace between properties
                    json_str = re.sub(r'\s+', ' ', json_str)
                    # Remove any trailing commas
                    json_str = re.sub(r',\s*}', '}', json_str)
                    # Try parsing again
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON from code block: %s", json_str)
                    pass

        # If no JSON found in code blocks, try to find any JSON-like structure
        try:
            # Look for anything that looks like a JSON object
            json_pattern = r'(\{[\s\S]*?\})'
            matches = re.findall(json_pattern, text)
            if matches:
                for match in matches:
                    try:
                        # Clean up the potential JSON string
                        json_str = match.strip()
                        # Remove any extra whitespace
                        json_str = re.sub(r'\s+', ' ', json_str)
                        # Try parsing
                        json.loads(json_str)
                        return json_str
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error("Error while searching for JSON: %s", str(e))

        return None

    def _convert_tool_call_to_dict(self, tool_call) -> Dict[str, Any]:
        """Convert a tool call object to a dictionary format."""
        return {
            "id": tool_call.id,
            "type": tool_call.type,
            "function": {
                "name": tool_call.function.name,
                "arguments": tool_call.function.arguments
            }
        }

    async def ainvoke(self, prompt: str, tools: list | None = None) -> str:
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # If tools are provided, convert them to LiteLLM format and add to system message
            litellm_tools = None
            if tools:
                litellm_tools = self._convert_tools_to_litellm_format(tools)
                system_message = {
                    "role": "system",
                    "content": "You have access to the following tools:",
                    "tools": litellm_tools
                }
                messages.insert(0, system_message)

            # DEBUG: Log the outgoing request
            logger.debug(f"Sending to LiteLLM: messages={messages}, tools={litellm_tools}")
            
            # Run the completion in a thread pool since it's sync
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: completion(
                    tools=litellm_tools,
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
                
            message = response.choices[0].message
            
            # Handle tool calls
            if message.tool_calls:
                logger.info("Tool calls detected: %s", message.tool_calls)
                
                # Convert tool calls to dictionary format to avoid Pydantic warnings
                tool_calls_dict = [self._convert_tool_call_to_dict(tc) for tc in message.tool_calls]
                
                # Add the assistant's message to the conversation
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": tool_calls_dict
                })
                
                # Process each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    logger.info("Executing tool: %s with args: %s", tool_name, tool_args)
                    
                    if tool_name not in TOOL_REGISTRY:
                        logger.error("Unknown tool called: %s", tool_name)
                        return "Error: Unknown tool called"
                        
                    tool_cls = TOOL_REGISTRY[tool_name]
                    tool_instance = tool_cls()
                    result = await tool_instance._call(**tool_args)
                    
                    logger.info("Tool result: %s", result)
                    
                    # Add the tool response to the conversation
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_name,
                        "content": json.dumps(result)
                    })
                
                # Get a new response from the model with the tool results
                second_response = await loop.run_in_executor(
                    None,
                    lambda: completion(
                        model=self.model,
                        messages=messages,
                        api_base=self.api_base,
                        **self.kwargs
                    )
                )
                
                if not isinstance(second_response, ModelResponse):
                    logger.error("Invalid response type from second LiteLLM call: %s", type(second_response))
                    return "Error: Invalid response from model"
                    
                if not second_response.choices:
                    logger.error("No choices in second LiteLLM response: %s", second_response)
                    return "Error: No response from model"
                    
                final_message = second_response.choices[0].message
                if not final_message.content:
                    logger.error("No content in final LiteLLM response: %s", second_response)
                    return "Error: Empty response from model"
                    
                return final_message.content
            
            # Handle regular content
            content = message.content
            if not content:
                logger.error("No content in LiteLLM response: %s", response)
                return "Error: Empty response from model"
            
            # Try to extract JSON from the content
            json_content = self._extract_json_from_text(content)
            if json_content:
                logger.info("Extracted JSON from response: %s", json_content)
                return json_content
                
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
) -> BaseModelAdapter:
    """Get a configured model.
    
    Parameters
    ----------
    model : str | None
        Model name (e.g. "ollama/llama3.1"). Defaults to LITELLM_MODEL env var or "ollama/llama3.1"
    api_base : str | None
        API base URL. Defaults to LITELLM_API_BASE env var or "http://localhost:11434"
    **kwargs
        Additional arguments to pass to the model
        
    Returns
    -------
    BaseModelAdapter
        Configured model instance
    """
    # Create a cache key from the model name and API base
    cache_key = f"{model}:{api_base}"
    
    # Check if we have a cached instance
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]
    
    # Create a new instance
    if os.getenv("DISABLE_OLLAMA") == "1":
        instance = DummyModel()
    else:
        instance = LiteLLMModel(model=model, api_base=api_base, **kwargs)
    
    # Cache the instance
    _MODEL_CACHE[cache_key] = instance
    return instance 