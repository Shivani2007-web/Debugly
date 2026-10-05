"""Tutor domain contracts.

The tutor turns a Phase 3 :class:`DetectedMisconception` into a Socratic
interaction. These models define the structured request/response so the client
never parses free-form text, and so the AI provider is asked for JSON matching
a known schema (validated server-side, with a deterministic fallback).
"""

from __future__ import annotations

from enum import Enum, IntEnum

from pydantic import BaseModel, Field

from app.models.misconception import DetectedMisconception


class HintLevel(IntEnum):
    """Progressive Socratic intervention levels."""

    QUESTION = 1          # make the student think
    DIRECTION = 2         # point toward the relevant concept
    CONCEPTUAL = 3        # explain the underlying principle
    STRONG_GUIDANCE = 4   # explicit enough to unblock, but not the full solution


class RobotState(str, Enum):
    """Visual states of the robot companion."""

    IDLE = "idle"
    THINKING = "thinking"
    CONCERNED = "concerned"
    ENCOURAGING = "encouraging"
    HAPPY = "happy"
    CELEBRATING = "celebrating"
    SAD = "sad"


class NextAction(str, Enum):
    """What the UI should offer the student next."""

    ANSWER_QUESTION = "answer_question"   # respond to a Socratic question
    REQUEST_NEXT_HINT = "request_next_hint"  # escalate to the next level
    TRY_AGAIN = "try_again"               # go edit the code and re-run
    CONTINUE = "continue"                 # acknowledge and move on


class TutorInteractionType(str, Enum):
    """Which tutor behavior is being requested."""

    HINT = "hint"
    EXPLAIN = "explain"
    FEEDBACK = "feedback"


class PriorAttempt(BaseModel):
    """A compact summary of a previous attempt (NOT full history).

    Only the minimal, relevant signal is passed to the model: the error type
    and whether tests passed. This honors "do not send unnecessary history".
    """

    attempt_number: int
    error_type: str | None = None
    passed: bool = False


class LearnerContext(BaseModel):
    """Compact behavioral context for the tutor (NOT full history).

    Phase 5 longitudinal signal. This NEVER changes what misconception the
    tutor discusses — it only lets the tutor pitch its tone/level given how the
    student has been doing.
    """

    concept_mastery: float | None = Field(
        default=None, description="Debugly Mastery Indicator for the concept (0-100)."
    )
    times_misconception_seen: int | None = Field(
        default=None, description="How many times THIS misconception has recurred."
    )
    persistent_gap: bool = Field(
        default=False, description="Whether this misconception is a recurring gap."
    )
    hint_dependency: float | None = Field(
        default=None, description="hints per attempt for the concept."
    )


class TutorRequest(BaseModel):
    """Request for a tutor interaction.

    ``misconception`` is the engine's verdict and is the SOLE diagnosis the
    tutor may reference. If it is None (e.g. a generic request), the tutor
    stays strictly generic and does not invent a misconception.
    """

    session_id: str
    interaction: TutorInteractionType = TutorInteractionType.HINT
    misconception: DetectedMisconception | None = None
    task_prompt: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    # Student's answer to a prior Socratic question (for wrong-answer handling).
    student_answer: str | None = None
    answer_was_correct: bool | None = None
    prior_attempts: list[PriorAttempt] = Field(default_factory=list)
    # Optional longitudinal learner context (Phase 5). Behavior NEVER overrides
    # the Phase 3 diagnosis in `misconception`; it only tells the tutor how the
    # student has been doing so hints can be pitched appropriately.
    learner_context: LearnerContext | None = None


class TutorResponse(BaseModel):
    """Structured tutor reply consumed directly by the UI."""

    message: str = Field(description="The tutor's spoken line to the student.")
    hint_level: HintLevel | None = Field(
        default=None, description="Current hint level, if this is a hint."
    )
    question: str | None = Field(
        default=None, description="A Socratic question to answer, if applicable."
    )
    options: list[str] = Field(
        default_factory=list, description="Optional multiple-choice options."
    )
    explanation: str | None = Field(
        default=None, description="Conceptual explanation or 'what you learned'."
    )
    robot_state: RobotState = RobotState.IDLE
    next_action: NextAction = NextAction.CONTINUE
    # True when a deterministic fallback produced this (AI unavailable).
    is_fallback: bool = False
    # Echoes the misconception key the response is grounded in (never invented).
    grounded_in: str | None = None
