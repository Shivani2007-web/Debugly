"""Behavior-tracking and learner-profile contracts.

Design:
* Raw events (:class:`BehaviorEvent`) are an append-only evidence trail — they
  are stored separately from aggregated state so a mastery score can always be
  reconstructed from the events that produced it.
* The :class:`LearnerProfile` is the aggregate, with a per-concept
  :class:`ConceptStat` map plus a mastery trend history.
* No keystroke-level data is modeled; only meaningful learning events.

The event vocabulary is an enum but the payload is a free-form dict, so new
event kinds can be added without reshaping storage.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BehaviorEventType(str, Enum):
    """Meaningful learning events (NOT keystrokes)."""

    CODE_EXECUTION = "code_execution"
    SUBMISSION = "submission"
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    TEST_FAILURE = "test_failure"
    SUCCESSFUL_EXECUTION = "successful_execution"
    REGION_REPEATEDLY_MODIFIED = "region_repeatedly_modified"
    HINT_REQUESTED = "hint_requested"
    HINT_LEVEL_REACHED = "hint_level_reached"
    TUTOR_QUESTION_ANSWERED = "tutor_question_answered"
    TUTOR_ANSWER_CORRECT = "tutor_answer_correct"
    TUTOR_ANSWER_INCORRECT = "tutor_answer_incorrect"
    SUCCESSFUL_CORRECTION = "successful_correction"
    MISCONCEPTION_DETECTED = "misconception_detected"
    # Reserved for later phases (challenges, smart reuse); modeled now so the
    # vocabulary is stable.
    CHALLENGE_ATTEMPT = "challenge_attempt"
    CODE_REUSE_PASTE = "code_reuse_paste"


class BehaviorEvent(BaseModel):
    """A single recorded learning event (append-only)."""

    user_id: str
    session_id: str | None = None
    event_type: BehaviorEventType
    concept_key: str | None = Field(
        default=None, description="Concept this event relates to, if known."
    )
    misconception_key: str | None = Field(
        default=None, description="Misconception key, for misconception/error events."
    )
    error_type: str | None = None
    hint_level: int | None = None
    difficulty: str | None = Field(
        default=None, description="beginner|developing|intermediate|advanced, if applicable."
    )
    payload: dict = Field(default_factory=dict, description="Extensible extra detail.")
    created_at: datetime = Field(default_factory=_utcnow)


class ConceptStat(BaseModel):
    """Aggregated per-concept learner statistics."""

    concept_key: str
    attempts: int = 0
    successful_attempts: int = 0
    error_count: int = 0
    # Count of each misconception key encountered under this concept.
    misconception_counts: dict[str, int] = Field(default_factory=dict)
    # Count of each error type seen (for repeated-error detection).
    error_type_counts: dict[str, int] = Field(default_factory=dict)
    repeated_misconception_events: int = 0  # times a misconception recurred (>=2nd occurrence)
    hints_requested: int = 0
    max_hint_level_reached: int = 0
    corrections: int = 0                 # successful_correction events
    corrections_after_hint: int = 0      # correction that followed a hint
    unaided_successes_after_correction: int = 0  # improvement evidence
    last_difficulty_passed: str | None = None
    mastery: float = 0.0                 # Debugly Mastery Indicator, 0-100
    mastery_updated_at: datetime | None = None

    @property
    def has_persistent_gap(self) -> bool:
        """True when any single misconception recurred (persistent gap, not a one-off)."""
        return any(c >= 2 for c in self.misconception_counts.values())


class MasteryTrendPoint(BaseModel):
    """A timestamped mastery snapshot for a concept (trend history)."""

    concept_key: str
    mastery: float
    at: datetime = Field(default_factory=_utcnow)


class LearnerProfile(BaseModel):
    """Aggregated learner state across sessions (one per user)."""

    user_id: str
    concepts: dict[str, ConceptStat] = Field(default_factory=dict)
    trend: list[MasteryTrendPoint] = Field(default_factory=list)
    total_events: int = 0
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---- Read-side DTOs (API responses) ----

class ConceptMastery(BaseModel):
    """Concept mastery as surfaced to the client."""

    concept_key: str
    mastery: float
    attempts: int
    successful_attempts: int
    has_persistent_gap: bool
    hint_dependency: float = Field(
        description="hints_requested / attempts (0 when no attempts)."
    )


class RecentMisconception(BaseModel):
    concept_key: str
    misconception_key: str
    occurrences: int
    persistent: bool


class Recommendation(BaseModel):
    concept_key: str
    reason: str
    suggested_difficulty: str


class LearnerSummary(BaseModel):
    """Top-level learner summary for the client."""

    user_id: str
    overall_mastery: float
    concept_count: int
    total_events: int
    concepts: list[ConceptMastery]
    persistent_gaps: list[str]
    is_new_learner: bool


class EventRecordRequest(BaseModel):
    """Request to record one event (API input)."""

    user_id: str
    session_id: str | None = None
    event_type: BehaviorEventType
    concept_key: str | None = None
    misconception_key: str | None = None
    error_type: str | None = None
    hint_level: int | None = None
    difficulty: str | None = None
    payload: dict = Field(default_factory=dict)


class EventBatchRequest(BaseModel):
    """Batch of events (client flushes these on run/submit, not per keystroke)."""

    events: list[EventRecordRequest]
