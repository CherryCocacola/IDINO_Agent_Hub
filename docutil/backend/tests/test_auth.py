"""Tests for the authentication endpoints (login, logout, refresh)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Reusable fake data
# ---------------------------------------------------------------------------
FAKE_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
FAKE_ORG_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _make_fake_user():
    """Return a mock object that mimics a User ORM instance."""
    user = MagicMock()
    user.id = FAKE_USER_ID
    user.username = "admin"
    user.email = "admin@test.com"
    user.role = "admin"
    user.organization_id = FAKE_ORG_ID
    return user


FAKE_TOKENS = {
    "access_token": "fake-access-token",
    "refresh_token": "fake-refresh-token",
    "token_type": "bearer",
}


# ===========================================================================
# POST /api/v1/auth/login
# ===========================================================================


@pytest.mark.asyncio
async def test_login_success(client):
    """Valid credentials should return 200 with access and refresh tokens."""
    fake_user = _make_fake_user()

    with (
        patch(
            "app.modules.auth.router.AuthService.authenticate_user",
            new_callable=AsyncMock,
            return_value=fake_user,
        ),
        patch(
            "app.modules.auth.router.AuthService.create_tokens",
            return_value=FAKE_TOKENS,
        ),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "secret123"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "fake-access-token"
    assert data["refresh_token"] == "fake-refresh-token"
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Invalid credentials should return 401 Unauthorized."""
    with patch(
        "app.modules.auth.router.AuthService.authenticate_user",
        new_callable=AsyncMock,
        return_value=None,
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "wrong", "password": "wrong"},
        )

    assert resp.status_code == 401
    data = resp.json()
    assert "Invalid credentials" in data["detail"]


@pytest.mark.asyncio
async def test_login_missing_fields(client):
    """Missing required fields should return 422 Unprocessable Entity."""
    resp = await client.post("/api/v1/auth/login", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_empty_password(client):
    """An empty password should be rejected by schema validation (422)."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ""},
    )
    assert resp.status_code == 422


# ===========================================================================
# POST /api/v1/auth/logout
# ===========================================================================


@pytest.mark.asyncio
async def test_logout_success(client, admin_headers):
    """A valid bearer token should be blacklisted and return 200."""
    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with (
        patch(
            "app.modules.auth.router.verify_token",
            return_value={
                "sub": str(FAKE_USER_ID),
                "exp": 9999999999,
                "role": "admin",
            },
        ),
        patch(
            "app.modules.auth.router.aioredis.from_url",
            return_value=mock_redis,
        ),
    ):
        resp = await client.post(
            "/api/v1/auth/logout",
            headers=admin_headers,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["detail"] == "Successfully logged out."


@pytest.mark.asyncio
async def test_logout_invalid_token(client, admin_headers):
    """An invalid/expired token should return 401 on logout."""
    with patch(
        "app.modules.auth.router.verify_token",
        return_value=None,
    ):
        resp = await client.post(
            "/api/v1/auth/logout",
            headers=admin_headers,
        )

    assert resp.status_code == 401


# ===========================================================================
# POST /api/v1/auth/refresh
# ===========================================================================


@pytest.mark.asyncio
async def test_refresh_success(client):
    """A valid refresh token should return a new access token."""
    with patch(
        "app.modules.auth.router.AuthService.refresh_token",
        new_callable=AsyncMock,
        return_value="new-access-token",
    ):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "valid-refresh-token"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "new-access-token"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    """An invalid refresh token should return 401."""
    with patch(
        "app.modules.auth.router.AuthService.refresh_token",
        new_callable=AsyncMock,
        side_effect=ValueError("Invalid or expired refresh token."),
    ):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "expired-token"},
        )

    assert resp.status_code == 401
    data = resp.json()
    assert "Invalid or expired" in data["detail"]
