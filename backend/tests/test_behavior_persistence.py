"""MongoDB persistence/retrieval test (Phase 5).

Verifies that events and the aggregated profile survive a round-trip through
MongoDB and that the profile can be retrieved by a FRESH repository instance
(i.e. truly persisted, not just in-memory). Skips cleanly when no MongoDB is
reachable so the suite still runs offline.
"""

import asyncio
import uuid

import pytest

from app.config import get_settings
from app.models.behavior import BehaviorEventType, EventRecordRequest
from app.services.behavior.tracker import BehaviorTracker
from app.services.behavior.profile_service import ProfileService


def test_profile_persists_and_reloads_from_mongo():
    """Whole test runs on ONE event loop so the Motor client stays loop-bound."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
    except Exception:  # pragma: no cover
        pytest.skip("motor not installed")

    from app.db.repositories.mongo import (
        MongoEventsRepository,
        MongoProfileRepository,
    )

    settings = get_settings()

    async def scenario():
        client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=1500)
        try:
            await client.admin.command("ping")
        except Exception:
            client.close()
            pytest.skip("MongoDB not reachable; skipping persistence test")

        db = client[f"debugly_test_{uuid.uuid4().hex[:8]}"]
        try:
            tracker = BehaviorTracker(
                MongoEventsRepository(db), MongoProfileRepository(db)
            )
            u = "persist_user"
            for _ in range(3):
                await tracker.record(EventRecordRequest(
                    user_id=u,
                    event_type=BehaviorEventType.MISCONCEPTION_DETECTED,
                    concept_key="list_indexing",
                    misconception_key="off_by_one",
                ))

            # Fresh repositories on the same DB prove real persistence.
            fresh_events = MongoEventsRepository(db)
            fresh_profiles = MongoProfileRepository(db)
            fresh_service = ProfileService(fresh_events, fresh_profiles)

            assert await fresh_events.count_for_user(u) == 3
            summary = await fresh_service.summary(u)
            assert "list_indexing" in summary.persistent_gaps
            stat = (await fresh_profiles.get(u)).concepts["list_indexing"]
            assert stat.misconception_counts["off_by_one"] == 3
            assert stat.repeated_misconception_events == 2
        finally:
            await client.drop_database(db.name)
            client.close()

    asyncio.new_event_loop().run_until_complete(scenario())
