from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_JWT_SECRETS = frozenset({"change-me", "dev-secret-change-me", "secret", ""})
_MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql+psycopg://career_os:career_os@localhost:5432/career_os"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 15
    jwt_refresh_token_expires_days: int = 30

    ai_default_provider: str = "gemini"
    ai_fallback_providers: list[str] = ["groq", "openrouter"]
    ai_max_retries: int = 2
    # Per-call ceiling on a single provider request, and an overall ceiling
    # across every retry/fallback attempt combined -- without these, a
    # single slow provider can occupy a request worker for minutes (up to
    # (ai_max_retries + 1) x len(providers) calls, each otherwise unbounded).
    ai_request_timeout_seconds: float = 30.0
    ai_total_timeout_seconds: float = 120.0

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-flash-latest"

    openrouter_api_key: str | None = None
    openrouter_model: str = "inclusionai/ling-3.0-flash:free"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # Local models via Ollama's OpenAI-compatible API -- unauthenticated
    # (no API key), and the base URL is configurable since, unlike every
    # other provider above, it isn't a fixed public endpoint.
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.1"

    cors_origins: list[str] = ["http://localhost:3000"]
    frontend_base_url: str = "http://localhost:3000"
    # Guards against Host-header attacks (cache poisoning, password-reset-
    # link poisoning via a spoofed Host). "*" (no restriction) is only a
    # safe default because _reject_insecure_production_secrets below
    # refuses to boot with it when ENVIRONMENT=production -- real
    # deployments must set this to their actual domain(s).
    allowed_hosts: list[str] = ["*"]

    email_verification_token_expires_hours: int = 24
    password_reset_token_expires_hours: int = 1

    email_provider: str = "console"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_address: str = "no-reply@example.com"
    smtp_from_name: str = "AI Career Platform"

    api_base_url: str = "http://localhost:8000/api/v1"

    storage_provider: str = "local"
    storage_local_path: str = "storage/local"
    max_avatar_size_mb: int = 5
    max_attachment_size_mb: int = 10
    max_cv_import_size_mb: int = 10

    s3_bucket: str | None = None
    s3_region: str = "auto"
    s3_endpoint_url: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    @model_validator(mode="after")
    def _reject_insecure_production_secrets(self) -> "Settings":
        if self.environment != "production":
            return self

        if (
            self.jwt_secret in _INSECURE_JWT_SECRETS
            or len(self.jwt_secret) < _MIN_JWT_SECRET_LENGTH
        ):
            raise ValueError(
                "JWT_SECRET must be set to a random value of at least "
                f"{_MIN_JWT_SECRET_LENGTH} characters when ENVIRONMENT=production."
            )
        if "*" in self.allowed_hosts:
            raise ValueError(
                "ALLOWED_HOSTS must be set to the real domain(s) when "
                "ENVIRONMENT=production -- \"*\" disables Host-header validation entirely."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
