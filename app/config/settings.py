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
    redis_url: str
    cache_ttl_seconds: int = 3600  # 1 hour

    # App
    app_env: str = "development"

    # JWT/Auth
    jwt_secret_key: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Notifications (AWS SNS/SQS)
    notifications_enabled: bool = False
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_sns_topic_arn: str | None = None
    aws_sqs_queue_url: str | None = None
    aws_sqs_wait_time_seconds: int = 10
    aws_sqs_max_messages: int = 10
    aws_sqs_visibility_timeout_seconds: int = 30

    # Email delivery
    email_provider: str = "smtp"  # smtp | ses

    # SMTP
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_sender_email: str | None = None
    smtp_timeout_seconds: int = 10

    # AWS SES (optional fallback)
    aws_ses_sender_email: str | None = None
    aws_ses_configuration_set: str | None = None

    notifications_email_subject_prefix: str = "[Maravilla]"
    notifications_scheduler_interval_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()