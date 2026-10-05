"""Challenge endpoints.

* POST /api/challenges/generate   — personalize + generate a challenge for a learner.
* GET  /api/challenges/{id}        — student-safe view (NO hidden answers).
* POST /api/challenges/{id}/submit — grade a submission, record result, update mastery.

The full Challenge (with answers) is never returned; only ChallengeView.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.validation import validate_code, validate_text
from app.models.challenge import (
    ChallengeView,
    GenerateChallengeRequest,
    SubmitChallengeRequest,
    SubmitChallengeResponse,
    to_view,
)
from app.services.challenge.deps import get_challenge_service

router = APIRouter(prefix="/challenges", tags=["challenges"])


@router.post("/generate", response_model=ChallengeView)
async def generate_challenge_route(payload: GenerateChallengeRequest) -> ChallengeView:
    """Select a target from the learner profile and generate a challenge."""
    service = get_challenge_service()
    challenge = await service.generate_for_learner(
        payload.user_id,
        preferred_concept=payload.concept_key,
        task_type=payload.task_type,
    )
    # Return ONLY the student-safe view.
    return to_view(challenge)


@router.get("/{challenge_id}", response_model=ChallengeView)
async def get_challenge_route(challenge_id: str) -> ChallengeView:
    """Return the student-safe view of a challenge."""
    service = get_challenge_service()
    challenge = await service._store.get_challenge(challenge_id)
    if challenge is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return to_view(challenge)


@router.post("/{challenge_id}/submit", response_model=SubmitChallengeResponse)
async def submit_challenge_route(
    challenge_id: str, payload: SubmitChallengeRequest
) -> SubmitChallengeResponse:
    """Grade a submission, record the result, and update mastery via Phase 5."""
    # Code challenges carry code; predict challenges carry text. Validate both.
    validate_code(payload.code, field="code", required=False)
    validate_text(payload.predicted_output, field="predicted_output")
    service = get_challenge_service()
    response = await service.submit(challenge_id, payload)
    if response is None:
        raise HTTPException(status_code=404, detail="Challenge not found")
    return response
