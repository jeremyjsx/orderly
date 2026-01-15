from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # General
    APP_NAME: str = "Orderly"
    DESCRIPTION: str = (
        "Scalable e-commerce backend with async processing and real-time tracking"
    )
    VERSION: str = "1.0.0"
    PORT: int = 8000
    ENV: str = Field(default="development")

    # API
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(..., description="SQLAlchemy database URL")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
