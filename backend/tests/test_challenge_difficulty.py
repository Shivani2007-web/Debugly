"""Deterministic difficulty + selection tests (Phase 6)."""

from app.models.behavior import ConceptStat
from app.models.challenge import Difficulty
from app.services.challenge.difficulty import (
    adjust_after_result,
    easier,
    harder,
    select_difficulty,
)


def test_no_history_is_beginner():
    assert select_difficulty(None) == Difficulty.BEGINNER
    assert select_difficulty(ConceptStat(concept_key="x")) == Difficulty.BEGINNER


def test_low_mastery_gives_easier_challenge():
    low = ConceptStat(concept_key="x", attempts=4, successful_attempts=1, mastery=28.0)
    assert select_difficulty(low) in (Difficulty.BEGINNER, Difficulty.DEVELOPING)
    assert select_difficulty(low) == Difficulty.BEGINNER


def test_high_mastery_gives_harder_challenge():
    high = ConceptStat(
        concept_key="x", attempts=6, successful_attempts=6, mastery=88.0, hints_requested=0
    )
    assert select_difficulty(high) == Difficulty.ADVANCED


def test_persistent_gap_caps_difficulty():
    # Even with decent mastery, a persistent gap must not exceed developing.
    gappy = ConceptStat(
        concept_key="x", attempts=5, successful_attempts=4, mastery=70.0,
        misconception_counts={"off_by_one": 3}, repeated_misconception_events=2,
    )
    assert select_difficulty(gappy) in (Difficulty.BEGINNER, Difficulty.DEVELOPING)


def test_high_hint_dependency_steps_down():
    dependent = ConceptStat(
        concept_key="x", attempts=4, successful_attempts=3, mastery=65.0, hints_requested=8
    )
    independent = ConceptStat(
        concept_key="x", attempts=4, successful_attempts=3, mastery=65.0, hints_requested=0
    )
    assert select_difficulty(dependent) != Difficulty.ADVANCED
    # The dependent learner gets an easier or equal level than the independent one.
    order = [Difficulty.BEGINNER, Difficulty.DEVELOPING, Difficulty.INTERMEDIATE, Difficulty.ADVANCED]
    assert order.index(select_difficulty(dependent)) <= order.index(select_difficulty(independent))


# ---- adaptive stepping ----

def test_repeated_success_increases_difficulty():
    assert adjust_after_result(Difficulty.BEGINNER, passed=True, hints_used=0) == Difficulty.DEVELOPING
    assert adjust_after_result(Difficulty.DEVELOPING, passed=True, hints_used=1) == Difficulty.INTERMEDIATE


def test_repeated_failure_decreases_difficulty():
    assert adjust_after_result(Difficulty.INTERMEDIATE, passed=False, hints_used=0) == Difficulty.DEVELOPING
    # Passing but needing many hints also steps down.
    assert adjust_after_result(Difficulty.ADVANCED, passed=True, hints_used=3) == Difficulty.INTERMEDIATE


def test_difficulty_stepping_is_bounded():
    assert easier(Difficulty.BEGINNER) == Difficulty.BEGINNER
    assert harder(Difficulty.ADVANCED) == Difficulty.ADVANCED
