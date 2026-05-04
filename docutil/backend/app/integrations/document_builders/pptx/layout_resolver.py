"""PPTX 레이아웃 · 플레이스홀더 런타임 탐색기 (Phase 4 S2 D3).

Phase 0 진단에서 드러난 **PPT 슬라이드마스터 실패 근본원인** 의 핵심 해결책.

기존 ``backend/app/workers/report_generator.py::_build_layout_catalog()`` 는
IDINO 조직 전용 한글 레이아웃 이름 ("1_표지", "Ⅰ. 본문", "맺음말" 등) 을
**하드코딩 매칭** 하여, 다른 조직이 업로드한 슬라이드마스터에서는 catalog 가
빈 딕셔너리가 되어 `slide_layouts[0]` fallback → 레이아웃 깨짐 → PPT 생성
실패로 이어졌다.

본 모듈은 다음 3 가지 전략으로 이를 대체한다:

1. **후보 리스트(candidate pool) 방식**: 각 ``LayoutId`` 에 대해 "가능성 있는
   이름들" 을 튜플로 보관. 한글 / 영문 / 숫자+기호 표기가 모두 후보에 포함
   되므로 특정 조직 전용 이름이 바뀌어도 다른 후보로 매칭이 성립.
2. **조직별 override**: ``organization_overrides`` 인자로 런타임에 layout_id
   → 실제 이름 매핑을 주입받는다. 장래 ``tb_organizations.pptx_layout_overrides``
   JSONB 컬럼 에서 로드 예정 (D4~S4 이후). 본 D3 에서는 시그니처만 제공.
3. **Normalize 후 매칭**: 대소문자 / 공백 / 밑줄 / 하이픈 / 마침표 차이를
   제거한 정규화 키로 비교해 "title_slide" vs "Title Slide" vs "title-slide"
   등을 모두 동일하게 취급.

플레이스홀더 또한 마찬가지. 기존 하드코딩 idx (0/1/10/11/16) 는 IDINO 마스터
에만 유효하다. 본 모듈의 ``resolve_placeholder()`` 는 python-pptx 의
``PP_PLACEHOLDER`` enum 을 semantic 키와 매칭하여 idx 의존성을 제거한다.

설계 판단 포인트:

- **하드코딩 레이아웃 이름은 "후보" 로만 취급**: ``LAYOUT_NAME_CANDIDATES`` 에
  "1_표지", "맺음말" 같은 IDINO 전용 이름이 들어있긴 하지만, 이는 과거 호환성
  을 위한 **여러 후보 중 하나** 이지 단일 정답이 아니다. 이름 변경 · 번역 ·
  커스텀 모두 후보 추가 또는 override 로 흡수.
- **fallback 전략**: 모든 후보 매칭 실패 시 (1) blank layout(idx=6) → 없으면
  (2) slide_layouts[0] 을 반환 + WARNING 로그. 빌드 실패로 이어지지 않게.
- **semantic placeholder**: ``PP_PLACEHOLDER.TITLE`` 등 semantic enum 과
  ``placeholder_format.type`` 을 직접 매칭. idx 경로는 완전히 제거.

참조:
- backend/app/workers/report_generator.py `_build_layout_catalog` (하드코딩 원천 — 폐기 대상)
- docs/techspec.md §7.1.1 (PPT 슬라이드마스터 실패 근본원인), §8 H3
- docs/s2_d1_pptx_decomposition_plan.md §6 (D3 하드코딩 제거 전략)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Final, Literal

from pptx.enum.shapes import PP_PLACEHOLDER

if TYPE_CHECKING:
    from pptx.presentation import Presentation
    from pptx.shapes.placeholder import _InheritsPlaceholderFormat
    from pptx.slide import SlideLayout

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LayoutId — DocumentSchema.LayoutId (Phase 1) 와 동일 6 종
# ---------------------------------------------------------------------------
#
# schemas.py 의 ``LayoutId = Literal[...]`` 와 값이 일치해야 한다. 중복 선언
# 으로 보일 수 있으나, layout_resolver 모듈은 integration 계층 전용 타입을
# 쓰고 schemas.py 는 modules 계층의 DocumentSchema 타입을 정의한다. 두 레이어
# 가 같은 Literal 값을 공유함으로써 모듈 간 결합도를 낮추고 테스트에서 개별
# 사용 가능하게 유지한다.

LayoutId = Literal[
    "title_slide",
    "section_divider",
    "content_body",
    "kpi_dashboard",
    "two_column",
    "closing",
]


# ---------------------------------------------------------------------------
# 후보 이름 리스트 (hardcoded-as-candidates, not hardcoded-as-truth)
# ---------------------------------------------------------------------------
#
# 규칙:
#  - 영문 스네이크 케이스(캐논) 를 항상 첫 후보로.
#  - 영문 스페이스 / 하이픈 변형을 다음 후보로.
#  - 한글 번역(IDINO 마스터 호환) 을 추가.
#  - 숫자 + 기호 조합 (IDINO "1_표지" 등) 도 후보에.
#
# 매칭은 ``_normalize_name()`` 이후 소문자 비교 → 공백/언더스코어/하이픈은 모두
# 제거되므로 "Title Slide" / "title_slide" / "title-slide" / "TITLESLIDE" 는 동등.

LAYOUT_NAME_CANDIDATES: Final[dict[LayoutId, tuple[str, ...]]] = {
    "title_slide": (
        "title_slide",
        "title slide",
        "title-slide",
        "title",
        "cover",
        "cover page",
        "표지",
        "커버",
        "1_표지",
        "표지-앞면",
    ),
    "section_divider": (
        "section_divider",
        "section divider",
        "section",
        "section_header",
        "section header",
        "섹션",
        "섹션 전환",
        "소단원 표지",
        "2_소단원 표지",
    ),
    "content_body": (
        "content_body",
        "content body",
        "content",
        "body",
        "text",
        "본문",
        "일반 본문",
        "Ⅰ. 본문",
        "본문 - Ⅰ",
    ),
    "kpi_dashboard": (
        "kpi_dashboard",
        "kpi dashboard",
        "kpi",
        "dashboard",
        "4분할",
        "quad",
        "kpi 대시보드",
    ),
    "two_column": (
        "two_column",
        "two column",
        "two-column",
        "2단",
        "2 column",
        "comparison",
        "비교",
        "2단 비교",
    ),
    "closing": (
        "closing",
        "conclusion",
        "summary",
        "end",
        "맺음말",
        "결론",
        "마침화면",
        "9_마침화면",
        "요약",
    ),
}


# ---------------------------------------------------------------------------
# 이름 정규화
# ---------------------------------------------------------------------------


# 공백 / 언더스코어 / 하이픈 / 마침표 / 중점 을 모두 제거해 비교.
_NORMALIZE_STRIP_RE: Final = re.compile(r"[\s_\-.·]+")


def _normalize_name(name: str) -> str:
    """레이아웃 이름을 비교 가능한 정규화 형태로 변환.

    규칙:
      1) 문자열 앞뒤 공백 제거.
      2) 소문자 변환 (ASCII 만 영향, 한글은 그대로).
      3) 공백 / _ / - / . / · 모두 제거.

    예::
        "Title Slide"  → "titleslide"
        "title_slide"  → "titleslide"
        "title-slide"  → "titleslide"
        "1_표지"       → "1표지"
        "Ⅰ. 본문"      → "ⅰ본문"
    """
    return _NORMALIZE_STRIP_RE.sub("", name.strip().lower())


# ---------------------------------------------------------------------------
# resolve_layout — 런타임 레이아웃 탐색
# ---------------------------------------------------------------------------


def _iter_normalized_candidates(layout_id: LayoutId) -> list[str]:
    """특정 LayoutId 의 후보 이름을 정규화해 반환 (중복 제거, 등장 순서 유지)."""
    candidates = LAYOUT_NAME_CANDIDATES.get(layout_id, ())
    seen: set[str] = set()
    result: list[str] = []
    for raw in candidates:
        normalized = _normalize_name(raw)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _pick_fallback_layout(prs: Presentation) -> SlideLayout:
    """모든 매칭 실패 시 사용할 기본 레이아웃.

    우선순위:
      1) slide_layouts[6] (python-pptx 기본 템플릿의 blank) 가 존재하면 이를 사용.
      2) 없으면 slide_layouts[0].

    반환 전 경고 로그를 호출부가 남기므로 본 함수는 조용히 객체만 반환한다.
    """
    layouts = prs.slide_layouts
    if len(layouts) > 6:
        return layouts[6]
    return layouts[0]


def resolve_layout(
    prs: Presentation,
    layout_id: LayoutId,
    *,
    organization_overrides: dict[str, str] | None = None,
) -> SlideLayout:
    """``Presentation`` 의 실제 ``SlideLayout`` 을 런타임에 탐색·반환한다.

    우선순위:
      1) ``organization_overrides[layout_id]`` 가 있으면 그 이름으로 탐색.
         (조직별 커스텀 마스터의 한글 이름을 주입하는 공식 경로)
      2) ``LAYOUT_NAME_CANDIDATES[layout_id]`` 후보를 순회하며 현재 마스터의
         레이아웃 이름과 정규화 비교. 첫 매칭을 반환.
      3) 매칭 실패 시 fallback 레이아웃(blank) + WARNING 로그.

    Args:
        prs: 작업 중인 python-pptx ``Presentation`` 인스턴스.
        layout_id: 우리 스키마에서의 논리적 레이아웃 ID (6 종).
        organization_overrides: 조직별 override 매핑 (layout_id → 실제 이름).
            D3 단계에서는 시그니처만 유지, 실제 DB 로드는 S4 이후.

    Returns:
        탐색된 ``SlideLayout``. 실패해도 None 을 반환하지 않고 fallback 사용.

    Notes:
        - 매칭 성공 시 INFO.
        - 매칭 실패 시: ``organization_overrides`` 가 제공됐으면 WARNING (설정 오류
          의심), 미제공이면 INFO (기본 마스터에서는 정상 fallback). D9-b 에서
          WARNING 노이즈 감쇄를 위해 도입된 2 단 분기.
        - 빌드 실패로 이어지지 않게 하는 것이 최우선. "잘못된 레이아웃이라도
          있는 게 낫다" 전략.
    """
    # 마스터의 실제 레이아웃 이름 → 객체 매핑. 정규화 이름을 키로.
    actual_by_normalized: dict[str, SlideLayout] = {}
    for layout in prs.slide_layouts:
        # layout.name 은 str. None 이나 빈 값은 매우 드물지만 방어.
        actual_name = layout.name or ""
        normalized = _normalize_name(actual_name)
        if normalized and normalized not in actual_by_normalized:
            actual_by_normalized[normalized] = layout

    # (1) organization_overrides 우선.
    if organization_overrides:
        override_raw = organization_overrides.get(layout_id)
        if override_raw:
            override_key = _normalize_name(override_raw)
            if override_key in actual_by_normalized:
                matched = actual_by_normalized[override_key]
                logger.info(
                    "resolve_layout: layout_id=%s → organization override '%s' 매칭 (실제 name=%r)",
                    layout_id,
                    override_raw,
                    matched.name,
                )
                return matched
            logger.warning(
                "resolve_layout: layout_id=%s 의 override '%s' 가 마스터에 없어 후보 탐색으로 fallback",
                layout_id,
                override_raw,
            )

    # (2) 후보 리스트 순회.
    for candidate_key in _iter_normalized_candidates(layout_id):
        if candidate_key in actual_by_normalized:
            matched = actual_by_normalized[candidate_key]
            logger.info(
                "resolve_layout: layout_id=%s → 후보 '%s' 매칭 (실제 name=%r)",
                layout_id,
                candidate_key,
                matched.name,
            )
            return matched

    # (3) 실패 → fallback.
    #
    # D9-b — 로그 레벨 분기 기준:
    #   - ``organization_overrides`` 가 호출자로부터 주어졌다는 것은 "조직 마스터에
    #     맞춤 매핑이 존재하리라 기대" 한다는 의미이다. 그럼에도 매칭 실패했다면
    #     실제 설정(DB / JSONB) 오류 가능성이 높으므로 WARNING 유지 — 운영에서
    #     눈에 띄게 집계되어야 한다.
    #   - override 가 전혀 없는 경우는 "기본 python-pptx 마스터" 처럼 한글 후보가
    #     애초에 존재하지 않는 정상 케이스가 많다. 이 경우 fallback 은 의도된
    #     동작이므로 INFO 로 강등 — D8 리뷰에서 지적된 WARNING 노이즈 10 건은
    #     대부분 이 경로였다.
    #
    # 요약: override 제공 시 = WARNING (설정 오류 의심), 미제공 시 = INFO (정상 fallback).
    fallback = _pick_fallback_layout(prs)
    log_level = logging.WARNING if organization_overrides else logging.INFO
    logger.log(
        log_level,
        "resolve_layout: layout_id=%s 매칭 실패 — fallback 사용 (실제 name=%r). "
        "조직 슬라이드마스터에 대응하는 레이아웃이 없거나 이름이 크게 다릅니다. "
        "organization_overrides 를 통해 매핑을 주입하세요.",
        layout_id,
        fallback.name,
    )
    return fallback


# ---------------------------------------------------------------------------
# resolve_placeholder — semantic 키로 placeholder 탐색
# ---------------------------------------------------------------------------
#
# 기존 ``_build_pptx_from_structured`` 는 ``slide.placeholders[0]`` (타이틀),
# ``[1]`` (서브타이틀), ``[10]``/``[11]``/``[16]`` (IDINO 본문/날짜/슬라이드번호)
# 를 인덱스로 직접 참조. 이는 IDINO 마스터의 특정 배치에만 유효. 본 함수는
# ``placeholder_format.type`` (PP_PLACEHOLDER enum) 으로 의미 기반 매칭.

PlaceholderSemantic = Literal["title", "subtitle", "body", "date", "slide_number"]


# semantic 키 → python-pptx PP_PLACEHOLDER enum 후보. 일부 semantic 은 여러
# enum 과 호환 가능 (예: body 는 BODY / OBJECT 모두 허용).

_SEMANTIC_TO_PP_TYPES: Final[dict[PlaceholderSemantic, tuple[PP_PLACEHOLDER, ...]]] = {
    "title": (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE),
    "subtitle": (PP_PLACEHOLDER.SUBTITLE,),
    # BODY 가 주 타입이나, OBJECT 도 텍스트 블록으로 쓰이는 경우가 많음.
    "body": (PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.OBJECT),
    "date": (PP_PLACEHOLDER.DATE,),
    "slide_number": (PP_PLACEHOLDER.SLIDE_NUMBER,),
}


def resolve_placeholder(
    layout: SlideLayout,
    semantic: PlaceholderSemantic,
) -> _InheritsPlaceholderFormat | None:
    """레이아웃에서 semantic 키에 해당하는 placeholder 객체를 찾아 반환.

    python-pptx 의 ``layout.placeholders`` 를 순회하며 각 placeholder 의
    ``placeholder_format.type`` 이 semantic 키에 매핑된 PP_PLACEHOLDER enum 과
    일치하는 첫 번째 항목을 반환. 매칭 실패 시 ``None``.

    Args:
        layout: python-pptx ``SlideLayout``.
        semantic: 의미적 placeholder 키 (title / subtitle / body / date / slide_number).

    Returns:
        매칭된 placeholder (layout placeholder 객체) 또는 None.

    Notes:
        - 하드코딩 idx (0/1/10/11/16) 경로는 이 함수가 사라지게 하는 목적.
        - 호출부는 반환값이 None 인 경우 해당 placeholder 가 없다고 판단해
          skip 또는 textbox 로 fallback 해야 한다.
    """
    allowed_types = _SEMANTIC_TO_PP_TYPES.get(semantic, ())
    if not allowed_types:
        logger.warning(
            "resolve_placeholder: 알 수 없는 semantic=%r (지원: %s)",
            semantic,
            list(_SEMANTIC_TO_PP_TYPES.keys()),
        )
        return None

    for placeholder in layout.placeholders:
        # type 은 PP_PLACEHOLDER enum. 누락 시 None 반환 가능.
        ph_type = placeholder.placeholder_format.type
        if ph_type in allowed_types:
            return placeholder

    return None


__all__ = [
    "LAYOUT_NAME_CANDIDATES",
    "LayoutId",
    "PlaceholderSemantic",
    "resolve_layout",
    "resolve_placeholder",
]
