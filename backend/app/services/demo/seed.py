"""Demo-mode seeding.

Populates a scripted class of learners (so the teacher dashboard has class-level
data) by replaying realistic behavior events through the EXISTING Phase 5
tracker — no mastery or data is fabricated outside the normal path. Idempotent
per user_id prefix: re-seeding clears the demo users first.

This is a convenience for the hackathon demo; it is not used in normal flow.
"""

from __future__ import annotations

from app.models.behavior import BehaviorEventType, EventRecordRequest
from app.services.behavior.tracker import BehaviorTracker

DEMO_PREFIX = "demo-"

# A small class with varied profiles. Each entry drives events through the
# tracker so the resulting mastery/gaps are produced by the real pipeline.
_CLASS = [
    # (user_id, concept, misconception, repeats, hints, solved_after)
    ("demo-ava", "list_indexing", "off_by_one", 3, 2, 1),      # persistent gap, recovering
    ("demo-ben", "loops", "infinite_loop", 2, 1, 2),            # persistent gap, improving
    ("demo-cleo", "functions", "missing_return", 1, 0, 3),     # mild, mostly fine
    ("demo-dia", "list_indexing", "off_by_one", 4, 3, 0),      # heavy struggle, needs attention
    ("demo-eve", "loops", "boolean_condition", 1, 0, 4),       # strong learner
]


async def _run_student(tracker: BehaviorTracker, user, concept, mkey, repeats, hints, solved_after):
    async def rec(et, **kw):
        await tracker.record(EventRecordRequest(user_id=user, concept_key=concept, event_type=et, **kw))

    # Repeated misconception occurrences (drives persistent-gap detection).
    for _ in range(repeats):
        await rec(BehaviorEventType.SUBMISSION)
        await rec(BehaviorEventType.RUNTIME_ERROR, error_type="IndexError")
        await rec(BehaviorEventType.MISCONCEPTION_DETECTED, misconception_key=mkey)
    for lvl in range(1, hints + 1):
        await rec(BehaviorEventType.HINT_REQUESTED)
        await rec(BehaviorEventType.HINT_LEVEL_REACHED, hint_level=lvl)
    if hints > 0 or repeats > 0:
        await rec(BehaviorEventType.SUCCESSFUL_CORRECTION, payload={"after_hint": hints > 0})
    # Unaided successes after correction -> recovery / mastery climb.
    for _ in range(solved_after):
        await rec(BehaviorEventType.SUBMISSION)
        await rec(BehaviorEventType.SUCCESSFUL_EXECUTION, payload={"used_hint": False})


async def seed_demo_class(tracker: BehaviorTracker, profile_repo, events_repo) -> dict:
    """Seed the demo class. Clears existing demo users first (in-memory only)."""
    # Best-effort clear for the in-memory path (used in tests/dev). Mongo path
    # simply overwrites per user on save.
    if hasattr(profile_repo, "_profiles"):
        for uid in [u for u in profile_repo._profiles if u.startswith(DEMO_PREFIX)]:
            profile_repo._profiles.pop(uid, None)
    if hasattr(events_repo, "_events"):
        events_repo._events = [e for e in events_repo._events if not e.user_id.startswith(DEMO_PREFIX)]

    for entry in _CLASS:
        await _run_student(tracker, *entry)

    return {"seeded_students": [c[0] for c in _CLASS], "count": len(_CLASS)}
