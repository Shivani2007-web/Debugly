"""Challenge-service dependency wiring.

Selects Mongo-backed or in-memory stores based on DB availability, reusing the
Phase 5 tracker/profile repositories so challenge results flow into the same
learner profile.
"""

from __future__ import annotations

from app.db.mongo import mongo
from app.services.behavior.deps import _repos  # reuse Phase 5 repo selection
from app.services.behavior.tracker import BehaviorTracker
from app.services.challenge.service import ChallengeService
from app.services.challenge.store import (
    InMemoryChallengeStore,
    MongoChallengeStore,
)

# Shared in-memory store (process lifetime) for the no-DB path.
_mem_store = InMemoryChallengeStore()


def _store():
    if mongo.database is not None:
        return MongoChallengeStore(mongo.database)
    return _mem_store


def get_challenge_service() -> ChallengeService:
    events_repo, profile_repo = _repos()
    tracker = BehaviorTracker(events_repo, profile_repo)
    return ChallengeService(_store(), tracker, profile_repo)
