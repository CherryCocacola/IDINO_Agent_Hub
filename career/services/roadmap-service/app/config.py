"""Roadmap Service Configuration"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "2012")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "idino_career")

    # Service
    SERVICE_NAME: str = "roadmap-service"
    SERVICE_PORT: int = 8015

    # Other services
    STUDENT_SERVICE_URL: str = os.getenv("STUDENT_SERVICE_URL", "http://localhost:8002")
    COMPETENCY_SERVICE_URL: str = os.getenv("COMPETENCY_SERVICE_URL", "http://localhost:8003")
    SKILL_SERVICE_URL: str = os.getenv("SKILL_SERVICE_URL", "http://localhost:8007")
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:8006")

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
