"""Tests for organisation and department management endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Reusable identifiers and helpers
# ---------------------------------------------------------------------------
FAKE_ORG_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
FAKE_DEPT_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


def _make_fake_org(**overrides):
    """Return a mock that behaves like an Organization ORM instance.

    OrganizationResponse uses validation_alias="ins_dt" for created_at,
    so the mock exposes ins_dt instead of created_at.
    """
    defaults = {
        "id": FAKE_ORG_ID,
        "name": "Test Organization",
        "slug": "test-org",
        "description": "A test organization",
        "settings": None,
        "ins_dt": datetime(2025, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    org = MagicMock()
    for key, val in defaults.items():
        setattr(org, key, val)
    return org


def _make_fake_department(**overrides):
    """Return a dict that matches the new ``DepartmentResponse`` contract.

    트랙 #106 결함 2' 이후: ``DepartmentService.get_departments`` 는
    AgentHub schema 를 raw SQL 로 직접 조회해 dict 리스트를 반환한다.
    Pydantic 의 ``from_attributes=True`` 는 dict 도 받아들이므로 그대로
    ``model_validate`` 된다. ``id`` 는 AgentHub int 의 문자열 표현.
    """
    defaults = {
        "id": str(FAKE_DEPT_ID),
        "organization_id": str(FAKE_ORG_ID),
        "parent_id": None,
        "name": "Engineering",
        "depth": 0,
        "path": f"/{FAKE_DEPT_ID}/",
        "code": None,
        "member_count": 0,
        "head_user_id": None,
        "head_user_name": None,
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return defaults


# ===========================================================================
# GET /api/v1/organizations/{org_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_get_organization_success(client, admin_headers):
    """Retrieving an existing organization returns 200 with correct data."""
    fake_org = _make_fake_org()

    with patch(
        "app.modules.organizations.router.OrganizationService.get_organization",
        new_callable=AsyncMock,
        return_value=fake_org,
    ):
        resp = await client.get(
            f"/api/v1/organizations/{FAKE_ORG_ID}",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(FAKE_ORG_ID)
    assert data["name"] == "Test Organization"
    assert data["slug"] == "test-org"


@pytest.mark.asyncio
async def test_get_organization_not_found(client, admin_headers):
    """Requesting a non-existent org should return 404."""
    from fastapi import HTTPException

    missing_id = uuid.uuid4()

    with patch(
        "app.modules.organizations.router.OrganizationService.get_organization",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=404, detail="Not found"),
    ):
        resp = await client.get(
            f"/api/v1/organizations/{missing_id}",
            headers=admin_headers,
        )

    assert resp.status_code == 404


# ===========================================================================
# PUT /api/v1/organizations/{org_id}
# ===========================================================================


@pytest.mark.asyncio
async def test_update_organization_success(client, admin_headers):
    """Admin can update organization name and description."""
    updated_org = _make_fake_org(name="Updated Org", description="new desc")

    with patch(
        "app.modules.organizations.router.OrganizationService.update_organization",
        new_callable=AsyncMock,
        return_value=updated_org,
    ):
        resp = await client.put(
            f"/api/v1/organizations/{FAKE_ORG_ID}",
            json={"name": "Updated Org", "description": "new desc"},
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Org"
    assert data["description"] == "new desc"


@pytest.mark.asyncio
async def test_update_organization_no_auth(unauth_client):
    """Unauthenticated update should return 401."""
    resp = await unauth_client.put(
        f"/api/v1/organizations/{FAKE_ORG_ID}",
        json={"name": "Hacked Org"},
    )
    assert resp.status_code == 401


# ===========================================================================
# GET /api/v1/organizations/{org_id}/departments
# ===========================================================================


@pytest.mark.asyncio
async def test_list_departments_success(client, admin_headers):
    """Listing departments returns a flat list of department objects."""
    fake_dept = _make_fake_department()

    with patch(
        "app.modules.organizations.router.DepartmentService.get_departments",
        new_callable=AsyncMock,
        return_value=[fake_dept],
    ):
        resp = await client.get(
            f"/api/v1/organizations/{FAKE_ORG_ID}/departments",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Engineering"
    assert data[0]["organization_id"] == str(FAKE_ORG_ID)


@pytest.mark.asyncio
async def test_list_departments_empty(client, admin_headers):
    """An organization with no departments returns an empty list."""
    with patch(
        "app.modules.organizations.router.DepartmentService.get_departments",
        new_callable=AsyncMock,
        return_value=[],
    ):
        resp = await client.get(
            f"/api/v1/organizations/{FAKE_ORG_ID}/departments",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data == []
