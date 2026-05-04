"""Pydantic schemas for the organisations module."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Organisation schemas
# ---------------------------------------------------------------------------


class OrganizationCreate(BaseModel):
    """Schema for creating a new organisation."""

    name: str = Field(..., min_length=2, max_length=128)
    slug: str = Field(..., min_length=2, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = None
    settings: dict[str, Any] | None = None


class OrganizationUpdate(BaseModel):
    """Schema for updating an existing organisation."""

    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = None
    settings: dict[str, Any] | None = None


class OrganizationResponse(BaseModel):
    """조직 조회 응답 스키마. ins_dt를 created_at으로 매핑한다."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    settings: dict[str, Any] | None = None
    created_at: datetime = Field(validation_alias="ins_dt")


# ---------------------------------------------------------------------------
# Department schemas
# ---------------------------------------------------------------------------


class DepartmentCreate(BaseModel):
    """Schema for creating a new department."""

    name: str = Field(..., min_length=1, max_length=128)
    parent_id: UUID | None = None


class DepartmentUpdate(BaseModel):
    """Schema for updating an existing department."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    parent_id: UUID | None = None


class DepartmentResponse(BaseModel):
    """부서 조회 응답 스키마. ins_dt를 created_at으로 매핑한다."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    parent_id: UUID | None = None
    name: str
    depth: int
    path: str
    created_at: datetime = Field(validation_alias="ins_dt")


class DepartmentTreeResponse(DepartmentResponse):
    """Recursive tree representation of a department with children."""

    children: list[DepartmentTreeResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Quota schemas (Phase 4 S3 D5)
# ---------------------------------------------------------------------------


class QuotaStatusResponse(BaseModel):
    """조직 월 쿼터 현황 응답 스키마.

    Phase 4 S3 D5: FE ImageForm 에서 DALL-E 잔여량을 표시하기 위한 엔드포인트
    ``GET /organizations/{org_id}/quotas/current`` 의 아이템 스키마.

    주의: 본 스키마는 신규 응답 전용이며 기존 Organization/Department 스키마를
    수정하지 않는다 (P1. Single Implementation 유지).
    """

    model_config = ConfigDict(from_attributes=True)

    quota_type: str = Field(..., description="쿼터 유형 (dalle_monthly | unsplash_monthly).")
    monthly_limit: int = Field(..., ge=0, description="월 허용 한도.")
    used_count: int = Field(..., ge=0, description="이번 달 누적 사용량.")
    remaining: int = Field(..., description="잔여 가능량 (limit - used, 음수 가능하지 않음).")
    year_month: str = Field(..., description="대상 연-월 (YYYY-MM).")


class OrganizationQuotasCurrentResponse(BaseModel):
    """``GET /organizations/{org_id}/quotas/current`` 전체 응답 wrapper.

    ``quota_type`` 을 key 로 하는 맵 형태로 반환해 FE 가 특정 쿼터만 빠르게
    조회할 수 있게 한다.
    """

    model_config = ConfigDict(from_attributes=True)

    organization_id: UUID
    year_month: str
    quotas: dict[str, QuotaStatusResponse] = Field(
        default_factory=dict,
        description="quota_type → QuotaStatusResponse 매핑.",
    )


class QuotaUpdateRequest(BaseModel):
    """``PUT /organizations/{org_id}/quotas/{quota_type}`` 요청 바디.

    Phase 4 S3 D6: 관리자 UI 에서 월 한도를 조정하기 위한 최소 스키마.
    현재 월 레코드의 ``monthly_limit`` 만 변경한다. ``used_count`` 는 차감
    로직에서만 갱신되므로 본 요청으로는 건드리지 않는다.
    """

    monthly_limit: int = Field(
        ...,
        ge=0,
        description="새로 적용할 월 한도. 0 이상 정수만 허용 (음수 = DB CHECK 위반).",
    )
