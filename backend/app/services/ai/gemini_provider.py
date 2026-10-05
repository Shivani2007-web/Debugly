"""Gemini AI provider.

Wraps the ``google-genai`` SDK. The API key is read from backend settings
(environment) only and never leaves the backend. The provider asks Gemini for
a JSON response via ``response_mime_type`` and returns the raw text; the tutor
service validates it.

If the SDK is not installed or no key is configured, ``available`` is False and
the factory selects the deterministic fallback instead — the app still runs.
"""

from __future__ import annotations

import logging

from app.services.ai.provider import AIProvider, AIProviderError

logger = logging.getLogger("debugly.ai.gemini")


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._client = None
        self._config_cls = None
        self._init_error: str | None = None

        if not api_key:
            self._init_error = "No GEMINI_API_KEY configured."
            return

        try:
            # Imported lazily so the backend runs without the SDK installed.
            from google import genai
            from google.genai import types

            self._client = genai.Client(api_key=api_key)
            self._config_cls = types.GenerateContentConfig
        except Exception as exc:  # pragma: no cover - env dependent
            self._init_error = f"Gemini SDK unavailable: {exc}"
            logger.warning(self._init_error)

    @property
    def available(self) -> bool:
        return self._client is not None

    def generate_json(self, system_instruction: str, user_prompt: str) -> str:
        if not self.available:
            raise AIProviderError(self._init_error or "Gemini provider not available.")

        try:
            config = self._config_cls(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.6,
                max_output_tokens=800,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=user_prompt,
                config=config,
            )
            text = getattr(response, "text", None)
            if not text:
                raise AIProviderError("Gemini returned an empty response.")
            return text
        except AIProviderError:
            raise
        except Exception as exc:  # network, rate limit, quota, etc.
            logger.warning("Gemini request failed: %s", exc)
            raise AIProviderError(str(exc)) from exc
