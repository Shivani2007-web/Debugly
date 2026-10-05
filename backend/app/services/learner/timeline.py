"""Human-readable labels for behavior events (presentational only).

Maps the existing Phase 5 event types to short student-facing labels for the
activity timeline. No new event data is created here.
"""

from __future__ import annotations

from app.models.behavior import BehaviorEvent, BehaviorEventType
from app.models.dashboard import TimelineEvent

_LABELS = {
    BehaviorEventType.CODE_EXECUTION: "Ran code",
    BehaviorEventType.SUBMISSION: "Submitted a solution",
    BehaviorEventType.SYNTAX_ERROR: "Syntax error detected",
    BehaviorEventType.RUNTIME_ERROR: "Runtime error detected",
    BehaviorEventType.TEST_FAILURE: "Tests failed",
    BehaviorEventType.SUCCESSFUL_EXECUTION: "Solution passed",
    BehaviorEventType.REGION_REPEATEDLY_MODIFIED: "Reworked the same lines",
    BehaviorEventType.HINT_REQUESTED: "Requested a hint",
    BehaviorEventType.HINT_LEVEL_REACHED: "Reached a new hint level",
    BehaviorEventType.TUTOR_QUESTION_ANSWERED: "Answered the tutor",
    BehaviorEventType.TUTOR_ANSWER_CORRECT: "Answered the tutor correctly",
    BehaviorEventType.TUTOR_ANSWER_INCORRECT: "Answered the tutor incorrectly",
    BehaviorEventType.SUCCESSFUL_CORRECTION: "Corrected the mistake",
    BehaviorEventType.MISCONCEPTION_DETECTED: "Misconception detected",
    BehaviorEventType.CHALLENGE_ATTEMPT: "Attempted a challenge",
    BehaviorEventType.CODE_REUSE_PASTE: "Reused prior code",
}


def _label(event: BehaviorEvent) -> str:
    base = _LABELS.get(event.event_type, event.event_type.value.replace("_", " "))
    if event.event_type == BehaviorEventType.MISCONCEPTION_DETECTED and event.misconception_key:
        base = f"Misconception detected: {event.misconception_key.replace('_', ' ')}"
    elif event.event_type == BehaviorEventType.HINT_LEVEL_REACHED and event.hint_level:
        base = f"Reached hint level {event.hint_level}"
    elif event.event_type == BehaviorEventType.CHALLENGE_ATTEMPT:
        passed = event.payload.get("passed")
        if passed is True:
            base = "Challenge passed"
        elif passed is False:
            base = "Challenge attempted (not yet passing)"
    return base


def to_timeline(event: BehaviorEvent) -> TimelineEvent:
    """Project a raw behavior event into a student-facing timeline entry."""
    return TimelineEvent(
        event_type=event.event_type.value,
        concept_key=event.concept_key,
        misconception_key=event.misconception_key,
        error_type=event.error_type,
        hint_level=event.hint_level,
        difficulty=event.difficulty,
        label=_label(event),
        at=event.created_at,
    )
