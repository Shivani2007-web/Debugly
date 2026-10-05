"""Smart Reuse endpoint.

* POST /api/reuse/check — classify a reuse/paste action against the task's
  reuse zones and record the behavior. Never blocks; it informs.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models.reuse import ReuseCheckRequest, ReuseCheckResponse
from app.services.reuse.deps import get_reuse_service

router = APIRouter(prefix="/reuse", tags=["reuse"])


@router.post("/check", response_model=ReuseCheckResponse)
async def check_reuse(payload: ReuseCheckRequest) -> ReuseCheckResponse:
    return await get_reuse_service().check(payload)
