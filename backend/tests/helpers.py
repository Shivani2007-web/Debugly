"""Test helpers for the misconception engine."""

from __future__ import annotations

from app.models.execution import (
    ErrorInfo,
    ExecutionResult,
    ExecutionStatus,
    TestResult,
)
from app.services.misconception.engine import diagnose


def make_execution(
    *,
    status: ExecutionStatus = ExecutionStatus.SUCCESS,
    error_type: str | None = None,
    error_message: str | None = None,
    error_line: int | None = None,
    failed_tests_with_error: list[str] | None = None,
) -> ExecutionResult:
    """Build an ExecutionResult for error-channel tests.

    ``failed_tests_with_error`` lets a test simulate N failing cases that all
    raised the same exception type, to exercise repetition weighting.
    """
    test_results: list[TestResult] = []
    if failed_tests_with_error:
        for i, et in enumerate(failed_tests_with_error):
            test_results.append(
                TestResult(
                    name=f"case {i}",
                    passed=False,
                    error=ErrorInfo(error_type=et, message=error_message, line=error_line),
                )
            )

    error = None
    if error_type is not None:
        error = ErrorInfo(error_type=error_type, message=error_message, line=error_line)

    return ExecutionResult(
        status=status,
        error=error,
        test_results=test_results,
        total_count=len(test_results),
        passed_count=0,
    )


def detect_keys(code: str, execution=None, target_concepts=None) -> dict[str, float]:
    """Run the engine and return {misconception_key: confidence}."""
    result = diagnose(code, execution_result=execution, target_concepts=target_concepts)
    return {m.misconception_key: m.confidence for m in result.misconceptions}


def diagnose_code(code: str, execution=None, target_concepts=None):
    """Return the full DiagnosisResult."""
    return diagnose(code, execution_result=execution, target_concepts=target_concepts)
