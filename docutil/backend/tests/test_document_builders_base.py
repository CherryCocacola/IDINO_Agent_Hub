"""Phase 4 S1 D3 — DocumentBuilder ABC + BuilderRegistry 테스트.

검증 범위 (요구 5건 + 추가 엣지):
1. `DocumentBuilder` 가 ABC 이므로 직접 인스턴스화 불가.
2. 가짜 빌더 구현체를 Registry 에 등록 → `get()` 으로 조회 성공.
3. 미등록 target 조회 → `HTTPException(501)` + 한국어 detail.
4. `validate_components()` 가 지원 외 컴포넌트를 탐지 (예: Chart 미지원 빌더).
5. 중복 등록은 덮어쓰기 허용 (경고 로그 + 뒤에 등록된 빌더가 반환).
6. 재귀 컨테이너(TwoColumn) 내부 자식도 `validate_components()` 대상.
7. 잘못된 target/ supported_components 등록 시 `ValueError`.
8. `list_targets()` 는 정렬된 목록을 반환.

참조:
- backend/app/integrations/document_builders/base.py
- docs/phase1_architecture.md §3, §4.1.2
- docs/phase1_decisions.md Q5
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.integrations.document_builders.base import (
    BuilderRegistry,
    DocumentBuilder,
    get_builder,
)
from app.modules.documents_v2.schemas import (
    ChartComponent,
    ChartData,
    ChartSeries,
    DocumentMetadata,
    DocumentSchema,
    Page,
    ParagraphComponent,
    SlideTitleComponent,
    TwoColumnComponent,
)

# ---------------------------------------------------------------------------
# 공용 fixture
# ---------------------------------------------------------------------------

_FIXED_DOC_ID = UUID("7b2a5f3e-1c4d-4b8a-9e7f-0a1b2c3d4e5f")


@pytest.fixture(autouse=True)
def _isolated_registry():
    """각 테스트 사이에 Registry 상태를 리셋 (테스트 격리)."""
    BuilderRegistry.clear()
    yield
    BuilderRegistry.clear()


@pytest.fixture
def simple_schema() -> DocumentSchema:
    """SlideTitle + Paragraph 만 포함한 최소 유효 문서."""
    now = datetime.now(UTC)
    return DocumentSchema(
        document_id=_FIXED_DOC_ID,
        schema_version="1.0",
        type="slide_report",
        mode="free_generation",
        template_id=None,
        pages=[
            Page(
                id="p1",
                page_kind="slide",
                layout="title_slide",
                title="표지",
                components=[
                    SlideTitleComponent(id="c1", text="2026년 1분기 사업 계획"),
                    ParagraphComponent(id="c2", text="요약 단락입니다."),
                ],
            ),
        ],
        metadata=DocumentMetadata(created_at=now, updated_at=now),
    )


@pytest.fixture
def schema_with_chart() -> DocumentSchema:
    """Chart 컴포넌트를 포함 — 가짜 빌더가 미지원으로 표시해야 함."""
    now = datetime.now(UTC)
    return DocumentSchema(
        document_id=_FIXED_DOC_ID,
        schema_version="1.0",
        type="slide_report",
        mode="free_generation",
        pages=[
            Page(
                id="p1",
                page_kind="slide",
                layout="content_body",
                components=[
                    SlideTitleComponent(id="c1", text="매출 추이"),
                    ChartComponent(
                        id="c2",
                        chart_type="bar",
                        title="월별 매출",
                        data=ChartData(
                            labels=["1월", "2월", "3월"],
                            series=[
                                ChartSeries(name="매출", values=[100.0, 120.0, 135.0]),
                            ],
                        ),
                    ),
                ],
            ),
        ],
        metadata=DocumentMetadata(created_at=now, updated_at=now),
    )


@pytest.fixture
def schema_with_nested_twocolumn() -> DocumentSchema:
    """TwoColumn 안에 Chart 를 넣어 재귀 탐색 동작을 확인."""
    now = datetime.now(UTC)
    chart = ChartComponent(
        id="c3",
        chart_type="line",
        title="추세",
        data=ChartData(
            labels=["1월", "2월"],
            series=[ChartSeries(name="KPI", values=[10.0, 20.0])],
        ),
    )
    return DocumentSchema(
        document_id=_FIXED_DOC_ID,
        schema_version="1.0",
        type="slide_report",
        mode="free_generation",
        pages=[
            Page(
                id="p1",
                page_kind="slide",
                layout="two_column",
                components=[
                    TwoColumnComponent(
                        id="c1",
                        left=[ParagraphComponent(id="c2", text="왼쪽 본문")],
                        right=[chart],
                    ),
                ],
            ),
        ],
        metadata=DocumentMetadata(created_at=now, updated_at=now),
    )


# ---------------------------------------------------------------------------
# 가짜 빌더 구현체 (테스트 전용)
# ---------------------------------------------------------------------------


class _FakeHtmlBuilder(DocumentBuilder):
    """모든 컴포넌트를 지원한다고 주장하는 가짜 HTML 빌더."""

    target = "html"
    supported_components = frozenset(
        {
            "SlideTitle",
            "SlideSubtitle",
            "Heading",
            "Paragraph",
            "Quote",
            "Callout",
            "BulletList",
            "KPI",
            "DataTable",
            "Chart",
            "Image",
            "Timeline",
            "ImageGrid",
            "IconRow",
            "TwoColumn",
            "ThreeColumn",
            "Hero",
            "Comparison",
            "ExecutiveSummary",
            "RiskMatrix",
            "ActionItemList",
            "AttendeeList",
        }
    )

    async def build(self, schema: DocumentSchema) -> bytes:
        # 테스트용 최소 구현 — 문서 ID 만 담은 바이트.
        return f'<html data-doc="{schema.document_id}"></html>'.encode()


class _NoChartBuilder(DocumentBuilder):
    """Chart 를 지원하지 않는 가짜 빌더 (degradation 탐지 검증용)."""

    target = "docx"
    supported_components = frozenset(
        {
            "SlideTitle",
            "Heading",
            "Paragraph",
            "BulletList",
            "TwoColumn",
            "ThreeColumn",
        }
    )

    async def build(self, schema: DocumentSchema) -> bytes:
        return b"fake-docx"


class _AlternateHtmlBuilder(DocumentBuilder):
    """중복 등록 덮어쓰기 검증용 — 같은 target='html' 을 가진 다른 구현."""

    target = "html"
    supported_components = frozenset({"SlideTitle", "Paragraph"})

    async def build(self, schema: DocumentSchema) -> bytes:
        return b"alt-html"


# ---------------------------------------------------------------------------
# 테스트 케이스
# ---------------------------------------------------------------------------


def test_document_builder_cannot_be_instantiated_directly():
    """요구 #1 — ABC 는 직접 인스턴스화 불가."""
    with pytest.raises(TypeError) as exc_info:
        DocumentBuilder()  # type: ignore[abstract]
    # 파이썬 기본 메시지에 'abstract' 포함.
    assert "abstract" in str(exc_info.value).lower()


async def test_register_and_get_returns_same_instance(simple_schema):
    """요구 #2 — 가짜 빌더 등록 후 `get()` 으로 동일 인스턴스 조회."""
    builder = _FakeHtmlBuilder()
    BuilderRegistry.register(builder)

    retrieved = BuilderRegistry.get("html")
    assert retrieved is builder

    # 팩토리 함수 경로도 동작.
    assert get_builder("html") is builder

    # 빌더 호출 자체가 정상 동작하는지 smoke test.
    result = await retrieved.build(simple_schema)
    assert isinstance(result, bytes)
    assert str(simple_schema.document_id).encode() in result


def test_get_unregistered_target_raises_korean_http_exception():
    """요구 #3 — 미등록 target 조회 시 HTTPException 한국어 메시지."""
    # 아직 아무것도 등록하지 않은 상태에서 조회.
    with pytest.raises(HTTPException) as exc_info:
        BuilderRegistry.get("pptx")

    exc = exc_info.value
    assert exc.status_code == 501
    # 한국어 키워드 확인.
    assert "pptx" in exc.detail
    assert "등록" in exc.detail  # '등록되지 않았습니다' 포함 확인.


def test_get_invalid_target_raises_http_400():
    """BuildTarget Literal 에 없는 값 조회 시 400."""
    with pytest.raises(HTTPException) as exc_info:
        BuilderRegistry.get("rtf")  # type: ignore[arg-type]
    assert exc_info.value.status_code == 400
    assert "지원하지 않는" in exc_info.value.detail


def test_validate_components_detects_unsupported_type(schema_with_chart):
    """요구 #4 — Chart 를 지원하지 않는 빌더가 Chart 를 탐지."""
    builder = _NoChartBuilder()
    BuilderRegistry.register(builder)

    unsupported = builder.validate_components(schema_with_chart)
    assert unsupported == ["Chart"]

    # 모든 컴포넌트를 지원하는 빌더는 빈 리스트.
    full = _FakeHtmlBuilder()
    assert full.validate_components(schema_with_chart) == []


def test_validate_components_recurses_into_twocolumn(
    schema_with_nested_twocolumn,
):
    """TwoColumn 내부에 있는 Chart 도 탐지되어야 한다."""
    builder = _NoChartBuilder()
    unsupported = builder.validate_components(schema_with_nested_twocolumn)
    # TwoColumn 은 지원, Chart 는 미지원.
    assert "Chart" in unsupported
    assert "TwoColumn" not in unsupported


def test_duplicate_registration_overwrites_with_warning(caplog):
    """요구 #5 — 동일 target 중복 등록 시 덮어쓰기 + WARNING 로그."""
    first = _FakeHtmlBuilder()
    second = _AlternateHtmlBuilder()

    BuilderRegistry.register(first)
    assert BuilderRegistry.get("html") is first

    with caplog.at_level("WARNING"):
        BuilderRegistry.register(second)

    # 두 번째 빌더가 유효한 등록 상태.
    assert BuilderRegistry.get("html") is second
    # 경고 로그에 target 이 포함.
    assert any("html" in rec.message for rec in caplog.records)


def test_list_targets_returns_sorted_registered(simple_schema):
    """`list_targets()` 는 등록된 target 만, 정렬된 리스트로 반환."""
    # 초기에는 빈 리스트.
    assert BuilderRegistry.list_targets() == []

    BuilderRegistry.register(_NoChartBuilder())  # target='docx'
    BuilderRegistry.register(_FakeHtmlBuilder())  # target='html'

    assert BuilderRegistry.list_targets() == ["docx", "html"]


def test_register_rejects_invalid_target():
    """잘못된 target 속성을 가진 빌더는 등록 거부."""

    class _BadTargetBuilder(DocumentBuilder):
        target = "markdown"  # type: ignore[assignment]
        supported_components = frozenset({"Paragraph"})

        async def build(self, schema):
            return b""

    with pytest.raises(ValueError) as exc_info:
        BuilderRegistry.register(_BadTargetBuilder())
    assert "target" in str(exc_info.value)


def test_register_rejects_non_frozenset_supported_components():
    """`supported_components` 는 반드시 frozenset 이어야 한다."""

    class _BadSupportBuilder(DocumentBuilder):
        target = "pdf"
        supported_components = {"Paragraph"}  # type: ignore[assignment]  # set (not frozen)

        async def build(self, schema):
            return b""

    with pytest.raises(ValueError) as exc_info:
        BuilderRegistry.register(_BadSupportBuilder())
    assert "frozenset" in str(exc_info.value)
