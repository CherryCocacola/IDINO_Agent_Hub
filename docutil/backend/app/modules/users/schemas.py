"""Pydantic schemas for the users module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="member", max_length=32)
    organization_id: UUID
    department_id: UUID | None = None


class UserUpdate(BaseModel):
    """Schema for updating an existing user (all fields optional)."""

    email: EmailStr | None = None
    role: str | None = Field(default=None, max_length=32)
    department_id: UUID | None = None
    language: str | None = Field(default=None, max_length=10)
    status: str | None = Field(default=None, max_length=20)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """사용자 조회 응답 스키마.

    DB 컬럼 ins_dt를 created_at으로 매핑하여 API 응답에서
    일관된 필드명을 제공한다.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    username: str
    email: str
    role: str
    status: str
    organization_id: UUID
    department_id: UUID | None = None
    language: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime = Field(validation_alias="ins_dt")


class UserListResponse(BaseModel):
    """Paginated list of users."""

    items: list[UserResponse]
    total: int
    page: int
    size: int
