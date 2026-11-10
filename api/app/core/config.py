from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_path: str = "sqlite+aiosqlite:///.state/db.sqlite"

    log_level: str = "INFO"

    environment: str = "PROD"

    session_idle_expire_minutes: int = 30
    session_expire_days: int = 7

    # origins allowed to call the API cross-origin; empty = same-origin only (no CORS headers)
    cors_origins: list[str] = []

    # origins accepted on unsafe requests (Origin / Referer check against CSRF)
    trusted_origins: list[str] = ["http://localhost:5173"]

@lru_cache
def get_settings() -> Settings:
    return Settings()
