# preview-pane

Designer Shell 중앙 55% 영역에 배치되는 **iframe 라이브 프리뷰** 패널. DocumentSchema를 iframe 내부에서 렌더하고, 부모 shell과 `postMessage`로 양방향 통신한다.

## 파일 구성

| 파일                                     | 역할                                                                                                                                                                           |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `index.tsx`                              | 외부에 노출되는 `<PreviewPane>`. 부모에서 import. ref 핸들로 `sendTokenUpdate`, `sendSchemaPatch` 를 노출.                                                                     |
| `PreviewFrame.tsx`                       | `<iframe>` 컨테이너. sandbox 속성과 contentWindow 접근자를 캡슐화.                                                                                                             |
| `preview-host.tsx`                       | iframe **내부**에서 실행되는 호스트 컴포넌트. Schema를 받아 D1~D2 완료 6종(SlideTitle/Heading/Paragraph/BulletList/KPI/DataTable)을 렌더하고, 그 외 16종은 placeholder로 표시. |
| `postmessage-protocol.ts`                | 프로토콜 타입·팩토리·가드·헬퍼. 런타임 의존성이 없어 host/parent 양쪽에서 재사용 가능.                                                                                         |
| `__tests__/postmessage-protocol.test.ts` | vitest 단위 테스트 (21건).                                                                                                                                                     |

## iframe 격리 방식

**결정**: `sandbox="allow-scripts allow-same-origin"` + Next.js same-origin 라우트(`/preview-host`).

- `srcdoc` 인라인 부트스트랩은 22종 React 컴포넌트를 수동 DOM 빌더로 다시 써야 해서 비용 과대 → 기각.
- `allow-same-origin` 없이 `allow-scripts` 만 쓰면 세션 쿠키/localStorage/presigned URL 요청이 막혀 프리뷰 데이터 조회가 불가 → 기각.
- same-origin 이지만 **postMessage origin 검증**을 strict 로 수행(`window.location.origin` 과 엄격 비교)해 XSS / 타 도메인 주입을 방어한다.
- `/preview-host` Next.js 라우트 파일(`app/preview-host/page.tsx`)은 D3 범위 밖이며 D4 작업에서 추가된다. 본 D3 파일들은 라우트가 import 할 "완성된 호스트"를 선제공한다.

## postMessage 프로토콜 3종

모두 `{ type: "docutil/<event>", schemaVersion: 1, payload: {...} }` 형태. `docutil/` 네임스페이스와 `schemaVersion` 일치가 아니면 수신 측에서 silent drop.

| 이름                         | 방향            | Payload                                                                                               |
| ---------------------------- | --------------- | ----------------------------------------------------------------------------------------------------- |
| `docutil/element-select`     | iframe → parent | `{ pageId, componentId }` — 컴포넌트 클릭 시                                                          |
| `docutil/token-update`       | parent → iframe | `{ tokens: Partial<DesignTokens> }` — 부분 병합 후 CSS 변수 override                                  |
| `docutil/schema-patch-local` | parent → iframe | `{ patchType: 'page'\|'component'\|'tokens', pageId?, componentId?, data }` — 서버 PATCH 와 동일 구조 |

`schema-patch-local` 은 서버 PATCH `/v2/documents/{id}` 의 request body 와 1:1 매칭되어, 동일 payload를 네트워크 호출 전 로컬 프리뷰 갱신 용도로 재사용한다 (`phase1_decisions.md` v1.2 Q10 의 Partial DocumentSchema 결정 반영).

## 사용 예

```tsx
// 부모 shell
const paneRef = useRef<PreviewPaneHandle>(null);

<PreviewPane
  ref={paneRef}
  onElementSelect={({ pageId, componentId }) => {
    // 좌측 edit-sidebar 활성화
  }}
/>;

// 토큰 피커가 값 변경 시
paneRef.current?.sendTokenUpdate({ primary_color: "#123456" });

// 컴포넌트 인라인 편집 저장 시
paneRef.current?.sendSchemaPatch({
  patchType: "component",
  pageId: "p1",
  componentId: "c3",
  data: { text: "새 본문" },
});
```

## 제약

- hex 색상 하드코딩 금지. iframe 내부는 `var(--doc-*)` 만 사용.
- `apiClient` / `fetch()` 직접 호출 금지. 본 디렉토리는 서버 호출을 하지 않는다.
- `edit-sidebar/`, `design-token-picker/` 의 기능 구현은 D4/D5 범위이며, 본 D3 는 프로토콜 골격만 제공한다.
- `<ComponentSwitch>` 22종 레지스트리는 D4+ 에서 본격 구축되며, 현재 host는 type 분기 6종 + placeholder 만 지원한다.

## 후속 작업

| 작업                                               | 담당   | 스프린트 |
| -------------------------------------------------- | ------ | -------- |
| `/preview-host` Next.js 라우트                     | FE     | S1 D4    |
| edit-sidebar 활성화 연결                           | FE     | S1 D4    |
| design-token-picker 슬라이더 + 서버 PATCH debounce | FE     | S1 D5    |
| `ComponentSwitch` 22종 레지스트리화                | FE     | S2~S6    |
| CSP 헤더 (frame-ancestors / script-src)            | DevOps | S7       |
