"""HtmlRenderer — DocumentSchema → HTML 바이트 빌더 (Phase 4 S1 D4).

DocumentBuilder ABC 를 상속한 첫 번째 구체 빌더. FE React 렌더와 동일한
클래스 네이밍·data-* 속성·CSS 변수(`--doc-*`)를 사용해 ``/preview-host``
라우트에서 서버 HTML ↔ React 렌더를 교체 가능하도록 설계했다.

설계 판단 포인트:
1. **`async def build()` 유지**: base.py ABC 시그니처 고정. HTML 자체는 순수
   문자열 조립이라 동기 함수로도 충분하지만, 향후 이미지 fetch/토큰 서명
   등을 동일 계층에서 수행할 여지를 남겨둠 (P4 데이터 흐름 유지).
2. **XSS 방어**: 사용자 제공 텍스트·컴포넌트 ID·디자인 토큰 값 모두
   `html.escape(..., quote=True)` 선행. 토큰 중 색상 문자열은 추가로
   `_safe_css_value()` 로 `url()` / `expression()` / 백슬래시 이스케이프를
   차단.
3. **Degradation 정책**: `supported_components` 에 없는 컴포넌트(예: Chart)
   는 `validate_components()` 가 탐지 → placeholder `<div>` 로 대체하고
   빌드 자체는 실패시키지 않는다. 로그는 WARNING 레벨 기록.
4. **design_tokens 주입**: FE 는 CSS 파일 `document-tokens.css` 로 기본값을
   가지며 data-brand-preset/data-spacing 속성으로 variant 를 변경한다.
   서버 HTML 은 단발성 산출물이므로 스키마 값으로 `:root` 블록을 한 번만
   오버라이드. data-* 속성도 함께 부여해 FE CSS variant 셀렉터와 호환.
5. **Registry 등록**: 모듈 최하단에서 `BuilderRegistry.register(HtmlRenderer())`
   를 호출하지 않는다. 호출은 `html/__init__.py` 쪽에서 임포트 시점에
   명시적으로 수행해 테스트 격리(clear) 후 재등록 제어를 쉽게 한다.

참조:
- docs/phase1_architecture.md §3.2, §3.5, 부록 B
- docs/phase3_execution_roadmap.md §2.1 S1 D4
- frontend/src/components/document-schema/components/*.tsx (FE 시각 호환)
"""

from __future__ import annotations

import html
import logging
import re
from typing import ClassVar

from app.integrations.document_builders.base import BuildTarget, DocumentBuilder
from app.integrations.document_builders.html import components, templates
from app.modules.documents_v2.schemas import (
    BulletListComponent,
    ChartComponent,
    Component,
    DataTableComponent,
    DesignTokens,
    DocumentSchema,
    HeadingComponent,
    ImageComponent,
    ImageGridComponent,
    KPIComponent,
    Page,
    ParagraphComponent,
    SlideTitleComponent,
    ThreeColumnComponent,
    TwoColumnComponent,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSS 안전 검증
# ---------------------------------------------------------------------------

# DesignTokens 의 색상 필드는 Pydantic pattern=r"^#[0-9A-Fa-f]{6}$" 로 이미
# 제약이 강하지만, 향후 custom brand_preset 등으로 임의 문자열이 들어올
# 가능성에 대비해 방어적으로 허용 문자 집합을 추가 검증한다.
#
# 허용 문자 (CSS value 문맥):
#   - 알파벳 / 숫자 / '#' / ',' / '.' / ' ' / '(' / ')' / '-' / '"'
#   - Pretendard 등 한글 폰트 패밀리 이름도 기본값은 위 집합 내에 있다.
_SAFE_CSS_VALUE_RE = re.compile(r"^[A-Za-z0-9 ,.\(\)\-#\"']+$")

# 블랙리스트 — 위 집합을 통과하더라도 이 키워드는 차단.
_DANGEROUS_CSS_KEYWORDS = ("url(", "expression(", "javascript:", "@import", "</")


def _safe_css_value(value: str, fallback: str) -> str:
    """CSS value 문자열을 검증 — 위험한 문자/키워드 포함 시 fallback 반환.

    HTML escape 만으로는 CSS 문맥 내부에서 ``url(javascript:...)`` 같은
    공격을 막을 수 없다. 토큰 값은 인용부호 없이 CSS property value 로
    직접 삽입되므로 정규식 화이트리스트 + 블랙리스트 이중 검증.
    """
    if not isinstance(value, str) or not value:
        return fallback
    if not _SAFE_CSS_VALUE_RE.match(value):
        return fallback
    lower = value.lower()
    if any(kw in lower for kw in _DANGEROUS_CSS_KEYWORDS):
        return fallback
    return value


# ---------------------------------------------------------------------------
# HtmlRenderer
# ---------------------------------------------------------------------------


class HtmlRenderer(DocumentBuilder):
    """DocumentSchema → utf-8 인코딩된 HTML 바이트.

    MVP 6 컴포넌트만 네이티브 렌더 지원. 나머지 16종은 `supported_components`
    에서 제외되어 placeholder 로 degrade 된다 (빌드 실패 X).
    """

    target: ClassVar[BuildTarget] = "html"
    # S3 D2 확장: Image / ImageGrid / Chart(정적 placeholder) 추가.
    # KPI/DataTable 은 S1 D4 시점에 이미 네이티브 렌더 지원 중이었다 — 본 업데이트에선
    # 문서상 보강만.
    supported_components: ClassVar[frozenset[str]] = frozenset(
        {
            "SlideTitle",
            "Heading",
            "Paragraph",
            "BulletList",
            "KPI",
            "DataTable",
            "Image",  # S3 D2 신규 — <img src alt> + <figcaption>
            "ImageGrid",  # S3 D2 신규 — CSS Grid 레이아웃
            "Chart",  # S3 D2 신규 — 서버 HTML 은 정적 placeholder, React 는 Recharts
        }
    )

    # -- 메인 진입점 ---------------------------------------------------------

    async def build(self, schema: DocumentSchema) -> bytes:
        """DocumentSchema 를 HTML bytes(utf-8) 로 변환한다.

        Args:
            schema: 변환 대상 문서 스키마. Pydantic 이 이미 타입·제약 검증 완료.

        Returns:
            utf-8 인코딩된 HTML 문자열 바이트. `<!doctype html>` 로 시작.

        Notes:
            - 빈 pages 는 Pydantic `min_length=1` 로 원천 차단되지만, 방어적
              으로 빈 컨테이너도 처리 가능하게 설계.
            - 미지원 컴포넌트는 placeholder 로 대체 + WARNING 로그.
        """
        unsupported = self.validate_components(schema)
        if unsupported:
            logger.warning(
                "HtmlRenderer: 미지원 컴포넌트 감지 → placeholder 렌더: %s",
                ", ".join(unsupported),
            )

        # 1) 페이지 HTML 조립
        pages_html = "".join(self._render_page(page) for page in schema.pages)

        # 2) design_tokens CSS 오버라이드 블록
        token_css = self._build_token_overrides(schema.design_tokens)

        # 3) 문서 래퍼 속성 (data-*)
        spacing_attr = html.escape(schema.design_tokens.spacing, quote=True)
        brand_preset_attr = html.escape(schema.design_tokens.brand_preset, quote=True)
        document_id_attr = html.escape(str(schema.document_id), quote=True)

        html_str = templates.render_document(
            token_overrides_css=token_css,
            spacing_attr=spacing_attr,
            brand_preset_attr=brand_preset_attr,
            document_id_attr=document_id_attr,
            body_inner=pages_html,
        )
        return html_str.encode("utf-8")

    # -- 토큰 → CSS ----------------------------------------------------------

    def _build_token_overrides(self, tokens: DesignTokens) -> str:
        """DesignTokens → `:root{...}` 오버라이드 CSS 문자열.

        기본값은 BASE_STYLE 이 담당하고, 여기서는 schema 가 제공한 값만 얹어
        지는 **두 번째** `<style>` 블록의 내용을 만든다. 사용자가 직접 hex
        값을 지정한 경우(brand_preset=custom) 에도 동일 경로로 처리된다.
        """
        defaults = DesignTokens()  # 타입 기본값
        entries: list[str] = []

        # 색상 4종 — pattern validator 로 이미 `#RRGGBB` 보장되지만 방어적 검증.
        for css_var, attr_name, default_val in (
            ("--doc-primary", "primary_color", defaults.primary_color),
            ("--doc-accent", "accent_color", defaults.accent_color),
            ("--doc-text", "text_color", defaults.text_color),
            ("--doc-background", "background_color", defaults.background_color),
        ):
            raw_val = getattr(tokens, attr_name)
            safe_val = _safe_css_value(raw_val, default_val)
            entries.append(f"  {css_var}: {safe_val};")

        # 폰트 패밀리 — FontFamily Literal 이므로 아래 맵으로 전체 스택 치환.
        font_stack = {
            "Pretendard": ('"Pretendard", "Noto Sans KR", ui-sans-serif, system-ui, sans-serif'),
            "NotoSansKR": ('"Noto Sans KR", "Pretendard", ui-sans-serif, system-ui, sans-serif'),
            "System": "ui-sans-serif, system-ui, sans-serif",
        }[tokens.font_family]
        # font_stack 은 라이브러리 상수라 추가 검증 불필요.
        entries.append(f"  --doc-font-family: {font_stack};")

        return ":root {\n" + "\n".join(entries) + "\n}"

    # -- 페이지/컴포넌트 ----------------------------------------------------

    def _render_page(self, page: Page) -> str:
        """단일 Page → `<section class="doc-page">` 블록."""
        components_html = "".join(self._render_component(c, page.id) for c in page.components)
        return templates.render_page(
            page_id_attr=html.escape(page.id, quote=True),
            page_kind_attr=html.escape(page.page_kind, quote=True),
            layout_attr=html.escape(page.layout, quote=True),
            components_html=components_html,
        )

    def _render_component(self, component: Component, page_id: str) -> str:
        """단일 Component → HTML 문자열.

        지원 타입이면 components 모듈의 전용 렌더 함수로 dispatch. 미지원
        타입이면 placeholder. TwoColumn/ThreeColumn 은 MVP 에서 미지원
        (supported_components 제외) 이므로 placeholder 경로로 떨어진다.
        다만 컨테이너 내부 자식 컴포넌트도 `validate_components()` 로는
        탐지되므로 로그 경고는 재귀적으로 이미 수집된다.
        """
        type_name = component.type
        if type_name not in self.supported_components:
            return templates.render_placeholder(
                component_type_attr=html.escape(type_name, quote=True),
                component_id_attr=html.escape(component.id, quote=True),
                page_id_attr=html.escape(page_id, quote=True),
            )

        # Pydantic Discriminated Union 덕에 isinstance 분기가 안전.
        if isinstance(component, SlideTitleComponent):
            return components.render_slide_title(component, page_id)
        if isinstance(component, HeadingComponent):
            return components.render_heading(component, page_id)
        if isinstance(component, ParagraphComponent):
            return components.render_paragraph(component, page_id)
        if isinstance(component, BulletListComponent):
            return components.render_bullet_list(component, page_id)
        if isinstance(component, KPIComponent):
            return components.render_kpi(component, page_id)
        if isinstance(component, DataTableComponent):
            return components.render_data_table(component, page_id)
        # S3 D2 — Image / ImageGrid / Chart (정적 placeholder).
        if isinstance(component, ImageComponent):
            return components.render_image(component, page_id)
        if isinstance(component, ImageGridComponent):
            return components.render_image_grid(component, page_id)
        if isinstance(component, ChartComponent):
            return components.render_chart_placeholder(component, page_id)

        # supported_components 에는 있는데 isinstance 매칭이 안 되는 경우.
        # 이론상 도달 불가이지만 방어적 fallback.
        if isinstance(component, (TwoColumnComponent, ThreeColumnComponent)):
            logger.warning("HtmlRenderer: 컨테이너 컴포넌트는 MVP 미지원 → placeholder")
        return templates.render_placeholder(
            component_type_attr=html.escape(type_name, quote=True),
            component_id_attr=html.escape(component.id, quote=True),
            page_id_attr=html.escape(page_id, quote=True),
        )
