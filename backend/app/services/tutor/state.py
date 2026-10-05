"""Hint-level state tracking.

Tracks the current Socratic hint level per (session, misconception) so repeated
help requests escalate 1 -> 4 instead of regenerating the same hint. In-memory
for Phase 4 (single process); the interface is small so a Mongo-backed store can
replace it later without touching the tutor service.
"""

from __future__ import annotations

from threading import Lock

from app.models.tutor import HintLevel

MAX_LEVEL = int(HintLevel.STRONG_GUIDANCE)


class HintStateStore:
    """Thread-safe in-memory hint-level store."""

    def __init__(self) -> None:
        self._levels: dict[tuple[str, str], int] = {}
        self._lock = Lock()

    @staticmethod
    def _key(session_id: str, misconception_key: str | None) -> tuple[str, str]:
        return (session_id, misconception_key or "_generic")

    def current_level(self, session_id: str, misconception_key: str | None) -> int:
        with self._lock:
            return self._levels.get(self._key(session_id, misconception_key), 0)

    def advance(self, session_id: str, misconception_key: str | None) -> int:
        """Advance to the next level (capped at MAX_LEVEL) and return it."""
        with self._lock:
            k = self._key(session_id, misconception_key)
            nxt = min(self._levels.get(k, 0) + 1, MAX_LEVEL)
            self._levels[k] = nxt
            return nxt

    def reset(self, session_id: str, misconception_key: str | None) -> None:
        """Reset progression (e.g. after a successful correction)."""
        with self._lock:
            self._levels.pop(self._key(session_id, misconception_key), None)


# Process-level singleton.
hint_state = HintStateStore()
