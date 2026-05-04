"""Phase 4 S1 D7 — documents_v2 FastAPI 라우터 테스트.

라우터 계약 검증:
    POST    /api/v1/v2/documents        : 생성 202, 에러 매핑 (422/502/503)
    GET     /api/v1/v2/documents/{id}   : 단건 조회, 404, 403 (타 조직)
    GET     /api/v1/v2/documents        : 목록 조회 + 필터 + 페이지네이션
    PATCH   /api/v1/v2/documents/{id}   : 501 (D8 대기)

실 LLM·DB 호출은 전부 mock 으로 대체한다. 조직 스코프 (``organization_id``)
가 SQL 레벨에서 적용되므로, SQLAlchemy select 호출 결과도 monkeypatch 로
제어 가능한 형태로 주입한다.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.documents_v2.exceptions import (
    DocumentGenerationError,
    DocumentSchemaValidationError,
    RAGContextError,
)
from tests.conftest import TEST_ORG_ID, TEST_USER_ID

ROUTE_POST = "/api/v1/v2/documents"
ROUTE_GET_ONE = "/api/v1/v2/documents/{id}"
ROUTE_LIST = "/api/v1/v2/documents"


# ---------------------------------------------------------------------------
# 공용 헬퍼 — mock DocumentV2 인스턴스 생성
# ---------------------------------------------------------------------------


def _make_mock_doc(
    *,
    doc_id: uuid.UUID | None = None,
    org_id: uuid.UUID = TEST_ORG_ID,
    document_type: str = "slide_report",
    mode: str = "free_generation",
    status_val: str = "completed",
    title: str = "테스트 문서",
) -> MagicMock:
    """라우터 응답 변환에 필요한 속성만 갖춘 DocumentV2 mock."""
    doc = MagicMock()
    doc.id = doc_id or uuid.uuid4()
    doc.organization_id = org_id
    doc.generated_by_user_id = TEST_USER_ID
    doc.agent_id = None
    doc.template_id = None
    doc.document_type = document_type
    doc.mode = mode
    doc.title = title
    doc.status = status_val
    doc.error_message = None
    doc.llm_provider = "openai"
    doc.llm_model = "gpt-4o"
    doc.prompt_tokens = None
    doc.completion_tokens = None
    doc.ins_dt = datetime(2026, 4, 19, 10, 0, 0, tzinfo=UTC)
    doc.completed_at = datetime(2026, 4, 19, 10, 0, 5, tzinfo=UTC)
    doc.document_schema = {
        "document_id": str(doc.id),
        "schema_version": "1.0",
        "type": document_type,
        "mode": mode,
        "template_id": None,
        "design_tokens": {
            "primary_color": "#0A4FC2",
            "accent_color": "#FF6B35",
            "text_color": "#1F2937",
            "background_color": "#FFFFFF",
            "font_family": "Pretendard",
            "spacing": "normal",
            "brand_preset": "idino_default",
        },
        "pages": [
            {
                "id": "p1",
                "page_kind": "slide",
                "layout": "title_slide",
                "title": title,
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "text": title,
                        "locked": False,
                        "anchor": None,
                    }
                ],
            }
        ],
        "metadata": {
            "created_at": "2026-04-19T10:00:00+00:00",
            "updated_at": "2026-04-19T10:00:00+00:00",
            "generated_by_user_id": str(TEST_USER_ID),
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "prompt_tokens": None,
            "completion_tokens": None,
            "source_document_ids": [],
            "source_chat_session_id": None,
            "citations": [],
            "degraded_components": [],
        },
    }
    return doc


def _valid_payload(**overrides) -> dict:
    base = {
        "prompt": "Q1 매출 20% 증가 슬라이드 3장 만들어줘",
        "document_type": "slide_report",
        "mode": "free_generation",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. POST 성공 (202)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_create_document_returns_202_on_success(client):
    """정상 흐름: 서비스가 DocumentV2 를 반환하면 202 + DTO."""

    fake_doc = _make_mock_doc()
    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(return_value=fake_doc),
    ) as mock_gen:
        response = await client.post(ROUTE_POST, json=_valid_payload())

    assert response.status_code == 202, response.text
    body = response.json()
    assert body["id"] == str(fake_doc.id)
    assert body["status"] == "completed"
    assert body["document_type"] == "slide_report"
    assert body["mode"] == "free_generation"
    # 서비스 호출 인자 검증
    mock_gen.assert_awaited_once()
    call_kwargs = mock_gen.call_args.kwargs
    assert call_kwargs["org_id"] == TEST_ORG_ID
    assert call_kwargs["user_id"] == TEST_USER_ID
    assert call_kwargs["prompt"].startswith("Q1 매출")
    assert call_kwargs["document_type"] == "slide_report"


# ---------------------------------------------------------------------------
# 2. POST 인증 없음 → 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_without_auth_returns_401(unauth_client):
    """Authorization 헤더 없이 호출 시 401."""
    response = await unauth_client.post(ROUTE_POST, json=_valid_payload())
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 3. POST agent_id 타조직 → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_with_agent_from_other_org_returns_403(client):
    """서비스가 '다른 조직의 에이전트' 에러를 던지면 403 으로 매핑."""

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(
            side_effect=DocumentGenerationError("다른 조직의 에이전트는 사용할 수 없습니다.")
        ),
    ):
        response = await client.post(
            ROUTE_POST,
            json=_valid_payload(agent_id=str(uuid.uuid4())),
        )

    assert response.status_code == 403
    assert "다른 조직" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 4. POST LLM 실패 → 502
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_llm_failure_returns_502(client):
    """LLM 호출 실패 (외부 서비스) 는 502 Bad Gateway 로 매핑."""

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(
            side_effect=DocumentGenerationError("LLM 호출에 실패했습니다. 잠시 후 다시 시도해 주세요.")
        ),
    ):
        response = await client.post(ROUTE_POST, json=_valid_payload())

    assert response.status_code == 502
    assert "LLM" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 5. POST Schema 검증 실패 → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_schema_validation_failure_returns_422(client):
    """LLM 응답 스키마 검증 실패는 422 로 매핑."""

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(
            side_effect=DocumentSchemaValidationError(
                "LLM 응답이 DocumentSchema 를 만족하지 못했습니다."
            )
        ),
    ):
        response = await client.post(ROUTE_POST, json=_valid_payload())

    assert response.status_code == 422
    assert "DocumentSchema" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 5b. POST RAG 실패 → 503 (추가 보강)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_rag_failure_returns_503(client):
    """RAG (Qdrant/DB) 실패는 503 Service Unavailable 로 매핑."""

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(side_effect=RAGContextError("RAG 검색 중 오류가 발생했습니다.")),
    ):
        response = await client.post(ROUTE_POST, json=_valid_payload())

    assert response.status_code == 503
    assert "RAG" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 6. GET 단건 (200)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_document_returns_200_when_found(client, db_session):
    """db.get 이 문서를 반환하면 200 + DTO."""

    target_id = uuid.uuid4()
    fake_doc = _make_mock_doc(doc_id=target_id)

    # db_session.get 을 패치하여 가짜 문서를 반환.
    async def fake_get(model, pk):  # noqa: ARG001
        assert pk == target_id
        return fake_doc

    with patch.object(db_session, "get", new=fake_get):
        response = await client.get(ROUTE_GET_ONE.format(id=target_id))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == str(target_id)
    assert body["organization_id"] == str(TEST_ORG_ID)


# ---------------------------------------------------------------------------
# 7. GET 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_document_returns_404_when_not_found(client, db_session):
    """db.get 이 None 이면 404."""
    target_id = uuid.uuid4()

    async def fake_get(model, pk):  # noqa: ARG001
        return None

    with patch.object(db_session, "get", new=fake_get):
        response = await client.get(ROUTE_GET_ONE.format(id=target_id))

    assert response.status_code == 404
    assert "찾을 수 없" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 8. GET 403 (타조직)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_document_returns_403_when_other_org(client, db_session):
    """문서의 organization_id 가 현재 사용자와 다르면 403."""
    target_id = uuid.uuid4()
    other_org = uuid.UUID("99999999-9999-9999-9999-999999999999")
    fake_doc = _make_mock_doc(doc_id=target_id, org_id=other_org)

    async def fake_get(model, pk):  # noqa: ARG001
        return fake_doc

    with patch.object(db_session, "get", new=fake_get):
        response = await client.get(ROUTE_GET_ONE.format(id=target_id))

    assert response.status_code == 403
    assert "다른 조직" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 9. GET 목록 — 필터 없음
# ---------------------------------------------------------------------------


def _patch_list_execute(db_session, docs: list[MagicMock], total: int):
    """db_session.execute 를 두 호출 (목록 + count) 에 맞춰 패치한다."""

    list_result = MagicMock()
    list_scalars = MagicMock()
    list_scalars.all.return_value = docs
    list_result.scalars.return_value = list_scalars

    count_result = MagicMock()
    count_result.scalar_one.return_value = total

    call_count = {"n": 0}

    async def fake_execute(stmt, *args, **kwargs):  # noqa: ARG001
        call_count["n"] += 1
        # 첫 호출은 목록, 두 번째는 count.
        if call_count["n"] == 1:
            return list_result
        return count_result

    return patch.object(db_session, "execute", new=fake_execute)


@pytest.mark.asyncio
async def test_list_documents_without_filters_returns_paginated_list(client, db_session):
    docs = [_make_mock_doc(title=f"doc-{i}") for i in range(3)]

    with _patch_list_execute(db_session, docs, total=3):
        response = await client.get(ROUTE_LIST)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 20  # default
    assert body["offset"] == 0
    assert len(body["items"]) == 3


# ---------------------------------------------------------------------------
# 10. GET 목록 — document_type 필터
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_documents_with_document_type_filter(client, db_session):
    docs = [_make_mock_doc(document_type="minutes") for _ in range(2)]

    with _patch_list_execute(db_session, docs, total=2):
        response = await client.get(
            ROUTE_LIST, params={"document_type": "minutes"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert all(item["document_type"] == "minutes" for item in body["items"])


# ---------------------------------------------------------------------------
# 11. GET 목록 — 페이지네이션
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_documents_pagination_respects_limit_offset(client, db_session):
    docs = [_make_mock_doc() for _ in range(5)]

    with _patch_list_execute(db_session, docs, total=123):
        response = await client.get(
            ROUTE_LIST, params={"limit": 5, "offset": 20}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 5
    assert body["offset"] == 20
    assert body["total"] == 123
    assert len(body["items"]) == 5


# ---------------------------------------------------------------------------
# 12. PATCH 라우팅 smoke-test (상세는 test_documents_v2_patch.py)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_document_route_delegates_to_service(client):
    """D8: PATCH 엔드포인트는 서비스에 위임하여 성공 시 200 DTO 를 반환한다."""

    target_id = uuid.uuid4()
    fake_doc = _make_mock_doc(doc_id=target_id)

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.apply_patch",
        new=AsyncMock(return_value=fake_doc),
    ) as mock_patch:
        response = await client.patch(
            ROUTE_GET_ONE.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "수정된 제목"},
            },
        )

    assert response.status_code == 200, response.text
    mock_patch.assert_awaited_once()
