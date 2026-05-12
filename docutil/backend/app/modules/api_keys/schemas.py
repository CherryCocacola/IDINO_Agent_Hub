"""Pydantic v2 schemas for the API-keys module.

DEPRECATED — Phase 7 R2 이후 신규 사용 금지 (트랙 #69, 2026-05-12).

운영자 키 발급은 AgentHub 운영자 콘솔(`/admin/api-keys`)로 이전.
본 schema 들은 legacy 호환을 위해 유지되며 신규 클라이언트 통합 대상이 아닙니다.

참조: ``user_mig/TECHSPEC.md`` §16 (Phase 7.3 단일 진입점 정책)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ApiKeyCreate(BaseModel):
    """Payload for registering a new LLM API key.

    .. deprecated:: Phase 7 R2 (트랙 #69)
        신규 키 등록은 AgentHub 운영자 콘솔(`/admin/api-keys`)에서 수행하세요.
    """

    llm_name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Name of the LLM provider (e.g. 'openai', 'anthropic').",
    )
    api_key: str = Field(
        ...,
        min_length=1,
        description="Plain-text API key (will be encrypted at rest).",
    )


class ApiKeyUpdate(BaseModel):
    """Payload for updating an existing API key entry."""

    llm_name: str | None = Field(
        default=None,
        max_length=64,
        description="Updated provider name.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ApiKeyResponse(BaseModel):
    """Public representation of a stored API key (key value is masked)."""

    # DB 컬럼 ins_dt/upd_dt를 created_at/updated_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    llm_name: str
    api_key_prefix: str = Field(..., description="Masked prefix of the original key (e.g. 'sk-abc1****').")
    is_verified: bool
    registered_by: UUID | None = None
    created_at: datetime = Field(validation_alias="ins_dt")
    updated_at: datetime = Field(validation_alias="upd_dt")


class ApiKeyListResponse(BaseModel):
    """Paginated list of API keys."""

    items: list[ApiKeyResponse]
    total: int
    page: int
    size: int


class ApiKeyVerifyResponse(BaseModel):
    """Result of an API-key verification attempt."""

    is_valid: bool = Field(..., description="Whether the key was accepted by the provider.")
    message: str = Field(..., description="Human-readable status message.")
