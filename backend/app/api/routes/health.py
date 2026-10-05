"""Health endpoint.

Reports whether the API is up and whether MongoDB is reachable. The frontend
landing page polls this to show the live connection chain for Phase 1.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.db.mongo import mongo

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Shape of the health payload consumed by the frontend."""

    status: str
    app: str
    environment: str
    database: str  # "connected" | "disconnected"


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return API and database status."""
    settings = get_settings()
    db_ok = await mongo.ping()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        environment=settings.environment,
        database="connected" if db_ok else "disconnected",
    )
