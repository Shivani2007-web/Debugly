"""Rule registry.

Rules register themselves via the ``@register`` decorator at import time. The
engine imports the ``rules`` package (which imports every rule module) and then
asks the registry for all instances. Adding a rule is: create a module, apply
the decorator — no engine edits.
"""

from __future__ import annotations

from app.services.misconception.base import Rule

_REGISTRY: list[type[Rule]] = []


def register(cls: type[Rule]) -> type[Rule]:
    """Class decorator that registers a Rule subclass."""
    if not getattr(cls, "key", ""):
        raise ValueError(f"Rule {cls.__name__} must define a non-empty 'key'.")
    _REGISTRY.append(cls)
    return cls


def all_rules() -> list[Rule]:
    """Instantiate and return every registered rule."""
    return [cls() for cls in _REGISTRY]
