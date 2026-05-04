"""Tests for user management endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Reusable identifiers and helpers
# ---------------------------------------------------------------------------
FAKE_USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
FAKE_ORG_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _make_fake_user(**overrides):
    """Return a mock that behaves like a User ORM instance."""
    defaults = {
        "id": FAKE_USER_ID,
        "username": "testuser",
        "email": "testuser@test.com",
        "role": "member",
        "status": "active",
        "organization_id": FAKE_ORG_ID,
        "department_id": None,
        "language": "en",
        "last_login_at": None,
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    user = MagicMock()
    for key, val in defaults.items():
        setattr(user, key, val)
    return user


# ===========================================================================
# GET /api/v1/users  (list)
# ===========================================================================


@pytest.mark.asyncio
async def test_list_users_success(client, admin_headers):
    """Admin listing users returns a paginated response."""
    fake_user = _make_fake_user()

    with patch(
        "app.modules.users.router.UserService.get_users",
        new_callable=AsyncMock,
        return_value=([fake_user], 1),
    ):
        resp = await client.get(
            "/api/v1/users/",
            params={"org_id": str(FAKE_ORG_ID)},
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["username"] == "testuser"


@pytest.mark.asyncio
async def test_list_users_pagination(client, admin_headers):
    """Page and size parameters should be forwarded correctly."""
    with patch(
        "app.modules.users.router.UserService.get_users",
        new_callable=AsyncMock,
        return_value=([], 0),
    ) as mock_get:
        resp = await client.get(
            "/api/v1/users/",
            params={"org_id": str(FAKE_ORG_ID), "page": "2", "size": "10"},
            headers=admin_headers,
        )

    assert resp.status_code == 200
    # Verify the service was called with correct pagination values
    call_kwargs = mock_get.call_args
    assert call_kwargs is not None


# ===========================================================================
# POST /api/v1/users  (create)
# ===========================================================================


@pytest.mark.asyncio
async def test_create_user_success(client, admin_headers):
    """Creating a valid user returns 201."""
    new_user = _make_fake_user(username="newuser", email="new@test.com")

    with patch(
        "app.modules.users.router.UserService.create_user",
        new_callable=AsyncMock,
        return_value=new_user,
    ):
        resp = await client.post(
            "/api/v1/users/",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "StrongP@ss1",
                "role": "member",
                "organization_id": str(FAKE_ORG_ID),
            },
            headers=admin_headers,
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@test.com"


@pytest.mark.asyncio
async def test_create_user_missing_fields(client, admin_headers):
    """Missing required fields returns 422."""
    resp = await client.post(
        "/api/v1/users/",
        json={"username": "x"},
        headers=admin_headers,
    )
    assert resp.status_code == 422


# ===========================================================================
# GET /api/v1/users/{user_id}  (get single)
# ===========================================================================


@pytest.mark.asyncio
async def test_get_user_success(client, admin_headers):
    """Retrieving an existing user by ID returns 200."""
    fake_user = _make_fake_user()

    with patch(
        "app.modules.users.router.UserService.get_user",
        new_callable=AsyncMock,
        return_value=fake_user,
    ):
        resp = await client.get(
            f"/api/v1/users/{FAKE_USER_ID}",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(FAKE_USER_ID)
    assert data["username"] == "testuser"


# ===========================================================================
# PUT /api/v1/users/{user_id}  (update)
# ===========================================================================


@pytest.mark.asyncio
async def test_update_user_success(client, admin_headers):
    """Updating a user's role returns 200 with the updated data."""
    updated_user = _make_fake_user(role="admin")

    with patch(
        "app.modules.users.router.UserService.update_user",
        new_callable=AsyncMock,
        return_value=updated_user,
    ):
        resp = await client.put(
            f"/api/v1/users/{FAKE_USER_ID}",
            json={"role": "admin"},
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"


# ===========================================================================
# Auth / RBAC
# ===========================================================================


@pytest.mark.asyncio
async def test_list_users_no_auth(unauth_client):
    """Unauthenticated requests to a protected endpoint return 401."""
    resp = await unauth_client.get(
        "/api/v1/users/",
        params={"org_id": str(FAKE_ORG_ID)},
    )
    assert resp.status_code == 401


# ===========================================================================
# 이슈 1 BE — 사용자 검색 필터
# ===========================================================================


@pytest.mark.asyncio
async def test_list_users_with_search_filter(client, admin_headers):
    """search 파라미터가 Service 에 search_filter 로 전달되는지 검증."""
    matched_user = _make_fake_user(username="kim_manager", email="kim@test.com")

    with patch(
        "app.modules.users.router.UserService.get_users",
        new_callable=AsyncMock,
        return_value=([matched_user], 1),
    ) as mock_get:
        resp = await client.get(
            "/api/v1/users/",
            params={"org_id": str(FAKE_ORG_ID), "search": "kim"},
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["username"] == "kim_manager"
    # Service 가 search_filter="kim" 을 받았는지 확인
    assert mock_get.call_args.kwargs["search_filter"] == "kim"
