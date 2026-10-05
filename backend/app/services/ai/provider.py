"""AI provider abstraction.

The tutor depends only on this interface, never on a concrete SDK. Swapping
Gemini for another provider (or a local model) is a new ``AIProvider`` subclass
plus a factory change — no tutor edits.

The contract is deliberately narrow: given a system instruction and a user
prompt, return raw text that is expected to be JSON. Parsing and validation
live in the tutor service, so providers stay dumb and interchangeable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class AIProviderError(Exception):
    """Raised when a provider cannot produce a response (API error, timeout, rate limit)."""


class AIProvider(ABC):
    """Minimal text-generation interface."""

    #: Human-readable provider name for logging/diagnostics.
    name: str = "base"

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether this provider is configured and usable."""
        raise NotImplementedError

    @abstractmethod
    def generate_json(self, system_instruction: str, user_prompt: str) -> str:
        """Return model output expected to be a JSON string.

        Must raise :class:`AIProviderError` on any failure so the caller can
        fall back deterministically.
        """
        raise NotImplementedError
