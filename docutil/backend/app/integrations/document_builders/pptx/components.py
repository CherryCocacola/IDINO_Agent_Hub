"""PPTX 텍스트 컴포넌트 렌더러 (Phase 4 S2 D2).

4 종 텍스트 컴포넌트(`SlideTitle`/`Heading`/`Paragraph`/`BulletList`) 를
python-pptx 슬라이드 위에 text box 로 삽입한다. 각 렌더 함수는 슬라이드의
적절한 인치 좌표에 `textbox` 를 추가한 뒤, `apply_idino_text_style()` 로
폰트·크기·색을 부여한다.

설계 판단 포인트:

1. **단일 레이아웃(blank) 위에 수동 배치**: D2 범위는 layout_resolver 가
   없는 상태이므로 `slide_layouts[6]` (blank) 위에 `shapes.add_textbox()`
   로 직접 좌표를 지정해 배치한다. D3 에서 layout_resolver 가 도입되면
   placeholder 주입 경로로 승격된다 (기존 `_fill_placeholder` 경로).

2. **Y 좌표 스택 관리**: 슬라이드당 여러 컴포넌트가 올 수 있으므로 builder
   쪽에서 상태(현재 Y 위치)를 관리하고 각 렌더 함수에 넘겨준다. 본 모듈은
   "현재 Y 에 배치" 한 뒤 "다음 컴포넌트가 쓸 Y" 를 반환한다 → 호출부가
   누적.

3. **BulletList 는 paragraph 반복 + glyph prefix**: python-pptx 는 자동
   불릿 리스트를 지원하지 않으므로 각 항목을 별도 paragraph 로 만들고 "•"
   prefix 를 텍스트에 포함시킨다. numbered=True 면 "1. ", "2. " 식 숫자
   prefix. sub_items 는 들여쓰기(들여쓰기 문자 + "◦") 로 표현.

4. **Pydantic isinstance 분기는 builder.py 에서**: 본 모듈의 함수들은 이미
   타입 힌트로 구체 컴포넌트를 받는다. Discriminated Union 분기는 호출부
   (builder._render_component) 가 책임.

참조:
- backend/app/integrations/document_builders/html/components.py (FE 시각 호환성)
- backend/app/workers/report_generator.py `_set_tf_text`, `_add_idino_*` (이관 원천)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from app.integrations.document_builders.pptx.constants import (
    BODY_HEIGHT_IN,
    BODY_LEFT_IN,
    BODY_TOP_IN,
    BODY_WIDTH_IN,
    BULLET_GLYPH_SUB,
    BULLET_GLYPH_UNORDERED,
    CALLOUT_BORDER_WIDTH_IN,
    CALLOUT_MIN_HEIGHT_IN,
    CALLOUT_PADDING_IN,
    CALLOUT_VARIANT_BG,
    CALLOUT_VARIANT_BORDER,
    CALLOUT_VARIANT_LETTER,
    CHARS_PER_LINE_BY_PT,
    CHART_AXIS_FONT_PT,
    CHART_DEFAULT_HEIGHT_IN,
    CHART_EMPTY_PLACEHOLDER_TEXT,
    CHART_ETC_CATEGORY_LABEL,
    CHART_FALLBACK_TYPE,
    CHART_LEGEND_FONT_PT,
    CHART_MAX_CATEGORIES,
    CHART_MIN_HEIGHT_IN,
    CHART_SERIES_PALETTE,
    CHART_TITLE_FONT_PT,
    CHART_XL_TYPE_NAME_BY_ALIAS,
    COMPONENT_VERTICAL_GAP_IN,
    DEFAULT_FONT,
    FONT_SIZE_BULLET,
    FONT_SIZE_BULLET_SUB,
    FONT_SIZE_CALLOUT,
    FONT_SIZE_ICON_ROW_LABEL,
    FONT_SIZE_ICON_ROW_LETTER,
    FONT_SIZE_IMAGE_CAPTION,
    FONT_SIZE_KPI_DELTA,
    FONT_SIZE_KPI_LABEL,
    FONT_SIZE_KPI_VALUE,
    FONT_SIZE_PARAGRAPH,
    FONT_SIZE_QUOTE,
    FONT_SIZE_QUOTE_AUTHOR,
    FONT_SIZE_SLIDE_SUBTITLE,
    FONT_SIZE_SLIDE_TITLE,
    FONT_SIZE_TABLE_CELL,
    FONT_SIZE_TABLE_HEADER,
    FONT_SIZE_TIMELINE_DATE,
    FONT_SIZE_TIMELINE_DESC,
    FONT_SIZE_TIMELINE_TITLE,
    HEADING_HEIGHT_IN,
    HEADING_LEFT_IN,
    HEADING_LEVEL_TO_PT,
    HEADING_TOP_IN,
    HEADING_WIDTH_IN,
    HIGHLIGHT_BG_COLOR,
    HIGHLIGHT_BG_VERTICAL_PADDING_IN,
    ICON_ROW_CIRCLE_DIAMETER_IN,
    ICON_ROW_ITEM_GAP_IN,
    ICON_ROW_LABEL_GAP_IN,
    ICON_ROW_LABEL_HEIGHT_IN,
    IDINO_ACCENT,
    IDINO_HEADER_NAVY,
    IDINO_PRIMARY,
    IDINO_TEXT,
    IDINO_TEXT_MUTED,
    IDINO_WHITE,
    IMAGE_CAPTION_HEIGHT_IN,
    IMAGE_FALLBACK_ASPECT_RATIO,
    IMAGE_GRID_GAP_IN,
    IMAGE_GRID_LAYOUT_BY_COUNT,
    IMAGE_PLACEHOLDER_BG,
    IMAGE_PLACEHOLDER_HEIGHT_IN,
    IMAGE_PLACEHOLDER_WIDTH_IN,
    KOREAN_CHAR_WIDTH_MULTIPLIER,
    KPI_BOX_BG,
    KPI_CARD_HEIGHT_IN,
    KPI_DELTA_DOWN_COLOR,
    KPI_DELTA_FLAT_COLOR,
    KPI_DELTA_HEIGHT_IN,
    KPI_DELTA_UP_COLOR,
    KPI_LABEL_HEIGHT_IN,
    KPI_VALUE_HEIGHT_IN,
    QUOTE_AUTHOR_HEIGHT_IN,
    QUOTE_BAR_WIDTH_IN,
    QUOTE_LINE_HEIGHT_MULTIPLIER,
    QUOTE_MIN_HEIGHT_IN,
    QUOTE_PADDING_LEFT_IN,
    SLIDE_SUBTITLE_HEIGHT_IN,
    SLIDE_TITLE_HEIGHT_IN,
    SLIDE_TITLE_LEFT_IN,
    SLIDE_TITLE_TOP_IN,
    SLIDE_TITLE_WIDTH_IN,
    TABLE_BORDER_COLOR,
    TABLE_MAX_DISPLAY_ROWS,
    TABLE_ROW_HEIGHT_IN,
    TABLE_ZEBRA_ROW_BG,
    TIMELINE_CONNECTOR_WIDTH_IN,
    TIMELINE_EVENT_BODY_HEIGHT_IN,
    TIMELINE_EVENT_GAP_IN,
    TIMELINE_MARKER_COLUMN_WIDTH_IN,
    TIMELINE_MARKER_DIAMETER_IN,
    TIMELINE_MAX_EVENTS,
)
from app.integrations.document_builders.pptx.image_fetcher import (
    ImageFetchError,
    fetch_image_bytes,
)
from app.integrations.document_builders.pptx.style import (
    apply_idino_text_style,
    parse_hex_color,
    reset_text_frame,
)

if TYPE_CHECKING:
    # 런타임에는 python-pptx Slide 객체가 Duck-typed 로 전달되므로 타입 힌트
    # 전용으로만 import. Pydantic 컴포넌트도 TC001 회피 + 순환 의존 최소화.
    from io import BytesIO

    from pptx.slide import Slide

    from app.modules.documents_v2.schemas import (
        BulletListComponent,
        CalloutComponent,
        ChartComponent,
        DataTableComponent,
        HeadingComponent,
        IconRowComponent,
        ImageComponent,
        ImageGridComponent,
        ImageGridItem,
        KPIComponent,
        ParagraphComponent,
        QuoteComponent,
        SlideSubtitleComponent,
        SlideTitleComponent,
        TimelineComponent,
    )

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------


def _add_textbox_at(
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float,
) -> object:
    """지정 좌표에 빈 textbox 를 추가하고 shape 를 반환.

    좌표 단위 변환(`Inches`) 을 한 지점에 모아 components 함수들이 순수하게
    상수 + 숫자만 다루게 한다.
    """
    return slide.shapes.add_textbox(
        Inches(left_in),
        Inches(top_in),
        Inches(width_in),
        Inches(height_in),
    )


def _is_korean_char(ch: str) -> bool:
    """U+AC00 ~ U+D7A3 (완성형 한글) 또는 U+3131 ~ U+318E (자모) 판정.

    D9-e 에서 도입. 한/영 혼용 텍스트의 라인 폭 추정 가중치 계산에 사용된다.
    중일 통합 한자는 가중치 측면에서 한글과 유사하지만, 본 프로젝트에서는
    한글 비중이 압도적이므로 단순화를 위해 한글만 판정.
    """
    if not ch:
        return False
    code = ord(ch)
    return 0xAC00 <= code <= 0xD7A3 or 0x3131 <= code <= 0x318E


def _count_weighted_chars(text: str) -> float:
    """한글 가중치 1.5 / 영문·숫자·기호 1.0 으로 합산한 가상 글자 수.

    D9-e — Paragraph 높이 추정을 한/영 혼용 텍스트에서도 적절히 수행하기 위한
    헬퍼. Pretendard 기준 한글이 영문 대비 약 1.5 배 넓다는 실측에서 유래.

    Args:
        text: 합산 대상 텍스트.

    Returns:
        가중치 합(float). 줄바꿈 문자는 폭에 기여하지 않으므로 0 으로 취급.
    """
    total = 0.0
    for ch in text:
        if ch == "\n":
            continue
        if _is_korean_char(ch):
            total += KOREAN_CHAR_WIDTH_MULTIPLIER
        else:
            total += 1.0
    return total


def _chars_per_line_for_pt(font_pt: int, width_in: float) -> int:
    """font_pt + width_in → 한 줄에 들어가는 영문 기준 글자 수.

    D9-e 에서 신규. ``CHARS_PER_LINE_BY_PT`` 는 BODY_WIDTH_IN(=12.133") 기준
    측정치이므로 호출부가 다른 width 로 박스를 잡을 때 비례 스케일.

    매핑에 없는 pt 는 가장 가까운 키로 추정 (이진 근사 대신 가장 가까운 키
    선택 — 계산이 간단하고 오차도 허용 범위 내).

    Args:
        font_pt: 폰트 크기 (pt).
        width_in: 박스 너비 (인치).

    Returns:
        한 줄에 들어가는 영문 기준 글자 수 (int, 최소 10).
    """
    # 사전에 있는 키 중 가장 가까운 키 선택.
    if font_pt in CHARS_PER_LINE_BY_PT:
        base = CHARS_PER_LINE_BY_PT[font_pt]
    else:
        closest = min(CHARS_PER_LINE_BY_PT.keys(), key=lambda k: abs(k - font_pt))
        base = CHARS_PER_LINE_BY_PT[closest]

    # BODY_WIDTH_IN 기준 표 → 실제 width 로 선형 스케일.
    scaled = int(round(base * (width_in / BODY_WIDTH_IN)))
    # 너비 0 근처에서 0 이 되는 극단 케이스 방어.
    return max(10, scaled)


def _estimate_height_by_chars(text: str, chars_per_line: int, pt_per_line: float) -> float:
    """텍스트 길이 기반 박스 높이 추정 (인치 반환).

    Paragraph / BulletList 은 길이가 가변이므로 박스 높이를 정확히 지정하기
    어렵다. python-pptx 의 `word_wrap=True` 로 자동 줄바꿈은 되지만, Y 스택
    관리를 위해 호출부가 다음 컴포넌트의 Y 를 알아야 하므로 보수적 추정.

    Args:
        text: 추정 대상 텍스트.
        chars_per_line: 한 줄에 들어가는 대략적 글자 수 (한글 기준 40~70).
        pt_per_line: 줄 높이 (pt 단위, 대략 font_size * 1.4).

    Returns:
        인치 단위 박스 높이. 최소 BODY_HEIGHT_IN 이상.
    """
    # 개행 기준 + 길이 기준 줄 수 계산.
    lines_from_newlines = text.count("\n") + 1
    lines_from_length = max(1, -(-len(text) // chars_per_line))  # ceil 나눗셈
    total_lines = max(lines_from_newlines, lines_from_length)
    # pt → 인치 (72 pt = 1 인치).
    height_in = (total_lines * pt_per_line) / 72.0
    return max(BODY_HEIGHT_IN, height_in + 0.1)  # 약간의 여유.


def _estimate_paragraph_height_weighted(
    text: str,
    *,
    font_pt: int,
    width_in: float,
    min_height_in: float = BODY_HEIGHT_IN,
) -> float:
    """D9-e — 한/영 가중치를 반영한 Paragraph 높이 추정.

    기존 ``_estimate_height_by_chars`` 는 순수 ``len(text)`` 를 사용해 한글
    밀집 텍스트에서 과소 추정 (박스 잘림), 영문 밀집 텍스트에서 과대 추정
    (아래 여백 과다) 문제가 있었다. 본 함수는 한글 1.5 / 영문 1.0 가중치로
    가상 글자 수를 계산한 뒤 font_pt · width 기반 실측 테이블에서 한 줄 수용량
    을 가져와 줄 수를 역산한다.

    Args:
        text: 추정 대상 텍스트.
        font_pt: 폰트 크기 (pt).
        width_in: 박스 너비 (인치).
        min_height_in: 최소 높이 (인치). 짧은 텍스트에도 최소 여백 확보.

    Returns:
        인치 단위 박스 높이. 최소 ``min_height_in``.
    """
    weighted = _count_weighted_chars(text)
    cpl = _chars_per_line_for_pt(font_pt, width_in)
    # ceil 나눗셈 (가중치가 float 이므로 올림 전용 식 사용).
    lines_from_length = max(1, int((weighted + cpl - 1) // cpl)) if weighted > 0 else 1
    # 명시적 개행이 더 많으면 그것을 우선.
    lines_from_newlines = text.count("\n") + 1
    total_lines = max(lines_from_newlines, lines_from_length)
    # pt → 인치 (72 pt = 1 인치), 행간 1.4 배.
    pt_per_line = font_pt * 1.4
    height_in = (total_lines * pt_per_line) / 72.0
    return max(min_height_in, height_in + 0.1)


# ---------------------------------------------------------------------------
# 1. SlideTitle
# ---------------------------------------------------------------------------


def render_slide_title(component: SlideTitleComponent, slide: Slide) -> float:
    """슬라이드 표제를 상단 중앙에 배치한다.

    - 좌우 여백 0.5", 위에서 0.5" 지점부터 시작 (constants 참조).
    - IDINO primary 색 + 32pt + bold + center 정렬.
    - 표지/섹션 divider 슬라이드에서 주로 사용되나, 본 D2 범위에선 레이아웃
      구분 없이 모든 슬라이드 상단에 동일 방식으로 배치.

    Args:
        component: `SlideTitleComponent` 인스턴스.
        slide: python-pptx Slide (호출자 소유, 이미 add_slide() 된 상태).

    Returns:
        이 컴포넌트 바닥의 Y 좌표 (인치). 호출부가 다음 컴포넌트의 top 으로 사용.
    """
    shape = _add_textbox_at(
        slide,
        left_in=SLIDE_TITLE_LEFT_IN,
        top_in=SLIDE_TITLE_TOP_IN,
        width_in=SLIDE_TITLE_WIDTH_IN,
        height_in=SLIDE_TITLE_HEIGHT_IN,
    )
    tf = shape.text_frame
    tf.word_wrap = True

    # 텍스트 설정 후 스타일 적용 (runs 가 텍스트 세팅 시점에 생성됨).
    paragraph = reset_text_frame(tf)
    paragraph.text = component.text
    apply_idino_text_style(
        paragraph,
        font_size=FONT_SIZE_SLIDE_TITLE,
        bold=True,
        color=IDINO_PRIMARY,
        alignment=PP_ALIGN.CENTER,
    )

    return SLIDE_TITLE_TOP_IN + SLIDE_TITLE_HEIGHT_IN + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 2. Heading
# ---------------------------------------------------------------------------


def render_heading(
    component: HeadingComponent,
    slide: Slide,
    top_in: float | None = None,
) -> float:
    """섹션 제목을 본문 영역 상단에 배치한다.

    level 에 따라 폰트 크기 차등 (constants.HEADING_LEVEL_TO_PT). 1/2/3 모두
    bold=True 로 유지하고 크기(24/20/16pt) 로 위계 표현.

    Args:
        component: `HeadingComponent` (level ∈ {1,2,3}).
        slide: python-pptx Slide.
        top_in: 시작 Y 좌표 (인치). None 이면 기본값(HEADING_TOP_IN).

    Returns:
        컴포넌트 바닥 Y 좌표 (다음 컴포넌트 top 으로 사용).
    """
    resolved_top = top_in if top_in is not None else HEADING_TOP_IN
    font_pt = HEADING_LEVEL_TO_PT[component.level]

    shape = _add_textbox_at(
        slide,
        left_in=HEADING_LEFT_IN,
        top_in=resolved_top,
        width_in=HEADING_WIDTH_IN,
        height_in=HEADING_HEIGHT_IN,
    )
    tf = shape.text_frame
    tf.word_wrap = True

    paragraph = reset_text_frame(tf)
    paragraph.text = component.text
    apply_idino_text_style(
        paragraph,
        font_size=font_pt,
        bold=True,
        color=IDINO_PRIMARY,
        alignment=PP_ALIGN.LEFT,
    )

    return resolved_top + HEADING_HEIGHT_IN + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 3. Paragraph
# ---------------------------------------------------------------------------


def render_paragraph(
    component: ParagraphComponent,
    slide: Slide,
    top_in: float | None = None,
) -> float:
    """본문 단락을 배치한다.

    emphasis 값에 따라 weight/italic 변주:
      - "normal" → 400, 기립
      - "bold"   → 700, 기립
      - "italic" → 400, italic

    python-pptx 는 italic 을 run.font.italic 으로 지정. 본 헬퍼
    `apply_idino_text_style()` 는 italic 을 지원하지 않아 여기서 직접 처리.

    Args:
        component: `ParagraphComponent`.
        slide: python-pptx Slide.
        top_in: 시작 Y 좌표 (인치). None 이면 본문 기본 Y (BODY_TOP_IN).

    Returns:
        컴포넌트 바닥 Y 좌표.
    """
    resolved_top = top_in if top_in is not None else BODY_TOP_IN

    # D9-e — 한/영 혼용 가중치 기반 높이 추정. 기존 하드코딩 chars_per_line=70
    # 은 영문 편향이라 한글 본문에서 박스 잘림이 발생. 가중치 + pt 테이블로
    # ±20 % 오차 이내 추정을 목표로 한다.
    est_height = _estimate_paragraph_height_weighted(
        component.text,
        font_pt=FONT_SIZE_PARAGRAPH,
        width_in=BODY_WIDTH_IN,
    )

    shape = _add_textbox_at(
        slide,
        left_in=BODY_LEFT_IN,
        top_in=resolved_top,
        width_in=BODY_WIDTH_IN,
        height_in=est_height,
    )
    tf = shape.text_frame
    tf.word_wrap = True

    paragraph = reset_text_frame(tf)
    paragraph.text = component.text
    bold = component.emphasis == "bold"
    apply_idino_text_style(
        paragraph,
        font_size=FONT_SIZE_PARAGRAPH,
        bold=bold,
        color=IDINO_TEXT,
        alignment=PP_ALIGN.LEFT,
    )

    # italic 은 style 헬퍼가 지원하지 않으므로 여기서 run 에 직접 적용.
    if component.emphasis == "italic":
        for run in paragraph.runs:
            run.font.italic = True

    return resolved_top + est_height + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 4. BulletList
# ---------------------------------------------------------------------------


def _format_bullet_prefix(index: int, numbered: bool) -> str:
    """bullet glyph prefix 문자열 생성.

    numbered=True → "1. ", "2. " / False → "• ".
    """
    if numbered:
        return f"{index + 1}. "
    return f"{BULLET_GLYPH_UNORDERED} "


def _draw_highlight_backgrounds(
    *,
    component: BulletListComponent,
    slide: Slide,
    left_in: float,
    top_in: float,
    width_in: float,
    bullet_line_h_in: float,
    sub_line_h_in: float,
) -> int:
    """D9-d — BulletList 중 ``emphasis="highlight"`` item 뒤에 배경 박스 배치.

    python-pptx 의 ``TextFrame`` 은 per-paragraph 배경 fill 을 지원하지 않는다.
    대안으로 **bullet 텍스트박스가 추가되기 전** 같은 Y 위치에 옅은 주황
    (``HIGHLIGHT_BG_COLOR``) 사각형 shape 를 깔고, 텍스트박스가 그 위에 얹힌다
    (z-order 는 add 순서로 결정됨).

    좌표 추정:
      - 각 bullet item 은 1 줄 + sub_items * 1 줄 로 근사 (word_wrap 으로 실제
        줄 수는 달라질 수 있으나, highlight 는 짧은 강조 문구가 대부분이므로
        ±1 ~2pt 오차 허용).
      - 첫 item Y = top_in. item_idx 가 증가할 때마다 이전 item 의 bullet + sub
        높이만큼 누적.

    Args:
        component: BulletListComponent.
        slide: python-pptx Slide.
        left_in / top_in / width_in: bullet 텍스트박스 전체 좌표.
        bullet_line_h_in: bullet 한 줄 높이 (인치).
        sub_line_h_in: sub_items 한 줄 높이 (인치).

    Returns:
        배치된 highlight 배경 박스의 개수 (테스트 검증 용).
    """
    # MSO_SHAPE 는 오직 highlight 가 있을 때만 import 해 불필요한 의존을 줄인다.
    # 먼저 highlight 존재 여부 확인.
    has_highlight = any(item.emphasis == "highlight" for item in component.items)
    if not has_highlight:
        return 0

    from pptx.enum.shapes import MSO_SHAPE

    drawn = 0
    # 현재 item 이 위치할 Y 를 선형 누적.
    current_y = top_in
    for item in component.items:
        if item.emphasis == "highlight":
            # 배경 박스를 bullet 라인 높이만큼 그린다. 위·아래 padding 추가.
            bg_top = current_y - HIGHLIGHT_BG_VERTICAL_PADDING_IN
            bg_height = bullet_line_h_in + 2 * HIGHLIGHT_BG_VERTICAL_PADDING_IN
            bg_shape = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(left_in),
                Inches(max(0.0, bg_top)),
                Inches(width_in),
                Inches(bg_height),
            )
            # 파스텔 톤 배경 + 외곽선 없음 (과도한 UI 효과 방지).
            _apply_shape_solid_fill(bg_shape, HIGHLIGHT_BG_COLOR)
            bg_shape.line.fill.background()
            drawn += 1

        # 다음 item 의 Y 로 진행: bullet 1 줄 + sub 개수만큼.
        current_y += bullet_line_h_in + sub_line_h_in * len(item.sub_items)

    return drawn


def render_bullet_list(
    component: BulletListComponent,
    slide: Slide,
    top_in: float | None = None,
) -> float:
    """불릿/번호 목록을 배치한다.

    각 `BulletItem` 은 하나의 paragraph. sub_items 가 있으면 같은 textbox 내
    추가 paragraph 로 들여쓰기 + 보조 glyph("◦") 로 삽입.

    emphasis 매핑 (D9-d 업데이트):
      - "normal"    → 일반 굵기(400), 기본 text 색
      - "bold"      → 굵게(700), 기본 text 색
      - "highlight" → 굵게(700), IDINO accent 색 **+ 옅은 배경 하이라이트 박스**.
                       python-pptx 는 per-paragraph 배경 fill 을 지원하지 않으므로,
                       bullet 텍스트박스 **뒤에** ``MSO_SHAPE.RECTANGLE`` 을 해당
                       라인 Y 좌표에 깔아 FE 의 background 효과를 근사한다.
                       색은 ``HIGHLIGHT_BG_COLOR`` (#FFF4ED, 파스텔 톤).
                       배경 박스는 z-order 상 텍스트박스보다 먼저 add 되어 뒤에
                       놓인다.

    Args:
        component: `BulletListComponent` (items: 1~12 개, numbered: bool).
        slide: python-pptx Slide.
        top_in: 시작 Y 좌표 (인치). None 이면 본문 기본 Y.

    Returns:
        컴포넌트 바닥 Y 좌표.
    """
    resolved_top = top_in if top_in is not None else BODY_TOP_IN

    # 박스 높이 추정: 각 item 1 줄 + sub_items 줄 수 합산.
    total_lines = 0
    for item in component.items:
        total_lines += 1
        total_lines += len(item.sub_items)
    pt_per_line = FONT_SIZE_BULLET * 1.4
    est_height = max(0.8, (total_lines * pt_per_line) / 72.0 + 0.2)

    # D9-d — highlight 배경 박스를 textbox 앞에 선 배치한다 (z-order 뒤).
    # python-pptx 는 add 순서대로 z-order 가 쌓이므로, 반드시 textbox add 이전에
    # 배경 shape 를 추가해야 텍스트가 위로 올라온다. 각 item 의 Y 위치는
    # 선형 누적으로 추정 — 정밀한 렌더러 한줄 높이 계산은 python-pptx 에서
    # 불가능하므로 ±1~2pt 오차 허용.
    bullet_line_h_in = (FONT_SIZE_BULLET * 1.4) / 72.0
    sub_line_h_in = (FONT_SIZE_BULLET_SUB * 1.4) / 72.0
    _draw_highlight_backgrounds(
        component=component,
        slide=slide,
        left_in=BODY_LEFT_IN,
        top_in=resolved_top,
        width_in=BODY_WIDTH_IN,
        bullet_line_h_in=bullet_line_h_in,
        sub_line_h_in=sub_line_h_in,
    )

    shape = _add_textbox_at(
        slide,
        left_in=BODY_LEFT_IN,
        top_in=resolved_top,
        width_in=BODY_WIDTH_IN,
        height_in=est_height,
    )
    tf = shape.text_frame
    tf.word_wrap = True
    # 배경 하이라이트가 뒤에 깔릴 때 텍스트박스 자체 배경은 투명해야 색이 보인다.
    # python-pptx 의 textbox 는 기본 배경이 투명(no fill) 이므로 별도 조치 불필요.

    # 첫 paragraph 는 reset_text_frame 으로 가져오고, 이후 paragraph 는
    # `tf.add_paragraph()` 로 덧붙임. 각 paragraph 에 스타일 개별 적용.
    first_paragraph = reset_text_frame(tf)
    first_rendered = False

    for idx, item in enumerate(component.items):
        # 메인 항목 paragraph.
        prefix = _format_bullet_prefix(idx, component.numbered)
        main_text = f"{prefix}{item.text}"
        # 첫 item 은 이미 존재하는 첫 paragraph 에 쓴다.
        if not first_rendered:
            para = first_paragraph
            first_rendered = True
        else:
            para = tf.add_paragraph()
        para.text = main_text
        # emphasis="bold" 또는 "highlight" 는 굵게. "normal" 은 400.
        main_bold = item.emphasis in ("bold", "highlight")
        # highlight 는 accent 색 + bold 로 텍스트 강조 (배경 박스는 별도 레이어).
        main_color = IDINO_ACCENT if item.emphasis == "highlight" else IDINO_TEXT
        apply_idino_text_style(
            para,
            font_size=FONT_SIZE_BULLET,
            bold=main_bold,
            color=main_color,
            alignment=PP_ALIGN.LEFT,
        )

        # 서브 항목들 — 들여쓰기 4 칸 + "◦ " prefix.
        for sub in item.sub_items:
            sub_para = tf.add_paragraph()
            sub_para.text = f"    {BULLET_GLYPH_SUB} {sub}"
            apply_idino_text_style(
                sub_para,
                font_size=FONT_SIZE_BULLET_SUB,
                bold=False,
                color=IDINO_TEXT,
                alignment=PP_ALIGN.LEFT,
            )

    return resolved_top + est_height + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 5. KPI (D3)
# ---------------------------------------------------------------------------


def _resolve_kpi_delta_color(component: KPIComponent) -> str:
    """KPI.delta + delta_direction → hex 색 문자열로 변환.

    우선순위:
      1) `delta_direction` 필드가 명시되어 있으면 그대로 사용 ("up"/"down"/"flat").
      2) 필드가 None 이지만 `delta` 가 있으면 첫 문자("+"/"-") 로 자동 감지.
      3) 전부 없으면 muted 색 반환 — 호출부는 delta 미렌더를 판단할 것.
    """
    direction = component.delta_direction
    if direction is None and component.delta:
        stripped = component.delta.strip()
        if stripped.startswith("+"):
            direction = "up"
        elif stripped.startswith("-"):
            direction = "down"
        else:
            direction = "flat"

    if direction == "up":
        return KPI_DELTA_UP_COLOR
    if direction == "down":
        return KPI_DELTA_DOWN_COLOR
    return KPI_DELTA_FLAT_COLOR


def _apply_shape_solid_fill(shape: object, hex_color: str) -> None:
    """도형에 solid fill 을 적용하는 공용 헬퍼.

    python-pptx 의 shape.fill 속성은 런타임에 AutoShape/TextBox 에서 동일
    하게 동작하나, 타입 힌트 상 명시하기 어려워 `object` 로 받는다.
    """
    # type: ignore[attr-defined] — 런타임 shape 는 fill.solid() / fill.fore_color 지원.
    fill = shape.fill  # type: ignore[attr-defined]
    fill.solid()
    fill.fore_color.rgb = parse_hex_color(hex_color)


def render_kpi(
    component: KPIComponent,
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float | None = None,
    show_box_bg: bool = False,
) -> float:
    """단일 KPI 카드를 지정 좌표에 배치한다.

    구조:
        ┌────────────────────────┐
        │        label (상)        │  ← 12pt muted color
        │     ┌──────────┐       │
        │     │  value   │  중앙  │  ← 36pt IDINO_PRIMARY bold
        │     └──────────┘       │
        │    ▲ delta (하) ▼       │  ← 12pt 부호별 색 (green/red/gray)
        └────────────────────────┘

    **IDINO 색상 정책 (D9-c 에서 문서화)**:

    이 정책은 `constants.py` 의 IDINO 팔레트를 KPI 전용 관점에서 재정리한 것이다.
    리포트 전체에서 색 통일성을 유지하기 위해 반드시 이 매핑만 사용한다.

    - **value** (큰 숫자, 36pt): 항상 ``IDINO_PRIMARY`` (#0A4FC2) + bold.
      이유: 주목도가 최고 — 슬라이드 내 단일 지표가 가장 먼저 눈에 들어와야 함.
    - **label** (상단, 12pt): 항상 ``IDINO_TEXT_MUTED`` (#6B7280).
      이유: value 의 보조 설명이므로 대비를 낮춰 value 가 돋보이게 함.
    - **delta** (하단, 12pt): ``delta_direction`` 또는 ``delta`` 부호에 따라
      3 색 중 하나로 **한정**. 다른 색은 허용하지 않는다.
        - up   → ``KPI_DELTA_UP_COLOR``   (#10B981, 녹색)
        - down → ``KPI_DELTA_DOWN_COLOR`` (#EF4444, 적색)
        - flat → ``KPI_DELTA_FLAT_COLOR`` (= ``IDINO_TEXT_MUTED``, 회색)

    **Accent (#FF6B35) 의 허용 범위**:
      - KPI 3 요소(value/label/delta) 에서는 **사용 금지**. delta 색은 위 3 색만.
      - accent 는 BulletList highlight / Callout 강조 등 "KPI 외" 영역 전용이다.
      - KPI 자체 배경(``show_box_bg=True``) 도 accent 대신 ``KPI_BOX_BG``
        (#F3F4F6, 연회색) 만 사용.

    이 정책을 벗어나는 색 지정 요청이 들어오면 별도 컴포넌트(Callout 등) 로
    분리해야 한다 — KPI 는 숫자 + 방향성 대시보드의 시각 일관성이 생명이다.

    Args:
        component: `KPIComponent` (label / value 필수, delta / delta_direction / description 선택).
        slide: python-pptx Slide.
        left_in: 카드 좌측 X (인치).
        top_in: 카드 상단 Y (인치).
        width_in: 카드 너비 (인치).
        height_in: 카드 높이 (인치). None 이면 KPI_CARD_HEIGHT_IN 사용.
        show_box_bg: True 면 옅은 회색 배경 박스를 추가. 기본 False (투명).

    Returns:
        카드 바닥 Y 좌표 (인치). 같은 Y 레벨에 여러 KPI 를 배치하는 경우 호출부
        는 반환값을 무시하고 자체 레이아웃 로직을 적용할 수 있다.
    """
    resolved_height = height_in if height_in is not None else KPI_CARD_HEIGHT_IN

    # (선택) 박스 배경 — 카드 전체 크기에 맞는 사각형.
    if show_box_bg:
        from pptx.enum.shapes import MSO_SHAPE

        bg_shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(left_in),
            Inches(top_in),
            Inches(width_in),
            Inches(resolved_height),
        )
        _apply_shape_solid_fill(bg_shape, KPI_BOX_BG)
        # 배경 박스는 외곽선 없음 (시각적 과밀 방지).
        bg_shape.line.fill.background()
        # 배경 박스에는 텍스트를 넣지 않는다 (별도 textbox 로 오버레이).

    # 3 단 stack 좌표 계산.
    label_top = top_in
    value_top = label_top + KPI_LABEL_HEIGHT_IN
    delta_top = value_top + KPI_VALUE_HEIGHT_IN

    # (1) label — 상단, 12pt muted, center.
    label_shape = _add_textbox_at(
        slide,
        left_in=left_in,
        top_in=label_top,
        width_in=width_in,
        height_in=KPI_LABEL_HEIGHT_IN,
    )
    label_tf = label_shape.text_frame
    label_tf.word_wrap = True
    label_para = reset_text_frame(label_tf)
    label_para.text = component.label
    apply_idino_text_style(
        label_para,
        font_size=FONT_SIZE_KPI_LABEL,
        bold=False,
        color=IDINO_TEXT_MUTED,
        alignment=PP_ALIGN.CENTER,
    )

    # (2) value — 중앙, 36pt IDINO_PRIMARY bold, center.
    value_shape = _add_textbox_at(
        slide,
        left_in=left_in,
        top_in=value_top,
        width_in=width_in,
        height_in=KPI_VALUE_HEIGHT_IN,
    )
    value_tf = value_shape.text_frame
    value_tf.word_wrap = True
    value_para = reset_text_frame(value_tf)
    value_para.text = component.value
    apply_idino_text_style(
        value_para,
        font_size=FONT_SIZE_KPI_VALUE,
        bold=True,
        color=IDINO_PRIMARY,
        alignment=PP_ALIGN.CENTER,
    )

    # (3) delta — 하단, 12pt 부호별 색. delta 값이 없으면 skip.
    if component.delta:
        delta_color = _resolve_kpi_delta_color(component)
        delta_shape = _add_textbox_at(
            slide,
            left_in=left_in,
            top_in=delta_top,
            width_in=width_in,
            height_in=KPI_DELTA_HEIGHT_IN,
        )
        delta_tf = delta_shape.text_frame
        delta_tf.word_wrap = True
        delta_para = reset_text_frame(delta_tf)
        delta_para.text = component.delta
        apply_idino_text_style(
            delta_para,
            font_size=FONT_SIZE_KPI_DELTA,
            bold=True,
            color=delta_color,
            alignment=PP_ALIGN.CENTER,
        )

    return top_in + resolved_height + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 6. DataTable (D3)
# ---------------------------------------------------------------------------


def _is_numeric_cell(value: str) -> bool:
    """문자열 셀이 숫자형인지 판정 (우측 정렬 결정용).

    기준:
      - 앞뒤 공백 제거 후 부호 옵션 + 숫자 + 옵션 소수점 + 옵션 콤마 + 옵션 % 기호.
      - "1,234", "99.5", "-12", "3.14%", "₩1,234" 모두 숫자로 간주.
      - "N/A", "-" (단독), 빈 문자열은 텍스트로 간주.
    """
    if value is None:
        return False
    s = str(value).strip()
    if not s:
        return False
    # 통화 기호·퍼센트·콤마 제거 후 float 변환 시도.
    cleaned = s.replace(",", "").replace("%", "").replace("₩", "").replace("$", "")
    if cleaned in {"", "-", "+"}:
        return False
    try:
        float(cleaned)
    except ValueError:
        return False
    return True


def _set_cell_bg(cell: object, hex_color: str) -> None:
    """테이블 셀의 배경색을 설정한다.

    python-pptx 는 `cell.fill.solid()` 를 지원하나, 미세한 양식 이슈로 OOXML
    조작을 선호하는 경우가 있다. 본 헬퍼는 고수준 API 를 그대로 사용 (기존
    report_generator.py `_set_cell_bg` 는 lxml 직접 조작이었으나, 여기선
    단순 solid() 경로가 충분히 동작).
    """
    fill = cell.fill  # type: ignore[attr-defined]
    fill.solid()
    fill.fore_color.rgb = parse_hex_color(hex_color)


def _style_table_cell(
    cell: object,
    text: str,
    *,
    font_size: int,
    bold: bool,
    color_hex: str,
    alignment: PP_ALIGN,
    bg_hex: str | None = None,
) -> None:
    """테이블 셀 하나에 텍스트·폰트·배경·정렬을 일괄 적용.

    python-pptx 는 cell.text 대입 시 기존 paragraph 가 유지되지만 run 이 재생성
    되므로 스타일 적용 타이밍이 중요하다. 본 헬퍼는 (1) text 설정 → (2) paragraph
    스타일 → (3) 배경 순으로 처리한다.
    """
    # type: ignore[attr-defined] — 런타임 cell 객체는 text / text_frame 지원.
    cell.text = text  # type: ignore[attr-defined]

    # paragraph 는 1 개 이상 보장 (text 설정 이후).
    for paragraph in cell.text_frame.paragraphs:  # type: ignore[attr-defined]
        paragraph.alignment = alignment
        for run in paragraph.runs:
            run.font.name = DEFAULT_FONT
            run.font.size = Pt(font_size)
            run.font.bold = bold
            run.font.color.rgb = parse_hex_color(color_hex)

    if bg_hex is not None:
        _set_cell_bg(cell, bg_hex)


def render_data_table(
    component: DataTableComponent,
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
) -> float:
    """DataTable 을 IDINO 스타일로 렌더한다.

    스타일 규칙:
      - 헤더 행: IDINO_HEADER_NAVY (#34495E) 배경 + 흰색 볼드 11pt, center 정렬.
      - 데이터 행: 홀수 행 흰색, 짝수 행 연회색 제브라, 10pt.
      - 셀 정렬: 값이 숫자면 우측, 아니면 좌측.
      - 행 수가 TABLE_MAX_DISPLAY_ROWS 초과 시 말미 "..." 행으로 축약 + 경고 로그.

    Args:
        component: `DataTableComponent` (headers + rows).
        slide: python-pptx Slide.
        left_in: 테이블 좌측 X (인치).
        top_in: 테이블 상단 Y (인치).
        width_in: 테이블 너비 (인치). 열 너비는 균등 분할.

    Returns:
        테이블 바닥 Y 좌표 (인치).
    """
    headers = component.headers
    rows = component.rows
    col_count = len(headers)

    # 행 truncation — 표시 가능 행 수 초과 시 말미 "..." 로 축약.
    truncated = False
    if len(rows) > TABLE_MAX_DISPLAY_ROWS:
        logger.warning(
            "PptxBuilder: DataTable rows %d 개가 최대 표시 %d 를 초과 — 축약합니다.",
            len(rows),
            TABLE_MAX_DISPLAY_ROWS,
        )
        visible_rows: list[list[str]] = list(rows[: TABLE_MAX_DISPLAY_ROWS - 1])
        # 말미 "..." 행: 첫 셀에만 "...", 나머지는 빈 문자열.
        ellipsis_row = ["..."] + [""] * (col_count - 1)
        visible_rows.append(ellipsis_row)
        truncated = True
    else:
        visible_rows = list(rows)

    row_count = len(visible_rows) + 1  # 헤더 1 행 포함.
    total_height_in = TABLE_ROW_HEIGHT_IN * row_count

    # python-pptx add_table — 좌표는 EMU. 호출부는 인치로 전달 받음.
    table_shape = slide.shapes.add_table(
        row_count,
        col_count,
        Inches(left_in),
        Inches(top_in),
        Inches(width_in),
        Inches(total_height_in),
    )
    table = table_shape.table

    # ── 헤더 행 ──
    for col_idx, header_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        _style_table_cell(
            cell,
            str(header_text),
            font_size=FONT_SIZE_TABLE_HEADER,
            bold=True,
            color_hex=IDINO_WHITE,
            alignment=PP_ALIGN.CENTER,
            bg_hex=IDINO_HEADER_NAVY,
        )

    # ── 데이터 행 ──
    for row_idx, row_data in enumerate(visible_rows):
        # 제브라: 짝수 행(1-indexed) → 연회색. 데이터 1 행째(row_idx=0) 는 흰색.
        is_zebra = (row_idx % 2) == 1
        bg_for_row = TABLE_ZEBRA_ROW_BG if is_zebra else IDINO_WHITE

        for col_idx in range(col_count):
            cell = table.cell(row_idx + 1, col_idx)
            # row_data 길이는 Pydantic 에서 headers 와 동일함이 이미 보장됨.
            # 축약 행은 col_count 만큼 미리 채워뒀으므로 안전.
            value = row_data[col_idx] if col_idx < len(row_data) else ""

            # 숫자 셀은 우측, 텍스트는 좌측 정렬. 축약 "..." 행은 좌측 유지.
            is_numeric = _is_numeric_cell(value) if not truncated or row_idx < len(visible_rows) - 1 else False
            alignment = PP_ALIGN.RIGHT if is_numeric else PP_ALIGN.LEFT

            _style_table_cell(
                cell,
                str(value),
                font_size=FONT_SIZE_TABLE_CELL,
                bold=False,
                color_hex=IDINO_TEXT,
                alignment=alignment,
                bg_hex=bg_for_row,
            )

    # 셀 테두리: python-pptx 가 기본 tbl border 를 자동 생성하므로 특별히 추가
    # 작업은 하지 않는다 — TABLE_BORDER_COLOR 는 향후 xml 직접 조작으로 확장.
    _ = TABLE_BORDER_COLOR  # 상수 사용 표시 (향후 확장 자리).

    return top_in + total_height_in + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 7. Image (D6)
# ---------------------------------------------------------------------------


def _detect_image_aspect_ratio(image_stream: BytesIO) -> float:
    """BytesIO 에 담긴 이미지의 (width / height) 비율을 감지한다.

    python-pptx 의 add_picture() 는 width/height 둘 중 하나만 지정해도 나머지를
    자동 계산하지만, Y 스택 관리를 위해 사전에 높이를 알아야 한다. PIL 이 설치돼
    있으면 사용하고, 없으면 fallback 비율(4:3) 을 반환한다.

    Args:
        image_stream: BytesIO — stream 위치는 0 이어야 한다. 호출 후 0 으로 리셋됨.

    Returns:
        (width / height) float. 감지 실패 시 IMAGE_FALLBACK_ASPECT_RATIO.
    """
    # Pillow 는 python-pptx 의 전이 의존성이라 항상 사용 가능하지만,
    # import 실패를 우아하게 처리해 환경 이슈에도 견고하게 동작.
    try:
        from PIL import Image as PILImage  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover — 환경 이슈 안전망.
        logger.debug("Pillow 미설치 — 이미지 aspect ratio fallback 사용.")
        image_stream.seek(0)
        return IMAGE_FALLBACK_ASPECT_RATIO

    try:
        image_stream.seek(0)
        with PILImage.open(image_stream) as img:
            width, height = img.size
            if height <= 0:
                raise ValueError("이미지 height 가 0 이하입니다.")
            ratio = width / height
    except Exception as exc:  # Pillow 가 raise 하는 다양한 예외 포괄.
        logger.warning("이미지 aspect ratio 감지 실패 — fallback 4:3 사용: %s", exc)
        ratio = IMAGE_FALLBACK_ASPECT_RATIO
    finally:
        image_stream.seek(0)
    return ratio


def _render_image_placeholder(
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float,
    alt_text: str,
) -> None:
    """fetch 실패 시 회색 박스 + alt 텍스트 placeholder 렌더.

    빌드 자체를 실패시키지 않고 사용자에게 "여기에 이미지가 들어갔어야 한다" 는
    신호를 남긴다. 박스 위에 작은 기울임 텍스트로 alt 를 노출.
    """
    # Import 를 함수 내부로 — pptx.enum.shapes 는 KPI 경로에서도 같은 패턴.
    from pptx.enum.shapes import MSO_SHAPE

    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left_in),
        Inches(top_in),
        Inches(width_in),
        Inches(height_in),
    )
    # 배경만 채우고 외곽선은 제거 (KPI _apply_shape_solid_fill 패턴 재사용).
    fill = bg_shape.fill  # type: ignore[attr-defined]
    fill.solid()
    fill.fore_color.rgb = parse_hex_color(IMAGE_PLACEHOLDER_BG)
    bg_shape.line.fill.background()  # type: ignore[attr-defined]

    # 박스 위에 alt 문구를 중앙 정렬로 표시 (단독 textbox 로 오버레이).
    label_shape = _add_textbox_at(
        slide,
        left_in=left_in,
        top_in=top_in,
        width_in=width_in,
        height_in=height_in,
    )
    tf = label_shape.text_frame
    tf.word_wrap = True
    paragraph = reset_text_frame(tf)
    paragraph.text = f"[이미지 없음] {alt_text}"
    apply_idino_text_style(
        paragraph,
        font_size=FONT_SIZE_IMAGE_CAPTION,
        bold=False,
        color=IDINO_TEXT_MUTED,
        alignment=PP_ALIGN.CENTER,
    )
    # italic 추가 — placeholder 상태임을 시각적으로 표시.
    for run in paragraph.runs:
        run.font.italic = True


def _set_picture_alt_text(picture_shape: object, alt: str) -> None:
    """python-pptx Picture 의 accessibility descr(=alt text) 을 설정.

    python-pptx 는 alt 전용 공식 setter 를 노출하지 않아 내부 XML 의 `descr`
    속성을 직접 설정한다. 실패해도 렌더러가 중단되면 안 되므로 예외는 삼키고
    debug 로그만 남긴다 (접근성은 필수 기능이 아닌 보완적 향상).
    """
    try:
        # _element 는 CT_Picture (nvPicPr/cNvPr 노드 보유).
        cnv_pr = picture_shape._element.nvPicPr.cNvPr  # type: ignore[attr-defined]
        cnv_pr.set("descr", alt)
    except Exception:  # pragma: no cover — alt 설정 실패는 빌드 실패가 아님.
        logger.debug("Picture alt text(descr) 설정 실패 — 무시.", exc_info=True)


def render_image(
    component: ImageComponent,
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    max_height_in: float,
) -> float:
    """Image 컴포넌트를 슬라이드에 삽입한다 (Phase 4 S2 D6).

    동작 순서:
        1) `component.src` 가 없으면(= prompt 만) 즉시 placeholder 렌더.
           이미지 자동 생성은 S3 범위 — D6 은 수동 source 만 처리.
        2) `fetch_image_bytes()` 로 BytesIO 확보 (URL / base64 / MinIO 분기).
        3) 원본 비율(width/height) 을 감지 → 요청 width 에 대한 height 계산.
        4) 계산된 height 가 `max_height_in` 을 초과하면 height 를 cap 하고
           동일 비율로 width 를 재계산 (수평 방향으로 축소).
        5) `slide.shapes.add_picture()` 로 삽입, alt 텍스트를 XML descr 에 설정.
        6) caption 이 있으면 이미지 바로 아래에 10pt italic 텍스트로 배치.
        7) fetch 실패 등 예외는 placeholder 로 degrade → 빌드는 계속 진행.

    Args:
        component: ImageComponent 인스턴스 (src 또는 prompt 중 하나 이상 존재).
        slide: python-pptx Slide.
        left_in: 이미지 좌측 X (인치).
        top_in: 이미지 상단 Y (인치).
        width_in: 요청 너비 (인치). 원본 비율 유지를 위해 height 는 자동 계산.
        max_height_in: 남은 슬라이드 영역 기반의 높이 상한 (인치). 이미지 + caption
            의 합이 이 값을 초과하지 않도록 렌더러가 조정한다.

    Returns:
        이미지(+ caption) 바닥 Y 좌표 (인치). 호출부가 다음 컴포넌트 top 으로 사용.
    """
    # 0) 안전값 — 음수/0 방지. 방어적 코드이지만 builder 쪽 계산 오류가 있으면
    #    placeholder 라도 최소 크기를 보장한다.
    safe_width = max(0.5, width_in)
    safe_max_height = max(0.5, max_height_in)

    # caption 이 있으면 이미지가 쓸 수 있는 최대 높이에서 caption 높이를 미리 차감.
    has_caption = bool(component.caption and component.caption.strip())
    image_max_height = safe_max_height - (IMAGE_CAPTION_HEIGHT_IN if has_caption else 0.0)
    image_max_height = max(0.5, image_max_height)

    # 1) src 부재 시(= prompt 만) placeholder 즉시 렌더.
    #    실제 이미지 자동 생성(DALL-E/Unsplash) 은 S3 범위.
    if not component.src:
        logger.info(
            "render_image: src 미지정(prompt 전용) — D6 범위 외, placeholder 로 degrade (alt=%r).",
            component.alt,
        )
        ph_height = min(IMAGE_PLACEHOLDER_HEIGHT_IN, image_max_height)
        ph_width = min(IMAGE_PLACEHOLDER_WIDTH_IN, safe_width)
        _render_image_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=ph_width,
            height_in=ph_height,
            alt_text=component.alt,
        )
        # caption 이 있으면 동일하게 아래에 배치.
        total_height = ph_height
        if has_caption:
            total_height += _render_image_caption(
                slide,
                caption=component.caption or "",
                left_in=left_in,
                top_in=top_in + ph_height,
                width_in=ph_width,
            )
        return top_in + total_height + COMPONENT_VERTICAL_GAP_IN

    # 2) 이미지 bytes 확보.
    try:
        image_stream = fetch_image_bytes(component.src)
    except ImageFetchError as exc:
        logger.warning(
            "render_image: 이미지 fetch 실패 — placeholder 로 degrade (src=%r, alt=%r): %s",
            component.src,
            component.alt,
            exc,
        )
        ph_height = min(IMAGE_PLACEHOLDER_HEIGHT_IN, image_max_height)
        ph_width = min(IMAGE_PLACEHOLDER_WIDTH_IN, safe_width)
        _render_image_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=ph_width,
            height_in=ph_height,
            alt_text=component.alt,
        )
        total_height = ph_height
        if has_caption:
            total_height += _render_image_caption(
                slide,
                caption=component.caption or "",
                left_in=left_in,
                top_in=top_in + ph_height,
                width_in=ph_width,
            )
        return top_in + total_height + COMPONENT_VERTICAL_GAP_IN

    # 3) aspect ratio 기반 높이 계산. PIL 없으면 fallback 4:3.
    aspect_ratio = _detect_image_aspect_ratio(image_stream)
    computed_height = safe_width / aspect_ratio

    # 4) 높이 상한 체크 — 초과 시 width 축소.
    final_width = safe_width
    final_height = computed_height
    if final_height > image_max_height:
        final_height = image_max_height
        final_width = final_height * aspect_ratio

    # 5) add_picture — python-pptx 는 width 와 height 둘 다 주면 해당 크기로 강제 삽입.
    try:
        picture = slide.shapes.add_picture(
            image_stream,
            Inches(left_in),
            Inches(top_in),
            width=Inches(final_width),
            height=Inches(final_height),
        )
    except Exception as exc:
        # add_picture 자체가 실패 (손상된 이미지, 지원하지 않는 포맷 등).
        logger.warning(
            "render_image: add_picture 실패 — placeholder 로 degrade (src=%r): %s",
            component.src,
            exc,
        )
        ph_height = min(IMAGE_PLACEHOLDER_HEIGHT_IN, image_max_height)
        ph_width = min(IMAGE_PLACEHOLDER_WIDTH_IN, safe_width)
        _render_image_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=ph_width,
            height_in=ph_height,
            alt_text=component.alt,
        )
        total_height = ph_height
        if has_caption:
            total_height += _render_image_caption(
                slide,
                caption=component.caption or "",
                left_in=left_in,
                top_in=top_in + ph_height,
                width_in=ph_width,
            )
        return top_in + total_height + COMPONENT_VERTICAL_GAP_IN

    # alt text (접근성) 설정.
    _set_picture_alt_text(picture, component.alt)

    # 6) caption — 이미지 바로 아래 10pt italic muted 색.
    used_height = final_height
    if has_caption:
        used_height += _render_image_caption(
            slide,
            caption=component.caption or "",
            left_in=left_in,
            top_in=top_in + final_height,
            width_in=final_width,
        )

    return top_in + used_height + COMPONENT_VERTICAL_GAP_IN


def _render_image_caption(
    slide: Slide,
    *,
    caption: str,
    left_in: float,
    top_in: float,
    width_in: float,
) -> float:
    """이미지 하단 caption 텍스트 박스를 렌더.

    10pt italic IDINO_TEXT_MUTED 색 + 중앙 정렬. caption 영역 자체는 고정 높이
    (IMAGE_CAPTION_HEIGHT_IN). 본 함수는 사용한 높이(인치) 를 반환 → 호출부가
    Y 누적에 사용.
    """
    caption_shape = _add_textbox_at(
        slide,
        left_in=left_in,
        top_in=top_in,
        width_in=width_in,
        height_in=IMAGE_CAPTION_HEIGHT_IN,
    )
    tf = caption_shape.text_frame
    tf.word_wrap = True
    paragraph = reset_text_frame(tf)
    paragraph.text = caption
    apply_idino_text_style(
        paragraph,
        font_size=FONT_SIZE_IMAGE_CAPTION,
        bold=False,
        color=IDINO_TEXT_MUTED,
        alignment=PP_ALIGN.CENTER,
    )
    # italic 은 style 헬퍼가 지원하지 않으므로 run 단위로 직접 적용.
    for run in paragraph.runs:
        run.font.italic = True

    return IMAGE_CAPTION_HEIGHT_IN


# ---------------------------------------------------------------------------
# 8. Chart (D7)
# ---------------------------------------------------------------------------
#
# PPTX native 차트(= OOXML `<c:chart>`) 를 `python-pptx` 의 `CategoryChartData`
# + `XL_CHART_TYPE` 경유로 삽입한다. D7 범위는 **bar / line 만** 공식 지원하며
# pie 는 본 플래그십 로드맵의 S3 범위 — 본 구현에선 bar 로 graceful-degrade.
# 스키마가 `Literal["bar", "line", "pie"]` 로 pie 를 허용하므로 빌드 파이프라인
# 을 깨뜨리지 않기 위해 WARN 로그 + fallback 을 수행한다.
#
# 설계 판단 포인트:
#   - 차트 type → XL_CHART_TYPE 매핑은 모듈 상수가 아닌 함수 내부 dict 로 관리.
#     외부 재사용 필요가 낮고, pie 등 "선언은 있지만 아직 native 미지원" 인 값의
#     정책이 변동 가능하기 때문.
#   - 시리즈 색상은 `CHART_SERIES_PALETTE` 를 modulo 순환 — 스키마가 series 를
#     max 6 개로 제한하지만 팔레트는 8 개라 여유가 있다.
#   - bar(column_clustered) 는 fill.fore_color 로, line 은 line.color 로 색상
#     적용 채널이 다르다 — 내부 헬퍼에서 타입별 분기.
#   - placeholder 경로는 이미지의 `_render_image_placeholder` 와 유사한 회색
#     박스 + 안내 문구. 안내 문구는 alt 대신 component.title 을 사용 (차트엔
#     alt 필드가 없음).


# chart_type 문자열 → XL_CHART_TYPE 매핑.
#
# S3 D1 업데이트: constants.CHART_XL_TYPE_NAME_BY_ALIAS 를 단일 소스로 재사용해
# 중복을 제거. 본 모듈 상수로 `CHART_XL_TYPE_NAME_BY_ALIAS` 를 재노출하는 대신
# alias 역할의 별칭만 유지 (하위 호환).
_CHART_TYPE_ALIAS: Final[dict[str, str]] = dict(CHART_XL_TYPE_NAME_BY_ALIAS)


# pie/doughnut 계열은 카테고리축/값축 개념이 없어 `_style_chart_axes()` 가
# 무의미하며, 스키마상 단일 시리즈 개념만 시각적으로 의미 있다.
_CHART_TYPES_WITHOUT_AXES: Final[frozenset[str]] = frozenset({"pie", "doughnut"})

# 기본 축 스타일이 필요한 타입들 (bar/column/line/area/stacked_*).
# pie 만 제외되는 현재 스키마에서는 "그 외 전부" 를 뜻하지만, 명시적 리스트로
# 유지해 향후 radar/scatter 등 축 없음 차트가 추가될 때 회귀 방지.
_CHART_TYPES_WITH_AXES: Final[frozenset[str]] = frozenset(
    {
        "bar",
        "column",
        "line",
        "area",
        "stacked_bar",
        "stacked_column",
        "stacked_area",
    }
)


def _resolve_xl_chart_type(chart_type: str) -> tuple[object, bool]:
    """스키마 `chart_type` 문자열을 python-pptx `XL_CHART_TYPE` enum 으로 변환.

    S3 D1 기준 **native 지원 범위**:
      - bar / column → COLUMN_CLUSTERED
      - line → LINE
      - pie → PIE (S3 승격, 이전엔 bar fallback)
      - area / stacked_bar / stacked_column / stacked_area → alias 등록돼 있으나
        현재 스키마 Literal 이 ["bar", "line", "pie"] 로 제한되어 있어 실제
        호출 경로는 열리지 않는다. 스키마 확장 시 무수정 승격 목적의 예비 매핑.

    Returns:
        (xl_chart_type, is_fallback) 튜플. is_fallback=True 면 스키마 요청 타입이
        지원되지 않아 bar 로 대체되었음을 의미.
    """
    from pptx.enum.chart import XL_CHART_TYPE  # integration layer 내 local import.

    key = (chart_type or "").strip().lower()
    alias = _CHART_TYPE_ALIAS.get(key)
    if alias is None:
        # 지원 외 타입 → fallback.
        fallback_alias = _CHART_TYPE_ALIAS[CHART_FALLBACK_TYPE]
        return getattr(XL_CHART_TYPE, fallback_alias), True
    # XL_CHART_TYPE 에 alias 가 존재하지 않는 환경 (초기 버전 python-pptx) 방어.
    xl_type = getattr(XL_CHART_TYPE, alias, None)
    if xl_type is None:
        logger.warning(
            "_resolve_xl_chart_type: XL_CHART_TYPE.%s 를 찾을 수 없음 — bar fallback.",
            alias,
        )
        fallback_alias = _CHART_TYPE_ALIAS[CHART_FALLBACK_TYPE]
        return getattr(XL_CHART_TYPE, fallback_alias), True
    return xl_type, False


def _coerce_numeric_values(raw_values: list[float]) -> list[float]:
    """시리즈의 숫자 값을 안전하게 float 로 변환.

    Pydantic 이 이미 `list[float]` 을 강제하므로 이 단계에서 대부분 통과하지만,
    방어적으로 비수치/None 값은 0.0 으로 치환해 chart_data 생성 단계의 예외를
    예방한다. `float("nan")` 은 add_series() 에서 OOXML 직렬화 시 문제를 일으키므로
    같이 0 처리.
    """
    import math

    safe: list[float] = []
    for v in raw_values:
        try:
            f = float(v)
            if math.isnan(f) or math.isinf(f):
                safe.append(0.0)
            else:
                safe.append(f)
        except (TypeError, ValueError):
            safe.append(0.0)
    return safe


def _truncate_categories_and_series(
    labels: list[str],
    series_pairs: list[tuple[str, list[float]]],
    max_categories: int,
) -> tuple[list[str], list[tuple[str, list[float]]]]:
    """카테고리 개수가 max 를 넘으면 상위 (max-1) 개 + "기타" 묶음으로 축약.

    "기타" 값은 나머지 카테고리 값들의 합계 (시리즈별 독립 sum). 시리즈 길이
    불일치는 이미 Pydantic 검증을 통과했으므로 여기서는 labels 와 동일 길이로
    가정하고 처리.

    Args:
        labels: 원본 카테고리 리스트.
        series_pairs: [(series_name, values)] — values 는 이미 float 로 정규화됨.
        max_categories: 허용 최대 카테고리 수 (>= 2).

    Returns:
        (축약 labels, 축약 series_pairs) 튜플. 길이 <= max_categories.
    """
    if len(labels) <= max_categories:
        return labels, series_pairs

    head_count = max(1, max_categories - 1)
    truncated_labels = list(labels[:head_count]) + [CHART_ETC_CATEGORY_LABEL]

    truncated_pairs: list[tuple[str, list[float]]] = []
    for name, values in series_pairs:
        head_values = list(values[:head_count])
        tail_sum = float(sum(values[head_count:]))
        truncated_pairs.append((name, head_values + [tail_sum]))

    logger.warning(
        "render_chart: categories %d 개가 최대 %d 초과 — 상위 %d 개 + '%s' 로 축약.",
        len(labels),
        max_categories,
        head_count,
        CHART_ETC_CATEGORY_LABEL,
    )
    return truncated_labels, truncated_pairs


def _apply_series_color(series: object, hex_color: str, is_line_chart: bool) -> None:
    """차트 시리즈 하나에 IDINO 팔레트 색상을 적용.

    python-pptx 의 color 적용 채널은 차트 타입별로 다르다:
      - bar/column/area: `series.format.fill.fore_color` (solid fill).
      - line           : `series.format.line.color` (선 색).

    pie 계열은 **시리즈 하나에 카테고리별로 색을 다르게** 적용해야 하므로 본
    함수 대신 `_apply_pie_data_point_colors()` 를 사용한다.

    둘 다 실패하면 WARN 로그만 남기고 진행 — 색상이 기본 파랑이 되는 것은
    렌더 실패가 아닌 시각적 degrade 이므로 빌드 전체를 깨뜨리지 않는다.
    """
    try:
        rgb = parse_hex_color(hex_color)
    except ValueError:  # pragma: no cover — CHART_SERIES_PALETTE 는 상수라 실제 경로 아님.
        logger.warning("_apply_series_color: 잘못된 hex 색상 — skip: %s", hex_color)
        return

    try:
        if is_line_chart:
            # type: ignore[attr-defined] — 런타임 series 객체는 format.line 지원.
            series.format.line.color.rgb = rgb  # type: ignore[attr-defined]
        else:
            # type: ignore[attr-defined] — bar/column/area 는 fill 경로.
            fill = series.format.fill  # type: ignore[attr-defined]
            fill.solid()
            fill.fore_color.rgb = rgb
    except Exception:  # pragma: no cover — 차트 구조 변동에도 렌더는 계속.
        logger.debug("_apply_series_color: 색 적용 실패 — 기본색 유지.", exc_info=True)


def _apply_pie_data_point_colors(series: object, palette: tuple[str, ...]) -> None:
    """Pie 시리즈의 각 카테고리(data point) 에 팔레트를 순환 적용.

    Pie 차트는 "시리즈 1 개 × 카테고리 N 개" 구조이므로 시리즈 전체를 한 색으로
    채우면 모든 조각이 동일색이 되어 정보 전달이 실패한다. python-pptx 는
    `series.points[i].format.fill` 을 통해 개별 포인트 색을 설정할 수 있다.

    설계 메모:
      - points iterable 은 일부 버전에서 lazy 평가되므로 list() 로 즉시 materialize.
      - 특정 data point 의 fill 설정이 실패해도 렌더 전체를 실패시키지 않는다.
    """
    try:
        points = list(series.points)  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        logger.debug("_apply_pie_data_point_colors: series.points 접근 실패.", exc_info=True)
        return

    palette_size = len(palette)
    for idx, point in enumerate(points):
        hex_color = palette[idx % palette_size]
        try:
            rgb = parse_hex_color(hex_color)
            fill = point.format.fill  # type: ignore[attr-defined]
            fill.solid()
            fill.fore_color.rgb = rgb
        except Exception:  # pragma: no cover — 일부 point 실패도 다른 point 는 계속.
            logger.debug("_apply_pie_data_point_colors: point[%d] 색 적용 실패.", idx, exc_info=True)


def _style_chart_axes(chart: object, x_label: str | None, y_label: str | None) -> None:
    """차트 축 폰트 크기를 IDINO 기본에 맞추고, 선택적으로 축 제목을 설정.

    python-pptx 의 `Axis.tick_labels.font` 는 존재하지만 일부 차트 타입에서는
    axis 자체가 없을 수 있다 (pie 등 — 현재 미지원이지만 방어). 접근 실패는
    debug 로그만 남긴다.

    Args:
        chart: python-pptx `Chart` 객체.
        x_label: X 축 제목 텍스트. None/빈 문자열이면 숨김.
        y_label: Y 축 제목 텍스트. None/빈 문자열이면 숨김.
    """
    for axis_attr, label_text in (("category_axis", x_label), ("value_axis", y_label)):
        try:
            axis = getattr(chart, axis_attr, None)
            if axis is None:
                continue
            # 눈금 라벨 폰트.
            try:
                axis.tick_labels.font.size = Pt(CHART_AXIS_FONT_PT)
                axis.tick_labels.font.name = DEFAULT_FONT
            except Exception:  # pragma: no cover — 일부 타입에서만 발생.
                logger.debug("_style_chart_axes: tick_labels 설정 실패 (%s)", axis_attr, exc_info=True)

            # 축 제목 표시 여부.
            if label_text and label_text.strip():
                try:
                    axis.has_title = True
                    axis.axis_title.text_frame.text = label_text
                    for paragraph in axis.axis_title.text_frame.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(CHART_AXIS_FONT_PT)
                            run.font.name = DEFAULT_FONT
                            run.font.color.rgb = parse_hex_color(IDINO_TEXT)
                except Exception:  # pragma: no cover
                    logger.debug("_style_chart_axes: 축 제목 설정 실패 (%s)", axis_attr, exc_info=True)
            else:
                # None 이면 명시적으로 축 제목 숨김. python-pptx 기본은 숨김이나
                # 방어적으로 False 세팅. 일부 축 타입은 has_title 속성이 없을 수 있어
                # contextlib.suppress 로 포괄.
                import contextlib

                with contextlib.suppress(Exception):  # pragma: no cover
                    axis.has_title = False
        except Exception:  # pragma: no cover
            logger.debug("_style_chart_axes: axis 접근 실패 (%s)", axis_attr, exc_info=True)


def _render_chart_placeholder(
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float,
    message: str,
) -> None:
    """차트 빌드 실패/빈 데이터 시 회색 박스 + 안내 문구 placeholder 를 렌더.

    `_render_image_placeholder` 와 동일 패턴 — 빌드를 실패시키지 않고 차트 위치에
    시각적 자리표시를 남긴다. message 는 차트 타이틀 또는 "[차트 데이터 없음]" 등.
    """
    from pptx.enum.shapes import MSO_SHAPE

    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left_in),
        Inches(top_in),
        Inches(width_in),
        Inches(height_in),
    )
    fill = bg_shape.fill  # type: ignore[attr-defined]
    fill.solid()
    fill.fore_color.rgb = parse_hex_color(IMAGE_PLACEHOLDER_BG)
    bg_shape.line.fill.background()  # type: ignore[attr-defined]

    # 안내 문구 textbox 를 박스 위에 오버레이.
    label_shape = _add_textbox_at(
        slide,
        left_in=left_in,
        top_in=top_in,
        width_in=width_in,
        height_in=height_in,
    )
    tf = label_shape.text_frame
    tf.word_wrap = True
    paragraph = reset_text_frame(tf)
    paragraph.text = message
    apply_idino_text_style(
        paragraph,
        font_size=FONT_SIZE_IMAGE_CAPTION,
        bold=False,
        color=IDINO_TEXT_MUTED,
        alignment=PP_ALIGN.CENTER,
    )
    for run in paragraph.runs:
        run.font.italic = True


def render_chart(
    component: ChartComponent,
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    max_height_in: float,
) -> float:
    """Chart 컴포넌트를 PPTX native 차트로 슬라이드에 삽입한다 (Phase 4 S2 D7).

    동작 순서:
        1) 데이터 유효성 검증 — labels 또는 series 가 비어있으면 placeholder 로 degrade.
           (Pydantic 이 min_length=1 을 보장하지만 방어적 체크 유지.)
        2) chart_type → XL_CHART_TYPE 매핑. pie 등 미지원은 bar 로 fallback + WARN.
        3) 시리즈 값을 float 로 정규화, labels 와 길이 맞춤 (Pydantic 검증 중복 방어).
        4) 카테고리 수가 CHART_MAX_CATEGORIES 초과면 상위 N-1 + "기타" 묶음으로 축약.
        5) `CategoryChartData` 구성 + `slide.shapes.add_chart()`.
        6) 시리즈별 색상을 CHART_SERIES_PALETTE modulo 순환으로 적용.
        7) 제목(component.title) 은 차트 상단에 표시. 14pt IDINO_TEXT bold.
        8) 범례: 시리즈 2 개 이상이면 BOTTOM, 1 개면 숨김.
        9) 축 라벨(x_label/y_label) 은 현재 스키마에 필드 없음 → 양쪽 None 으로 축 제목 숨김.
           (S3 에서 필드 추가 시 확장 포인트.)

    Args:
        component: `ChartComponent` 인스턴스 (chart_type/title/data 필수).
        slide: python-pptx Slide.
        left_in: 차트 좌측 X (인치).
        top_in: 차트 상단 Y (인치).
        width_in: 차트 너비 (인치).
        max_height_in: 차트가 사용 가능한 최대 높이 (인치). CHART_DEFAULT_HEIGHT_IN 과
            min 을 취해 실제 높이를 결정.

    Returns:
        차트 바닥 Y 좌표 (인치). 호출부가 다음 컴포넌트 top 으로 사용.
    """
    # 0) 안전값 — 음수/0 방지 + 최소 공간 확인.
    safe_width = max(1.0, width_in)
    safe_max_height = max(CHART_MIN_HEIGHT_IN, max_height_in)
    chart_height = min(CHART_DEFAULT_HEIGHT_IN, safe_max_height)

    # 1) 빈 데이터 체크. Pydantic 이 min_length=1 을 강제하므로 통상 이 경로는 거치지
    #    않으나, 추후 스키마 완화/직접 호출에 대비한 방어 코드.
    labels = list(component.data.labels)
    raw_series = component.data.series
    if not labels or not raw_series or all(not s.values for s in raw_series):
        logger.warning(
            "render_chart: 빈 데이터 — placeholder 로 degrade (title=%r, chart_type=%s).",
            component.title,
            component.chart_type,
        )
        _render_chart_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=safe_width,
            height_in=chart_height,
            message=CHART_EMPTY_PLACEHOLDER_TEXT,
        )
        return top_in + chart_height + COMPONENT_VERTICAL_GAP_IN

    # 2) chart_type 매핑. fallback 발생 시 WARN.
    xl_chart_type, is_fallback = _resolve_xl_chart_type(component.chart_type)
    if is_fallback:
        logger.warning(
            "render_chart: chart_type=%r 은 현재 native 범위 외 — '%s' 로 graceful-degrade.",
            component.chart_type,
            CHART_FALLBACK_TYPE,
        )
    # 정규화된 chart_type 키 — 색상 채널 / 축 스타일 분기에 사용.
    normalized_chart_type = (component.chart_type or "").strip().lower()
    # line 여부는 색상 채널 선택에 사용.
    is_line_chart = normalized_chart_type == "line" and not is_fallback
    # pie 계열 여부 — 축/범례/색상 적용 규칙이 다르다.
    is_pie_chart = normalized_chart_type in _CHART_TYPES_WITHOUT_AXES and not is_fallback

    # 3) 시리즈 값 정규화 — 각 시리즈 values 를 float 로 coerce 하고, labels 와
    #    길이가 다르면 짧은 쪽에 맞춰 자르거나 0 으로 채운다. Pydantic ChartData
    #    validator 가 이미 일치시키지만 방어적 전처리 유지.
    expected_len = len(labels)
    series_pairs: list[tuple[str, list[float]]] = []
    for s in raw_series:
        values = _coerce_numeric_values(list(s.values))
        if len(values) < expected_len:
            values = values + [0.0] * (expected_len - len(values))
        elif len(values) > expected_len:
            values = values[:expected_len]
        series_pairs.append((s.name, values))

    # S3 D1 — pie 차트는 단일 시리즈만 의미가 있다. 여러 시리즈가 들어오면 첫
    # 시리즈만 사용하고 나머지는 WARN 로그 + drop. (bar/line 등은 multi-series 허용)
    if is_pie_chart and len(series_pairs) > 1:
        logger.warning(
            "render_chart: pie 차트는 단일 시리즈만 지원 — %d 개 중 첫 시리즈만 사용 (drop=%s).",
            len(series_pairs),
            [name for name, _ in series_pairs[1:]],
        )
        series_pairs = series_pairs[:1]

    # 4) 카테고리 truncation.
    labels, series_pairs = _truncate_categories_and_series(labels, series_pairs, CHART_MAX_CATEGORIES)

    # 5) CategoryChartData 구성 + add_chart.
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_LEGEND_POSITION

    chart_data_obj = CategoryChartData()
    chart_data_obj.categories = labels
    for name, values in series_pairs:
        chart_data_obj.add_series(name, values)

    try:
        chart_shape = slide.shapes.add_chart(
            xl_chart_type,
            Inches(left_in),
            Inches(top_in),
            Inches(safe_width),
            Inches(chart_height),
            chart_data_obj,
        )
    except Exception as exc:
        # python-pptx 가 차트 삽입에 실패하는 경우 (극히 드물지만 데이터 이상값 등).
        logger.warning(
            "render_chart: add_chart 실패 — placeholder 로 degrade (title=%r): %s",
            component.title,
            exc,
        )
        _render_chart_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=safe_width,
            height_in=chart_height,
            message=CHART_EMPTY_PLACEHOLDER_TEXT,
        )
        return top_in + chart_height + COMPONENT_VERTICAL_GAP_IN

    chart = chart_shape.chart

    # 6) 색상 적용 — 차트 타입별 분기.
    palette_size = len(CHART_SERIES_PALETTE)
    try:
        # 기본적으로 plots[0].series 에 모든 시리즈가 들어있다.
        plot_series = list(chart.plots[0].series)
    except Exception:  # pragma: no cover — 구조 변동 방어.
        logger.debug("render_chart: plots[0].series 접근 실패 — 색상 적용 skip.", exc_info=True)
        plot_series = []

    if is_pie_chart and plot_series:
        # pie: 단일 시리즈 내 각 카테고리(data point) 에 팔레트 순환 적용.
        _apply_pie_data_point_colors(plot_series[0], CHART_SERIES_PALETTE)
    else:
        # bar/column/line/area/stacked_*: 시리즈 단위 색상 순환.
        for idx, series_obj in enumerate(plot_series):
            hex_color = CHART_SERIES_PALETTE[idx % palette_size]
            _apply_series_color(series_obj, hex_color, is_line_chart=is_line_chart)

    # 7) 제목 표시 (component.title 은 Pydantic min_length=1 보장).
    try:
        chart.has_title = True
        chart.chart_title.text_frame.text = component.title
        # 제목 폰트 — IDINO_TEXT 색 + 14pt bold + Pretendard.
        for paragraph in chart.chart_title.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.size = Pt(CHART_TITLE_FONT_PT)
                run.font.name = DEFAULT_FONT
                run.font.bold = True
                run.font.color.rgb = parse_hex_color(IDINO_TEXT)
    except Exception:  # pragma: no cover — 제목 설정 실패는 렌더 실패가 아님.
        logger.debug("render_chart: 제목 설정 실패.", exc_info=True)

    # 8) 범례 정책 — 차트 타입별로 다르다.
    #    - pie: 단일 시리즈여도 카테고리 식별을 위해 범례 필요 → 항상 표시.
    #    - bar/line/area/stacked_*: 시리즈 2 개 이상이면 하단 표시, 1 개면 숨김.
    try:
        if is_pie_chart or len(plot_series) >= 2:
            chart.has_legend = True
            chart.legend.position = XL_LEGEND_POSITION.BOTTOM
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(CHART_LEGEND_FONT_PT)
            chart.legend.font.name = DEFAULT_FONT
        else:
            chart.has_legend = False
    except Exception:  # pragma: no cover
        logger.debug("render_chart: 범례 설정 실패.", exc_info=True)

    # 9) 축 스타일 — pie 계열은 축 자체가 없으므로 skip.
    #    bar/line/area/stacked_* 은 현재 스키마에 x_label/y_label 필드가 없어 둘 다 None.
    if not is_pie_chart:
        _style_chart_axes(chart, x_label=None, y_label=None)

    return top_in + chart_height + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 9. ImageGrid (S3 D2)
# ---------------------------------------------------------------------------
#
# Pydantic 스키마 ``ImageGridComponent.images`` 필드는 2~4 개의 ImageGridItem
# 리스트 (min_length=2, max_length=4). columns/rows 필드가 없으므로 렌더러가
# 이미지 수로부터 레이아웃을 자동 결정한다 (``IMAGE_GRID_LAYOUT_BY_COUNT``).
#
# 설계 판단 포인트:
#   1. **개별 셀은 ``render_image`` 를 재사용하지 않는다** — 이유: render_image 는
#      caption 처리·image 상·하 스택 관리·COMPONENT_VERTICAL_GAP_IN 가산을 자동
#      수행하는데, 그리드 셀에서는 이런 동작이 불필요하고 오히려 좌표 어긋남을
#      유발한다. 대신 내부 private helper ``_render_image_cell()`` 로 재사용.
#   2. **캡션 간소화**: 개별 셀에는 caption 을 렌더하지 않는다. ImageGridItem 이
#      caption 필드를 가지지만, 그리드 내부 시각적 노이즈를 줄이기 위해 alt text
#      는 accessibility(descr) 로만 주입하고 caption 은 생략.
#   3. **개별 셀 fetch 실패**: 다른 셀 렌더에 영향 없이 그 셀만 placeholder 로
#      대체. render_image 와 동일 degradation 정책.


def _render_image_cell(
    item: ImageGridItem,
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float,
) -> None:
    """ImageGrid 내 단일 이미지 셀을 고정 박스 크기로 렌더.

    ``render_image`` 와 달리 원본 aspect ratio 를 유지하지 않고 **정확히
    width_in × height_in 박스** 에 맞춰 삽입한다. 그리드는 모든 셀이 동일
    크기일 때 시각적으로 정돈되므로 약간의 왜곡을 감수한다.

    fetch 실패 시 ``_render_image_placeholder`` 경로.
    """
    safe_w = max(0.3, width_in)
    safe_h = max(0.3, height_in)

    # src 미지정 → placeholder (prompt 기반 자동 생성은 S3 D3 이후 범위).
    if not item.src:
        logger.info(
            "_render_image_cell: src 미지정 — placeholder (alt=%r).",
            item.alt,
        )
        _render_image_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=safe_w,
            height_in=safe_h,
            alt_text=item.alt,
        )
        return

    # 이미지 bytes 확보.
    try:
        image_stream = fetch_image_bytes(item.src)
    except ImageFetchError as exc:
        logger.warning(
            "_render_image_cell: fetch 실패 — placeholder (src=%r, alt=%r): %s",
            item.src,
            item.alt,
            exc,
        )
        _render_image_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=safe_w,
            height_in=safe_h,
            alt_text=item.alt,
        )
        return

    try:
        picture = slide.shapes.add_picture(
            image_stream,
            Inches(left_in),
            Inches(top_in),
            width=Inches(safe_w),
            height=Inches(safe_h),
        )
        _set_picture_alt_text(picture, item.alt)
    except Exception as exc:
        logger.warning(
            "_render_image_cell: add_picture 실패 — placeholder (src=%r): %s",
            item.src,
            exc,
        )
        _render_image_placeholder(
            slide,
            left_in=left_in,
            top_in=top_in,
            width_in=safe_w,
            height_in=safe_h,
            alt_text=item.alt,
        )


def render_image_grid(
    component: ImageGridComponent,
    slide: Slide,
    *,
    left_in: float,
    top_in: float,
    width_in: float,
    max_height_in: float,
) -> float:
    """ImageGrid 컴포넌트를 슬라이드에 격자로 배치 (Phase 4 S3 D2).

    동작 순서:
        1) ``len(component.images)`` 로부터 (rows, cols) 결정.
           - 2 → (1, 2), 3 → (1, 3), 4 → (2, 2). 없는 경우 cols=min(4, n).
        2) 주어진 width_in 을 cols 로 균등 분할 (gap 반영).
        3) max_height_in 기반으로 rows 균등 분할 셀 높이 산출.
        4) 각 셀마다 ``_render_image_cell`` 로 실제 이미지/placeholder 삽입.

    Args:
        component: ImageGridComponent — images 2~4 개.
        slide: python-pptx Slide.
        left_in: 그리드 좌측 X (인치).
        top_in: 그리드 상단 Y (인치).
        width_in: 그리드 전체 너비 (인치).
        max_height_in: 그리드가 사용 가능한 최대 높이 (인치).

    Returns:
        그리드 바닥 Y 좌표 (인치). 호출부가 다음 컴포넌트 top 으로 사용.
    """
    items = list(component.images)
    n = len(items)
    if n == 0:  # pragma: no cover — Pydantic min_length=2 가 차단.
        return top_in + COMPONENT_VERTICAL_GAP_IN

    # 1) 레이아웃 결정 — 스키마상 columns/rows 필드 없음 → 이미지 수로 자동 결정.
    rows, cols = IMAGE_GRID_LAYOUT_BY_COUNT.get(n, (1, max(1, min(4, n))))

    # 2) 안전값 보정 + gap 기반 셀 크기 계산.
    safe_width = max(1.0, width_in)
    safe_max_height = max(1.0, max_height_in)
    gap = IMAGE_GRID_GAP_IN

    # 셀 너비 = (전체 너비 - gap * (cols-1)) / cols, 최소 0.5" 보장.
    total_h_gap = gap * max(0, cols - 1)
    cell_width = max(0.5, (safe_width - total_h_gap) / cols)

    total_v_gap = gap * max(0, rows - 1)
    cell_height = max(0.5, (safe_max_height - total_v_gap) / rows)

    # 3) 각 셀 렌더 — items 순서대로 (row-major: 왼→오, 위→아래).
    for idx, item in enumerate(items):
        r = idx // cols
        c = idx % cols
        cell_left = left_in + c * (cell_width + gap)
        cell_top = top_in + r * (cell_height + gap)
        _render_image_cell(
            item,
            slide,
            left_in=cell_left,
            top_in=cell_top,
            width_in=cell_width,
            height_in=cell_height,
        )

    # 4) 반환값 — 그리드가 사용한 실제 높이 + 다음 컴포넌트를 위한 기본 gap.
    used_height = rows * cell_height + total_v_gap
    return top_in + used_height + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 10. SlideSubtitle (S3 D6)
# ---------------------------------------------------------------------------
#
# SlideTitle 바로 아래에 한 줄로 깔리는 보조 제목. 20pt muted·center.
# italic 은 기본 off (스키마에 italic 플래그가 없으므로 정책적으로 off 고정).
# FE React 렌더는 24px(≈18pt) muted·center 와 근사 → PPTX 에서는 20pt 로 약간
# 크게 잡아 슬라이드 가시성을 확보한다.


def render_slide_subtitle(
    component: SlideSubtitleComponent,
    slide: Slide,
    *,
    left_in: float | None = None,
    top_in: float | None = None,
    width_in: float | None = None,
) -> float:
    """SlideSubtitle 을 SlideTitle 아래 위치에 중앙 정렬로 배치.

    Args:
        component: `SlideSubtitleComponent` (text 필수).
        slide: python-pptx Slide.
        left_in: 좌측 X (인치). None 이면 SLIDE_TITLE_LEFT_IN 과 동일.
        top_in: 상단 Y (인치). None 이면 SlideTitle 바닥 바로 아래.
        width_in: 너비 (인치). None 이면 SLIDE_TITLE_WIDTH_IN 과 동일.

    Returns:
        컴포넌트 바닥 Y 좌표 (인치). 호출부가 다음 컴포넌트 top 으로 사용.
    """
    resolved_left = left_in if left_in is not None else SLIDE_TITLE_LEFT_IN
    # SlideTitle 바로 아래 — SLIDE_TITLE_TOP_IN + SLIDE_TITLE_HEIGHT_IN
    # (gap 은 두지 않고 타이틀 바로 붙임 — SlideTitle/Subtitle 은 한 덩어리 인상).
    resolved_top = top_in if top_in is not None else (SLIDE_TITLE_TOP_IN + SLIDE_TITLE_HEIGHT_IN)
    resolved_width = width_in if width_in is not None else SLIDE_TITLE_WIDTH_IN

    shape = _add_textbox_at(
        slide,
        left_in=resolved_left,
        top_in=resolved_top,
        width_in=resolved_width,
        height_in=SLIDE_SUBTITLE_HEIGHT_IN,
    )
    tf = shape.text_frame
    tf.word_wrap = True

    paragraph = reset_text_frame(tf)
    paragraph.text = component.text
    apply_idino_text_style(
        paragraph,
        font_size=FONT_SIZE_SLIDE_SUBTITLE,
        bold=False,
        color=IDINO_TEXT_MUTED,
        alignment=PP_ALIGN.CENTER,
    )

    return resolved_top + SLIDE_SUBTITLE_HEIGHT_IN + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 11. Quote (S3 D6)
# ---------------------------------------------------------------------------
#
# 인용 블록. 좌측에 얇은 세로 강조선(accent color) + 들여쓴 인용문 (italic) +
# author 있으면 하단 우측에 "— {author}" mute color 로 표기.
#
# 구현 요점:
#   - 좌측 강조선은 `MSO_SHAPE.RECTANGLE` 4pt 폭, accent color 채움.
#   - 인용문 텍스트 박스는 강조선 우측 padding(0.3") 지점부터 시작.
#   - 인용문은 italic, line-height 1.5 (python-pptx 는 paragraph.line_spacing 으로).
#   - author 는 같은 박스 아래 별도 textbox — right 정렬 + muted color.


def _estimate_quote_text_height(text: str, width_in: float) -> float:
    """Quote 본문 박스 높이 추정 (인치).

    16pt + 행간 1.5 배 기준. 한/영 가중치를 재사용해 한글 밀집 인용문에서
    박스가 잘리지 않도록 ±20 % 여유를 둔다.
    """
    cpl = _chars_per_line_for_pt(FONT_SIZE_QUOTE, width_in)
    weighted = _count_weighted_chars(text)
    lines_from_length = max(1, int((weighted + cpl - 1) // cpl)) if weighted > 0 else 1
    lines_from_newlines = text.count("\n") + 1
    total_lines = max(lines_from_newlines, lines_from_length)
    # pt → 인치 (72 pt = 1 인치), 행간 1.5 배.
    pt_per_line = FONT_SIZE_QUOTE * QUOTE_LINE_HEIGHT_MULTIPLIER
    height_in = (total_lines * pt_per_line) / 72.0
    return max(QUOTE_MIN_HEIGHT_IN, height_in + 0.15)


def render_quote(
    component: QuoteComponent,
    slide: Slide,
    *,
    left_in: float | None = None,
    top_in: float | None = None,
    width_in: float | None = None,
) -> float:
    """Quote 컴포넌트 — 들여쓴 인용 블록 + 좌측 세로 강조선.

    Args:
        component: `QuoteComponent`.
        slide: python-pptx Slide.
        left_in: 좌측 X (인치). None 이면 BODY_LEFT_IN.
        top_in: 상단 Y (인치). None 이면 BODY_TOP_IN.
        width_in: 전체 너비 (인치). None 이면 BODY_WIDTH_IN.

    Returns:
        컴포넌트 바닥 Y 좌표 (인치).
    """
    # MSO_SHAPE 는 강조선 그릴 때에만 import — 기존 모듈 패턴과 동일.
    from pptx.enum.shapes import MSO_SHAPE

    resolved_left = left_in if left_in is not None else BODY_LEFT_IN
    resolved_top = top_in if top_in is not None else BODY_TOP_IN
    resolved_width = width_in if width_in is not None else BODY_WIDTH_IN

    # 본문 박스 너비는 전체 너비에서 강조선 + padding 만큼 제외.
    text_left = resolved_left + QUOTE_BAR_WIDTH_IN + QUOTE_PADDING_LEFT_IN
    text_width = max(1.0, resolved_width - QUOTE_BAR_WIDTH_IN - QUOTE_PADDING_LEFT_IN)

    # 1) 인용문 박스 — italic + 행간 1.5.
    text_height = _estimate_quote_text_height(component.text, text_width)
    quote_shape = _add_textbox_at(
        slide,
        left_in=text_left,
        top_in=resolved_top,
        width_in=text_width,
        height_in=text_height,
    )
    tf = quote_shape.text_frame
    tf.word_wrap = True
    paragraph = reset_text_frame(tf)
    paragraph.text = component.text
    apply_idino_text_style(
        paragraph,
        font_size=FONT_SIZE_QUOTE,
        bold=False,
        color=IDINO_TEXT,
        alignment=PP_ALIGN.LEFT,
    )
    # italic 은 style 헬퍼 미지원 → run 에 직접 적용.
    for run in paragraph.runs:
        run.font.italic = True
    # 행간 1.5 — python-pptx 의 paragraph.line_spacing 은 float(배수) 지원.
    paragraph.line_spacing = QUOTE_LINE_HEIGHT_MULTIPLIER

    # 2) 좌측 세로 강조선 — 인용문 박스와 같은 높이로 맞춤.
    bar_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(resolved_left),
        Inches(resolved_top),
        Inches(QUOTE_BAR_WIDTH_IN),
        Inches(text_height),
    )
    _apply_shape_solid_fill(bar_shape, IDINO_ACCENT)
    # 외곽선 제거 — 단순 선 인상만 남김.
    bar_shape.line.fill.background()

    # 3) author — 있으면 인용문 아래 right 정렬 mute color.
    next_y = resolved_top + text_height
    if component.author:
        author_shape = _add_textbox_at(
            slide,
            left_in=text_left,
            top_in=next_y,
            width_in=text_width,
            height_in=QUOTE_AUTHOR_HEIGHT_IN,
        )
        author_tf = author_shape.text_frame
        author_tf.word_wrap = True
        author_para = reset_text_frame(author_tf)
        author_para.text = f"— {component.author}"
        apply_idino_text_style(
            author_para,
            font_size=FONT_SIZE_QUOTE_AUTHOR,
            bold=False,
            color=IDINO_TEXT_MUTED,
            alignment=PP_ALIGN.RIGHT,
        )
        next_y += QUOTE_AUTHOR_HEIGHT_IN

    return next_y + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 12. Callout (S3 D6)
# ---------------------------------------------------------------------------
#
# variant 별 배경색 + 좌측 border. 둥근 사각형(MSO_SHAPE.ROUNDED_RECTANGLE) 으로
# 모서리 radius 0.08" 부여. lucide 아이콘은 불가 → variant 이니셜 letter 로 대체.
#
# 시각 요소:
#   1) 배경 rounded_rect — variant_bg 색.
#   2) 좌측 얇은 rectangle border — variant_border 색 (4pt 폭).
#   3) 좌측 letter — variant_letter (i/!/✓/!) — border 우측에 작은 원형 배경 없이 직접.
#   4) 본문 — 14pt + padding 0.15".


def _estimate_callout_height(text: str, width_in: float) -> float:
    """Callout 전체 높이 추정 (인치). border + padding + 본문 줄 수 기준."""
    # 본문 박스에 사용 가능한 폭 = 전체 - border - padding - letter 영역(~0.45") - 우 padding.
    inner_width = max(1.0, width_in - CALLOUT_BORDER_WIDTH_IN - CALLOUT_PADDING_IN * 2 - 0.45)
    cpl = _chars_per_line_for_pt(FONT_SIZE_CALLOUT, inner_width)
    weighted = _count_weighted_chars(text)
    lines_from_length = max(1, int((weighted + cpl - 1) // cpl)) if weighted > 0 else 1
    lines_from_newlines = text.count("\n") + 1
    total_lines = max(lines_from_newlines, lines_from_length)
    pt_per_line = FONT_SIZE_CALLOUT * 1.4
    body_height = (total_lines * pt_per_line) / 72.0
    # 위·아래 padding 추가.
    return max(CALLOUT_MIN_HEIGHT_IN, body_height + CALLOUT_PADDING_IN * 2)


def render_callout(
    component: CalloutComponent,
    slide: Slide,
    *,
    left_in: float | None = None,
    top_in: float | None = None,
    width_in: float | None = None,
) -> float:
    """Callout 컴포넌트 — variant 별 배경색 + 좌측 border + 본문 텍스트.

    Args:
        component: `CalloutComponent`. variant ∈ {info, warning, success, danger}.
        slide: python-pptx Slide.
        left_in / top_in / width_in: 위치·크기. 기본값은 BODY 영역.

    Returns:
        컴포넌트 바닥 Y 좌표 (인치).
    """
    from pptx.enum.shapes import MSO_SHAPE

    resolved_left = left_in if left_in is not None else BODY_LEFT_IN
    resolved_top = top_in if top_in is not None else BODY_TOP_IN
    resolved_width = width_in if width_in is not None else BODY_WIDTH_IN

    # variant 미지원값 방어 (Pydantic Literal 로 차단되지만 런타임 안전망).
    bg_color = CALLOUT_VARIANT_BG.get(component.variant, CALLOUT_VARIANT_BG["info"])
    border_color = CALLOUT_VARIANT_BORDER.get(component.variant, CALLOUT_VARIANT_BORDER["info"])
    letter = CALLOUT_VARIANT_LETTER.get(component.variant, "i")

    total_height = _estimate_callout_height(component.text, resolved_width)

    # 1) 배경 rounded_rect — variant_bg.
    bg_shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(resolved_left),
        Inches(resolved_top),
        Inches(resolved_width),
        Inches(total_height),
    )
    _apply_shape_solid_fill(bg_shape, bg_color)
    # 외곽선은 얕게 — border 색과 동일하게 해 시각 일체감 유지.
    try:
        bg_shape.line.color.rgb = parse_hex_color(border_color)
        bg_shape.line.width = Pt(0.5)
    except Exception:  # pragma: no cover — line 설정 실패는 렌더 치명적 아님.
        logger.debug("render_callout: 배경 외곽선 설정 실패 (무시)", exc_info=True)

    # 2) 좌측 세로 border (굵은 4pt rectangle).
    border_shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(resolved_left),
        Inches(resolved_top),
        Inches(CALLOUT_BORDER_WIDTH_IN),
        Inches(total_height),
    )
    _apply_shape_solid_fill(border_shape, border_color)
    border_shape.line.fill.background()

    # 3) variant letter — border 우측 padding 위치.
    letter_width = 0.4
    letter_shape = _add_textbox_at(
        slide,
        left_in=resolved_left + CALLOUT_BORDER_WIDTH_IN + CALLOUT_PADDING_IN,
        top_in=resolved_top + CALLOUT_PADDING_IN,
        width_in=letter_width,
        height_in=0.4,
    )
    letter_tf = letter_shape.text_frame
    letter_tf.word_wrap = False
    letter_para = reset_text_frame(letter_tf)
    letter_para.text = letter
    apply_idino_text_style(
        letter_para,
        font_size=FONT_SIZE_CALLOUT + 4,  # 본문보다 약간 크게 강조.
        bold=True,
        color=border_color,
        alignment=PP_ALIGN.CENTER,
    )

    # 4) 본문 — letter 우측 + padding.
    body_left = resolved_left + CALLOUT_BORDER_WIDTH_IN + CALLOUT_PADDING_IN + letter_width + 0.1
    body_width = max(
        1.0,
        resolved_width - (body_left - resolved_left) - CALLOUT_PADDING_IN,
    )
    body_shape = _add_textbox_at(
        slide,
        left_in=body_left,
        top_in=resolved_top + CALLOUT_PADDING_IN,
        width_in=body_width,
        height_in=total_height - CALLOUT_PADDING_IN * 2,
    )
    body_tf = body_shape.text_frame
    body_tf.word_wrap = True
    body_para = reset_text_frame(body_tf)
    body_para.text = component.text
    apply_idino_text_style(
        body_para,
        font_size=FONT_SIZE_CALLOUT,
        bold=False,
        color=IDINO_TEXT,
        alignment=PP_ALIGN.LEFT,
    )

    # 로깅 — variant 적용 추적용.
    logger.debug(
        "render_callout: variant=%s, bg=%s, border=%s",
        component.variant,
        bg_color,
        border_color,
    )

    # corner_radius — python-pptx 는 ROUNDED_RECTANGLE 의 adjustment 로 변경.
    # 기본 adjustment 값(~0.16) 도 충분히 IDINO 톤이라 보정 생략. 필요 시 아래 주석 참조.
    # bg_shape.adjustments[0] = CALLOUT_CORNER_RADIUS_IN / total_height  # 상대비율.

    return resolved_top + total_height + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 13. Timeline (S3 D7)
# ---------------------------------------------------------------------------
#
# 세로 리스트 형태. 각 이벤트는 좌측 마커(원) + 우측 3 단 (date / title / description).
# 연속된 마커 사이에는 IDINO_ACCENT 세로 연결선을 그려 시각적 흐름을 표현.
# 최대 5 개 이벤트 제한 — 초과분은 스킵 + WARN.


def render_timeline(
    component: TimelineComponent,
    slide: Slide,
    *,
    left_in: float | None = None,
    top_in: float | None = None,
    width_in: float | None = None,
    max_height_in: float | None = None,
) -> float:
    """Timeline 컴포넌트 — 세로 이벤트 목록 + 마커 + 연결선.

    Args:
        component: `TimelineComponent` (events 1~10 개).
        slide: python-pptx Slide.
        left_in / top_in / width_in / max_height_in: 배치 영역.

    Returns:
        컴포넌트 바닥 Y 좌표 (인치).
    """
    from pptx.enum.shapes import MSO_SHAPE

    resolved_left = left_in if left_in is not None else BODY_LEFT_IN
    resolved_top = top_in if top_in is not None else BODY_TOP_IN
    resolved_width = width_in if width_in is not None else BODY_WIDTH_IN

    # 5 개 초과 events 스킵 + WARN.
    events = list(component.events)
    if len(events) > TIMELINE_MAX_EVENTS:
        logger.warning(
            "render_timeline: events %d 개 중 상위 %d 개만 렌더 (초과 %d 개 스킵)",
            len(events),
            TIMELINE_MAX_EVENTS,
            len(events) - TIMELINE_MAX_EVENTS,
        )
        events = events[:TIMELINE_MAX_EVENTS]

    if not events:  # pragma: no cover — Pydantic min_length=1 이 차단.
        return resolved_top + COMPONENT_VERTICAL_GAP_IN

    # 좌측 마커 컬럼 / 우측 본문 컬럼 분할.
    marker_col_left = resolved_left
    body_col_left = resolved_left + TIMELINE_MARKER_COLUMN_WIDTH_IN
    body_col_width = max(1.0, resolved_width - TIMELINE_MARKER_COLUMN_WIDTH_IN)

    event_height = TIMELINE_EVENT_BODY_HEIGHT_IN
    row_stride = event_height + TIMELINE_EVENT_GAP_IN

    # max_height 가 주어지면 이벤트 수에 맞춰 압축 가능 — 우선은 단순 배치.
    for idx, event in enumerate(events):
        row_top = resolved_top + idx * row_stride

        # 1) 마커 — 작은 원형. 본문 컬럼 상단 가까이 배치.
        marker_left = marker_col_left + (TIMELINE_MARKER_COLUMN_WIDTH_IN - TIMELINE_MARKER_DIAMETER_IN) / 2.0
        marker_top = row_top + 0.1  # 날짜 텍스트와 수직 정렬 미세 조정.
        marker = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            Inches(marker_left),
            Inches(marker_top),
            Inches(TIMELINE_MARKER_DIAMETER_IN),
            Inches(TIMELINE_MARKER_DIAMETER_IN),
        )
        _apply_shape_solid_fill(marker, IDINO_ACCENT)
        marker.line.fill.background()

        # 2) 연결선 — 현재 마커와 다음 마커 사이. 마지막 이벤트에는 그리지 않음.
        if idx < len(events) - 1:
            connector_left = marker_col_left + (TIMELINE_MARKER_COLUMN_WIDTH_IN - TIMELINE_CONNECTOR_WIDTH_IN) / 2.0
            connector_top = marker_top + TIMELINE_MARKER_DIAMETER_IN
            # 다음 마커까지의 거리 = row_stride - 마커 직경.
            connector_height = row_stride - TIMELINE_MARKER_DIAMETER_IN
            connector = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(connector_left),
                Inches(connector_top),
                Inches(TIMELINE_CONNECTOR_WIDTH_IN),
                Inches(max(0.05, connector_height)),
            )
            _apply_shape_solid_fill(connector, IDINO_ACCENT)
            connector.line.fill.background()

        # 3) 본문 — date / title / description 3 단. 작은 박스 3 개를 세로로 쌓음.
        date_h = 0.25
        title_h = 0.3
        desc_h = max(0.05, event_height - date_h - title_h)

        # date (11pt, muted color).
        date_shape = _add_textbox_at(
            slide,
            left_in=body_col_left,
            top_in=row_top,
            width_in=body_col_width,
            height_in=date_h,
        )
        date_tf = date_shape.text_frame
        date_tf.word_wrap = True
        date_para = reset_text_frame(date_tf)
        date_para.text = event.date
        apply_idino_text_style(
            date_para,
            font_size=FONT_SIZE_TIMELINE_DATE,
            bold=True,
            color=IDINO_ACCENT,
            alignment=PP_ALIGN.LEFT,
        )

        # title (14pt, bold, primary).
        title_shape = _add_textbox_at(
            slide,
            left_in=body_col_left,
            top_in=row_top + date_h,
            width_in=body_col_width,
            height_in=title_h,
        )
        title_tf = title_shape.text_frame
        title_tf.word_wrap = True
        title_para = reset_text_frame(title_tf)
        title_para.text = event.title
        apply_idino_text_style(
            title_para,
            font_size=FONT_SIZE_TIMELINE_TITLE,
            bold=True,
            color=IDINO_PRIMARY,
            alignment=PP_ALIGN.LEFT,
        )

        # description (11pt, muted) — 있는 경우만.
        if event.description:
            desc_shape = _add_textbox_at(
                slide,
                left_in=body_col_left,
                top_in=row_top + date_h + title_h,
                width_in=body_col_width,
                height_in=desc_h,
            )
            desc_tf = desc_shape.text_frame
            desc_tf.word_wrap = True
            desc_para = reset_text_frame(desc_tf)
            desc_para.text = event.description
            apply_idino_text_style(
                desc_para,
                font_size=FONT_SIZE_TIMELINE_DESC,
                bold=False,
                color=IDINO_TEXT_MUTED,
                alignment=PP_ALIGN.LEFT,
            )

    total_height = len(events) * row_stride - TIMELINE_EVENT_GAP_IN
    return resolved_top + total_height + COMPONENT_VERTICAL_GAP_IN


# ---------------------------------------------------------------------------
# 14. IconRow (S3 D7)
# ---------------------------------------------------------------------------
#
# items 가로 균등 배치. 각 item = 큰 원형(IDINO_PRIMARY) + 원 안 letter(흰색) + 라벨.
# python-pptx 로 lucide 아이콘 직접 렌더 불가 → 원 + letter 대체.
# letter 는 icon 이름의 **첫 글자 대문자** (예: "rocket" → "R").


def _icon_letter(icon_name: str) -> str:
    """lucide 아이콘 이름 → 원 안에 들어갈 letter.

    규칙:
      - 첫 글자를 대문자로 (ASCII 만).
      - 비-ASCII(한글 등) 이름은 첫 글자 그대로 (이미 1 글자면 그대로 표시).
      - 빈 문자열은 '?' fallback.
    """
    s = (icon_name or "").strip()
    if not s:
        return "?"
    first = s[0]
    if first.isascii() and first.isalpha():
        return first.upper()
    return first


def render_icon_row(
    component: IconRowComponent,
    slide: Slide,
    *,
    left_in: float | None = None,
    top_in: float | None = None,
    width_in: float | None = None,
) -> float:
    """IconRow 컴포넌트 — items 가로 균등 배치, 원형 도형 + letter + 라벨.

    Args:
        component: `IconRowComponent` (items 2~6 개).
        slide: python-pptx Slide.
        left_in / top_in / width_in: 배치 영역.

    Returns:
        컴포넌트 바닥 Y 좌표 (인치).
    """
    from pptx.enum.shapes import MSO_SHAPE

    resolved_left = left_in if left_in is not None else BODY_LEFT_IN
    resolved_top = top_in if top_in is not None else BODY_TOP_IN
    resolved_width = width_in if width_in is not None else BODY_WIDTH_IN

    items = list(component.items)
    n = len(items)
    if n == 0:  # pragma: no cover — Pydantic min_length=2 차단.
        return resolved_top + COMPONENT_VERTICAL_GAP_IN

    # item 당 가로 폭 = (전체 - gap * (n-1)) / n.
    total_gap = ICON_ROW_ITEM_GAP_IN * max(0, n - 1)
    item_width = max(
        ICON_ROW_CIRCLE_DIAMETER_IN,
        (resolved_width - total_gap) / n,
    )
    # 원은 정사각형이므로 diameter 는 item_width 와 구분. 너무 좁아도 하한 유지.
    diameter = min(ICON_ROW_CIRCLE_DIAMETER_IN, item_width - 0.1)
    diameter = max(0.4, diameter)

    # 원 상단 Y = resolved_top. 라벨은 그 아래.
    circle_top = resolved_top
    label_top = circle_top + diameter + ICON_ROW_LABEL_GAP_IN

    for idx, item in enumerate(items):
        item_left = resolved_left + idx * (item_width + ICON_ROW_ITEM_GAP_IN)
        # 원은 item 폭 안에서 중앙 정렬.
        circle_left = item_left + (item_width - diameter) / 2.0

        # 1) 원형 도형 (IDINO_PRIMARY 채움).
        circle = slide.shapes.add_shape(
            MSO_SHAPE.OVAL,
            Inches(circle_left),
            Inches(circle_top),
            Inches(diameter),
            Inches(diameter),
        )
        _apply_shape_solid_fill(circle, IDINO_PRIMARY)
        circle.line.fill.background()

        # 2) 원 안 letter — 흰 텍스트, 원 중앙.
        letter_shape = _add_textbox_at(
            slide,
            left_in=circle_left,
            top_in=circle_top,
            width_in=diameter,
            height_in=diameter,
        )
        letter_tf = letter_shape.text_frame
        letter_tf.word_wrap = False
        letter_para = reset_text_frame(letter_tf)
        letter_para.text = _icon_letter(item.icon)
        apply_idino_text_style(
            letter_para,
            font_size=FONT_SIZE_ICON_ROW_LETTER,
            bold=True,
            color=IDINO_WHITE,
            alignment=PP_ALIGN.CENTER,
        )

        # 3) 라벨 — 원 아래 중앙 정렬.
        label_shape = _add_textbox_at(
            slide,
            left_in=item_left,
            top_in=label_top,
            width_in=item_width,
            height_in=ICON_ROW_LABEL_HEIGHT_IN,
        )
        label_tf = label_shape.text_frame
        label_tf.word_wrap = True
        label_para = reset_text_frame(label_tf)
        label_para.text = item.label
        apply_idino_text_style(
            label_para,
            font_size=FONT_SIZE_ICON_ROW_LABEL,
            bold=False,
            color=IDINO_TEXT,
            alignment=PP_ALIGN.CENTER,
        )

    total_height = diameter + ICON_ROW_LABEL_GAP_IN + ICON_ROW_LABEL_HEIGHT_IN
    return resolved_top + total_height + COMPONENT_VERTICAL_GAP_IN
