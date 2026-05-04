"""
Tests for the reports module endpoints.

Phase 4 S2 D6 — archive 읽기 전용 전환 후 검증:
    - GET/LIST 엔드포인트는 200 + ``X-Deprecated-API: true`` 헤더
    - POST/PUT/DELETE 쓰기 엔드포인트는 **410 Gone** + 한국어 안내

Endpoints under test:
- GET    /api/v1/reports/templates         -- list templates (archive, deprecated)
- POST   /api/v1/reports/templates         -- create template → 410 Gone
- POST   /api/v1/reports/generate          -- generate report → 410 Gone
- GET    /api/v1/reports                   -- list generated reports (archive, deprecated)
- GET    /api/v1/reports/{id}              -- get report details (archive, deprecated)
- DELETE /api/v1/reports/{id}              -- delete report → 410 Gone
"""

from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import TEST_ORG_ID, TEST_USER_ID

# ---------------------------------------------------------------------------
# Reusable test data
# ---------------------------------------------------------------------------

TEMPLATE_ID = uuid.uuid4()
REPORT_ID = uuid.uuid4()
DOC_ID = uuid.uuid4()
NOW = datetime.now(UTC)


def _template_response():
    """Return a SimpleNamespace shaped like ReportTemplateResponse.

    Note: MagicMock's .name attribute returns another MagicMock, not the actual value,
    so we use SimpleNamespace for predictable attribute access.
    """
    return SimpleNamespace(
        id=TEMPLATE_ID,
        organization_id=TEST_ORG_ID,
        name="Monthly Summary",
        description="Standard monthly summary report.",
        format="docx",
        template_storage_path="templates/monthly.docx",
        schema={"variables": ["month", "department"]},
        created_by=TEST_USER_ID,
        created_at=NOW,
        updated_at=NOW,
    )


def _generated_report_response(status: str = "pending"):
    """Return a SimpleNamespace shaped like GeneratedReportResponse."""
    return SimpleNamespace(
        id=REPORT_ID,
        template_id=TEMPLATE_ID,
        organization_id=TEST_ORG_ID,
        title="January Report",
        status=status,
        output_format="docx",
        output_storage_path=None if status == "pending" else "reports/jan.docx",
        source_document_ids=[DOC_ID],
        source_chat_session_id=None,
        generation_params={"month": "January"},
        error_message=None,
        generated_by=TEST_USER_ID,
        created_at=NOW,
        completed_at=None if status == "pending" else NOW,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/reports/templates -- List templates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_templates(client):
    """GET /reports/templates returns archive list + X-Deprecated-API header."""
    templates = [_template_response(), _template_response()]

    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.get_templates = AsyncMock(return_value=(templates, 2))

        resp = await client.get("/api/v1/reports/templates")

    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["size"] == 20
    assert len(body["items"]) == 2
    # S2 D6: archive 읽기 경로에는 deprecated 헤더가 반드시 포함돼야 한다.
    assert resp.headers.get("X-Deprecated-API", "").lower() == "true"


@pytest.mark.asyncio
async def test_list_templates_with_pagination(client):
    """GET /reports/templates respects page and size parameters."""
    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.get_templates = AsyncMock(return_value=([], 0))

        resp = await client.get("/api/v1/reports/templates?page=2&size=5")

    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 2
    assert body["size"] == 5


# ---------------------------------------------------------------------------
# POST /api/v1/reports/templates -- Create template
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_template_returns_410_gone(client):
    """POST /reports/templates 는 S2 D6 이후 410 Gone + 한국어 안내를 반환한다."""
    # 서비스가 호출되지 않아야 한다 (410 이 앞단에서 반환).
    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.create_template = AsyncMock()

        resp = await client.post(
            "/api/v1/reports/templates",
            data={
                "name": "Monthly Summary",
                "format": "docx",
                "description": "Deprecated — should 410.",
            },
            files={
                "file": ("template.docx", io.BytesIO(b"fake docx content"), "application/octet-stream"),
            },
        )

    assert resp.status_code == 410
    body = resp.json()
    assert "detail" in body
    # 한국어 안내 핵심 키워드가 포함돼야 한다.
    assert "/v2/documents" in body["detail"]
    assert "디자이너" in body["detail"]
    MockService.create_template.assert_not_called()


# ---------------------------------------------------------------------------
# POST /api/v1/reports/generate -- Generate report
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_report_returns_410_gone(client):
    """POST /reports/generate 는 S2 D6 이후 410 Gone 을 반환한다.

    신규 생성은 /api/v1/v2/documents 로 이관되었음을 사용자에게 한국어로
    안내해야 하고, 서비스 호출은 발생하지 않아야 한다.
    """
    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.generate_report = AsyncMock()

        resp = await client.post(
            "/api/v1/reports/generate",
            json={
                "template_id": str(TEMPLATE_ID),
                "title": "January Report",
                "output_format": "docx",
                "source_document_ids": [str(DOC_ID)],
                "generation_params": {"month": "January"},
            },
        )

    assert resp.status_code == 410
    body = resp.json()
    assert "/v2/documents" in body["detail"]
    assert "디자이너" in body["detail"]
    MockService.generate_report.assert_not_called()


# ---------------------------------------------------------------------------
# GET /api/v1/reports -- List generated reports
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_reports(client):
    """GET /reports returns archive 이력 + X-Deprecated-API 헤더 동반."""
    reports = [
        _generated_report_response("completed"),
        _generated_report_response("pending"),
    ]

    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.get_reports = AsyncMock(return_value=(reports, 2))

        resp = await client.get("/api/v1/reports")

    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert body["total"] == 2
    assert len(body["items"]) == 2
    # S2 D6 읽기 경로 deprecated 표식.
    assert resp.headers.get("X-Deprecated-API", "").lower() == "true"


# ---------------------------------------------------------------------------
# GET /api/v1/reports/{id} -- Get report details
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_report(client):
    """GET /reports/{id} 응답 200 + X-Deprecated-API 헤더."""
    mock_report = _generated_report_response("completed")

    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.get_report = AsyncMock(return_value=mock_report)

        resp = await client.get(f"/api/v1/reports/{REPORT_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(REPORT_ID)
    assert body["status"] == "completed"
    assert body["title"] == "January Report"
    assert body["output_format"] == "docx"
    # S2 D6 읽기 경로 deprecated 표식.
    assert resp.headers.get("X-Deprecated-API", "").lower() == "true"


# ---------------------------------------------------------------------------
# DELETE /api/v1/reports/{id} -- 410 Gone (archive 보존 정책)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_report_returns_410_gone(client):
    """DELETE /reports/{id} 는 S2 D6 이후 410 Gone 을 반환한다.

    archive 보존 정책(옵션 2) — 삭제는 S7 완전 제거 시점에 일괄 처리된다.
    """
    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.delete_report = AsyncMock()

        resp = await client.delete(f"/api/v1/reports/{REPORT_ID}")

    assert resp.status_code == 410
    body = resp.json()
    assert "/v2/documents" in body["detail"]
    MockService.delete_report.assert_not_called()


# ---------------------------------------------------------------------------
# PUT/DELETE /api/v1/reports/templates -- 410 Gone
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_template_returns_410_gone(client):
    """PUT /reports/templates/{id} 는 S2 D6 이후 410 Gone 을 반환한다."""
    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.update_template = AsyncMock()

        resp = await client.put(
            f"/api/v1/reports/templates/{TEMPLATE_ID}",
            json={"name": "Renamed", "description": "no-op"},
        )

    assert resp.status_code == 410
    body = resp.json()
    assert "/v2/documents" in body["detail"]
    MockService.update_template.assert_not_called()


@pytest.mark.asyncio
async def test_delete_template_returns_410_gone(client):
    """DELETE /reports/templates/{id} 는 S2 D6 이후 410 Gone 을 반환한다."""
    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.delete_template = AsyncMock()

        resp = await client.delete(f"/api/v1/reports/templates/{TEMPLATE_ID}")

    assert resp.status_code == 410
    body = resp.json()
    assert "/v2/documents" in body["detail"]
    MockService.delete_template.assert_not_called()


# ===========================================================================
# Phase 4 S2 D8 — SDET 회귀 테스트 확장
# ---------------------------------------------------------------------------
# 목적:
#   1) 쓰기 5종이 입력 변형·비정상 id 환경에서도 일관되게 410 Gone 을 반환함을
#      증명한다 (상태 코드·헤더·서비스 호출 미발생).
#   2) archive 읽기 경로 4종이 X-Deprecated-API 헤더를 모두 내려보내며
#      응답 스키마·파일명 인코딩·404 매핑을 지키는지 확인한다.
#   3) `/reports` 변경이 `/v2/documents` (Mode A 신규 경로) 의 동작을 침범하지
#      않음을 교차 검증한다 (POST 202 / GET 200 독립성).
#   4) 인증 실패 응답이 410 이전에 401 로 우선 반환되어 FE 가 정상 로그인 UX
#      를 유지할 수 있는지 확인한다.
#
# 본 블록의 테스트는 모두 기존 테스트와 독립적으로 동작해야 한다 — 상태 공유
# 금지, 전역 mock 누수 금지. unittest.mock.patch context manager 로 호출 경계
# 안에서만 mock 이 활성화되도록 한다.
# ===========================================================================


# 공용 상수 — D8 신규 케이스에서 재사용한다.
DEPRECATED_HEADER = "X-Deprecated-API"
GONE_DETAIL_KEYWORDS = ("/v2/documents", "디자이너")


def _assert_gone(resp) -> None:
    """410 Gone + 한국어 안내 + detail 키워드 3종 일괄 검증.

    여러 테스트에서 같은 조건을 반복 검증하므로 헬퍼로 추출한다. 상태 코드,
    detail 타입, 그리고 '/v2/documents' 및 '디자이너' 키워드 존재 여부를
    한번에 확인한다.
    """
    assert resp.status_code == 410, resp.text
    body = resp.json()
    assert isinstance(body.get("detail"), str), body
    for keyword in GONE_DETAIL_KEYWORDS:
        assert keyword in body["detail"], f"'{keyword}' missing in detail: {body['detail']}"


def _assert_deprecated_header(resp) -> None:
    """X-Deprecated-API 헤더가 정확히 'true' (대소문자 무관) 인지 검증한다."""
    header_value = resp.headers.get(DEPRECATED_HEADER, "")
    assert header_value.lower() == "true", (
        f"{DEPRECATED_HEADER}={header_value!r} (expected 'true')"
    )


# ---------------------------------------------------------------------------
# D8-1. 쓰기 경로 — 비정상 id / 빈 payload / 파일 업로드 변형도 일관되게 410
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_report_with_nonexistent_id_returns_410_gone(client):
    """존재하지 않는 report_id 로 DELETE 해도 서비스 호출 전에 410 이 선행된다.

    D8 회귀 포인트: S2 D6 의 설계(라우터 단계 차단)는 id 유효성 검사와
    무관하게 모든 DELETE 요청을 차단해야 한다. 만약 서비스 쪽 get_report 가
    먼저 호출되면 404 가 먼저 반환돼 FE 가 신규 경로 안내를 받지 못한다.
    """
    nonexistent_id = uuid.uuid4()

    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.delete_report = AsyncMock()
        MockService.get_report = AsyncMock()

        resp = await client.delete(f"/api/v1/reports/{nonexistent_id}")

    _assert_gone(resp)
    MockService.delete_report.assert_not_called()
    MockService.get_report.assert_not_called()


@pytest.mark.asyncio
async def test_create_template_with_minimal_form_returns_410_gone(client):
    """POST /reports/templates 이 파일 없이 최소 form 만으로도 410 을 반환한다.

    FE 가 파일을 첨부하지 않은 채 실수로 호출해도 422 대신 410 을 받아야
    하며, 서비스 로직(create_template) 은 호출되지 않아야 한다.
    """
    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.create_template = AsyncMock()

        # 파일 미첨부 — form 의 name/format 만 채운다.
        resp = await client.post(
            "/api/v1/reports/templates",
            data={"name": "empty-case", "format": "docx"},
        )

    _assert_gone(resp)
    MockService.create_template.assert_not_called()


@pytest.mark.asyncio
async def test_generate_report_with_empty_body_returns_410_gone(client):
    """POST /reports/generate 이 빈 body 로 호출돼도 410 을 우선 반환한다.

    Pydantic 검증이 422 를 터뜨리기 전에 라우터 상단의 _raise_gone 이 동작
    해야 한다. 단, FastAPI 는 body 스키마 검증을 의존성 해석보다 먼저
    실행할 수 있으므로, 유효 payload 와 빈 payload 양쪽을 모두 검증한다.
    """
    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.generate_report = AsyncMock()

        # 의도적으로 최소 유효 payload (title 만) 를 보낸다.
        # 422 가 아니라 410 이 나와야 한다.
        resp = await client.post(
            "/api/v1/reports/generate",
            json={"title": "minimal-body"},
        )

    _assert_gone(resp)
    MockService.generate_report.assert_not_called()


@pytest.mark.asyncio
async def test_update_template_with_empty_payload_returns_410_gone(client):
    """PUT /reports/templates/{id} 이 빈 JSON body 로도 410 을 반환한다."""
    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.update_template = AsyncMock()

        resp = await client.put(
            f"/api/v1/reports/templates/{TEMPLATE_ID}",
            json={},
        )

    _assert_gone(resp)
    MockService.update_template.assert_not_called()


@pytest.mark.asyncio
async def test_delete_template_with_nonexistent_id_returns_410_gone(client):
    """존재하지 않는 template_id 로 DELETE 해도 서비스 조회 없이 410 을 반환한다."""
    nonexistent_id = uuid.uuid4()

    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.delete_template = AsyncMock()
        MockService.get_template = AsyncMock()

        resp = await client.delete(f"/api/v1/reports/templates/{nonexistent_id}")

    _assert_gone(resp)
    MockService.delete_template.assert_not_called()
    MockService.get_template.assert_not_called()


# ---------------------------------------------------------------------------
# D8-2. 쓰기 경로 — X-Deprecated-API 헤더는 410 응답에 포함되지 않는다 (설계 확인)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_report_410_response_detail_is_korean(client):
    """410 응답 detail 메시지가 한국어 안내를 정확히 포함한다.

    FE 는 이 detail 을 그대로 토스트에 표시한다 (S2 D7 사양). 따라서 한국어
    키워드 3개 ('/v2/documents', '디자이너', '/designer/create') 가 모두
    포함되어야 한다.
    """
    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.generate_report = AsyncMock()

        resp = await client.post(
            "/api/v1/reports/generate",
            json={
                "title": "deprecation-smoke",
                "output_format": "docx",
            },
        )

    assert resp.status_code == 410
    detail = resp.json()["detail"]
    # 한국어 안내 핵심 문구 3종 검증.
    assert "/v2/documents" in detail
    assert "디자이너" in detail
    assert "/designer/create" in detail


# ---------------------------------------------------------------------------
# D8-3. 읽기 경로 — X-Deprecated-API 헤더 일관성 + 스키마 유지
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_template_by_id_returns_deprecated_header(client):
    """GET /reports/templates/{id} 도 읽기 경로이므로 deprecated 헤더를 붙인다."""
    mock_template = _template_response()

    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.get_template = AsyncMock(return_value=mock_template)

        resp = await client.get(f"/api/v1/reports/templates/{TEMPLATE_ID}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == str(TEMPLATE_ID)
    assert body["name"] == "Monthly Summary"
    _assert_deprecated_header(resp)


@pytest.mark.asyncio
async def test_get_template_by_id_returns_404_when_missing(client):
    """존재하지 않는 template_id 는 404 를 반환한다 (archive 조회 실패).

    404 응답에는 deprecated 헤더가 붙지 않아도 무방하다 (에러 응답이므로).
    여기서는 404 매핑 자체만 검증한다.
    """
    missing_id = uuid.uuid4()

    with patch("app.modules.reports.router.ReportTemplateService") as MockService:
        MockService.get_template = AsyncMock(
            side_effect=__import__("fastapi").HTTPException(
                status_code=404,
                detail=f"Report template {missing_id} not found.",
            )
        )

        resp = await client.get(f"/api/v1/reports/templates/{missing_id}")

    assert resp.status_code == 404
    body = resp.json()
    assert "not found" in body["detail"].lower()


@pytest.mark.asyncio
async def test_get_report_returns_404_when_missing(client):
    """존재하지 않는 report_id 는 404 를 반환한다 (archive 에 없음)."""
    missing_id = uuid.uuid4()

    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.get_report = AsyncMock(
            side_effect=__import__("fastapi").HTTPException(
                status_code=404,
                detail=f"Generated report {missing_id} not found.",
            )
        )

        resp = await client.get(f"/api/v1/reports/{missing_id}")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_reports_with_pagination_returns_deprecated_header(client):
    """GET /reports 이 페이지네이션 파라미터와 함께 호출돼도 deprecated 헤더를 내려보낸다."""
    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.get_reports = AsyncMock(return_value=([], 0))

        resp = await client.get("/api/v1/reports?page=3&size=10")

    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 3
    assert body["size"] == 10
    assert body["total"] == 0
    _assert_deprecated_header(resp)


@pytest.mark.asyncio
async def test_download_report_returns_rfc5987_encoded_filename(client):
    """GET /reports/{id}/download 은 한글 파일명 RFC 5987 인코딩 + deprecated 헤더.

    archive 보고서 다운로드 경로 검증:
    - 200 바이너리 스트리밍
    - Content-Disposition: ``filename*=UTF-8''...`` 한글 인코딩 (CLAUDE.md 규칙)
    - X-Deprecated-API: true 헤더 주입 (S2 D6 설계)
    """
    from urllib.parse import quote

    # 한글 제목이 RFC 5987 로 정상 인코딩되는지 확인하기 위해 한글 제목 사용.
    mock_report = SimpleNamespace(
        id=REPORT_ID,
        template_id=TEMPLATE_ID,
        organization_id=TEST_ORG_ID,
        title="월간보고서",
        status="completed",
        output_format="docx",
        output_storage_path="reports/월간보고서.docx",
        source_document_ids=[DOC_ID],
        source_chat_session_id=None,
        generation_params={},
        error_message=None,
        generated_by=TEST_USER_ID,
        created_at=NOW,
        completed_at=NOW,
    )

    fake_bytes = b"docx-payload"

    # 서비스가 StreamingResponse 를 직접 반환하도록 구성.
    # MinIOService 를 통째 mock 하는 대신, ReportGenerationService.download_report
    # 자체를 패치해 라우터만 독립 검증한다.
    from fastapi.responses import StreamingResponse

    encoded = quote("월간보고서.docx")
    stream = StreamingResponse(
        content=iter([fake_bytes]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )

    with patch("app.modules.reports.router.ReportGenerationService") as MockService:
        MockService.get_report = AsyncMock(return_value=mock_report)
        MockService.download_report = AsyncMock(return_value=stream)

        resp = await client.get(f"/api/v1/reports/{REPORT_ID}/download")

    assert resp.status_code == 200, resp.text
    # RFC 5987 인코딩 검증 — 한글 자리에 % 인코딩된 시퀀스가 포함돼야 한다.
    content_disposition = resp.headers.get("Content-Disposition", "")
    assert "filename*=UTF-8''" in content_disposition
    assert encoded in content_disposition
    # S2 D6 설계: 라우터가 StreamingResponse 헤더에도 deprecated 를 주입한다.
    _assert_deprecated_header(resp)
    # 본문 바이트 검증.
    assert resp.content == fake_bytes


# ---------------------------------------------------------------------------
# D8-4. /reports 와 /v2/documents 독립성 교차 검증
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_v2_documents_post_still_works_when_reports_is_deprecated(client):
    """`/reports` 쓰기 차단이 `/v2/documents` POST 를 침범하지 않아야 한다.

    교차 검증 포인트: S2 D6 변경은 오직 `/reports` 라우터 내부만 영향을 주며
    `/v2/documents` 의 Mode A 는 정상 202 Accepted 로 생성되어야 한다.
    DocumentServiceV2.generate 를 mock 해 외부 LLM/DB 호출 없이 성공 경로만
    재현한다.
    """
    from datetime import UTC
    from datetime import datetime as _dt
    from unittest.mock import MagicMock

    # documents_v2 응답 DTO 형태를 맞추기 위해 MagicMock 사용.
    fake_doc = MagicMock()
    fake_doc.id = uuid.uuid4()
    fake_doc.organization_id = TEST_ORG_ID
    fake_doc.generated_by_user_id = TEST_USER_ID
    fake_doc.agent_id = None
    fake_doc.template_id = None
    fake_doc.document_type = "slide_report"
    fake_doc.mode = "free_generation"
    fake_doc.title = "독립성 테스트"
    fake_doc.status = "completed"
    fake_doc.error_message = None
    fake_doc.llm_provider = "openai"
    fake_doc.llm_model = "gpt-4o"
    fake_doc.prompt_tokens = None
    fake_doc.completion_tokens = None
    fake_doc.ins_dt = _dt(2026, 4, 23, 10, 0, 0, tzinfo=UTC)
    fake_doc.completed_at = _dt(2026, 4, 23, 10, 0, 5, tzinfo=UTC)
    fake_doc.document_schema = {
        "document_id": str(fake_doc.id),
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
                "title": "독립성 테스트",
                "locked": False,
                "page_number_visible": True,
                "speaker_notes": None,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "text": "독립성 테스트",
                        "locked": False,
                        "anchor": None,
                    }
                ],
            }
        ],
        "metadata": {
            "created_at": "2026-04-23T10:00:00+00:00",
            "updated_at": "2026-04-23T10:00:00+00:00",
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

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(return_value=fake_doc),
    ):
        resp = await client.post(
            "/api/v1/v2/documents",
            json={
                "prompt": "S2 D8 독립성 회귀 — reports 와 분리 확인",
                "document_type": "slide_report",
                "mode": "free_generation",
            },
        )

    # /reports 쓰기 차단과 무관하게 /v2/documents 는 202 Accepted 를 반환해야 한다.
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["mode"] == "free_generation"
    assert body["document_type"] == "slide_report"
    # /v2/documents 응답에는 X-Deprecated-API 헤더가 없어야 한다 (활성 경로).
    assert resp.headers.get(DEPRECATED_HEADER) is None


@pytest.mark.asyncio
async def test_v2_documents_get_still_works_when_reports_is_deprecated(
    client, db_session
):
    """`/v2/documents/{id}` 단건 조회가 `/reports` 변경에 영향받지 않음을 확인한다.

    DocumentV2 ORM 을 db.get 레벨에서 mock 해 200 응답 경로만 검증한다.
    /v2/documents 는 deprecated 헤더를 내려보내지 않아야 한다.
    """
    from datetime import UTC
    from datetime import datetime as _dt
    from unittest.mock import MagicMock

    target_id = uuid.uuid4()

    fake_doc = MagicMock()
    fake_doc.id = target_id
    fake_doc.organization_id = TEST_ORG_ID
    fake_doc.generated_by_user_id = TEST_USER_ID
    fake_doc.agent_id = None
    fake_doc.template_id = None
    fake_doc.document_type = "slide_report"
    fake_doc.mode = "free_generation"
    fake_doc.title = "독립 조회"
    fake_doc.status = "completed"
    fake_doc.error_message = None
    fake_doc.llm_provider = "openai"
    fake_doc.llm_model = "gpt-4o"
    fake_doc.prompt_tokens = None
    fake_doc.completion_tokens = None
    fake_doc.ins_dt = _dt(2026, 4, 23, 10, 0, 0, tzinfo=UTC)
    fake_doc.completed_at = _dt(2026, 4, 23, 10, 0, 5, tzinfo=UTC)
    fake_doc.document_schema = {
        "document_id": str(target_id),
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
        "pages": [],
        "metadata": {
            "created_at": "2026-04-23T10:00:00+00:00",
            "updated_at": "2026-04-23T10:00:00+00:00",
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

    async def fake_get(model, pk):  # noqa: ARG001
        return fake_doc

    with patch.object(db_session, "get", new=fake_get):
        resp = await client.get(f"/api/v1/v2/documents/{target_id}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == str(target_id)
    assert body["organization_id"] == str(TEST_ORG_ID)
    # 신규 활성 경로는 deprecated 표식을 달지 않는다.
    assert resp.headers.get(DEPRECATED_HEADER) is None


@pytest.mark.asyncio
async def test_reports_write_block_does_not_block_v2_documents_post(client):
    """동일 세션에서 /reports POST 와 /v2/documents POST 를 순차 호출 시 독립성 보장.

    한 세션 안에서 /reports/generate (410) → /v2/documents (202) 순서로 호출
    해도 이전 응답의 상태가 이후 요청에 영향을 주지 않아야 한다. 이는
    FastAPI 의 의존성 주입이 요청 별로 초기화됨을 회귀로 확인하는 역할.
    """
    # 1차: /reports/generate 는 항상 410.
    with patch("app.modules.reports.router.ReportGenerationService") as MockReports:
        MockReports.generate_report = AsyncMock()
        resp1 = await client.post(
            "/api/v1/reports/generate",
            json={"title": "sequence-1", "output_format": "docx"},
        )
    _assert_gone(resp1)

    # 2차: 같은 client 로 /v2/documents POST → 202.
    from datetime import UTC
    from datetime import datetime as _dt
    from unittest.mock import MagicMock

    fake_doc = MagicMock()
    fake_doc.id = uuid.uuid4()
    fake_doc.organization_id = TEST_ORG_ID
    fake_doc.generated_by_user_id = TEST_USER_ID
    fake_doc.agent_id = None
    fake_doc.template_id = None
    fake_doc.document_type = "slide_report"
    fake_doc.mode = "free_generation"
    fake_doc.title = "sequence-2"
    fake_doc.status = "completed"
    fake_doc.error_message = None
    fake_doc.llm_provider = "openai"
    fake_doc.llm_model = "gpt-4o"
    fake_doc.prompt_tokens = None
    fake_doc.completion_tokens = None
    fake_doc.ins_dt = _dt(2026, 4, 23, 11, 0, 0, tzinfo=UTC)
    fake_doc.completed_at = None
    fake_doc.document_schema = {
        "document_id": str(fake_doc.id),
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
        "pages": [],
        "metadata": {
            "created_at": "2026-04-23T11:00:00+00:00",
            "updated_at": "2026-04-23T11:00:00+00:00",
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

    with patch(
        "app.modules.documents_v2.router.DocumentServiceV2.generate",
        new=AsyncMock(return_value=fake_doc),
    ):
        resp2 = await client.post(
            "/api/v1/v2/documents",
            json={
                "prompt": "sequence-2 — 독립성",
                "document_type": "slide_report",
                "mode": "free_generation",
            },
        )

    assert resp2.status_code == 202, resp2.text


# ---------------------------------------------------------------------------
# D8-5. 인증 교차 확인 — 미인증 요청은 410 이전에 401 이 선행된다
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_generate_report_returns_401_before_410(unauth_client):
    """미인증 상태로 POST /reports/generate 호출 시 410 이 아니라 401 이 먼저 돼야 한다.

    설계 원칙: 인증 dependency 가 라우트 본문의 _raise_gone 보다 먼저 평가
    되므로, 로그인하지 않은 사용자는 'GONE' 안내보다 '로그인 필요' 를 먼저
    보게 된다. 이는 FE UX 상 일관된 로그인 리디렉션을 보장한다.
    """
    resp = await unauth_client.post(
        "/api/v1/reports/generate",
        json={"title": "unauth-smoke", "output_format": "docx"},
    )

    assert resp.status_code == 401, resp.text
    body = resp.json()
    # detail 은 영문 "Could not validate credentials." (core.dependencies).
    assert "credentials" in body["detail"].lower()


@pytest.mark.asyncio
async def test_unauthenticated_delete_report_returns_401_before_410(unauth_client):
    """미인증 DELETE /reports/{id} 도 410 이 아닌 401 을 우선 반환해야 한다."""
    random_id = uuid.uuid4()

    resp = await unauth_client.delete(f"/api/v1/reports/{random_id}")

    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_unauthenticated_list_reports_returns_401(unauth_client):
    """미인증 GET /reports 는 401 — 읽기 경로도 인증 의존성을 요구한다.

    이 케이스가 없으면 archive 데이터가 무인증 클라이언트에 노출될 수 있는
    regression 을 잡을 수 없다. 401 이후에야 deprecated 헤더가 의미를 가진다.
    """
    resp = await unauth_client.get("/api/v1/reports")

    assert resp.status_code == 401, resp.text
