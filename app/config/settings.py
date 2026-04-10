from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    twelve_data_base_url: str = "https://api.twelvedata.com"
    twelve_data_api_key: str
    twelve_data_timeout_seconds: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()