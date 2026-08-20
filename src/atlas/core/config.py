"""Application configuration, loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Atlas AI"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- API ---
    api_v1_prefix: str = "/api/v1"

    # --- Infrastructure (no defaults: must be supplied) ---
    database_url: PostgresDsn
    redis_url: RedisDsn

    # --- Security ---
    jwt_secret_key: str  # no default, ever
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    """Return the settings singleton.

    Cached so the .env file is parsed once per process, and so this can be
    used directly as a FastAPI dependency.
    """
    return Settings()
