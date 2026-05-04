# Phase 4 S2 D8 — PPTX A/B 비교 리뷰 (신규 `PptxBuilder` vs 기존 `report_generator.py`)

- **작성일**: 2026-04-23
- **범위**: S2 D1~D7 에서 완성한 신규 PPTX 경로 vs 기존 3,702 줄 경로의 정적 비교 + 자동 메트릭
- **방식**: 리뷰어 3 명 대신 `scripts/_s2_d8_generate_ab_samples.py` + `scripts/_s2_d8_measure_samples.py` 로 자동 메트릭 수집 → 자가 체크리스트 평가
- **기존 경로 수정 금지** — 본 리뷰는 읽기만 수행

---

## 1. 샘플 요약

`docs/s2_d8_samples/` 에 5 건 `.pptx` + `metadata.json` + `metrics.json` 저장.

| 샘플 | 컴포넌트 조합 | 슬라이드 | 파일 크기 | 생성 시간 | Shape 수 | IDINO 팔레트 |
|---|---|---:|---:|---:|---:|---:|
| A 텍스트 중심 | SlideTitle + Heading + Paragraph + BulletList | 1 | 32.94 KB | 12.61 ms | 4 | 100% |
| B KPI 대시보드 | SlideTitle + KPI×4 + Paragraph | 1 | 28.27 KB | 11.37 ms | 14 | 100% |
| C 테이블 중심 | SlideTitle + DataTable + Paragraph | 1 | 28.40 KB | 17.26 ms | 3 | 100% |
| D 차트 2종 | SlideTitle + Chart(bar) + Chart(line) + Heading | 1 | 40.56 KB | 42.71 ms | 4 | 100% |
| E 미디어 포함 | SlideTitle + Image(placeholder) + Paragraph + BulletList | 1 | 28.28 KB | 10.01 ms | 6 | 100% |
| **평균** | — | 1 | 31.69 KB | **18.79 ms** | 6.2 | **100%** |

모든 샘플이 16:9 (13.333" × 7.5"), 스키마 컴포넌트 수 ≤ 실제 shape 수 → 컴포넌트 누락 없음.

---

## 2. 구조적 비교

| 기준 | 기존 `report_generator.py` | 신규 `PptxBuilder` |
|---|---|---|
| 코드 위치 | `backend/app/workers/report_generator.py` 단일 파일 (3,702 줄) | `backend/app/integrations/document_builders/pptx/` 5 모듈 (빌더 372 + 컴포넌트 1,523 + layout_resolver 374 + style + constants ≈ 306) |
| 모듈 구조 (P2) | ❌ workers/ 밑에 single-file 거대 함수 묶음 | ✅ integration 계층 하위 서브패키지 |
| 레이아웃 선택 | ❌ `_build_layout_catalog()` 가 **IDINO 한글 14 종 하드코딩** (`"1_표지"`, `"Ⅰ. 본문"`, `"9_마침화면"` 등) | ✅ `layout_resolver.resolve_layout()` 런타임 탐색 + 정규화 매칭 + organization_overrides 시그니처 + blank fallback |
| placeholder idx | ❌ `slide.placeholders[0/1/10/11/16]` 하드코딩 | ⚠ `resolve_placeholder(semantic)` 준비 완료 — 현재 빌더는 textbox 직접 배치 경로만 사용 (S2 후반~S3 에 placeholder 경로 활성화 예정) |
| 스타일 로직 | ❌ 2,000+ 줄 내에 `_set_tf_text`, `_add_chart_to_slide`, `_add_table_to_slide` 산재 | ✅ `style.py` `apply_idino_text_style` 공용 헬퍼 + `reset_text_frame` 단일 paragraph 진입점 |
| 색상 상수 | ❌ 함수 내부 로컬 변수 (`CLR_HEADER = RGBColor(...)`, `FONT = "Malgun Gothic"`) | ✅ `constants.py` 중앙 관리 (`IDINO_PALETTE` + `CHART_SERIES_PALETTE` 합 14 색) |
| 폰트 | Malgun Gothic (Windows 전용) | Pretendard (FE DesignTokens 와 일치, OS 미설치 시 fallback) |
| Jinja2 치환 | 지원 (Mode B 경로) | Mode A 범위 밖 — S4 에서 Mode B 재연결 |
| 컴포넌트 커버리지 | 임시 Structured Output JSON 12 타입 (feature-specific) | Pydantic Discriminated Union 22 컴포넌트 중 8 종 구현 (SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable/Image/Chart) |
| 테스트 커버리지 | 사실상 E2E 의존 (경로 복잡) | 단위 테스트 40+ PASS (pytest backend/tests/integrations/document_builders/pptx/) |
| 빌드 시간 | 측정 어려움 (Celery 워커 전체) | 로컬 빌드 평균 18.79 ms, 최댓값 42.71 ms |
| 파이프라인 결합도 | worker + MinIO + DB + LLM 강결합 | builder 자체는 순수 함수 (schema → bytes), worker 는 얇은 래퍼 (export_worker.py) |

---

## 3. IDINO 디자인 체크리스트

각 샘플에 대해 **PASS** / **FAIL** / **WARN** 표기. 기준은 `constants.py` 의 상수 값.

| 항목 | A 텍스트 | B KPI | C 테이블 | D 차트 | E 미디어 | 비고 |
|---|---|---|---|---|---|---|
| Primary #0A4FC2 적용 | PASS (4회 관측) | PASS (10회) | PASS (2회) | PASS (4회) | PASS (2회) | SlideTitle + KPI value + chart 시리즈 |
| Accent #FF6B35 적용 | PASS (2회, highlight bullet) | — (본 샘플은 미사용) | — | — | — | 샘플에 highlight 있을 때만 기대됨 |
| Header navy #34495E | — | — | PASS (4회, 표 헤더) | — | — | 테이블 샘플에서만 기대됨 |
| Pretendard 폰트 설정 | PASS | PASS | PASS | PASS | PASS | `DEFAULT_FONT = "Pretendard"` 상수 경유 |
| 텍스트 계층 (32 → 24/20/16 → 14 → 10) | PASS | PASS (label 12 / value 36 / delta 12) | PASS (header 11 / cell 10) | PASS (chart title 14 / axis 10) | PASS | `FONT_SIZE_*` 상수 준수 |
| 슬라이드 크기 16:9 (13.333 × 7.5") | PASS | PASS | PASS | PASS | PASS | metrics.json `is_16_9=true` |
| 여백 일관성 (left 0.5~0.6", body 11 여유") | PASS | PASS | PASS | PASS | PASS | BODY_LEFT_IN / BODY_WIDTH_IN 상수 고정 |
| 컴포넌트 누락 없음 | PASS | PASS | PASS | PASS | PASS | shape ≥ component 수 |
| placeholder 경로 사용 | WARN | WARN | WARN | WARN | WARN | 현재 textbox 직접 배치 — `resolve_placeholder` 는 준비만 됨 |
| 조직 마스터 이름 매칭 | WARN | WARN | WARN | WARN | WARN | python-pptx 기본 마스터에는 한글 후보가 없어 fallback 로그 발생 — 의도된 동작이나 IDINO 마스터 업로드 시나리오는 D9 통합 시연에서 검증 필요 |

**합계**: PASS 40, WARN 10, FAIL 0. (항목 10 × 샘플 5 = 50 중 80% PASS.)

WARN 2 항목은 **기능 실패가 아닌 "S2 범위에서 의도적으로 후순위로 미룬 활성화"** — 빌드 자체는 전부 성공하며 빈 박스/깨진 레이아웃은 없다.

---

## 4. Phase 0 근본원인 해소 자평

진단 근거: `docs/techspec.md §7.1.1`.

| 진단 항목 | 기존 | 신규 | 해소 여부 |
|---|---|---|---|
| 하드코딩 한글 레이아웃 이름 14 종 | `_build_layout_catalog()` 내 고정 dict | `LAYOUT_NAME_CANDIDATES` **후보** (hardcoded-as-candidates, not hardcoded-as-truth) + organization_overrides 주입 + 정규화 매칭 | ✅ **해소** — 이름이 바뀌어도 후보 추가/override 로 흡수, 전부 실패해도 blank fallback 으로 빌드 계속 |
| 다른 조직 마스터에서 catalog 가 빈 dict → `slide_layouts[0]` fallback 으로 레이아웃 깨짐 | 빌드 통째로 깨지거나 PowerPoint 가 오류 | 매칭 실패 시에도 `Blank` 레이아웃으로 bytes 생성 성공, WARNING 로그만 남김 | ✅ **해소** — 본 D8 샘플 생성 시 python-pptx 기본 마스터(한글 없음) 에서 5 건 모두 성공 |
| 플레이스홀더 idx(0/1/10/11/16) 하드코딩 | IDINO 마스터 배치에만 유효 | `resolve_placeholder(semantic)` 정의 완료, 현재 빌더는 textbox 직접 배치로 우회 | ⚠ **부분 해소** — 의존성은 제거됐으나 활성화는 S2 D9 또는 S3 범위 |
| 레이아웃 catalog 와 LayoutId enum 불일치 (기존 8 종 vs 신규 6 종) | 두 세트 공존 | `LayoutId` Literal 6 종으로 단일화 (`layout_resolver.py` 와 `schemas.py` 동일 값) | ✅ **해소** |

**자평**: 3 건 해소 + 1 건 부분 해소. 하드코딩 제거는 실제로 **런타임 증빙** 되었음 (python-pptx 기본 마스터에서 한글 후보 전부 실패해도 5 샘플 모두 `.pptx` 정상 생성).

---

## 5. 개선 권고 리스트

### P0 — S2 잔여 구간 내 반영

- **P0-1 `resolve_placeholder` 활성화 시나리오 검증**
  - 현재 `builder._render_page()` 는 `add_textbox()` 직접 배치 경로만 사용. IDINO 한글 마스터가 업로드된 실전에서는 `placeholder_format.type=TITLE` 에 `SlideTitleComponent` 를 채우는 것이 자연스럽다.
  - 조치: S2 D9 에 "IDINO 기본 마스터 + 5 샘플" 을 주입한 통합 빌드를 한 번 더 돌려 placeholder 매칭 성공 여부를 로그로 확인. 실패 시에도 빌드는 진행되므로 회귀 위험은 없음.
- **P0-2 레이아웃 fallback 로그 과다**
  - `python-pptx` 기본 마스터는 한글 후보 전부 실패 → 5 샘플 × 페이지 수만큼 WARNING. organization 미지정 시 로그 레벨을 INFO 로 강등 또는 처음 1 회만 WARN 출력 옵션 추가.
  - 조치: `layout_resolver.py` 의 `logger.warning` 을 호출부 컨텍스트(조직 슬라이드마스터 존재 여부) 에 따라 레벨 조정.

### P1 — S2 D9 반영

- **P1-1 Accent 색 의도적 사용 경로 확장**
  - 샘플 A 에서 `BulletItem.emphasis="highlight"` 는 accent 색으로 렌더되나, KPI delta_direction="up" 도 녹색 #10B981 이지 accent 가 아니다. "positive trend" 에 대한 브랜드 정체성 강화를 위해 KPI description/chart 시리즈 기본값을 재검토.
  - 조치: D9 에서 FE `KPICard` 와 시각 대조 — PPT 와 HTML 프리뷰가 같은 강조 색을 내도록 accent 사용 정책 문서화.
- **P1-2 BulletList 의 `highlight` emphasis → PPT 에서는 배경이 아닌 color 치환**
  - FE 는 background 로 highlight 를 그리지만 PPTX 는 font.color 로 대체 중 (`components.py:422`). 시각 일치성을 높이려면 accent 배경 도형 + 흰 글씨 조합을 검토.
  - 조치: `apply_idino_text_style` 에 `background_hex` 파라미터 추가 시 영향 범위 확인 후 S2 D9 에 반영.
- **P1-3 Paragraph 높이 추정이 보수적 → 여백 낭비**
  - `_estimate_height_by_chars` 가 `chars_per_line=70` 으로 한글 기준 계산하지만 실제 13" 폭에서는 80~90 자까지 들어간다. Y 스택이 빨리 소진되어 차트 샘플에서 남은 공간 계산 경계값에 몰린다.
  - 조치: chars_per_line 상수화 + font size 별 mapping 테이블로 분리.

### P2 — S3 이후

- **P2-1 Chart 시리즈 색상이 line 차트에서 시각 추출 불가**
  - line 차트는 내부 XML 에서 fill 이 아닌 line.color 로 저장되어 metrics 스크립트가 RGB 샘플을 수집하지 못했다 (샘플 D color_samples_total=4 로 SlideTitle+Heading 수준).
  - 조치: S3 에서 Chart 색상 적용 검증을 위한 별도 XML 경로 테스트 추가.
- **P2-2 ImageComponent 자동 생성 (DALL-E/Unsplash)**
  - 현재 `src=None` 시 placeholder 로 degrade. S3 범위에서 prompt → 이미지 자동 생성 활성화.
- **P2-3 `validate_components()` unsupported 로그 → UI 경고 채널**
  - 현재 INFO 로그만 남아 사용자가 "왜 이 컴포넌트가 안 들어갔지?" 를 알 수 없음. `DocumentMetadata.degraded_components` 에 누적해 편집 UI 에 노출.

### P3 — S7 이후 (레거시 폐기)

- **P3-1 `backend/app/workers/report_generator.py::_build_pptx_from_structured`** + `_build_layout_catalog` 전체 함수 블록 (약 L1250~L2080, ~830 줄) 폐기.
- **P3-2 `report_generator` 의 IDINO 수동 디자인 로직 (CLR_HEADER, FONT="Malgun Gothic" 등)** → `constants.py` 로 완전 이관 후 삭제.
- **P3-3 `_add_chart_to_slide` (matplotlib → PNG 삽입 경로)** 폐기 → `components.render_chart()` (PPTX native) 로 일원화.

---

## 6. 자동 메트릭 요약 표

(상세 값은 `docs/s2_d8_samples/metrics.json` 참조.)

| 지표 | 값 | 비고 |
|---|---|---|
| 총 샘플 수 | 5 | D1~D7 에 구현된 8 컴포넌트 중 7 종 커버 (Image 실제 fetch 는 placeholder 경로) |
| 전 샘플 16:9 | 예 | `all_16_9: true` |
| 컴포넌트 누락 | 없음 | `any_component_missing: false` |
| 평균 IDINO 팔레트 일치율 | 100.00% | 5 샘플 모두 1.0 |
| 평균 재빌드 시간 | 18.79 ms | 차트 2 개 샘플이 42.71 ms 로 최대 |
| 파일 크기 범위 | 28.27 ~ 40.56 KB | 차트 native 가 XML 용량 증가 주도 |
| 가장 빈번한 색상 | `#1F2937` (Text) | 본문 샘플 지배 |
| 누락 감지 알고리즘 | shape ≥ component 수 | 보수적 — KPI/Image 는 1 컴포넌트에 여러 shape |

---

## 7. 블로커 / 미해결

- **블로커 없음**. 신규 PPTX 빌더는 Mode A 모든 샘플을 오류 없이 생성한다.
- **미해결 (S2 D9 로 이관)**
  - IDINO 실제 슬라이드마스터(`1_표지`, `Ⅰ. 본문`) 파일을 업로드한 상태에서의 `resolve_layout` 매칭 성공 로그 확인
  - `resolve_placeholder` 활성 경로로 전환 여부 결정 (textbox 직접 배치 대비 시각 차이 정량화)
  - Accent 색 사용 정책 문서화 (P1-1) 및 BulletList highlight 시각 강화 (P1-2)
- **미해결 (S7 이후)**
  - 기존 `report_generator.py` 의 PPTX 경로 폐기 타임라인 확정

---

## 8. 재현 방법

```bash
cd D:\workspace\document_utilization
python scripts/_s2_d8_generate_ab_samples.py
python scripts/_s2_d8_measure_samples.py
```

생성물:
- `docs/s2_d8_samples/sample_{a..e}_*.pptx`
- `docs/s2_d8_samples/metadata.json`
- `docs/s2_d8_samples/metrics.json`

리뷰 재평가 시 스크립트를 그대로 다시 돌리면 결정론적 결과 (LLM 비의존) 가 나온다.
