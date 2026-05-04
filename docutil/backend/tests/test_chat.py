"""
Tests for the chat module endpoints.

Endpoints under test:
- POST /api/v1/chat/sessions            -- create session
- GET  /api/v1/chat/sessions            -- list sessions
- GET  /api/v1/chat/sessions/{id}       -- get session
- POST /api/v1/chat/sessions/{id}/messages  -- send message
- DELETE /api/v1/chat/sessions/{id}     -- delete session
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

SESSION_ID = uuid.uuid4()
DOC_ID_1 = uuid.uuid4()
DOC_ID_2 = uuid.uuid4()
MESSAGE_ID = uuid.uuid4()
NOW = datetime.now(UTC)


def _session_response():
    """Return a MagicMock shaped like ChatSessionResponse."""
    return MagicMock(
        id=SESSION_ID,
        user_id=TEST_USER_ID,
        organization_id=TEST_ORG_ID,
        search_scope_id=None,
        title="Test Session",
        scoped_document_ids=[DOC_ID_1, DOC_ID_2],
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def _message_response():
    """Return a MagicMock shaped like ChatMessageResponse."""
    return MagicMock(
        id=MESSAGE_ID,
        session_id=SESSION_ID,
        role="assistant",
        content="This is the assistant response.",
        citations=None,
        model_used="gpt-4o",
        token_count_input=120,
        token_count_output=45,
        latency_ms=350,
        hallucination_score=0.02,
        created_at=NOW,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/chat/sessions -- Create session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session(client):
    """POST /chat/sessions creates a new session with scoped_document_ids."""
    mock_session = _session_response()

    with patch("app.modules.chat.router.ChatService") as MockService:
        MockService.create_session = AsyncMock(return_value=mock_session)

        resp = await client.post(
            "/api/v1/chat/sessions",
            json={
                "title": "Test Session",
                "scoped_document_ids": [str(DOC_ID_1), str(DOC_ID_2)],
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Test Session"
    assert body["is_active"] is True
    assert len(body["scoped_document_ids"]) == 2


# ---------------------------------------------------------------------------
# GET /api/v1/chat/sessions -- List sessions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions(client):
    """GET /chat/sessions returns a paginated list of sessions."""
    sessions = [_session_response(), _session_response()]

    with patch("app.modules.chat.router.ChatService") as MockService:
        MockService.get_sessions = AsyncMock(return_value=(sessions, 2))

        resp = await client.get("/api/v1/chat/sessions")

    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["size"] == 20
    assert len(body["items"]) == 2


# ---------------------------------------------------------------------------
# GET /api/v1/chat/sessions/{id} -- Get session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session(client):
    """GET /chat/sessions/{id} returns the session details."""
    mock_session = _session_response()

    with patch("app.modules.chat.router.ChatService") as MockService:
        MockService.get_session = AsyncMock(return_value=mock_session)

        resp = await client.get(f"/api/v1/chat/sessions/{SESSION_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(SESSION_ID)
    assert body["title"] == "Test Session"


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    """GET /chat/sessions/{id} returns 404 when the session does not exist."""
    missing_id = uuid.uuid4()

    with patch("app.modules.chat.router.ChatService") as MockService:
        MockService.get_session = AsyncMock(side_effect=ValueError("Session not found"))

        resp = await client.get(f"/api/v1/chat/sessions/{missing_id}")

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/chat/sessions/{id}/messages -- Send message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message(client):
    """POST /chat/sessions/{id}/messages returns the assistant response."""
    mock_session = _session_response()

    # The route collects streaming WebSocketResponse chunks into a single
    # ChatMessageSendResponse. We simulate the async generator that
    # ChatService.process_message yields.
    async def _fake_process_message(**kwargs):
        yield MagicMock(type="chunk", data={"text": "This is "})
        yield MagicMock(type="chunk", data={"text": "the response."})
        yield MagicMock(type="citations", data={"citations": None})
        yield MagicMock(
            type="metadata",
            data={
                "model_used": "gpt-4o",
                "token_count_input": 100,
                "token_count_output": 30,
                "latency_ms": 250,
                "hallucination_score": 0.01,
            },
        )
        yield MagicMock(type="done", data={"message_id": str(MESSAGE_ID)})

    with patch("app.modules.chat.router.ChatService") as MockService:
        MockService.get_session = AsyncMock(return_value=mock_session)
        MockService.process_message = _fake_process_message

        resp = await client.post(
            f"/api/v1/chat/sessions/{SESSION_ID}/messages",
            json={"content": "Hello, can you help me?"},
        )

    assert resp.status_code == 201
    body = resp.json()
    assert "message" in body
    msg = body["message"]
    assert msg["role"] == "assistant"
    assert "This is the response." in msg["content"]


# ---------------------------------------------------------------------------
# DELETE /api/v1/chat/sessions/{id} -- Delete session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_session(client):
    """DELETE /chat/sessions/{id} soft-deletes and returns 204."""
    with patch("app.modules.chat.router.ChatService") as MockService:
        MockService.delete_session = AsyncMock(return_value=None)

        resp = await client.delete(f"/api/v1/chat/sessions/{SESSION_ID}")

    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_session_not_found(client):
    """DELETE /chat/sessions/{id} returns 404 when session is missing."""
    missing_id = uuid.uuid4()

    with patch("app.modules.chat.router.ChatService") as MockService:
        MockService.delete_session = AsyncMock(side_effect=ValueError("Session not found"))

        resp = await client.delete(f"/api/v1/chat/sessions/{missing_id}")

    assert resp.status_code == 404
