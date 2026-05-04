"""Pydantic v2 schemas for the audit-log module."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AuditLogResponse(BaseModel):
    """Public representation of a single audit-log entry."""

    # DB 컬럼 ins_dt를 created_at으로 매핑
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    organization_id: UUID
    user_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str | UUID | None = None
    details: dict | None = None
    ip_address: str | None = None
    created_at: datetime = Field(validation_alias="ins_dt")


class AuditLogListResponse(BaseModel):
    """Paginated list of audit-log entries."""

    items: list[AuditLogResponse]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Filter schema
# ---------------------------------------------------------------------------


class AuditLogFilter(BaseModel):
    """Optional filters applied when querying audit logs."""

    action: str | None = Field(default=None, description="Filter by action name.")
    resource_type: str | None = Field(
        default=None, description="Filter by resource type."
    )
    user_id: UUID | None = Field(
        default=None, description="Filter by acting user."
    )
    start_date: datetime | None = Field(
        default=None, description="Include entries on or after this timestamp."
    )
    end_date: datetime | None = Field(
        default=None, description="Include entries on or before this timestamp."
    )
