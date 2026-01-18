from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # General
    APP_NAME: str = "Orderly"
    DESCRIPTION: str = (
        "Scalable e-commerce backend with async processing and real-time tracking"
    )
    VERSION: str = "1.0.0"
    ENV: str = Field(default="development")

    # API
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://orderly:orderly@localhost:5432/orderly",
        description="SQLAlchemy database URL",
    )

    # RabbitMQ
    RABBITMQ_URL: str = Field(
        default="amqp://orderly:orderly@localhost:5672/",
        description="RabbitMQ URL",
    )

    # JWT
    JWT_SECRET_KEY: str = Field(
        default="change-me",
        description="JWT secret key",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    JWT_EXPIRATION_TIME: int = Field(
        default=60,
        description="JWT expiration time in minutes",
    )


settings = Settings()
