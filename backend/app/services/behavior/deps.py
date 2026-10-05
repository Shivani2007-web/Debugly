"""Behavior-service dependency wiring.

Selects MongoDB-backed repositories when the database is connected, otherwise
falls back to process-wide in-memory repositories so behavior tracking still
works (and tests run without a DB). The tracker and profile service are built
on top of whichever repositories are active.
"""

from __future__ import annotations

from app.db.mongo import mongo
from app.db.repositories.memory import (
    InMemoryEventsRepository,
    InMemoryProfileRepository,
)
from app.db.repositories.mongo import (
    MongoEventsRepository,
    MongoProfileRepository,
)
from app.services.behavior.profile_service import ProfileService
from app.services.behavior.tracker import BehaviorTracker

# Shared in-memory fallbacks (persist for the process lifetime).
_mem_events = InMemoryEventsRepository()
_mem_profiles = InMemoryProfileRepository()


def _repos():
    """Return (events_repo, profile_repo) based on DB availability."""
    if mongo.database is not None:
        db = mongo.database
        return MongoEventsRepository(db), MongoProfileRepository(db)
    return _mem_events, _mem_profiles


def get_tracker() -> BehaviorTracker:
    events, profiles = _repos()
    return BehaviorTracker(events, profiles)


def get_profile_service() -> ProfileService:
    events, profiles = _repos()
    return ProfileService(events, profiles)
