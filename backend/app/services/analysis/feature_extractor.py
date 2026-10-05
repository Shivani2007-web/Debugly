"""Unified feature object.

Combines the structural (:mod:`ast_analyzer`) and error (:mod:`error_analyzer`)
channels into a single :class:`Features` object that rules receive. Phase 5 will
add a ``behavior`` channel here; rules that don't use it are unaffected because
they only read the fields they need.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.execution import ExecutionResult
from app.services.analysis.ast_analyzer import CodeFeatures, analyze_code
from app.services.analysis.error_analyzer import ErrorFeatures, analyze_execution


@dataclass
class Features:
    """All evidence channels a rule may inspect."""

    code: CodeFeatures
    error: ErrorFeatures
    # Concepts the current task targets (used only to break ties, never to
    # invent verdicts). Optional.
    target_concepts: list[str] | None = None


def extract_features(
    code: str,
    execution_result: ExecutionResult | None = None,
    target_concepts: list[str] | None = None,
) -> Features:
    """Build the unified feature object from raw inputs."""
    return Features(
        code=analyze_code(code),
        error=analyze_execution(execution_result),
        target_concepts=target_concepts,
    )
