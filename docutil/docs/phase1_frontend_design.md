# DocUtil — Phase 1 프론트엔드 설계 기준선 (v1.0)

> **작성일**: 2026-04-19
> **작성자**: frontend-specialist
> **상위 문서**: `docs/phase1_architecture.md` (enterprise-architect, 2026-04-19)
> **동반 문서**: `docs/phase1_frontend_wireframes.md` (UX 와이어프레임)
> **상태**: Phase 1 설계 기준선 확정. 실제 React 구현은 Phase 4 S1에서 착수한다.

---

## 0. Executive Summary

Phase 1은 **실제 React 렌더를 작성하지 않는다**. 본 에이전트의 산출은 (1) 폴더 구조, (2) TypeScript 타입 초안, (3) MVP 5종 컴포넌트 스켈레톤, (4) 3분할 UX 와이어프레임, (5) 핵심 훅·API 클라이언트 시그니처, (6) 디자인 토큰 CSS 변수 시스템, (7) 기존 UI 폐기·이관 계획이다.

핵심 결정 세 가지:

1. **`--doc-*` 네임스페이스 분리**: 기존 애플리케이션 셸의 토큰(`--color-*`, `globals.css`)과 DocumentSchema 프리뷰의 토큰(`--doc-*`, `styles/document-tokens.css`)을 분리했다. 프리뷰는 iframe 내부에서 다른 조직의 브랜드 색(예: custom 프리셋)을 허용해야 하므로 셸 토큰과 같은 이름을 쓰면 오염된다.
2. **편집 사이드바와 프롬프트 박스의 Tab 공유**: 좌측 30% 영역을 두 개로 쪼개지 않고 상단 Tab(편집 / 프롬프트)으로 전환시킨다. 사용자는 한 번에 한 가지 의도(속성 수정 vs 자연어 지시)만 갖기 때문에 동시 노출이 오히려 산만함을 유발한다.
3. **iframe 프리뷰 고수**: 중앙 프리뷰는 iframe 격리로 유지한다. 앱 셸의 Tailwind/shadcn 토큰이 DocumentSchema의 `--doc-*`를 덮지 못하게 하는 가장 확실한 경계선이다. Phase 4 S1에서 postMessage 프로토콜(element-select, token-update, schema-patch)을 확정한다.

MVP 5종(SlideTitle, Heading, Paragraph, BulletList, KPI + 요구 범위에 포함된 DataTable까지 6종 스켈레톤)은 Phase 4 S1의 첫 스프린트에서 렌더를 완성하고, 나머지 17종은 S2~S6에 단계적으로 추가된다.

---

## 1. 폴더 구조 확정

```
frontend/src/
├── app/
│   └── (user)/
│       ├── designer/                            ★ 신규 라우트
│       │   ├── README.md
│       │   ├── create/
│       │   │   └── page.tsx                     Mode A 진입 placeholder
│       │   └── fill/
│       │       └── [templateId]/
│       │           └── page.tsx                 Mode B 진입 placeholder
│       ├── reports/                             (유지, S7에서 designer로 리다이렉트)
│       └── ...
├── components/
│   ├── document-designer/                       ★ Mode A/B 공통 shell
│   │   ├── README.md
│   │   ├── preview-pane/README.md
│   │   ├── edit-sidebar/README.md
│   │   ├── prompt-box/README.md
│   │   ├── export-menu/README.md
│   │   └── design-token-picker/README.md
│   ├── document-schema/                         ★ Schema → React 변환
│   │   ├── README.md
│   │   ├── components/
│   │   │   ├── README.md
│   │   │   ├── SlideTitle.tsx                   MVP 스켈레톤
│   │   │   ├── Heading.tsx                      MVP 스켈레톤
│   │   │   ├── Paragraph.tsx                    MVP 스켈레톤
│   │   │   ├── BulletList.tsx                   MVP 스켈레톤
│   │   │   ├── KPI.tsx                          MVP 스켈레톤
│   │   │   └── DataTable.tsx                    MVP 스켈레톤 (요구 #3 포함)
│   │   ├── layouts/README.md
│   │   └── renderer/README.md
│   └── citations/                               ★ 공통 Citations 승격 예정지
│       └── README.md
├── lib/
│   ├── api/
│   │   ├── client.ts                            (기존)
│   │   └── documents-v2.ts                      ★ 신규 API 클라이언트 시그니처
│   └── document-schema/                         ★ 훅/유틸
│       ├── README.md
│       └── use-document.ts                      3종 훅 시그니처
├── styles/
│   └── document-tokens.css                      ★ --doc-* CSS 변수 스펙
└── types/
    └── document-schema.ts                       ★ 수동 draft (22컴포넌트 + Page + Document)
```

### 1.1 폴더 구조 핵심 결정 3가지

**결정 1 — `document-designer`와 `document-schema` 분리**: 셸 UI(패널/메뉴)와 스키마 렌더를 다른 디렉토리로 두었다. 이유는 (a) `document-schema`는 iframe 내부에서도 실행되는 **순수 렌더 레이어**여야 하고, (b) PDF export나 공유 링크 등 **여러 소비자가 동일한 Schema → 동일한 시각 결과**를 받아야 하므로, 셸과 섞이면 재사용이 불가능해진다. `phase1_architecture.md` §4.2.1에서도 이 두 폴더를 별도 트리로 제시했다.

**결정 2 — `components/document-designer/*` 아래에 **서브디렉토리 per 패널****: 요구 과제에서 지정된 5개 패널(preview-pane, edit-sidebar, prompt-box, export-menu, design-token-picker) 각각을 **디렉토리 단위**로 배치했다. 단일 `.tsx`가 아닌 디렉토리인 이유는 각 패널이 (1) 진입점 컴포넌트 + (2) 내부 훅/유틸 + (3) 서브 컴포넌트로 성장할 것이기 때문. 예를 들어 `edit-sidebar/`는 Phase 4 S1에서 `EditSidebar.tsx` 진입점 외에 `forms/KPIForm.tsx`, `forms/DataTableForm.tsx` 등 22개 폼이 추가된다.

**결정 3 — `lib/document-schema/`와 `types/document-schema.ts` 분리**: 타입은 `types/`에 두고 훅/유틸은 `lib/document-schema/`에 두었다. Phase 4 S1에서 타입이 `document-schema.generated.ts`로 **자동 생성**되면 diff가 타입 파일에만 집중돼 PR 리뷰 비용이 줄어든다. 훅은 수작업 코드이므로 자동 생성과 섞이면 안 된다.

---

## 2. 22개 컴포넌트 TypeScript 타입

`frontend/src/types/document-schema.ts` 수동 draft를 완성했다. 핵심:

- Pydantic v2 `Field(discriminator="type")` 패턴을 정확히 1:1 재현하는 **discriminated union** (`Component` 타입).
- 22개 컴포넌트 + `ComponentBase`(id, locked, anchor) + 6종 layout enum(`LayoutId`) + `DesignTokens`(7필드) + `Page`(id, page_kind, layout, locked, components, speaker_notes, page_number_visible) + `DocumentMetadata`(created_at, updated_at, llm 정보, citations, degraded_components) + 루트 `DocumentSchema`(document_id, schema_version="1.0", type, mode, template_id, design_tokens, pages, metadata).
- DocumentType enum 7종(`slide_report` / `docx_report` / `proposal` / `minutes` / `one_pager` / `weekly_status` / `freeform_doc`).
- ExportFormat 5종(`pptx` / `docx` / `hwpx` / `pdf` / `html`) — HWP는 제외(techspec §7.3.1).
- `isComponentOfType<T>` 헬퍼를 둬 `ComponentSwitch` 레지스트리에서 type predicate로 사용 가능.

**props 세부는 `phase1_architecture.md` 부록 B의 19개 표 + §3.3의 상세 3개를 그대로 옮겼다.** 임의 필드 추가·제거 없음.

**자동 생성 경로**: Phase 4 S1 DoD에 `backend/app/modules/documents_v2/schemas.py` 작성과 동시에 `openapi-typescript`로 `types/document-schema.generated.ts`를 생성하고 본 수동 draft는 제거한다. 전환 시점까지는 이 수동 파일이 유일한 정답이다.

---

## 3. MVP 5종 + DataTable = 6개 컴포넌트 스켈레톤

| 컴포넌트 | 파일 | 상태 |
|---|---|---|
| SlideTitle | `components/document-schema/components/SlideTitle.tsx` | 시그니처 완료, placeholder div |
| Heading | `.../Heading.tsx` | 시그니처 완료 |
| Paragraph | `.../Paragraph.tsx` | 시그니처 완료 |
| BulletList | `.../BulletList.tsx` | 시그니처 완료 |
| KPI | `.../KPI.tsx` | 시그니처 완료 |
| DataTable | `.../DataTable.tsx` | 시그니처 완료 |

각 파일의 공통 규약:

- Props는 `{ component: XxxComponent; isSelected?: boolean; onSelect?: (id) => void }` 형태로 통일. `ComponentSwitch`가 모든 컴포넌트를 동일 시그니처로 취급할 수 있게 한다.
- `data-component`, `data-component-id`, `data-locked`, `data-selected` 속성을 스켈레톤에 이미 심어두어, Phase 4 S1에서 E2E 테스트(Playwright)의 셀렉터로 활용 가능.
- `onClick={() => onSelect?.(component.id)}` 만 구현되어 있고 실제 렌더 로직(태그 종류, 스타일)은 `// TODO(Phase 4 S1)` 한글 주석으로 명시했다.
- hex 색상 하드코딩 없음. `// TODO`에서 참조할 CSS 변수를 구체적으로 기술("var(--doc-primary)", "var(--doc-text-muted)" 등)해 구현 시 혼선을 줄였다.

**DataTable은 MVP 5종에 추가로 포함**했다. 요구 과제 #3에 명시된 5종(SlideTitle/Paragraph/BulletList/KPI/DataTable)과 `phase1_architecture.md` §3.2의 MVP 5종(SlideTitle/Heading/Paragraph/BulletList/KPI)이 일치하지 않아, **합집합 6개** 모두 스켈레톤을 작성했다. 이렇게 하면 S1 DoD의 "5-컴포넌트 문서 생성" 요구와 S2 DoD의 "DataTable 도입"을 양쪽 모두 커버할 수 있다. 이 차이는 미해결 질문 §7에 기록.

---

## 4. UX 와이어프레임 (요약)

3분할 레이아웃:

- **좌측 30%** — 상단 Tabs (편집 | 프롬프트). 편집은 선택된 Page/Component의 form, 프롬프트는 자연어 입력.
- **중앙 55%** — iframe 라이브 프리뷰. 페이지 수직 스크롤.
- **우측 15%** — 상단 Export 드롭다운, 하단 디자인 토큰 피커(7필드).

전체 다이어그램과 컴포넌트 트리, 반응형 전환점은 `docs/phase1_frontend_wireframes.md` 참조.

### 4.1 인터랙션 5가지 (요약)

1. **프롬프트 → 생성**: 타입 선택 → 프롬프트 입력 → `generateDocument` → 5~15초 대기 → `/designer/[id]` 이동.
2. **컴포넌트 클릭 → 편집**: iframe postMessage → selectedRef 업데이트 → 좌측 편집 탭 자동 활성 → form 편집 → debounce 500ms → `updatePage`.
3. **Mode B locked 시각 구분**: `locked=true` 컴포넌트에 Lock 아이콘 + overlay dim + `aria-disabled`, 편집 시도 시 toast.
4. **Export**: 드롭다운 선택 → `exportDocument` → job_id 폴링 → presigned URL 다운로드. HWPX degraded 경고 배지.
5. **부분 재생성**: 컴포넌트 선택 상태에서 프롬프트 입력 → "재생성" 모드 → `regenerateComponent` → iframe 부분 갱신.

상세 플로우는 와이어프레임 문서 §3 참조.

### 4.2 3분할 이유 (핵심 요약)

1. **시선 흐름**: 한국어 LTR + 입력(좌) → 결과(중) → 출력(우) 자연스러움.
2. **프리뷰 크기**: 중앙 55%(1440px 기준 792px)면 슬라이드 16:9(1280×720)를 60% 스케일로 실제 비율대로 표시 가능.
3. **모바일 대응**: 1023px 이하에서 단계적으로 붕괴. Phase 4 S7에서 완성.

상세 대안 비교는 와이어프레임 문서 §1.3.

---

## 5. 핵심 훅 및 API 클라이언트 스켈레톤

### 5.1 `lib/document-schema/use-document.ts`

3종 훅 시그니처 확정:

- **`useDocument(documentId)`** — 지정 문서의 DocumentSchema 구독 (SWR/React Query 캐시).
- **`useDocumentMutation()`** — `generate`, `fillTemplate`, `updatePage`, `deleteDocument`, `exportDocument` 5개 mutate 함수 번들.
- **`useComponentRegeneration()`** — `regenerateComponent`, `regeneratePage` 2개. Mode B locked 지정 시 서버가 `LockedRegionError`(422) 반환.

모든 함수는 Phase 1에서는 `throw new Error("Phase 4 S1에서 구현 예정")`으로 되어 있고, TODO 주석에 SWR 캐시 키(`["document", documentId]`)와 실제 호출 체인을 기술했다.

### 5.2 `lib/api/documents-v2.ts`

8개 함수 시그니처:

- `generateDocument`, `fillTemplate`, `fetchDocument`, `updatePage`, `regenerateComponent`, `regeneratePage`, `deleteDocument`, `exportDocument` + 내부 `pollExportJob`.
- 모두 `apiClient`를 경유 (직접 `fetch` 금지, anti-patterns.md 준수).
- 경로 상수 `DOCUMENTS_V2_BASE = "/v2/documents"`. prefix `/api/v1`은 apiClient가 자동 부여.
- `EXPORT_FORMATS` 상수 배열: 메뉴 렌더용. HWPX는 Phase 4 S5까지 `disabled: true` + hint.

---

## 6. 디자인 토큰 CSS 변수 시스템

`frontend/src/styles/document-tokens.css` — **`--doc-*` 네임스페이스** 전용 CSS 변수.

### 6.1 변수 카테고리

| 카테고리 | 변수 예 | 설명 |
|---|---|---|
| 색상 | `--doc-primary`, `--doc-accent`, `--doc-text`, `--doc-background`, `--doc-surface`, `--doc-border` | DesignTokens 4색 + 보조 |
| 상태/의미 | `--doc-info`, `--doc-warning`, `--doc-success`, `--doc-danger` | Callout variant 대응 |
| 차트 | `--doc-chart-1` ~ `--doc-chart-5` | Chart 기본 팔레트 |
| 타이포 | `--doc-font-family`, `--doc-font-size-*`, `--doc-line-height-*` | spacing enum + 폰트 |
| 간격 | `--doc-spacing-xs/sm/md/lg/xl/2xl`, `--doc-page-padding` | spacing enum(compact/normal/relaxed)에 따라 data-attribute 선택자로 전환 |
| 라디우스 | `--doc-radius-sm/md/lg/xl` | KPI 카드·DataTable 공통 |
| 그림자 | `--doc-shadow-sm/md/lg` | 카드 레이어 |
| 페이지 치수 | `--doc-page-aspect-slide`, `--doc-page-width-slide`, `--doc-page-width-section-a4` | iframe 내부 페이지 박스 |

### 6.2 런타임 변경 구조

`<DesignTokenPicker>`에서 값이 바뀌면:

1. React state 업데이트 → `<PreviewPane>`로 전달
2. iframe `contentWindow.postMessage({ type: "token-update", tokens })` 호출
3. iframe 측 리스너가 `document.documentElement.style.setProperty('--doc-primary', hex)` 수행
4. CSS 변수 변경 → 영향받는 요소 자동 repaint (React 재렌더 불필요)
5. debounce 500ms 후 서버 PATCH

**`brand_preset=idino_*`일 때**: `document-preview-root[data-brand-preset="idino_mono"]` 선택자로 자동 팔레트 변형. 색상 필드는 picker에서 readOnly.

### 6.3 Tailwind와의 관계

Tailwind v4(`@theme inline`)는 앱 셸용이다. Designer Shell의 `bg-background`, `text-foreground`는 그대로 Tailwind를 쓴다. 하지만 `document-schema/components/*`의 렌더 내부는 **Tailwind 유틸은 레이아웃(flex, gap-*)에만** 쓰고 **색상/타이포는 `var(--doc-*)`**만 참조한다. 이렇게 하면 같은 컴포넌트를 iframe 밖(예: 공유 PDF 서버 렌더)에서도 동일하게 재사용 가능.

---

## 7. 기존 UI 폐기·이관 계획

### 7.1 `/reports` (사용자 보고서 페이지)

- **Phase 4 S2 완료 시**: `/reports`에 `Mode A designer로 이동할까요?` 안내 배너 추가, 기존 CRUD는 유지.
- **Phase 4 S4 완료 시**: `/reports`의 신규 생성 버튼을 `/designer/create`로 라우팅.
- **Phase 4 S7**: `/reports/*` 모든 경로를 `/designer/*`로 301 리다이렉트, 페이지 파일 삭제.

### 7.2 `/templates` (관리자 템플릿 관리)

- **Phase 4 S4까지**: 현 페이지 유지. 기존 Jinja2 템플릿 CRUD 그대로.
- **Phase 4 S4**: DocumentSchema 기반 템플릿 에디터 신규 탭 추가("Schema 기반 템플릿" vs "Jinja2 템플릿"). 기존 16개 Jinja2 템플릿 중 5개를 수동으로 Schema로 변환(샘플링).
- **Phase 4 S7**: Jinja2 탭 read-only 후 제거. `/templates`는 Schema 에디터만 남김.

### 7.3 검색 페이지의 "Jinja2 변수 입력"

`frontend/src/app/(user)/search/` 내 Jinja2 변수 채우기 폼 → designer로 흡수. **Phase 4 S4**에서 검색 → "이 결과로 문서 만들기" 버튼 → `/designer/create?prefill=...`로 이동하는 딥링크로 대체.

### 7.4 `components/chat/` 내 Citations UI

- **Phase 4 S6**: `components/citations/`로 승격(현재 디렉토리 + README만 준비됨). 챗봇과 designer 양쪽이 동일 컴포넌트 사용.

### 7.5 `components/templates/variable-mapping-editor.tsx`

- **Phase 4 S4**: dialog/inline 이중 모드 제거, `edit-sidebar/forms/*`로 재설계 통합.
- **Phase 4 S7**: 파일 삭제.

### 7.6 이관 리스크

- **리스크 A** — `/reports` 사용자 학습 곡선: 기존 보고서 생성 플로우에 익숙한 사용자가 Mode A/B 분기에 혼란. 대응: `/designer/create` 진입 시 2-카드 온보딩(자유 생성 / 양식 시작) + Tour.
- **리스크 B** — Jinja2 템플릿 자동 변환 실패: 16개 중 일부는 복잡한 중첩 반복문으로 Schema 변환 불가. 대응: S4에서 수동 재작성 5개 우선, 자동 변환 실패 템플릿은 `rendering_mode=jinja2` read-only로 1년간 유지 후 폐기.
- **리스크 C** — 검색 페이지 Jinja2 UX 이관 지연: `/search`는 사용 빈도가 매우 높아 급격한 변경 시 업무 차질. 대응: S4에서 기존 Jinja2 경로와 병행, S7에서 제거.
- **리스크 D** — Citations 컴포넌트 승격 타이밍: Chat에서 이미 구현된 Citations를 S6에서 이관하면 챗봇 회귀 리스크. 대응: S6 초반 2일은 두 경로 병존(동일 구현 mirror), 검증 후 swap.

---

## 8. 미해결 질문

**Q1. MVP 5종 컴포넌트 정의 불일치 (enterprise-architect에 확인 요망)**
- `phase1_architecture.md` §3.2의 MVP 5종: SlideTitle, **Heading**, Paragraph, BulletList, KPI
- 본 에이전트 입력 과제 #3의 MVP 5종: SlideTitle, Paragraph, BulletList, KPI, **DataTable**
- 현재 합집합 6개 모두 스켈레톤 작성으로 대응했으나, S1 DoD의 "5-컴포넌트 end-to-end 문서"가 어느 5종을 의미하는지 확정 필요.

**Q2. 라우트 그룹 — `/designer`의 소속 (user) (enterprise-architect)**
- `phase1_architecture.md` §4.2.1은 `app/(user)/designer/`로 배치. 관리자도 템플릿 편집 시 같은 Shell을 쓸 텐데, `(user)` 그룹에만 두면 admin 라우트에서 재사용 문제가 생긴다.
- Phase 4 S4에서 admin 전용 템플릿 편집 경로가 필요해지면 `(admin)/template-designer/`로 별도 라우트를 두거나 Shell을 layout 없이 공용 경로로 승격하는 선택지 중 어느 것으로 갈지?

**Q3. iframe postMessage 프로토콜 (enterprise-architect / backend-specialist 공동)**
- 프리뷰 iframe ↔ shell 간 메시지 스키마(`element-select`, `token-update`, `schema-patch` 등)는 Phase 4 S1에서 확정해야 하며, 그 전에 backend가 제공하는 schema patch 단위(전체 교체 vs JSON patch)가 결정되어야 함.
- 현재 `use-document.ts`는 "전체 schema 교체" 가정이지만, 편집 사이드바 debounce 500ms 저장 시 네트워크 페이로드가 크다. S1에서 `PATCH /v2/documents/{id}` JSON Patch 지원 여부 결정 필요.

**Q4. SWR vs React Query (내부 결정 허용)**
- 훅 시그니처는 두 라이브러리 어느 쪽으로도 구현 가능. 기존 코드베이스에 둘 다 쓰이지 않고 있어 Phase 4 S1 착수 시점에 frontend-specialist가 선정 가능. database-architect/enterprise-architect 개입 불필요.

---

## 9. Phase 1 완료 기준 자체 검증

- [x] 폴더 구조(디렉토리 + README 10개) 생성
- [x] MVP 6개 컴포넌트 placeholder 스켈레톤 (요구 과제 5종 + 아키텍처 MVP 5종 합집합)
- [x] 22개 컴포넌트 + 6 layout + DesignTokens + Page + Metadata + DocumentSchema 타입 (수동 draft)
- [x] 핵심 훅 3종 시그니처 (useDocument, useDocumentMutation, useComponentRegeneration)
- [x] `lib/api/documents-v2.ts` 8개 함수 시그니처 + EXPORT_FORMATS 상수
- [x] `styles/document-tokens.css` `--doc-*` 변수 스펙
- [x] 3분할 UX 와이어프레임 + 5개 인터랙션 흐름 (wireframes.md)
- [x] `/designer/create`, `/designer/fill/[templateId]` 라우트 placeholder 2개
- [x] 기존 UI(`/reports`, `/templates`, Jinja2 변수 입력, Citations) 이관 계획
- [x] hex 하드코딩 0건 (컴포넌트 스켈레톤은 placeholder + TODO로만 기술)
- [x] apiClient 우회 0건 (모든 fetch는 apiClient 경유 주석)
- [x] anti-patterns.md · architecture.md 준수
- [x] 본 설계 문서 1500~2500 단어 범위 (현재 ~2100단어)

---

## 10. 변경 이력

| 날짜 | 버전 | 변경 |
|---|---|---|
| 2026-04-19 | v1.0 | 최초 작성 (frontend-specialist) |
| 2026-04-19 | v1.1 | `phase1_decisions.md` 반영 필요 (Q8~Q10 해소). 본문 변경은 Phase 2 병합 시. 주요 영향: §3 MVP 6종 확정 (Q8, `SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable`), §1 폴더 구조에 `(admin)/template-designer/` 신규 라우트 + Shell 재사용 원칙 추가 (Q9), §5.1 TODO(JSON Patch 미결정) 해소 → `PATCH /v2/documents/{id}` Partial DocumentSchema 확정 (Q10, RFC 6902 미도입), §7.2 `/templates`는 목록 페이지로 역할 축소. |

---

**(문서 끝)**
