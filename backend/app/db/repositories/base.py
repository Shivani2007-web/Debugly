"""Repository interfaces for behavior events and learner profiles.

The behavior services depend only on these protocols, so storage can be
in-memory (tests, no-DB dev) or MongoDB (production) without service changes.
Raw events and aggregated profiles are deliberately separate stores.
"""

from __future__ import annotations

from typing import Protocol

from app.models.behavior import BehaviorEvent, LearnerProfile


class EventsRepository(Protocol):
    """Append-only store of raw behavior events."""

    async def append(self, event: BehaviorEvent) -> None: ...

    async def list_for_user(
        self, user_id: str, limit: int = 50
    ) -> list[BehaviorEvent]:
        """Most-recent-first events for a user."""
        ...

    async def count_for_user(self, user_id: str) -> int: ...


class ProfileRepository(Protocol):
    """Store of aggregated learner profiles (one per user)."""

    async def get(self, user_id: str) -> LearnerProfile | None: ...

    async def save(self, profile: LearnerProfile) -> None: ...

    async def list_all(self) -> list[LearnerProfile]: ...
