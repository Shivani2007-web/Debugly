"""Misconception domain contracts.

These models are what the deterministic analysis layer (Phase 3) produces and
what the Socratic tutor (Phase 4), behavior tracker (Phase 5) and knowledge
graph (Phase 7) will consume. The verdict shape matches the product brief:
concept, misconception, confidence, evidence, line numbers, and an optional
error type.

Confidence is deliberately framed as *the system's confidence*, aggregated
from weighted evidence and capped — it is NOT a scientifically validated
probability.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class EvidenceWeight(float, Enum):
    """Discrete evidence strengths.

    Weights are intentionally coarse. The engine combines them with a
    diminishing-returns aggregation so that one WEAK signal alone can never
    reach the reporting threshold — multiple or stronger signals are required.
    """

    WEAK = 0.25
    MEDIUM = 0.45
    STRONG = 0.7


class EvidenceSource(str, Enum):
    """Which evidence channel produced a signal (per the hybrid architecture)."""

    CODE = "code"          # AST / structural
    ERROR = "error"        # compiler / runtime / exception
    BEHAVIOR = "behavior"  # attempts, repeats, timing (Phase 5)


class Evidence(BaseModel):
    """A single piece of supporting evidence for a misconception."""

    source: EvidenceSource
    weight: EvidenceWeight
    detail: str = Field(description="Human-readable description of the signal.")
    line: int | None = Field(
        default=None, description="1-based line in student code, if applicable."
    )
    error_type: str | None = Field(
        default=None, description="Exception type, if this is error evidence."
    )


class DetectedMisconception(BaseModel):
    """A ranked misconception verdict produced by the engine."""

    concept: str = Field(description="The concept area, e.g. 'List Indexing'.")
    misconception_key: str = Field(description="Stable key, e.g. 'off_by_one'.")
    misconception: str = Field(description="Human-readable misconception name.")
    confidence: float = Field(
        ge=0.0, le=1.0, description="System confidence (aggregated, capped)."
    )
    evidence: list[Evidence] = Field(default_factory=list)
    lines: list[int] = Field(
        default_factory=list, description="Relevant 1-based line numbers."
    )
    error_type: str | None = Field(default=None)


class DiagnosisRequest(BaseModel):
    """Request body for /api/analysis/diagnose.

    ``code`` is required. ``execution_result`` is optional: when the client has
    already run/submitted, passing the result enriches detection with error
    evidence. ``task_id`` lets the engine know the targeted concepts (used to
    gently prioritise, never to fabricate, verdicts).
    """

    code: str
    execution_result: dict | None = None
    task_id: str | None = None
    session_id: str | None = None


class DiagnosisResult(BaseModel):
    """Full diagnosis payload returned to the client."""

    misconceptions: list[DetectedMisconception] = Field(default_factory=list)
    analyzed_lines: int = 0
    had_execution_evidence: bool = False
