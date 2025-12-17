# common/config/settings.py

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str
    app_env: str

    # Database
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    # Redis
    redis_host: str
    redis_port: int

    # Observability
    log_level: str = "INFO"

    # AI
    openrouter_api_key: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
