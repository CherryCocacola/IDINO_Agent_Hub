"""Business logic for the admin dashboard module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import case, cast, func, select, Date, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User

from .schemas import (
    DashboardMetrics,
    ResponseTimeData,
    SearchErrorData,
    SearchUsageStats,
    UploadStatusChart,
)


def _period_to_timedelta(period: str) -> timedelta:
    """Convert a period string like '7d' or '24h' to a timedelta."""
    unit = period[-1].lower()
    value = int(period[:-1])
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)
    if unit == "w":
        return timedelta(weeks=value)
    return timedelta(days=value)


class AdminService:
    """Stateless service methods for admin dashboard analytics."""

    # ------------------------------------------------------------------
    # Dashboard metrics
    # ------------------------------------------------------------------

    @staticmethod
    async def get_dashboard_metrics(
        db: AsyncSession,
        org_id: UUID,
    ) -> DashboardMetrics:
        """Return high-level metrics for an organisation's dashboard.

        Counts users (total and active), documents, and search requests
        using SQL aggregation queries.
        """
        from app.modules.documents.models import Document
        from app.modules.chat.models import ChatMessage, ChatSession

        # Total and active users
        user_result = await db.execute(
            select(
                func.count(User.id).label("total"),
                func.count(
                    case((User.status == "active", User.id))
                ).label("active"),
            ).where(User.organization_id == org_id)
        )
        user_row = user_result.one()
        total_users = user_row.total
        active_users = user_row.active

        # Total documents
        doc_result = await db.execute(
            select(func.count(Document.id)).where(
                Document.organization_id == org_id
            )
        )
        total_documents = doc_result.scalar_one()

        # Total searches (chat messages with role 'user' as proxy)
        search_result = await db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.organization_id == org_id,
                ChatMessage.role == "user",
            )
        )
        total_searches = search_result.scalar_one()

        # Feature-usage breakdown
        feature_result = await db.execute(
            select(
                ChatMessage.role,
                func.count(ChatMessage.id),
            )
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(ChatSession.organization_id == org_id)
            .group_by(ChatMessage.role)
        )
        feature_usage = {row[0]: row[1] for row in feature_result.all()}

        return DashboardMetrics(
            total_users=total_users,
            active_users=active_users,
            total_documents=total_documents,
            total_searches=total_searches,
            feature_usage=feature_usage,
        )

    # ------------------------------------------------------------------
    # Search usage
    # ------------------------------------------------------------------

    @staticmethod
    async def get_search_usage(
        db: AsyncSession,
        org_id: UUID,
        period: str = "7d",
    ) -> SearchUsageStats:
        """Return aggregated search-request statistics for *period*."""
        from app.modules.chat.models import ChatMessage, ChatSession

        cutoff = datetime.now(timezone.utc) - _period_to_timedelta(period)

        # Join ChatMessage with ChatSession to filter by organization_id
        result = await db.execute(
            select(
                func.count(ChatMessage.id).label("total"),
            )
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.organization_id == org_id,
                ChatMessage.role == "user",
                ChatMessage.ins_dt >= cutoff,
            )
        )
        row = result.one()

        # Count assistant messages as responses
        response_result = await db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.organization_id == org_id,
                ChatMessage.role == "assistant",
                ChatMessage.ins_dt >= cutoff,
            )
        )
        total_responses = response_result.scalar_one()

        return SearchUsageStats(
            total_requests=row.total,
            total_responses=total_responses,
            total_failures=0,  # No status field in ChatMessage
            period=period,
        )

    # ------------------------------------------------------------------
    # Upload status
    # ------------------------------------------------------------------

    @staticmethod
    async def get_upload_status(
        db: AsyncSession,
        org_id: UUID,
    ) -> UploadStatusChart:
        """Return document counts grouped by processing status."""
        from app.modules.documents.models import Document

        result = await db.execute(
            select(
                Document.status,
                func.count(Document.id),
            )
            .where(Document.organization_id == org_id)
            .group_by(Document.status)
        )
        counts = {row[0]: row[1] for row in result.all()}

        return UploadStatusChart(
            completed=counts.get("completed", 0),
            processing=counts.get("processing", 0),
            waiting=counts.get("waiting", 0),
            error=counts.get("error", 0),
        )

    # ------------------------------------------------------------------
    # Response times
    # ------------------------------------------------------------------

    @staticmethod
    async def get_response_times(
        db: AsyncSession,
        org_id: UUID,
        period: str = "24h",
    ) -> ResponseTimeData:
        """Aggregate chat-message latency_ms by hour for *period*."""
        from app.modules.chat.models import ChatMessage, ChatSession

        cutoff = datetime.now(timezone.utc) - _period_to_timedelta(period)

        hour_trunc = func.date_trunc("hour", ChatMessage.ins_dt)

        result = await db.execute(
            select(
                hour_trunc.label("hour"),
                func.avg(ChatMessage.latency_ms).label("avg_latency"),
            )
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatSession.organization_id == org_id,
                ChatMessage.role == "assistant",
                ChatMessage.latency_ms.isnot(None),
                ChatMessage.ins_dt >= cutoff,
            )
            .group_by(hour_trunc)
            .order_by(hour_trunc)
        )

        timestamps: list[str] = []
        values: list[float] = []
        for row in result.all():
            timestamps.append(row.hour.isoformat())
            values.append(round(float(row.avg_latency), 2))

        return ResponseTimeData(timestamps=timestamps, values=values)

    # ------------------------------------------------------------------
    # Search errors
    # ------------------------------------------------------------------

    @staticmethod
    async def get_search_errors(
        db: AsyncSession,
        org_id: UUID,
        period: str = "7d",
    ) -> SearchErrorData:
        """Count failed search requests per day over *period*.

        Note: ChatMessage doesn't have a status field, so we return empty data.
        In a production system, this would query an error/audit log table.
        """
        # Return empty data since ChatMessage doesn't track error status
        # Generate dates for the period to show on the chart
        delta = _period_to_timedelta(period)
        days = delta.days or 1

        dates: list[str] = []
        error_counts: list[int] = []

        today = datetime.now(timezone.utc).date()
        for i in range(days, 0, -1):
            date = today - timedelta(days=i)
            dates.append(date.strftime("%Y-%m-%d"))
            error_counts.append(0)

        return SearchErrorData(dates=dates, error_counts=error_counts)
