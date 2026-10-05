"""Student dashboard + knowledge-graph contracts.

These are READ-ONLY projections composed from existing Phase 5 (learner
profile, behavior events) and Phase 6 (challenge selector) data. No mastery,
misconception, or selection logic is defined here — only the shapes returned to
the student-facing UI.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.behavior import (
    ConceptMastery,
    MasteryTrendPoint,
    RecentMisconception,
)


class MasteryBand(str, Enum):
    """Human-facing band for the Debugly Mastery Indicator."""

    NOT_STARTED = "not_started"   # no attempts yet
    EMERGING = "emerging"         # < 35
    DEVELOPING = "developing"     # 35-59
    PROFICIENT = "proficient"     # 60-84
    STRONG = "strong"             # 85+


def band_for(mastery: float, attempts: int = 1) -> MasteryBand:
    """Map a mastery score to a band (purely presentational)."""
    if attempts == 0:
        return MasteryBand.NOT_STARTED
    if mastery >= 85:
        return MasteryBand.STRONG
    if mastery >= 60:
        return MasteryBand.PROFICIENT
    if mastery >= 35:
        return MasteryBand.DEVELOPING
    return MasteryBand.EMERGING


class OverallMastery(BaseModel):
    """Section A — the headline Debugly Mastery Indicator."""

    indicator: float = Field(description="0-100 Debugly Mastery Indicator (not a validated probability).")
    band: MasteryBand
    label: str = "Debugly Mastery Indicator"
    disclaimer: str = (
        "A Debugly indicator of demonstrated understanding, not a validated "
        "measure of ability."
    )
    trend: list[MasteryTrendPoint] = Field(default_factory=list)


class ConceptProgress(BaseModel):
    """Section B — per-concept progress (extends ConceptMastery with band + trend)."""

    concept_key: str
    mastery: float
    band: MasteryBand
    attempts: int
    successful_attempts: int
    has_persistent_gap: bool
    hint_dependency: float
    trend: list[float] = Field(default_factory=list)


class Bottleneck(BaseModel):
    """Section C — a misconception bottleneck with recovery context."""

    concept_key: str
    misconception_key: str
    occurrences: int
    persistent: bool
    hint_dependency: float
    recovery_successes: int = Field(
        description="Unaided successes after a correction (recovery evidence)."
    )
    concept_mastery: float


class TimelineEvent(BaseModel):
    """Section D — one meaningful learning event (no keystrokes)."""

    event_type: str
    concept_key: str | None = None
    misconception_key: str | None = None
    error_type: str | None = None
    hint_level: int | None = None
    difficulty: str | None = None
    label: str
    at: datetime


class RecommendedChallenge(BaseModel):
    """Section E — the next challenge target (from Phase 6 selector, read-only)."""

    available: bool
    concept_key: str | None = None
    concept_name: str | None = None
    misconception_key: str | None = None
    misconception_name: str | None = None
    difficulty: str | None = None
    task_type: str | None = None
    learning_objective: str | None = None
    reason: str | None = None


class DashboardResponse(BaseModel):
    """Full student dashboard payload."""

    user_id: str
    is_new_learner: bool
    overall: OverallMastery
    concepts: list[ConceptProgress]
    bottlenecks: list[Bottleneck]
    timeline: list[TimelineEvent]
    recommended_challenge: RecommendedChallenge


# ---- Knowledge graph ----

class GraphNodeType(str, Enum):
    STUDENT = "student"
    CONCEPT = "concept"
    MISCONCEPTION = "misconception"
    EVIDENCE = "evidence"
    INTERVENTION = "intervention"
    CHALLENGE = "challenge"
    OUTCOME = "outcome"


class GraphNode(BaseModel):
    id: str
    type: GraphNodeType
    label: str
    # Presentational health flag: True for mastered/healthy, False for a gap.
    healthy: bool | None = None
    meta: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str  # e.g. "struggles_with", "has_misconception", "triggered_by"


class KnowledgeGraph(BaseModel):
    user_id: str
    is_empty: bool
    nodes: list[GraphNode]
    edges: list[GraphEdge]
