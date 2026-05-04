"""Phase 4 S1 D1 — DocumentSchema v1.0 Pydantic 검증 자동 테스트.

참조:
- docs/phase1_architecture.md §2, 부록 A (JSON 샘플 3건)
- docs/phase1_database_design.md
- backend/app/modules/documents_v2/schemas.py — Pydantic 정의

테스트 범위:
1. 22 컴포넌트 중 핵심 6종 정상 케이스 (SlideTitle, Heading, Paragraph,
   BulletList, KPI, DataTable)
2. 부록 A 샘플 JSON 3건 (slide_report / weekly_status / minutes)
3. Discriminated Union 거부 케이스 (unknown type, required 누락)
4. 설계 기본값 / 비즈니스 검증 / 22 컴포넌트 전수 확인

절대 import 엄수 (P3), 동기 테스트 (pytest-asyncio 미사용).
"""

from __future__ import annotations

import copy
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.modules.documents_v2.schemas import (
    BulletItem,
    BulletListComponent,
    DataTableComponent,
    DesignTokens,
    DocumentSchema,
    HeadingComponent,
    KPIComponent,
    ParagraphComponent,
    SlideTitleComponent,
)

# ---------------------------------------------------------------------------
# 부록 A 샘플 JSON — placeholder(UUID)를 유효한 값으로 보정
# ---------------------------------------------------------------------------

# 문서 내 샘플은 `"..."`, `"a1b2c3d4-...-0001"` 등 placeholder 를 사용한다.
# 스키마 자체 검증이 목표이므로 구조는 보존하되 UUID 자리만 유효값으로 교체.

_FIXED_DOC_A1 = UUID("7b2a5f3e-1c4d-4b8a-9e7f-0a1b2c3d4e5f")
_FIXED_DOC_A2 = UUID("a1b2c3d4-e5f6-7890-abcd-ef0123456789")
_FIXED_DOC_A3 = UUID("cccccccc-dddd-eeee-ffff-000000000001")
_FIXED_USER_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_FIXED_TEMPLATE_ID = UUID("bbbbbbbb-1111-2222-3333-444444444444")
_FIXED_CHAT_ID = UUID("dddddddd-0000-1111-2222-333333333333")


@pytest.fixture
def sample_a1_slide_report() -> dict:
    """부록 A.1 — Mode A 자유생성 slide_report 3페이지."""
    return {
        "document_id": str(_FIXED_DOC_A1),
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
                "title": None,
                "locked": False,
                "components": [
                    {
                        "id": "c1",
                        "type": "SlideTitle",
                        "locked": False,
                        "anchor": None,
                        "text": "2026 Q1 매출 보고서",
                    },
                    {
                        "id": "c2",
                        "type": "SlideSubtitle",
                        "locked": False,
                        "anchor": None,
                        "text": "IDINO 사업개발팀 · 2026-04-19",
                    },
                ],
                "speaker_notes": "회사 소개와 보고서 범위를 간단히 설명합니다.",
                "page_number_visible": False,
            },
            {
                "id": "p2",
                "page_kind": "slide",
                "layout": "kpi_dashboard",
                "title": "핵심 지표",
                "locked": False,
                "components": [
                    {
                        "id": "c3",
                        "type": "Heading",
                        "locked": False,
                        "anchor": None,
                        "level": 2,
                        "text": "2026 Q1 실적 요약",
                    },
                    {
                        "id": "c4",
                        "type": "KPI",
                        "locked": False,
                        "anchor": None,
                        "label": "총 매출",
                        "value": "₩1.2B",
                        "delta": "+12% YoY",
                        "delta_direction": "up",
                        "description": "전년 동기 대비",
                    },
                    {
                        "id": "c5",
                        "type": "KPI",
                        "locked": False,
                        "anchor": None,
                        "label": "신규 계약",
                        "value": "24건",
                        "delta": "+3건",
                        "delta_direction": "up",
                        "description": None,
                    },
                    {
                        "id": "c6",
                        "type": "KPI",
                        "locked": False,
                        "anchor": None,
                        "label": "이탈률",
                        "value": "2.1%",
                        "delta": "-0.4%p",
                        "delta_direction": "down",
                        "description": "개선",
                    },
                ],
                "speaker_notes": "세 개 KPI 중 이탈률 개선이 가장 주목할 만한 포인트입니다.",
                "page_number_visible": True,
            },
            {
                "id": "p3",
                "page_kind": "slide",
                "layout": "content_body",
                "title": "Q2 실행 계획",
                "locked": False,
                "components": [
                    {
                        "id": "c7",
                        "type": "Heading",
                        "locked": False,
                        "anchor": None,
                        "level": 2,
                        "text": "Q2 실행 계획",
                    },
                    {
                        "id": "c8",
                        "type": "BulletList",
                        "locked": False,
                        "anchor": None,
                        "numbered": True,
                        "items": [
                            {
                                "text": "신규 고객사 파일럿 런칭",
                                "sub_items": ["제조업 3사", "공공 1사"],
                                "emphasis": "bold",
                            },
                            {
                                "text": "파트너십 확대",
                                "sub_items": [],
                                "emphasis": "normal",
                            },
                            {
                                "text": "인력 충원: 개발 2명, 영업 1명",
                                "sub_items": [],
                                "emphasis": "highlight",
                            },
                        ],
                    },
                ],
                "speaker_notes": None,
                "page_number_visible": True,
            },
        ],
        "metadata": {
            "created_at": "2026-04-19T10:00:00Z",
            "updated_at": "2026-04-19T10:00:05Z",
            "generated_by_user_id": str(_FIXED_USER_ID),
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "prompt_tokens": 1280,
            "completion_tokens": 640,
            "source_document_ids": [],
            "source_chat_session_id": None,
            "citations": [],
            "degraded_components": [],
        },
    }


@pytest.fixture
def sample_a2_weekly_status() -> dict:
    """부록 A.2 — Mode B 양식채우기 weekly_status 2페이지 (locked 포함).

    원문은 p2.components 에 빈 BulletList.items=[] 를 포함하지만 스키마는
    `min_length=1` 을 요구하므로 테스트용으로 1개 항목을 채운다. 스키마 결함이
    아닌 문서/스키마 불일치 (완료 보고에 리포트).
    """
    return {
        "document_id": str(_FIXED_DOC_A2),
        "schema_version": "1.0",
        "type": "weekly_status",
        "mode": "template_fill",
        "template_id": str(_FIXED_TEMPLATE_ID),
        "design_tokens": {
            "primary_color": "#0A4FC2",
            "accent_color": "#FF6B35",
            "text_color": "#1F2937",
            "background_color": "#FFFFFF",
            "font_family": "Pretendard",
            "spacing": "compact",
            "brand_preset": "idino_default",
        },
        "pages": [
            {
                "id": "p1",
                "page_kind": "section",
                "layout": "content_body",
                "title": "주간 업무 보고서",
                "locked": True,
                "components": [
                    {
                        "id": "c1",
                        "type": "Heading",
                        "locked": True,
                        "anchor": "title_slot",
                        "level": 1,
                        "text": "{{week}} 주간 업무 보고서",
                    },
                    {
                        "id": "c2",
                        "type": "DataTable",
                        "locked": True,
                        "anchor": "summary_table",
                        "headers": ["구분", "내용"],
                        "rows": [
                            ["작성자", "__AUTO_FILL__"],
                            ["부서", "__AUTO_FILL__"],
                            ["주차", "__AUTO_FILL__"],
                        ],
                        "emphasis_column_index": None,
                        "caption": None,
                    },
                ],
                "speaker_notes": None,
                "page_number_visible": False,
            },
            {
                "id": "p2",
                "page_kind": "section",
                "layout": "content_body",
                "title": "이번 주 실적",
                "locked": False,
                "components": [
                    {
                        "id": "c3",
                        "type": "Heading",
                        "locked": True,
                        "anchor": "achievements_heading",
                        "level": 2,
                        "text": "이번 주 실적",
                    },
                    {
                        "id": "c4",
                        "type": "BulletList",
                        "locked": False,
                        "anchor": "achievements_slot",
                        "numbered": False,
                        "items": [
                            {
                                "text": "플레이스홀더: 사용자가 채울 내용",
                                "sub_items": [],
                                "emphasis": "normal",
                            }
                        ],
                    },
                ],
                "speaker_notes": None,
                "page_number_visible": True,
            },
        ],
        "metadata": {
            "created_at": "2026-04-19T10:00:00Z",
            "updated_at": "2026-04-19T10:00:00Z",
            "generated_by_user_id": str(_FIXED_USER_ID),
            "llm_provider": None,
            "llm_model": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "source_document_ids": [],
            "source_chat_session_id": None,
            "citations": [],
            "degraded_components": [],
        },
    }


@pytest.fixture
def sample_a3_minutes() -> dict:
    """부록 A.3 — minutes 1페이지 (AttendeeList + ActionItemList + Citation)."""
    return {
        "document_id": str(_FIXED_DOC_A3),
        "schema_version": "1.0",
        "type": "minutes",
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
                "page_kind": "section",
                "layout": "content_body",
                "title": "2026-04-18 주간 회의록",
                "locked": False,
                "components": [
                    {
                        "id": "c1",
                        "type": "Heading",
                        "locked": False,
                        "anchor": None,
                        "level": 1,
                        "text": "2026-04-18 주간 회의록",
                    },
                    {
                        "id": "c2",
                        "type": "AttendeeList",
                        "locked": False,
                        "anchor": None,
                        "attendees": [
                            {"name": "변동언", "role": "대표이사", "present": True},
                            {"name": "김용휴", "role": "미래기술연구소장", "present": True},
                            {"name": "이현수", "role": "AI기술팀", "present": False},
                        ],
                    },
                    {
                        "id": "c3",
                        "type": "Heading",
                        "locked": False,
                        "anchor": None,
                        "level": 2,
                        "text": "안건 및 결정사항",
                    },
                    {
                        "id": "c4",
                        "type": "BulletList",
                        "locked": False,
                        "anchor": None,
                        "numbered": True,
                        "items": [
                            {
                                "text": "DocUtil 재설계 Phase 1 착수 승인 [cite: r1]",
                                "sub_items": [],
                                "emphasis": "bold",
                            },
                            {
                                "text": "HWPX 우선 지원 확정 [cite: r2]",
                                "sub_items": [],
                                "emphasis": "normal",
                            },
                        ],
                    },
                    {
                        "id": "c5",
                        "type": "ActionItemList",
                        "locked": False,
                        "anchor": None,
                        "items": [
                            {
                                "text": "DocumentSchema 초안",
                                "owner": "enterprise-architect",
                                "due": "2026-04-22",
                                "status": "in_progress",
                            },
                            {
                                "text": "DB 스키마 변경안",
                                "owner": "database-architect",
                                "due": "2026-04-25",
                                "status": "pending",
                            },
                        ],
                    },
                ],
                "speaker_notes": None,
                "page_number_visible": True,
            }
        ],
        "metadata": {
            "created_at": "2026-04-18T15:30:00Z",
            "updated_at": "2026-04-18T15:45:00Z",
            "generated_by_user_id": str(_FIXED_USER_ID),
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "prompt_tokens": 2040,
            "completion_tokens": 820,
            "source_document_ids": [],
            "source_chat_session_id": str(_FIXED_CHAT_ID),
            "citations": [
                {
                    "id": "r1",
                    "chunk_id": "chunk-001",
                    "document_id": None,
                    "excerpt": "재설계 Phase 1 착수를 승인함",
                },
                {
                    "id": "r2",
                    "chunk_id": "chunk-002",
                    "document_id": None,
                    "excerpt": "HWPX 우선, HWP 생성은 포기",
                },
            ],
            "degraded_components": [],
        },
    }


# ---------------------------------------------------------------------------
# 1) 정상 케이스 — 핵심 컴포넌트 6종
# ---------------------------------------------------------------------------


def test_slide_title_valid_creates_component():
    """SlideTitle — id/text 만으로 생성 성공."""
    c = SlideTitleComponent(id="c1", text="2026 Q1 매출 보고서")
    assert c.type == "SlideTitle"
    assert c.text == "2026 Q1 매출 보고서"
    assert c.locked is False
    assert c.anchor is None


@pytest.mark.parametrize("level", [1, 2, 3])
def test_heading_valid_allows_levels_1_to_3(level: int):
    """Heading — level 1,2,3 허용."""
    c = HeadingComponent(id="c1", text="제목", level=level)
    assert c.level == level
    assert c.type == "Heading"


def test_paragraph_valid_with_text_creates_component():
    """Paragraph — text 필드만으로 생성, emphasis 기본값 확인."""
    c = ParagraphComponent(id="c1", text="본문 문단 내용.")
    assert c.type == "Paragraph"
    assert c.emphasis == "normal"


def test_bullet_list_valid_with_items_creates_component():
    """BulletList — items 배열 최소 1개 허용, sub_items 2레벨 지원."""
    c = BulletListComponent(
        id="c1",
        items=[
            BulletItem(text="첫째", sub_items=["하위1", "하위2"]),
            BulletItem(text="둘째"),
        ],
        numbered=True,
    )
    assert c.type == "BulletList"
    assert len(c.items) == 2
    assert c.items[0].sub_items == ["하위1", "하위2"]
    assert c.numbered is True


def test_kpi_valid_with_label_value_delta_creates_component():
    """KPI — label+value+delta+delta_direction 조합 생성 성공."""
    c = KPIComponent(
        id="c1",
        label="총 매출",
        value="₩1.2B",
        delta="+12% YoY",
        delta_direction="up",
        description="전년 동기 대비",
    )
    assert c.label == "총 매출"
    assert c.value == "₩1.2B"
    assert c.delta_direction == "up"


def test_data_table_valid_with_headers_and_rows_creates_component():
    """DataTable — headers 와 rows 길이 일치 시 생성 성공."""
    c = DataTableComponent(
        id="c1",
        headers=["구분", "내용", "담당"],
        rows=[
            ["작성자", "홍길동", "개발팀"],
            ["부서", "AI기술팀", "연구소"],
        ],
        caption="주간 보고 요약",
    )
    assert len(c.headers) == 3
    assert len(c.rows) == 2
    assert all(len(r) == 3 for r in c.rows)


# ---------------------------------------------------------------------------
# 2) 부록 A 샘플 JSON 3건 — model_validate 성공
# ---------------------------------------------------------------------------


def test_sample_a1_slide_report_validates_successfully(sample_a1_slide_report):
    """부록 A.1 — Mode A 자유생성 slide_report 3페이지 전체 검증."""
    doc = DocumentSchema.model_validate(sample_a1_slide_report)
    assert doc.type == "slide_report"
    assert doc.mode == "free_generation"
    assert doc.template_id is None
    assert len(doc.pages) == 3
    # 2페이지의 KPI 3개 확인
    page2 = doc.pages[1]
    kpis = [c for c in page2.components if c.type == "KPI"]
    assert len(kpis) == 3


def test_sample_a2_weekly_status_validates_and_preserves_locked(
    sample_a2_weekly_status,
):
    """부록 A.2 — Mode B template_fill + locked=True 필드가 보존되는지."""
    doc = DocumentSchema.model_validate(sample_a2_weekly_status)
    assert doc.type == "weekly_status"
    assert doc.mode == "template_fill"
    assert doc.template_id == _FIXED_TEMPLATE_ID

    # p1 은 페이지 자체가 locked=True
    p1 = doc.pages[0]
    assert p1.locked is True
    # p1.c1, p1.c2 도 locked=True 로 보존
    assert all(comp.locked is True for comp in p1.components)
    # p2.c3 는 locked=True, p2.c4 는 locked=False 로 보존
    p2 = doc.pages[1]
    locked_flags = [c.locked for c in p2.components]
    assert locked_flags == [True, False]
    # anchor 도 보존
    assert p1.components[0].anchor == "title_slot"
    assert p1.components[1].anchor == "summary_table"


def test_sample_a3_minutes_validates_with_citations(sample_a3_minutes):
    """부록 A.3 — minutes 1페이지, AttendeeList/ActionItemList/Citation 검증."""
    doc = DocumentSchema.model_validate(sample_a3_minutes)
    assert doc.type == "minutes"
    assert doc.mode == "free_generation"
    assert len(doc.pages) == 1
    assert len(doc.metadata.citations) == 2
    assert doc.metadata.citations[0].id == "r1"
    # 컴포넌트 타입 집합 확인
    comp_types = {c.type for c in doc.pages[0].components}
    assert {"Heading", "AttendeeList", "BulletList", "ActionItemList"}.issubset(comp_types)


# ---------------------------------------------------------------------------
# 3) Discriminated Union — 거부 케이스
# ---------------------------------------------------------------------------


def test_unknown_component_type_raises_validation_error(sample_a1_slide_report):
    """알 수 없는 type 값 → ValidationError."""
    payload = copy.deepcopy(sample_a1_slide_report)
    payload["pages"][0]["components"][0]["type"] = "UnknownWidget"
    with pytest.raises(ValidationError) as exc_info:
        DocumentSchema.model_validate(payload)
    # discriminator 실패 메시지 포함 확인
    msg = str(exc_info.value)
    assert "UnknownWidget" in msg or "discriminator" in msg.lower() or "tag" in msg.lower()


def test_kpi_missing_required_value_raises_validation_error():
    """KPI 의 required 필드(value) 누락 → ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        KPIComponent(id="c1", label="총 매출")  # value 누락
    errors = exc_info.value.errors()
    missing_fields = {e["loc"][-1] for e in errors if e["type"] == "missing"}
    assert "value" in missing_fields


# ---------------------------------------------------------------------------
# 4) 권장 추가 테스트 — design_tokens 기본값 / 비즈니스 검증 / 22 컴포넌트
# ---------------------------------------------------------------------------


def test_design_tokens_apply_defaults_when_omitted():
    """design_tokens 미지정 시 IDINO 기본값이 적용."""
    tokens = DesignTokens()
    assert tokens.primary_color == "#0A4FC2"
    assert tokens.accent_color == "#FF6B35"
    assert tokens.text_color == "#1F2937"
    assert tokens.background_color == "#FFFFFF"
    assert tokens.font_family == "Pretendard"
    assert tokens.spacing == "normal"
    assert tokens.brand_preset == "idino_default"


def test_template_fill_without_template_id_fails_business_validation(
    sample_a2_weekly_status,
):
    """mode='template_fill' 인데 template_id=None → 비즈니스 검증 실패."""
    payload = copy.deepcopy(sample_a2_weekly_status)
    payload["template_id"] = None
    with pytest.raises(ValidationError) as exc_info:
        DocumentSchema.model_validate(payload)
    assert "template_id" in str(exc_info.value)


def test_free_generation_with_template_id_fails_business_validation(
    sample_a1_slide_report,
):
    """대칭 검증: mode='free_generation' 인데 template_id 가 있으면 실패."""
    payload = copy.deepcopy(sample_a1_slide_report)
    payload["template_id"] = str(uuid4())
    with pytest.raises(ValidationError) as exc_info:
        DocumentSchema.model_validate(payload)
    assert "template_id" in str(exc_info.value)


def test_document_schema_exposes_all_22_component_defs():
    """DocumentSchema.model_json_schema() 에 22 컴포넌트 모두 $defs 로 노출."""
    schema = DocumentSchema.model_json_schema()
    defs = schema.get("$defs", {})

    expected_components = {
        "SlideTitleComponent",
        "SlideSubtitleComponent",
        "HeadingComponent",
        "ParagraphComponent",
        "QuoteComponent",
        "CalloutComponent",
        "BulletListComponent",
        "KPIComponent",
        "DataTableComponent",
        "ChartComponent",
        "ImageComponent",
        "TimelineComponent",
        "ImageGridComponent",
        "IconRowComponent",
        "TwoColumnComponent",
        "ThreeColumnComponent",
        "HeroComponent",
        "ComparisonComponent",
        "ExecutiveSummaryComponent",
        "RiskMatrixComponent",
        "ActionItemListComponent",
        "AttendeeListComponent",
    }
    assert len(expected_components) == 22
    missing = expected_components - defs.keys()
    assert not missing, f"$defs 에 누락된 컴포넌트: {missing}"


def test_data_table_non_rectangular_rows_raise_validation_error():
    """DataTable — rows 길이가 headers 와 다르면 검증 실패 (model_validator)."""
    with pytest.raises(ValidationError) as exc_info:
        DataTableComponent(
            id="c1",
            headers=["A", "B", "C"],
            rows=[["1", "2"]],  # 길이 2 → 불일치
        )
    assert "headers" in str(exc_info.value) or "길이" in str(exc_info.value)


def test_bullet_list_empty_items_raises_validation_error():
    """BulletList.items=[] 는 min_length=1 위반 (부록 A.2 원문과 불일치)."""
    with pytest.raises(ValidationError):
        BulletListComponent(id="c1", items=[])
