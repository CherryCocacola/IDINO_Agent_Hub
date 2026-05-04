"""Privacy Service Configuration"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "privacy-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8017

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "2012")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "idino_career")

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Data retention settings
    DATA_RETENTION_DAYS: int = 365 * 5  # 5 years default
    EXPORT_FORMAT: str = "json"  # json or csv

    # Request processing
    REQUEST_PROCESSING_DAYS: int = 30  # GDPR requires 30 days

    # Other services
    STUDENT_SERVICE_URL: str = os.getenv("STUDENT_SERVICE_URL", "http://localhost:8002")
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8011")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def async_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
