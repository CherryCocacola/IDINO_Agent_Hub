"""WorkNet Service Configuration"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Service Configuration
    SERVICE_NAME: str = "worknet-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8018

    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "idino_career")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_SCHEMA: str = os.getenv("DB_SCHEMA", "idino_career")

    # WorkNet API Configuration
    WORKNET_API_BASE_URL: str = os.getenv(
        "WORKNET_API_BASE_URL",
        "https://www.work.go.kr/consltJobCarpa"
    )
    WORKNET_API_KEY: str = os.getenv("WORKNET_API_KEY", "")
    WORKNET_CALLBACK_URL: str = os.getenv("WORKNET_CALLBACK_URL", "")

    # Diagnosis Types
    SUPPORTED_DIAGNOSIS_TYPES: List[str] = [
        "aptitude",          # 직업적성검사
        "interest",          # 직업흥미검사
        "values",            # 직업가치관검사
        "personality",       # 성인용 직업성격검사
        "entrepreneurship",  # 창업적성검사
        "career_maturity",   # 진로성숙도검사
    ]

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Cache Settings
    DIAGNOSIS_CACHE_TTL: int = 3600  # 1 hour
    RESULT_RETENTION_DAYS: int = 365 * 2  # 2 years

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
