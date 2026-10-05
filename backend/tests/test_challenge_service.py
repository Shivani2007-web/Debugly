"""Challenge service + result persistence + mastery-update tests (Phase 6)."""

import asyncio

import pytest

from app.db.repositories.memory import (
    InMemoryEventsRepository,
    InMemoryProfileRepository,
)
from app.models.behavior import BehaviorEventType, EventRecordRequest
from app.models.challenge import (
    ChallengeType,
    Difficulty,
    SubmitChallengeRequest,
)
from app.services.behavior.tracker import BehaviorTracker
from app.services.challenge import generator
from app.services.challenge.service import ChallengeService
from app.services.challenge.store import InMemoryChallengeStore


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


@pytest.fixture
def wiring(monkeypatch):
    # Force deterministic fallback generation (no provider).
    monkeypatch.setattr(generator, "get_provider", lambda: None)
    events = InMemoryEventsRepository()
    profiles = InMemoryProfileRepository()
    store = InMemoryChallengeStore()
    tracker = BehaviorTracker(events, profiles)
    service = ChallengeService(store, tracker, profiles)
    return service, tracker, profiles, store


async def _seed_persistent_gap(tracker, user="u1", concept="list_indexing"):
    for _ in range(3):
        await tracker.record(EventRecordRequest(
            user_id=user, event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
            concept_key=concept, misconception_key="off_by_one",
        ))
    await tracker.record(EventRecordRequest(
        user_id=user, event_type=BehaviorEventType.SUBMISSION, concept_key=concept))
    await tracker.record(EventRecordRequest(
        user_id=user, event_type=BehaviorEventType.RUNTIME_ERROR,
        concept_key=concept, error_type="IndexError"))


def test_generate_targets_persistent_gap(wiring):
    service, tracker, _, _ = wiring
    run(_seed_persistent_gap(tracker))
    ch = run(service.generate_for_learner("u1"))
    assert ch.concept_key == "list_indexing"
    assert ch.misconception_key == "off_by_one"
    # Persistent gap caps difficulty at developing or below.
    assert ch.difficulty in (Difficulty.BEGINNER, Difficulty.DEVELOPING)


def test_generate_for_clean_learner_is_beginner(wiring):
    service, _, _, _ = wiring
    ch = run(service.generate_for_learner("brand_new"))
    assert ch.difficulty == Difficulty.BEGINNER
    assert ch.test_cases  # gradeable


def _solution_for(challenge) -> str:
    """A correct solution for whichever fallback Fix-the-Bug challenge was generated."""
    starter = challenge.starter_code
    if "get_last_three" in starter:
        return "def get_last_three(items):\n    return items[len(items) - 3:]\n"
    if "add_one" in starter:
        return "def add_one(n):\n    return n + 1\n"
    if "count_positive" in starter:
        return "def count_positive(nums):\n    return sum(1 for n in nums if n > 0)\n"
    raise AssertionError(f"no known solution for starter:\n{starter}")


def test_submit_correct_solution_passes_and_persists(wiring):
    service, tracker, _, store = wiring
    run(_seed_persistent_gap(tracker, user="solver"))
    ch = run(service.generate_for_learner("solver"))
    resp = run(service.submit(ch.id, SubmitChallengeRequest(user_id="solver", code=_solution_for(ch))))
    assert resp is not None
    assert resp.passed is True
    # Result persisted.
    results = run(store.results_for_user("solver"))
    assert len(results) == 1
    assert results[0].passed is True


def test_submit_updates_mastery_via_phase5(wiring):
    service, tracker, profiles, _ = wiring
    run(_seed_persistent_gap(tracker, user="m_user"))
    ch = run(service.generate_for_learner("m_user"))
    resp = run(service.submit(ch.id, SubmitChallengeRequest(user_id="m_user", code=_solution_for(ch))))
    # Mastery was computed by the Phase 5 tracker and surfaced back.
    assert resp.new_mastery is not None
    profile = run(profiles.get("m_user"))
    assert ch.concept_key in profile.concepts
    assert profile.concepts[ch.concept_key].attempts >= 1


def test_submit_wrong_solution_fails(wiring):
    service, tracker, _, _ = wiring
    run(_seed_persistent_gap(tracker, user="wrong_user"))
    ch = run(service.generate_for_learner("wrong_user"))
    wrong = "def get_last_three(items):\n    return []\n"
    resp = run(service.submit(ch.id, SubmitChallengeRequest(user_id="wrong_user", code=wrong)))
    assert resp.passed is False


def test_submit_feedback_hides_expected_values(wiring):
    service, tracker, _, _ = wiring
    run(_seed_persistent_gap(tracker, user="safe_user"))
    ch = run(service.generate_for_learner("safe_user"))
    wrong = "def get_last_three(items):\n    return []\n"
    resp = run(service.submit(ch.id, SubmitChallengeRequest(user_id="safe_user", code=wrong)))
    # Feedback has names + pass flags only — no expected/actual values.
    for fb in resp.test_feedback:
        assert set(fb.keys()) == {"name", "passed"}


def test_submit_unknown_challenge_returns_none(wiring):
    service, _, _, _ = wiring
    assert run(service.submit("does-not-exist", SubmitChallengeRequest(user_id="u", code="x"))) is None


def test_predict_challenge_grading(wiring):
    service, _, _, _ = wiring
    ch = run(service.generate_for_learner("p_user", task_type=ChallengeType.PREDICT_THE_OUTPUT))
    # Submit the correct predicted output (fallback off_by_one predict).
    resp = run(service.submit(ch.id, SubmitChallengeRequest(
        user_id="p_user", predicted_output="10\n20\n30")))
    assert resp.passed is True
    # Wrong prediction fails.
    ch2 = run(service.generate_for_learner("p_user2", task_type=ChallengeType.PREDICT_THE_OUTPUT))
    resp2 = run(service.submit(ch2.id, SubmitChallengeRequest(
        user_id="p_user2", predicted_output="wrong")))
    assert resp2.passed is False
