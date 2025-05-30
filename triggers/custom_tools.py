from triggered.tools import BaseTool, ToolInput
from pydantic import Field
import random


class RandomNumberInput(ToolInput):
    """Input schema for RandomNumberTool."""
    min_value: int = Field(
        default=0,
        description="Minimum value (inclusive)"
    )
    max_value: int = Field(
        default=100,
        description="Maximum value (inclusive)"
    )


class RandomNumberTool(BaseTool):
    """Tool that generates a random number within a range."""
    name: str = "random_number"
    description: str = "Generates a random number within the specified range"
    args_schema: type[ToolInput] = RandomNumberInput

    async def _run(self, min_value: int = 0, max_value: int = 100) -> str:
        number = random.randint(min_value, max_value)
        return str(number) 