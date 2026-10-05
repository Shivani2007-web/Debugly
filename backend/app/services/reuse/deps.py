"""Smart Reuse dependency wiring (reuses the Phase 5 tracker)."""

from __future__ import annotations

from app.services.behavior.deps import _repos
from app.services.behavior.tracker import BehaviorTracker
from app.services.reuse.service import ReuseService


def get_reuse_service() -> ReuseService:
    events_repo, profile_repo = _repos()
    return ReuseService(BehaviorTracker(events_repo, profile_repo))
