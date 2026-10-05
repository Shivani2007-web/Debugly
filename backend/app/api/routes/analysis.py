"""Misconception diagnosis endpoint.

``POST /api/analysis/diagnose`` runs the deterministic engine over the student's
code plus any execution evidence and returns ranked misconception verdicts.
No Gemini is involved — this is the pure analysis layer (Phase 3).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import ValidationError

from app.core.validation import validate_code
from app.models.execution import ExecutionResult
from app.models.misconception import DiagnosisRequest, DiagnosisResult
from app.services.misconception.engine import diagnose
from app.services.tasks import get_task

logger = logging.getLogger("debugly.analysis")

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/diagnose", response_model=DiagnosisResult)
async def diagnose_code(payload: DiagnosisRequest) -> DiagnosisResult:
    """Diagnose misconceptions from code (+ optional execution result)."""
    validate_code(payload.code)
    execution_result: ExecutionResult | None = None
    if payload.execution_result is not None:
        try:
            execution_result = ExecutionResult.model_validate(payload.execution_result)
        except ValidationError:
            logger.warning("Ignoring malformed execution_result in diagnose request")
            execution_result = None

    target_concepts: list[str] | None = None
    if payload.task_id:
        task = get_task(payload.task_id)
        if task is not None:
            target_concepts = task.concept_keys

    return diagnose(
        payload.code,
        execution_result=execution_result,
        target_concepts=target_concepts,
    )
