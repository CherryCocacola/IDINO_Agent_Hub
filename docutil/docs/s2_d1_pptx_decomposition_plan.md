# S2 D1 — `_build_pptx_from_structured` 분해 계획

Phase 4 S2 D1 산출물. 기존 `backend/app/workers/report_generator.py` 의 약 3,700 줄 중 **PPTX 생성 경로(L1316~L2085, 약 770 줄)** 를 신규 `app/integrations/document_builders/pptx/` 서브패키지로 이관하기 위한 분해 매핑 문서. 실제 이관은 D2~D3 에서 수행하며 본 문서는 이관 대상과 우선순위를 확정하는 것만을 목표로 한다.

## 1. 기존 함수 라인 범위

| 함수 | 라인 | 역할 | 이관 대상 |
|---|---|---|---|
| `_build_layout_catalog(prs)` | 1316~1410 | IDINO 한글 레이아웃 이름 → layout_type 하드코딩 매핑 | **폐기** — D3 `layout_resolver.py` 가 런타임 탐색으로 대체 |
| `_build_pptx_from_structured(data, slide_master_data, params)` | 1418~2085 | Structured Output JSON → PPTX bytes 본체 (슬라이드마스터 경로 + IDINO 기본 경로) | `PptxBuilder.build()` 로 통합 |

`_build_pptx_from_structured` 는 두 개의 큰 분기(if `slide_master_data` else)로 나뉜다.

- **분기 A (L1449~L1551, 103 줄)**: 슬라이드마스터 기반 생성 — `_build_layout_catalog` + placeholder 주입 + 표/차트/이미지 삽입 + 원본 슬라이드 제거.
- **분기 B (L1553~L2084, 531 줄)**: IDINO 디자인 수동 생성 — 내부 로컬 헬퍼(`_set_shape_fill`, `_set_tf_text`, `_add_idino_header_bar` 등)와 레이아웃 생성기(`_add_idino_title_slide`, `_add_idino_content_slide`, …) 6 종으로 구성.

## 2. 내부 논리 블록 식별

분기 A 를 5 단계로 쪼갠다.

1. 슬라이드마스터 로드 (tempfile 경유 Presentation 생성)
2. 레이아웃 카탈로그 빌드 (`_build_layout_catalog`)
3. 슬라이드 루프 — layout 매칭 + placeholder 주입
4. 컴포넌트 삽입 (표/차트/이미지/노트)
5. 원본 슬라이드 제거 + BytesIO save

분기 B 는 6 개 IDINO 레이아웃 생성기 + 2 개 공통 바(헤더·푸터) + 5 개 텍스트/도형 유틸.

## 3. 이관 매핑 테이블 (기존 → 신규)

| 기존 로직 (report_generator.py) | 신규 위치 | 스프린트 |
|---|---|---|
| 분기 A ① 슬라이드마스터 로드 | `PptxBuilder.build()` 초반 | D3 |
| 분기 A ② 레이아웃 카탈로그 | `pptx/layout_resolver.py::resolve_layout()` | **D3** |
| 분기 A ③ 슬라이드 루프 · placeholder 주입 | `PptxBuilder._render_page()` | D2 |
| 분기 A ④-1 표 삽입 `_add_table_to_slide` | `PptxBuilder._render_data_table()` | **D3** |
| 분기 A ④-2 차트 삽입 `_add_chart_to_slide` | S2 D7 Chart 빌더 | S2 D7 |
| 분기 A ④-3 이미지 삽입 `_add_image_to_slide` | S2 D6 Image 빌더 | S2 D6 |
| 분기 B IDINO 수동 디자인 (531 줄) | `pptx/styles.py` (Utils) + `layout_resolver.py` fallback 경로 | D3 |
| 헬퍼 `_set_shape_fill` / `_set_tf_text` | `pptx/styles.py::apply_idino_text_style()` 등 | D2 |
| 헬퍼 `_add_idino_header_bar` / `_footer_bar` | `pptx/styles.py::insert_idino_frame()` | D3 |

## 4. 컴포넌트 이관 우선순위

- **D2 (4종)**: `SlideTitle`, `Heading`, `Paragraph`, `BulletList` — 텍스트 중심, 기존 placeholder 주입 로직 재활용.
- **D3 (2종)**: `KPI`, `DataTable` — 셀 스타일·강조 색상 필요. DataTable 은 `_add_table_to_slide` 이관으로 커버.

이관이 끝난 순간부터 해당 컴포넌트는 `PptxBuilder.supported_components` 에서 "의도 선언"과 "실구현" 이 일치한다.

## 5. 재사용 가능 헬퍼 후보

- `_apply_idino_text_style(tf, text, size, color, bold, align)` — 기존 `_set_tf_text` 를 그대로 옮겨 공용 스타일러로.
- `_insert_table_with_header(slide, headers, rows)` — 기존 `_add_table_to_slide` 를 header emphasis 옵션 추가해 승격.
- `_resolve_layout(prs, layout_id)` — 하드코딩 한글 이름 대신 `page.layout`(Literal 6종) → 실제 layout 객체 탐색. 마스터에 해당 이름이 없으면 `blank_layout` fallback.

모두 `pptx/styles.py` 와 `pptx/layout_resolver.py` 에 각각 배치, 한글 주석 필수.

## 6. 하드코딩 제거 전략 (D3 `layout_resolver`)

기존 `_build_layout_catalog` 의 문제:

1. **하드코딩된 한글 레이아웃 이름** ("1_표지", "Ⅰ. 본문", "맺음말" 등 14 종) — 마스터 파일이 바뀌면 즉시 깨짐.
2. **가로·세로 분기 이원화** — landscape 여부만으로 두 벌의 매핑 테이블을 가짐.
3. **layout_type enum 과 DocumentSchema.LayoutId 불일치** — 기존은 "body_text/body_with_table/body_with_chart/…" 8종, 신규 LayoutId 는 6종("title_slide/section_divider/content_body/kpi_dashboard/two_column/closing").

D3 해결책:

- `LAYOUT_ID_TO_NAME_CANDIDATES: dict[LayoutId, tuple[str, ...]]` 상수로 후보 이름 리스트를 유지. 마스터 변경 시 상수만 갱신.
- 런타임에 마스터를 순회하며 첫 매칭 이름을 반환, 전부 실패 시 "content_body" fallback.
- 환경변수·설정으로 커스텀 매핑 주입 여지를 남김(조직별 커스텀 마스터).

## 7. 리스크 및 블로커

- 기존 `workers/report_generator.py` 는 `/reports` 레거시 경로에서 아직 사용 중 — D5 export worker 가 신규 경로를 덮기 전까지 **수정 금지**. 본 문서는 이관 전 매핑 확정만 담당.
- IDINO 마스터 파일 경로·바이트 전달 방식(`slide_master_data: bytes`) 은 S2 D3 까지 그대로 계승, S2 D4 에서 `settings` 기반으로 일원화 검토.

— 문서 길이: 약 470 단어.
