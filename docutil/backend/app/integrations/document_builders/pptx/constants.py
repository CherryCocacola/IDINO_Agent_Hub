"""PPTX 빌더 전역 상수 (Phase 4 S2 D2).

IDINO 디자인 시스템 색상·폰트·레이아웃 위치 상수를 모아둔다. D3 에서
`layout_resolver.py` 가 마스터 기반 런타임 탐색을 도입하기 전까지는 본 모듈
상수가 단일 레이아웃(slide_layouts[6] blank) 기반 배치 좌표의 근거가 된다.

설계 판단 포인트:

1. **hex 문자열 + `RGBColor` 변환 유틸**: FE DesignTokens 는 ``#RRGGBB`` 를
   쓰므로 본 모듈도 문자열 hex 를 1 차 소스로 삼는다. `parse_hex_color()`
   로 런타임에 `pptx.dml.color.RGBColor` 로 변환한다 — 상수 자체를 RGBColor
   로 선언하지 않는 이유는 (a) DesignTokens 와의 직접 비교 편의, (b) 테스트
   에서 `assert "#0A4FC2" in palette` 같은 검증이 가능해져서.

2. **폰트 이름은 문자열 상수**: python-pptx 는 font.name 에 임의 문자열을
   받는다. OS 에 해당 폰트가 없으면 PowerPoint / LibreOffice 가 대체 폰트로
   렌더하므로 "Pretendard" 가 설치돼 있지 않은 환경(Ubuntu 서버, macOS) 에서도
   안전하다. 기존 `report_generator.py` 의 "Malgun Gothic" 과의 관계는 주석으로
   남긴다: Pretendard 는 FE 기본값, Malgun Gothic 은 윈도우 fallback.

3. **EMU 좌표 숫자**: python-pptx 는 `Inches(...)` / `Pt(...)` 로 EMU 로 변환
   하므로 본 모듈은 **인치 단위 float** 만 보관한다. 실제 `Inches()` 호출은
   components.py 에서 수행 — 단위 환산 책임을 한 지점에 몰아 테스트하기 쉽게.

참조:
- docs/phase1_architecture.md §4.1.1 (DesignTokens)
- docs/s2_d1_pptx_decomposition_plan.md §5, §6
- frontend/src/styles/document-tokens.css (FE DesignTokens 원본)
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# IDINO 디자인 시스템 — 색상 (hex, #RRGGBB)
# ---------------------------------------------------------------------------

# 본문/표지 제목 등 기본 강조 색 — FE DesignTokens.primary_color 기본값.
IDINO_PRIMARY: Final[str] = "#0A4FC2"

# Call-to-action / KPI 강조 등 보조 강조 색 — FE accent_color 기본값.
IDINO_ACCENT: Final[str] = "#FF6B35"

# 본문 텍스트 기본 색 — FE text_color 기본값(짙은 회색, 검정 대비 가독성↑).
IDINO_TEXT: Final[str] = "#1F2937"

# 보조 텍스트 (caption, muted) 색.
IDINO_TEXT_MUTED: Final[str] = "#6B7280"

# 배경/표지 화이트.
IDINO_WHITE: Final[str] = "#FFFFFF"

# 표 헤더 등에 쓰는 진한 남색 — 기존 report_generator 의 CLR_HEADER 와 호환.
IDINO_HEADER_NAVY: Final[str] = "#34495E"

# KPI delta 부호별 강조색 — Tailwind 기본 green-500 / red-500 과 동일 토큰.
# FE 에서도 동일 팔레트 사용 (document-tokens.css) 하여 PPT ↔ HTML 시각 일치 유지.
KPI_DELTA_UP_COLOR: Final[str] = "#10B981"  # 증가 — 녹색
KPI_DELTA_DOWN_COLOR: Final[str] = "#EF4444"  # 감소 — 적색
KPI_DELTA_FLAT_COLOR: Final[str] = IDINO_TEXT_MUTED  # 변화 없음 — 회색

# KPI 박스 기본 배경 (옅은 회색, alpha 대신 단색 톤 사용).
KPI_BOX_BG: Final[str] = "#F3F4F6"

# DataTable 제브라 스트라이프 행 색상 (홀수 행은 흰색, 짝수 행은 아래 색).
TABLE_ZEBRA_ROW_BG: Final[str] = "#F9FAFB"

# DataTable 셀 테두리 — 얇은 연회색.
TABLE_BORDER_COLOR: Final[str] = "#E5E7EB"


# 색상 이름 → hex 딕셔너리. 테스트에서 전체 팔레트 검증에 사용.
IDINO_PALETTE: Final[dict[str, str]] = {
    "primary": IDINO_PRIMARY,
    "accent": IDINO_ACCENT,
    "text": IDINO_TEXT,
    "text_muted": IDINO_TEXT_MUTED,
    "white": IDINO_WHITE,
    "header_navy": IDINO_HEADER_NAVY,
    "kpi_delta_up": KPI_DELTA_UP_COLOR,
    "kpi_delta_down": KPI_DELTA_DOWN_COLOR,
    "kpi_delta_flat": KPI_DELTA_FLAT_COLOR,
    "kpi_box_bg": KPI_BOX_BG,
    "table_zebra": TABLE_ZEBRA_ROW_BG,
    "table_border": TABLE_BORDER_COLOR,
}


# ---------------------------------------------------------------------------
# 폰트
# ---------------------------------------------------------------------------

# 기본 한글 폰트 — FE DesignTokens.font_family="Pretendard" 와 동일.
# OS 에 미설치 시 PowerPoint 가 시스템 fallback 으로 대체하므로 안전.
FONT_PRETENDARD: Final[str] = "Pretendard"

# 윈도우 fallback (기존 report_generator 호환).
FONT_MALGUN_GOTHIC: Final[str] = "Malgun Gothic"

# 본 모듈 기본값 — D2 범위는 전부 Pretendard 로 통일.
DEFAULT_FONT: Final[str] = FONT_PRETENDARD


# ---------------------------------------------------------------------------
# 폰트 크기 (pt)
# ---------------------------------------------------------------------------
#
# FE Paragraph/Heading 등의 --doc-font-size-* CSS 변수와 위계를 맞춘다.
# FE 에서는 rem 단위이나, PPTX 는 pt 단위이므로 근사 환산 (16px≈12pt 기준).

FONT_SIZE_SLIDE_TITLE: Final[int] = 32  # SlideTitle — 표지/섹션 제목
FONT_SIZE_HEADING_1: Final[int] = 24  # Heading level=1
FONT_SIZE_HEADING_2: Final[int] = 20  # Heading level=2
FONT_SIZE_HEADING_3: Final[int] = 16  # Heading level=3
FONT_SIZE_PARAGRAPH: Final[int] = 14  # Paragraph 본문
FONT_SIZE_BULLET: Final[int] = 14  # BulletList 각 항목
FONT_SIZE_BULLET_SUB: Final[int] = 12  # BulletList sub_items (들여쓰기 2 레벨)


# level → pt 매핑. Heading 렌더러가 dict 접근으로 분기.
HEADING_LEVEL_TO_PT: Final[dict[int, int]] = {
    1: FONT_SIZE_HEADING_1,
    2: FONT_SIZE_HEADING_2,
    3: FONT_SIZE_HEADING_3,
}


# ---------------------------------------------------------------------------
# 슬라이드 크기 (인치)
# ---------------------------------------------------------------------------
#
# python-pptx `Presentation()` 기본은 10"x7.5" (4:3). IDINO 디자인은 16:9
# (13.333"x7.5") 를 채택. D2 에서는 `PptxBuilder.build()` 에서 명시적으로
# 세팅 (아래 상수 사용).

SLIDE_WIDTH_IN: Final[float] = 13.333
SLIDE_HEIGHT_IN: Final[float] = 7.5


# ---------------------------------------------------------------------------
# 텍스트 박스 기본 좌표 (인치) — D2 단일 blank 레이아웃 기준
# ---------------------------------------------------------------------------
#
# D3 에서 layout_resolver 가 페이지별 layout 을 선택하게 되면 본 상수들은
# 해당 레이아웃별 기본값으로 역할이 축소된다. 당장은 "blank 위 직접 배치"
# 규칙의 단일 소스.
#
# 좌표는 (left, top, width, height) 네 값 모두 인치. `Inches()` 변환은 호출부.

# SlideTitle — 슬라이드 상단 중앙. 좌우 여백 0.5", 위 0.5" 에서 시작.
SLIDE_TITLE_LEFT_IN: Final[float] = 0.5
SLIDE_TITLE_TOP_IN: Final[float] = 0.5
SLIDE_TITLE_WIDTH_IN: Final[float] = SLIDE_WIDTH_IN - 1.0  # 12.333
SLIDE_TITLE_HEIGHT_IN: Final[float] = 1.0

# Heading — SlideTitle 아래 또는 본문 구획 제목. 본문 영역 상단에서 시작.
HEADING_LEFT_IN: Final[float] = 0.6
HEADING_TOP_IN: Final[float] = 1.7
HEADING_WIDTH_IN: Final[float] = SLIDE_WIDTH_IN - 1.2
HEADING_HEIGHT_IN: Final[float] = 0.6

# Paragraph / BulletList — 본문 영역. Heading 아래에 세로로 쌓임.
BODY_LEFT_IN: Final[float] = 0.6
BODY_TOP_IN: Final[float] = 2.4
BODY_WIDTH_IN: Final[float] = SLIDE_WIDTH_IN - 1.2
BODY_HEIGHT_IN: Final[float] = 0.8


# 복수 컴포넌트가 같은 슬라이드에 배치될 때 Y 좌표를 눌러주는 증분값 (인치).
# 실제 텍스트 길이에 따라 박스가 자동 확장(word_wrap) 되지만, 초기 오프셋
# 가이드로 사용한다. D3 에서 layout_resolver 가 세밀한 스택을 제공하게 됨.
COMPONENT_VERTICAL_GAP_IN: Final[float] = 0.15


# ---------------------------------------------------------------------------
# 한/영 혼용 높이 추정 테이블 (D9-e)
# ---------------------------------------------------------------------------
#
# Paragraph 박스 높이를 "글자 수 → 줄 수" 로 역산할 때 사용.
# D8 까지는 ``chars_per_line=70`` 하드코딩 단일 값이었다. Sample C (영문 비중
# 높은 본문) 에서는 여유, Sample A (한글 위주) 에서는 잘림 발생.
#
# 실측 근거 — 16:9 슬라이드 본문 영역 너비(12.133") 기준, Pretendard 표준 폭:
#   - 한글 1 글자 ≈ 1.0 em (정비율), 영문 1 글자 ≈ 0.55 em (proportional)
#   - 따라서 영문 기준 한 줄 가용 글자 수에 한글은 1/1.5 배만 들어감.
#
# 구현 전략 (간단화):
#   - ``_count_weighted_chars()`` 가 한글(가중치 1.5) · 영문(1.0) 을 합산.
#   - ``CHARS_PER_LINE_BY_PT[pt]`` 가 영문 기준 가용 글자 수.
#   - 줄 수 = ceil(weighted / chars_per_line_by_pt).
#
# 테이블 값은 BODY_WIDTH_IN(=12.133") 기준이며, 호출부가 다른 width 로 박스를
# 잡을 경우엔 width 에 비례 스케일. ±20 % 오차 범위 내 추정이 목표.

CHARS_PER_LINE_BY_PT: Final[dict[int, int]] = {
    10: 90,
    11: 82,
    12: 75,
    14: 65,
    16: 55,
    18: 48,
    20: 42,
    24: 35,
    28: 30,
    32: 26,
}

# 한글 문자 (U+AC00 ~ U+D7A3 완성형 + U+3131 ~ U+318E 자모) 를 판정할 때의
# 가중치. 영문/숫자 1.0 대비.
KOREAN_CHAR_WIDTH_MULTIPLIER: Final[float] = 1.5


# ---------------------------------------------------------------------------
# BulletList bullet glyph
# ---------------------------------------------------------------------------
#
# python-pptx 는 list numbering 을 자동 생성해 주지 않으므로 paragraph 에
# glyph prefix 를 붙여 시각적으로 bullet 을 표현한다. numbered=True 인 경우
# "1. ", "2. " 식으로 렌더러에서 인덱스 기반 문자열을 생성.

BULLET_GLYPH_UNORDERED: Final[str] = "•"  # "•"
BULLET_GLYPH_SUB: Final[str] = "◦"  # "◦"


# ---------------------------------------------------------------------------
# BulletList highlight 배경 (D9-d)
# ---------------------------------------------------------------------------
#
# ``emphasis="highlight"`` 로 표시된 bullet 항목 뒤에 얕게 깔리는 배경 박스 색.
# IDINO accent(#FF6B35) 대비 약 15 % 블렌드 수준의 옅은 주황 — 파스텔 톤을 유지해
# 슬라이드 전체 인상을 해치지 않는다. FE DesignTokens 의 hover/highlight 톤과
# 호환되는 범위.

HIGHLIGHT_BG_COLOR: Final[str] = "#FFF4ED"

# highlight 배경 박스의 세로 여백 (인치). 텍스트 baseline 대비 위·아래로 주는
# 여유. 너무 크면 다음 항목과 시각적 겹침이 생기므로 작게 유지.
HIGHLIGHT_BG_VERTICAL_PADDING_IN: Final[float] = 0.03


# ---------------------------------------------------------------------------
# KPI / DataTable 전용 좌표 · 폰트 (D3)
# ---------------------------------------------------------------------------
#
# KPI 카드는 label(상) / value(중앙, 큰 글씨) / delta(하) 3 단 구조. value 는
# 슬라이드 주목도를 위해 폰트를 매우 크게 잡고, label 과 delta 는 상대적으로
# 작게 잡는다. FE `KPICard` 컴포넌트 비율(label:value ≈ 12:40) 과 근사.

FONT_SIZE_KPI_LABEL: Final[int] = 12
FONT_SIZE_KPI_VALUE: Final[int] = 36
FONT_SIZE_KPI_DELTA: Final[int] = 12

# KPI 카드 기본 크기 (인치). 좌/상 좌표는 호출부에서 지정.
KPI_CARD_WIDTH_IN: Final[float] = 2.6
KPI_CARD_HEIGHT_IN: Final[float] = 1.5

# KPI 내부 3 단 높이 분배 (합은 KPI_CARD_HEIGHT_IN).
KPI_LABEL_HEIGHT_IN: Final[float] = 0.35
KPI_VALUE_HEIGHT_IN: Final[float] = 0.80
KPI_DELTA_HEIGHT_IN: Final[float] = 0.35


# DataTable.
FONT_SIZE_TABLE_HEADER: Final[int] = 11
FONT_SIZE_TABLE_CELL: Final[int] = 10

# 행당 기본 높이 (인치). 행 수가 많으면 아래에서 적절히 압축한다.
TABLE_ROW_HEIGHT_IN: Final[float] = 0.4

# DataTable 최대 표시 행 수 — 초과분은 말미 "..." 행으로 축약 (truncation).
# 너무 큰 표는 가독성이 떨어지고 slide 면적을 초과한다. Pydantic 스키마에서는
# rows: max_length=20 이지만, 렌더 단계에서도 시각적 한계를 지킨다.
TABLE_MAX_DISPLAY_ROWS: Final[int] = 18

# DataTable 기본 좌표. 본문 영역과 동일한 좌·너비 기준 (BODY_LEFT_IN 등).
# top 은 호출부에서 누적 Y 로 지정.
TABLE_DEFAULT_WIDTH_IN: Final[float] = BODY_WIDTH_IN


# ---------------------------------------------------------------------------
# Image 컴포넌트 전용 (D6)
# ---------------------------------------------------------------------------
#
# ImageComponent 는 현재 스키마에 width/height 필드가 없다 — 렌더러가 슬라이드
# 여백과 본문 영역을 기준으로 기본 너비를 잡고, 원본 이미지 비율을 유지해
# 높이를 자동 계산한다.

# 기본 이미지 너비 (인치) — 본문 영역의 약 60%. 호출부가 width_in 을 override 할 수 있다.
IMAGE_DEFAULT_WIDTH_IN: Final[float] = BODY_WIDTH_IN * 0.6

# fetch 실패 시 placeholder 박스 크기.
IMAGE_PLACEHOLDER_WIDTH_IN: Final[float] = 4.0
IMAGE_PLACEHOLDER_HEIGHT_IN: Final[float] = 2.5

# placeholder 배경색 (연회색) — KPI_BOX_BG 와 동일한 톤 재사용으로 단일 팔레트 유지.
IMAGE_PLACEHOLDER_BG: Final[str] = KPI_BOX_BG

# caption 텍스트 영역 높이 (인치) 와 폰트 크기.
IMAGE_CAPTION_HEIGHT_IN: Final[float] = 0.35
FONT_SIZE_IMAGE_CAPTION: Final[int] = 10

# 원본 비율을 읽을 수 없을 때 사용할 fallback 비율 (width : height = 4 : 3).
IMAGE_FALLBACK_ASPECT_RATIO: Final[float] = 4.0 / 3.0


# ---------------------------------------------------------------------------
# Chart 컴포넌트 전용 (D7)
# ---------------------------------------------------------------------------
#
# IDINO 차트 팔레트 — 여러 시리즈를 겹쳐 렌더할 때 색상이 순환(modulo)된다.
# FE document-tokens.css 의 차트 팔레트와 시각적 대응을 유지하여 HTML ↔ PPTX
# 동일한 차트 인상이 나오도록 한다. 8 색 사이클은 `ChartData.series` 의
# max_length=6 을 여유 있게 커버한다.

CHART_SERIES_PALETTE: Final[tuple[str, ...]] = (
    IDINO_PRIMARY,  # #0A4FC2 — 기본 시리즈
    IDINO_ACCENT,  # #FF6B35 — 보조 시리즈
    "#10B981",  # green (KPI_DELTA_UP 과 동일 톤)
    IDINO_TEXT_MUTED,  # #6B7280 — 중성 회색
    "#EF4444",  # red
    "#F59E0B",  # amber
    "#8B5CF6",  # purple
    "#14B8A6",  # teal
)

# 차트 축(axis) 눈금 라벨 폰트 크기 (pt).
CHART_AXIS_FONT_PT: Final[int] = 10

# 차트 범례(legend) 폰트 크기 (pt).
CHART_LEGEND_FONT_PT: Final[int] = 10

# 차트 타이틀 폰트 크기 (pt). SlideTitle(32pt) 대비 작게 유지 — 슬라이드
# 제목은 따로 존재하므로 차트 자체 타이틀은 본문 수준 강조만.
CHART_TITLE_FONT_PT: Final[int] = 14

# 차트 기본 너비 (인치) — 본문 영역의 약 70% 차지. 호출부 override 가능.
CHART_DEFAULT_WIDTH_IN: Final[float] = BODY_WIDTH_IN * 0.7

# 차트 최소 높이 (인치). 슬라이드 내 남은 공간이 이보다 작으면 placeholder 로 degrade.
CHART_MIN_HEIGHT_IN: Final[float] = 2.0

# 차트 기본 높이 (인치) — max_height 가 충분할 때 사용하는 권장 높이.
CHART_DEFAULT_HEIGHT_IN: Final[float] = 3.5

# 최대 카테고리(= labels) 표시 개수. 초과 시 상위 N-1 개 + "기타" 로 묶음.
# 스키마상 max_length=24 이지만, 시각적 가독성 한계는 더 낮다.
CHART_MAX_CATEGORIES: Final[int] = 15

# "기타" 묶음 카테고리 라벨.
CHART_ETC_CATEGORY_LABEL: Final[str] = "기타"

# 지원되지 않는 chart_type 에 대한 fallback 타입.
# 스키마는 Literal["bar", "line", "pie"] 로 제한되지만 D7 범위는 bar/line 만
# PPTX native 로 처리하므로 pie 는 bar 로 graceful-degrade.
CHART_FALLBACK_TYPE: Final[str] = "bar"

# 차트 데이터가 비어있을 때 placeholder 에 표시할 안내 문구.
CHART_EMPTY_PLACEHOLDER_TEXT: Final[str] = "[차트 데이터 없음]"


# ---------------------------------------------------------------------------
# ImageGrid 컴포넌트 전용 (S3 D2)
# ---------------------------------------------------------------------------
#
# ImageGrid 는 2~4 개 이미지를 격자로 배치한다. Pydantic 스키마상 `images`
# 필드는 min_length=2 / max_length=4 로 제약되며 columns/rows 필드는 없다.
# 따라서 렌더러가 자동으로 "이미지 수 → 최적 열 수" 매핑을 내부적으로 결정한다.
#
# 레이아웃 규칙:
#   - 2 개     → 1 행 2 열 (가로 나열)
#   - 3 개     → 1 행 3 열 (가로 나열)
#   - 4 개     → 2 행 2 열 (정사각 그리드)
# 각 셀은 `render_image` 재사용하지만 caption 은 본 범위에선 생략해 시각적
# 노이즈를 줄인다 (개별 Image 컴포넌트는 caption 유지).

# 셀 간 간격 (인치). 너무 크면 슬라이드 공간 낭비, 작으면 시각 분리 약화.
IMAGE_GRID_GAP_IN: Final[float] = 0.1

# 이미지 수 → (rows, cols) 매핑. 키가 없으면 min(4, n) 을 cols 로 사용.
IMAGE_GRID_LAYOUT_BY_COUNT: Final[dict[int, tuple[int, int]]] = {
    2: (1, 2),
    3: (1, 3),
    4: (2, 2),
}


# ---------------------------------------------------------------------------
# S3 D1 — Chart 확장 alias 상수
# ---------------------------------------------------------------------------
#
# 스키마상 ChartComponent.chart_type 은 Literal["bar", "line", "pie"] 로 제한되어
# 있어 실제로 호출 가능한 값은 3 종뿐이다. 그러나 파일단 `_CHART_TYPE_ALIAS` 에
# 확장 타입의 XL_CHART_TYPE 매핑을 선제적으로 등록해두면, 후속에서 스키마를
# 확장할 때 components.py 는 **무수정**으로 승격시킬 수 있다.
#
# 본 상수는 components.py `_CHART_TYPE_ALIAS` 가 문자열 alias 를 읽어 쓸 수
# 있도록 "XL_CHART_TYPE 멤버 이름" 을 매핑 테이블로 노출한다. 실제 enum 해석은
# 런타임 `getattr(XL_CHART_TYPE, name)` 이 담당.
CHART_XL_TYPE_NAME_BY_ALIAS: Final[dict[str, str]] = {
    # 스키마 Literal 3 종 (native).
    "bar": "COLUMN_CLUSTERED",
    "column": "COLUMN_CLUSTERED",  # alias — "bar" 와 동일.
    "line": "LINE",
    "pie": "PIE",
    # S3 이후 확장 예비 (스키마 확장 시 즉시 활성화 가능).
    "area": "AREA",
    "stacked_bar": "BAR_STACKED",
    "stacked_column": "COLUMN_STACKED",
    "stacked_area": "AREA_STACKED",
}


# ---------------------------------------------------------------------------
# S3 D6 — SlideSubtitle / Quote / Callout 전용 상수
# ---------------------------------------------------------------------------
#
# 세 컴포넌트 모두 "보조 텍스트" 계열이므로 한 블록으로 묶는다. SlideTitle
# 바로 아래 등장할 수 있는 SlideSubtitle, 본문 중간에 들어가는 Quote/Callout
# 각각의 시각 규칙을 상수로 고정해 Renderer 와 Test 가 동일 기준을 공유.

# SlideSubtitle — 20pt muted·center. SlideTitle 아래 얇게 깔림.
FONT_SIZE_SLIDE_SUBTITLE: Final[int] = 20
SLIDE_SUBTITLE_HEIGHT_IN: Final[float] = 0.5

# Quote — 들여쓴 인용 블록 + 좌측 세로 강조선.
FONT_SIZE_QUOTE: Final[int] = 16
FONT_SIZE_QUOTE_AUTHOR: Final[int] = 12
QUOTE_PADDING_LEFT_IN: Final[float] = 0.3  # 강조선 우측에 주는 본문 시작 여백.
QUOTE_BAR_WIDTH_IN: Final[float] = 0.055  # 좌측 세로 강조선 두께 (≈4pt).
QUOTE_LINE_HEIGHT_MULTIPLIER: Final[float] = 1.5  # 인용문 행간 배수.
QUOTE_MIN_HEIGHT_IN: Final[float] = 0.8
QUOTE_AUTHOR_HEIGHT_IN: Final[float] = 0.35

# Callout — variant 별 배경색 / 좌측 border 색. 순서 고정 (info/warning/success/danger).
CALLOUT_VARIANT_BG: Final[dict[str, str]] = {
    "info": "#E0F2FE",
    "warning": "#FEF3C7",
    "success": "#D1FAE5",
    "danger": "#FEE2E2",
}
CALLOUT_VARIANT_BORDER: Final[dict[str, str]] = {
    "info": IDINO_PRIMARY,  # #0A4FC2
    "warning": "#F59E0B",  # amber-500
    "success": "#10B981",  # green-500 (KPI_DELTA_UP 과 동일)
    "danger": "#EF4444",  # red-500  (KPI_DELTA_DOWN 과 동일)
}
FONT_SIZE_CALLOUT: Final[int] = 14
CALLOUT_PADDING_IN: Final[float] = 0.15  # 좌측 border 우측에 주는 본문 여백.
CALLOUT_BORDER_WIDTH_IN: Final[float] = 0.055  # 좌측 border 두께 (≈4pt).
CALLOUT_CORNER_RADIUS_IN: Final[float] = 0.08  # 둥근 사각형 모서리 반경.
CALLOUT_MIN_HEIGHT_IN: Final[float] = 0.7

# variant → 이니셜 대체 문자 (lucide 불가 → 텍스트 letter 로 대체).
CALLOUT_VARIANT_LETTER: Final[dict[str, str]] = {
    "info": "i",
    "warning": "!",
    "success": "✓",
    "danger": "!",
}


# ---------------------------------------------------------------------------
# S3 D7 — Timeline / IconRow 전용 상수
# ---------------------------------------------------------------------------

# Timeline — events 세로 리스트 + 좌측 마커(원) + 연결선.
TIMELINE_MAX_EVENTS: Final[int] = 5  # 이 값 초과 events 는 스킵 + WARN.
TIMELINE_EVENT_GAP_IN: Final[float] = 0.4  # 이벤트 간 세로 간격.
TIMELINE_MARKER_DIAMETER_IN: Final[float] = 0.2  # 좌측 원형 마커 직경.
TIMELINE_MARKER_COLUMN_WIDTH_IN: Final[float] = 0.45  # 마커가 차지하는 좌측 컬럼 폭.
TIMELINE_CONNECTOR_WIDTH_IN: Final[float] = 0.035  # 마커 간 세로 연결선 두께.
TIMELINE_EVENT_BODY_HEIGHT_IN: Final[float] = 0.85  # 이벤트 1 건의 본문 영역 높이.
FONT_SIZE_TIMELINE_DATE: Final[int] = 11
FONT_SIZE_TIMELINE_TITLE: Final[int] = 14
FONT_SIZE_TIMELINE_DESC: Final[int] = 11

# IconRow — items 가로 균등 배치. lucide 불가 → 큰 원형 + letter 대체.
ICON_ROW_CIRCLE_DIAMETER_IN: Final[float] = 0.9  # 각 item 의 원형 도형 직경.
ICON_ROW_LABEL_GAP_IN: Final[float] = 0.2  # 원과 라벨 사이 세로 간격.
ICON_ROW_LABEL_HEIGHT_IN: Final[float] = 0.4  # 라벨 박스 높이.
FONT_SIZE_ICON_ROW_LETTER: Final[int] = 24  # 원 안에 들어가는 letter.
FONT_SIZE_ICON_ROW_LABEL: Final[int] = 14
ICON_ROW_ITEM_GAP_IN: Final[float] = 0.1  # item 간 가로 여백.
