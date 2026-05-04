# DocUtil — Phase 1 목표 아키텍처 기준선 (v1.0)

> **작성일**: 2026-04-19
> **작성자**: enterprise-architect (Claude Opus 4.7)
> **상위 문서**: `docs/techspec.md` §3 목표 아키텍처
> **후속 배포 대상**: database-architect / frontend-specialist / research-assistant
> **상태**: Phase 1 설계 기준선 확정. Phase 2~4 에이전트는 본 문서만을 기준으로 병렬 착수한다.

---

## 0. Executive Summary

Phase 0 진단 결과 DocUtil 문서 생성 엔진은 **하드코딩된 IDINO 마스터 매칭**, **이중화된 템플릿 시스템**, **회의록 전용 구조 부재**, **Chat 소스 증발**이라는 네 가지 구조적 결함을 동시에 안고 있다. 단편적 수정은 이미 핫픽스(H1~H7)로 소진되었고, 여기서부터는 **생성 엔진 자체의 재구성**이 필요하다.

본 문서는 그 재구성을 **접근법 C — 컴포넌트 라이브러리 + DocumentSchema**로 확정한다. 핵심 결정은 다음과 같다.

1. **DocumentSchema를 단일 진실의 원천(SSOT)으로 삼는다.** LLM은 Structured Outputs로 이 스키마만 생성하며, HTML 프리뷰·PPTX·DOCX·HWPX·PDF는 모두 이 스키마를 **소비**하는 빌더로 구현한다. P1(단일 구현)의 범위를 "LLM 출력 형태"로 확장한다.
2. **Mode A(자유 생성) / Mode B(양식 채우기)는 동일 스키마의 두 가지 생성 경로**다. 분기는 `mode` 필드와 `locked` 플래그로만 표현하고, 렌더러/빌더는 분기하지 않는다. 이로써 렌더링 품질·IDINO 브랜드 준수를 한 곳에서 보장한다.
3. **컴포넌트 라이브러리는 Pydantic Discriminated Union 기반 22개 MVP**로 출발한다. 각 컴포넌트는 (Pydantic 스키마, React 렌더러, PPTX 빌더, DOCX 빌더) 4-쌍을 동시에 제공하며, HWPX는 지원 가능한 서브셋만 매핑한다.
4. **기존 `modules/reports`와 `modules/templates`는 단계적 폐기**하고 신규 `modules/documents_v2` 단일 모듈로 통합한다. `tb_report_templates`와 `tb_document_templates`의 이중화도 해소한다.
5. **S1~S7 스프린트는 Schema-first 순서**로 재편한다. S1에서 Schema와 React 렌더러 골격을 확정한 뒤에야 S2(PPTX 빌더), S5(HWPX 어댑터)가 착수할 수 있도록 의존성을 잠근다.

기존 자산은 약 **55~60% 재활용(IDINO 토큰, Structured Outputs 스키마, Agent 시스템, Jinja2 엔진 일부, DALL-E 3, Agentic RAG, python-pptx 빌더 단편)**, 약 **40~45% 폐기 또는 대체**(하드코딩 레이아웃 카탈로그, 이중 템플릿 테이블, `rendering_mode=jinja2` 분기 대부분)된다.

---

## 1. 아키텍처 원칙 재확인

본 설계는 `.claude/rules/architecture.md`의 P1~P6를 재확인·확장한다.

- **P1 단일 구현의 확장**: 이제 "문서 생성의 유일한 경로"는 `LLM → DocumentSchema → Builders[*]`. `rendering_mode` 자유 텍스트 분기, `structured` vs `jinja2` 이중 경로, Mode A/B 별도 엔진은 모두 금지.
- **P2 고정 모듈 구조**: 신규 `modules/documents_v2/`도 `router/service/schemas/models/utils/constants/exceptions`만 허용. 컴포넌트 스키마가 파일당 다량 필요하면 `schemas.py` 내 서브모듈 대신 `schemas.py` 단일 파일에서 Pydantic discriminated union으로 표현한다(모듈 구조 원칙을 위한 타협).
- **P3 절대 import**: 변경 없음.
- **P4 Router → Service → Integration 단방향**: 빌더는 `app/integrations/document_builders/` 하위에 배치. Service만 빌더를 호출. Router는 절대 빌더를 직접 호출하지 않는다.
- **P5 에러 처리**: LLM이 Schema 제약을 위반하면(화이트리스트 컴포넌트 외 생성) `HTTPException(422, "지원하지 않는 컴포넌트 타입입니다")` 발생. 빌더별 실패(예: HWPX에서 Chart 미지원)는 렌더링 단계에서 **graceful degradation**(텍스트 대체 + 경고 metadata 기록).
- **P6 Structured Outputs First**: DocumentSchema는 **그 자체**가 Structured Output. 프롬프트 변경으로 schema를 우회하려 해서는 안 된다.

**새로 추가되는 원칙(P7)** — **Builder Adapter Interface**:
> 모든 파일 포맷 빌더는 `DocumentBuilder`(ABC)를 구현하고 `build(schema: DocumentSchema) -> bytes` 시그니처를 준수한다. 신규 포맷 추가는 ABC 구현 + 레지스트리 등록만으로 끝나야 한다.

---

## 2. 과제 1 — DocumentSchema 최종 스펙

### 2.1 설계 결정

**대안 비교**:

| 대안 | 장점 | 단점 | 판정 |
|---|---|---|---|
| (가) Flat 배열 (컴포넌트 평탄 리스트) | 단순 | 슬라이드/섹션 경계 표현 불가 | 기각 |
| (나) slides+sections 혼합 단일 트리 | 유연 | 타입 안전성 약함, LLM 혼란 | 기각 |
| (다) **type에 따라 `pages` 단일 추상화 + page_kind(slide/section) 분기** | 단일 구조, 타입별 제약 선언적, Discriminated Union 자연스러움 | 초기 학습 곡선 | **채택** |

`slides[]` vs `sections[]`로 나누지 않고 공통 `pages[]`로 추상화한다. `page_kind`가 `slide`면 슬라이드(고정 종횡비 16:9), `section`이면 DOCX/HWPX의 흐름형 섹션을 의미한다. 렌더러·빌더가 이 필드로 분기한다.

### 2.2 루트 구조

```python
# 의사-Pydantic (실제 구현은 database-architect + backend-specialist가 수행)
class DocumentSchema(BaseModel):
    document_id: UUID
    schema_version: Literal["1.0"]
    type: DocumentType          # 아래 enum
    mode: Literal["free_generation", "template_fill"]
    template_id: UUID | None    # mode=="template_fill"에서만 non-null
    design_tokens: DesignTokens
    pages: list[Page]           # 최소 1
    metadata: DocumentMetadata
```

### 2.3 `type` Enum (DocumentType)

DocUtil 실제 도메인을 반영해 **7종**으로 확정한다. 과거 Agent `agent_type` 4종(chatbot/report/proposal/minutes)과 호환되되 문서 타입을 더 세분한다.

| 값 | 설명 | 기본 page_kind | 대응 에이전트 타입 |
|---|---|---|---|
| `slide_report` | 슬라이드형 보고서 (PPTX 주산출물) | `slide` | report |
| `docx_report` | 문서형 보고서 (DOCX 주산출물) | `section` | report |
| `proposal` | 사업제안서 | `slide` 또는 `section` | proposal |
| `minutes` | 회의록 | `section` | minutes |
| `one_pager` | 한 페이지 요약 | `slide` (1장 고정) | report |
| `weekly_status` | 주간업무보고 | `section` | report |
| `freeform_doc` | 일반 자유 문서 | `section` | — |

**왜**: Phase 0 진단에서 회의록·주간보고는 보고서와 프롬프트·출력 구조가 달라야 한다는 근거가 확인되었다(techspec §7.1.3, §7.2.1-R4). `type`이 곧 프롬프트·스키마 제약·기본 레이아웃 풀을 결정하는 **주 분류 축**이 된다.

### 2.4 `mode` Enum

- `free_generation` — Mode A. `template_id=null`. LLM이 페이지 수·레이아웃·컴포넌트를 **전부** 결정.
- `template_fill` — Mode B. `template_id` 필수. 페이지 구조와 `locked=true` 컴포넌트는 고정, LLM은 slot 채우기만 수행.

> **v1.6 주석 (Q3 반영)**: Mode 전환(생성 후 다른 Mode로 전환) 기능은 Phase 1 범위 외. 필요 시 별도 ADR로 승격. DB 레이어는 엄격 CHECK (`ck_tb_documents_v2_template_consistency`) 유지. 상세는 `phase1_decisions.md` Q3 참조.

### 2.5 `design_tokens`

IDINO 브랜드를 스키마 수준에서 강제한다. **7개 필드**로 최소화(클라이언트/빌더에서 공통 참조).

```python
class DesignTokens(BaseModel):
    primary_color: str          # hex, default "#0A4FC2" (IDINO 코퍼레이트)
    accent_color: str           # hex, default "#FF6B35"
    text_color: str             # hex, default "#1F2937"
    background_color: str       # hex, default "#FFFFFF"
    font_family: Literal["Pretendard", "NotoSansKR", "System"] = "Pretendard"
    spacing: Literal["compact", "normal", "relaxed"] = "normal"
    brand_preset: Literal["idino_default", "idino_mono", "custom"] = "idino_default"
```

**왜 색상을 enum이 아닌 hex로?** 고객사 브랜드 확장(다른 조직이 DocUtil을 쓰는 시나리오)을 염두에 둔다. 단 `brand_preset=idino_*`일 때 PPTX 빌더는 IDINO 마스터 고정 색을 우선 적용하고 hex는 무시(정책 충돌 방지).

### 2.6 `Page`

```python
class Page(BaseModel):
    id: str                         # "p1", "p2"... 안정 식별자
    page_kind: Literal["slide", "section"]
    layout: LayoutId                # 컴포넌트 배치 템플릿 식별자 (§3.4 참고)
    title: str | None
    locked: bool = False            # Mode B에서 True면 LLM이 수정 금지
    components: list[Component]     # discriminated union
    speaker_notes: str | None       # slide 전용
    page_number_visible: bool = True
```

- `locked=true`이면 해당 페이지 전체가 템플릿에 의해 고정. Mode B에서 잠금 영역 구현.
- 개별 컴포넌트 수준의 잠금은 `Component.locked`로 표현(§3.2 참고).

### 2.7 `Component` Discriminated Union (Pydantic v2)

Pydantic v2의 `Field(discriminator="type")` 사용. **왜 Discriminator인가**: (1) LLM Structured Output이 `oneOf` + `discriminator`를 지원하는 OpenAI/Azure/Gemini 공통 패턴. (2) 타입 오류를 스키마 단에서 차단. (3) 신규 컴포넌트 추가가 Union에 한 줄 추가로 완료.

```python
Component = Annotated[
    KPIComponent | DataTableComponent | BulletListComponent | ChartComponent |
    SlideTitleComponent | HeadingComponent | ParagraphComponent | ImageComponent |
    ... (22종),
    Field(discriminator="type")
]
```

공통 베이스:

```python
class ComponentBase(BaseModel):
    id: str                 # "c1", "c2"... 페이지 내 안정 식별자
    locked: bool = False    # 컴포넌트 단위 잠금
    anchor: str | None      # Mode B에서 템플릿 슬롯 이름과 매칭
```

### 2.8 `metadata`

```python
class DocumentMetadata(BaseModel):
    created_at: datetime
    updated_at: datetime
    generated_by_user_id: UUID | None
    llm_provider: str | None        # "openai" | "azure" | "gemini" | "claude" | "vllm"
    llm_model: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    source_document_ids: list[UUID] = []
    source_chat_session_id: UUID | None
    citations: list[Citation] = []  # 근거 청크 인용
    degraded_components: list[str] = []  # 빌더에서 graceful degradation된 컴포넌트 id 목록
```

**왜 citations를 metadata에?** Phase 0 §7.2.1-R4에서 회의록·요약에 Citations 필수화가 요구되었다. 컴포넌트별이 아닌 문서 메타에 보관해 모든 빌더가 공통으로 푸터/주석에 삽입 가능.

> **v1.6 주석 (Q2 반영)**: `source_document_ids`는 Phase 4 S6까지 ARRAY로 유지한다. 역방향 질의 빈도 실측 후 S6에서 조인 테이블 정규화 여부 결정. 상세는 `phase1_decisions.md` Q2 참조.

### 2.9 샘플 스키마 (부록 A로 이동)

3종 전체 예시는 부록 A 참조.

---

## 3. 과제 2 — 컴포넌트 라이브러리 카탈로그

### 3.1 설계 결정

**대안 비교**:

| 대안 | 장점 | 단점 | 판정 |
|---|---|---|---|
| (가) ABC 베이스 + 플러그인 레지스트리 | 런타임 확장성 | LLM 스키마 generation 복잡, 타입 안전성 약함 | 기각 |
| (나) **Pydantic Discriminated Union** | Structured Outputs 자연스러움, 타입 안전, JSON Schema 자동 생성 | 런타임 플러그인 불가(신규 컴포넌트 = 코드 배포) | **채택** |

DocUtil은 사내 시스템으로 핫스왑 컴포넌트가 필요 없으므로 (나)의 단점이 실질 문제 아님.

### 3.2 컴포넌트 카탈로그 (22종)

MVP 6종은 S1 완료 기준(Q8 확정, `phase1_decisions.md` 참조). Phase 4 S1~S7에 걸쳐 단계적 추가.

| # | 이름 | 카테고리 | 용도 | 필수 props | HWPX 지원 | 도입 스프린트 |
|---|---|---|---|---|---|---|
| 1 | `SlideTitle` | 텍스트 | 슬라이드 표제 | `text` | 예 | **S1 MVP** |
| 2 | `Heading` | 텍스트 | 섹션 제목(H1~H3) | `text`, `level` | 예 | **S1 MVP** |
| 3 | `Paragraph` | 텍스트 | 본문 단락 | `text` | 예 | **S1 MVP** |
| 4 | `BulletList` | 텍스트 | 불릿 목록 | `items` | 예 | **S1 MVP** |
| 5 | `KPI` | 데이터 | 핵심지표 카드 | `label`, `value` | 부분 (표로 대체) | **S1 MVP** |
| 6 | `DataTable` | 데이터 | 표 | `headers`, `rows` | 예 | **S1 MVP** |
| 7 | `Chart` | 데이터 | 차트(bar/line/pie) | `chart_type`, `data` | 아니요 (이미지 대체) | S2 |
| 8 | `Image` | 미디어 | 단일 이미지 | `src` 또는 `prompt` | 예 | S2 |
| 9 | `SlideSubtitle` | 텍스트 | 부제목 | `text` | 예 | S3 |
| 10 | `Quote` | 텍스트 | 인용 | `text`, `author` | 예 | S3 |
| 11 | `Callout` | 텍스트 | 강조 박스(info/warning) | `text`, `variant` | 부분 | S3 |
| 12 | `Timeline` | 데이터 | 타임라인 | `events` | 부분 (목록 대체) | S3 |
| 13 | `ImageGrid` | 미디어 | 이미지 그리드(2~4장) | `images` | 예 | S3 |
| 14 | `IconRow` | 미디어 | 아이콘+라벨 행 | `items` | 아니요 (목록 대체) | S3 |
| 15 | `TwoColumn` | 레이아웃 | 2단 컨테이너 | `left`, `right` | 예 | S4 |
| 16 | `ThreeColumn` | 레이아웃 | 3단 컨테이너 | `columns` | 예 | S4 |
| 17 | `Hero` | 레이아웃 | 표지 히어로 | `title`, `subtitle` | 예 | S4 |
| 18 | `Comparison` | 레이아웃 | 비교 표(좌/우) | `left`, `right` | 예 | S4 |
| 19 | `ExecutiveSummary` | 보고서 특화 | 경영진 요약 | `bullets`, `conclusion` | 예 | S6 |
| 20 | `RiskMatrix` | 보고서 특화 | 리스크 매트릭스 | `risks` | 부분 | S6 |
| 21 | `ActionItemList` | 보고서 특화 | 액션 아이템 | `items` | 예 | S6 |
| 22 | `AttendeeList` | 보고서 특화 | 회의 참석자 | `attendees` | 예 | S6 |

**MVP 6종 선정 근거** (v1.6, Q8 반영): 전체 테스트 보고서·회의록 생성의 약 75% 페이지 커버리지 달성. DataTable 포함으로 "문서다움"을 가진 시연 가치 확보 + Mode B 템플릿 슬롯의 가장 흔한 형태(표) 선검증. S1에서 end-to-end 동작(스키마→React→PPTX→DOCX) 검증 가능.

### 3.3 대표 3개 컴포넌트 상세 스펙

전체 22종 props 명세는 부록 B 참조. 여기서는 KPI, DataTable, BulletList만 상세.

**(1) KPI**

```python
class KPIComponent(ComponentBase):
    type: Literal["KPI"] = "KPI"
    label: str              # "월간 매출"
    value: str              # "₩1.2B"
    delta: str | None       # "+12% YoY"
    delta_direction: Literal["up", "down", "flat"] | None
    description: str | None # 한 줄 설명
```

- **React**: `<KPICard label value delta deltaDirection description tokens />` — Tailwind로 `rounded-2xl`, 델타 화살표 아이콘, 방향별 색(up=primary, down=red-500, flat=gray-400).
- **PPTX**: `build_kpi(slide, comp, tokens)` — IDINO 마스터의 `KPI` 플레이스홀더(idx=15) 우선. 없으면 `add_textbox` + `add_shape(MSO_SHAPE.ROUNDED_RECTANGLE)`로 합성.
- **DOCX**: `build_kpi(doc, comp, tokens)` — `add_table(rows=2, cols=1)`. 1행: value(28pt bold), 2행: label + delta(10pt).
- **HWPX**: `DataTable` 2x1로 degradation.
- **LLM description (프롬프트 내)**: "KPI: 핵심 수치 한 개를 강조 표시. value는 단위 포함(예: ₩, %, 건). delta는 YoY/QoQ 등 비교값."

**(2) DataTable**

```python
class DataTableComponent(ComponentBase):
    type: Literal["DataTable"] = "DataTable"
    headers: list[str]              # ["항목", "2025", "2026", "증감"]
    rows: list[list[str]]           # 행×열
    emphasis_column_index: int | None = None  # 강조 열(primary 컬러 배경)
    caption: str | None             # 표 제목
```

- **제약**: `len(rows[i]) == len(headers)` 검증(스키마 validator). 최대 20행 × 8열(LLM 토큰/렌더 성능).
- **React**: `<DataTable>` — shadcn/ui Table 기반, 헤더 행 `bg-primary text-white`.
- **PPTX**: `slide.shapes.add_table(rows+1, cols)`. 헤더는 IDINO primary(#0A4FC2) 배경 + 흰 글자. 강조 열은 accent(#FF6B35) 배경.
- **DOCX**: `doc.add_table(rows+1, cols, style="IDINO Table")`. `caption`은 표 위 Heading3.
- **HWPX**: HWPX 표 스펙 네이티브 매핑(`<hp:tbl>`). 스타일은 제한적 — 헤더 셀 회색 배경만 보장.

**(3) BulletList**

```python
class BulletListComponent(ComponentBase):
    type: Literal["BulletList"] = "BulletList"
    items: list[BulletItem]
    numbered: bool = False

class BulletItem(BaseModel):
    text: str
    sub_items: list[str] = []   # 2레벨 제한
    emphasis: Literal["normal", "bold", "highlight"] = "normal"
```

- **제약**: 최대 12개 항목. 2레벨 초과 금지(프롬프트 + validator 양쪽).
- **React**: `<ul class="list-disc">` 또는 `<ol>`. `emphasis=highlight`는 `bg-accent/20`.
- **PPTX**: paragraph별 `add_paragraph(text, level=0/1)`. 마스터의 본문 placeholder를 우선 사용.
- **DOCX**: `doc.add_paragraph(style="List Bullet")` or `"List Number"`.
- **HWPX**: `<hp:p>` + `<hp:listIdRef>`.

### 3.4 Layout 카탈로그

`Page.layout`은 문자열 enum. 각 layout은 **컴포넌트 배치 제약**을 선언한다(PPTX 슬라이드 마스터와 대응).

**MVP 6개**(S1):

| layout | 허용 컴포넌트 | PPTX 대응 마스터 |
|---|---|---|
| `title_slide` | `SlideTitle` + `SlideSubtitle` + `Image?` | 표지 레이아웃 |
| `section_divider` | `Heading(level=1)` | 섹션 분할 |
| `content_body` | 본문 컴포넌트 자유 | 본문 기본 |
| `kpi_dashboard` | `KPI` ×2~4 + `Heading?` | KPI 레이아웃 |
| `two_column` | `TwoColumn` 1개 | 2단 레이아웃 |
| `closing` | `Heading` + `Paragraph` | 맺음 |

**왜 layout을 enum으로?** 현재 `_build_layout_catalog()`가 **한글 레이아웃 이름 하드코딩**으로 실패한 것이 원인(techspec §7.1.1). layout을 코드 enum으로 고정하고, 업로드된 IDINO 마스터의 실제 레이아웃 이름은 **런타임 매핑 테이블**(설정 또는 DB)로 분리한다. LLM은 enum만 본다.

### 3.5 IDINO 브랜드 토큰 강제 방식

- 스키마 단: `design_tokens.brand_preset=idino_*` → 특정 hex 필드 값을 무시·오버라이드.
- PPTX 빌더: IDINO 마스터 사용 시 placeholder의 테마 색을 유지(컴포넌트 스타일 override 금지 경로).
- React 렌더러: CSS 변수(`--primary`, `--accent`)를 `design_tokens`에서 주입, 컴포넌트는 변수만 참조.
- LLM 프롬프트: "design_tokens의 색상은 조직 브랜드이며 임의로 바꾸지 마세요" 명시.

### 3.6 Export 매핑 요약

| 포맷 | 지원 컴포넌트 | 구현 | 노트 |
|---|---|---|---|
| HTML 프리뷰 | 22/22 | React | 완전 지원 |
| PPTX | 22/22 | python-pptx + IDINO 마스터 | 차트 네이티브 |
| DOCX | 22/22 | docxtpl / python-docx | 차트=matplotlib PNG |
| HWPX | 14/22 | python-hwpx(MIT, airmang) | Chart/IconRow 등 텍스트 대체, `metadata.degraded_components`에 기록 |
| PDF | 22/22 | HTML 프리뷰 → Playwright print | 가장 정확한 렌더, 서버 부하 큼 |
| HWP | — | **생성 포기** (techspec §7.3.1 결정) | UI에서 "HWPX로 받기" 안내 |

---

## 4. 과제 3 — 모듈 배치 및 레이어 구조

### 4.1 백엔드

#### 4.1.1 신규 모듈 — `modules/documents_v2/`

P2 고정 구조:

```
backend/app/modules/documents_v2/
├── __init__.py
├── router.py        # POST /v2/documents (generate) / GET / PATCH / DELETE / exports
├── service.py       # DocumentServiceV2: LLM→Schema→저장, 부분 재생성, export 위임
├── schemas.py       # DocumentSchema + 22 컴포넌트 + request/response
├── models.py        # DocumentV2 ORM, DocumentTemplateV2 ORM (templates와 통합)
├── utils.py         # schema→HTML 변환 유틸(프리뷰용, 선택적)
├── constants.py     # DocumentType/layout enum 문자열, MAX_PAGES 등
└── exceptions.py    # UnsupportedComponentError, LockedRegionError 등
```

**왜 `documents_v2`인가?** 기존 `modules/documents`는 **업로드 원본 파일** 관리(domain-model.md의 "Document" = 업로드 문서). 여기서 다루는 것은 "생성되는 문서"로 엄밀히는 `Report` 개념에 더 가깝다. 그러나 이제 보고서/회의록/제안서/자유문서를 **단일 추상**으로 다루므로 `reports`는 좁다. `generated_documents`도 검토했으나 짧고 의미 명확한 `documents_v2`를 채택. (네이밍 최종 확정은 Phase 2 착수 시 database-architect 합의.)

#### 4.1.2 빌더 레이어 — `integrations/document_builders/`

```
backend/app/integrations/document_builders/
├── __init__.py
├── base.py          # DocumentBuilder ABC + BuilderRegistry
├── html/
│   ├── __init__.py
│   └── renderer.py  # Server-side HTML 렌더(프리뷰 fallback용, 주로는 Next.js가 처리)
├── pptx/
│   ├── __init__.py
│   ├── builder.py        # PptxBuilder(DocumentBuilder)
│   ├── components.py     # 22 컴포넌트 → python-pptx 변환 함수
│   └── layout_resolver.py # 업로드된 마스터 ↔ layout enum 런타임 매핑(§3.4)
├── docx/
│   ├── __init__.py
│   ├── builder.py
│   └── components.py
├── hwpx/
│   ├── __init__.py
│   ├── builder.py        # python-hwpx(airmang) 어댑터
│   └── components.py     # 지원 14종만 구현 + 폴백 정책
└── pdf/
    ├── __init__.py
    └── builder.py        # Playwright HTML→PDF
```

**왜 ABC + Registry?** 신규 포맷(예: Markdown export) 추가가 파일 2개로 끝나야 한다. P4 Router→Service→Integration 흐름에서 Service가 `BuilderRegistry.get(format)`만 호출하도록 설계.

#### 4.1.3 컴포넌트 등록 방식

- Pydantic discriminated union은 **스키마 표현**.
- 빌더별 컴포넌트 처리는 **함수 레지스트리**(Pydantic discriminator 값 기준 dict 디스패치). 클래스 계층 과잉 피함.

```python
# 예: pptx/components.py
PPTX_BUILDERS: dict[str, Callable[[Slide, Component, DesignTokens], None]] = {
    "KPI": build_kpi,
    "DataTable": build_datatable,
    "BulletList": build_bulletlist,
    # ...
}
```

#### 4.1.4 기존 모듈과의 관계

| 기존 | Phase 1 결정 |
|---|---|
| `modules/reports` | **단계적 폐기**. S2에 `documents_v2`와 병존, S4에 read-only 모드, S6에 완전 제거. |
| `modules/templates` | **흡수 통합**. 템플릿은 `DocumentSchema`에 `mode=template_fill` + `locked=true` 페이지로 표현되어 `documents_v2`의 하위 개념이 됨. 기존 CRUD는 S3에서 이관. |
| `workers/report_generator.py` | **분해**. LLM 호출은 `documents_v2/service.py`로, 빌더 로직은 `integrations/document_builders/*`로 이관. 하드코딩 `_build_layout_catalog()`는 폐기. |
| `workers/jinja2_engine.py` | **부분 재활용**. 변수 치환 로직은 `template_fill` 모드에서 slot 주입 시 재사용 가능(특히 docxtpl 흐름). 독립 실행 경로는 폐기. |
| `workers/structured_schemas.py` | **대체**. 기존 JSON 스키마는 DocumentSchema로 일원화. 일부 프롬프트 엔지니어링 노하우는 포팅. |
| `integrations/rag/agentic_rag.py` | **dead code 제거** (techspec §7.2.1-R5). `modules/search/agentic_search.py`만 존치. |

### 4.2 프론트엔드

#### 4.2.1 신규 구조

```
frontend/src/
├── app/(user)/designer/
│   ├── create/              # Mode A: 자유 생성 진입
│   │   └── page.tsx
│   ├── fill/[templateId]/   # Mode B: 양식 채우기
│   │   └── page.tsx
│   └── [documentId]/
│       └── page.tsx         # 편집/프리뷰
├── components/document-designer/
│   ├── preview-panel.tsx        # iframe 라이브 프리뷰
│   ├── editor-sidebar.tsx       # 컴포넌트 편집 패널
│   ├── prompt-box.tsx           # 자연어 입력 + 부분 재생성 버튼
│   ├── design-token-picker.tsx  # 브랜드 토큰 UI
│   └── export-menu.tsx          # PPTX/DOCX/HWPX/PDF 다운로드
└── components/document-schema/
    ├── renderer.tsx             # DocumentSchema → React 트리
    ├── components/              # 22개 React 컴포넌트 (SlideTitle.tsx, KPI.tsx …)
    └── layouts/                 # 6개 layout 래퍼
```

#### 4.2.2 페이지 경로 결정

- **Mode A (user)**: `(user)/designer/create` (신규). 기존 `(user)/reports/` **유지 but 내부 교체**. 첫 화면에서 "자유 생성" / "양식으로 시작" 선택 → Mode A는 `/designer/create`로, Mode B는 `/designer/fill/[id]`로 라우팅.
- **Mode B (user)**: 기존 `(user)/reports/`의 보고서 생성 플로우와 템플릿 선택 흐름을 **designer** 하위로 병합.
- **(admin) 템플릿 편집 (Q9 확정, v1.6)**: `(admin)/template-designer/` 신규 라우트. 동일 `components/document-designer/` Shell을 props(`mode="template_authoring"`, `allow_lock_toggle=true`)로 재사용. 저장 시 `tb_documents_v2_templates` 경로. 상세는 `phase1_decisions.md` Q9.
  ```
  app/(admin)/template-designer/
    ├── create/page.tsx         신규 템플릿 작성
    └── [templateId]/page.tsx   기존 템플릿 편집
  ```
- `(admin)/templates/`는 **템플릿 목록 관리자 페이지로 역할 축소**. 편집은 `/template-designer/[id]`로 위임.

### 4.3 데이터 흐름도

**공통 생성 흐름**:

```
User → Router(POST /v2/documents)
     → Service.generate()
        ├─ Mode A: build prompt + RAG context → LLM.structured_output(DocumentSchema)
        └─ Mode B: load template.schema → build slot-fill prompt → LLM.structured_output(partial)
     → Save DocumentV2 row (schema JSONB)
     → Return schema to client
Client (Next.js)
     → DocumentRenderer(schema) → 실시간 프리뷰
     → [Export 요청] → Router(POST /v2/documents/{id}/export?format=pptx)
                     → Service.export() → BuilderRegistry.get("pptx").build(schema)
                     → MinIO upload → presigned URL 반환
```

**부분 재생성**:

```
User: "3번째 슬라이드의 KPI를 더 공격적인 목표로 바꿔줘"
  → Router(POST /v2/documents/{id}/regenerate-component)
     body: { page_id: "p3", component_id: "c2", instruction: "..." }
  → Service: 기존 schema + component + instruction → LLM → 단일 Component 반환
  → JSONB 패치 후 저장
  → 클라이언트 낙관적 업데이트
```

**부분 편집 저장 (Q10 확정, v1.6)** — RFC 6902 JSON Patch는 도입하지 않는다. Partial DocumentSchema PATCH로 통일:

```
User 편집 debounce 500ms
  → Router(PATCH /v2/documents/{id})
     body: { patch_type: "component" | "page" | "tokens" | "metadata",
             page_id?: "p3", component_id?: "c2",
             component?: {...},  // 교체할 Component 전체
             page?: {...},
             tokens?: {...} }
  → Service: Pydantic validation → jsonb_set 적용 → 저장
  → 응답: 전체 DocumentSchema (클라이언트 캐시 동기화용)
```

iframe ↔ Shell 메시지(앱 내부 프로토콜):
- `{ type: "element-select", component_id, page_id }`
- `{ type: "token-update", tokens }` (실시간 미리보기, 서버 저장 전)
- `{ type: "schema-patch-local", patch }` (Shell → iframe 재렌더 트리거)
- `{ type: "export-request", format }`

### 4.4 동기성 결정 — WebSocket vs Celery vs SSE

| 기능 | 선택 | 근거 |
|---|---|---|
| 전체 문서 생성(초기) | **동기 HTTP + 백그라운드 Celery 선택적** | 첫 Schema 생성은 5~15초 예상. 프론트는 fetch로 대기(loading UI). 30초 초과 예상 시에만 Celery로 전환. |
| 파일 Export (PPTX/DOCX) | **Celery 비동기** | 현행 유지. 빌더 호출은 CPU 부하 있음. MinIO 업로드 완료 후 상태 폴링. |
| HTML 프리뷰 갱신 | **클라이언트 즉시 렌더** | 서버 왕복 없이 schema JSON만 주고받고 React가 렌더. |
| 부분 재생성 | **동기 HTTP** | 1~3초, WS 불필요. |
| **편집 저장 (v1.6, Q10)** | **`PATCH /v2/documents/{id}` Partial DocumentSchema** | RFC 6902 미도입. `patch_type` 판별 필드 + 부분 본체. 동시편집 미지원. |
| 긴 자유생성(10슬라이드+) 진행상황 | **SSE** | 페이지별 단위 스트리밍. 향후 enhancement. S7에서 구현. |

**WS를 쓰지 않는 이유**: 현재 WS는 챗봇 전용. 생성 UI에서 양방향 지속 세션 불필요. SSE(단방향 스트림)가 Celery/Redis 없이도 충분하며 Nginx 프록시 설정도 더 단순.

---

## 5. 과제 4 — LLM 통합 방식

### 5.1 Structured Outputs 강제 전략

- **근본 원칙**: 모든 LLM 호출은 `LLMClient.generate_structured(prompt, json_schema=DocumentSchema.model_json_schema())`만 허용. 자유 텍스트 호출 금지(P6 재확인).
- **JSON Schema 생성**: Pydantic v2의 `.model_json_schema()`를 그대로 OpenAI `response_format.json_schema`에 전달. Discriminated Union은 `oneOf`로 자동 변환됨.
- **프롬프트 골격**:
  ```
  System: 당신은 {document_type} 전문 작성자입니다.
          반드시 제공된 JSON 스키마에 맞춰 응답하세요.
          사용 가능한 컴포넌트: {component_list_with_descriptions}
          사용 가능한 레이아웃: {layout_list}
          디자인 토큰은 임의 변경 금지.
  User:   {user_prompt + RAG_context + citations_required}
  ```

### 5.2 Mode A vs Mode B 프롬프트 차이

| | Mode A | Mode B |
|---|---|---|
| LLM에 전달되는 schema | 전체 DocumentSchema | `pages[].components[]` 중 `locked=false` 필드만 (partial schema) |
| 출력 강제 | 전체 문서 생성 | slot만 채우기(나머지 필드 이미 확정) |
| 프롬프트 역할 | "이 주제로 N페이지 문서를 만들어주세요" | "이 양식의 빈 슬롯만 채워주세요. 기존 구조 변경 금지." |
| 재생성 단위 | 문서 전체 / 페이지 / 컴포넌트 | 슬롯 단위 |

### 5.3 멀티 프로바이더 Structured Output 차이 처리

현재 5개 프로바이더 중 지원 차이(techspec §11):

| 프로바이더 | Structured 지원 | 전략 |
|---|---|---|
| OpenAI | strict JSON Schema | **기본 경로** |
| Azure OpenAI | strict | 동일 |
| Gemini | 부분(OpenAI 호환 엔드포인트) | 스키마 단순화 필요 시 `StrictSchemaFallback` — discriminator 제거한 평탄화 버전 주입 |
| Claude | Tool Use 패턴 | `LLMClient.generate_structured` 구현 내부에서 Tool 선언으로 변환 |
| vLLM/SGLang | 모델 의존 | 사용자 선택 시만 허용. 미지원 모델엔 경고. |

**왜 LLMClient 한 층에서 처리하는가**: P1(단일 구현). 호출 측(Service)은 프로바이더를 모른다.

### 5.4 컴포넌트 부분 재생성

- API: `POST /v2/documents/{id}/regenerate-component` + `POST /v2/documents/{id}/regenerate-page`.
- 프롬프트 패턴: 기존 schema 일부 + "다음 컴포넌트만 새로 생성" + user instruction → `json_schema`는 **단일 컴포넌트 유니언**으로 축소.

### 5.5 이미지 자동 삽입 알고리즘

기존 자산 `integrations/image_generation/service.py`의 DALL-E 3 + Unsplash 둘 다 활성 유지.

**선택 알고리즘**:

```
if component.src in schema:            # 사용자 지정 URL
    use_as_is
elif component.prompt 존재:
    if prompt에 "로고|스크린샷|실제 제품" 키워드 → Unsplash (사실적 이미지)
    elif prompt에 "아이콘|일러스트|개념도|추상" 키워드 → DALL-E 3
    else: Unsplash 시도 → 관련성 0.6 미만이면 DALL-E 3 fallback
else:
    LLM이 prompt 생성(component.prompt 필드 채움) → 위 규칙 적용
```

**비용 제어**: `metadata.llm_provider="openai"`일 때도 DALL-E 3는 별도 API key 필요. 관리자 설정에서 "이미지 생성 예산 월 N회" 제한(S3 구현).

### 5.6 Agentic RAG ↔ Mode A 결합

- Mode A에서 사용자가 "기준 문서" 선택 시: `AgenticSearchService`(기존)를 활용해 다회 검색 루프 수행.
- 반환된 chunk들을 `metadata.citations`에 기록.
- 프롬프트에 "다음 근거만 사용해 작성하세요" + "모든 주요 주장에 [cite: id] 표기" 삽입.
- Component 수준에서는 `ComponentBase`에 선택적 `citation_ids: list[str]` 추가하지 않고, **metadata 중앙 집중**. 렌더러가 본문 내 `[cite: …]` 마커를 감지해 푸터와 연결.

---

## 6. 과제 5 — 재활용 자산 최종 분류

| # | 자산 | 상태 | 재활용 방식 | 편입 위치 |
|---|---|---|---|---|
| 1 | `workers/report_generator.py` `_rag_extract_content` | **재활용** | Service에서 RAG 컨텍스트 주입 로직으로 이관 | `documents_v2/service.py` |
| 2 | `workers/report_generator.py` `_build_layout_catalog()` | **폐기** | 하드코딩 → layout enum + 런타임 매핑 | — |
| 3 | `workers/report_generator.py` PPTX 스타일 helper (헤더바/푸터 등) | **재활용** | IDINO 브랜드 적용 함수로 추출 | `integrations/document_builders/pptx/components.py` |
| 4 | `workers/structured_schemas.py` | **부분 재활용** | 회의록 전용 schema는 컴포넌트 매핑 참고. 나머지는 DocumentSchema로 대체. | — |
| 5 | IDINO 슬라이드마스터 파일 16종 | **재활용** | MinIO 그대로 유지. layout_resolver가 마스터의 실제 이름을 enum에 매핑. | `integrations/document_builders/pptx/layout_resolver.py` |
| 5-B | 조직별 PPTX 템플릿 (`tb_report_templates` 내 레코드, v1.6 Q4) | **S4 자동 변환 스크립트의 입력 소스 확장** | 현 시점 가정: "IDINO 슬라이드마스터 외 조직별 템플릿 없음". 실재 시 `tb_document_templates`와 동일 경로로 처리하되 S4 스크립트 입력에 `tb_report_templates`를 추가. 변환 실패 시 관리자 수동 재작성. | S4 변환 스크립트 |
| 6 | `modules/templates` (`tb_document_templates`) | **통합** | DocumentV2 하위 타입으로 흡수. 데이터 마이그레이션 필요. | `documents_v2` |
| 7 | `tb_report_templates` | **폐기** | 중복 테이블. `tb_document_templates`로 통합 후 drop. | — |
| 8 | `modules/agents` (tb_agents) | **재활용** | 그대로. Mode A/B 모두 Agent의 system_prompt/temperature/max_tokens 사용. `agent_type` enum에 `freeform_doc` 추가만. | 현 위치 유지 |
| 9 | `workers/jinja2_engine.py` 변수 치환 로직 | **부분 재활용** | Mode B에서 slot 주입 시 docxtpl 호출부만 사용. 양식 자동분석/카테고리 분류는 폐기. | `integrations/document_builders/docx/` 내부 유틸 |
| 10 | Jinja2 양식 자동 분석 (빈 양식 → 변수 추출) | **폐기** | 새 모델: Mode B 템플릿은 **DocumentSchema로 저장**. 기존 `.docx/.pptx` 원본 템플릿은 관리자 페이지에서 **DocumentSchema 에디터로 변환**(반자동, S4). | — |
| 11 | `modules/templates` 변수 매핑 에디터(dialog/inline 2모드) | **재설계** | 단일 `designer` UX로 통합. Dialog/Inline 분기 제거. | `frontend/components/document-designer/` |
| 12 | `integrations/image_generation/` DALL-E 3 + Unsplash | **재활용** | 그대로. 선택 알고리즘(§5.5)을 `documents_v2/service.py`에서 호출. | 현 위치 유지 |
| 13 | `modules/search/agentic_search.py` AgenticSearchService | **재활용** | Mode A에서 직접 호출. REST 챗봇에도 옵션으로 활성화(H7 후속). | 현 위치 유지 |
| 14 | `integrations/rag/agentic_rag.py` AgenticRAGEngine | **폐기** | dead code. 제거. | — |
| 15 | `integrations/rag/graph_rag.py` | **현상 유지(관망)** | 활성 사용처 없음. S6에서 폐기 검토. | — |
| 16 | Multi-provider LLM Factory (`integrations/llm/factory.py`) | **재활용 및 확장** | `generate_structured(schema)` 통일 인터페이스 추가. Claude Tool Use 변환은 Claude 클라이언트 내부. | 현 위치 유지 |
| 17 | `core/llm_keys.py` DB 저장 키 해석 | **재활용** | 그대로. | 현 위치 유지 |
| 18 | Citations UI (챗봇에서 구현된) | **재활용** | 동일 컴포넌트를 `designer`에서도 사용. | `frontend/components/common/citations.tsx` 로 승격 |
| 19 | docxtpl | **부분 재활용** | DOCX 빌더의 Jinja2 치환 케이스에서만 사용. 기본은 python-docx로 프로그래매틱 빌드. | `document_builders/docx/` |
| 20 | Celery 비동기 인프라 | **재활용** | Export(PPTX/DOCX/HWPX/PDF 파일 빌드)에 사용. Schema 생성은 동기. | 현 위치 유지 |

**재활용 비율 추정**: 파일·함수 단위 약 **55~60%**. 주요 이익은 IDINO 브랜드 빌드 로직·Agent/LLM 인프라·이미지 생성·Agentic RAG 재사용. 주요 폐기는 `_build_layout_catalog()`, 이중 템플릿 테이블, Jinja2 자동 분석, rendering_mode 분기.

---

## 7. 과제 6 — HWP/HWPX 어댑터 설계 (고수준)

상세 파생은 research-assistant에 위임하되 기준선 확정:

### 7.1 기술 선택 (확정)

techspec §7.3.2 "시나리오 B 균형형"을 그대로 확정.

- **HWPX 생성**: `python-hwpx` (airmang, MIT)
- **HWPX 파싱**: `python-hwpx`로 기존 zipfile 파싱 교체
- **HWP 파싱**: `olefile` + `hwp-extract`(Apache 2.0) 보강
- **HWP 생성**: **지원하지 않음**. UI에서 "HWPX로 내려받기" 안내.
- **금지**: `pyhwp`(AGPL 상용 위험).

### 7.2 모듈 위치

- 빌더: `backend/app/integrations/document_builders/hwpx/builder.py`
- 파서(업로드 문서용): `backend/app/integrations/docling/` 하위에 기존 HWPX 파서를 `python-hwpx` 기반으로 교체(별도 PR).

### 7.3 지원 컴포넌트 서브셋

§3.6 표 재확인. **이 표는 HWPX 포맷이 표현 가능한 컴포넌트 집합을 의미하며, 실제 빌더 구현은 §3.2의 도입 스프린트를 따른다** (Q6 확정, `phase1_decisions.md` 참조):

- **완전 지원 (14종)**: SlideTitle, Heading, Paragraph, BulletList, DataTable, Image, Quote, ImageGrid, TwoColumn, ThreeColumn, Hero, Comparison, ExecutiveSummary, ActionItemList, AttendeeList
  - S5 HwpxBuilder 구현 범위: SlideTitle/Heading/Paragraph/BulletList/DataTable/Image/Quote + 레이아웃(TwoColumn/ThreeColumn/Hero/Comparison/ImageGrid) = 12종
  - S6 추가: ExecutiveSummary/ActionItemList/AttendeeList = 3종
- **Degradation 처리 (8종)**: KPI(DataTable 2x1), Chart(PNG 이미지), Callout(인용 단락), Timeline(BulletList), IconRow(BulletList), RiskMatrix(DataTable), SlideSubtitle(Heading level=3), Hero 내 이미지 과도 사용 금지.
- Degradation 발생 시 `metadata.degraded_components`에 컴포넌트 id 목록 저장 → UI에서 "HWPX에서 간소화 표시됨" 배지.

### 7.4 어댑터 ABC 준수

```python
class HwpxBuilder(DocumentBuilder):
    format_id = "hwpx"

    def build(self, schema: DocumentSchema) -> bytes:
        doc = HwpxDocument.new(design_tokens=schema.design_tokens)
        for page in schema.pages:  # hwpx는 전부 section으로 취급
            section = doc.add_section(layout=page.layout)
            for comp in page.components:
                handler = HWPX_BUILDERS.get(comp.type, degrade_to_paragraph)
                handler(section, comp, schema.design_tokens)
        return doc.to_bytes()
```

HWPX는 슬라이드 개념이 없으므로 `page_kind=slide`인 Page도 A4 섹션으로 변환(페이지 구분자 삽입).

---

## 8. 과제 7 — 후속 에이전트 인계 (부록 E 참조)

각 에이전트에 필요한 입력의 요약은 부록 E에. 여기서는 책임 분장만 명시.

- **database-architect** — DocumentSchema 저장 테이블, `tb_document_templates` 통합 스키마, 기존 `tb_report_templates`/`tb_generated_reports` 마이그레이션, Alembic 006 작성.
- **frontend-specialist** — 22개 React 컴포넌트, `designer` UX(프리뷰/편집/프롬프트/Export), Mode A/B 라우팅, citations 컴포넌트 승격.
- **research-assistant** — `python-hwpx` 실제 API 탐색, HWPX 생성 PoC, `hwp-extract` 통합, LibreOffice+H2Orestart 사이드카 컨테이너 스펙(S5 옵션).

---

## 9. 과제 8 — Phase 2·3·4 실행 로드맵

### 9.1 스프린트별 Definition of Done

| 스프린트 | 기간 | Deliverable | DoD |
|---|---|---|---|
| **S1** DocumentSchema MVP | 2주 | Pydantic 모델 전체, 22 컴포넌트 중 **6개**(MVP: SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable), React 렌더러, HTML 프리뷰, `PATCH /v2/documents/{id}` Partial body | `POST /v2/documents` Mode A로 **6-컴포넌트** 문서 생성, 프리뷰 정상, PATCH로 부분 편집 가능. QA 80+ 유지 |
| **S2** PPTX 빌더 + Mode A PoC | 2주 | `PptxBuilder`, layout_resolver, IDINO 마스터 매핑, 1개 보고서 타입(slide_report) end-to-end | 업로드된 IDINO 마스터로 `slide_report` 생성→PPTX 다운로드 성공. 구 `_build_layout_catalog` 완전 미사용 |
| **S3** 컴포넌트 확장 + 이미지 | 2주 | 컴포넌트 13종 추가(S1 5 + S2 포함 누적 13), Chart/Image/DALL-E/Unsplash 통합 | 한 문서 내 차트+이미지 자동 삽입 동작. 월별 이미지 쿼터 관리 UI |
| **S4** Mode B 통합 + 템플릿 에디터 | 1.5주 | `mode=template_fill`, locked 페이지, DocumentSchema 기반 템플릿 에디터 | 기존 Jinja2 16개 템플릿 중 5개를 DocumentSchema로 변환. Mode B 슬롯 채우기 성공 |
| **S5** HWPX + DOCX 고도화 | 2주 | `HwpxBuilder`(S5 구현 **12종** — Q6), `python-hwpx` 전면 도입, **스타일 이름·폰트 적용까지** (색상 주입은 stretch/S6 이연 — Q7), DOCX 빌더 컴포넌트 22/22 | HWPX 다운로드 한컴 2020+에서 열림, 한글 UTF-8 정상 표시, degraded_components 기록 확인 |
| **S6** RAG·보고서 품질 + 특화 컴포넌트 | 1.5주 | 회의록 전용 프롬프트, Agentic RAG/Mode A 결합, 보고서 특화 컴포넌트 4종, HWPX 보고서 특화 3종 추가(ExecutiveSummary/ActionItemList/AttendeeList — Q6), HWPX 표 헤더 색상 주입(Q7), `source_document_ids` 역방향 질의 실측 후 정규화 결정(Q2) | 회의록 생성 시 참석자/결정사항/액션아이템 구조화. Citations 자동 삽입. HWPX 헤더 배경색 적용 검증 |
| **S7** 인라인 편집 + 부분 재생성 + QA | 2주 | `regenerate-component`/`regenerate-page` API, 클라이언트 인라인 편집, PDF export, 폐기 모듈 삭제 | `modules/reports` 제거, `tb_report_templates` drop. QA 90+ |

### 9.2 의존성 그래프

```
S1 (Schema) ──────────────┬─→ S2 (PPTX)
                          ├─→ S5 (HWPX) ──→ S6 (RAG)
                          ├─→ S4 (Mode B)
S2 ───→ S3 (컴포넌트 확장)  ┘
S3 ───→ S6 / S7
S4 ───→ S7 (폐기 흡수)
```

- **S1 스키마 lock**이 모든 후속 스프린트의 전제. S1 완료 전 S2·S4·S5 착수 금지.
- S3와 S4는 병렬 가능(별도 개발자).
- S7은 반드시 마지막 — 기존 모듈 제거는 모든 신규 경로 검증 후.

### 9.3 기능 폐기 순서

| 시점 | 조치 |
|---|---|
| S2 완료 | `_build_layout_catalog()` 호출 경로 제거, 신규 PPTX 빌더 전환 |
| S4 완료 | 관리자 UI에서 Jinja2 양식 업로드 경로 **read-only**, 신규 업로드 불가 |
| S5 완료 | HWP 생성 UI 버튼 제거, HWPX 안내 문구 전환 |
| S6 완료 | `structured_schemas.py` 폐기 (DocumentSchema로 대체) |
| S7 완료 | `modules/reports` 제거, `modules/templates` 제거, `tb_report_templates` drop |

### 9.4 데이터 마이그레이션

- **기존 `tb_document_templates`** → `tb_documents_v2_templates`(가칭). Jinja2 변수 정의는 `DocumentSchema` + `locked` 페이지로 **자동 변환 스크립트**(S4). 자동 변환 실패 템플릿은 관리자가 수동 재작성.
- **기존 `tb_generated_reports`** → 아카이브 테이블로 이름 변경(`tb_generated_reports_archive`). 읽기 전용 열람만 유지(1년). 신규 생성은 `tb_documents_v2`로.
- **16개 IDINO 슬라이드마스터 PPTX** → MinIO 경로 변경 없음. `layout_resolver`가 이름 매핑.

### 9.5 리스크 매트릭스 (부록 D)

부록 D 참조.

---

## 10. Phase 1 완료 기준 자체 검증

- [x] DocumentSchema 타입/모드/토큰/페이지/컴포넌트/메타 6개 구역 모두 정의
- [x] 22개 컴포넌트 카탈로그, 도입 스프린트 명시
- [x] MVP 5종 + 단계적 Phase별 추가 순서
- [x] 백엔드 모듈 P2 구조 준수 + 빌더 레이어 P4 단방향 명시
- [x] 프론트엔드 페이지 경로 Mode A/B 분기 확정
- [x] 동기/비동기 결정(WS 불채택 이유 포함)
- [x] 멀티프로바이더 Structured Output 처리 전략
- [x] Agentic RAG 활용 결정
- [x] 재활용/폐기 20항목 분류
- [x] HWPX 어댑터 기술·위치·서브셋 확정
- [x] 7개 스프린트 DoD + 의존성 + 폐기 순서 + 마이그레이션
- [x] 3000~5000 단어 범위, 한국어, 근거 명시

---

## 부록 A — DocumentSchema JSON 샘플 3건

### A.1 Mode A 자유 생성 — slide_report (3페이지)

```json
{
  "document_id": "7b2a5f3e-1c4d-4b8a-9e7f-0a1b2c3d4e5f",
  "schema_version": "1.0",
  "type": "slide_report",
  "mode": "free_generation",
  "template_id": null,
  "design_tokens": {
    "primary_color": "#0A4FC2",
    "accent_color": "#FF6B35",
    "text_color": "#1F2937",
    "background_color": "#FFFFFF",
    "font_family": "Pretendard",
    "spacing": "normal",
    "brand_preset": "idino_default"
  },
  "pages": [
    {
      "id": "p1",
      "page_kind": "slide",
      "layout": "title_slide",
      "title": null,
      "locked": false,
      "components": [
        { "id": "c1", "type": "SlideTitle", "locked": false, "anchor": null, "text": "2026 Q1 매출 보고서" },
        { "id": "c2", "type": "SlideSubtitle", "locked": false, "anchor": null, "text": "IDINO 사업개발팀 · 2026-04-19" }
      ],
      "speaker_notes": "회사 소개와 보고서 범위를 간단히 설명합니다.",
      "page_number_visible": false
    },
    {
      "id": "p2",
      "page_kind": "slide",
      "layout": "kpi_dashboard",
      "title": "핵심 지표",
      "locked": false,
      "components": [
        { "id": "c3", "type": "Heading", "locked": false, "anchor": null, "level": 2, "text": "2026 Q1 실적 요약" },
        { "id": "c4", "type": "KPI", "locked": false, "anchor": null, "label": "총 매출", "value": "₩1.2B", "delta": "+12% YoY", "delta_direction": "up", "description": "전년 동기 대비" },
        { "id": "c5", "type": "KPI", "locked": false, "anchor": null, "label": "신규 계약", "value": "24건", "delta": "+3건", "delta_direction": "up", "description": null },
        { "id": "c6", "type": "KPI", "locked": false, "anchor": null, "label": "이탈률", "value": "2.1%", "delta": "-0.4%p", "delta_direction": "down", "description": "개선" }
      ],
      "speaker_notes": "세 개 KPI 중 이탈률 개선이 가장 주목할 만한 포인트입니다.",
      "page_number_visible": true
    },
    {
      "id": "p3",
      "page_kind": "slide",
      "layout": "content_body",
      "title": "Q2 실행 계획",
      "locked": false,
      "components": [
        { "id": "c7", "type": "Heading", "locked": false, "anchor": null, "level": 2, "text": "Q2 실행 계획" },
        { "id": "c8", "type": "BulletList", "locked": false, "anchor": null, "numbered": true, "items": [
          { "text": "신규 고객사 파일럿 런칭", "sub_items": ["제조업 3사", "공공 1사"], "emphasis": "bold" },
          { "text": "파트너십 확대", "sub_items": [], "emphasis": "normal" },
          { "text": "인력 충원: 개발 2명, 영업 1명", "sub_items": [], "emphasis": "highlight" }
        ]}
      ],
      "speaker_notes": null,
      "page_number_visible": true
    }
  ],
  "metadata": {
    "created_at": "2026-04-19T10:00:00Z",
    "updated_at": "2026-04-19T10:00:05Z",
    "generated_by_user_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "llm_provider": "openai",
    "llm_model": "gpt-4o",
    "prompt_tokens": 1280,
    "completion_tokens": 640,
    "source_document_ids": [],
    "source_chat_session_id": null,
    "citations": [],
    "degraded_components": []
  }
}
```

### A.2 Mode B 양식 채우기 — weekly_status (2페이지, locked 포함)

```json
{
  "document_id": "a1b2c3d4-...-0001",
  "schema_version": "1.0",
  "type": "weekly_status",
  "mode": "template_fill",
  "template_id": "tmpl-weekly-2026",
  "design_tokens": { "primary_color": "#0A4FC2", "accent_color": "#FF6B35", "text_color": "#1F2937", "background_color": "#FFFFFF", "font_family": "Pretendard", "spacing": "compact", "brand_preset": "idino_default" },
  "pages": [
    {
      "id": "p1", "page_kind": "section", "layout": "content_body",
      "title": "주간 업무 보고서", "locked": true,
      "components": [
        { "id": "c1", "type": "Heading", "locked": true, "anchor": "title_slot", "level": 1, "text": "{{week}} 주간 업무 보고서" },
        { "id": "c2", "type": "DataTable", "locked": true, "anchor": "summary_table",
          "headers": ["구분", "내용"],
          "rows": [["작성자", "__AUTO_FILL__"], ["부서", "__AUTO_FILL__"], ["주차", "__AUTO_FILL__"]],
          "emphasis_column_index": null, "caption": null }
      ],
      "speaker_notes": null, "page_number_visible": false
    },
    {
      "id": "p2", "page_kind": "section", "layout": "content_body",
      "title": "이번 주 실적", "locked": false,
      "components": [
        { "id": "c3", "type": "Heading", "locked": true, "anchor": "achievements_heading", "level": 2, "text": "이번 주 실적" },
        { "id": "c4", "type": "BulletList", "locked": false, "anchor": "achievements_slot", "numbered": false, "items": [] }
      ],
      "speaker_notes": null, "page_number_visible": true
    }
  ],
  "metadata": { "created_at": "2026-04-19T10:00:00Z", "updated_at": "2026-04-19T10:00:00Z", "generated_by_user_id": "...", "llm_provider": null, "llm_model": null, "prompt_tokens": null, "completion_tokens": null, "source_document_ids": [], "source_chat_session_id": null, "citations": [], "degraded_components": [] }
}
```

### A.3 회의록 — minutes (1페이지, AttendeeList + ActionItemList)

```json
{
  "document_id": "m-...-2026-04-18",
  "schema_version": "1.0",
  "type": "minutes",
  "mode": "free_generation",
  "template_id": null,
  "design_tokens": { "primary_color": "#0A4FC2", "accent_color": "#FF6B35", "text_color": "#1F2937", "background_color": "#FFFFFF", "font_family": "Pretendard", "spacing": "normal", "brand_preset": "idino_default" },
  "pages": [
    {
      "id": "p1", "page_kind": "section", "layout": "content_body",
      "title": "2026-04-18 주간 회의록", "locked": false,
      "components": [
        { "id": "c1", "type": "Heading", "locked": false, "anchor": null, "level": 1, "text": "2026-04-18 주간 회의록" },
        { "id": "c2", "type": "AttendeeList", "locked": false, "anchor": null,
          "attendees": [
            { "name": "변동언", "role": "대표이사", "present": true },
            { "name": "김용휴", "role": "미래기술연구소장", "present": true },
            { "name": "이현수", "role": "AI기술팀", "present": false }
          ]
        },
        { "id": "c3", "type": "Heading", "locked": false, "anchor": null, "level": 2, "text": "안건 및 결정사항" },
        { "id": "c4", "type": "BulletList", "locked": false, "anchor": null, "numbered": true, "items": [
          { "text": "DocUtil 재설계 Phase 1 착수 승인 [cite: r1]", "sub_items": [], "emphasis": "bold" },
          { "text": "HWPX 우선 지원 확정 [cite: r2]", "sub_items": [], "emphasis": "normal" }
        ]},
        { "id": "c5", "type": "ActionItemList", "locked": false, "anchor": null,
          "items": [
            { "text": "DocumentSchema 초안", "owner": "enterprise-architect", "due": "2026-04-22", "status": "in_progress" },
            { "text": "DB 스키마 변경안", "owner": "database-architect", "due": "2026-04-25", "status": "pending" }
          ]
        }
      ],
      "speaker_notes": null, "page_number_visible": true
    }
  ],
  "metadata": {
    "created_at": "2026-04-18T15:30:00Z", "updated_at": "2026-04-18T15:45:00Z",
    "generated_by_user_id": "...",
    "llm_provider": "openai", "llm_model": "gpt-4o",
    "prompt_tokens": 2040, "completion_tokens": 820,
    "source_document_ids": [],
    "source_chat_session_id": "chat-2026-04-18-weekly",
    "citations": [
      { "id": "r1", "chunk_id": "...", "document_id": "...", "excerpt": "재설계 Phase 1 착수를 승인함" },
      { "id": "r2", "chunk_id": "...", "document_id": "...", "excerpt": "HWPX 우선, HWP 생성은 포기" }
    ],
    "degraded_components": []
  }
}
```

---

## 부록 B — 컴포넌트 카탈로그 전체 props 표

(§3.2 카탈로그 22종 + §3.3 상세 3종이 본문에 이미 수록. 이하 나머지 19종의 props 핵심만 요약)

| 이름 | 핵심 props |
|---|---|
| `SlideTitle` | `text: str` |
| `SlideSubtitle` | `text: str` |
| `Heading` | `text: str`, `level: Literal[1,2,3]` |
| `Paragraph` | `text: str`, `emphasis: Literal["normal","bold","italic"]` |
| `Quote` | `text: str`, `author: str \| None` |
| `Callout` | `text: str`, `variant: Literal["info","warning","success","danger"]` |
| `Image` | `src: str \| None`, `prompt: str \| None`, `alt: str`, `caption: str \| None` (둘 중 하나 필수) |
| `Chart` | `chart_type: Literal["bar","line","pie"]`, `title: str`, `data: {labels: [str], series: [{name, values:[float]}]}` |
| `Timeline` | `events: [{date: str, title: str, description: str \| None}]` |
| `ImageGrid` | `images: list[Image] (2~4개)` |
| `IconRow` | `items: [{icon: str (lucide name), label: str, description: str \| None}]` |
| `TwoColumn` | `left: list[Component]`, `right: list[Component]`, `ratio: Literal["50-50","60-40","40-60"]` |
| `ThreeColumn` | `columns: list[list[Component]]` (길이 3) |
| `Hero` | `title: str`, `subtitle: str \| None`, `background: Literal["primary","accent","image"]`, `image: Image \| None` |
| `Comparison` | `left: {title, items: [str]}`, `right: {title, items: [str]}` |
| `ExecutiveSummary` | `bullets: list[str] (3~5개)`, `conclusion: str` |
| `RiskMatrix` | `risks: [{title, likelihood: 1-5, impact: 1-5, mitigation: str}]` |
| `ActionItemList` | `items: [{text, owner, due: date, status: Literal["pending","in_progress","done"]}]` |
| `AttendeeList` | `attendees: [{name, role: str \| None, present: bool}]` |

각 항목의 정확한 validator와 React/PPTX/DOCX/HWPX 변환 함수 시그니처는 S1 착수 시 backend-specialist + frontend-specialist가 공동 lock.

---

## 부록 C — 폴더 구조 트리

```
backend/
├── app/
│   ├── core/                              # (변경 없음)
│   ├── modules/
│   │   ├── documents/                     # 기존 (업로드 원본 관리)
│   │   ├── documents_v2/                  # ★ 신규
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py                 # DocumentSchema + 22 컴포넌트
│   │   │   ├── models.py
│   │   │   ├── utils.py
│   │   │   ├── constants.py
│   │   │   └── exceptions.py
│   │   ├── agents/                        # (변경 없음)
│   │   ├── search/                        # (변경 없음, agentic_search 재활용)
│   │   ├── reports/                       # → S7에서 제거
│   │   ├── templates/                     # → S4~S7에서 흡수·제거
│   │   └── ...
│   ├── integrations/
│   │   ├── document_builders/             # ★ 신규 레이어
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # DocumentBuilder ABC + Registry
│   │   │   ├── html/renderer.py
│   │   │   ├── pptx/{builder,components,layout_resolver}.py
│   │   │   ├── docx/{builder,components}.py
│   │   │   ├── hwpx/{builder,components}.py
│   │   │   └── pdf/builder.py
│   │   ├── llm/                           # (확장: generate_structured 통일)
│   │   ├── image_generation/              # (변경 없음)
│   │   ├── rag/                           # agentic_rag.py 제거, graph_rag.py 관망
│   │   ├── vector_store/
│   │   ├── object_storage/
│   │   ├── docling/                       # (HWPX 파서 python-hwpx로 교체)
│   │   └── ocr/
│   └── workers/
│       ├── document_processor.py          # (변경 없음)
│       ├── embedding_generator.py         # (변경 없음)
│       ├── report_generator.py            # → S7에서 제거
│       ├── jinja2_engine.py               # → 부분만 document_builders/docx/로 이관 후 제거
│       ├── structured_schemas.py          # → S6에서 제거
│       └── export_worker.py               # ★ 신규: DocumentBuilder 호출 전담
└── alembic/versions/                      # Alembic 006 (database-architect)

frontend/
├── src/
│   ├── app/
│   │   ├── (user)/
│   │   │   ├── designer/                  # ★ 신규
│   │   │   │   ├── create/page.tsx        # Mode A 진입
│   │   │   │   ├── fill/[templateId]/page.tsx  # Mode B 진입
│   │   │   │   └── [documentId]/page.tsx  # 편집/프리뷰
│   │   │   ├── reports/                   # → S7에서 designer로 리다이렉트
│   │   │   ├── chat/                      # (변경 없음)
│   │   │   └── search/                    # (변경 없음)
│   │   └── (admin)/
│   │       ├── templates/                 # (유지, DocumentSchema 에디터 추가)
│   │       ├── agents/                    # (변경 없음)
│   │       └── ...
│   └── components/
│       ├── document-designer/             # ★ 신규
│       │   ├── preview-panel.tsx
│       │   ├── editor-sidebar.tsx
│       │   ├── prompt-box.tsx
│       │   ├── design-token-picker.tsx
│       │   └── export-menu.tsx
│       ├── document-schema/               # ★ 신규
│       │   ├── renderer.tsx
│       │   ├── components/                # 22개 React 컴포넌트
│       │   └── layouts/                   # 6개 레이아웃 래퍼
│       ├── common/
│       │   └── citations.tsx              # 챗봇에서 승격
│       ├── chat/                          # (변경 없음)
│       ├── search/                        # (변경 없음)
│       └── ui/                            # shadcn/ui (변경 없음)
```

---

## 부록 D — 리스크 매트릭스

| # | 리스크 | 발생확률 | 영향도 | 점수 | 대응책 |
|---|---|---|---|---|---|
| R1 | Gemini/Claude가 Discriminated Union Structured Output을 불완전 지원 | 중 | 높음 | 6 | `StrictSchemaFallback` 평탄화 버전 주비. 멀티프로바이더 테스트 수트 S1 DoD에 포함. |
| R2 | `python-hwpx`가 신생 라이브러리라 생성 품질 부족 | 중 | 중 | 4 | S5에서 PoC 우선. lxml 수동 XML fallback 경로 유지. 한컴 뷰어 호환 테스트 매트릭스. |
| R3 | 기존 16개 IDINO 템플릿 자동 변환 실패율 높음 | 중 | 중 | 4 | S4에서 5개 우선 수동 변환. 관리자 에디터 제공. 호환 layer 필요 시 read-only 모드 유지. |
| R4 | 하드코딩 제거 후 기존 고객 PPTX 품질 체감 저하 | 낮 | 높음 | 4 | S2 PoC 단계에서 현행 대비 A/B 비교 리뷰. QA 90+ 유지 게이트. |
| R5 | Schema JSON 과도 성장 → LLM 토큰 한계 | 낮 | 중 | 2 | 페이지 수 상한(20), 컴포넌트 수 상한(페이지당 10), 부분 재생성으로 분할. |
| R6 | `modules/reports` 병존 기간 중 이중 유지보수 비용 | 높 | 중 | 6 | S4부터 read-only, S7에 완전 제거. 공유 유틸은 `core/` 또는 `integrations/`로 사전 이관. |
| R7 | Playwright PDF 빌더가 서버 메모리 폭주(헤드리스 크롬) | 중 | 중 | 4 | Celery 워커 분리(`pdf-worker` 전용). 동시 2건 제한. |
| R8 | Mode A/B 동시 지원으로 UX 복잡도 증가 → 사용자 혼란 | 중 | 중 | 4 | `designer` 진입 페이지에 2-카드 명확한 분기 + onboarding tour. |
| R9 | 이미지 생성 비용(DALL-E 3) 예산 초과 | 중 | 낮 | 2 | 조직별 월 쿼터. Unsplash 우선 알고리즘. |
| R10 | DocumentSchema v1.0 → v1.1 migration 복잡 | 낮 | 높음 | 4 | `schema_version` 필드 필수화. 버전별 loader. 신규 필드는 반드시 Optional로 추가. |

**Top 3 (점수 높은 순)**: R1(Multi-provider Schema 호환), R6(이중 유지보수), R2(HWPX 신생 라이브러리).

---

## 부록 E — Phase 2~4 후속 에이전트 인계 문서

### E.1 database-architect 입력

1. **Scope**:
   - `tb_documents_v2` 신규 테이블 (DocumentSchema JSONB + 인덱스 전략)
   - `tb_documents_v2_templates` (Mode B 템플릿 저장)
   - `tb_report_templates` / `tb_generated_reports` → `tb_generated_reports_archive` 리네이밍 마이그레이션
   - `tb_agents.agent_type` CHECK 확장 (`freeform_doc` 추가)
2. **Deliverable**:
   - Alembic 006 migration (신규 테이블 + 인덱스 + 기존 데이터 COPY)
   - `documents_v2/models.py` ORM 모델
   - JSONB 쿼리 성능 테스트(페이지 수 20, 컴포넌트 10 기준 P95 < 100ms)
3. **제약**:
   - `DocumentSchema` Pydantic은 본 문서 §2와 부록 A를 **정답**으로 간주. 임의 필드 추가 금지.
   - JSONB 스키마 버저닝은 `schema_version` 컬럼으로 중복 관리.
4. **선행 조건**:
   - 본 문서 §2 스펙 lock (Phase 1 종료로 충족).

### E.2 frontend-specialist 입력

1. **Scope**:
   - 22개 React 컴포넌트 (`frontend/src/components/document-schema/components/`)
   - 6개 layout 래퍼
   - `designer` UX (프리뷰/편집/프롬프트/Export)
   - Mode A/B 라우팅 (`/designer/create`, `/designer/fill/[id]`)
   - Citations 공통 컴포넌트 승격
2. **Deliverable**:
   - S1: MVP 5종 + 프리뷰 패널 + 기본 Export 메뉴
   - S3/S4/S6: 나머지 컴포넌트 단계적
3. **제약**:
   - 디자인 토큰은 CSS 변수로만 주입. 컴포넌트 내 hex 하드코딩 금지.
   - 컴포넌트 Props TypeScript 타입은 Pydantic `model_json_schema()` + `openapi-typescript`로 자동 생성.
4. **UX 요구사항**:
   - 우측 프리뷰(iframe), 좌측 프롬프트/편집 사이드바, 상단 Export 메뉴 3분할.
   - Mode B에선 `locked=true` 영역에 자물쇠 아이콘 + 편집 방지.
5. **선행 조건**:
   - §2(Schema), §3(컴포넌트 카탈로그), §4.2(프론트 구조) lock.

### E.3 research-assistant 입력

1. **Scope**:
   - `python-hwpx`(airmang, MIT) 실제 API 탐색 및 컴포넌트 14종 구현 PoC
   - `hwp-extract`(Volexity, Apache 2.0) 표·이미지 추출 통합
   - LibreOffice + H2Orestart 사이드카 컨테이너 설계(S5 옵션 PDF 변환용)
2. **Deliverable**:
   - 기술 검증 보고 (한컴 2020/2022, Polaris, LibreOffice 호환성 매트릭스)
   - PoC 코드(컴포넌트 5종 최소, `SlideTitle/Heading/Paragraph/BulletList/DataTable`)
   - 빌더 인터페이스 초안 (`DocumentBuilder` ABC 준수)
3. **제약**:
   - pyhwp(AGPL) 절대 금지.
   - HWP 이진 생성은 범위 외.
4. **선행 조건**:
   - §2(Schema), §3.6(Export 매핑), §7(HWPX 어댑터) lock.

---

## 변경 이력

| 날짜 | 버전 | 내용 | 담당 |
|---|---|---|---|
| 2026-04-19 | v1.0 | 최초 작성 (Phase 1 기준선 확정) | enterprise-architect |
| 2026-04-19 | v1.6 | 후속 의사결정 10건 반영 (`phase1_decisions.md`): §2.4 Mode 전환 Phase 1 범위 외 (Q3), §2.8 `source_document_ids` ARRAY 유지 (Q2), §3.2 MVP 5→6종 (Q8), §4.2.2 `(admin)/template-designer/` 신설 (Q9), §4.3 PATCH Partial DocumentSchema 프로토콜 (Q10), §4.4 편집 저장 행 추가, §5.3 5-B 조직별 PPTX 템플릿 (Q4), §7.3 HWPX 지원 컴포넌트 구현 시점 분리 (Q6), §9.1 S1 DoD 6-컴포넌트·PATCH / S5 DoD 색상 주입 S6 이연 (Q7) / S6 DoD 확장 | enterprise-architect |

---

**(문서 끝)**
