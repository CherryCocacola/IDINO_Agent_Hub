from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "coaching-service"
    SERVICE_PORT: int = 8009
    DEBUG: bool = True

    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "2012"
    DB_SCHEMA: str = "idino_career"

    # Connection Pool
    DB_POOL_MIN: int = 2
    DB_POOL_MAX: int = 10

    # AI Service URL (for coaching insights)
    AI_SERVICE_URL: str = "http://localhost:8006"

    # Student Service URL (for student profile lookup)
    STUDENT_SERVICE_URL: str = "http://localhost:8002"

    # OpenAI for AI Coach
    OPENAI_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
