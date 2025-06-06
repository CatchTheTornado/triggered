"""Triggered runtime engine package."""

from .core import Trigger, Action, TriggerAction  # noqa: F401
from .registry import register_trigger, register_action  # noqa: F401
from importlib import import_module
from .discovery import register_discovered_components

# Import built-in triggers/actions so registries are populated on import.
import_module("triggered.triggers")
import_module("triggered.actions")

# Register all discovered components
register_discovered_components()

__all__ = [
    "Trigger",
    "Action",
    "TriggerAction",
    "register_trigger",
    "register_action",
]

__version__ = "0.1.0" 