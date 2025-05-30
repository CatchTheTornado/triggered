import pytest
import os
from unittest.mock import patch, MagicMock

from triggered.tools import (
    BaseTool,
    ToolInput,
    WeatherTool,
    CurrentDateTool,
    RandomNumberTool,
    create_tool,
    get_tools,
    get_ollama_tools,
    register_tool,
    AVAILABLE_TOOLS
)
from triggered.models import (
    OllamaModel,
    DummyModel,
    get_model
)


# Test Tool Input Schemas
def test_tool_input_schemas():
    """Test that tool input schemas are properly defined."""
    # Test WeatherInput
    weather_input = WeatherTool.args_schema(city="London")
    assert weather_input.city == "London"
    
    # Test RandomNumberInput
    random_input = RandomNumberTool.args_schema(min_value=1, max_value=10)
    assert random_input.min_value == 1
    assert random_input.max_value == 10


# Test Tool Registration
def test_tool_registration():
    """Test tool registration system."""
    # Create a test tool
    class TestToolInput(ToolInput):
        test_param: str = "test"
    
    class TestTool(BaseTool):
        name: str = "test_tool"
        description: str = "Test tool"
        args_schema: type = TestToolInput
        
        async def _run(self, test_param: str) -> str:
            return f"Test: {test_param}"
    
    # Register the tool
    register_tool("test_tool", TestTool)
    assert "test_tool" in AVAILABLE_TOOLS
    assert AVAILABLE_TOOLS["test_tool"] == TestTool


# Test Tool Creation
def test_create_tool():
    """Test tool creation from config."""
    config = {
        "type": "random_number",
        "name": "random"
    }
    tool = create_tool(config)
    assert isinstance(tool, RandomNumberTool)
    assert tool.name == "random_number"


# Test Tool Execution
@pytest.mark.asyncio
async def test_tool_execution():
    """Test that tools execute properly."""
    # Test RandomNumberTool
    tool = RandomNumberTool()
    result = await tool._run(min_value=1, max_value=10)
    assert result.isdigit()
    assert 1 <= int(result) <= 10
    
    # Test CurrentDateTool
    tool = CurrentDateTool()
    result = await tool._run()
    assert len(result) == 10  # YYYY-MM-DD format
    assert result[4] == "-" and result[7] == "-"


# Test Weather Tool
@pytest.mark.asyncio
async def test_weather_tool():
    """Test weather tool with mocked API."""
    with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test_key"}):
        with patch("httpx.AsyncClient.get") as mock_get:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "weather": [{"main": "Cloudy"}],
                "main": {"temp": 20}
            }
            mock_get.return_value = mock_response
            
            tool = WeatherTool()
            result = await tool._run(city="London")
            assert "cloudy" in result.lower()
            assert "20°C" in result
            
            # Test error handling
            mock_response.status_code = 404
            mock_response.json.return_value = {"message": "City not found"}
            result = await tool._run(city="InvalidCity")
            assert "error" in result.lower()


# Test Ollama Model
@pytest.mark.asyncio
async def test_ollama_model():
    """Test Ollama model with mocked responses."""
    # Check if environment is set
    if not os.getenv("OLLAMA_MODEL"):
        import warnings
        warnings.warn(
            "OLLAMA_MODEL environment variable not set - "
            "some tests may be skipped"
        )
        return

    with patch("ollama.chat") as mock_chat:
        # Test successful response
        mock_chat.return_value = {
            "message": {
                "content": "Test response"
            }
        }
        
        model = OllamaModel()
        result = await model.ainvoke("test prompt")
        assert result == "Test response"
        
        # Test empty response
        mock_chat.return_value = None
        result = await model.ainvoke("test prompt")
        assert "Error: Empty response" in result
        
        # Test missing message
        mock_chat.return_value = {}
        result = await model.ainvoke("test prompt")
        assert "Error: Empty response" in result
        
        # Test missing content
        mock_chat.return_value = {"message": {}}
        result = await model.ainvoke("test prompt")
        assert "Error: Empty response" in result


# Test Model Factory
def test_get_model():
    """Test model factory function."""
    # Test dummy model fallback
    with patch.dict(os.environ, {"DISABLE_OLLAMA": "1"}):
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
        },
        {
            "type": "weather",
            "name": "weather"
        }
    ]
    
    # Test get_tools
    tools = get_tools(configs)
    assert len(tools) == 2
    assert isinstance(tools["random_number"], RandomNumberTool)
    assert isinstance(tools["weather"], WeatherTool)
    
    # Test get_ollama_tools
    ollama_tools = get_ollama_tools(configs)
    assert len(ollama_tools) == 2
    assert ollama_tools[0]["type"] == "function"
    assert ollama_tools[0]["function"]["name"] == "random_number"


# Test Error Handling
@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in tools and models."""
    # Test invalid tool type
    with pytest.raises(ValueError):
        create_tool({"type": "invalid_tool"})
    
    # Test model not found
    with patch("ollama.chat") as mock_chat:
        mock_chat.side_effect = Exception("model not found")
        with patch("ollama.pull") as mock_pull:
            mock_pull.side_effect = Exception("pull failed")
            model = OllamaModel()
            result = await model.ainvoke("test")
            assert "Error: Failed to load model" in result 