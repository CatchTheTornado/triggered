import pytest
from pydantic import Field, StrictInt
from triggered.core import Trigger, BaseConfig

class TestTriggerConfig(BaseConfig):
    interval: StrictInt = Field(description="Interval in seconds")
    max_retries: StrictInt = Field(default=3, description="Maximum number of retries")

class TestTrigger(Trigger):
    config_model = TestTriggerConfig
    async def watch(self, queue_put) -> None:
        pass
    async def check(self):
        pass

def test_valid_config():
    config = {"name": "test_trigger", "interval": 60, "max_retries": 5}
    is_valid, error = TestTrigger.validate_config(config)
    assert is_valid, f"Should be valid, got error: {error}"


def test_wrong_type():
    config = {"name": "test_trigger", "interval": "60", "max_retries": 5}
    is_valid, error = TestTrigger.validate_config(config)
    assert not is_valid and "interval" in error, "Should fail due to wrong type for 'interval'"

def test_default_value():
    config = {"name": "test_trigger", "interval": 60}
    is_valid, error = TestTrigger.validate_config(config)
    assert is_valid, f"Should be valid with default max_retries, got error: {error}" 