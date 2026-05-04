"""IDINO PPTX 텍스트 스타일 공용 헬퍼 (Phase 4 S2 D2).

`apply_idino_text_style()` 하나로 모든 components.py 렌더 함수가 폰트·크기·
굵기·색·정렬을 일관되게 적용하도록 모은 모듈. 기존 `report_generator.py` 의
`_set_tf_text` 에 흩어져 있던 스타일 로직을 파라미터화해 외부에서 재사용
가능하게 한다.

설계 판단 포인트:

1. **대상은 `TextFrame` 이 아니라 `Paragraph`**: `python-pptx` 에서 텍스트
   프레임(shape.text_frame) 은 여러 문단을 담을 수 있고, 각 문단이 여러 run
   으로 나뉜다. BulletList 처럼 항목별 스타일이 다른 경우 "텍스트 프레임 통째"
   에 스타일을 적용하면 모든 문단이 동일 스타일이 된다. 본 헬퍼는 **paragraph
   단위** 로 동작해 호출부가 필요한 경우 여러 번 호출할 수 있게 한다.

2. **hex → RGBColor 변환을 헬퍼 내부에서**: 호출부(components.py) 는 항상
   constants.py 의 hex 문자열로 색을 전달한다. RGBColor 변환은 단일 지점
   (`parse_hex_color`) 에 두어 잘못된 hex 에 대한 방어 검증을 중앙집중화.

3. **키워드 전용 인자**: `bold`, `color`, `font_name`, `alignment` 는 모두
   기본값이 있어 호출부가 원하는 것만 오버라이드한다. 위치 인자 섞임으로
   인한 실수를 방지.

4. **alignment 은 Optional[PP_ALIGN]**: None 이면 paragraph 기본값(LEFT) 유지.
   python-pptx 의 PP_ALIGN enum 을 직접 노출해 호출부가 필요 시 명시적으로
   지정할 수 있게 한다.

참조:
- backend/app/workers/report_generator.py `_set_tf_text` (이관 원천)
- backend/app/integrations/document_builders/pptx/constants.py (팔레트)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pptx.dml.color import RGBColor
from pptx.util import Pt

from app.integrations.document_builders.pptx.constants import (
    DEFAULT_FONT,
    IDINO_TEXT,
)

if TYPE_CHECKING:
    # PP_ALIGN / _Paragraph / TextFrame 은 타입 힌트 전용 — 런타임 사용 없음.
    from pptx.enum.text import PP_ALIGN
    from pptx.text.text import TextFrame, _Paragraph

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# hex 색 변환
# ---------------------------------------------------------------------------


def parse_hex_color(hex_str: str) -> RGBColor:
    """`#RRGGBB` 형태 hex 문자열을 `pptx.dml.color.RGBColor` 로 변환.

    DesignTokens / constants.py 가 hex 문자열 형태로 색을 보관하므로,
    실제 python-pptx 호출 시점에 변환이 필요하다.

    Args:
        hex_str: "#RRGGBB" 또는 "RRGGBB" (# 는 선택). 6 자리 16진수.

    Returns:
        RGBColor 인스턴스.

    Raises:
        ValueError: 형식 불일치 또는 16진수 파싱 실패.
    """
    # '#' prefix 제거 — FE 기본값은 '#' 포함, 내부 상수도 '#' 포함.
    s = hex_str.lstrip("#")
    if len(s) != 6:
        raise ValueError(f"잘못된 hex 색상 문자열입니다: {hex_str!r}. '#RRGGBB' 형식이어야 합니다.")
    try:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
    except ValueError as exc:  # pragma: no cover — len 체크 후엔 드문 경로.
        raise ValueError(f"16진수 파싱 실패: {hex_str!r}") from exc
    return RGBColor(r, g, b)


# ---------------------------------------------------------------------------
# 스타일 적용기 (Paragraph 단위)
# ---------------------------------------------------------------------------


def apply_idino_text_style(
    paragraph: _Paragraph,
    *,
    font_size: int,
    bold: bool = False,
    color: str | None = None,
    font_name: str = DEFAULT_FONT,
    alignment: PP_ALIGN | None = None,
) -> None:
    """단일 paragraph 에 IDINO 기본 텍스트 스타일을 적용한다.

    paragraph.runs 중 첫 번째 run 에 우선 적용하되, 모든 run 에 동일 스타일을
    퍼뜨린다(BulletList 렌더처럼 하나의 paragraph.text 를 통째 세팅해도 동작).
    run 이 비어있으면 paragraph.font 에 직접 적용.

    Args:
        paragraph: python-pptx `_Paragraph` 인스턴스 (textbox.text_frame.paragraphs[i] 등).
        font_size: 폰트 크기 (pt 단위).
        bold: True 면 굵게.
        color: "#RRGGBB" hex 문자열. None 이면 기본 본문 색(IDINO_TEXT) 적용.
        font_name: 폰트 패밀리 이름. 기본값은 Pretendard.
        alignment: PP_ALIGN enum. None 이면 paragraph 기본값(보통 LEFT) 유지.

    Notes:
        - paragraph.text 가 비어있는 상태에서 호출하면 run 이 없어서 색/굵기가
          실제 출력에 반영되지 않는다. 먼저 text 를 세팅한 뒤 호출할 것.
        - 호출자가 text 를 변경할 계획이라면 변경 **후** 에 스타일을 적용해야
          한다 — runs 가 재생성되기 때문.
    """
    resolved_color_hex = color if color is not None else IDINO_TEXT
    rgb = parse_hex_color(resolved_color_hex)

    # 정렬은 paragraph 레벨.
    if alignment is not None:
        paragraph.alignment = alignment

    # paragraph.font 에 적용 — 이후 추가되는 run 이 이 기본값을 상속한다.
    paragraph.font.name = font_name
    paragraph.font.size = Pt(font_size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = rgb

    # 이미 존재하는 run 들에도 동일 스타일 (기존 run 은 paragraph.font 를
    # 자동 상속하지 않으므로 명시적으로 덮어쓰기).
    for run in paragraph.runs:
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.color.rgb = rgb


def reset_text_frame(text_frame: TextFrame) -> _Paragraph:
    """텍스트 프레임을 비우고 첫 문단을 반환하는 편의 함수.

    `text_frame.clear()` 는 첫 문단을 남기고 나머지를 지우며, 남은 문단도
    텍스트는 비어있고 run 은 0 개다. 이 상태에서 단일 paragraph 에 텍스트를
    쓰고 싶을 때 사용한다.
    """
    text_frame.clear()
    return text_frame.paragraphs[0]
