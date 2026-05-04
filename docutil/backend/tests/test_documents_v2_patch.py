"""Phase 4 S1 D8 — ``PATCH /v2/documents/{id}`` 본구현 테스트.

``DocumentServiceV2.apply_patch`` + ``router.patch_document`` 를 같이 검증한다.
실 DB / 실 LLM 호출 없이 ``AsyncMock`` 기반으로 동작한다.

커버 범위 (요구사항의 15건)
---------------------------
1~3.  page patch 성공 / 잘못된 page_id / 유효하지 않은 schema (422)
4~7.  component patch 성공 / type 변경 거부 / 없는 component / locked 필드 업데이트
8~9.  tokens patch 성공 / 필드 부족 (422)
10~11. 낙관적 락 일치 / 불일치 (409)
12~13. 타조직 PATCH (403) / 인증 없음 (401)
14~15. PATCH → GET 응답 반영 / schema_version 증가
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.modules.documents_v2.exceptions import (
    ConcurrentModificationError,
    DocumentGenerationError,
    DocumentSchemaValidationError,
)
from app.modules.documents_v2.models import DocumentV2
from app.modules.documents_v2.schemas import DocumentSchema
from app.modules.documents_v2.service import DocumentServiceV2
from tests.conftest import TEST_ORG_ID, TEST_USER_ID

ROUTE_PATCH = "/api/v1/v2/documents/{id}"


# ---------------------------------------------------------------------------
# 공용 헬퍼
# ---------------------------------------------------------------------------


def _make_valid_schema_dict(
    *, document_id: uuid.UUID | None = None
) -> dict[str, Any]:
    """최소한으로 유효한 DocumentSchema dict 를 반환한다 (mock 문서 저장용)."""

    doc_id = document_id or uuid.uuid4()
    return {
        "document_id": str(doc_id),
        "schema_version": "1.0",
        "type": "slide_report",
        "mode": "free_generation",
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
                "title": "원본 제목",
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "text": "원본 컴포넌트 텍스트",
                        "locked": False,
                        "anchor": None,
                    },
                    {
                        "id": "c2",
                        "type": "Paragraph",
                        "text": "본문 문단",
                        "emphasis": "normal",
                        "locked": False,
                        "anchor": None,
                    },
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


def _make_doc_model(
    *,
    doc_id: uuid.UUID | None = None,
    org_id: uuid.UUID = TEST_ORG_ID,
    schema_version: int = 1,
    schema_dict: dict | None = None,
) -> DocumentV2:
    """실제 ORM 인스턴스를 메모리에만 생성 (DB 저장하지 않음)."""

    actual_id = doc_id or uuid.uuid4()
    doc = DocumentV2(
        id=actual_id,
        organization_id=org_id,
        generated_by_user_id=TEST_USER_ID,
        agent_id=None,
        template_id=None,
        document_type="slide_report",
        mode="free_generation",
        schema_version=schema_version,
        title="테스트 문서",
        status="completed",
        completed_at=datetime(2026, 4, 19, 10, 0, 0, tzinfo=UTC),
        llm_provider="openai",
        llm_model="gpt-4o",
        document_schema=schema_dict or _make_valid_schema_dict(document_id=actual_id),
    )
    # AuditMixin 필드 — SQLAlchemy 가 flush 전엔 None 이므로 명시 세팅.
    doc.ins_dt = datetime(2026, 4, 19, 10, 0, 0, tzinfo=UTC)
    doc.upd_dt = datetime(2026, 4, 19, 10, 0, 0, tzinfo=UTC)
    return doc


def _patch_db_for_service(db_session, doc_model: DocumentV2):
    """``DocumentServiceV2.apply_patch`` 가 사용하는 ``db.execute`` 결과를 패치.

    서비스가 ``select(...).with_for_update()`` 로 문서를 로드하므로,
    execute 응답 객체의 ``scalar_one_or_none`` 이 대상 mock 을 반환하도록 구성한다.
    또한 refresh/flush 는 no-op 으로 둔다.
    """

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = doc_model

    async def fake_execute(stmt, *args, **kwargs):  # noqa: ARG001
        return exec_result

    async def fake_flush():
        return None

    async def fake_refresh(obj):  # noqa: ARG001
        return None

    return (
        patch.object(db_session, "execute", new=fake_execute),
        patch.object(db_session, "flush", new=fake_flush),
        patch.object(db_session, "refresh", new=fake_refresh),
    )


# =============================================================================
# 1~3. page patch
# =============================================================================


@pytest.mark.asyncio
async def test_patch_page_replaces_page_and_bumps_version(client, db_session):
    """1. patch_type='page' 성공: pages[i] 교체 + schema_version 증가."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id, schema_version=3)

    new_page_data = {
        "id": "p1",  # 서버가 강제로 page_id 로 덮어쓰지만 일관성을 위해 동일값
        "page_kind": "slide",
        "layout": "content_body",
        "title": "교체된 제목",
        "locked": False,
        "page_number_visible": True,
        "speaker_notes": None,
        "components": [
            {
                "id": "c1",
                "type": "Heading",
                "level": 1,
                "text": "새 헤딩",
                "locked": False,
                "anchor": None,
            }
        ],
    }

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={"patch_type": "page", "page_id": "p1", "data": new_page_data},
        )

    assert response.status_code == 200, response.text
    body = response.json()

    # 페이지 교체 확인
    assert body["document_schema"]["pages"][0]["title"] == "교체된 제목"
    assert body["document_schema"]["pages"][0]["layout"] == "content_body"
    assert body["document_schema"]["pages"][0]["components"][0]["type"] == "Heading"
    # schema_version 증가 확인
    assert doc_model.schema_version == 4


@pytest.mark.asyncio
async def test_patch_page_with_unknown_page_id_returns_400(client, db_session):
    """2. 존재하지 않는 page_id → 400 Bad Request."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    new_page_data = {
        "id": "p9",
        "page_kind": "slide",
        "layout": "content_body",
        "locked": False,
        "page_number_visible": True,
        "components": [
            {
                "id": "c1",
                "type": "Paragraph",
                "text": "없음",
                "emphasis": "normal",
                "locked": False,
                "anchor": None,
            }
        ],
    }

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={"patch_type": "page", "page_id": "p9", "data": new_page_data},
        )

    assert response.status_code == 400
    assert "페이지를 찾을 수 없습니다" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patch_page_with_invalid_schema_returns_422(client, db_session):
    """3. page patch data 가 유효하지 않은 schema → 422 Unprocessable Entity."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    # components 가 비어 있어 min_length=1 위반
    invalid_page_data = {
        "id": "p1",
        "page_kind": "slide",
        "layout": "content_body",
        "locked": False,
        "page_number_visible": True,
        "components": [],
    }

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "page",
                "page_id": "p1",
                "data": invalid_page_data,
            },
        )

    assert response.status_code == 422
    assert "스키마" in response.json()["detail"] or "검증" in response.json()["detail"]


# =============================================================================
# 4~7. component patch
# =============================================================================


@pytest.mark.asyncio
async def test_patch_component_merges_fields_and_preserves_type(
    client, db_session
):
    """4. component patch 성공: 필드 병합 + type 보존."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "병합된 새 텍스트"},
            },
        )

    assert response.status_code == 200, response.text
    body = response.json()
    comp = body["document_schema"]["pages"][0]["components"][0]
    assert comp["text"] == "병합된 새 텍스트"
    assert comp["type"] == "SlideTitle"  # 타입 보존
    assert comp["id"] == "c1"  # id 보존


@pytest.mark.asyncio
async def test_patch_component_rejects_type_change(client, db_session):
    """5. component type 변경 시도 → 400 (type 보호)."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"type": "Paragraph", "text": "바꾸려는 시도"},
            },
        )

    assert response.status_code == 400
    assert "타입 변경" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patch_component_with_unknown_component_id_returns_400(
    client, db_session
):
    """6. 존재하지 않는 component_id → 400."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c99",
                "data": {"text": "없음"},
            },
        )

    assert response.status_code == 400
    assert "컴포넌트를 찾을 수 없습니다" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patch_component_locked_field_allowed(client, db_session):
    """7. component patch 에 locked=True 필드 → 그대로 저장 허용."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"locked": True, "anchor": "title_slot"},
            },
        )

    assert response.status_code == 200, response.text
    comp = response.json()["document_schema"]["pages"][0]["components"][0]
    assert comp["locked"] is True
    assert comp["anchor"] == "title_slot"
    # type/text 는 기존 유지
    assert comp["type"] == "SlideTitle"
    assert comp["text"] == "원본 컴포넌트 텍스트"


# =============================================================================
# 8~9. tokens patch
# =============================================================================


@pytest.mark.asyncio
async def test_patch_tokens_replaces_design_tokens(client, db_session):
    """8. patch_type='tokens' 성공: design_tokens 전체 교체."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    new_tokens = {
        "primary_color": "#123456",
        "accent_color": "#ABCDEF",
        "text_color": "#000000",
        "background_color": "#FFFFFF",
        "font_family": "NotoSansKR",
        "spacing": "compact",
        "brand_preset": "custom",
    }

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={"patch_type": "tokens", "data": new_tokens},
        )

    assert response.status_code == 200, response.text
    tokens = response.json()["document_schema"]["design_tokens"]
    assert tokens["primary_color"] == "#123456"
    assert tokens["font_family"] == "NotoSansKR"
    assert tokens["spacing"] == "compact"
    assert tokens["brand_preset"] == "custom"


@pytest.mark.asyncio
async def test_patch_tokens_invalid_color_returns_422(client, db_session):
    """9. 토큰 필드가 유효하지 않을 때 → 422 재검증 실패."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    # primary_color 가 hex 패턴 위반
    bad_tokens = {
        "primary_color": "not-a-color",
        "accent_color": "#FF6B35",
        "text_color": "#1F2937",
        "background_color": "#FFFFFF",
        "font_family": "Pretendard",
        "spacing": "normal",
        "brand_preset": "idino_default",
    }

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={"patch_type": "tokens", "data": bad_tokens},
        )

    assert response.status_code == 422


# =============================================================================
# 10~11. 낙관적 락
# =============================================================================


@pytest.mark.asyncio
async def test_patch_with_matching_expected_version_succeeds(
    client, db_session
):
    """10. expected_version 이 현재 schema_version 과 일치 → 성공."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id, schema_version=5)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "v5 기반 수정"},
                "expected_version": 5,
            },
        )

    assert response.status_code == 200, response.text
    assert doc_model.schema_version == 6  # 락 통과 후 증가


@pytest.mark.asyncio
async def test_patch_with_stale_expected_version_returns_409(
    client, db_session
):
    """11. expected_version 이 현재와 다르면 → 409 Conflict."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id, schema_version=7)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "구버전 기반"},
                "expected_version": 3,
            },
        )

    assert response.status_code == 409
    assert "수정되었" in response.json()["detail"]
    # 락 실패 시 schema_version 은 변하지 않아야 함
    assert doc_model.schema_version == 7


# =============================================================================
# 12~13. 권한
# =============================================================================


@pytest.mark.asyncio
async def test_patch_other_org_document_returns_403(client, db_session):
    """12. 타 조직 문서 PATCH → 403 Forbidden."""

    target_id = uuid.uuid4()
    other_org = uuid.UUID("99999999-9999-9999-9999-999999999999")
    doc_model = _make_doc_model(doc_id=target_id, org_id=other_org)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "x"},
            },
        )

    assert response.status_code == 403
    assert "다른 조직" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patch_without_auth_returns_401(unauth_client):
    """13. 인증 없이 PATCH → 401 Unauthorized."""

    target_id = uuid.uuid4()
    response = await unauth_client.patch(
        ROUTE_PATCH.format(id=target_id),
        json={
            "patch_type": "component",
            "page_id": "p1",
            "component_id": "c1",
            "data": {"text": "x"},
        },
    )

    assert response.status_code == 401


# =============================================================================
# 14~15. 회귀 (PATCH 결과 반영 확인)
# =============================================================================


@pytest.mark.asyncio
async def test_patch_response_reflects_modified_schema(client, db_session):
    """14. PATCH 응답의 document_schema 가 수정된 상태를 반영한다."""

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c2",
                "data": {"text": "회귀테스트 수정본", "emphasis": "bold"},
            },
        )

    assert response.status_code == 200
    body = response.json()
    comp = body["document_schema"]["pages"][0]["components"][1]
    assert comp["id"] == "c2"
    assert comp["text"] == "회귀테스트 수정본"
    assert comp["emphasis"] == "bold"
    # 영향받지 않은 컴포넌트는 그대로
    other = body["document_schema"]["pages"][0]["components"][0]
    assert other["text"] == "원본 컴포넌트 텍스트"
    # ORM 속성의 schema_version 과 응답이 일관
    assert doc_model.schema_version == 2


@pytest.mark.asyncio
async def test_patch_increments_schema_version_by_one(client, db_session):
    """15. PATCH 성공 시 schema_version 이 정확히 1 증가한다."""

    target_id = uuid.uuid4()
    initial_version = 10
    doc_model = _make_doc_model(
        doc_id=target_id, schema_version=initial_version
    )

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={"patch_type": "tokens", "data": {
                "primary_color": "#AAAAAA",
                "accent_color": "#BBBBBB",
                "text_color": "#CCCCCC",
                "background_color": "#DDDDDD",
                "font_family": "System",
                "spacing": "relaxed",
                "brand_preset": "idino_mono",
            }},
        )

    assert response.status_code == 200
    assert doc_model.schema_version == initial_version + 1


# =============================================================================
# 추가: 서비스 레이어 단위 테스트 — 예외 직접 검증
# =============================================================================


@pytest.mark.asyncio
async def test_service_apply_patch_raises_on_missing_document(db_session):
    """서비스 레이어: 문서 없음 → DocumentGenerationError."""

    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None

    async def fake_execute(stmt, *args, **kwargs):  # noqa: ARG001
        return exec_result

    with patch.object(db_session, "execute", new=fake_execute):
        with pytest.raises(DocumentGenerationError) as exc_info:
            await DocumentServiceV2.apply_patch(
                db=db_session,
                user_id=TEST_USER_ID,
                org_id=TEST_ORG_ID,
                document_id=uuid.uuid4(),
                patch_type="tokens",
                page_id=None,
                component_id=None,
                data={
                    "primary_color": "#0A4FC2",
                    "accent_color": "#FF6B35",
                    "text_color": "#1F2937",
                    "background_color": "#FFFFFF",
                    "font_family": "Pretendard",
                    "spacing": "normal",
                    "brand_preset": "idino_default",
                },
            )
        assert "찾을 수 없" in str(exc_info.value)


@pytest.mark.asyncio
async def test_service_apply_patch_raises_concurrent_modification(db_session):
    """서비스 레이어: expected_version 불일치 → ConcurrentModificationError."""

    doc_model = _make_doc_model(schema_version=2)
    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh, pytest.raises(ConcurrentModificationError):
        await DocumentServiceV2.apply_patch(
            db=db_session,
            user_id=TEST_USER_ID,
            org_id=TEST_ORG_ID,
            document_id=doc_model.id,
            patch_type="component",
            page_id="p1",
            component_id="c1",
            data={"text": "x"},
            expected_version=1,  # 실제 2 와 불일치
        )


@pytest.mark.asyncio
async def test_service_apply_patch_revalidates_schema(db_session):
    """서비스 레이어: 재검증이 실패하면 DocumentSchemaValidationError."""

    doc_model = _make_doc_model()
    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    # SlideTitle 의 text 최대 길이 초과 (200 자 제한)
    with p_exec, p_flush, p_refresh, pytest.raises(DocumentSchemaValidationError):
        await DocumentServiceV2.apply_patch(
            db=db_session,
            user_id=TEST_USER_ID,
            org_id=TEST_ORG_ID,
            document_id=doc_model.id,
            patch_type="component",
            page_id="p1",
            component_id="c1",
            data={"text": "x" * 201},
        )


@pytest.mark.asyncio
async def test_patch_locked_page_is_rejected(client, db_session):
    """Mode B: page.locked=True 인 페이지의 page patch 는 거부되어야 한다."""

    target_id = uuid.uuid4()
    schema_dict = _make_valid_schema_dict(document_id=target_id)
    schema_dict["pages"][0]["locked"] = True  # 페이지 잠금
    doc_model = _make_doc_model(doc_id=target_id, schema_dict=schema_dict)

    new_page_data = {
        "id": "p1",
        "page_kind": "slide",
        "layout": "content_body",
        "title": "잠긴 페이지 수정 시도",
        "locked": True,
        "page_number_visible": True,
        "components": [
            {
                "id": "c1",
                "type": "Paragraph",
                "text": "수정 시도",
                "emphasis": "normal",
                "locked": False,
                "anchor": None,
            }
        ],
    }

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={"patch_type": "page", "page_id": "p1", "data": new_page_data},
        )

    assert response.status_code == 400
    assert "잠긴" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patch_component_on_locked_page_is_rejected(client, db_session):
    """Mode B: page.locked=True 의 자식 컴포넌트 수정도 거부되어야 한다."""

    target_id = uuid.uuid4()
    schema_dict = _make_valid_schema_dict(document_id=target_id)
    schema_dict["pages"][0]["locked"] = True  # 부모 페이지 잠금
    doc_model = _make_doc_model(doc_id=target_id, schema_dict=schema_dict)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "잠긴 페이지 컴포넌트 수정 시도"},
            },
        )

    assert response.status_code == 400
    assert "잠긴 페이지" in response.json()["detail"]


@pytest.mark.asyncio
async def test_patch_locked_component_is_rejected(client, db_session):
    """Mode B: 이미 locked=True 인 컴포넌트 자체의 내용 수정은 거부되어야 한다.

    단, 잠금 해제 (locked=False) 요청은 허용된다 (편집 재개 시나리오).
    """

    target_id = uuid.uuid4()
    schema_dict = _make_valid_schema_dict(document_id=target_id)
    schema_dict["pages"][0]["components"][0]["locked"] = True  # 컴포넌트 자체 잠금
    doc_model = _make_doc_model(doc_id=target_id, schema_dict=schema_dict)

    # 1) 잠긴 컴포넌트의 text 수정 시도 → 거부
    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "수정 시도"},
            },
        )

    assert response.status_code == 400
    assert "잠긴 컴포넌트" in response.json()["detail"]

    # 2) 잠금 해제 (locked=False) 만 요청 → 허용
    p_exec2, p_flush2, p_refresh2 = _patch_db_for_service(db_session, doc_model)
    with p_exec2, p_flush2, p_refresh2:
        response2 = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"locked": False},
            },
        )

    assert response2.status_code == 200
    comp = response2.json()["document_schema"]["pages"][0]["components"][0]
    assert comp["locked"] is False


@pytest.mark.asyncio
async def test_patch_empty_data_is_noop_but_bumps_version(client, db_session):
    """빈 patch data 라도 200 과 schema_version 증가를 보장한다.

    스키마상 빈 dict 는 component 병합에서 no-op 이며, 재검증을 통과하므로
    의도적으로 200 으로 응답한다 (400 처리하면 UI 가 버저닝을 놓침).
    """

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id, schema_version=4)

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {},
            },
        )

    assert response.status_code == 200
    assert doc_model.schema_version == 5  # 빈 patch 도 버전은 증가


@pytest.mark.asyncio
async def test_service_apply_patch_updates_metadata_updated_at(db_session):
    """서비스 레이어: 성공 시 metadata.updated_at 갱신 확인."""

    doc_model = _make_doc_model()
    before_ts = doc_model.document_schema["metadata"]["updated_at"]

    p_exec, p_flush, p_refresh = _patch_db_for_service(db_session, doc_model)
    with p_exec, p_flush, p_refresh:
        await DocumentServiceV2.apply_patch(
            db=db_session,
            user_id=TEST_USER_ID,
            org_id=TEST_ORG_ID,
            document_id=doc_model.id,
            patch_type="component",
            page_id="p1",
            component_id="c1",
            data={"text": "갱신 확인"},
        )

    # DocumentSchema.model_validate 를 통과했는지 부가 확인
    parsed = DocumentSchema.model_validate(doc_model.document_schema)
    assert parsed.metadata.updated_at.isoformat() != before_ts
