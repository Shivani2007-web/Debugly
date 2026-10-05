"""Smart Reuse service.

Classifies a reuse/paste action against a task's reuse zones and records the
behavior via the Phase 5 tracker (a ``code_reuse_paste`` event). It NEVER
blocks: a learning-critical overlap is flagged and recorded, so legitimate
boilerplate reuse is frictionless while concept bypass is made visible.
"""

from __future__ import annotations

from app.models.behavior import BehaviorEventType, EventRecordRequest
from app.models.reuse import (
    ReuseCheckRequest,
    ReuseCheckResponse,
    ReuseVerdict,
    ReuseZoneKind,
)
from app.models.task import ReuseZone
from app.services.behavior.tracker import BehaviorTracker
from app.services.tasks import get_task


def _overlaps(a_start: int, a_end: int, z: ReuseZone) -> bool:
    """Inclusive line-range overlap test."""
    lo, hi = min(a_start, a_end), max(a_start, a_end)
    return not (hi < z.start_line or lo > z.end_line)


class ReuseService:
    def __init__(self, tracker: BehaviorTracker) -> None:
        self._tracker = tracker

    async def check(self, req: ReuseCheckRequest) -> ReuseCheckResponse:
        task = get_task(req.task_id) if req.task_id else None
        zones = task.reuse_zones if task else []

        if not zones:
            # Nothing declared to protect: reuse is unrestricted (still recorded).
            await self._record(req, learning_critical=False, concept_key=task.concept_keys[0] if task and task.concept_keys else None)
            return ReuseCheckResponse(
                verdict=ReuseVerdict.UNRESTRICTED,
                overlaps=[],
                message="Reuse is unrestricted for this task.",
                allowed=True,
                learning_critical_overlap=False,
            )

        overlaps: list[ReuseZoneKind] = []
        for z in zones:
            if _overlaps(req.start_line, req.end_line, z):
                try:
                    overlaps.append(ReuseZoneKind(z.kind))
                except ValueError:
                    continue

        critical = ReuseZoneKind.LEARNING_CRITICAL in overlaps
        concept_key = task.concept_keys[0] if task and task.concept_keys else None
        await self._record(req, learning_critical=critical, concept_key=concept_key)

        if critical:
            return ReuseCheckResponse(
                verdict=ReuseVerdict.FLAGGED,
                overlaps=overlaps,
                message=(
                    "This region is the part of the task that tests the concept. "
                    "Reusing it may skip the learning — try adapting it yourself. "
                    "(You can still proceed.)"
                ),
                allowed=True,
                learning_critical_overlap=True,
            )

        return ReuseCheckResponse(
            verdict=ReuseVerdict.ALLOWED,
            overlaps=overlaps,
            message="Boilerplate reuse — go ahead.",
            allowed=True,
            learning_critical_overlap=False,
        )

    async def _record(
        self, req: ReuseCheckRequest, *, learning_critical: bool, concept_key: str | None
    ) -> None:
        await self._tracker.record(
            EventRecordRequest(
                user_id=req.user_id,
                session_id=req.session_id,
                event_type=BehaviorEventType.CODE_REUSE_PASTE,
                concept_key=concept_key,
                payload={
                    "task_id": req.task_id,
                    "start_line": req.start_line,
                    "end_line": req.end_line,
                    "char_count": req.char_count,
                    "source": req.source,
                    "learning_critical": learning_critical,
                },
            )
        )
