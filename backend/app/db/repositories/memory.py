"""In-memory repositories.

Used by the test suite and as a graceful default when MongoDB is unavailable,
so behavior tracking works in any environment. Data lives for the process
lifetime only.
"""

from __future__ import annotations

from app.models.behavior import BehaviorEvent, LearnerProfile


class InMemoryEventsRepository:
    def __init__(self) -> None:
        self._events: list[BehaviorEvent] = []

    async def append(self, event: BehaviorEvent) -> None:
        self._events.append(event)

    async def list_for_user(self, user_id: str, limit: int = 50) -> list[BehaviorEvent]:
        items = [e for e in self._events if e.user_id == user_id]
        items.sort(key=lambda e: e.created_at, reverse=True)
        return items[:limit]

    async def count_for_user(self, user_id: str) -> int:
        return sum(1 for e in self._events if e.user_id == user_id)

    def clear(self) -> None:
        self._events.clear()


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._profiles: dict[str, LearnerProfile] = {}

    async def get(self, user_id: str) -> LearnerProfile | None:
        p = self._profiles.get(user_id)
        # Return a deep copy so callers mutate explicitly via save().
        return p.model_copy(deep=True) if p is not None else None

    async def save(self, profile: LearnerProfile) -> None:
        self._profiles[profile.user_id] = profile.model_copy(deep=True)

    async def list_all(self) -> list[LearnerProfile]:
        return [p.model_copy(deep=True) for p in self._profiles.values()]

    def clear(self) -> None:
        self._profiles.clear()
