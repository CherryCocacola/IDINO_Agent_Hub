"""Phase 4 S1 D4 — HtmlRenderer 테스트.

요구 8건 + 엣지 검증:
1. Registry 에 HtmlRenderer 등록 → `get_builder("html")` 조회 성공.
2. `build()` 가 bytes 반환 + utf-8 디코드 성공.
3. 결과가 `<!doctype html>` 로 시작.
4. 6 종 MVP 컴포넌트 각각 data-component-type="{Type}" 존재.
5. XSS 방어 — `<script>` 삽입 text 가 escape 되어 `&lt;script&gt;` 출력.
6. 디자인 토큰 — `--doc-primary` 변수가 head style 블록에 포함.
7. 미지원 Chart 컴포넌트 포함 시 placeholder 렌더 + 빌드 성공.
8. 빈 pages (min_length=1 로 불가) 대체: 지원 컴포넌트만 있는 단일 페이지 →
   placeholder 0 개 보장 (부정 테스트로 보완).

참조:
- backend/app/integrations/document_builders/html/
- docs/phase3_execution_roadmap.md §2.1 S1 D4
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.integrations.document_builders.base import BuilderRegistry, get_builder
from app.integrations.document_builders.html import HtmlRenderer, register_html_renderer
from app.modules.documents_v2.schemas import (
    BulletItem,
    BulletListComponent,
    CalloutComponent,
    ChartComponent,
    ChartData,
    ChartSeries,
    DataTableComponent,
    DesignTokens,
    DocumentMetadata,
    DocumentSchema,
    HeadingComponent,
    ImageComponent,
    ImageGridComponent,
    ImageGridItem,
    KPIComponent,
    Page,
    ParagraphComponent,
    SlideTitleComponent,
)

_FIXED_DOC_ID = UUID("7b2a5f3e-1c4d-4b8a-9e7f-0a1b2c3d4e5f")


# ---------------------------------------------------------------------------
# 공용 fixture
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_registry():
    """각 테스트 간 Registry 격리 — clear → 다시 HtmlRenderer 등록."""
    BuilderRegistry.clear()
    register_html_renderer()
    yield
    BuilderRegistry.clear()


def _make_metadata() -> DocumentMetadata:
    now = datetime.now(UTC)
    return DocumentMetadata(created_at=now, updated_at=now)


@pytest.fixture
def full_mvp_schema() -> DocumentSchema:
    """6 MVP 컴포넌트 전부를 한 페이지에 담은 문서."""
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
                    SlideTitleComponent(id="c1", text="2026 1분기 사업계획"),
                    HeadingComponent(id="c2", text="핵심 성과", level=2),
                    ParagraphComponent(
                        id="c3",
                        text="작년 대비 매출 30% 성장을 달성했습니다.",
                        emphasis="bold",
                    ),
                    BulletListComponent(
                        id="c4",
                        items=[
                            BulletItem(
                                text="신규 고객 확보",
                                sub_items=["대기업 3사", "중견기업 7사"],
                                emphasis="highlight",
                            ),
                            BulletItem(text="기존 고객 유지율 95%"),
                        ],
                        numbered=False,
                    ),
                    KPIComponent(
                        id="c5",
                        label="분기 매출",
                        value="₩12.5B",
                        delta="+30%",
                        delta_direction="up",
                        description="전년 동기 대비",
                    ),
                    DataTableComponent(
                        id="c6",
                        headers=["월", "매출", "성장률"],
                        rows=[
                            ["1월", "3.8B", "+25%"],
                            ["2월", "4.2B", "+32%"],
                            ["3월", "4.5B", "+33%"],
                        ],
                        emphasis_column_index=2,
                        caption="월별 매출 추이",
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )


@pytest.fixture
def xss_schema() -> DocumentSchema:
    """악성 `<script>` 텍스트 포함 문서 — XSS 이스케이프 검증용."""
    return DocumentSchema(
        document_id=_FIXED_DOC_ID,
        schema_version="1.0",
        type="slide_report",
        mode="free_generation",
        pages=[
            Page(
                id="p1",
                page_kind="slide",
                layout="title_slide",
                components=[
                    SlideTitleComponent(
                        id="c1",
                        text='<script>alert("xss")</script>',
                    ),
                    ParagraphComponent(
                        id="c2",
                        text='<img src=x onerror="alert(1)">',
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )


@pytest.fixture
def schema_with_unsupported() -> DocumentSchema:
    """미지원 Callout 포함 — placeholder degradation 검증용.

    S3 D2 에서 Chart 가 지원되면서 미지원 역할을 Callout 이 이어받는다.
    Callout 은 S3 후속에서 HTML 지원 예정.
    """
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
                    SlideTitleComponent(id="c1", text="공지"),
                    CalloutComponent(
                        id="c2",
                        text="S3 후속에서 HTML 네이티브 지원 예정.",
                        variant="info",
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )


@pytest.fixture
def custom_tokens_schema() -> DocumentSchema:
    """custom 디자인 토큰 — 주입 검증용."""
    return DocumentSchema(
        document_id=_FIXED_DOC_ID,
        schema_version="1.0",
        type="slide_report",
        mode="free_generation",
        design_tokens=DesignTokens(
            primary_color="#123456",
            accent_color="#AABBCC",
            font_family="NotoSansKR",
            spacing="compact",
            brand_preset="custom",
        ),
        pages=[
            Page(
                id="p1",
                page_kind="slide",
                layout="title_slide",
                components=[SlideTitleComponent(id="c1", text="커스텀 토큰 문서")],
            ),
        ],
        metadata=_make_metadata(),
    )


# ---------------------------------------------------------------------------
# 요구 테스트 8건
# ---------------------------------------------------------------------------


def test_html_renderer_registered_in_registry():
    """#1 — Registry 자동 등록 확인.

    S3 D2 업데이트: Image / ImageGrid / Chart 추가 (6 → 9 종).
    """
    builder = get_builder("html")
    assert isinstance(builder, HtmlRenderer)
    assert builder.target == "html"
    # S3 D2 기준 — 9 종 지원.
    assert builder.supported_components == frozenset(
        {
            "SlideTitle",
            "Heading",
            "Paragraph",
            "BulletList",
            "KPI",
            "DataTable",
            "Image",
            "ImageGrid",
            "Chart",
        }
    )


async def test_build_returns_utf8_bytes(full_mvp_schema):
    """#2 — build() 가 bytes 반환, utf-8 디코드 성공."""
    renderer = get_builder("html")
    result = await renderer.build(full_mvp_schema)
    assert isinstance(result, bytes)
    decoded = result.decode("utf-8")
    assert len(decoded) > 0
    # 한글 문자열이 깨지지 않고 포함.
    assert "2026 1분기 사업계획" in decoded


async def test_build_output_starts_with_doctype(full_mvp_schema):
    """#3 — 반환 HTML 이 `<!doctype html>` 로 시작."""
    renderer = get_builder("html")
    result = (await renderer.build(full_mvp_schema)).decode("utf-8")
    assert result.startswith("<!doctype html>")


async def test_all_six_mvp_components_rendered(full_mvp_schema):
    """#4 — 6 컴포넌트 각각 data-component-type 속성 존재."""
    renderer = get_builder("html")
    result = (await renderer.build(full_mvp_schema)).decode("utf-8")
    for comp_type in ("SlideTitle", "Heading", "Paragraph", "BulletList", "KPI", "DataTable"):
        assert f'data-component-type="{comp_type}"' in result, f"'{comp_type}' 컴포넌트가 렌더되지 않았습니다."
    # placeholder 가 *엘리먼트로* 들어있지 않아야 한다.
    # (클래스명 자체는 BASE_STYLE 의 CSS 규칙에 등장하므로 단순 substring 검사는
    #  false-positive. class="..." 적용 여부로 판정.)
    assert 'class="doc-component doc-component-placeholder"' not in result


async def test_xss_protection_escapes_script_tags(xss_schema):
    """#5 — `<script>` 및 HTML 속성 주입 시도가 이스케이프되어 출력."""
    renderer = get_builder("html")
    result = (await renderer.build(xss_schema)).decode("utf-8")

    # 원형 `<script>` 는 본문 삽입 영역에 존재하면 안 된다.
    # (Body 내부의 `</h1>` 앞뒤로 날것의 `<script` 가 있으면 XSS 실행.)
    assert "<script>alert" not in result
    assert 'onerror="alert' not in result

    # 이스케이프된 형태는 반드시 존재.
    assert "&lt;script&gt;" in result
    assert "&lt;/script&gt;" in result
    # `<img` 이스케이프 검증 — `&lt;img` 형태로 존재.
    assert "&lt;img src=x" in result


async def test_design_tokens_injected_into_head_style(full_mvp_schema):
    """#6 — design_tokens 가 `<head>` `<style>` 블록에 `--doc-*` 로 주입."""
    renderer = get_builder("html")
    result = (await renderer.build(full_mvp_schema)).decode("utf-8")

    # head 안에 style 블록이 2 개(기본 + 오버라이드). 오버라이드 식별자.
    assert "--doc-primary" in result
    assert "--doc-accent" in result
    assert "--doc-text" in result
    assert "--doc-font-family" in result
    # 기본 IDINO primary 값이 기본 스타일에 존재.
    assert "#0a4fc2" in result


async def test_unsupported_component_falls_back_to_placeholder(schema_with_unsupported, caplog):
    """#7 — 미지원 Callout 은 placeholder 로 대체, 빌드 성공 + WARNING 로그.

    S3 D2 기준 — Chart 는 native placeholder 로 승격되었으므로 미지원 역할을
    Callout 이 대체한다.
    """
    renderer = get_builder("html")
    with caplog.at_level("WARNING"):
        result = (await renderer.build(schema_with_unsupported)).decode("utf-8")

    # SlideTitle 은 정상 렌더.
    assert 'data-component-type="SlideTitle"' in result
    # Callout 은 placeholder 로 대체 — class 적용 여부로 정확히 판정.
    assert 'class="doc-component doc-component-placeholder"' in result
    assert 'data-component-type="Callout"' in result
    # 사용자 메시지 포함.
    assert "Callout" in result
    # WARNING 로그 확인.
    assert any("Callout" in rec.message for rec in caplog.records)
    # 빌드는 예외 없이 완료되고 doctype 로 시작.
    assert result.startswith("<!doctype html>")


async def test_only_supported_components_yields_no_placeholder(full_mvp_schema):
    """#8 — 6 MVP 만으로 구성된 문서는 placeholder 가 전혀 포함되지 않는다.

    Pydantic pages min_length=1 제약으로 '완전히 빈 pages' 는 만들 수 없기에,
    '지원 컴포넌트만 존재 → degraded_components 없음' 을 부정 경로로 대체.
    """
    renderer = get_builder("html")
    result = (await renderer.build(full_mvp_schema)).decode("utf-8")
    # placeholder 가 *엘리먼트로* 적용된 흔적이 없어야 한다 (CSS 규칙 정의는 허용).
    assert 'class="doc-component doc-component-placeholder"' not in result
    # doc-root 래퍼는 정확히 한 번.
    assert result.count('class="doc-root') == 1
    # 페이지는 정확히 한 개.
    assert result.count('class="doc-page"') == 1


# ---------------------------------------------------------------------------
# 추가 엣지 검증
# ---------------------------------------------------------------------------


async def test_custom_design_tokens_override_injected(custom_tokens_schema):
    """custom brand_preset + 임의 hex → 오버라이드 CSS 에 반영."""
    renderer = get_builder("html")
    result = (await renderer.build(custom_tokens_schema)).decode("utf-8")

    # 사용자 지정 값.
    assert "#123456" in result
    assert "#AABBCC" in result
    # data-* variant 속성.
    assert 'data-spacing="compact"' in result
    assert 'data-brand-preset="custom"' in result
    # NotoSansKR 폰트 스택 첫 family.
    assert '"Noto Sans KR"' in result


async def test_malicious_token_value_falls_back_to_default():
    """DesignTokens 의 hex 패턴을 우회한 가짜 토큰 객체를 상상하기 어려우므로,
    `_safe_css_value` 단위로 검증한다. 위험 문자열은 fallback 으로 대체."""
    from app.integrations.document_builders.html.renderer import _safe_css_value

    assert _safe_css_value("#0A4FC2", "#000000") == "#0A4FC2"
    assert _safe_css_value("url(javascript:alert(1))", "#000000") == "#000000"
    assert _safe_css_value("expression(alert(1))", "#000000") == "#000000"
    assert _safe_css_value("</style><script>", "#000000") == "#000000"
    assert _safe_css_value("", "#000000") == "#000000"


async def test_data_attributes_include_page_and_component_ids(full_mvp_schema):
    """data-page-id / data-component-id 가 FE 포맷과 일치 (iframe postMessage 용)."""
    renderer = get_builder("html")
    result = (await renderer.build(full_mvp_schema)).decode("utf-8")
    assert 'data-page-id="p1"' in result
    for cid in ("c1", "c2", "c3", "c4", "c5", "c6"):
        assert f'data-component-id="{cid}"' in result


async def test_css_class_names_match_fe_convention(full_mvp_schema):
    """FE 컴포넌트 파일들이 참조하는 CSS 변수 + 공통 클래스 규약 일치."""
    renderer = get_builder("html")
    result = (await renderer.build(full_mvp_schema)).decode("utf-8")

    # 공통 래퍼 클래스 prefix.
    assert "doc-component doc-component-SlideTitle" in result
    assert "doc-component doc-component-Heading" in result
    assert "doc-component doc-component-Paragraph" in result
    assert "doc-component doc-component-BulletList" in result
    assert "doc-component doc-component-KPI" in result
    assert "doc-component doc-component-DataTable" in result
    # FE 와 동일한 preview-root 클래스도 병기.
    assert "document-preview-root" in result


async def test_bullet_list_numbered_renders_ol():
    """numbered=True 면 `<ol>`, False 면 `<ul>` — FE 동작 동형."""
    renderer = HtmlRenderer()
    schema = DocumentSchema(
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
                    BulletListComponent(
                        id="c1",
                        items=[BulletItem(text="항목 1"), BulletItem(text="항목 2")],
                        numbered=True,
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")
    # ol 태그 존재, ul 은 sub_items 용으로만 존재 (이 케이스는 sub_items 없음).
    assert "<ol " in result
    assert 'data-numbered="true"' in result


async def test_kpi_delta_direction_auto_resolves_from_delta_string():
    """명시 direction 없이 delta 문자열 prefix 로 색상 자동 결정."""
    renderer = HtmlRenderer()
    schema = DocumentSchema(
        document_id=_FIXED_DOC_ID,
        schema_version="1.0",
        type="slide_report",
        mode="free_generation",
        pages=[
            Page(
                id="p1",
                page_kind="slide",
                layout="kpi_dashboard",
                components=[
                    KPIComponent(id="c1", label="매출", value="1B", delta="-5%"),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")
    # delta 가 '-' 시작 → direction='down' 자동 해석.
    assert 'data-delta-direction="down"' in result
    assert "var(--doc-danger)" in result


# ---------------------------------------------------------------------------
# S3 D2 신규 테스트 — Image / ImageGrid / Chart placeholder
# ---------------------------------------------------------------------------


async def test_s3d2_image_with_src_renders_img_tag():
    """S3 D2 — Image 컴포넌트 (src 있음) 는 `<img>` 태그 + alt 포함 렌더."""
    renderer = HtmlRenderer()
    schema = DocumentSchema(
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
                    ImageComponent(
                        id="c1",
                        src="https://example.com/chart.png",
                        alt="분기별 매출 차트",
                        caption="2026 Q1 매출 현황",
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")

    # <img> 태그 존재 + src 속성.
    assert '<img class="doc-image-img"' in result
    assert 'src="https://example.com/chart.png"' in result
    # alt text 포함 (접근성).
    assert 'alt="분기별 매출 차트"' in result
    # caption 은 figcaption 으로 렌더.
    assert "<figcaption" in result
    assert "2026 Q1 매출 현황" in result
    # 래퍼는 Image 컴포넌트 data-attr.
    assert 'data-component-type="Image"' in result


async def test_s3d2_image_without_src_renders_placeholder_div():
    """S3 D2 — Image 컴포넌트 (prompt 만) 는 dashed placeholder 박스로 렌더."""
    renderer = HtmlRenderer()
    schema = DocumentSchema(
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
                    ImageComponent(
                        id="c1",
                        prompt="사무실 회의 장면",
                        alt="회의 일러스트",
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")

    # <img> 태그는 없어야 한다 (src 부재).
    assert '<img class="doc-image-img"' not in result
    # placeholder 박스가 존재.
    assert 'class="doc-image-placeholder"' in result
    assert "[이미지 없음]" in result
    assert "회의 일러스트" in result
    # 래퍼 속성 — data-has-src=false.
    assert 'data-has-src="false"' in result


async def test_s3d2_image_grid_uses_css_grid_with_correct_columns():
    """S3 D2 — ImageGrid 는 CSS Grid + repeat(N, 1fr) 레이아웃.

    이미지 수별 자동 cols: 2→2, 3→3, 4→2 (2x2).
    """
    renderer = HtmlRenderer()
    # 4 개 케이스 → 2 열.
    schema = DocumentSchema(
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
                    ImageGridComponent(
                        id="c1",
                        images=[
                            ImageGridItem(
                                src=f"https://example.com/img{i}.png",
                                alt=f"이미지 {i}",
                            )
                            for i in range(1, 5)
                        ],
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")

    # CSS display: grid + repeat(2, 1fr) 확인 (4장 → 2열).
    assert "display: grid" in result
    assert "grid-template-columns: repeat(2, 1fr)" in result
    # 4 개 셀 모두 렌더.
    for i in range(1, 5):
        assert f"이미지 {i}" in result
    # data-attr 확인.
    assert 'data-component-type="ImageGrid"' in result
    assert 'data-image-count="4"' in result
    assert 'data-cols="2"' in result


async def test_s3d2_image_grid_3_items_uses_3_columns():
    """S3 D2 보조 — ImageGrid 3 개는 3 열 레이아웃."""
    renderer = HtmlRenderer()
    schema = DocumentSchema(
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
                    ImageGridComponent(
                        id="c1",
                        images=[
                            ImageGridItem(src="https://e.com/a.png", alt="A"),
                            ImageGridItem(src="https://e.com/b.png", alt="B"),
                            ImageGridItem(src="https://e.com/c.png", alt="C"),
                        ],
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")
    assert "grid-template-columns: repeat(3, 1fr)" in result
    assert 'data-cols="3"' in result


async def test_s3d2_chart_renders_static_placeholder_with_metadata():
    """S3 D2 — Chart 는 서버 HTML 에서 정적 placeholder 로 렌더.

    실제 시각화는 FE Recharts 가 담당. 서버는 메타정보만 노출.
    """
    renderer = HtmlRenderer()
    schema = DocumentSchema(
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
                    ChartComponent(
                        id="c1",
                        chart_type="pie",
                        title="시장 점유율",
                        data=ChartData(
                            labels=["A", "B", "C"],
                            series=[ChartSeries(name="점유율", values=[40.0, 35.0, 25.0])],
                        ),
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")

    # placeholder 클래스와 메타 데이터 속성.
    assert 'class="chart-placeholder"' in result
    assert 'data-chart-type="pie"' in result
    assert 'data-series-count="1"' in result
    assert 'data-category-count="3"' in result
    # 차트 타이틀은 별도 figcaption 으로 렌더.
    assert "시장 점유율" in result
    # 안내 메시지 (차트: 원형 차트, 시리즈 1개, 카테고리 3개).
    assert "시리즈 1개" in result
    assert "카테고리 3개" in result
    # placeholder 는 정상 컴포넌트로 렌더 — doc-component-placeholder 가 **아닌**
    # Chart 전용 경로를 탔는지 확인 (`supported_components` 에 포함).
    assert 'data-component-type="Chart"' in result


async def test_s3d2_chart_html_xss_protection_in_title():
    """S3 D2 — Chart title 에 악성 태그가 있어도 이스케이프 처리된다."""
    renderer = HtmlRenderer()
    schema = DocumentSchema(
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
                    ChartComponent(
                        id="c1",
                        chart_type="bar",
                        title="<script>alert(1)</script>",
                        data=ChartData(
                            labels=["Q1"],
                            series=[ChartSeries(name="x", values=[1.0])],
                        ),
                    ),
                ],
            ),
        ],
        metadata=_make_metadata(),
    )
    result = (await renderer.build(schema)).decode("utf-8")
    assert "<script>alert(1)</script>" not in result
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in result
