"""AI provider factory.

Selects the Gemini provider when a key is configured and the SDK loads;
otherwise returns None so the tutor service uses its deterministic fallback.
Cached so the client is built once per process.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.config import get_settings
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.provider import AIProvider

logger = logging.getLogger("debugly.ai")


@lru_cache
def get_provider() -> AIProvider | None:
    """Return the active AI provider, or None if none is available."""
    settings = get_settings()
    provider = GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
    if provider.available:
        logger.info("AI provider active: %s (model=%s)", provider.name, settings.gemini_model)
        return provider
    logger.info("No AI provider available; tutor will use deterministic fallback.")
    return None
