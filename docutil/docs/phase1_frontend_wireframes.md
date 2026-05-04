# DocUtil — Phase 1 프론트엔드 와이어프레임 (v1.0)

> **작성일**: 2026-04-19
> **작성자**: frontend-specialist
> **상위 문서**: `docs/phase1_architecture.md` §4.2, 부록 E.2
> **상태**: Phase 1 UX 기준선. 실제 구현은 Phase 4 S1~S7.

---

## 1. 3분할 레이아웃 개요

`/designer/create`(Mode A), `/designer/fill/[templateId]`(Mode B), `/designer/[documentId]`(편집/프리뷰) 세 라우트는 모두 아래와 동일한 **`DocumentDesignerShell`** 을 사용한다. 화면은 1440px 기준 **3분할**이다.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ Top bar: 문서 제목 · Mode 표시 · 저장 상태 · 뒤로가기                          │
├──────────────────────┬─────────────────────────────────────┬───────────────────┤
│ 좌측 30% (432px)     │ 중앙 55% (792px)                    │ 우측 15% (216px)  │
│                      │                                     │                   │
│ [Tabs]               │  iframe 라이브 프리뷰                  │  Export  ▼        │
│  편집 | 프롬프트       │                                     │                   │
│ ─────                │  ┌─────────────────────┐             │ ─────             │
│  (선택된 탭 내용)     │  │                     │             │  디자인 토큰      │
│                      │  │  Page 1             │             │   primary ⬛       │
│                      │  │                     │             │   accent  ⬛       │
│                      │  └─────────────────────┘             │   font [▼]        │
│                      │  ┌─────────────────────┐             │   spacing [▼]     │
│                      │  │  Page 2             │             │   preset  [▼]     │
│                      │  │                     │             │                   │
│                      │  └─────────────────────┘             │ ─────             │
│                      │                                     │  메타·경고         │
│                      │  [ + 페이지 추가 ]                   │                   │
└──────────────────────┴─────────────────────────────────────┴───────────────────┘
```

### 1.1 영역별 책임

| 영역 | 비율 | 주 컴포넌트 | 책임 |
|---|---|---|---|
| **좌측(편집+프롬프트)** | 30% | `<EditSidebar>`, `<PromptBox>` | Tab으로 전환. 편집 모드에선 선택된 Page/Component 속성 form, 프롬프트 모드에선 자연어 지시 입력. |
| **중앙(프리뷰)** | 55% | `<PreviewPane>` (iframe) | DocumentSchema → React 렌더. 페이지 별로 수직 스크롤. 페이지/컴포넌트 클릭 시 좌측 편집 탭 활성화. |
| **우측(토큰+Export)** | 15% | `<ExportMenu>`, `<DesignTokenPicker>` | 상단 Export 드롭다운, 하단 디자인 토큰 7필드. |

### 1.2 3분할 선정 근거

1. **시선 흐름**: 대부분 사용자는 좌→중→우의 자연스러운 탐색 흐름을 쓴다(한국어도 LTR). 입력(프롬프트) → 결과 확인(프리뷰) → 출력(Export) 순서를 시각적으로 일치시킨다.
2. **프리뷰 우선**: 기존 `/reports`가 폼 위주라 "내가 지금 어떤 문서를 만드는지" 맥락이 약했다. 중앙을 55%로 크게 잡아 A4/16:9 프리뷰가 실제 비율대로 들어가게 한다(792px 폭이면 1280×720 슬라이드를 60% 스케일로 표시 가능).
3. **토큰 피커 경량화**: 토큰은 7필드 + 프리셋만이므로 우측 15%로 충분. Export 메뉴와 수직 적층해 우측 레일 하나로 묶는다.
4. **모바일 대응**: < 1024px에선 좌측만 노출하고 프리뷰는 하단 Drawer, 우측은 상단 햄버거 메뉴로 붕괴(Phase 4 S7 RWD 대응 예정).

### 1.3 대안 검토

| 대안 | 기각 사유 |
|---|---|
| 좌-우 2분할(프리뷰 없음) | 프리뷰 지연 및 의도와 불일치한 결과 확인 비용 증가 |
| 상-하 분할 (프롬프트 위, 프리뷰 아래) | 세로 스크롤로 프리뷰 컷오프 빈번. 한 번에 2슬라이드 비교 불가 |
| Notion식 단일 뷰 + 사이드패널 슬라이드 | 디자인 토큰/Export가 자주 접근되어 상시 노출이 필요 |

---

## 2. 컴포넌트 트리

```
<DocumentDesignerShell mode={"A"|"B"} documentId={uuid}>
  <TopBar>
    <BreadcrumbAndTitle />
    <SaveIndicator />
    <ModeBadge />
  </TopBar>
  <ThreeColumnLayout>
    <LeftPane>
      <Tabs defaultValue="edit">
        <TabsList>
          <TabsTrigger value="edit">편집</TabsTrigger>
          <TabsTrigger value="prompt">프롬프트</TabsTrigger>
        </TabsList>
        <TabsContent value="edit">
          <EditSidebar schema={...} selectedRef={...} />
        </TabsContent>
        <TabsContent value="prompt">
          <PromptBox mode={...} selectedRef={...} />
        </TabsContent>
      </Tabs>
    </LeftPane>

    <CenterPane>
      <PreviewPane schema={...} onElementClick={...} />
    </CenterPane>

    <RightPane>
      <ExportMenu documentId={...} degradedComponents={...} />
      <Separator />
      <DesignTokenPicker tokens={...} onChange={...} />
      <Separator />
      <MetadataPanel metadata={...} />
    </RightPane>
  </ThreeColumnLayout>
</DocumentDesignerShell>
```

---

## 3. UX 인터랙션 흐름 5가지

### 3.1 프롬프트 입력 → 문서 생성 (Mode A 최초 진입)

```
사용자 /designer/create 진입
  │
  ▼
[문서 타입 선택 모달] — 7종 중 1개 선택 (slide_report, minutes, ...)
  │
  ▼
Shell 렌더, 좌측 탭 = 프롬프트, 중앙 = 비어있는 프리뷰
  │
  ├─ (옵션) 기준 문서 선택 버튼 → <DocumentSelector> 모달
  │        └ 선택된 documentId들을 PromptBox state에 보관
  │
  ▼
사용자 프롬프트 작성 → Enter(또는 "생성" 버튼)
  │
  ▼
<PromptBox> → useDocumentMutation.generate({type, prompt, source_document_ids})
  │
  ▼
apiClient.post("/v2/documents", ...)  [5~15초 동기 대기]
  │         중앙 프리뷰 영역은 <Skeleton> 애니메이션 표시
  │         좌측 프롬프트 입력 disabled
  │
  ▼
응답 DocumentSchema 수신
  │
  ▼
router.push(`/designer/${schema.document_id}`)
  │
  ▼
새 라우트에서 useDocument가 schema 구독 → <PreviewPane>이 iframe 렌더
```

### 3.2 컴포넌트 클릭 → 편집 사이드바 활성화

```
iframe 내부 <KPI onSelect={…}> 클릭
  │
  ▼
iframe postMessage({ type: "element-select", page_id, component_id })
  │
  ▼
Shell 측 useEffect(window.onmessage) 리스너
  │
  ▼
selectedRef state 업데이트 → { page_id, component_id }
  │
  ├ 좌측 Tab을 "편집"으로 자동 전환
  │
  ▼
<EditSidebar>가 해당 컴포넌트 props form 렌더
  (KPI면 label/value/delta/delta_direction/description 5 필드)
  │
  ▼
사용자 form 편집 → onChange debounce 500ms
  │
  ▼
useDocumentMutation.updatePage({document_id, page_id, page: patchedPage})
  │
  ▼
서버 응답(새 schema) → useDocument 캐시 교체 → iframe 프리뷰 재렌더
  │
  (<PreviewPane>은 schema 변경 시 iframe contentWindow.postMessage로 부분 갱신,
   URL 리로드는 하지 않는다. Phase 4 S1에서 메시지 프로토콜 확정)
```

### 3.3 Mode B — `locked=true` 영역 시각적 구분

```
진입: /designer/fill/[templateId]
  │
  ▼
fillTemplate 호출 → schema.mode === "template_fill", 일부 page/component locked=true
  │
  ▼
<PreviewPane> iframe 내부 컴포넌트 렌더 시:
  locked=true → 컴포넌트 우상단에 <Lock /> 아이콘 배지
                + overlay `pointer-events-none` + 회색 dim 10%
                + cursor: not-allowed
  │
사용자 클릭 시도 → onClick 핸들러 no-op + toast "잠긴 영역은 편집할 수 없습니다"
  │
<EditSidebar>에서 해당 컴포넌트 선택 불가
  (선택되더라도 form 필드 전부 disabled + "템플릿 잠금" 안내 배너)
  │
프롬프트 입력 시 locked 컴포넌트는 재생성 대상에서 제외됨을 서버가 보장
  (regenerateComponent가 LockedRegionError 422 반환 → toast)
```

### 3.4 Export 드롭다운

```
우측 <ExportMenu> 버튼 클릭
  │
  ▼
<DropdownMenu>
  ├ PowerPoint (PPTX)
  ├ Word (DOCX)
  ├ 한글 HWPX        [Phase 4 S5까지 disabled, hint 툴팁]
  ├ PDF
  └ HTML
  │
사용자 항목 선택
  │
  ▼
useDocumentMutation.exportDocument({document_id, format})
  │
  ├ 서버에 job_id 요청
  ├ Toast "내보내기를 시작했어요" (Celery 대기)
  │
  ▼
pollExportJob (interval 1s, timeout 120s)
  │
  ├ completed → download_url 수신
  ├ MinIO presigned URL로 <a href download> 자동 클릭 또는 새 탭 오픈
  ├ degraded_components.length > 0 & format === "hwpx"
  │   → Toast(warning) "HWPX에서 간소화된 항목: {…}"
  │
  └ failed → Toast(error) + 재시도 버튼
```

### 3.5 부분 재생성 (컴포넌트 단위)

```
사용자 편집 사이드바에서 KPI 컴포넌트 선택 상태
  │
  ▼
프롬프트 탭으로 전환 → <PromptBox>에 "더 공격적인 목표로 수정해줘" 입력
  │
  ▼
<PromptBox>는 selectedRef가 있으면 "재생성" 모드로 전환
  ("전체 재생성" 대신 "선택한 컴포넌트만 재생성" 버튼 표시)
  │
  ▼
useComponentRegeneration.regenerateComponent({
  document_id, page_id, component_id, instruction
})
  │
  ▼
낙관적 업데이트: 해당 컴포넌트를 "생성 중..." placeholder로 일시 교체
  │
  ▼
apiClient.post("/v2/documents/{id}/regenerate-component") — 1~3초 예상
  │
  ├ 성공: 응답 Component 1개를 schema에 patch → iframe 부분 갱신
  │       (prop change만으로 재렌더, iframe 리로드 없음)
  │
  └ 실패: 원본 복원 + Toast 에러
      (Mode B에서 locked 컴포넌트 지시 시 422 — LockedRegionError)
```

---

## 4. 디자인 토큰 인터랙션

`<DesignTokenPicker>`는 7필드를 보여주지만 **실제 저장은 debounce 500ms** 후에만 수행한다. 색상 변경 즉시 iframe에 반영되는 이유:

1. 변경 이벤트 → React state 업데이트
2. iframe `<html>`의 `style` 속성을 postMessage로 갱신 (`--doc-primary: #xxx`)
3. Tailwind/컴포넌트 재렌더 없이 CSS 변수만 바뀌므로 성능 비용 거의 없음
4. debounce 완료 시점에 서버 PATCH

`brand_preset=idino_*`일 때는 색상 필드 3개(primary/accent/text)를 readOnly로 잠그고, 상단에 "IDINO 브랜드 프리셋 사용 중입니다. 색상은 자동 적용됩니다." 안내를 띄운다.

---

## 5. 키보드·접근성 요구사항

- `Tab` 순서: TopBar → LeftPane → CenterPane(iframe 포커스 → 페이지 단위 이동) → RightPane.
- 프롬프트 박스: Enter 제출, Shift+Enter 줄바꿈.
- Export 메뉴: 방향키로 항목 이동, Enter로 선택, Escape로 닫기 (shadcn dropdown 기본 동작).
- iframe 내부: 페이지별 `<section role="group" aria-label="슬라이드 N">`. 컴포넌트 클릭은 `<button>` 또는 `role="button" tabIndex={0}`.
- `locked=true` 컴포넌트는 `aria-disabled="true"` + 스크린리더 텍스트 "잠긴 영역".
- 색상 대비: 모든 `--doc-*` 기본값은 WCAG AA 4.5:1 이상.

---

## 6. 반응형 전환점

| 너비 | 동작 |
|---|---|
| ≥ 1440px | 3분할 그대로 (30 / 55 / 15) |
| 1280~1440px | 3분할 유지 비율 (28 / 56 / 16) |
| 1024~1279px | 3분할 (24 / 58 / 18), 우측 토큰 피커는 아이콘만 노출 + 클릭 시 팝오버 |
| 768~1023px | 2분할 (35 / 65), 우측 패널은 상단 툴바로 붕괴(Export 버튼만, 토큰 피커는 모달) |
| < 768px | 1분할(프리뷰만). 편집은 하단 Drawer, 프롬프트는 상단 고정 Bar |

Phase 4 S7에서 RWD 완성. S1 시점에는 ≥ 1280px만 지원.

---

**(문서 끝)**
