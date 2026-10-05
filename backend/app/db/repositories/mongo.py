"""MongoDB-backed repositories.

Collections:
* ``behavior_events``  — append-only raw event log (evidence trail).
* ``learner_profiles`` — one aggregated document per user, keyed by user_id.

Keeping them in separate collections means the profile can always be rebuilt
by replaying ``behavior_events`` for a user.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.behavior import BehaviorEvent, LearnerProfile

EVENTS_COLLECTION = "behavior_events"
PROFILES_COLLECTION = "learner_profiles"


class MongoEventsRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db[EVENTS_COLLECTION]

    async def append(self, event: BehaviorEvent) -> None:
        await self._col.insert_one(event.model_dump(mode="json"))

    async def list_for_user(self, user_id: str, limit: int = 50) -> list[BehaviorEvent]:
        cursor = (
            self._col.find({"user_id": user_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [BehaviorEvent.model_validate(_strip_id(d)) for d in docs]

    async def count_for_user(self, user_id: str) -> int:
        return await self._col.count_documents({"user_id": user_id})


class MongoProfileRepository:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self._col = db[PROFILES_COLLECTION]

    async def get(self, user_id: str) -> LearnerProfile | None:
        doc = await self._col.find_one({"user_id": user_id})
        if doc is None:
            return None
        return LearnerProfile.model_validate(_strip_id(doc))

    async def save(self, profile: LearnerProfile) -> None:
        await self._col.replace_one(
            {"user_id": profile.user_id},
            profile.model_dump(mode="json"),
            upsert=True,
        )

    async def list_all(self) -> list[LearnerProfile]:
        docs = await self._col.find({}).to_list(length=1000)
        return [LearnerProfile.model_validate(_strip_id(d)) for d in docs]


def _strip_id(doc: dict) -> dict:
    """Drop Mongo's _id so Pydantic validation doesn't choke on it."""
    doc.pop("_id", None)
    return doc
