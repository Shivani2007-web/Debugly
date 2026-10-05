"""FastAPI application entry point.

Wires configuration, CORS, the MongoDB lifecycle and the API routers.
Phase 1 mounts only the health router; later phases add more routers under
``/api`` without changing this file's structure.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.validation import InputValidationError
from app.api.routes import (
    analysis,
    behavior,
    challenges,
    demo,
    execution,
    health,
    learner,
    profile,
    reuse,
    tasks,
    teacher,
    tutor,
)
from app.config import get_settings
from app.db.mongo import mongo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debugly")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage startup/shutdown: open and close the Mongo connection."""
    await mongo.connect()
    logger.info("Debugly backend started")
    try:
        yield
    finally:
        await mongo.disconnect()
        logger.info("Debugly backend stopped")


def create_app() -> FastAPI:
    """Application factory. Keeps setup testable and importable."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routers (all mounted under /api).
    app.include_router(health.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")
    app.include_router(execution.router, prefix="/api")
    app.include_router(analysis.router, prefix="/api")
    app.include_router(tutor.router, prefix="/api")
    app.include_router(behavior.router, prefix="/api")
    app.include_router(profile.router, prefix="/api")
    app.include_router(challenges.router, prefix="/api")
    app.include_router(learner.router, prefix="/api")
    app.include_router(reuse.router, prefix="/api")
    app.include_router(teacher.router, prefix="/api")
    app.include_router(demo.router, prefix="/api")

    @app.exception_handler(InputValidationError)
    async def _on_input_validation_error(_request: Request, exc: InputValidationError):
        # Untrusted-input guard violations become a clean 422, not a 500.
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"name": settings.app_name, "docs": "/docs", "health": "/api/health"}

    return app


app = create_app()
