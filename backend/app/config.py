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

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
