"""Challenge domain contracts.

A challenge is selected and difficulty-rated deterministically from the learner
profile; Gemini only fills in the content under constraints. Two views exist:

* :class:`Challenge` — the full server-side record, including test cases and
  expected behavior (NEVER sent to the student).
* :class:`ChallengeView` — the student-safe projection: prompt, starter code,
  visible test names only. Expected outputs and hidden-test details are
  stripped so answers can't leak.

Challenge results feed the Phase 5 behavior tracker; no mastery logic is
duplicated here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from app.models.execution import TestCase


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Difficulty(str, Enum):
    """Adaptive difficulty levels (ordered)."""

    BEGINNER = "beginner"
    DEVELOPING = "developing"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# Ordered for comparisons / stepping up and down.
DIFFICULTY_ORDER: list[Difficulty] = [
    Difficulty.BEGINNER,
    Difficulty.DEVELOPING,
    Difficulty.INTERMEDIATE,
    Difficulty.ADVANCED,
]


class ChallengeType(str, Enum):
    """Supported challenge formats."""

    FIX_THE_BUG = "fix_the_bug"        # starter code has a bug to fix (Monaco+exec integrated)
    COMPLETE_THE_CODE = "complete_the_code"
    PREDICT_THE_OUTPUT = "predict_the_output"
    SMALL_BUILD_TASK = "small_build_task"


class ChallengeConstraints(BaseModel):
    """Structured constraints the backend hands to Gemini.

    Gemini generates content to satisfy these; it does NOT choose the concept,
    misconception, or difficulty — those are decided deterministically.
    """

    concept_key: str
    concept_name: str
    misconception_key: str | None = None
    misconception_name: str | None = None
    difficulty: Difficulty
    task_type: ChallengeType
    learning_objective: str
    # Compact learner context (not full history).
    learner_context: dict = Field(default_factory=dict)
    # Explicit anti-memorization note, surfaced into the prompt.
    avoid_pattern: str | None = None


class Challenge(BaseModel):
    """Full server-side challenge record (includes answers)."""

    id: str
    title: str
    description: str
    concept_key: str
    misconception_key: str | None = None
    difficulty: Difficulty
    task_type: ChallengeType
    starter_code: str = ""
    expected_behavior: str = ""          # server-side only
    test_cases: list[TestCase] = Field(default_factory=list)  # server-side only
    # For PREDICT_THE_OUTPUT: the code to read and the correct answer (hidden).
    predict_code: str | None = None
    predict_answer: str | None = None    # server-side only
    learning_objective: str = ""
    hints_available: int = 4
    generated_by: str = "fallback"       # "gemini" | "fallback"
    user_id: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class VisibleTest(BaseModel):
    """A test case name shown to the student (NO expected output)."""

    name: str


class ChallengeView(BaseModel):
    """Student-safe projection — contains NO hidden answers."""

    id: str
    title: str
    description: str
    concept: str
    difficulty: Difficulty
    task_type: ChallengeType
    starter_code: str = ""
    predict_code: str | None = None      # the code to predict, but not the answer
    learning_objective: str = ""
    hints_available: int = 4
    visible_tests: list[VisibleTest] = Field(default_factory=list)
    total_tests: int = 0


def to_view(challenge: Challenge) -> ChallengeView:
    """Project a full Challenge into the student-safe view.

    Deliberately omits: expected_behavior, test-case args/expected, predict
    answer, hidden-test names. Only non-hidden test NAMES are surfaced.
    """
    visible = [VisibleTest(name=t.name) for t in challenge.test_cases if not t.hidden]
    return ChallengeView(
        id=challenge.id,
        title=challenge.title,
        description=challenge.description,
        concept=challenge.concept_key,
        difficulty=challenge.difficulty,
        task_type=challenge.task_type,
        starter_code=challenge.starter_code,
        predict_code=challenge.predict_code,
        learning_objective=challenge.learning_objective,
        hints_available=challenge.hints_available,
        visible_tests=visible,
        total_tests=len(challenge.test_cases),
    )


# ---- Request / result DTOs ----

class GenerateChallengeRequest(BaseModel):
    """Ask Debugly to pick + generate a personalized challenge for a learner."""

    user_id: str
    # Optional overrides (e.g. for reinforcement of a specific concept).
    concept_key: str | None = None
    task_type: ChallengeType | None = None
    session_id: str | None = None


class ChallengeResult(BaseModel):
    """Recorded outcome of a challenge attempt."""

    challenge_id: str
    user_id: str
    concept_key: str
    misconception_key: str | None = None
    difficulty: Difficulty
    passed: bool
    attempts: int = 1
    hints_used: int = 0
    duration_ms: int = 0
    created_at: datetime = Field(default_factory=_utcnow)


class SubmitChallengeRequest(BaseModel):
    """Submit a solution to a challenge for grading + recording.

    For code challenges, ``code`` is graded against the stored test cases.
    For PREDICT_THE_OUTPUT, ``predicted_output`` is compared to the stored
    answer. Neither the test cases nor the answer are ever returned.
    """

    user_id: str
    code: str | None = None
    predicted_output: str | None = None
    attempts: int = 1
    hints_used: int = 0
    duration_ms: int = 0
    session_id: str | None = None


class SubmitChallengeResponse(BaseModel):
    """Result of grading a challenge submission (no hidden answers leaked)."""

    passed: bool
    passed_count: int = 0
    total_count: int = 0
    # Per-visible-test pass/fail (names only, no expected values).
    test_feedback: list[dict] = Field(default_factory=list)
    message: str = ""
    new_mastery: float | None = None
