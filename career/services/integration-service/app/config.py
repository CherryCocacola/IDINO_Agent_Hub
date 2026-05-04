"""
Integration Service Configuration.
"""
import os
from typing import List


class Settings:
    """Service settings."""

    # Service Info
    SERVICE_NAME: str = "integration-service"
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8019"))

    # Database (for DB-backed mock data)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "postgres")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "2012")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "idino_career")

    @property
    def database_url(self) -> str:
        """Get async database URL."""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # Redis (for caching external API responses)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/1")
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

    # External API Endpoints (for future real integration)
    WORKNET_API_URL: str = os.getenv(
        "WORKNET_API_URL", "https://api.worknet.go.kr/v1"
    )
    WORKNET_API_KEY: str = os.getenv("WORKNET_API_KEY", "")

    UNIVERSITY_API_URL: str = os.getenv(
        "UNIVERSITY_API_URL", "https://api.university.ac.kr/v1"
    )
    UNIVERSITY_API_KEY: str = os.getenv("UNIVERSITY_API_KEY", "")

    HRD_API_URL: str = os.getenv(
        "HRD_API_URL", "https://api.hrd.go.kr/v1"
    )
    HRD_API_KEY: str = os.getenv("HRD_API_KEY", "")

    # Mock Mode (use mock data instead of real API calls)
    USE_MOCK_DATA: bool = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
