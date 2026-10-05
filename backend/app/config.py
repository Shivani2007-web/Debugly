"""Application configuration loaded from environment variables.

Uses pydantic-settings so every setting is typed and documented in one place.
Values come from the process environment or a local ``.env`` file.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env path ABSOLUTELY relative to the backend package root so the
# key loads no matter which working directory the server is launched from.
# config.py lives at backend/app/config.py -> parents[1] is the backend root.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """Typed application settings.

    Settings come from the process environment first, then the backend-root
    ``.env`` file (resolved to an absolute path, so CWD no longer matters).
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- Server ----
    app_name: str = "Debugly"
    environment: str = "development"

    # ---- MongoDB ----
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "debugly"

    # ---- CORS ----
    cors_origins: str = "http://localhost:3000"

    # ---- Gemini (Phase 4+) ----
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"

    # ---- Auth (later phases) ----
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a clean list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read once per process)."""
    return Settings()
