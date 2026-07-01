"""Central app configuration, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    # --- Database ---
    database_url: str = ""

    # --- Supabase ---
    # Base project URL, e.g. https://xxxx.supabase.co
    supabase_url: str = ""
    # New-style keys: publishable (browser-safe) + secret (backend only).
    supabase_anon_key: str = ""      # sb_publishable_...
    supabase_secret_key: str = ""    # sb_secret_...  (used later for admin user creation)

    # --- Groq (comma-separated keys, rotated automatically) ---
    groq_api_keys: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Google OAuth (added later) ---
    google_client_id: str = ""
    google_client_secret: str = ""

    @property
    def is_prod(self) -> bool:
        return self.app_env == "production"

    @property
    def groq_keys(self) -> list[str]:
        return [k.strip() for k in self.groq_api_keys.split(",") if k.strip()]

    @property
    def jwks_url(self) -> str:
        """Supabase publishes its JWT signing public keys here (for ECC/RSA verify)."""
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
