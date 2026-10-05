"""Socratic tutor orchestration.

Flow for a hint:
  1. Determine the hint level (advance server-side state unless answering).
  2. Build structured prompts.
  3. Ask the AI provider for JSON; on ANY failure, use the deterministic
     fallback for the same level.
  4. Validate/parse into a TutorResponse. Enforce guardrails that the model
     cannot bypass: grounding to the engine's misconception, and level
     consistency.

This module is the ONLY place that decides levels and enforces grounding, so
the policy lives in one spot.
"""

from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from app.models.tutor import (
    HintLevel,
    NextAction,
    RobotState,
    TutorInteractionType,
    TutorRequest,
    TutorResponse,
)
from app.services.ai.fallback import build_fallback_json
from app.services.ai.factory import get_provider
from app.services.ai.provider import AIProviderError
from app.services.tutor.prompts import build_prompts
from app.services.tutor.state import hint_state

logger = logging.getLogger("debugly.tutor")


def _resolve_level(req: TutorRequest) -> int:
    """Decide the hint level for this interaction.

    - FEEDBACK / EXPLAIN don't use a level (returned as current, unused).
    - A wrong-answer retry stays at the current level (don't escalate on a
      wrong answer; re-ask the same level from another angle).
    - A normal hint request advances to the next level.
    """
    mkey = req.misconception.misconception_key if req.misconception else None

    if req.interaction != TutorInteractionType.HINT:
        return max(hint_state.current_level(req.session_id, mkey), 1)

    if req.answer_was_correct is False:
        # Stay at the current level (at least 1).
        return max(hint_state.current_level(req.session_id, mkey), 1)

    return hint_state.advance(req.session_id, mkey)


def _parse_response(raw: str) -> dict:
    """Parse model/fallback JSON, tolerating accidental markdown fences."""
    text = raw.strip()
    if text.startswith("```"):
        # Strip ```json ... ``` fences if a model added them.
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def _coerce_to_response(data: dict, req: TutorRequest, level: int, is_fallback: bool) -> TutorResponse:
    """Validate a dict into TutorResponse and enforce grounding guardrails."""
    resp = TutorResponse.model_validate(data)

    # Guardrail: ground the response in the engine's misconception; the model
    # cannot invent a different one. We only ever echo the engine's key.
    resp.grounded_in = req.misconception.misconception_key if req.misconception else None
    resp.is_fallback = is_fallback

    # Guardrail: keep hint_level consistent with server state for hints.
    if req.interaction == TutorInteractionType.HINT:
        resp.hint_level = HintLevel(level)
    else:
        resp.hint_level = None

    return resp


def _fallback_response(req: TutorRequest, level: int) -> TutorResponse:
    data = _parse_response(build_fallback_json(req, level))
    return _coerce_to_response(data, req, level, is_fallback=True)


def generate(req: TutorRequest) -> TutorResponse:
    """Produce a structured tutor response for the request."""
    level = _resolve_level(req)
    provider = get_provider()

    if provider is None:
        return _fallback_response(req, level)

    try:
        system, user = build_prompts(req, level)
        raw = provider.generate_json(system, user)
        data = _parse_response(raw)
        return _coerce_to_response(data, req, level, is_fallback=False)
    except (AIProviderError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        logger.warning("Tutor AI path failed (%s); using fallback.", type(exc).__name__)
        return _fallback_response(req, level)


def on_successful_correction(session_id: str, misconception_key: str | None) -> None:
    """Reset hint progression after the student fixes the issue."""
    hint_state.reset(session_id, misconception_key)
