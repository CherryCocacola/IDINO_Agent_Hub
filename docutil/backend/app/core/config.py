"""
Application configuration via Pydantic Settings.

Loads all service URLs, secrets, and tunables from environment variables
(or an .env file) and exposes a single cached ``get_settings()`` accessor.
"""

from __future__ import annotations

import math
from collections import Counter
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object.

    Every attribute maps to an environment variable with the same (upper-case)
    name.  A ``.env`` file placed next to the working directory is loaded
    automatically.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── application ──────────────────────────────────────────────────────
    app_name: str = "Document Utilization System"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"

    # ── database (PostgreSQL + asyncpg) ──────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/doc_util",
        description="Async SQLAlchemy database URL (asyncpg driver).",
    )
    # Phase 4.1: AGENT_HUB DB 통합 — DocUtil 모든 테이블이 위치할 단일 schema.
    # 모든 SQLAlchemy 모델은 자동으로 이 schema 에 매핑되며, alembic 도 동일
    # schema 의 `alembic_version` 테이블을 사용한다. Cross-schema 조회는 R3
    # 규칙(스키마 격리)에 의해 금지된다.
    db_schema: str = Field(
        default="document_utilization",
        description="DocUtil 전용 PostgreSQL schema. AGENT_HUB DB 통합 후 강제 격리.",
    )
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_echo: bool = False

    # ── redis ────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    redis_decode_responses: bool = True
    embedding_cache_ttl: int = 86400  # 24시간
    httpx_pool_max_connections: int = 100

    # ── rabbitmq ─────────────────────────────────────────────────────────
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672//"

    # ── celery ───────────────────────────────────────────────────────────
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── minio (S3-compatible object storage) ─────────────────────────────
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "documents"
    minio_secure: bool = False

    # ── jwt / authentication ─────────────────────────────────────────────
    jwt_secret_key: str = Field(
        default="CHANGE-ME-super-secret-key-for-jwt",
        description="Symmetric secret used when RS256 keys are not provided.",
    )
    jwt_algorithm: str = "RS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    jwt_private_key_path: str | None = Field(
        default=None,
        description="Path to PEM-encoded RSA private key for RS256 signing.",
    )
    jwt_public_key_path: str | None = Field(
        default=None,
        description="Path to PEM-encoded RSA public key for RS256 verification.",
    )

    # ── qdrant (vector store) ────────────────────────────────────────────
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "documents"

    # ── AI 프로바이더 토글 ─────────────────────────────────────────────
    # 지원값: "openai" | "vllm" | "azure_openai" | "gemini" | "anthropic"
    llm_provider: str = "openai"
    # "openai" = OpenAI Embedding API 사용, "local" = 내부 GPU 임베딩 서비스
    embedding_provider: str = "openai"

    # ── 기능별 프로바이더 오버라이드 ──────────────────────────────────
    # None이면 llm_provider 기본값을 따른다.
    # 예: 챗봇은 Gemini Flash(저렴+빠름), 보고서는 GPT-4o(Structured 강점)
    chat_llm_provider: str | None = None
    report_llm_provider: str | None = None
    template_llm_provider: str | None = None

    # ── OpenAI API ─────────────────────────────────────────────────────
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimension: int = 1536

    # ── Azure OpenAI ───────────────────────────────────────────────────
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None  # 예: https://myresource.openai.azure.com
    azure_openai_deployment: str | None = None  # 예: gpt-4o
    azure_openai_api_version: str = "2024-08-01-preview"

    # ── Anthropic (Claude) ─────────────────────────────────────────────
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # ── Google Gemini ──────────────────────────────────────────────────
    google_api_key: str | None = None
    google_model: str = "gemini-2.0-flash"

    # ── llm / embedding (공통) ─────────────────────────────────────────
    vllm_url: str = "http://localhost:8001/v1"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    embedding_service_url: str = "http://localhost:8002"
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # -- sglang (alternative serving) --
    sglang_url: str = "http://localhost:30000/v1"
    sglang_enabled: bool = False

    # -- reranker --
    reranker_model: str = "Qwen/Qwen3-Reranker-8B"
    reranker_url: str = "http://localhost:8003/v1"

    # -- docling VLM --
    docling_service_url: str = "http://localhost:8005"
    docling_model: str = "ibm-granite/granite-docling-258M"

    # -- Unsplash (무료 스톡 이미지 검색) --
    unsplash_access_key: str | None = None

    # -- 이미지 생성 설정 --
    # "dalle3" = OpenAI DALL-E 3 AI 이미지 생성, "unsplash" = 무료 스톡 이미지 검색
    image_generation_provider: str = "dalle3"

    # -- RAG advanced --
    hyde_enabled: bool = True
    self_rag_enabled: bool = True
    graph_rag_enabled: bool = False
    max_rag_iterations: int = 3

    # -- OpenTelemetry --
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "document-utilization-api"

    # ── encryption (AES-256) ─────────────────────────────────────────────
    # 트랙 #65: default 는 "validator 가 통과하는 형식적 placeholder" 일 뿐,
    # 실제 키는 반드시 환경변수 ENCRYPTION_KEY 로 주입해야 한다. 아래 default
    # 는 dev 부팅 편의용 random hex 이며, 운영에서는 절대 사용 금지.
    # 강한 키 생성: python -c "import secrets; print(secrets.token_hex(32))"
    encryption_key: str = Field(
        default=(
            # dev placeholder — 운영 키 아님 (validator 통과용 random hex)
            "7c4e9a1f3b8d6021e5a738c92f0b14d6a89c52e0316f7b94d2f508a17c4e1b03"
        ),
        description=(
            "32-byte hex-encoded AES-256 key for encrypting API keys at rest. "
            "MUST be overridden via ENCRYPTION_KEY env var in production."
        ),
    )

    # ── cors ─────────────────────────────────────────────────────────────
    # ["*"]로 설정하면 모든 origin을 허용한다. 운영 환경에서는
    # CORS_ORIGINS 환경변수로 허용 도메인을 명시적으로 지정할 것.
    cors_origins: list[str] = Field(
        default=["*"],
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default=["*"])
    cors_allow_headers: list[str] = Field(default=["*"])

    # ── uploads ──────────────────────────────────────────────────────────
    max_upload_size_mb: int = 100
    allowed_upload_formats: list[str] = Field(
        default=[
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/haansofthwp",
            "application/vnd.hancom.hwp",
            "application/vnd.hancom.hwpx",
            "application/x-hwp",
            "application/octet-stream",
            "text/plain",
            "text/csv",
            "text/markdown",
            "image/png",
            "image/jpeg",
        ],
    )

    # ── derived helpers ──────────────────────────────────────────────────

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def effective_jwt_algorithm(self) -> str:
        """Fall back to HS256 when no RSA key paths are configured."""
        if self.jwt_algorithm == "RS256" and self.jwt_private_key_path is None:
            return "HS256"
        return self.jwt_algorithm

    # ── validators ───────────────────────────────────────────────────────

    @field_validator("encryption_key")
    @classmethod
    def _validate_encryption_key(cls, v: str) -> str:
        """ENCRYPTION_KEY (AES-256-GCM) validator.

        검증 항목 (트랙 #65 — 약한 키 부팅 차단):
        1. 64자 hex (32바이트) — AES-256 키 길이 강제
        2. distinct byte ratio ≥ 16/32 (50%) — 패턴화된 키 차단
        3. Shannon entropy ≥ 4.5 bits/byte — 저엔트로피 키 차단
        4. 16/32자 hex 반복 패턴 차단 (`0123...0123...` 같은 데모 키)

        트랙 #64 회전 사고(데모 키 `0123456789abcdef...` 가 운영에 적재됨)
        재발을 코드 레이어에서 원천 차단한다. 약한 키가 환경변수로 주입되면
        FastAPI 부팅 자체가 실패하여 운영 반영 전에 발견되도록 한다.

        강한 키 생성:
            python -c "import secrets; print(secrets.token_hex(32))"
        """
        # 조건 1: hex 디코딩 + 길이
        try:
            key_bytes = bytes.fromhex(v)
        except ValueError as exc:
            raise ValueError("encryption_key must be valid hex characters (0-9a-fA-F)") from exc

        if len(key_bytes) != 32:
            raise ValueError("encryption_key must be exactly 32 bytes (64 hex characters) for AES-256.")

        # 조건 4 (먼저 차단): 명확한 반복 패턴 — 데모 키 즉시 차단
        # 16자 hex(8바이트)가 4회 반복: `0123456789abcdef` × 4 형태
        if v[:16] == v[16:32] == v[32:48] == v[48:64]:
            raise ValueError(
                "encryption_key uses a repeating 16-char hex pattern (demo/weak key). "
                "Generate a cryptographically random key: "
                "python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        # 32자 hex(16바이트)가 2회 반복
        if v[:32] == v[32:64]:
            raise ValueError(
                "encryption_key uses a repeating 32-char hex pattern (weak key). "
                "Generate a cryptographically random key: "
                "python -c 'import secrets; print(secrets.token_hex(32))'"
            )

        # 조건 2: distinct byte 비율 — 32바이트 중 16개 미만 distinct 는 약한 키
        distinct = len(set(key_bytes))
        if distinct < 16:
            raise ValueError(
                f"encryption_key has too few distinct bytes ({distinct}/32, required ≥ 16). "
                "Generate a cryptographically random key: "
                "python -c 'import secrets; print(secrets.token_hex(32))'"
            )

        # 조건 3: Shannon entropy — 4.5 bits/byte 미만은 약한 키
        # 강한 random 키는 7.0+ bits/byte, 약한 데모 키는 4.0 미만
        counts = Counter(key_bytes)
        total = len(key_bytes)
        entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
        if entropy < 4.5:
            raise ValueError(
                f"encryption_key entropy too low ({entropy:.2f} bits/byte, required ≥ 4.5). "
                "Generate a cryptographically random key: "
                "python -c 'import secrets; print(secrets.token_hex(32))'"
            )

        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return an application-wide, cached ``Settings`` instance."""
    return Settings()
