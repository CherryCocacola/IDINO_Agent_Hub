"""Business logic for audit logging."""

from __future__ import annotations

import csv
import io
from uuid import UUID

from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AuditLog
from .schemas import AuditLogFilter


class AuditService:
    """Stateless service methods for creating and querying audit logs."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_log(
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: str | UUID | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """Record a new audit-log entry.

        This is designed to be called from anywhere in the application
        (route handlers, other services, middleware, etc.).
        """
        # Coerce string resource_id to UUID when possible
        _resource_uuid = None
        if resource_id is not None:
            _resource_uuid = (
                resource_id if isinstance(resource_id, UUID) else UUID(str(resource_id))
            )

        log = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=_resource_uuid,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log

    # ------------------------------------------------------------------
    # List with filters
    # ------------------------------------------------------------------

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        org_id: UUID,
        filters: AuditLogFilter,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        """Return a filtered, paginated list of audit logs.

        Returns a tuple of ``(logs, total_count)``.
        """
        base_query = select(AuditLog).where(
            AuditLog.organization_id == org_id
        )

        if filters.action is not None:
            base_query = base_query.where(AuditLog.action == filters.action)
        if filters.resource_type is not None:
            base_query = base_query.where(
                AuditLog.resource_type == filters.resource_type
            )
        if filters.user_id is not None:
            base_query = base_query.where(AuditLog.user_id == filters.user_id)
        if filters.start_date is not None:
            base_query = base_query.where(
                AuditLog.ins_dt >= filters.start_date
            )
        if filters.end_date is not None:
            base_query = base_query.where(
                AuditLog.ins_dt <= filters.end_date
            )

        # Total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # Paginated results
        offset = (page - 1) * size
        items_query = (
            base_query
            .order_by(AuditLog.ins_dt.desc())
            .offset(offset)
            .limit(size)
        )
        result = await db.execute(items_query)
        logs = list(result.scalars().all())

        return logs, total

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    @staticmethod
    async def export_csv(
        db: AsyncSession,
        org_id: UUID,
        filters: AuditLogFilter,
    ) -> StreamingResponse:
        """Generate a CSV file containing all matching audit-log entries.

        Returns a ``StreamingResponse`` suitable for direct return from a
        FastAPI route handler.
        """
        # Fetch all matching logs (no pagination for export)
        base_query = select(AuditLog).where(
            AuditLog.organization_id == org_id
        )

        if filters.action is not None:
            base_query = base_query.where(AuditLog.action == filters.action)
        if filters.resource_type is not None:
            base_query = base_query.where(
                AuditLog.resource_type == filters.resource_type
            )
        if filters.user_id is not None:
            base_query = base_query.where(AuditLog.user_id == filters.user_id)
        if filters.start_date is not None:
            base_query = base_query.where(
                AuditLog.ins_dt >= filters.start_date
            )
        if filters.end_date is not None:
            base_query = base_query.where(
                AuditLog.ins_dt <= filters.end_date
            )

        base_query = base_query.order_by(AuditLog.ins_dt.desc())
        result = await db.execute(base_query)
        logs = list(result.scalars().all())

        # Build CSV in-memory
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id",
            "organization_id",
            "user_id",
            "action",
            "resource_type",
            "resource_id",
            "details",
            "ip_address",
            "created_at",
        ])

        for log in logs:
            writer.writerow([
                str(log.id),
                str(log.organization_id),
                str(log.user_id) if log.user_id else "",
                log.action,
                log.resource_type,
                log.resource_id or "",
                str(log.details) if log.details else "",
                log.ip_address or "",
                log.ins_dt.isoformat(),
            ])

        output.seek(0)

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=audit_logs.csv",
            },
        )
