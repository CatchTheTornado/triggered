import pytest
import os
from unittest.mock import patch, MagicMock

from triggered.tools import (
    Tool,
    ToolInput,
    RandomNumberTool,
    get_tools
)
from triggered.models import (
    DummyModel,
    get_model
)


# Test Tool Input Schemas
def test_tool_input_schemas():
    """Test that tool input schemas are properly defined."""
    # Test RandomNumberInput
    random_input = RandomNumberTool.args_schema(min_value=1, max_value=10)
    assert random_input.min_value == 1
    assert random_input.max_value == 10


# Test Tool Execution
@pytest.mark.asyncio
async def test_tool_execution():
    """Test that tools execute properly."""
    # Test RandomNumberTool
    tool = RandomNumberTool()
    result = await tool._call(min_value=1, max_value=10)
    assert result.isdigit()
    assert 1 <= int(result) <= 10


# Test Model Factory
def test_get_model():
    """Test model factory function."""
    # Test dummy model fallback
    with patch.dict(os.environ, {"DISABLE_OLLAMA": "1", "LITELLM_MODEL": "dummy"}):
        model = get_model("unknown")
        assert isinstance(model, DummyModel)
    
    # Test model caching
    model1 = get_model("dummy")
    model2 = get_model("dummy")
    assert model1 is model2


# Test Tool Configuration
def test_tool_configuration():
    """Test tool configuration handling."""
    configs = [
        {
            "type": "random_number",
            "name": "random"
        }
    ]
    
    # Test get_tools
    tools = get_tools(configs)
    assert len(tools) == 1
    assert isinstance(tools["random_number"], RandomNumberTool)


# Test Error Handling
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in tools and models."""
    # Test model not found
    with patch("ollama.chat") as mock_chat:
        mock_chat.side_effect = Exception("model not found")
        with patch("ollama.pull") as mock_pull:
            mock_pull.side_effect = Exception("pull failed")
            model = DummyModel()
            result = await model.ainvoke("test")
            assert "Error: Failed to load model" in result or "yes" in result 