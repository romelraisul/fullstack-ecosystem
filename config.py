"""Central configuration module using Pydantic BaseSettings.

Environment variable precedence examples:
- DASH_HOST / HOST
- DASH_PORT / PORT
- DASH_RELOAD / RELOAD (bool)
Feature flags:
- ENABLE_PROFILE (bool) controls /profile endpoint exposure.
- ENABLE_REQUEST_LOG (bool) toggles per-request logging summary.

This module centralises runtime settings to avoid scattering literals.
"""

from __future__ import annotations

import os
import subprocess
from functools import lru_cache

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field("Unified Master Dashboard - Protocol Alpha Enhanced", alias="APP_NAME")
    host: str = Field("127.0.0.1", alias="DASH_HOST")
    port: int = Field(5125, alias="DASH_PORT")
    reload: bool = Field(False, alias="DASH_RELOAD")
    debug: bool = Field(False, alias="DEBUG")
    enable_profile: bool = Field(False, alias="ENABLE_PROFILE")
    enable_request_log: bool = Field(True, alias="ENABLE_REQUEST_LOG")
    request_id_header: str = Field("X-Request-ID", alias="REQUEST_ID_HEADER")
    log_file: str | None = Field(None, alias="LOG_FILE")
    log_rotate_bytes: int = Field(5_000_000, alias="LOG_ROTATE_BYTES")
    log_rotate_backups: int = Field(3, alias="LOG_ROTATE_BACKUPS")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    json_logging: bool = Field(True, alias="JSON_LOGGING")
    postgres_dsn: str | None = Field(None, alias="POSTGRES_DSN")
    enable_async_migrations: bool = Field(False, alias="ENABLE_ASYNC_MIGRATIONS")
    enable_tracing: bool = Field(False, alias="ENABLE_TRACING")
    tracing_endpoint: str | None = Field(None, alias="TRACING_ENDPOINT")

    git_sha: str | None = None
    build_meta: str | None = None

    model_config = ConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    def effective_reload(self) -> bool:
        # Fallback: if debug true and reload not explicitly set
        return bool(self.reload or self.debug)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Attempt to fill git SHA if not provided
    if not s.git_sha:
        try:
            s.git_sha = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], text=True
            ).strip()
        except Exception:
            s.git_sha = os.environ.get("GIT_SHA") or "unknown"
    return s


__all__ = ["Settings", "get_settings"]
