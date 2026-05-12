"""
LLMApiKey ORM model for storing encrypted LLM provider API keys.

DEPRECATED — Phase 7 R2 이후 신규 사용 금지 (트랙 #69, 2026-05-12).

DocUtil 의 모든 LLM 호출은 Phase 7.3+ 부터 AgentHub `/v1/chat/completions`
(외부) 또는 `/v1/embeddings` (임베딩) 단일 진입점으로 위임된다. 본 모델이
저장한 ``tb_llm_api_keys`` 행은 운영 ``app/core/llm_keys.py::resolve_api_key``
의 fallback 경로(`report_generator.py` 의 보고서 워커 일부)에서만 잔존
참조되며, **신규 운영 데이터를 적재하지 말 것**.

운영자 키 발급/회전은 AgentHub 운영자 콘솔(`/admin/api-keys`) 단일 권위로
일원화한다. 본 테이블/모듈은 다음 정책 결정 후 별도 트랙에서 제거:

- 옵션 B: 라우터 410 Gone + 데이터 보존 (deprecation 기간)
- 옵션 C: 데이터/마이그레이션 완전 제거 (별도 트랙, 본 트랙 범위 외)

참조:
- ``user_mig/TECHSPEC.md`` §16 (R2 + Phase 7.3 단일 진입점 정책)
- ``docs/DB_MIGRATION.md`` §10 (Phase 7 후속 트랙 후보)
- 트랙 #69 분석 (progress.md)
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LLMApiKey(Base):
    """Encrypted API key for an LLM provider, scoped to an organization.

    Inherits ``id`` and audit columns from ``Base``.

    .. deprecated:: Phase 7 R2 (트랙 #69, 2026-05-12)
        DocUtil 의 LLM 호출은 AgentHub `/v1/chat/completions` 단일 진입점
        위임이 표준이다. 본 모델 신규 사용 금지. 운영 키 관리는
        AgentHub 운영자 콘솔로 이전. 자세한 사항은 모듈 docstring 참조.
    """

    __tablename__ = "tb_llm_api_keys"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tb_organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    llm_name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    registered_by: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<LLMApiKey id={self.id!s} llm={self.llm_name!r} prefix={self.api_key_prefix!r}>"
