from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql+psycopg://career_os:career_os@localhost:5432/career_os"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 15
    jwt_refresh_token_expires_days: int = 30

    ai_default_provider: str = "anthropic"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    cors_origins: list[str] = ["http://localhost:3000"]
    frontend_base_url: str = "http://localhost:3000"

    email_verification_token_expires_hours: int = 24
    password_reset_token_expires_hours: int = 1

    api_base_url: str = "http://localhost:8000/api/v1"

    storage_provider: str = "local"
    storage_local_path: str = "storage/local"
    max_avatar_size_mb: int = 5
    max_attachment_size_mb: int = 10

    s3_bucket: str | None = None
    s3_region: str = "auto"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
