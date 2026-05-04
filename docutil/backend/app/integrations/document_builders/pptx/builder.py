"""PptxBuilder — DocumentSchema → PPTX 바이트 빌더 (Phase 4 S2 D1 골격 → D3 확장).

`DocumentBuilder` ABC 를 상속한 두 번째 구체 빌더. S1 에서 확정한
`BuilderRegistry` 시그니처(`async def build(schema) -> bytes`) 를 그대로
준수한다.

**S2 D1 범위(완료)**: 빌더 계약·Registry 등록 · 빈 PPTX 반환 골격.
**S2 D2 범위(완료)**: 텍스트 계열 4 종 컴포넌트(SlideTitle / Heading /
Paragraph / BulletList) 를 단일 blank 레이아웃에 수동 배치하는 경로 구현.
**S2 D3 범위(본 업데이트)**:
  - KPI / DataTable 2 종 컴포넌트 렌더 추가.
  - `layout_resolver.resolve_layout()` 통합 — page.layout (LayoutId 6 종) 에
    따라 런타임에 실제 SlideLayout 을 탐색. 하드코딩 한글 이름 매칭 폐기.

설계 판단 포인트:

1. **layout_resolver 통합 (D3)**: D2 에서 `slide_layouts[6]` (blank) 로 단일
   레이아웃만 쓰던 것을 `resolve_layout(prs, page.layout)` 로 교체. Pydantic
   의 `LayoutId` Literal 6 종이 그대로 layout_resolver 의 LayoutId 와 값으로
   일치한다. 매칭 실패 시 layout_resolver 내부에서 blank fallback 처리하므로
   빌드는 절대 실패하지 않는다.

2. **async 시그니처 유지**: base.py ABC 와 HtmlRenderer 를 따라 `async def
   build`. 실제 I/O 는 없지만 P1 을 위해 시그니처 고정.

3. **Y 스택 계산은 builder 에서**: components.py 의 각 렌더 함수는 "현재 Y
   입력 → 배치 후 다음 Y 반환" 계약을 가진다. 한 슬라이드 내 여러 컴포넌트
   누적은 본 모듈 `_render_page()` 가 담당.

4. **SlideTitle 은 고정 좌표, 나머지는 동적 Y 스택**: SlideTitle 은 항상
   상단 중앙이므로 고정 좌표를 사용하고 Y 반환값을 다음 컴포넌트의 시작점
   으로 쓴다. 페이지에 SlideTitle 이 없으면 Heading 부터 기본 HEADING_TOP_IN
   에서 시작.

5. **미지원 컴포넌트(KPI/DataTable/Image/Chart 등) 의 D2 fallback**: 본 D2 는
   4 종만 구현하고 나머지는 "skip + 경고 로그" 처리. 빌드 실패로 이어지지
   않는다 (P5 의 "외부 오류 swallow 금지" 와 다른 차원 — 미지원 컴포넌트는
   오류가 아닌 "아직 이관되지 않음"). `validate_components()` 와 함께 동작.

참조:
- docs/phase1_architecture.md §3, §5.3, §7
- docs/phase3_execution_roadmap.md §2.2 S2 D1~D3
- docs/s2_d1_pptx_decomposition_plan.md (D2 이관 계획)
- backend/app/workers/report_generator.py `_build_pptx_from_structured` (이관 대상)
- backend/app/integrations/document_builders/html/renderer.py (동일 ABC 구현체)
"""

from __future__ import annotations

import io
import logging
from typing import TYPE_CHECKING, ClassVar

# integration layer 예외 — 외부 SDK 직접 import 허용 범위.
# python-pptx 는 본 모듈과 하위 helpers 외에서는 절대 사용 금지 (P1 단일 구현).
from pptx import Presentation
from pptx.util import Inches

from app.integrations.document_builders.base import BuildTarget, DocumentBuilder
from app.integrations.document_builders.pptx import components as pptx_components
from app.integrations.document_builders.pptx.constants import (
    BODY_LEFT_IN,
    BODY_WIDTH_IN,
    CHART_DEFAULT_WIDTH_IN,
    COMPONENT_VERTICAL_GAP_IN,
    FONT_SIZE_SLIDE_TITLE,
    HEADING_TOP_IN,
    IDINO_PRIMARY,
    IMAGE_DEFAULT_WIDTH_IN,
    KPI_CARD_HEIGHT_IN,
    KPI_CARD_WIDTH_IN,
    SLIDE_HEIGHT_IN,
    SLIDE_TITLE_HEIGHT_IN,
    SLIDE_TITLE_TOP_IN,
    SLIDE_WIDTH_IN,
)
from app.integrations.document_builders.pptx.layout_resolver import (
    resolve_layout,
    resolve_placeholder,
)
from app.integrations.document_builders.pptx.style import apply_idino_text_style
from app.modules.documents_v2.schemas import (
    BulletListComponent,
    CalloutComponent,
    ChartComponent,
    DataTableComponent,
    HeadingComponent,
    IconRowComponent,
    ImageComponent,
    ImageGridComponent,
    KPIComponent,
    ParagraphComponent,
    QuoteComponent,
    SlideSubtitleComponent,
    SlideTitleComponent,
    TimelineComponent,
)

if TYPE_CHECKING:
    from pptx.presentation import Presentation as PresentationType
    from pptx.slide import Slide

    from app.modules.documents_v2.schemas import Component, DocumentSchema, Page

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PptxBuilder
# ---------------------------------------------------------------------------


class PptxBuilder(DocumentBuilder):
    """DocumentSchema → PPTX (OOXML) 바이트.

    **S2 D3 범위** — 6 종 컴포넌트(SlideTitle / Heading / Paragraph /
    BulletList / KPI / DataTable) 를 layout_resolver 로 탐색된 실제 슬라이드
    레이아웃 위에 배치한다. Image / Chart 등은 S2 D6~D7 에서 이관 예정.

    Degradation 정책:
      - `supported_components` 에 선언된 6 종 외의 16 종 컴포넌트는 "skip +
        경고 로그" 로 우아하게 degrade — 빌드 실패로 이어지지 않는다.
      - layout_resolver 가 레이아웃 매칭에 실패해도 blank fallback 을 반환
        하므로 빌드는 계속 진행된다 (WARNING 로그만).
    """

    target: ClassVar[BuildTarget] = "pptx"
    supported_components: ClassVar[frozenset[str]] = frozenset(
        {
            "SlideTitle",  # S2 D2 구현 완료
            "Heading",  # S2 D2 구현 완료
            "Paragraph",  # S2 D2 구현 완료
            "BulletList",  # S2 D2 구현 완료
            "KPI",  # S2 D3 구현 완료
            "DataTable",  # S2 D3 구현 완료
            "Image",  # S2 D6 구현 완료
            "Chart",  # S3 D1 확장 — bar/line/pie native (pie 특수 처리: 단일 시리즈·축 없음)
            "ImageGrid",  # S3 D2 신규 — 2~4 장 자동 격자 레이아웃
            "SlideSubtitle",  # S3 D6 신규 — SlideTitle 아래 보조 제목
            "Quote",  # S3 D6 신규 — 인용 블록 + 좌측 강조선
            "Callout",  # S3 D6 신규 — variant 별 배경·border (info/warning/success/danger)
            "Timeline",  # S3 D7 신규 — 세로 이벤트 리스트 + 마커·연결선
            "IconRow",  # S3 D7 신규 — 가로 균등 배치 (원형 + letter + 라벨)
        }
    )

    # -- 메인 진입점 ---------------------------------------------------------

    async def build(self, schema: DocumentSchema) -> bytes:
        """DocumentSchema 를 PPTX 파일 바이트로 변환한다.

        흐름:
          1) 16:9 기본 Presentation 생성 (slide_width/height 세팅).
          2) blank 레이아웃 선택 (slide_layouts[6] 우선, 없으면 [0] fallback).
          3) `schema.pages` 순회 → 각 페이지마다 add_slide() → `_render_page()`.
          4) BytesIO 경유로 bytes 반환.

        Args:
            schema: 변환 대상 문서 스키마. Pydantic 이 이미 타입·제약 검증 완료.

        Returns:
            OOXML(ZIP) 포맷 PPTX 바이트. `b"PK"` ZIP 시그니처로 시작.

        Notes:
            - 미지원 컴포넌트는 `validate_components()` 로 탐지 후 페이지
              렌더 중 "skip + WARN 로그" 로 degrade.
            - 슬라이드 수 = len(schema.pages). Pydantic 이 pages: min_length=1
              을 보장하므로 최소 1 장.
        """
        unsupported = self.validate_components(schema)
        if unsupported:
            # 현재 범위에서 미지원인 컴포넌트들은 INFO 로그 후 skip (빌드 실패 X).
            logger.info(
                "PptxBuilder: 이번 범위에서 미지원 컴포넌트 %d 종 skip — %s",
                len(unsupported),
                ", ".join(unsupported),
            )

        # 16:9 Presentation 생성. python-pptx 기본은 4:3 이므로 명시적 세팅.
        prs = Presentation()
        prs.slide_width = Inches(SLIDE_WIDTH_IN)
        prs.slide_height = Inches(SLIDE_HEIGHT_IN)

        # 각 페이지를 한 슬라이드로 렌더.
        for page in schema.pages:
            self._render_page(page, prs)

        # BytesIO 경유로 바이트 추출.
        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()

    # -- 페이지 렌더러 -------------------------------------------------------

    def _render_page(self, page: Page, prs: PresentationType) -> None:
        """단일 Page 를 PPTX 슬라이드로 렌더.

        D3 범위 동작:
          - `resolve_layout(prs, page.layout)` 로 실제 SlideLayout 탐색.
          - 매칭 실패 시 layout_resolver 내부 fallback (blank/[0]) 이 동작.
          - `page.components` 를 순회하며 `_render_component()` 호출.
          - KPI 가 연속으로 나오면 같은 Y 레벨에 가로로 나란히 배치.
          - Y 좌표는 컴포넌트별 반환값으로 누적.
          - speaker_notes 가 있으면 notes_slide 에 기록.

        Args:
            page: 렌더 대상 페이지.
            prs: python-pptx Presentation 객체 (호출자 소유).
        """
        # D3 — page.layout (LayoutId 6 종) 을 런타임 탐색. 하드코딩 제거.
        selected_layout = resolve_layout(prs, page.layout)
        slide = prs.slides.add_slide(selected_layout)

        # Y 스택 추적. SlideTitle 이 없는 페이지는 HEADING_TOP_IN 부터 시작.
        current_y: float = HEADING_TOP_IN

        # KPI 들을 한 줄에 몰아두기 위한 버퍼. 연속된 KPI 는 같은 Y 레벨에
        # 가로로 나란히 배치 → 4 개까지 한 줄. 비-KPI 를 만나면 flush.
        kpi_buffer: list[KPIComponent] = []

        def _flush_kpi_row() -> None:
            """쌓인 KPI 버퍼를 같은 Y 행에 가로로 렌더하고 Y 를 진행시킨다."""
            nonlocal current_y
            if not kpi_buffer:
                return
            self._render_kpi_row(kpi_buffer, slide, top_in=current_y)
            current_y += KPI_CARD_HEIGHT_IN + COMPONENT_VERTICAL_GAP_IN
            kpi_buffer.clear()

        for component in page.components:
            if isinstance(component, KPIComponent):
                kpi_buffer.append(component)
                continue
            # 비-KPI 직전에 KPI 버퍼를 flush.
            _flush_kpi_row()
            next_y = self._render_component(component, slide, current_y)
            # 렌더 함수가 None 을 반환하면(skip 케이스) 현재 Y 유지.
            if next_y is not None:
                current_y = next_y

        # 페이지 끝에 남은 KPI 들도 flush.
        _flush_kpi_row()

        # speaker_notes 는 별도 텍스트 프레임 없이 발표자 노트에만 저장.
        if page.speaker_notes:
            try:
                slide.notes_slide.notes_text_frame.text = page.speaker_notes
            except Exception:  # pragma: no cover — 노트 기록 실패는 빌드 실패가 아님.
                logger.debug("PptxBuilder: 발표자 노트 기록 실패 (무시)", exc_info=True)

    # -- KPI row 렌더러 -----------------------------------------------------

    def _render_kpi_row(
        self,
        kpis: list[KPIComponent],
        slide: Slide,
        *,
        top_in: float,
    ) -> None:
        """같은 Y 행에 여러 KPI 를 가로로 나란히 배치.

        규칙:
          - 최대 4 개까지 한 줄. 가로 공간이 넘치면 카드 너비를 줄여 균등 분할.
          - 좌측 BODY_LEFT_IN 부터 시작, 전체 너비 BODY_WIDTH_IN 이내에서 배치.
          - 카드 간 gap = COMPONENT_VERTICAL_GAP_IN (양쪽 여백에 재사용).

        Args:
            kpis: 렌더할 KPIComponent 리스트 (1 개 이상).
            slide: python-pptx Slide.
            top_in: KPI 행 상단 Y 좌표 (인치).
        """
        if not kpis:
            return
        count = len(kpis)
        gap = COMPONENT_VERTICAL_GAP_IN
        total_gap = gap * (count - 1)
        # 각 카드가 가져야 할 너비. 균등 분할 후 최대 기본 카드 너비로 cap.
        even_width = (BODY_WIDTH_IN - total_gap) / count
        card_width = min(KPI_CARD_WIDTH_IN, even_width)

        # 실제 점유 너비. 카드 너비가 작아졌으면 좌측 정렬, 카드 수가 적으면
        # 중앙 정렬이 더 자연스럽지만 단순화를 위해 좌측 정렬.
        left_x = BODY_LEFT_IN
        for kpi in kpis:
            pptx_components.render_kpi(
                kpi,
                slide,
                left_in=left_x,
                top_in=top_in,
                width_in=card_width,
            )
            left_x += card_width + gap

    # -- placeholder-first 주입 헬퍼 (D9-a) --------------------------------

    def _render_slide_title_into_placeholder(
        self,
        component: SlideTitleComponent,
        slide: Slide,
    ) -> bool:
        """SlideTitle 을 슬라이드 마스터의 TITLE placeholder 에 주입.

        D9-a 도입 이유:
          D8 A/B 리뷰에서 Sample A~E 총 50 항목 중 10 항목이 "placeholder 미활용"
          WARN 으로 집계. 기존 구현은 `resolve_placeholder()` 가 정의만 돼 있고
          builder 에선 항상 textbox 직접 배치 경로만 사용 → IDINO 실 마스터의
          타이틀 placeholder 가 비어버리는 문제 발생.

        동작 조건 (3 단 분기):
          1) ``slide.slide_layout`` 에 TITLE/CENTER_TITLE placeholder 가 존재하고,
          2) 슬라이드 자체에 해당 idx 의 placeholder 가 상속돼 있고,
          3) 실제 주입 과정에서 예외가 발생하지 않으면 → True 반환.
          위 조건 중 하나라도 어긋나면 False 반환 → 호출부가 기존 textbox
          경로로 자동 fallback.

        예외 처리:
          - python-pptx 의 layout / placeholder API 는 드물게 AttributeError /
            KeyError 를 내므로, 주입 실패는 모두 False 반환으로 치환한다.
            fallback 경로가 존재하므로 빌드 실패로 이어지지 않는다 (P5 의
            "swallow 금지" 는 외부 서비스 오류가 대상 — 여기선 "degrade 경로"
            가 의도된 설계).

        Args:
            component: 렌더할 SlideTitleComponent.
            slide: 이미 add_slide 된 python-pptx Slide.

        Returns:
            True = placeholder 주입 성공 (textbox 추가 불필요),
            False = placeholder 없음/실패 (호출부가 textbox 경로 fallback 필요).
        """
        try:
            layout_title_ph = resolve_placeholder(slide.slide_layout, "title")
        except Exception:  # pragma: no cover — layout 객체 이상은 드묾.
            logger.debug(
                "PptxBuilder: resolve_placeholder 예외 — textbox fallback",
                exc_info=True,
            )
            return False

        if layout_title_ph is None:
            # 마스터에 TITLE placeholder 자체가 없음 → 기존 textbox 경로 fallback.
            return False

        # layout 의 placeholder idx 가 슬라이드 placeholder 로 상속돼 있는지 확인.
        # python-pptx 는 layout placeholder 를 슬라이드에 자동 복제하지 않을 수
        # 있으므로 idx 매칭으로 직접 찾는다.
        target_idx = layout_title_ph.placeholder_format.idx
        try:
            for ph in slide.placeholders:
                if ph.placeholder_format.idx != target_idx:
                    continue
                # 텍스트 주입 + IDINO 스타일 적용.
                ph.text = component.text
                # reset 후 첫 paragraph 에만 스타일 — BulletList 아님이므로 단일.
                if ph.text_frame.paragraphs:
                    apply_idino_text_style(
                        ph.text_frame.paragraphs[0],
                        font_size=FONT_SIZE_SLIDE_TITLE,
                        bold=True,
                        color=IDINO_PRIMARY,
                    )
                logger.info(
                    "PptxBuilder: SlideTitle 을 마스터 TITLE placeholder 에 주입 (idx=%d)",
                    target_idx,
                )
                return True
        except Exception:  # pragma: no cover — placeholder 주입 실패는 희귀.
            logger.debug(
                "PptxBuilder: TITLE placeholder 주입 실패 — textbox fallback",
                exc_info=True,
            )
            return False

        # layout 에는 있으나 슬라이드에 상속 안 된 경우 — 역시 fallback.
        return False

    # -- 컴포넌트 디스패처 --------------------------------------------------

    def _render_component(
        self,
        component: Component,
        slide: Slide,
        current_y: float,
    ) -> float | None:
        """단일 Component 를 슬라이드 위에 렌더.

        Discriminated Union isinstance 분기 (HtmlRenderer 와 동일 패턴) 로
        타입별 components.py 함수에 dispatch. 미지원/미구현 타입은 skip +
        WARN 로그, 반환값 None → 호출부가 Y 를 그대로 유지.

        Note:
            KPIComponent 는 이 함수로 들어오지 않는다 — `_render_page` 가
            버퍼링 후 `_render_kpi_row` 로 일괄 렌더하기 때문. 방어적으로
            본 함수에서도 단일 KPI 렌더는 지원.

        Args:
            component: 렌더 대상 컴포넌트 (Discriminated Union 인스턴스).
            slide: python-pptx Slide 객체.
            current_y: 현재 Y 스택 (인치). top_in 인자로 전달.

        Returns:
            다음 컴포넌트가 쓸 Y 좌표 (인치). skip 시 None.
        """
        # SlideTitle 은 고정 좌표 (상단 중앙) 이므로 current_y 를 무시.
        #
        # D9-a — placeholder-first 전략: 슬라이드 마스터에 TITLE placeholder 가
        # 있으면 우선 그쪽에 주입한다. 실패하면 기존 textbox 경로로 자동 fallback —
        # 어떤 마스터에서도 빌드가 깨지지 않는다. 이 경로를 타면 IDINO 실 마스터의
        # 상단 타이틀 placeholder 가 자동으로 채워져 D8 리뷰의 WARN 5 건이 해소된다.
        if isinstance(component, SlideTitleComponent):
            if self._render_slide_title_into_placeholder(component, slide):
                # placeholder 주입 성공 시: textbox 를 추가하지 않으므로
                # render_slide_title 과 동일한 Y 진행값을 수동으로 계산해 반환한다.
                return SLIDE_TITLE_TOP_IN + SLIDE_TITLE_HEIGHT_IN + COMPONENT_VERTICAL_GAP_IN
            return pptx_components.render_slide_title(component, slide)

        if isinstance(component, HeadingComponent):
            return pptx_components.render_heading(component, slide, top_in=current_y)

        if isinstance(component, ParagraphComponent):
            return pptx_components.render_paragraph(component, slide, top_in=current_y)

        if isinstance(component, BulletListComponent):
            return pptx_components.render_bullet_list(component, slide, top_in=current_y)

        # D3 — KPI 단일 렌더 (실제로는 _render_page 에서 버퍼링).
        if isinstance(component, KPIComponent):
            return pptx_components.render_kpi(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=KPI_CARD_WIDTH_IN,
            )

        # D3 — DataTable. 전체 본문 너비 사용.
        if isinstance(component, DataTableComponent):
            return pptx_components.render_data_table(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=BODY_WIDTH_IN,
            )

        # D6 — Image. 남은 슬라이드 세로 공간에 맞춰 max_height 를 동적 계산.
        #   SLIDE_HEIGHT_IN 에서 현재 Y 와 하단 여백(0.3") 을 뺀 값을 상한으로 사용.
        #   너비는 IMAGE_DEFAULT_WIDTH_IN (본문의 약 60%) 을 기본값으로 준다 —
        #   이미지는 좌우 중앙으로 쏠리지 않고 좌측 정렬(좌측 BODY_LEFT_IN 기준)
        #   되지만 본문의 일부 폭만 차지하여 Paragraph 와 공존하기 쉽다.
        if isinstance(component, ImageComponent):
            remaining_height = SLIDE_HEIGHT_IN - current_y - 0.3
            return pptx_components.render_image(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=IMAGE_DEFAULT_WIDTH_IN,
                max_height_in=max(0.5, remaining_height),
            )

        # D7 — Chart. Image 와 동일하게 남은 슬라이드 세로 공간을 상한으로 사용.
        #   너비는 CHART_DEFAULT_WIDTH_IN (본문의 약 70%) 로 이미지보다 조금 넓게 —
        #   범례/축 라벨까지 포함하는 차트 특성상 가로 공간이 더 필요하다.
        if isinstance(component, ChartComponent):
            remaining_height = SLIDE_HEIGHT_IN - current_y - 0.3
            return pptx_components.render_chart(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=CHART_DEFAULT_WIDTH_IN,
                max_height_in=max(0.5, remaining_height),
            )

        # S3 D2 — ImageGrid. 본문 전체 너비를 사용해 2~4 장 자동 격자 배치.
        #   남은 세로 공간을 상한으로 하되, 한 페이지 내 다른 컴포넌트와 공존할
        #   수 있도록 4" 로 상한을 한 번 더 걸어 과도한 영역 점유를 방지.
        if isinstance(component, ImageGridComponent):
            remaining_height = SLIDE_HEIGHT_IN - current_y - 0.3
            grid_max_height = min(4.0, max(1.0, remaining_height))
            return pptx_components.render_image_grid(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=BODY_WIDTH_IN,
                max_height_in=grid_max_height,
            )

        # S3 D6 — SlideSubtitle. SlideTitle 과 비슷하게 고정 좌표(상단) 을 쓰되,
        # current_y 가 이미 아래로 내려갔다면 그 위치를 존중 (Subtitle 단독 사용도 가능).
        if isinstance(component, SlideSubtitleComponent):
            # current_y 가 초기값(HEADING_TOP_IN=1.7) 이하이면 SlideTitle 바닥 바로 아래로
            # 기본 배치. 그 외엔 현재 Y 를 그대로 사용해 유연성 확보.
            subtitle_top = current_y if current_y > 1.7 else None
            return pptx_components.render_slide_subtitle(
                component,
                slide,
                top_in=subtitle_top,
            )

        # S3 D6 — Quote. 본문 너비 사용. 들여쓴 인용 블록 + 좌측 강조선.
        if isinstance(component, QuoteComponent):
            return pptx_components.render_quote(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=BODY_WIDTH_IN,
            )

        # S3 D6 — Callout. variant 별 배경색/border. 본문 너비 사용.
        if isinstance(component, CalloutComponent):
            return pptx_components.render_callout(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=BODY_WIDTH_IN,
            )

        # S3 D7 — Timeline. 세로 이벤트 리스트. 남은 세로 공간을 상한으로.
        if isinstance(component, TimelineComponent):
            remaining_height = SLIDE_HEIGHT_IN - current_y - 0.3
            return pptx_components.render_timeline(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=BODY_WIDTH_IN,
                max_height_in=max(1.0, remaining_height),
            )

        # S3 D7 — IconRow. 가로 균등 배치.
        if isinstance(component, IconRowComponent):
            return pptx_components.render_icon_row(
                component,
                slide,
                left_in=BODY_LEFT_IN,
                top_in=current_y,
                width_in=BODY_WIDTH_IN,
            )

        # 14 종 외 — 아직 이관되지 않은 컴포넌트. skip + WARN.
        logger.warning(
            "PptxBuilder: 미지원 컴포넌트 skip — type=%s (S3 이후 이관 예정)",
            component.type,
        )
        return None
