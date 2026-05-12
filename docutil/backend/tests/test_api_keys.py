"""
Tests for the API keys module endpoints.

Endpoints under test:
- GET    /api/v1/api-keys                -- list API keys (masked)
- POST   /api/v1/api-keys               -- create API key
- POST   /api/v1/api-keys/{id}/verify   -- verify API key connection
- DELETE /api/v1/api-keys/{id}           -- delete API key

NOTE: The api_keys router is mounted with prefix="/api/v1" in main.py,
and the router endpoints are defined as "/api-keys", "/api-keys/{key_id}",
etc.  The effective paths are therefore "/api/v1/api-keys/...".
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

KEY_ID = uuid.uuid4()
NOW = datetime.now(UTC)


def _api_key_db_row():
    """Return a MagicMock for the raw DB row that model_validate receives.

    ApiKeyResponse uses validation_alias="ins_dt" / "upd_dt" for
    created_at / updated_at, so the mock must expose those attributes.
    """
    row = MagicMock()
    row.id = KEY_ID
    row.organization_id = TEST_ORG_ID
    row.llm_name = "openai"
    row.api_key_prefix = "sk-abc1****"
    row.is_verified = True
    row.registered_by = TEST_USER_ID
    row.ins_dt = NOW
    row.upd_dt = NOW
    return row


# ---------------------------------------------------------------------------
# GET /api/v1/api-keys -- List API keys
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_api_keys(client):
    """GET /api-keys returns a paginated list of masked API keys."""
    rows = [_api_key_db_row(), _api_key_db_row()]

    with patch("app.modules.api_keys.router.ApiKeyService") as MockService:
        MockService.get_api_keys = AsyncMock(return_value=(rows, 2))

        resp = await client.get("/api/v1/api-keys")

    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["size"] == 20
    # Verify that keys are masked
    for item in body["items"]:
        assert "api_key_prefix" in item
        assert "****" in item["api_key_prefix"]


# ---------------------------------------------------------------------------
# POST /api/v1/api-keys -- Create API key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_api_key(client):
    """POST /api-keys creates a new key and returns a masked response."""
    mock_row = _api_key_db_row()

    with patch("app.modules.api_keys.router.ApiKeyService") as MockService:
        MockService.create_api_key = AsyncMock(return_value=mock_row)

        resp = await client.post(
            "/api/v1/api-keys",
            json={
                "llm_name": "openai",
                "api_key": "sk-abc123456789secretkey",
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["llm_name"] == "openai"
    assert "api_key_prefix" in body
    assert "****" in body["api_key_prefix"]
    # The raw secret must never be in the response
    assert "sk-abc123456789secretkey" not in str(body)


# ---------------------------------------------------------------------------
# POST /api/v1/api-keys/{id}/verify -- Verify API key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_api_key(client):
    """POST /api-keys/{id}/verify tests the provider connection."""
    mock_verify = MagicMock(
        is_valid=True,
        message="Connection successful. Model access verified.",
    )

    with patch("app.modules.api_keys.router.ApiKeyService") as MockService:
        MockService.verify_api_key = AsyncMock(return_value=mock_verify)

        resp = await client.post(f"/api/v1/api-keys/{KEY_ID}/verify")

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_valid"] is True
    assert "successful" in body["message"].lower()


@pytest.mark.asyncio
async def test_verify_api_key_invalid(client):
    """POST /api-keys/{id}/verify returns is_valid=false for a bad key."""
    mock_verify = MagicMock(
        is_valid=False,
        message="Authentication failed. The API key is invalid or expired.",
    )

    with patch("app.modules.api_keys.router.ApiKeyService") as MockService:
        MockService.verify_api_key = AsyncMock(return_value=mock_verify)

        resp = await client.post(f"/api/v1/api-keys/{KEY_ID}/verify")

    assert resp.status_code == 200
    body = resp.json()
    assert body["is_valid"] is False


# ---------------------------------------------------------------------------
# DELETE /api/v1/api-keys/{id} -- Delete API key
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_api_key(client):
    """DELETE /api-keys/{id} removes the key and returns 204."""
    with patch("app.modules.api_keys.router.ApiKeyService") as MockService:
        MockService.delete_api_key = AsyncMock(return_value=None)

        resp = await client.delete(f"/api/v1/api-keys/{KEY_ID}")

    assert resp.status_code == 204


# ---------------------------------------------------------------------------
# Role-based access -- member gets 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_keys_requires_admin(rbac_client, member_headers):
    """GET /api-keys returns 403 for a member role."""
    with patch("app.modules.api_keys.router.ApiKeyService") as MockService:
        MockService.get_api_keys = AsyncMock(return_value=([], 0))

        resp = await rbac_client.get(
            "/api/v1/api-keys",
            headers=member_headers,
        )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 트랙 #69 — Deprecation 헤더 회귀 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_api_keys_responses_include_deprecation_headers(client):
    """모든 api-keys endpoint 응답이 Deprecation 표준 헤더를 포함하는지 검증.

    트랙 #69 (Phase 7 R2): RFC 8594 + IETF deprecation header draft 준수.
    클라이언트가 deprecation 신호를 감지하여 successor-version 으로
    이전할 수 있도록 한다.
    """
    rows = [_api_key_db_row()]

    with patch("app.modules.api_keys.router.ApiKeyService") as MockService:
        MockService.get_api_keys = AsyncMock(return_value=(rows, 1))
        MockService.create_api_key = AsyncMock(return_value=_api_key_db_row())
        MockService.delete_api_key = AsyncMock(return_value=None)
        MockService.verify_api_key = AsyncMock(return_value=MagicMock(is_valid=True, message="ok"))

        # GET /api-keys
        list_resp = await client.get("/api/v1/api-keys")
        # POST /api-keys
        create_resp = await client.post(
            "/api/v1/api-keys",
            json={"llm_name": "openai", "api_key": "sk-test-deprecate"},
        )
        # POST /api-keys/{id}/verify
        verify_resp = await client.post(f"/api/v1/api-keys/{KEY_ID}/verify")
        # DELETE /api-keys/{id}
        delete_resp = await client.delete(f"/api/v1/api-keys/{KEY_ID}")

    for resp, label in [
        (list_resp, "GET /api-keys"),
        (create_resp, "POST /api-keys"),
        (verify_resp, "POST /api-keys/{id}/verify"),
        (delete_resp, "DELETE /api-keys/{id}"),
    ]:
        assert resp.headers.get("Deprecation") == "true", f"{label}: Deprecation 헤더 누락 (트랙 #69 회귀)"
        assert "successor-version" in resp.headers.get("Link", ""), (
            f"{label}: Link successor-version 누락 (트랙 #69 회귀)"
        )
        assert resp.headers.get("X-Deprecation-Track") == "track-69-phase-7-r2", (
            f"{label}: X-Deprecation-Track 누락 (트랙 #69 회귀)"
        )
