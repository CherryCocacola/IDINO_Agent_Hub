from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Service Info
    SERVICE_NAME: str = "ai-service"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8006

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Service URLs
    STUDENT_SERVICE_URL: str = "http://localhost:8002"
    COMPETENCY_SERVICE_URL: str = "http://localhost:8003"
    ALUMNI_SERVICE_URL: str = "http://localhost:8005"
    INTEGRATION_SERVICE_URL: str = "http://localhost:8019"

    # Database (for RAG and Eval)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_SCHEMA: str = "idino_career"

    # AI Settings
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7

    # Tool Calling Settings
    MAX_TOOL_CALLS: int = 5
    ENABLE_TOOL_CALLING: bool = True

    # RAG Settings
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIM: int = 1536
    RAG_TOP_K: int = 5
    RAG_ALPHA: float = 0.7  # Vector weight (1-alpha = BM25 weight)

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
