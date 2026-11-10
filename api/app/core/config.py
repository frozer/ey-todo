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

    # extra origins accepted on unsafe requests (Origin / Referer check against CSRF);
    # same-origin requests (SPA served by this server, or via the Vite dev proxy)
    # are always accepted, so this is only for front-ends on a different origin
    trusted_origins: list[str] = []

    # SPA to serve from /; None = API only
    webapp_dir: str | None = None

@lru_cache
def get_settings() -> Settings:
    return Settings()
