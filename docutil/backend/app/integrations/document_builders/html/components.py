"""MVP 6 컴포넌트 → HTML 문자열 렌더러 (Phase 4 S1 D4).

FE ``frontend/src/components/document-schema/components/*.tsx`` 의 클래스
네이밍·data-* 속성·CSS 변수 사용을 완전히 모방한다. 교체 가능성 보장을
위해 다음 규약을 지킨다:

- 공통 래퍼 클래스: ``doc-component doc-component-{Type}``
- data-* 속성: ``data-component-id``, ``data-component-type``, ``data-page-id``
  (+ 컴포넌트별 보조 data-* — level, numbered, emphasis 등)
- 색/폰트/간격은 **모두 `var(--doc-*)` 로만** 표기. hex 리터럴 금지.
- 모든 사용자 입력 텍스트는 `html.escape()` 처리 (XSS 방어).

각 함수는 `(component, page_id: str) -> str` 시그니처. renderer.py 가 컴포넌
트 타입에 따라 dispatch 한다.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 런타임엔 단순 문자열 포매팅만 하므로 타입 힌트 전용. TC001 회피 + 순환
    # 의존 최소화.
    from app.modules.documents_v2.schemas import (
        BulletListComponent,
        ChartComponent,
        DataTableComponent,
        HeadingComponent,
        ImageComponent,
        ImageGridComponent,
        KPIComponent,
        ParagraphComponent,
        SlideTitleComponent,
    )

# ---------------------------------------------------------------------------
# 공용 헬퍼
# ---------------------------------------------------------------------------


def _wrapper_attrs(component_type: str, component_id: str, page_id: str, extra: str = "") -> str:
    """공통 래퍼 속성 문자열.

    ``html.escape(..., quote=True)`` 로 속성 값의 따옴표·꺽쇠까지 이스케이프
    해 XSS 를 원천 차단한다.
    """
    base = (
        f'class="doc-component doc-component-{html.escape(component_type, quote=True)}" '
        f'data-component-id="{html.escape(component_id, quote=True)}" '
        f'data-component-type="{html.escape(component_type, quote=True)}" '
        f'data-page-id="{html.escape(page_id, quote=True)}"'
    )
    if extra:
        base = f"{base} {extra}"
    return base


# ---------------------------------------------------------------------------
# 1. SlideTitle
# ---------------------------------------------------------------------------


def render_slide_title(comp: SlideTitleComponent, page_id: str) -> str:
    """슬라이드 표제: IDINO primary 색 + font-size-3xl 중앙 정렬.

    FE ``SlideTitle.tsx`` 와 동일하게 ``data-component="SlideTitle"`` 대신
    ``data-component-type="SlideTitle"`` 을 쓴다 — FE 는 두 속성을 모두
    갖지만, 서버 HTML 은 FE 의 data-component-id/type 쌍에 맞춰 간결화.
    """
    text = html.escape(comp.text)
    attrs = _wrapper_attrs("SlideTitle", comp.id, page_id)
    return (
        f"      <div {attrs}"
        f' style="display: flex; flex-direction: column; align-items: center;'
        f" justify-content: center; text-align: center;"
        f' padding: var(--doc-spacing-2xl) var(--doc-spacing-lg);">\n'
        f'        <h1 class="doc-slide-title-text"'
        f' style="color: var(--doc-primary);'
        f" font-family: var(--doc-font-family);"
        f" font-size: var(--doc-font-size-3xl);"
        f" font-weight: 700;"
        f" line-height: var(--doc-line-height-tight);"
        f" word-break: keep-all;"
        f' margin: 0;">{text}</h1>\n'
        f"      </div>\n"
    )


# ---------------------------------------------------------------------------
# 2. Heading
# ---------------------------------------------------------------------------

# FE Heading.tsx 의 LEVEL_FONT_SIZE 매핑과 동일.
_HEADING_FONT_SIZE = {
    1: "var(--doc-font-size-2xl)",
    2: "var(--doc-font-size-xl)",
    3: "var(--doc-font-size-lg)",
}


def render_heading(comp: HeadingComponent, page_id: str) -> str:
    """섹션 제목: level 별로 h1/h2/h3 + border-left 4px primary.

    FE 는 `<div>` 래퍼 내부에 `<hN>` 을 두는 구조. 서버에서도 같은 구조로
    유지해 outer wrapper 에 data-* 를 달고 내부 heading 은 텍스트만 담당.
    """
    text = html.escape(comp.text)
    level = comp.level  # 1..3 (Literal)
    tag = f"h{level}"
    font_size = _HEADING_FONT_SIZE[level]
    weight = 700 if level == 1 else 600
    attrs = _wrapper_attrs(
        "Heading",
        comp.id,
        page_id,
        extra=f'data-level="{level}"',
    )
    return (
        f"      <div {attrs}"
        f' style="padding-left: var(--doc-spacing-md);'
        f" padding-top: var(--doc-spacing-sm);"
        f" padding-bottom: var(--doc-spacing-sm);"
        f" border-left: 4px solid var(--doc-primary);"
        f" margin-top: var(--doc-spacing-lg);"
        f' margin-bottom: var(--doc-spacing-md);">\n'
        f'        <{tag} class="doc-heading-text"'
        f' style="color: var(--doc-text);'
        f" font-family: var(--doc-font-family);"
        f" font-size: {font_size};"
        f" font-weight: {weight};"
        f" line-height: var(--doc-line-height-tight);"
        f" word-break: keep-all;"
        f' margin: 0;">{text}</{tag}>\n'
        f"      </div>\n"
    )


# ---------------------------------------------------------------------------
# 3. Paragraph
# ---------------------------------------------------------------------------

# FE Paragraph.tsx 의 EMPHASIS_STYLE 매핑을 CSS 문자열로 치환.
_PARAGRAPH_EMPHASIS = {
    "normal": ("400", "normal"),
    "bold": ("600", "normal"),
    "italic": ("400", "italic"),
}


def render_paragraph(comp: ParagraphComponent, page_id: str) -> str:
    """본문 단락: emphasis 에 따라 font-weight / font-style 변주."""
    text = html.escape(comp.text)
    weight, font_style = _PARAGRAPH_EMPHASIS[comp.emphasis]
    attrs = _wrapper_attrs(
        "Paragraph",
        comp.id,
        page_id,
        extra=f'data-emphasis="{html.escape(comp.emphasis, quote=True)}"',
    )
    return (
        f"      <div {attrs}"
        f' style="padding: var(--doc-spacing-xs) var(--doc-spacing-sm);'
        f' margin-bottom: var(--doc-spacing-md);">\n'
        f'        <p class="doc-paragraph-text"'
        f' style="color: var(--doc-text);'
        f" font-family: var(--doc-font-family);"
        f" font-size: var(--doc-font-size-base);"
        f" line-height: var(--doc-line-height-normal);"
        f" word-break: keep-all;"
        f" margin: 0;"
        f" font-weight: {weight};"
        f' font-style: {font_style};">{text}</p>\n'
        f"      </div>\n"
    )


# ---------------------------------------------------------------------------
# 4. BulletList
# ---------------------------------------------------------------------------

# FE ITEM_EMPHASIS_STYLE 와 동일.
_BULLET_EMPHASIS = {
    "normal": {"font_weight": "400", "background": "transparent", "padding_inline": "0"},
    "bold": {"font_weight": "600", "background": "transparent", "padding_inline": "0"},
    "highlight": {
        "font_weight": "500",
        "background": "var(--doc-accent-soft)",
        "padding_inline": "var(--doc-spacing-sm)",
    },
}


def render_bullet_list(comp: BulletListComponent, page_id: str) -> str:
    """불릿/번호 목록. numbered=True 면 `<ol>`, 아니면 `<ul>`.

    2 레벨 구조. 각 item 의 emphasis 에 따라 span 에 하이라이트 배경 부여.
    sub_items 는 문자열 리스트이므로 각 항목 개별 이스케이프.
    """
    list_tag = "ol" if comp.numbered else "ul"
    list_style = "decimal" if comp.numbered else "disc"

    items_html_parts: list[str] = []
    for idx, item in enumerate(comp.items):
        emp = _BULLET_EMPHASIS[item.emphasis]
        item_text = html.escape(item.text)
        highlight_radius = " border-radius: var(--doc-radius-sm);" if item.emphasis == "highlight" else ""
        span_html = (
            f'<span style="font-weight: {emp["font_weight"]};'
            f" background: {emp['background']};"
            f' padding-inline: {emp["padding_inline"]};{highlight_radius}">'
            f"{item_text}</span>"
        )
        sub_html = ""
        if item.sub_items:
            sub_items_html = "".join(
                f'<li style="word-break: keep-all;">{html.escape(sub)}</li>' for sub in item.sub_items
            )
            sub_html = (
                f'<ul style="margin-top: var(--doc-spacing-xs);'
                f" padding-inline-start: var(--doc-spacing-lg);"
                f" list-style-type: circle;"
                f" color: var(--doc-text-muted);"
                f' font-size: var(--doc-font-size-sm);">{sub_items_html}</ul>'
            )
        items_html_parts.append(
            f'<li data-item-index="{idx}"'
            f' style="margin-bottom: var(--doc-spacing-xs);'
            f' word-break: keep-all;">{span_html}{sub_html}</li>'
        )
    items_html = "".join(items_html_parts)

    attrs = _wrapper_attrs(
        "BulletList",
        comp.id,
        page_id,
        extra=(f'data-numbered="{str(comp.numbered).lower()}" data-item-count="{len(comp.items)}"'),
    )
    return (
        f"      <div {attrs}"
        f' style="padding: var(--doc-spacing-sm);'
        f' margin-bottom: var(--doc-spacing-md);">\n'
        f'        <{list_tag} class="doc-bullet-list-items"'
        f' style="color: var(--doc-text);'
        f" font-family: var(--doc-font-family);"
        f" font-size: var(--doc-font-size-base);"
        f" line-height: var(--doc-line-height-normal);"
        f" padding-inline-start: var(--doc-spacing-xl);"
        f" margin: 0;"
        f' list-style-type: {list_style};">{items_html}</{list_tag}>\n'
        f"      </div>\n"
    )


# ---------------------------------------------------------------------------
# 5. KPI
# ---------------------------------------------------------------------------

_KPI_DIRECTION_COLOR = {
    "up": "var(--doc-success)",
    "down": "var(--doc-danger)",
    "flat": "var(--doc-text-muted)",
}
# 화살표 문자열(유니코드). FE 는 lucide 아이콘(ArrowUp/ArrowDown/Minus) 사용,
# 서버 HTML 은 외부 아이콘 라이브러리 의존성 없이 유니코드 기호로 대체.
_KPI_DIRECTION_GLYPH = {
    "up": "\u2191",  # ↑
    "down": "\u2193",  # ↓
    "flat": "\u2212",  # −
}
_KPI_DIRECTION_LABEL = {"up": "증가", "down": "감소", "flat": "변동 없음"}


def _resolve_kpi_direction(comp: KPIComponent) -> str | None:
    """FE resolveDirection() 과 동일 규칙.

    1) 명시적 delta_direction 이 있으면 그대로 사용.
    2) delta 문자열이 '+' 시작이면 up, '-' 시작이면 down, 그 외는 flat.
    3) delta 도 없으면 None (화살표/색 미표시).
    """
    if comp.delta_direction:
        return comp.delta_direction
    if not comp.delta:
        return None
    trimmed = comp.delta.strip()
    if trimmed.startswith("+"):
        return "up"
    if trimmed.startswith("-"):
        return "down"
    return "flat"


def render_kpi(comp: KPIComponent, page_id: str) -> str:
    """KPI 카드: label(작은 muted) / value(primary 2xl bold) / delta(방향색)."""
    direction = _resolve_kpi_direction(comp)
    label = html.escape(comp.label)
    value = html.escape(comp.value)

    delta_html = ""
    if comp.delta and direction:
        color = _KPI_DIRECTION_COLOR[direction]
        glyph = _KPI_DIRECTION_GLYPH[direction]
        aria_label = _KPI_DIRECTION_LABEL[direction]
        delta_text = html.escape(comp.delta)
        delta_html = (
            f'\n        <span class="doc-kpi-delta"'
            f' style="color: {color};'
            f" font-size: var(--doc-font-size-sm);"
            f" font-weight: 600;"
            f' display: inline-flex; align-items: center; gap: var(--doc-spacing-xs);"'
            f' aria-label="{html.escape(aria_label, quote=True)}">'
            f'<span aria-hidden="true">{glyph}</span>'
            f"<span>{delta_text}</span></span>"
        )

    description_html = ""
    if comp.description:
        description_html = (
            f'\n        <p class="doc-kpi-description"'
            f' style="margin: var(--doc-spacing-xs) 0 0 0;'
            f" font-size: var(--doc-font-size-xs);"
            f" color: var(--doc-text-muted);"
            f" line-height: var(--doc-line-height-normal);"
            f' word-break: keep-all;">{html.escape(comp.description)}</p>'
        )

    attrs = _wrapper_attrs(
        "KPI",
        comp.id,
        page_id,
        extra=f'data-delta-direction="{direction or "none"}"',
    )
    # `<article>` 대신 `<div>` 사용 — 래퍼 공통 클래스·data-* 를 단순화.
    # FE 는 `<article role="group">` 이지만 서버 HTML 은 FE 와 *시각*만 일치
    # 하면 되므로 semantic 일치는 필수가 아님 (/preview-host 는 iframe).
    return (
        f"      <div {attrs}"
        f' style="background: var(--doc-surface);'
        f" border: 1px solid var(--doc-border);"
        f" border-radius: var(--doc-radius-lg);"
        f" padding: var(--doc-spacing-lg);"
        f" box-shadow: var(--doc-shadow-sm);"
        f" display: flex; flex-direction: column; gap: var(--doc-spacing-xs);"
        f' min-width: 0;">\n'
        f'        <span class="doc-kpi-label"'
        f' style="font-size: var(--doc-font-size-sm);'
        f" color: var(--doc-text-muted);"
        f" font-family: var(--doc-font-family);"
        f" font-weight: 500;"
        f' word-break: keep-all;">{label}</span>\n'
        f'        <span class="doc-kpi-value"'
        f' style="font-size: var(--doc-font-size-2xl);'
        f" color: var(--doc-primary);"
        f" font-family: var(--doc-font-family);"
        f" font-weight: 700;"
        f" line-height: var(--doc-line-height-tight);"
        f' word-break: keep-all;">{value}</span>'
        f"{delta_html}"
        f"{description_html}\n"
        f"      </div>\n"
    )


# ---------------------------------------------------------------------------
# 6. DataTable
# ---------------------------------------------------------------------------


def render_data_table(comp: DataTableComponent, page_id: str) -> str:
    """데이터 표: 헤더는 primary 배경 + white 전경, 짝수행 surface 스트라이프.

    ``emphasis_column_index`` 가 지정되면 해당 열을 accent-soft 배경 + bold.
    FE 와 동일하게 `<figure>`/`<table>` semantic 구조 유지.
    """
    emphasis_idx = comp.emphasis_column_index

    # 캡션
    caption_html = ""
    if comp.caption:
        caption_html = (
            f'        <figcaption class="doc-data-table-caption"'
            f' style="font-size: var(--doc-font-size-lg);'
            f" font-weight: 600;"
            f" color: var(--doc-text);"
            f" font-family: var(--doc-font-family);"
            f" margin-bottom: var(--doc-spacing-sm);"
            f' word-break: keep-all;">{html.escape(comp.caption)}</figcaption>\n'
        )

    # 헤더
    header_cells = "".join(
        f'<th scope="col" data-col-index="{i}"'
        f' style="background: var(--doc-primary);'
        f" color: var(--doc-primary-foreground);"
        f" font-weight: 600; text-align: left;"
        f" padding: var(--doc-spacing-sm) var(--doc-spacing-md);"
        f" border-bottom: 1px solid var(--doc-border);"
        f' word-break: keep-all;">{html.escape(h)}</th>'
        for i, h in enumerate(comp.headers)
    )

    # 바디
    body_rows: list[str] = []
    for row_idx, row in enumerate(comp.rows):
        # 짝수 인덱스(0-based) 는 background, 홀수 인덱스는 surface — FE 가
        # `rowIdx % 2 === 1 ? surface : background` 이므로 동일.
        row_bg = "var(--doc-surface)" if row_idx % 2 == 1 else "var(--doc-background)"
        cells: list[str] = []
        for col_idx, cell in enumerate(row):
            is_emphasis = emphasis_idx is not None and col_idx == emphasis_idx
            emphasis_bg = " background: var(--doc-accent-soft);" if is_emphasis else ""
            emphasis_weight = "600" if is_emphasis else "400"
            emphasis_attr = ' data-emphasis="true"' if is_emphasis else ""
            cells.append(
                f'<td data-col-index="{col_idx}"{emphasis_attr}'
                f' style="padding: var(--doc-spacing-sm) var(--doc-spacing-md);'
                f" border-bottom: 1px solid var(--doc-border);"
                f"{emphasis_bg}"
                f" font-weight: {emphasis_weight};"
                f" word-break: keep-all;"
                f' vertical-align: top;">{html.escape(cell)}</td>'
            )
        body_rows.append(f'<tr data-row-index="{row_idx}" style="background: {row_bg};">{"".join(cells)}</tr>')
    body_html = "".join(body_rows)

    attrs = _wrapper_attrs(
        "DataTable",
        comp.id,
        page_id,
        extra=(f'data-row-count="{len(comp.rows)}" data-col-count="{len(comp.headers)}"'),
    )
    return (
        f"      <figure {attrs}"
        f' style="margin: 0 0 var(--doc-spacing-lg) 0;'
        f" padding: var(--doc-spacing-sm);"
        f" border: 1px solid var(--doc-border);"
        f" border-radius: var(--doc-radius-md);"
        f' background: var(--doc-background);">\n'
        f"{caption_html}"
        f'        <div style="width: 100%; overflow-x: auto;">\n'
        f'          <table class="doc-data-table"'
        f' style="width: 100%; border-collapse: collapse;'
        f" font-family: var(--doc-font-family);"
        f" font-size: var(--doc-font-size-sm);"
        f' color: var(--doc-text);">\n'
        f"            <thead><tr>{header_cells}</tr></thead>\n"
        f"            <tbody>{body_html}</tbody>\n"
        f"          </table>\n"
        f"        </div>\n"
        f"      </figure>\n"
    )


# ---------------------------------------------------------------------------
# 7. Image (S3 D2)
# ---------------------------------------------------------------------------
#
# FE `Image.tsx` 와 동일한 `<figure>` + `<img>` + `<figcaption>` 구조.
# src 가 없는 경우(= prompt 기반 자동 생성 예정) 는 dashed placeholder 박스로
# degrade — FE/서버 양쪽이 동일 시각 효과를 보이도록 border-dashed 처리.


def render_image(comp: ImageComponent, page_id: str) -> str:
    """Image 컴포넌트 렌더.

    동작:
      - src 존재: `<img>` 태그 + alt 속성 (접근성). caption 있으면 `<figcaption>`.
      - src 부재 (prompt 만 있는 경우): dashed placeholder `<div>` + alt 텍스트.

    스키마 제약:
      - ``src`` 또는 ``prompt`` 중 최소 하나 존재 (Pydantic model_validator).
      - ``alt`` 는 필수 (min_length=1).
    """
    alt = html.escape(comp.alt, quote=True)
    caption_html = ""
    if comp.caption:
        caption_html = (
            f'\n        <figcaption class="doc-image-caption"'
            f' style="margin-top: var(--doc-spacing-xs);'
            f" font-size: var(--doc-font-size-sm);"
            f" color: var(--doc-text-muted);"
            f" font-style: italic;"
            f" text-align: center;"
            f" font-family: var(--doc-font-family);"
            f' word-break: keep-all;">{html.escape(comp.caption)}</figcaption>'
        )

    attrs = _wrapper_attrs(
        "Image",
        comp.id,
        page_id,
        extra=f'data-has-src="{str(bool(comp.src)).lower()}"',
    )

    if comp.src:
        # 실제 `<img>` 경로. src 는 속성이므로 quote=True 이스케이프.
        src_attr = html.escape(comp.src, quote=True)
        return (
            f"      <figure {attrs}"
            f' style="margin: 0 0 var(--doc-spacing-md) 0;'
            f' display: flex; flex-direction: column; align-items: center;">\n'
            f'        <img class="doc-image-img" src="{src_attr}" alt="{alt}"'
            f' style="max-width: 100%; height: auto;'
            f" border-radius: var(--doc-radius-sm);"
            f' box-shadow: var(--doc-shadow-sm);" />{caption_html}\n'
            f"      </figure>\n"
        )

    # src 부재 → placeholder (prompt 전용). dashed border + alt 라벨.
    return (
        f"      <figure {attrs}"
        f' style="margin: 0 0 var(--doc-spacing-md) 0;'
        f' display: flex; flex-direction: column; align-items: center;">\n'
        f'        <div class="doc-image-placeholder"'
        f' role="img" aria-label="{alt}"'
        f' style="width: 100%; min-height: 12rem;'
        f" display: flex; align-items: center; justify-content: center;"
        f" border: 2px dashed var(--doc-border);"
        f" border-radius: var(--doc-radius-md);"
        f" background: var(--doc-surface);"
        f" color: var(--doc-text-muted);"
        f" font-style: italic;"
        f" font-family: var(--doc-font-family);"
        f" font-size: var(--doc-font-size-sm);"
        f' padding: var(--doc-spacing-md);">'
        f"[이미지 없음] {html.escape(comp.alt)}"
        f"</div>{caption_html}\n"
        f"      </figure>\n"
    )


# ---------------------------------------------------------------------------
# 8. ImageGrid (S3 D2)
# ---------------------------------------------------------------------------
#
# Pydantic 스키마 ``ImageGridComponent.images`` 는 2~4 개의 ImageGridItem 리스트.
# columns/rows 필드는 없으므로 렌더러가 자동 결정 — 2/3 개는 1 행, 4 개는 2x2.
# FE 와 동일한 CSS Grid 레이아웃 사용.


# 이미지 수 → CSS Grid 열 수 매핑 (PPTX 쪽 IMAGE_GRID_LAYOUT_BY_COUNT 와 동일).
_IMAGE_GRID_COLS_BY_COUNT = {2: 2, 3: 3, 4: 2}


def render_image_grid(comp: ImageGridComponent, page_id: str) -> str:
    """ImageGrid 컴포넌트 렌더 — CSS Grid 레이아웃.

    레이아웃:
      - 2 개 → `grid-template-columns: repeat(2, 1fr)`
      - 3 개 → `grid-template-columns: repeat(3, 1fr)`
      - 4 개 → `grid-template-columns: repeat(2, 1fr)` (자동 2 행)
    """
    n = len(comp.images)
    cols = _IMAGE_GRID_COLS_BY_COUNT.get(n, max(1, min(4, n)))

    # 개별 셀 HTML — Image 컴포넌트와 유사하되 래퍼는 <div class="doc-image-grid-cell">.
    cell_parts: list[str] = []
    for idx, item in enumerate(comp.images):
        alt = html.escape(item.alt, quote=True)
        caption_html = ""
        if item.caption:
            caption_html = (
                f"<figcaption"
                f' style="margin-top: var(--doc-spacing-xs);'
                f" font-size: var(--doc-font-size-xs);"
                f" color: var(--doc-text-muted);"
                f" font-style: italic;"
                f' text-align: center;">{html.escape(item.caption)}</figcaption>'
            )

        if item.src:
            src_attr = html.escape(item.src, quote=True)
            inner = (
                f'<img src="{src_attr}" alt="{alt}"'
                f' style="width: 100%; height: 100%; object-fit: cover;'
                f" border-radius: var(--doc-radius-sm);"
                f' box-shadow: var(--doc-shadow-sm);" />{caption_html}'
            )
        else:
            # src 없음 — placeholder.
            inner = (
                f'<div role="img" aria-label="{alt}"'
                f' style="width: 100%; height: 100%;'
                f" display: flex; align-items: center; justify-content: center;"
                f" border: 2px dashed var(--doc-border);"
                f" border-radius: var(--doc-radius-sm);"
                f" background: var(--doc-surface);"
                f" color: var(--doc-text-muted);"
                f" font-style: italic;"
                f' font-size: var(--doc-font-size-xs);">'
                f"[이미지 없음] {html.escape(item.alt)}"
                f"</div>{caption_html}"
            )

        cell_parts.append(
            f'<figure class="doc-image-grid-cell"'
            f' data-cell-index="{idx}"'
            f' style="margin: 0; min-height: 8rem;'
            f" display: flex; flex-direction: column;"
            f' align-items: stretch;">{inner}</figure>'
        )
    cells_html = "".join(cell_parts)

    attrs = _wrapper_attrs(
        "ImageGrid",
        comp.id,
        page_id,
        extra=f'data-image-count="{n}" data-cols="{cols}"',
    )
    return (
        f"      <div {attrs}"
        f' style="display: grid;'
        f" grid-template-columns: repeat({cols}, 1fr);"
        f" gap: var(--doc-spacing-sm);"
        f' margin-bottom: var(--doc-spacing-md);">\n'
        f"        {cells_html}\n"
        f"      </div>\n"
    )


# ---------------------------------------------------------------------------
# 9. Chart (S3 D2 — 서버 HTML 은 정적 placeholder)
# ---------------------------------------------------------------------------
#
# Chart 의 실제 React 렌더는 FE `Chart.tsx` (Recharts 기반) 가 담당한다.
# 서버에서 생성하는 HTML 은 미리보기/PDF 변환 경로에서 쓰이므로, Recharts 를
# 서버에서 그릴 수는 없고 정적 placeholder + 메타데이터(타입/시리즈 수/제목)
# 만 노출한다. 이 경로는 iframe 에서 FE 렌더로 교체되거나, PDF 변환기가
# placeholder 그대로 캡처해도 의미가 전달되도록 설계.


# chart_type → 사람이 읽기 쉬운 한국어 라벨. FE 와 별개로 서버 HTML 전용.
_CHART_TYPE_KO_LABEL = {
    "bar": "막대 차트",
    "line": "선 차트",
    "pie": "원형 차트",
    "area": "영역 차트",
    "stacked_bar": "누적 막대 차트",
    "stacked_column": "누적 세로 막대 차트",
    "stacked_area": "누적 영역 차트",
}


def render_chart_placeholder(comp: ChartComponent, page_id: str) -> str:
    """Chart 컴포넌트 — 서버 HTML 은 정적 placeholder 로 렌더.

    실제 시각화는 React Recharts (FE 책임) 에서 동일 스키마를 받아 그린다.
    서버는 메타정보 (차트 타입·시리즈 수·제목·카테고리 수) 만 CSS 박스에 담아
    사용자에게 "차트가 여기 들어감" 신호를 전달.
    """
    chart_type = (comp.chart_type or "").strip().lower()
    type_label = _CHART_TYPE_KO_LABEL.get(chart_type, chart_type or "차트")
    series_count = len(comp.data.series) if comp.data and comp.data.series else 0
    category_count = len(comp.data.labels) if comp.data and comp.data.labels else 0
    title = html.escape(comp.title)

    attrs = _wrapper_attrs(
        "Chart",
        comp.id,
        page_id,
        extra=(
            f'data-chart-type="{html.escape(chart_type, quote=True)}"'
            f' data-series-count="{series_count}"'
            f' data-category-count="{category_count}"'
        ),
    )
    return (
        f"      <figure {attrs}"
        f' style="margin: 0 0 var(--doc-spacing-md) 0;'
        f" padding: var(--doc-spacing-lg);"
        f" border: 1px solid var(--doc-border);"
        f" border-radius: var(--doc-radius-md);"
        f' background: var(--doc-surface);">\n'
        f'        <figcaption class="doc-chart-title"'
        f' style="font-size: var(--doc-font-size-lg);'
        f" font-weight: 600;"
        f" color: var(--doc-text);"
        f" font-family: var(--doc-font-family);"
        f" margin-bottom: var(--doc-spacing-sm);"
        f' text-align: center;">{title}</figcaption>\n'
        f'        <div class="chart-placeholder"'
        f' role="img"'
        f' aria-label="{html.escape(type_label, quote=True)} — 시리즈 {series_count}개, 카테고리 {category_count}개"'
        f' style="min-height: 10rem;'
        f" display: flex; align-items: center; justify-content: center;"
        f" border: 2px dashed var(--doc-border);"
        f" border-radius: var(--doc-radius-sm);"
        f" background: var(--doc-background);"
        f" color: var(--doc-text-muted);"
        f" font-family: var(--doc-font-family);"
        f" font-size: var(--doc-font-size-sm);"
        f' font-style: italic;">'
        f"차트: {type_label}, 시리즈 {series_count}개, 카테고리 {category_count}개"
        f"</div>\n"
        f"      </figure>\n"
    )
