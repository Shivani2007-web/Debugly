"""Full adaptive journey (Phase 6):

misconception -> intervention -> personalized challenge -> successful solution
-> mastery improvement -> harder follow-up challenge.

Runs entirely on in-memory stores with deterministic fallback generation.
"""

import asyncio

import pytest

from app.db.repositories.memory import (
    InMemoryEventsRepository,
    InMemoryProfileRepository,
)
from app.models.behavior import BehaviorEventType, EventRecordRequest
from app.models.challenge import DIFFICULTY_ORDER, SubmitChallengeRequest
from app.services.behavior.tracker import BehaviorTracker
from app.services.challenge import generator
from app.services.challenge.service import ChallengeService
from app.services.challenge.store import InMemoryChallengeStore


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_full_adaptive_journey(monkeypatch):
    monkeypatch.setattr(generator, "get_provider", lambda: None)
    events = InMemoryEventsRepository()
    profiles = InMemoryProfileRepository()
    tracker = BehaviorTracker(events, profiles)
    service = ChallengeService(InMemoryChallengeStore(), tracker, profiles)
    u = "journey"

    async def scenario():
        # 1. Repeated off-by-one misconception (persistent gap) + struggle.
        for _ in range(3):
            await tracker.record(EventRecordRequest(
                user_id=u, event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
                concept_key="list_indexing", misconception_key="off_by_one"))
        await tracker.record(EventRecordRequest(
            user_id=u, event_type=BehaviorEventType.SUBMISSION, concept_key="list_indexing"))
        await tracker.record(EventRecordRequest(
            user_id=u, event_type=BehaviorEventType.RUNTIME_ERROR,
            concept_key="list_indexing", error_type="IndexError"))

        # 2. Personalized challenge targets the gap at an easy level.
        ch1 = await service.generate_for_learner(u)
        assert ch1.concept_key == "list_indexing"
        assert ch1.difficulty in (DIFFICULTY_ORDER[0], DIFFICULTY_ORDER[1])  # beginner/developing
        d1 = ch1.difficulty

        # 3. Student solves it correctly.
        correct = "def get_last_three(items):\n    return items[len(items) - 3:]\n"
        r1 = await service.submit(ch1.id, SubmitChallengeRequest(user_id=u, code=correct))
        assert r1.passed is True
        mastery_after_1 = profiles_get_mastery(await profiles.get(u), "list_indexing")

        # 4. Several more unaided successes drive mastery up.
        for _ in range(5):
            ch = await service.generate_for_learner(u)
            await service.submit(ch.id, SubmitChallengeRequest(user_id=u, code=correct))

        profile = await profiles.get(u)
        mastery_final = profiles_get_mastery(profile, "list_indexing")

        # 5. Mastery improved after the intervention + successes.
        assert mastery_final > mastery_after_1

        # 6. A follow-up challenge is now at least as hard as the first
        #    (difficulty rises as the learner demonstrates competence).
        ch_follow = await service.generate_for_learner(u)
        assert DIFFICULTY_ORDER.index(ch_follow.difficulty) >= DIFFICULTY_ORDER.index(d1)

        return mastery_after_1, mastery_final, d1, ch_follow.difficulty

    m1, m2, d1, d2 = run(scenario())
    assert m2 > m1


def profiles_get_mastery(profile, concept_key) -> float:
    return profile.concepts[concept_key].mastery if concept_key in profile.concepts else 0.0
