"""
Alumni Service Configuration.
"""
import os
from typing import List


class Settings:
    """Service settings."""

    # Service Info
    SERVICE_NAME: str = "alumni-service"
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8005"))

    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "2012")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "idino_career")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # External Services
    STUDENT_SERVICE_URL: str = os.getenv(
        "STUDENT_SERVICE_URL", "http://localhost:8002"
    )
    COMPETENCY_SERVICE_URL: str = os.getenv(
        "COMPETENCY_SERVICE_URL", "http://localhost:8003"
    )

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
    )


settings = Settings()
