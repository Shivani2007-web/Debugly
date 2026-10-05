"""Error evidence analysis.

Turns an :class:`ExecutionResult` (from Phase 2) into an :class:`ErrorFeatures`
snapshot: the primary exception type, the line it occurred on, and a coarse
classification the rules key off. Also surfaces per-test errors so a submission
that fails several cases with the same exception becomes stronger evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.execution import ExecutionResult, ExecutionStatus


@dataclass
class ErrorFeatures:
    """Error-channel facts extracted from an execution."""

    had_execution: bool = False
    status: str | None = None

    primary_error_type: str | None = None
    primary_error_message: str | None = None
    primary_error_line: int | None = None

    timed_out: bool = False
    syntax_error: bool = False
    syntax_error_line: int | None = None

    # Count of exception types seen across test cases, e.g. {"IndexError": 3}.
    error_type_counts: dict[str, int] = field(default_factory=dict)
    # Lines implicated by any error.
    error_lines: list[int] = field(default_factory=list)

    failed_test_count: int = 0
    total_test_count: int = 0


def analyze_execution(result: ExecutionResult | None) -> ErrorFeatures:
    """Extract error features from an execution result (or empty if None)."""
    features = ErrorFeatures()
    if result is None:
        return features

    features.had_execution = True
    features.status = result.status.value if isinstance(result.status, ExecutionStatus) else str(result.status)
    features.timed_out = features.status == ExecutionStatus.TIMEOUT.value
    features.syntax_error = features.status == ExecutionStatus.SYNTAX_ERROR.value

    if result.error is not None:
        features.primary_error_type = result.error.error_type
        features.primary_error_message = result.error.message
        features.primary_error_line = result.error.line
        if features.syntax_error:
            features.syntax_error_line = result.error.line
        if result.error.line is not None:
            features.error_lines.append(result.error.line)
        if result.error.error_type:
            features.error_type_counts[result.error.error_type] = (
                features.error_type_counts.get(result.error.error_type, 0) + 1
            )

    features.total_test_count = result.total_count
    for tr in result.test_results:
        if not tr.passed:
            features.failed_test_count += 1
        if tr.error and tr.error.error_type:
            features.error_type_counts[tr.error.error_type] = (
                features.error_type_counts.get(tr.error.error_type, 0) + 1
            )
            if tr.error.line is not None:
                features.error_lines.append(tr.error.line)
            # Promote the first per-test error to primary if none set yet.
            if features.primary_error_type is None:
                features.primary_error_type = tr.error.error_type
                features.primary_error_message = tr.error.message
                features.primary_error_line = tr.error.line

    return features
