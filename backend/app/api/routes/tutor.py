"""Socratic tutor endpoints.

* POST /api/tutor/hint     — next progressive Socratic hint (level tracked).
* POST /api/tutor/explain  — conceptual explanation of the misconception.
* POST /api/tutor/feedback — encouraging feedback after a correction (resets level).

All three return a structured :class:`TutorResponse`. The Gemini key never
leaves the backend; failures degrade to a deterministic fallback.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models.tutor import (
    TutorInteractionType,
    TutorRequest,
    TutorResponse,
)
from app.services.tutor.socratic import generate, on_successful_correction

router = APIRouter(prefix="/tutor", tags=["tutor"])


@router.post("/hint", response_model=TutorResponse)
async def tutor_hint(payload: TutorRequest) -> TutorResponse:
    """Return the next Socratic hint, advancing the server-tracked level."""
    payload.interaction = TutorInteractionType.HINT
    return generate(payload)


@router.post("/explain", response_model=TutorResponse)
async def tutor_explain(payload: TutorRequest) -> TutorResponse:
    """Return a conceptual explanation grounded in the detected misconception."""
    payload.interaction = TutorInteractionType.EXPLAIN
    return generate(payload)


@router.post("/feedback", response_model=TutorResponse)
async def tutor_feedback(payload: TutorRequest) -> TutorResponse:
    """Return encouraging feedback after a correction and reset hint progression."""
    payload.interaction = TutorInteractionType.FEEDBACK
    response = generate(payload)
    mkey = payload.misconception.misconception_key if payload.misconception else None
    on_successful_correction(payload.session_id, mkey)
    return response
