"""Phase 4 S2 D8-a — PPTX A/B 비교용 샘플 5건 생성 스크립트.

목적:
    D1~D7 에서 완성한 신규 `PptxBuilder` (BuilderRegistry 경유) 에
    DocumentSchema 5 가지 변형을 직접 Pydantic 객체로 주입해 PPTX bytes 를
    얻고, 결과 파일을 `docs/s2_d8_samples/` 아래에 저장한다.

왜 LLM 을 쓰지 않는가:
    - D8 은 **빌더 출력물의 시각·구조 품질** 을 평가하는 단계이지
      Mode A 프롬프트 → Structured Output 변환 품질을 보는 단계가 아니다.
    - LLM 은 같은 프롬프트에도 출력이 달라지므로 "변화 추적" 이 어렵다.
    - 직접 Pydantic 객체를 구성하면 입력이 고정 → 빌더 개선 전후 차이가
      명확해진다.

샘플 구성 (모두 `document_type="slide_report"`, `mode="free_generation"`):
    A. 텍스트 중심       — SlideTitle + Heading + Paragraph + BulletList
    B. KPI 대시보드     — SlideTitle + KPI×4 + Paragraph
    C. 테이블 중심       — SlideTitle + DataTable + Paragraph
    D. 차트 2종          — SlideTitle + Chart(bar) + Chart(line) + Heading
    E. 미디어 포함       — SlideTitle + Image(placeholder) + Paragraph + BulletList

제약:
    - `BuilderRegistry.get("pptx")` 경유로 PptxBuilder 인스턴스 획득 (P1).
    - 절대 python-pptx 를 직접 호출하지 않음 (P1 단일 구현).
    - 각 샘플 생성 시간을 `time.perf_counter()` 로 측정해 metadata.json 에 기록.

산출물:
    - docs/s2_d8_samples/sample_a_text.pptx
    - docs/s2_d8_samples/sample_b_kpi.pptx
    - docs/s2_d8_samples/sample_c_table.pptx
    - docs/s2_d8_samples/sample_d_chart.pptx
    - docs/s2_d8_samples/sample_e_media.pptx
    - docs/s2_d8_samples/metadata.json
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# ---------------------------------------------------------------------------
# 경로 — backend/ 를 sys.path 에 먼저 추가해야 app.* 임포트가 가능.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(r"D:\workspace\document_utilization")
BACKEND_ROOT = PROJECT_ROOT / "backend"
SAMPLES_DIR = PROJECT_ROOT / "docs" / "s2_d8_samples"

sys.path.insert(0, str(BACKEND_ROOT))

# app.* 임포트는 sys.path 세팅 이후에 수행해야 하므로 위치가 고정.
# ruff: noqa: E402 — 의도된 지연 임포트.
from app.integrations.document_builders import BuilderRegistry  # noqa: E402
from app.integrations.document_builders.pptx import (  # noqa: E402 — 부수효과로 레지스트리 등록.
    register_pptx_builder,
)
from app.modules.documents_v2.schemas import (  # noqa: E402
    BulletItem,
    BulletListComponent,
    ChartComponent,
    ChartData,
    ChartSeries,
    DataTableComponent,
    DesignTokens,
    DocumentMetadata,
    DocumentSchema,
    HeadingComponent,
    ImageComponent,
    KPIComponent,
    Page,
    ParagraphComponent,
    SlideTitleComponent,
)


# ---------------------------------------------------------------------------
# 상수 — 하드코딩 금지를 위해 샘플 정의에 사용될 고정 값들을 한 곳에 모음.
# ---------------------------------------------------------------------------

# 샘플 ID (파일명 일부로 사용).
SAMPLE_A_ID = "sample_a_text"
SAMPLE_B_ID = "sample_b_kpi"
SAMPLE_C_ID = "sample_c_table"
SAMPLE_D_ID = "sample_d_chart"
SAMPLE_E_ID = "sample_e_media"

# 공통 metadata 헬퍼에 사용할 생성 주체 태그.
GENERATED_BY_TAG = "phase4_s2_d8_ab_review"


def _fresh_metadata() -> DocumentMetadata:
    """샘플별 고유 metadata 를 생성한다.

    created_at / updated_at 은 호출 시점의 UTC 로 고정. LLM 관련 필드는
    None (본 샘플은 LLM 미경유).
    """
    now = datetime.now(tz=timezone.utc)
    return DocumentMetadata(
        created_at=now,
        updated_at=now,
        generated_by_user_id=None,
        llm_provider=None,
        llm_model=None,
        prompt_tokens=None,
        completion_tokens=None,
        source_document_ids=[],
        source_chat_session_id=None,
        citations=[],
        degraded_components=[],
    )


def _doc_wrapper(*, page: Page) -> DocumentSchema:
    """단일 페이지로 구성된 DocumentSchema 를 만든다.

    모든 샘플은 1 슬라이드 구성으로 평가를 단순화한다 — 여러 페이지 결합
    케이스는 S2 D9 에서 다룬다.
    """
    return DocumentSchema(
        document_id=uuid4(),
        schema_version="1.0",
        type="slide_report",
        mode="free_generation",
        template_id=None,
        design_tokens=DesignTokens(),  # 기본 IDINO 프리셋.
        pages=[page],
        metadata=_fresh_metadata(),
    )


# ---------------------------------------------------------------------------
# 샘플 A — 텍스트 중심
# ---------------------------------------------------------------------------


def build_sample_a() -> DocumentSchema:
    """SlideTitle + Heading + Paragraph + BulletList 의 기본 텍스트 조합.

    목적:
        - 가장 단순한 4 종 조합에서 IDINO 색/폰트/간격이 잘 적용되는지 확인.
        - Y 스택 누적이 깨지지 않는지 시각 검증 기준점으로 사용.
    """
    return _doc_wrapper(
        page=Page(
            id="p1",
            page_kind="slide",
            layout="content_body",
            title="텍스트 중심 샘플",
            locked=False,
            components=[
                SlideTitleComponent(id="c1", text="2026년 1분기 업무 추진 현황"),
                HeadingComponent(id="c2", text="핵심 성과 요약", level=1),
                ParagraphComponent(
                    id="c3",
                    text=(
                        "문서 활용 시스템(DocUtil) 신규 보고서 엔진의 PPTX 빌더 "
                        "모듈화가 완료되었으며, Phase 0 진단에서 지적된 IDINO 전용 "
                        "레이아웃 하드코딩 문제가 해소되었다."
                    ),
                    emphasis="normal",
                ),
                BulletListComponent(
                    id="c4",
                    items=[
                        BulletItem(
                            text="PptxBuilder 신설 — layout_resolver 기반 런타임 탐색",
                            emphasis="bold",
                        ),
                        BulletItem(
                            text="컴포넌트 8 종 렌더러 완성 (D2~D7)",
                            emphasis="normal",
                            sub_items=[
                                "SlideTitle / Heading / Paragraph / BulletList",
                                "KPI / DataTable / Image / Chart",
                            ],
                        ),
                        BulletItem(
                            text="IDINO 디자인 시스템 색상 상수 중앙화",
                            emphasis="highlight",
                        ),
                    ],
                    numbered=False,
                ),
            ],
            speaker_notes="발표자 노트 예시 — 텍스트 중심 샘플의 발표 대본입니다.",
            page_number_visible=True,
        ),
    )


# ---------------------------------------------------------------------------
# 샘플 B — KPI 대시보드
# ---------------------------------------------------------------------------


def build_sample_b() -> DocumentSchema:
    """SlideTitle + KPI×4 + Paragraph 의 대시보드 조합.

    목적:
        - KPI 4 개가 가로 한 줄에 균등 배치되는지 확인 (`_render_kpi_row`).
        - delta_direction 별 색상(up/down/flat) 이 팔레트와 일치하는지 확인.
    """
    return _doc_wrapper(
        page=Page(
            id="p1",
            page_kind="slide",
            layout="kpi_dashboard",
            title="KPI 대시보드 샘플",
            locked=False,
            components=[
                SlideTitleComponent(id="c1", text="2026년 1분기 주요 지표"),
                KPIComponent(
                    id="c2",
                    label="월간 활성 사용자",
                    value="18,420",
                    delta="+12.4%",
                    delta_direction="up",
                    description="전월 대비 증가",
                ),
                KPIComponent(
                    id="c3",
                    label="평균 응답 시간",
                    value="142ms",
                    delta="-8.2%",
                    delta_direction="down",
                    description="성능 개선",
                ),
                KPIComponent(
                    id="c4",
                    label="신규 문서 업로드",
                    value="3,210건",
                    delta="+5.0%",
                    delta_direction="up",
                ),
                KPIComponent(
                    id="c5",
                    label="오류율",
                    value="0.04%",
                    delta="±0.00%",
                    delta_direction="flat",
                ),
                ParagraphComponent(
                    id="c6",
                    text="전반적으로 안정적 성장 추세이며 응답 시간 개선이 두드러진다.",
                    emphasis="bold",
                ),
            ],
            speaker_notes=None,
            page_number_visible=True,
        ),
    )


# ---------------------------------------------------------------------------
# 샘플 C — 테이블 중심
# ---------------------------------------------------------------------------


def build_sample_c() -> DocumentSchema:
    """SlideTitle + DataTable + Paragraph 의 표 중심 조합.

    목적:
        - 헤더 남색(#34495E) + 제브라 스트라이프 + 숫자 우측정렬이 제대로
          적용되는지 확인.
        - 5 행 x 4 열 — max_display_rows 이내.
    """
    return _doc_wrapper(
        page=Page(
            id="p1",
            page_kind="slide",
            layout="content_body",
            title="테이블 중심 샘플",
            locked=False,
            components=[
                SlideTitleComponent(id="c1", text="사업부별 매출 실적"),
                DataTableComponent(
                    id="c2",
                    headers=["사업부", "1분기 매출", "전년 동기", "증감률"],
                    rows=[
                        ["플랫폼", "1,240", "1,080", "+14.8%"],
                        ["컨설팅", "980", "920", "+6.5%"],
                        ["교육", "320", "340", "-5.9%"],
                        ["연구개발", "560", "410", "+36.6%"],
                        ["합계", "3,100", "2,750", "+12.7%"],
                    ],
                    emphasis_column_index=3,
                    caption="단위: 백만원. 합계 행은 자체 감사 기준.",
                ),
                ParagraphComponent(
                    id="c3",
                    text="플랫폼과 연구개발 부문 성장이 전체 매출 증가를 견인했다.",
                    emphasis="normal",
                ),
            ],
            speaker_notes=None,
            page_number_visible=True,
        ),
    )


# ---------------------------------------------------------------------------
# 샘플 D — 차트 2종
# ---------------------------------------------------------------------------


def build_sample_d() -> DocumentSchema:
    """SlideTitle + Chart(bar) + Chart(line) + Heading 의 차트 중심 조합.

    목적:
        - bar / line 네이티브 차트 모두 IDINO 팔레트로 시리즈 색이 순환 적용
          되는지 확인.
        - 한 슬라이드에 차트 2 개 + Heading 이 수직 스택될 때 max_height
          계산이 깨지지 않는지 확인.
    """
    bar_chart = ChartComponent(
        id="c2",
        chart_type="bar",
        title="월별 신규 가입자",
        data=ChartData(
            labels=["1월", "2월", "3월"],
            series=[
                ChartSeries(name="개인", values=[420.0, 510.0, 640.0]),
                ChartSeries(name="기업", values=[110.0, 165.0, 210.0]),
            ],
        ),
    )
    line_chart = ChartComponent(
        id="c3",
        chart_type="line",
        title="주간 평균 응답 시간(ms)",
        data=ChartData(
            labels=["W1", "W2", "W3", "W4", "W5", "W6"],
            series=[
                ChartSeries(name="API", values=[160.0, 155.0, 148.0, 145.0, 143.0, 142.0]),
            ],
        ),
    )
    return _doc_wrapper(
        page=Page(
            id="p1",
            page_kind="slide",
            layout="content_body",
            title="차트 2종 샘플",
            locked=False,
            components=[
                SlideTitleComponent(id="c1", text="성과 지표 그래프"),
                bar_chart,
                line_chart,
                HeadingComponent(id="c4", text="결론", level=2),
            ],
            speaker_notes=None,
            page_number_visible=True,
        ),
    )


# ---------------------------------------------------------------------------
# 샘플 E — 미디어 포함
# ---------------------------------------------------------------------------


def build_sample_e() -> DocumentSchema:
    """SlideTitle + Image + Paragraph + BulletList 의 미디어 혼합 조합.

    ImageComponent.src 를 None 으로 둬서 D6 빌더의 placeholder degrade 경로
    (회색 박스 + [이미지 없음] 문구) 를 의도적으로 유도한다. 실제 네트워크
    fetch 를 요구하지 않으므로 오프라인 재현성이 좋다.
    """
    return _doc_wrapper(
        page=Page(
            id="p1",
            page_kind="slide",
            layout="content_body",
            title="미디어 포함 샘플",
            locked=False,
            components=[
                SlideTitleComponent(id="c1", text="사용자 여정 지도"),
                ImageComponent(
                    id="c2",
                    src=None,
                    prompt="사용자가 문서를 업로드하고 챗봇에게 질문하는 장면",
                    alt="사용자 여정 개념도 (placeholder)",
                    caption="출처: 내부 워크숍 결과",
                ),
                ParagraphComponent(
                    id="c3",
                    text="사용자는 업로드 → 질문 → 보고서 생성 3 단계를 거쳐 업무를 완료한다.",
                    emphasis="normal",
                ),
                BulletListComponent(
                    id="c4",
                    items=[
                        BulletItem(text="업로드 단계 평균 4 초 소요"),
                        BulletItem(text="질문 단계 평균 2 회 왕복"),
                        BulletItem(text="보고서 생성까지 약 38 초"),
                    ],
                    numbered=True,
                ),
            ],
            speaker_notes=None,
            page_number_visible=True,
        ),
    )


# ---------------------------------------------------------------------------
# 엔트리 포인트
# ---------------------------------------------------------------------------


def _count_components_by_type(schema: DocumentSchema) -> dict[str, int]:
    """DocumentSchema 의 페이지들을 순회하며 컴포넌트 타입별 개수를 집계.

    리뷰 문서에 "스키마가 어떤 컴포넌트를 몇 개 보냈는지" 를 그대로 보여주기
    위한 용도. 실제 빌드 후 shape 개수는 metrics 단계에서 별도 측정.
    """
    counts: dict[str, int] = {}
    for page in schema.pages:
        for comp in page.components:
            counts[comp.type] = counts.get(comp.type, 0) + 1
    return counts


async def _build_and_save(
    sample_id: str,
    builder: Any,
    schema: DocumentSchema,
    *,
    out_dir: Path,
) -> dict[str, Any]:
    """샘플 하나를 빌드해 파일로 저장하고 메타데이터 dict 를 반환한다.

    시간 측정은 build 호출 직전/직후를 감싸는 perf_counter 로 수행.
    """
    out_path = out_dir / f"{sample_id}.pptx"
    start = time.perf_counter()
    pptx_bytes = await builder.build(schema)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    out_path.write_bytes(pptx_bytes)
    print(f"[OK] {sample_id:20s} | {len(pptx_bytes):>8d} bytes | {elapsed_ms:>7.1f} ms")
    return {
        "sample_id": sample_id,
        "file_name": out_path.name,
        "file_size_bytes": len(pptx_bytes),
        "build_time_ms": round(elapsed_ms, 2),
        "page_count": len(schema.pages),
        "component_counts": _count_components_by_type(schema),
        "layouts": [page.layout for page in schema.pages],
    }


async def run() -> int:
    """전체 실행 — 5 샘플 빌드 후 metadata.json 저장."""
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    # P1 준수 — Registry 경유로 빌더 획득. PptxBuilder 인스턴스를 직접 만들지 않음.
    #   __init__.py 가 import 시점에 register_pptx_builder() 를 호출하긴 하지만,
    #   본 스크립트가 독립 실행될 때도 확실히 등록되도록 명시적으로 한 번 더 호출.
    register_pptx_builder()
    builder = BuilderRegistry.get("pptx")
    print(f"[INFO] 획득한 빌더: {type(builder).__name__} (target={builder.target})")

    samples = [
        (SAMPLE_A_ID, build_sample_a()),
        (SAMPLE_B_ID, build_sample_b()),
        (SAMPLE_C_ID, build_sample_c()),
        (SAMPLE_D_ID, build_sample_d()),
        (SAMPLE_E_ID, build_sample_e()),
    ]

    results: list[dict[str, Any]] = []
    for sample_id, schema in samples:
        entry = await _build_and_save(sample_id, builder, schema, out_dir=SAMPLES_DIR)
        results.append(entry)

    metadata_path = SAMPLES_DIR / "metadata.json"
    metadata_payload: dict[str, Any] = {
        "generated_by": GENERATED_BY_TAG,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "builder": {
            "target": builder.target,
            "class": type(builder).__name__,
            "supported_components": sorted(builder.supported_components),
        },
        "samples": results,
    }
    metadata_path.write_text(
        json.dumps(metadata_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[DONE] metadata.json 저장 → {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
