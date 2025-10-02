from __future__ import annotations
import os
from pydantic import BaseModel
from functools import lru_cache

class Settings(BaseModel):
    app_id: str | None = os.getenv("GITHUB_APP_ID")
    private_key: str | None = os.getenv("GITHUB_APP_PRIVATE_KEY")  # PEM contents (can be multiline)
    webhook_secret: str | None = os.getenv("GITHUB_WEBHOOK_SECRET")
    github_api_url: str = os.getenv("GITHUB_API_URL", "https://api.github.com")
    user_agent: str = os.getenv("GOV_APP_USER_AGENT", "governance-app/0.1")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        arbitrary_types_allowed = True

@lru_cache
def get_settings() -> Settings:
    return Settings()
