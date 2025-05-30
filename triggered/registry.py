from typing import Dict, Type, Callable

from .core import Trigger, Action

TRIGGER_REGISTRY: Dict[str, Type[Trigger]] = {}
ACTION_REGISTRY: Dict[str, Type[Action]] = {}


def register_trigger(name: str) -> Callable[[Type[Trigger]], Type[Trigger]]:
    """Decorator to register a Trigger subclass under a given name."""

    def decorator(cls: Type[Trigger]) -> Type[Trigger]:
        TRIGGER_REGISTRY[name] = cls
        return cls

    return decorator


def register_action(name: str) -> Callable[[Type[Action]], Type[Action]]:
    """Decorator to register an Action subclass under a given name."""

    def decorator(cls: Type[Action]) -> Type[Action]:
        ACTION_REGISTRY[name] = cls
        return cls

    return decorator


def get_trigger(name: str) -> Type[Trigger]:
    if name not in TRIGGER_REGISTRY:
        raise KeyError(f"Trigger '{name}' not found in registry")
    return TRIGGER_REGISTRY[name]


def get_action(name: str) -> Type[Action]:
    if name not in ACTION_REGISTRY:
        raise KeyError(f"Action '{name}' not found in registry")
    return ACTION_REGISTRY[name] 