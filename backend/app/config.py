from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_debug: bool = True
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/medical_messenger"
    database_url_sync: str = (
        "postgresql://postgres:postgres@localhost:5432/medical_messenger"
    )

    # Redis
    redis_url: str = "redis://localhost:6380/0"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5673//"

    # JWT
    jwt_secret_key: str = "change-me-to-a-random-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # AI - Anthropic (Claude)
    anthropic_api_key: str = ""

    # AI - Azure OpenAI
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_mini_deployment_name: str = "gpt-4o-mini"
    azure_openai_embedding_deployment: str = "text-embedding-3-small"

    # AI - Google Gemini
    google_api_key: str = ""

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "medical-messenger"

    # AI defaults
    ai_temperature: float = 0.7
    ai_max_tokens: int = 1024

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # KingOrder
    kingorder_secret_key: str = ""

    # Alipay
    alipay_public_key: str = ""

    # Azure Blob Storage
    azure_storage_connection_string: str = ""
    azure_storage_container: str = "uploads"

    # Resilience
    http_timeout_seconds: int = 30
    http_max_retries: int = 3
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60

    # Rate limiting
    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "10/minute"

    # Body size limit
    max_body_size_mb: int = 10

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.app_env == "production":
            if self.jwt_secret_key == "change-me-to-a-random-secret-key":
                raise ValueError("JWT secret key must be changed in production")
            if self.app_debug:
                raise ValueError("Debug mode must be disabled in production")
            if "localhost" in self.database_url:
                raise ValueError("Database URL must not point to localhost in production")
            if "localhost" in self.redis_url:
                raise ValueError("Redis URL must not point to localhost in production")
            if "guest:guest" in self.rabbitmq_url:
                raise ValueError("RabbitMQ must not use default credentials in production")
            if "localhost" in self.cors_origins:
                raise ValueError("CORS origins must not include localhost in production")
            if not any([self.anthropic_api_key, self.azure_openai_api_key, self.google_api_key]):
                raise ValueError("At least one AI API key must be configured in production")
        # Cross-field: if Azure OpenAI key set, endpoint must also be set
        if self.azure_openai_api_key and not self.azure_openai_endpoint:
            raise ValueError("Azure OpenAI endpoint is required when API key is set")
        return self


settings = Settings()
