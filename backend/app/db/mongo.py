"""MongoDB connection management using Motor (async driver).

A single client is created on application startup and reused across requests.
Connection failures are handled gracefully: the app still boots and the health
endpoint reports the database as unavailable rather than crashing. This keeps
the demo resilient when MongoDB is not running.
"""

from __future__ import annotations

import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger("debugly.db")


class MongoManager:
    """Holds the Motor client/database and exposes connectivity helpers."""

    client: AsyncIOMotorClient | None = None
    database: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Create the Motor client. Does not force a round-trip here.

        Connectivity is verified lazily via :meth:`ping` so a down database
        never blocks application startup.
        """
        settings = get_settings()
        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=2000,
            )
            self.database = self.client[settings.mongodb_db_name]
            logger.info("Mongo client initialized for db '%s'", settings.mongodb_db_name)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to initialize Mongo client")
            self.client = None
            self.database = None

    async def disconnect(self) -> None:
        """Close the Motor client cleanly on shutdown."""
        if self.client is not None:
            self.client.close()
            logger.info("Mongo client closed")
        self.client = None
        self.database = None

    async def ping(self) -> bool:
        """Return True if the database answers a ping within the timeout."""
        if self.client is None:
            return False
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            logger.warning("MongoDB ping failed", exc_info=True)
            return False

    def get_database(self) -> AsyncIOMotorDatabase:
        """Return the active database, raising if it was never initialized."""
        if self.database is None:
            raise RuntimeError("MongoDB is not connected")
        return self.database


# Module-level singleton used across the app.
mongo = MongoManager()
