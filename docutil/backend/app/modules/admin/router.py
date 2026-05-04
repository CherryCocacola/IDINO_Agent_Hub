"""FastAPI router for admin dashboard endpoints.

All routes in this module are mounted under the ``/admin`` prefix by the
application factory.  The router itself uses ``prefix=""`` so that the
parent mount point has full control over the final URL namespace.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role

from .schemas import (
    DashboardMetrics,
    ResponseTimeData,
    SearchErrorData,
    SearchUsageStats,
    UploadStatusChart,
)
from .service import AdminService

router = APIRouter(prefix="", tags=["admin"])


# ---------------------------------------------------------------------------
# GET /dashboard/metrics
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard/metrics",
    response_model=DashboardMetrics,
    summary="Get dashboard metrics",
    description="Return high-level summary metrics for the admin dashboard.",
)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> DashboardMetrics:
    """Aggregate user, document, and search counts for the organisation."""
    return await AdminService.get_dashboard_metrics(
        db, org_id=current_user.organization_id
    )


# ---------------------------------------------------------------------------
# GET /dashboard/search-usage
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard/search-usage",
    response_model=SearchUsageStats,
    summary="Get search usage statistics",
    description="Return aggregated search-request statistics for a given period.",
)
async def get_search_usage(
    period: str = Query("7d", description="Time period (e.g. '7d', '30d', '24h')."),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> SearchUsageStats:
    """Search usage breakdown for the current organisation."""
    return await AdminService.get_search_usage(
        db, org_id=current_user.organization_id, period=period
    )


# ---------------------------------------------------------------------------
# GET /dashboard/upload-status
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard/upload-status",
    response_model=UploadStatusChart,
    summary="Get upload status chart data",
    description="Return document counts grouped by processing status.",
)
async def get_upload_status(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> UploadStatusChart:
    """Upload pipeline status counts for the current organisation."""
    return await AdminService.get_upload_status(
        db, org_id=current_user.organization_id
    )


# ---------------------------------------------------------------------------
# GET /dashboard/response-times
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard/response-times",
    response_model=ResponseTimeData,
    summary="Get response time data",
    description="Return hourly average response times for plotting.",
)
async def get_response_times(
    period: str = Query("24h", description="Time period (e.g. '24h', '7d')."),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> ResponseTimeData:
    """Hourly aggregated response latencies."""
    return await AdminService.get_response_times(
        db, org_id=current_user.organization_id, period=period
    )


# ---------------------------------------------------------------------------
# GET /dashboard/search-errors
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard/search-errors",
    response_model=SearchErrorData,
    summary="Get search error data",
    description="Return daily error counts for search requests.",
)
async def get_search_errors(
    period: str = Query("7d", description="Time period (e.g. '7d', '30d')."),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(["super_admin", "admin", "org_admin"])),
) -> SearchErrorData:
    """Daily search-error counts for the current organisation."""
    return await AdminService.get_search_errors(
        db, org_id=current_user.organization_id, period=period
    )
