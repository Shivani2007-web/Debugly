"""Execution domain contracts.

These Pydantic models are the shared language between the frontend, the
execution service, and (in later phases) the misconception engine, behavior
tracker and tutor. Keeping them stable and explicit means new phases plug in
without reshaping the core request/response.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExecutionStatus(str, Enum):
    """Top-level outcome of running a submission."""

    SUCCESS = "success"            # ran to completion, all tests passed (submit) or no error (run)
    TEST_FAILED = "test_failed"    # ran, but one or more assertion tests failed
    SYNTAX_ERROR = "syntax_error"  # code did not compile
    RUNTIME_ERROR = "runtime_error"  # raised an uncaught exception while running
    TIMEOUT = "timeout"            # exceeded the wall-clock limit and was killed
    INTERNAL_ERROR = "internal_error"  # sandbox/harness failure, not the student's fault


class ErrorInfo(BaseModel):
    """Structured error detail.

    This is intentionally richer than a raw traceback string: later phases
    (error analysis, misconception detection) consume ``error_type`` and
    ``line`` as evidence, so we capture them as first-class fields now.
    """

    error_type: str | None = Field(
        default=None, description="Exception class name, e.g. 'IndexError'."
    )
    message: str | None = Field(default=None, description="Human-readable error message.")
    line: int | None = Field(
        default=None, description="1-based line in the student's code, if known."
    )
    traceback: str | None = Field(default=None, description="Full traceback text, truncated.")


class TestCase(BaseModel):
    """A single assertion-based test for a task.

    The MVP execution model (agreed in Phase 1) is: call the student's
    ``function_name`` with ``args`` and compare the return value against
    ``expected``. ``name`` is shown in the results panel. ``hidden`` tests run
    but their inputs are not revealed to the student.
    """

    name: str
    function_name: str
    args: list = Field(default_factory=list)
    kwargs: dict = Field(default_factory=dict)
    expected: object = None
    hidden: bool = False


class TestResult(BaseModel):
    """Outcome of one test case."""

    name: str
    passed: bool
    expected: object = None
    actual: object = None
    error: ErrorInfo | None = None
    hidden: bool = False


class ExecutionRequest(BaseModel):
    """Request body for /run.

    A plain run executes the code and captures stdout/stderr with no grading.
    ``session_id`` is optional now; later phases attach runs to a session for
    behavior tracking.
    """

    code: str
    session_id: str | None = None


class SubmitRequest(BaseModel):
    """Request body for /submit.

    Either ``task_id`` (resolve test cases from the seeded task) or an explicit
    ``test_cases`` list may be supplied. Explicit cases take precedence.
    """

    code: str
    task_id: str | None = None
    test_cases: list[TestCase] | None = None
    session_id: str | None = None


class ExecutionResult(BaseModel):
    """Unified result returned by both /run and /submit.

    ``test_results`` is empty for a plain run. ``error`` is populated for
    syntax/runtime/timeout outcomes. ``truncated`` signals that stdout/stderr
    hit the output cap. The misconception engine (Phase 3) will read ``error``
    and ``test_results`` as evidence without any schema change here.
    """

    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    error: ErrorInfo | None = None
    test_results: list[TestResult] = Field(default_factory=list)
    passed_count: int = 0
    total_count: int = 0
    duration_ms: int = 0
    truncated: bool = False
