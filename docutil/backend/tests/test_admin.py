"""
Tests for the admin dashboard module endpoints.

Endpoints under test:
- GET /api/v1/dashboard/metrics          -- dashboard summary metrics
- GET /api/v1/dashboard/upload-status    -- upload status chart data
- GET /api/v1/dashboard/response-times   -- hourly response time data
- Role-based access control (member => 403)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Reusable test data
# ---------------------------------------------------------------------------


def _dashboard_metrics():
    """Return a MagicMock shaped like DashboardMetrics."""
    return MagicMock(
        total_users=150,
        active_users=120,
        total_documents=3400,
        total_searches=98000,
        feature_usage={
            "chat": 4500,
            "qa": 2200,
            "keyword": 1800,
            "chatbot": 3100,
        },
    )


def _upload_status():
    """Return a MagicMock shaped like UploadStatusChart."""
    return MagicMock(
        completed=2800,
        processing=45,
        waiting=120,
        error=35,
    )


def _response_times():
    """Return a MagicMock shaped like ResponseTimeData."""
    return MagicMock(
        timestamps=[
            "2025-01-15T00:00:00Z",
            "2025-01-15T01:00:00Z",
            "2025-01-15T02:00:00Z",
            "2025-01-15T03:00:00Z",
        ],
        values=[120.5, 135.2, 98.1, 145.7],
    )


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/metrics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_metrics(client):
    """GET /dashboard/metrics returns search_users, feature_usage, registered_docs, total_searches."""
    mock_data = _dashboard_metrics()

    with patch("app.modules.admin.router.AdminService") as MockService:
        MockService.get_dashboard_metrics = AsyncMock(return_value=mock_data)

        resp = await client.get("/api/v1/dashboard/metrics")

    assert resp.status_code == 200
    body = resp.json()
    assert body["total_users"] == 150
    assert body["active_users"] == 120
    assert body["total_documents"] == 3400
    assert body["total_searches"] == 98000
    assert "feature_usage" in body
    assert body["feature_usage"]["chat"] == 4500
    assert body["feature_usage"]["qa"] == 2200


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/upload-status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_status(client):
    """GET /dashboard/upload-status returns document status counts."""
    mock_data = _upload_status()

    with patch("app.modules.admin.router.AdminService") as MockService:
        MockService.get_upload_status = AsyncMock(return_value=mock_data)

        resp = await client.get("/api/v1/dashboard/upload-status")

    assert resp.status_code == 200
    body = resp.json()
    assert body["completed"] == 2800
    assert body["processing"] == 45
    assert body["waiting"] == 120
    assert body["error"] == 35


# ---------------------------------------------------------------------------
# GET /api/v1/dashboard/response-times
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_times(client):
    """GET /dashboard/response-times returns hourly time-series data."""
    mock_data = _response_times()

    with patch("app.modules.admin.router.AdminService") as MockService:
        MockService.get_response_times = AsyncMock(return_value=mock_data)

        resp = await client.get("/api/v1/dashboard/response-times")

    assert resp.status_code == 200
    body = resp.json()
    assert "timestamps" in body
    assert "values" in body
    assert len(body["timestamps"]) == 4
    assert len(body["values"]) == 4
    assert isinstance(body["values"][0], float)


@pytest.mark.asyncio
async def test_response_times_with_period(client):
    """GET /dashboard/response-times respects the period query parameter."""
    mock_data = _response_times()

    with patch("app.modules.admin.router.AdminService") as MockService:
        MockService.get_response_times = AsyncMock(return_value=mock_data)

        resp = await client.get("/api/v1/dashboard/response-times?period=7d")

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Role-based access -- member gets 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_requires_role_metrics(rbac_client, member_headers):
    """GET /dashboard/metrics returns 403 for a member role."""
    with patch("app.modules.admin.router.AdminService") as MockService:
        MockService.get_dashboard_metrics = AsyncMock(return_value=_dashboard_metrics())

        resp = await rbac_client.get(
            "/api/v1/dashboard/metrics",
            headers=member_headers,
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_requires_role_upload_status(rbac_client, member_headers):
    """GET /dashboard/upload-status returns 403 for a member role."""
    with patch("app.modules.admin.router.AdminService") as MockService:
        MockService.get_upload_status = AsyncMock(return_value=_upload_status())

        resp = await rbac_client.get(
            "/api/v1/dashboard/upload-status",
            headers=member_headers,
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_requires_role_response_times(rbac_client, member_headers):
    """GET /dashboard/response-times returns 403 for a member role."""
    with patch("app.modules.admin.router.AdminService") as MockService:
        MockService.get_response_times = AsyncMock(return_value=_response_times())

        resp = await rbac_client.get(
            "/api/v1/dashboard/response-times",
            headers=member_headers,
        )

    assert resp.status_code == 403
