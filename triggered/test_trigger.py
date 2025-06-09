from typing import Any, Dict
from pydantic import Field
from .core import Trigger, BaseConfig


class TestTriggerConfig(BaseConfig):
    """Configuration for the test trigger."""
    interval: int = Field(description="Interval in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")


class TestTrigger(Trigger):
    """A test trigger implementation."""
    config_model = TestTriggerConfig

    async def watch(self, queue_put) -> None:
        """Test watch implementation."""
        pass

    async def check(self) -> None:
        """Test check implementation."""
        pass 