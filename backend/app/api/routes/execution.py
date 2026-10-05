"""Code execution endpoints.

* ``POST /api/execution/run``    — run code, capture output, no grading.
* ``POST /api/execution/submit`` — run code against assertion test cases.

Both return the unified :class:`ExecutionResult`. Later phases will hang
behavior tracking and misconception analysis off ``/submit`` without changing
these signatures.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.validation import validate_code, validate_test_case_count
from app.models.execution import (
    ExecutionRequest,
    ExecutionResult,
    SubmitRequest,
)
from app.services.execution.runner import execute
from app.services.tasks import get_task

router = APIRouter(prefix="/execution", tags=["execution"])


@router.post("/run", response_model=ExecutionResult)
async def run_code(payload: ExecutionRequest) -> ExecutionResult:
    """Execute code without grading. Captures stdout/stderr and errors."""
    validate_code(payload.code)
    return execute(payload.code, tests=None)


@router.post("/submit", response_model=ExecutionResult)
async def submit_code(payload: SubmitRequest) -> ExecutionResult:
    """Execute code against test cases.

    Test cases come from ``test_cases`` if provided, otherwise from the task
    referenced by ``task_id``.
    """
    validate_code(payload.code)

    tests = payload.test_cases
    if tests is None and payload.task_id is not None:
        task = get_task(payload.task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        tests = task.test_cases

    if tests is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'test_cases' or a valid 'task_id'.",
        )

    validate_test_case_count(len(tests))
    return execute(payload.code, tests=tests)
