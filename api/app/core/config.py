from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_path: str = "sqlite+aiosqlite:///.state/db.sqlite"

    log_level: str = "INFO"
    
    session_idle_expire_minutes: int = 30
    session_expire_days: int = 7

@lru_cache
def get_settings() -> Settings:
    return Settings()

SettingsDep = Annotated[Settings, Depends(get_settings)]