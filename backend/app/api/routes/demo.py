"""Demo-mode endpoint.

* POST /api/demo/seed — populate a scripted demo class via the real tracker.

Convenience for the hackathon demo so the teacher dashboard and student views
have realistic data immediately.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.services.behavior.deps import _repos
from app.services.behavior.tracker import BehaviorTracker
from app.services.demo.seed import seed_demo_class

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed")
async def seed_demo() -> dict:
    events_repo, profile_repo = _repos()
    tracker = BehaviorTracker(events_repo, profile_repo)
    return await seed_demo_class(tracker, profile_repo, events_repo)
