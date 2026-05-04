"""
Tests for the search module endpoints.

Endpoints under test:
- POST /api/v1/search/chatbot
- POST /api/v1/search/qa
- POST /api/v1/search/keyword
- POST /api/v1/search/test  (admin only)
- Unauthenticated access returns 401
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Reusable test data
# ---------------------------------------------------------------------------

SCOPE_ID = uuid.uuid4()
DOC_ID = uuid.uuid4()
CHUNK_ID = uuid.uuid4()


def _search_response_data():
    """Return a dict shaped like SearchResponse."""
    return MagicMock(
        query="test",
        results=[
            MagicMock(
                document_id=DOC_ID,
                document_name="doc.pdf",
                chunk_id=CHUNK_ID,
                chunk_index=0,
                content="some content",
                score=0.95,
                page_number=1,
                section_title="Intro",
                chunk_type="text",
                highlights=["test highlight"],
            )
        ],
        total_results=1,
        search_type="hybrid",
        latency_ms=42,
    )


def _chatbot_response_data():
    """Return a dict shaped like ChatbotSearchResponse."""
    return MagicMock(
        answer="This is the chatbot answer based on retrieved context.",
        citations=[
            MagicMock(
                document_id=DOC_ID,
                document_name="doc.pdf",
                page_number=1,
                snippet="relevant excerpt",
                relevance_score=0.9,
            )
        ],
        faq_matches=None,
    )


def _qa_response_data():
    """Return a dict shaped like QASearchResponse."""
    return MagicMock(
        answer="The answer with [1] citations.",
        citations=[
            MagicMock(
                document_id=DOC_ID,
                document_name="doc.pdf",
                page_number=2,
                snippet="source passage",
                relevance_score=0.88,
            )
        ],
        hallucination_score=0.05,
        model_used="gpt-4o",
    )


# ---------------------------------------------------------------------------
# POST /api/v1/search/chatbot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chatbot_search(client):
    """POST /search/chatbot returns 200 with an LLM-grounded answer."""
    mock_data = _chatbot_response_data()

    with patch("app.modules.search.router.SearchService") as MockService:
        MockService.chatbot_search = AsyncMock(return_value=mock_data)

        resp = await client.post(
            "/api/v1/search/chatbot",
            json={
                "query": "test",
                "search_scope_id": str(SCOPE_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert body["answer"] == "This is the chatbot answer based on retrieved context."
    assert isinstance(body.get("citations"), list)


# ---------------------------------------------------------------------------
# POST /api/v1/search/qa
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_qa_search(client):
    """POST /search/qa returns 200 with answer, citations, and hallucination score."""
    mock_data = _qa_response_data()

    with patch("app.modules.search.router.SearchService") as MockService:
        MockService.qa_search = AsyncMock(return_value=mock_data)

        resp = await client.post(
            "/api/v1/search/qa",
            json={
                "query": "What is the policy?",
                "search_scope_id": str(SCOPE_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "citations" in body
    assert len(body["citations"]) >= 1
    assert "hallucination_score" in body
    assert "model_used" in body


# ---------------------------------------------------------------------------
# POST /api/v1/search/keyword
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_keyword_search(client):
    """POST /search/keyword returns 200 with BM25-based results."""
    mock_data = _search_response_data()

    with patch("app.modules.search.router.SearchService") as MockService:
        MockService.keyword_search = AsyncMock(return_value=mock_data)

        resp = await client.post(
            "/api/v1/search/keyword",
            json={
                "query": "configuration settings",
                "search_scope_id": str(SCOPE_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert "total_results" in body
    assert body["total_results"] >= 1
    assert body["search_type"] == "hybrid"


# ---------------------------------------------------------------------------
# POST /api/v1/search/test -- admin only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_test_admin_only(client):
    """POST /search/test succeeds for admin users (the default client is admin)."""
    mock_data = _search_response_data()

    with patch("app.modules.search.router.SearchService") as MockService:
        MockService.hybrid_search = AsyncMock(return_value=mock_data)

        resp = await client.post(
            "/api/v1/search/test",
            json={
                "search_scope_id": str(SCOPE_ID),
                "query": "admin test query",
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body


@pytest.mark.asyncio
async def test_search_test_forbidden_for_member(rbac_client, member_headers):
    """POST /search/test returns 403 when called by a member."""
    with patch("app.modules.search.router.SearchService") as MockService:
        MockService.hybrid_search = AsyncMock(return_value=_search_response_data())

        resp = await rbac_client.post(
            "/api/v1/search/test",
            json={
                "search_scope_id": str(SCOPE_ID),
                "query": "sneaky member query",
            },
            headers=member_headers,
        )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_requires_auth(unauth_client):
    """Endpoints return 401 when no Authorization header is provided."""
    resp = await unauth_client.post(
        "/api/v1/search/chatbot",
        json={"query": "test", "search_scope_id": str(SCOPE_ID)},
    )
    assert resp.status_code == 401
