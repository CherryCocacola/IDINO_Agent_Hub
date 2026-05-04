"""Phase 4 S1 D10-B — documents_v2 통합 회귀 테스트.

Phase 3 실행 로드맵 §2.1 D10 에 명시된 ``test_documents_v2.py`` 에 해당하며,
S1 DoD(Definition of Done) 회귀 세트를 완성한다. 기존 분할 파일
(``test_documents_v2_schemas.py``, ``_router.py``, ``_service.py``,
``_patch.py``) 과 **중복되지 않는 12 케이스** 를 신규로 추가한다.

신규 커버 범위 (기존 파일 대비)
----------------------------

1. 버저닝 — ORM ``schema_version`` int 증가 vs JSONB ``schema_version="1.0"``
   유지 (E2E 시연 관찰 해명).
2. 전체 엔드포인트 라운드트립 — POST → GET → LIST → PATCH → GET 일관성.
3. Discriminated Union 22 컴포넌트 ``type`` discriminator 강제 분리.
4. PATCH 동시성 (버전 충돌) — If-Match 없이 2회 연속 PATCH 시 ``schema_version``
   이 순차 증가하는지.
5. PATCH 잘못된 ``patch_type`` → 422 (Pydantic Literal 거부).
6. 대용량 페이지 — ``pages`` max_length=20 경계 (19/20 pass, 21 fail).
7. ``template_id`` CHECK 제약 — Mode A + template_id, Mode B + None 대칭 거부.
8. LLM strict 스키마 회귀 — ``_enforce_openai_strict`` 가 pattern/minLength
   등 unsupported keywords 를 제거하는지.
9. POST 직후 초기 ``schema_version`` 값 확인 (ORM=1, JSON="1.0").
10. POST 시 organization_id 가 JWT 에서 전달되는지 (격리 회귀).

실 LLM/Qdrant 호출은 전부 mock. ``conftest.py`` 의 ``client`` / ``db_session``
픽스처와 ``test_documents_v2_router.py`` 의 mock 헬퍼 패턴을 재사용한다.
"""

from __future__ import annotations

import copy
import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.integrations.llm.schema_adapter import (
    _OPENAI_STRICT_UNSUPPORTED_KEYWORDS,
    pydantic_to_openai_schema,
)
from app.modules.documents_v2.models import DocumentV2
from app.modules.documents_v2.schemas import (
    Component,  # Annotated discriminated union
    DocumentSchema,
    GenerateDocumentRequest,
    PartialDocumentPatch,
)
from app.modules.documents_v2.service import DocumentServiceV2
from tests.conftest import TEST_ORG_ID, TEST_USER_ID

# ---------------------------------------------------------------------------
# 경로 상수
# ---------------------------------------------------------------------------

ROUTE_POST = "/api/v1/v2/documents"
ROUTE_LIST = "/api/v1/v2/documents"
ROUTE_GET_ONE = "/api/v1/v2/documents/{id}"
ROUTE_PATCH = "/api/v1/v2/documents/{id}"


# ---------------------------------------------------------------------------
# 헬퍼 — 모의 문서/스키마 생성
# ---------------------------------------------------------------------------


def _make_valid_schema_dict(
    *,
    document_id: uuid.UUID | None = None,
    n_pages: int = 1,
) -> dict[str, Any]:
    """유효한 DocumentSchema dict 를 ``n_pages`` 만큼 생성한다.

    페이지 id 는 ``p1`` ~ ``pN`` 패턴 (``^p\\d+$``) 으로 유지한다.
    """

    doc_id = document_id or uuid.uuid4()
    pages: list[dict[str, Any]] = []
    for i in range(1, n_pages + 1):
        pages.append(
            {
                "id": f"p{i}",
                "page_kind": "slide",
                "layout": "content_body",
                "title": f"페이지 {i}",
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "text": f"제목 {i}",
                        "locked": False,
                        "anchor": None,
                    }
                ],
            }
        )
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
        "pages": pages,
        "metadata": {
            "created_at": "2026-04-22T10:00:00+00:00",
            "updated_at": "2026-04-22T10:00:00+00:00",
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
    status_val: str = "completed",
    title: str = "D10 회귀 문서",
) -> DocumentV2:
    """ORM ``DocumentV2`` 메모리 인스턴스를 반환 (DB flush 미수행)."""

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
        title=title,
        status=status_val,
        completed_at=datetime(2026, 4, 22, 10, 0, 0, tzinfo=UTC),
        llm_provider="openai",
        llm_model="gpt-4o",
        document_schema=schema_dict
        or _make_valid_schema_dict(document_id=actual_id),
    )
    doc.ins_dt = datetime(2026, 4, 22, 10, 0, 0, tzinfo=UTC)
    doc.upd_dt = datetime(2026, 4, 22, 10, 0, 0, tzinfo=UTC)
    return doc


def _patch_db_for_patch_service(db_session, doc_model: DocumentV2):
    """``DocumentServiceV2.apply_patch`` 가 사용하는 DB 메서드 mock.

    ``test_documents_v2_patch.py`` 의 ``_patch_db_for_service`` 와 동일한
    패턴을 재사용한다. 순환 import 를 피하기 위해 여기 복제.
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
# 1. 버저닝: ORM schema_version 증가 + JSON schema_version "1.0" 유지
# =============================================================================


@pytest.mark.asyncio
async def test_patch_bumps_orm_schema_version_but_keeps_json_literal_1_0(
    client, db_session
):
    """PATCH 후 ORM ``schema_version`` (int) 만 증가하고 JSONB 내
    ``schema_version`` 은 문자열 ``"1.0"`` (Literal) 으로 유지되는지.

    E2E 시연 (2026-04-23) 에서 "1.0 → 1.0" 관찰된 것은 **JSON 필드** 가
    ``Literal["1.0"]`` 로 고정되어 있기 때문. ORM 의 int 버전만 증가하는 것이
    Phase 1 설계 (JSON=major.minor 표현, DB=정수 리비전) 와 일치한다.
    """

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id, schema_version=1)
    assert doc_model.document_schema["schema_version"] == "1.0"

    p_exec, p_flush, p_refresh = _patch_db_for_patch_service(
        db_session, doc_model
    )
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "버저닝 확인"},
            },
        )

    assert response.status_code == 200, response.text
    # ORM 의 정수 버전은 1 → 2
    assert doc_model.schema_version == 2
    # JSONB 내 schema_version 은 그대로 "1.0" (Literal)
    assert doc_model.document_schema["schema_version"] == "1.0"
    # 응답 JSON 도 동일
    assert response.json()["document_schema"]["schema_version"] == "1.0"


# =============================================================================
# 2. 전체 엔드포인트 라운드트립 — POST → GET → LIST → PATCH → GET
# =============================================================================


@pytest.mark.asyncio
async def test_full_roundtrip_post_get_list_patch_get_keeps_consistency(
    client, db_session
):
    """POST → GET → LIST → PATCH → GET 전체 라운드트립 시 id/제목/버전 일관성.

    실제 DB 에 데이터가 없으므로 각 단계의 mock 을 순차 주입한다. 라운드트립의
    목적은 **엔드포인트 체인 전체가 한 번 깨지지 않고 연결되는지** 확인하는 것.
    """

    # ── 1) POST: 서비스가 새 ORM 인스턴스를 돌려준다. ───────────────────
    created_id = uuid.uuid4()
    created_doc = _make_doc_model(
        doc_id=created_id, schema_version=1, title="라운드트립 문서"
    )

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(return_value=created_doc),
    ):
        post_resp = await client.post(
            ROUTE_POST,
            json={
                "prompt": "라운드트립 테스트",
                "document_type": "slide_report",
                "mode": "free_generation",
            },
        )
    assert post_resp.status_code == 202, post_resp.text
    post_body = post_resp.json()
    assert post_body["id"] == str(created_id)
    assert post_body["title"] == "라운드트립 문서"

    # ── 2) GET 단건: db.get 이 같은 doc 을 반환. ──────────────────────
    async def fake_get(model, pk):  # noqa: ARG001
        assert pk == created_id
        return created_doc

    with patch.object(db_session, "get", new=fake_get):
        get_resp = await client.get(ROUTE_GET_ONE.format(id=created_id))
    assert get_resp.status_code == 200, get_resp.text
    assert get_resp.json()["id"] == str(created_id)
    assert get_resp.json()["title"] == "라운드트립 문서"

    # ── 3) LIST: 같은 문서를 목록에 포함. ────────────────────────────
    list_result = MagicMock()
    list_scalars = MagicMock()
    list_scalars.all.return_value = [created_doc]
    list_result.scalars.return_value = list_scalars
    count_result = MagicMock()
    count_result.scalar_one.return_value = 1

    call_count = {"n": 0}

    async def fake_execute_list(stmt, *args, **kwargs):  # noqa: ARG001
        call_count["n"] += 1
        return list_result if call_count["n"] == 1 else count_result

    with patch.object(db_session, "execute", new=fake_execute_list):
        list_resp = await client.get(ROUTE_LIST)
    assert list_resp.status_code == 200
    list_body = list_resp.json()
    assert list_body["total"] == 1
    assert list_body["items"][0]["id"] == str(created_id)

    # ── 4) PATCH: apply_patch 로 같은 doc 의 title/ver 을 갱신. ─────
    p_exec, p_flush, p_refresh = _patch_db_for_patch_service(
        db_session, created_doc
    )
    with p_exec, p_flush, p_refresh:
        patch_resp = await client.patch(
            ROUTE_PATCH.format(id=created_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "라운드트립 후 제목"},
            },
        )
    assert patch_resp.status_code == 200, patch_resp.text
    assert created_doc.schema_version == 2

    # ── 5) 최종 GET: 갱신된 버전과 필드가 반영되는지. ────────────────
    with patch.object(db_session, "get", new=fake_get):
        final_get = await client.get(ROUTE_GET_ONE.format(id=created_id))
    assert final_get.status_code == 200
    final_body = final_get.json()
    # 라운드트립 끝까지 id 가 동일
    assert final_body["id"] == str(created_id)
    # 수정된 컴포넌트 text 가 반영됨 (mock 동일 인스턴스)
    assert (
        final_body["document_schema"]["pages"][0]["components"][0]["text"]
        == "라운드트립 후 제목"
    )


# =============================================================================
# 3. Discriminated Union — type discriminator 강제 (중요 4종)
# =============================================================================


@pytest.mark.parametrize(
    "valid_payload, wrong_type",
    [
        # KPI: label/value 필수 — Paragraph 는 text 필수 → label/value 가 extra=forbid 위반
        (
            {
                "id": "c1",
                "type": "KPI",
                "label": "매출",
                "value": "₩1B",
            },
            "Paragraph",
        ),
        # Heading: level 필수 — Paragraph 에는 level 필드가 없어 extra=forbid 위반
        (
            {"id": "c1", "type": "Heading", "text": "H1", "level": 1},
            "Paragraph",
        ),
        # DataTable: headers/rows 필수 — Paragraph 로는 해당 필드 모두 금지
        (
            {
                "id": "c1",
                "type": "DataTable",
                "headers": ["A", "B"],
                "rows": [["1", "2"]],
            },
            "Paragraph",
        ),
        # BulletList: items 필수 — SlideTitle 로는 items 불가
        (
            {
                "id": "c1",
                "type": "BulletList",
                "items": [{"text": "항목"}],
            },
            "SlideTitle",
        ),
    ],
)
def test_discriminated_union_rejects_mismatched_type_for_required_fields(
    valid_payload, wrong_type
):
    """Discriminated Union: 특정 타입의 필수 필드가 다른 타입으로 검증되면 거부.

    Pydantic v2 Discriminated Union 은 ``type`` 값을 discriminator 로 사용해
    정확한 서브모델을 선택한다. type 을 엉뚱한 값으로 바꾸면 그 서브모델의
    ``extra="forbid"`` 설정 때문에 필드 불일치로 ValidationError.
    """

    from pydantic import TypeAdapter

    # 1) 원래 type 으로는 OK
    adapter = TypeAdapter(Component)
    validated = adapter.validate_python(valid_payload)
    assert validated.type == valid_payload["type"]

    # 2) type 을 엉뚱하게 바꾸면 거부
    bad_payload = dict(valid_payload)
    bad_payload["type"] = wrong_type
    with pytest.raises(ValidationError):
        adapter.validate_python(bad_payload)


def test_discriminated_union_unknown_type_raises_discriminator_error():
    """알려지지 않은 ``type`` 값 → discriminator tag 매칭 실패."""

    from pydantic import TypeAdapter

    adapter = TypeAdapter(Component)
    with pytest.raises(ValidationError) as exc_info:
        adapter.validate_python(
            {"id": "c1", "type": "BogusComponent", "text": "x"}
        )
    # discriminator 실패 힌트가 메시지에 포함되어야 한다
    msg = str(exc_info.value).lower()
    assert "discriminator" in msg or "tag" in msg or "union" in msg


# =============================================================================
# 4. PATCH 동시성 — 2회 연속 PATCH 시 schema_version 순차 증가
# =============================================================================


@pytest.mark.asyncio
async def test_consecutive_patches_without_lock_increment_version_sequentially(
    client, db_session
):
    """If-Match (expected_version) 없이 2회 연속 PATCH 시 schema_version 이
    ``v → v+1 → v+2`` 로 단조 증가하는지 (락 생략 경로 회귀).
    """

    target_id = uuid.uuid4()
    doc_model = _make_doc_model(doc_id=target_id, schema_version=10)

    # 첫 PATCH
    p_exec1, p_flush1, p_refresh1 = _patch_db_for_patch_service(
        db_session, doc_model
    )
    with p_exec1, p_flush1, p_refresh1:
        r1 = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "수정 1"},
            },
        )
    assert r1.status_code == 200
    assert doc_model.schema_version == 11

    # 둘째 PATCH (동일 세션, expected_version 없음)
    p_exec2, p_flush2, p_refresh2 = _patch_db_for_patch_service(
        db_session, doc_model
    )
    with p_exec2, p_flush2, p_refresh2:
        r2 = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "component",
                "page_id": "p1",
                "component_id": "c1",
                "data": {"text": "수정 2"},
            },
        )
    assert r2.status_code == 200
    assert doc_model.schema_version == 12


# =============================================================================
# 5. PATCH 잘못된 patch_type → 422
# =============================================================================


@pytest.mark.asyncio
async def test_patch_with_invalid_patch_type_returns_422(client, db_session):
    """``patch_type`` 가 ``page|component|tokens`` 외 값이면 Pydantic Literal
    가 거부해 422 를 응답한다.
    """

    target_id = uuid.uuid4()
    # db 는 문서 로드 전에 Pydantic 검증이 실패하므로 실제 호출되지 않지만
    # 안전하게 mock 해둔다.
    doc_model = _make_doc_model(doc_id=target_id)
    p_exec, p_flush, p_refresh = _patch_db_for_patch_service(
        db_session, doc_model
    )
    with p_exec, p_flush, p_refresh:
        response = await client.patch(
            ROUTE_PATCH.format(id=target_id),
            json={
                "patch_type": "metadata",  # 허용 외 값
                "data": {"whatever": True},
            },
        )

    assert response.status_code == 422
    body = response.json()
    # FastAPI 는 validation error 를 detail 리스트로 반환
    detail = body.get("detail")
    assert detail is not None
    assert any(
        "patch_type" in str(err) for err in (detail if isinstance(detail, list) else [detail])
    )


# =============================================================================
# 6. 대용량 페이지 경계 — max_length=20
# =============================================================================


def test_document_schema_accepts_20_pages_at_boundary():
    """pages=20 (max_length 경계) 는 통과한다."""

    payload = _make_valid_schema_dict(n_pages=20)
    doc = DocumentSchema.model_validate(payload)
    assert len(doc.pages) == 20


def test_document_schema_accepts_19_pages_below_boundary():
    """pages=19 도 당연히 통과 (경계 바로 아래)."""

    payload = _make_valid_schema_dict(n_pages=19)
    doc = DocumentSchema.model_validate(payload)
    assert len(doc.pages) == 19


def test_document_schema_rejects_21_pages_above_boundary():
    """pages=21 은 max_length=20 위반 → ValidationError."""

    payload = _make_valid_schema_dict(n_pages=21)
    with pytest.raises(ValidationError) as exc_info:
        DocumentSchema.model_validate(payload)
    # max_length 힌트가 에러 메시지에 포함
    assert "20" in str(exc_info.value) or "max_length" in str(exc_info.value).lower()


# =============================================================================
# 7. template_id CHECK 제약 — Pydantic 레벨 대칭 검증
# =============================================================================


def test_free_generation_with_template_id_is_rejected():
    """Mode A (free_generation) 인데 template_id 가 있으면 거부.

    ``DocumentSchema._template_id_consistency`` 에서 막는다. DB CHECK 제약
    (``ck_tb_documents_v2_template_consistency``) 과 대칭이다.
    """

    payload = _make_valid_schema_dict()
    payload["mode"] = "free_generation"
    payload["template_id"] = str(uuid.uuid4())
    with pytest.raises(ValidationError) as exc_info:
        DocumentSchema.model_validate(payload)
    assert "template_id" in str(exc_info.value)


def test_template_fill_without_template_id_is_rejected():
    """Mode B (template_fill) 인데 template_id 가 None 이면 거부."""

    payload = _make_valid_schema_dict()
    payload["mode"] = "template_fill"
    payload["template_id"] = None
    with pytest.raises(ValidationError) as exc_info:
        DocumentSchema.model_validate(payload)
    assert "template_id" in str(exc_info.value)


# =============================================================================
# 8. LLM strict 스키마 회귀 — unsupported keywords 제거 확인
# =============================================================================


def test_enforce_openai_strict_removes_unsupported_validation_keywords():
    """``pydantic_to_openai_schema(strict=True)`` 의 반환 스키마에는
    ``_OPENAI_STRICT_UNSUPPORTED_KEYWORDS`` 에 속한 키가 하나도 없어야 한다.

    D8 H12 회귀: pattern / minLength / maxItems 등이 남아있으면 OpenAI
    API 가 400 Bad Request 를 반환한다 (D7 live API 에서 확인된 이슈).
    """

    wrapper = pydantic_to_openai_schema(DocumentSchema, strict=True)
    schema = wrapper["schema"]

    # 재귀적으로 모든 노드의 키를 모은다.
    def _walk(node: Any) -> list[str]:
        out: list[str] = []
        if isinstance(node, dict):
            out.extend(node.keys())
            for v in node.values():
                out.extend(_walk(v))
        elif isinstance(node, list):
            for item in node:
                out.extend(_walk(item))
        return out

    all_keys = set(_walk(schema))
    violations = all_keys & _OPENAI_STRICT_UNSUPPORTED_KEYWORDS
    assert not violations, (
        f"OpenAI strict 모드 호환 스키마에 금지 키워드가 남아 있습니다: "
        f"{violations}"
    )


def test_enforce_openai_strict_converts_oneof_to_anyof_and_removes_discriminator():
    """Discriminated Union 은 ``oneOf + discriminator`` → ``anyOf`` 로 치환.

    OpenAI strict 는 ``oneOf`` / ``discriminator`` 키워드를 거부한다.
    """

    wrapper = pydantic_to_openai_schema(DocumentSchema, strict=True)
    schema = wrapper["schema"]

    # 재귀 탐색으로 oneOf/discriminator 잔존 여부 확인
    def _has_key(node: Any, key: str) -> bool:
        if isinstance(node, dict):
            if key in node:
                return True
            return any(_has_key(v, key) for v in node.values())
        if isinstance(node, list):
            return any(_has_key(item, key) for item in node)
        return False

    assert not _has_key(schema, "oneOf"), "oneOf 가 anyOf 로 치환되지 않았습니다"
    assert not _has_key(schema, "discriminator"), "discriminator 가 제거되지 않았습니다"
    # anyOf 는 존재 (Component union)
    assert _has_key(schema, "anyOf"), "anyOf 가 생성되지 않았습니다"


# =============================================================================
# 9. POST 직후 초기 schema_version — ORM=1, JSON="1.0"
# =============================================================================


@pytest.mark.asyncio
async def test_post_initial_schema_version_is_1_at_orm_and_1_0_at_json(
    client,
):
    """POST 로 생성 직후 반환된 문서의 버전 필드 값:

    - ORM ``schema_version`` (DB 컬럼, int) = 1
    - JSONB ``document_schema.schema_version`` (Literal) = "1.0"
    """

    created_id = uuid.uuid4()
    fake_doc = _make_doc_model(doc_id=created_id, schema_version=1)
    # JSON 내부의 schema_version 확인을 위해 헬퍼가 생성하는 값 점검
    assert fake_doc.document_schema["schema_version"] == "1.0"

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(return_value=fake_doc),
    ):
        resp = await client.post(
            ROUTE_POST,
            json={
                "prompt": "버전 초기값 확인",
                "document_type": "slide_report",
                "mode": "free_generation",
            },
        )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    # 응답 DTO 에는 ORM 의 schema_version 은 직접 노출되지 않지만 JSON 안에 있음
    assert body["document_schema"]["schema_version"] == "1.0"
    # ORM 모델 자체는 초기값 1
    assert fake_doc.schema_version == 1


# =============================================================================
# 10. 조직 격리 (POST) — 서비스 호출 시 JWT 의 org_id 가 전달되는지
# =============================================================================


@pytest.mark.asyncio
async def test_post_passes_jwt_organization_id_to_service(client):
    """POST 가 항상 ``current_user.organization_id`` 를 ``generate`` 에 전달.

    다른 조직의 ORG_ID 로 생성을 시도해도 서비스는 JWT 의 조직 id 만 본다.
    ``conftest.py`` 의 ``client`` 는 ``TEST_ORG_ID`` 로 고정되어 있으므로,
    서비스 호출의 org_id 도 반드시 ``TEST_ORG_ID`` 여야 한다.
    """

    created_id = uuid.uuid4()
    fake_doc = _make_doc_model(doc_id=created_id)

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(return_value=fake_doc),
    ) as mock_gen:
        response = await client.post(
            ROUTE_POST,
            json={
                "prompt": "조직 격리 회귀",
                "document_type": "slide_report",
                "mode": "free_generation",
            },
        )

    assert response.status_code == 202, response.text
    mock_gen.assert_awaited_once()
    kwargs = mock_gen.call_args.kwargs
    assert kwargs["org_id"] == TEST_ORG_ID
    assert kwargs["user_id"] == TEST_USER_ID


# =============================================================================
# 부록 — GenerateDocumentRequest schema 회귀 (Mode B 는 D8 에서 활성화)
# =============================================================================


def test_generate_request_rejects_unknown_document_type_via_pydantic():
    """``GenerateDocumentRequest.document_type`` 은 Literal 7종만 허용.

    라우터 진입 전 Pydantic 단계에서 알 수 없는 타입을 거부 → 422 유도.
    """

    with pytest.raises(ValidationError):
        GenerateDocumentRequest(
            prompt="뭐든",
            document_type="unknown_type",  # Literal 에 없음
            mode="free_generation",
        )


def test_partial_document_patch_component_requires_both_ids():
    """PATCH component 요청은 ``page_id`` 와 ``component_id`` 모두 필요."""

    # page_id 만 있고 component_id 없음 → 거부
    with pytest.raises(ValidationError) as exc_info:
        PartialDocumentPatch(
            patch_type="component",
            page_id="p1",
            component_id=None,
            data={"text": "x"},
        )
    assert "component_id" in str(exc_info.value) or "component" in str(exc_info.value)


def test_partial_document_patch_tokens_disallows_identifiers():
    """PATCH tokens 에는 ``page_id`` / ``component_id`` 를 지정하면 안 된다."""

    with pytest.raises(ValidationError) as exc_info:
        PartialDocumentPatch(
            patch_type="tokens",
            page_id="p1",
            data={
                "primary_color": "#000000",
                "accent_color": "#111111",
                "text_color": "#222222",
                "background_color": "#FFFFFF",
                "font_family": "Pretendard",
                "spacing": "normal",
                "brand_preset": "idino_default",
            },
        )
    assert "page_id" in str(exc_info.value) or "tokens" in str(exc_info.value)


# =============================================================================
# 서비스 레이어 회귀 — metadata.updated_at 재갱신 여부
# =============================================================================


@pytest.mark.asyncio
async def test_service_patch_updates_metadata_updated_at_timestamp(db_session):
    """PATCH 후 ``document_schema.metadata.updated_at`` 이 최신 시각으로 갱신.

    ``test_documents_v2_patch.py`` 의 동일 이름 테스트는 다른 의미
    (문자열 변경 여부) 를 보지만, 본 테스트는 갱신 값이 **원본 대비 미래**
    인지까지 확인한다. Phase 1 설계의 "편집 시 metadata 갱신" 규약 회귀.
    """

    doc_model = _make_doc_model()
    before = datetime.fromisoformat(
        doc_model.document_schema["metadata"]["updated_at"]
    )

    p_exec, p_flush, p_refresh = _patch_db_for_patch_service(
        db_session, doc_model
    )
    with p_exec, p_flush, p_refresh:
        await DocumentServiceV2.apply_patch(
            db=db_session,
            user_id=TEST_USER_ID,
            org_id=TEST_ORG_ID,
            document_id=doc_model.id,
            patch_type="component",
            page_id="p1",
            component_id="c1",
            data={"text": "타임스탬프 갱신 확인"},
        )

    after_raw = doc_model.document_schema["metadata"]["updated_at"]
    after = datetime.fromisoformat(after_raw)
    # 갱신된 시각은 원본 이후
    assert after > before
    # tz-aware 인지 확인
    assert after.tzinfo is not None


# =============================================================================
# DocumentSchema 전용 불변식 — components 배열 min/max 경계
# =============================================================================


def test_page_with_empty_components_is_rejected():
    """components 가 빈 배열이면 min_length=1 위반."""

    payload = _make_valid_schema_dict()
    payload["pages"][0]["components"] = []
    with pytest.raises(ValidationError):
        DocumentSchema.model_validate(payload)


def test_page_with_more_than_ten_components_is_rejected():
    """components 가 10개 초과면 max_length=10 위반."""

    payload = _make_valid_schema_dict()
    # 11개 컴포넌트로 부풀리기
    payload["pages"][0]["components"] = [
        {
            "id": f"c{i}",
            "type": "Paragraph",
            "text": f"문단 {i}",
            "emphasis": "normal",
            "locked": False,
            "anchor": None,
        }
        for i in range(1, 12)
    ]
    with pytest.raises(ValidationError) as exc_info:
        DocumentSchema.model_validate(payload)
    assert "10" in str(exc_info.value) or "max_length" in str(exc_info.value).lower()


# =============================================================================
# 회귀: 부록 A.1 round-trip JSON serialization
# =============================================================================


def test_document_schema_round_trip_preserves_component_types():
    """``model_validate`` → ``model_dump`` → ``model_validate`` 라운드트립.

    22 개 컴포넌트 중 실제로 쓰이는 주요 타입이 dump/재검증 후에도 보존됨.
    """

    payload = _make_valid_schema_dict()
    # 다양한 컴포넌트 타입 추가
    payload["pages"][0]["components"] = [
        {
            "id": "c1",
            "type": "SlideTitle",
            "text": "제목",
            "locked": False,
            "anchor": None,
        },
        {
            "id": "c2",
            "type": "Paragraph",
            "text": "본문",
            "emphasis": "bold",
            "locked": False,
            "anchor": None,
        },
        {
            "id": "c3",
            "type": "KPI",
            "label": "매출",
            "value": "₩1B",
            "delta": "+10%",
            "delta_direction": "up",
            "description": None,
            "locked": False,
            "anchor": None,
        },
    ]

    doc1 = DocumentSchema.model_validate(payload)
    dumped = doc1.model_dump(mode="json")
    doc2 = DocumentSchema.model_validate(copy.deepcopy(dumped))

    types1 = [c.type for c in doc1.pages[0].components]
    types2 = [c.type for c in doc2.pages[0].components]
    assert types1 == types2 == ["SlideTitle", "Paragraph", "KPI"]
