"""
Tests for the audit-log module endpoints.

Endpoints under test:
- GET /api/v1/audit-logs   -- list paginated audit logs (admin only)
- Role-based access control (member => 403)
- Pagination parameters (page, size)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import TEST_ORG_ID, TEST_USER_ID

# ---------------------------------------------------------------------------
# Reusable test data
# ---------------------------------------------------------------------------

LOG_ID_1 = uuid.uuid4()
LOG_ID_2 = uuid.uuid4()
LOG_ID_3 = uuid.uuid4()
RESOURCE_ID = uuid.uuid4()
NOW = datetime.now(UTC)


def _audit_log_row(
    log_id: uuid.UUID | None = None,
    action: str = "document.upload",
    resource_type: str = "document",
):
    """Return a MagicMock that mimics a raw DB audit-log row.

    The router calls ``AuditLogResponse.model_validate(log)`` on each row,
    so the mock must expose the correct attribute names.
    """
    row = MagicMock()
    row.id = log_id or uuid.uuid4()
    row.organization_id = TEST_ORG_ID
    row.user_id = TEST_USER_ID
    row.action = action
    row.resource_type = resource_type
    row.resource_id = str(RESOURCE_ID)
    row.details = {"filename": "report.pdf"}
    row.ip_address = "192.168.1.10"
    row.created_at = NOW
    return row


# ---------------------------------------------------------------------------
# GET /api/v1/audit-logs -- List audit logs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_audit_logs(client):
    """GET /audit-logs returns a paginated list with action, resource_type, user_id."""
    rows = [
        _audit_log_row(log_id=LOG_ID_1, action="document.upload", resource_type="document"),
        _audit_log_row(log_id=LOG_ID_2, action="user.login", resource_type="user"),
        _audit_log_row(log_id=LOG_ID_3, action="search.execute", resource_type="search"),
    ]

    with patch("app.modules.audit.router.AuditService") as MockService:
        MockService.get_logs = AsyncMock(return_value=(rows, 3))

        resp = await client.get("/api/v1/audit-logs")

    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["size"] == 20
    assert len(body["items"]) == 3

    # Verify structure of each log entry
    first = body["items"][0]
    assert "action" in first
    assert "resource_type" in first
    assert "user_id" in first
    assert first["action"] == "document.upload"
    assert first["resource_type"] == "document"
    assert first["user_id"] == str(TEST_USER_ID)


@pytest.mark.asyncio
async def test_list_audit_logs_with_filters(client):
    """GET /audit-logs respects action and resource_type query filters."""
    rows = [
        _audit_log_row(action="user.login", resource_type="user"),
    ]

    with patch("app.modules.audit.router.AuditService") as MockService:
        MockService.get_logs = AsyncMock(return_value=(rows, 1))

        resp = await client.get(
            "/api/v1/audit-logs",
            params={"action": "user.login", "resource_type": "user"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["action"] == "user.login"


# ---------------------------------------------------------------------------
# Role-based access -- admin only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_logs_admin_only(rbac_client, member_headers):
    """GET /audit-logs returns 403 for a member role."""
    with patch("app.modules.audit.router.AuditService") as MockService:
        MockService.get_logs = AsyncMock(return_value=([], 0))

        resp = await rbac_client.get(
            "/api/v1/audit-logs",
            headers=member_headers,
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_viewer_forbidden(rbac_client, viewer_headers):
    """GET /audit-logs returns 403 for a viewer role."""
    with patch("app.modules.audit.router.AuditService") as MockService:
        MockService.get_logs = AsyncMock(return_value=([], 0))

        resp = await rbac_client.get(
            "/api/v1/audit-logs",
            headers=viewer_headers,
        )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_logs_pagination(client):
    """GET /audit-logs with page/size params returns the correct pagination metadata."""
    rows = [_audit_log_row()]

    with patch("app.modules.audit.router.AuditService") as MockService:
        MockService.get_logs = AsyncMock(return_value=(rows, 50))

        resp = await client.get(
            "/api/v1/audit-logs",
            params={"page": 3, "size": 10},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 3
    assert body["size"] == 10
    assert body["total"] == 50
    assert len(body["items"]) == 1


@pytest.mark.asyncio
async def test_audit_logs_empty(client):
    """GET /audit-logs returns an empty list when there are no logs."""
    with patch("app.modules.audit.router.AuditService") as MockService:
        MockService.get_logs = AsyncMock(return_value=([], 0))

        resp = await client.get("/api/v1/audit-logs")

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
