"""Central app configuration, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    database_url: str = ""
    supabase_jwt_secret: str = ""

    # Raw comma-separated string from env; parsed into a list below.
    groq_api_keys: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    google_client_id: str = ""
    google_client_secret: str = ""

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"

    @property
    def groq_keys(self) -> list[str]:
        return [k.strip() for k in self.groq_api_keys.split(",") if k.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
