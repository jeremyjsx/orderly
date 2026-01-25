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

    # Redis
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis host",
    )
    REDIS_PORT: int = Field(
        default=6379,
        description="Redis port",
    )
    REDIS_PASSWORD: str = Field(
        default="",
        description="Redis password",
    )
    REDIS_DB: int = Field(
        default=0,
        description="Redis database number",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
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

    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting",
    )
    RATE_LIMIT_AUTH_REQUESTS: int = Field(
        default=5,
        description="Number of requests allowed for auth endpoints",
    )
    RATE_LIMIT_AUTH_WINDOW: int = Field(
        default=60,
        description="Time window in seconds for auth rate limiting",
    )
    RATE_LIMIT_GLOBAL_REQUESTS: int = Field(
        default=100,
        description="Number of requests allowed globally per window",
    )
    RATE_LIMIT_GLOBAL_WINDOW: int = Field(
        default=60,
        description="Time window in seconds for global rate limiting",
    )


settings = Settings()
