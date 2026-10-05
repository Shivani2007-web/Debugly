"""Behavior-event ingestion endpoints.

Clients batch meaningful learning events and flush them (e.g. on run/submit),
rather than streaming keystrokes. Both a single-event and a batch endpoint are
provided.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.behavior import EventBatchRequest, EventRecordRequest
from app.services.behavior.deps import get_tracker

router = APIRouter(prefix="/behavior", tags=["behavior"])


class RecordResponse(BaseModel):
    recorded: int
    total_events: int


@router.post("/event", response_model=RecordResponse)
async def record_event(payload: EventRecordRequest) -> RecordResponse:
    """Record a single behavior event."""
    tracker = get_tracker()
    profile = await tracker.record(payload)
    return RecordResponse(recorded=1, total_events=profile.total_events)


@router.post("/events", response_model=RecordResponse)
async def record_events(batch: EventBatchRequest) -> RecordResponse:
    """Record a batch of behavior events in order."""
    tracker = get_tracker()
    total = 0
    for ev in batch.events:
        profile = await tracker.record(ev)
        total = profile.total_events
    return RecordResponse(recorded=len(batch.events), total_events=total)
