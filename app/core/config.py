from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
    DATABASE_URL: str = Field(..., description="SQLAlchemy database URL")

    # JWT
    JWT_SECRET_KEY: str = Field(..., description="JWT secret key")
    JWT_ALGORITHM: str = Field(..., description="JWT algorithm")
    JWT_EXPIRATION_TIME: int = Field(..., description="JWT expiration time in seconds")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
