"""Challenge generation orchestration.

Takes deterministic :class:`ChallengeConstraints`, asks the AI provider for
content, validates it into a :class:`Challenge`, and falls back to a
deterministic template on any failure (no provider, API error, malformed JSON,
schema violation). Both paths converge on the same validated Challenge.

Difficulty, concept and misconception are already fixed by the caller — the
generator never changes them, even if the model tries to.
"""

from __future__ import annotations

import json
import logging
import uuid

from pydantic import ValidationError

from app.models.challenge import (
    Challenge,
    ChallengeConstraints,
    ChallengeType,
)
from app.models.execution import TestCase
from app.services.ai.factory import get_provider
from app.services.ai.provider import AIProviderError
from app.services.challenge import prompts
from app.services.challenge.fallback import build_fallback_dict

logger = logging.getLogger("debugly.challenge")


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def _build_challenge(
    data: dict,
    constraints: ChallengeConstraints,
    *,
    generated_by: str,
    user_id: str | None,
) -> Challenge:
    """Validate a content dict into a Challenge, enforcing fixed fields.

    Raises ValidationError/ValueError/KeyError on malformed content so the
    caller can fall back.
    """
    # Test cases (may be empty for predict-the-output).
    raw_tests = data.get("test_cases") or []
    test_cases = [TestCase.model_validate(t) for t in raw_tests]

    # A code challenge MUST have gradeable tests; a predict challenge MUST have
    # an answer. Enforce so malformed/empty content falls back.
    if constraints.task_type == ChallengeType.PREDICT_THE_OUTPUT:
        if not data.get("predict_code") or not data.get("predict_answer"):
            raise ValueError("predict challenge missing code/answer")
    else:
        if not test_cases:
            raise ValueError("code challenge missing test cases")
        if not (data.get("starter_code") or "").strip():
            raise ValueError("code challenge missing starter code")

    return Challenge(
        id=uuid.uuid4().hex,
        title=str(data["title"]),
        description=str(data["description"]),
        concept_key=constraints.concept_key,          # fixed by backend
        misconception_key=constraints.misconception_key,  # fixed by backend
        difficulty=constraints.difficulty,            # fixed by backend
        task_type=constraints.task_type,              # fixed by backend
        starter_code=str(data.get("starter_code") or ""),
        expected_behavior=str(data.get("expected_behavior") or ""),
        test_cases=test_cases,
        predict_code=data.get("predict_code"),
        predict_answer=data.get("predict_answer"),
        learning_objective=str(
            data.get("learning_objective") or constraints.learning_objective
        ),
        hints_available=4,
        generated_by=generated_by,
        user_id=user_id,
    )


def generate_challenge(
    constraints: ChallengeConstraints, *, user_id: str | None = None
) -> Challenge:
    """Produce a validated Challenge for the given constraints."""
    provider = get_provider()

    if provider is not None:
        try:
            system, user = prompts.build_prompts(constraints)
            raw = provider.generate_json(system, user)
            data = _parse_json(raw)
            return _build_challenge(
                data, constraints, generated_by="gemini", user_id=user_id
            )
        except (AIProviderError, json.JSONDecodeError, ValidationError, ValueError, KeyError) as exc:
            logger.warning(
                "Challenge AI generation failed (%s); using fallback.",
                type(exc).__name__,
            )

    # Deterministic fallback (also used when no provider is configured).
    data = build_fallback_dict(constraints)
    return _build_challenge(data, constraints, generated_by="fallback", user_id=user_id)
