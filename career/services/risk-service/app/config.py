from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Service Configuration
    SERVICE_NAME: str = "risk-service"
    SERVICE_PORT: int = 8010
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: list = ["*"]

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

    # Risk thresholds - GPA
    GPA_WARNING_THRESHOLD: float = 2.5
    GPA_CRITICAL_THRESHOLD: float = 2.0
    GPA_MEDIUM_THRESHOLD: float = 3.0  # 목표 기업/대학원 지원 권장 기준
    GPA_CRITICAL_RISK_SCORE: float = 90.0
    GPA_WARNING_RISK_SCORE: float = 60.0
    GPA_MEDIUM_RISK_SCORE: float = 30.0

    # Risk thresholds - Credits
    CREDIT_WARNING_THRESHOLD: int = 15  # credits behind
    CREDIT_HIGH_THRESHOLD: int = 30  # HIGH severity 기준
    CREDITS_PER_YEAR: int = 30  # 연간 예상 이수 학점
    CREDIT_MAX_RISK_SCORE: float = 80.0

    # Risk thresholds - Graduation
    GRADUATION_REQUIRED_CREDITS: int = 130  # 졸업 필수 학점
    GRADUATION_HIGH_PER_SEMESTER: int = 21  # HIGH severity (학기당 필요 학점)
    GRADUATION_MEDIUM_PER_SEMESTER: int = 18  # MEDIUM severity (학기당 필요 학점)
    GRADUATION_HIGH_RISK_SCORE: float = 70.0
    GRADUATION_MEDIUM_RISK_SCORE: float = 40.0
    TOTAL_SEMESTERS: int = 8  # 전체 학기 수

    # Risk thresholds - Skill Gap
    SKILL_GAP_MEDIUM_THRESHOLD: float = 50.0
    SKILL_GAP_HIGH_THRESHOLD: float = 70.0
    SKILL_GAP_RISK_MULTIPLIER: float = 0.8

    # Risk thresholds - Attendance
    ATTENDANCE_WARNING_THRESHOLD: float = 80.0  # percent

    # Risk Level Thresholds
    RISK_LEVEL_CRITICAL_THRESHOLD: float = 70.0
    RISK_LEVEL_HIGH_THRESHOLD: float = 50.0
    RISK_LEVEL_MEDIUM_THRESHOLD: float = 30.0

    # Risk Score Weights
    RISK_WEIGHT_GPA: float = 0.3
    RISK_WEIGHT_CREDITS: float = 0.2
    RISK_WEIGHT_PREREQUISITE: float = 0.15
    RISK_WEIGHT_GRADUATION: float = 0.2
    RISK_WEIGHT_SKILL_GAP: float = 0.15

    # Recommendation Resources
    ACADEMIC_COUNSELING_URL: str = "https://career.example.edu/counseling"
    TUTORING_SERVICE_URL: str = "https://career.example.edu/tutoring"
    CAREER_CENTER_URL: str = "https://career.example.edu/career-center"
    SKILL_DEVELOPMENT_URL: str = "https://career.example.edu/skill-courses"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
