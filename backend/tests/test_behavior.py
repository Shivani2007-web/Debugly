"""Behavior tracking, learner profile, and mastery tests (Phase 5).

Covers: event recording, repeated-misconception tracking, profile aggregation,
deterministic mastery calculation, improvement after intervention, clean new
student, and edge cases. Uses in-memory repositories for determinism.
"""

import asyncio

import pytest

from app.db.repositories.memory import (
    InMemoryEventsRepository,
    InMemoryProfileRepository,
)
from app.models.behavior import (
    BehaviorEventType,
    ConceptStat,
    EventRecordRequest,
)
from app.services.behavior.mastery import compute_mastery, hint_dependency_ratio
from app.services.behavior.profile_service import ProfileService
from app.services.behavior.tracker import BehaviorTracker


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def stores():
    return InMemoryEventsRepository(), InMemoryProfileRepository()


@pytest.fixture
def tracker(stores):
    return BehaviorTracker(*stores)


@pytest.fixture
def profiles(stores):
    return ProfileService(*stores)


def ev(user="u1", **kw):
    return EventRecordRequest(user_id=user, **kw)


# ---- Event recording ----

def test_event_is_recorded_and_counted(tracker, stores):
    events_repo, _ = stores
    run(tracker.record(ev(event_type=BehaviorEventType.SUBMISSION, concept_key="loops")))
    assert run(events_repo.count_for_user("u1")) == 1
    stored = run(events_repo.list_for_user("u1"))
    assert stored[0].event_type == BehaviorEventType.SUBMISSION


def test_profile_created_on_first_event(tracker, stores):
    _, profile_repo = stores
    run(tracker.record(ev(event_type=BehaviorEventType.SUBMISSION, concept_key="loops")))
    profile = run(profile_repo.get("u1"))
    assert profile is not None
    assert profile.total_events == 1
    assert "loops" in profile.concepts


# ---- Aggregation ----

def test_attempts_and_successes_aggregate(tracker, stores):
    _, profile_repo = stores
    run(tracker.record(ev(event_type=BehaviorEventType.SUBMISSION, concept_key="loops")))
    run(tracker.record(ev(event_type=BehaviorEventType.SUBMISSION, concept_key="loops")))
    run(tracker.record(ev(event_type=BehaviorEventType.SUCCESSFUL_EXECUTION, concept_key="loops")))
    stat = run(profile_repo.get("u1")).concepts["loops"]
    assert stat.attempts == 2
    assert stat.successful_attempts == 1


# ---- Repeated misconception (persistent gap) ----

def test_single_misconception_is_not_persistent(tracker, stores):
    _, profile_repo = stores
    run(tracker.record(ev(
        event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
        concept_key="list_indexing", misconception_key="off_by_one",
    )))
    stat = run(profile_repo.get("u1")).concepts["list_indexing"]
    assert stat.misconception_counts["off_by_one"] == 1
    assert stat.repeated_misconception_events == 0
    assert stat.has_persistent_gap is False


def test_repeated_misconception_flags_persistent_gap(tracker, stores):
    _, profile_repo = stores
    for _ in range(3):
        run(tracker.record(ev(
            event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
            concept_key="list_indexing", misconception_key="off_by_one",
        )))
    stat = run(profile_repo.get("u1")).concepts["list_indexing"]
    assert stat.misconception_counts["off_by_one"] == 3
    # 2nd and 3rd occurrences count as repeats.
    assert stat.repeated_misconception_events == 2
    assert stat.has_persistent_gap is True


def test_distinct_misconceptions_not_counted_as_repeats(tracker, stores):
    _, profile_repo = stores
    run(tracker.record(ev(
        event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
        concept_key="loops", misconception_key="off_by_one",
    )))
    run(tracker.record(ev(
        event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
        concept_key="loops", misconception_key="infinite_loop",
    )))
    stat = run(profile_repo.get("u1")).concepts["loops"]
    assert stat.repeated_misconception_events == 0
    assert stat.has_persistent_gap is False


# ---- Mastery calculation (pure) ----

def test_mastery_zero_for_no_attempts():
    assert compute_mastery(ConceptStat(concept_key="x")) == 0.0


def test_mastery_rises_with_success():
    low = ConceptStat(concept_key="x", attempts=4, successful_attempts=1)
    high = ConceptStat(concept_key="x", attempts=4, successful_attempts=4)
    assert compute_mastery(high) > compute_mastery(low)


def test_repeated_misconception_lowers_mastery():
    clean = ConceptStat(concept_key="x", attempts=4, successful_attempts=3)
    gappy = ConceptStat(
        concept_key="x", attempts=4, successful_attempts=3,
        misconception_counts={"off_by_one": 3}, repeated_misconception_events=2,
    )
    assert compute_mastery(gappy) < compute_mastery(clean)


def test_hint_dependency_lowers_mastery():
    independent = ConceptStat(concept_key="x", attempts=4, successful_attempts=3)
    dependent = ConceptStat(
        concept_key="x", attempts=4, successful_attempts=3, hints_requested=9
    )
    assert compute_mastery(dependent) < compute_mastery(independent)


def test_improvement_raises_mastery():
    base = ConceptStat(concept_key="x", attempts=4, successful_attempts=3, corrections=1)
    improved = ConceptStat(
        concept_key="x", attempts=4, successful_attempts=3, corrections=1,
        unaided_successes_after_correction=3,
    )
    assert compute_mastery(improved) >= compute_mastery(base)


def test_mastery_is_bounded():
    maxed = ConceptStat(
        concept_key="x", attempts=10, successful_attempts=10, corrections=10,
        unaided_successes_after_correction=10, last_difficulty_passed="advanced",
    )
    assert 0.0 <= compute_mastery(maxed) <= 100.0


def test_hint_dependency_ratio_zero_without_attempts():
    assert hint_dependency_ratio(ConceptStat(concept_key="x")) == 0.0


# ---- Improvement after intervention (integration) ----

def test_intervention_improvement_journey(tracker, stores):
    _, profile_repo = stores
    u = "learner"
    seq = [
        # Attempt 1 fails with the misconception.
        ev(u, event_type=BehaviorEventType.SUBMISSION, concept_key="list_indexing"),
        ev(u, event_type=BehaviorEventType.RUNTIME_ERROR, concept_key="list_indexing", error_type="IndexError"),
        ev(u, event_type=BehaviorEventType.MISCONCEPTION_DETECTED, concept_key="list_indexing", misconception_key="off_by_one"),
        # Hint sequence.
        ev(u, event_type=BehaviorEventType.HINT_REQUESTED, concept_key="list_indexing"),
        ev(u, event_type=BehaviorEventType.HINT_LEVEL_REACHED, concept_key="list_indexing", hint_level=1),
        ev(u, event_type=BehaviorEventType.TUTOR_ANSWER_INCORRECT, concept_key="list_indexing"),
        ev(u, event_type=BehaviorEventType.HINT_LEVEL_REACHED, concept_key="list_indexing", hint_level=2),
        # Student corrects after the hint.
        ev(u, event_type=BehaviorEventType.SUCCESSFUL_CORRECTION, concept_key="list_indexing", payload={"after_hint": True}),
        # Follow-up: succeeds WITHOUT a hint => improvement evidence.
        ev(u, event_type=BehaviorEventType.SUBMISSION, concept_key="list_indexing"),
        ev(u, event_type=BehaviorEventType.SUCCESSFUL_EXECUTION, concept_key="list_indexing", payload={"used_hint": False}),
    ]
    for e in seq:
        run(tracker.record(e))

    stat = run(profile_repo.get(u)).concepts["list_indexing"]
    assert stat.corrections == 1
    assert stat.corrections_after_hint == 1
    assert stat.unaided_successes_after_correction == 1
    assert stat.mastery > 0.0


# ---- Trend history ----

def test_trend_points_recorded_on_mastery_change(tracker, stores):
    _, profile_repo = stores
    run(tracker.record(ev(event_type=BehaviorEventType.SUBMISSION, concept_key="loops")))
    run(tracker.record(ev(event_type=BehaviorEventType.SUCCESSFUL_EXECUTION, concept_key="loops")))
    profile = run(profile_repo.get("u1"))
    assert len(profile.trend) >= 1
    assert profile.trend[-1].concept_key == "loops"


# ---- Profile read service + clean new student ----

def test_clean_new_student_summary(profiles):
    summary = run(profiles.summary("nobody"))
    assert summary.is_new_learner is True
    assert summary.overall_mastery == 0.0
    assert summary.concepts == []
    assert summary.persistent_gaps == []


def test_summary_reports_persistent_gap(tracker, profiles):
    u = "gap_user"
    for _ in range(2):
        run(tracker.record(ev(u, event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
                              concept_key="list_indexing", misconception_key="off_by_one")))
    summary = run(profiles.summary(u))
    assert "list_indexing" in summary.persistent_gaps
    assert summary.is_new_learner is False


def test_recommendations_prioritise_persistent_gap(tracker, profiles):
    u = "rec_user"
    for _ in range(2):
        run(tracker.record(ev(u, event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
                              concept_key="list_indexing", misconception_key="off_by_one")))
    recs = run(profiles.recommendations(u))
    assert any(r.concept_key == "list_indexing" for r in recs)


def test_recent_misconceptions_marks_persistent(tracker, profiles):
    u = "rm_user"
    for _ in range(3):
        run(tracker.record(ev(u, event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
                              concept_key="loops", misconception_key="infinite_loop")))
    rms = run(profiles.recent_misconceptions(u))
    assert rms[0].misconception_key == "infinite_loop"
    assert rms[0].persistent is True


# ---- Edge cases ----

def test_event_without_concept_still_counts_total(tracker, stores):
    _, profile_repo = stores
    run(tracker.record(ev(event_type=BehaviorEventType.CODE_EXECUTION)))  # no concept_key
    profile = run(profile_repo.get("u1"))
    assert profile.total_events == 1
    assert profile.concepts == {}


def test_recent_events_empty_for_unknown_user(profiles):
    assert run(profiles.recent_events("ghost")) == []


def test_mastery_trend_empty_for_unknown_user(profiles):
    assert run(profiles.mastery_trend("ghost")) == []
