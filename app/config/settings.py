from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Twelve Data
    twelve_data_base_url: str = "https://api.twelvedata.com"
    twelve_data_api_key: str
    twelve_data_timeout_seconds: float = 10.0

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/maravilla_db"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600  # 1 hour

    # App
    app_env: str = "development"

    # JWT/Auth
    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()