"""FastAPI router for audit-log endpoints.

All routes in this module are mounted under the ``/audit`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role

from .schemas import AuditLogFilter, AuditLogListResponse, AuditLogResponse
from .service import AuditService

router = APIRouter(prefix="", tags=["audit"])


# ---------------------------------------------------------------------------
# GET /audit-logs
# ---------------------------------------------------------------------------


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List audit logs",
    description="Return a filtered, paginated list of audit-log entries.",
)
async def list_audit_logs(
    page: int = Query(1, ge=1, description="Page number."),
    size: int = Query(20, ge=1, le=100, description="Items per page."),
    action: str | None = Query(None, description="Filter by action name."),
    resource_type: str | None = Query(None, description="Filter by resource type."),
    user_id: UUID | None = Query(None, description="Filter by acting user ID."),
    start_date: datetime | None = Query(
        None, description="Include entries on or after this timestamp."
    ),
    end_date: datetime | None = Query(
        None, description="Include entries on or before this timestamp."
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> AuditLogListResponse:
    """Retrieve audit logs for the current organisation."""
    filters = AuditLogFilter(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    logs, total = await AuditService.get_logs(
        db,
        org_id=current_user.organization_id,
        filters=filters,
        page=page,
        size=size,
    )
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size,
    )


# ---------------------------------------------------------------------------
# GET /audit-logs/export
# ---------------------------------------------------------------------------


@router.get(
    "/audit-logs/export",
    summary="Export audit logs as CSV",
    description="Download a CSV file containing all matching audit-log entries.",
    response_class=StreamingResponse,
)
async def export_audit_logs(
    action: str | None = Query(None, description="Filter by action name."),
    resource_type: str | None = Query(None, description="Filter by resource type."),
    user_id: UUID | None = Query(None, description="Filter by acting user ID."),
    start_date: datetime | None = Query(
        None, description="Include entries on or after this timestamp."
    ),
    end_date: datetime | None = Query(
        None, description="Include entries on or before this timestamp."
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> StreamingResponse:
    """Export audit logs as a downloadable CSV file."""
    filters = AuditLogFilter(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )
    return await AuditService.export_csv(
        db,
        org_id=current_user.organization_id,
        filters=filters,
    )
