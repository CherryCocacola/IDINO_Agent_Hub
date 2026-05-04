# document-schema

`DocumentSchema`(Pydantic v2 discriminated union 22종 컴포넌트 + 6종 layout)를 React 트리로 변환하는 **스키마 렌더 레이어**. document-designer 패널들이 아닌 iframe 프리뷰와 PDF용 서버 렌더(향후 Playwright), 공유 링크 등 **여러 소비자가 동일한 시각 결과**를 얻도록 단일 진실의 원천을 제공한다.

- `components/` — 22개 컴포넌트 (SlideTitle, KPI, DataTable …). MVP 5종(S1)만 placeholder 스켈레톤 완료. 나머지 17종은 타입만 정의.
- `layouts/` — 6개 layout(`title_slide`, `section_divider`, `content_body`, `kpi_dashboard`, `two_column`, `closing`) 래퍼. Page의 `layout` enum을 보고 어떤 배치 슬롯으로 컴포넌트를 흘릴지 결정.
- `renderer/` — `<DocumentRenderer schema>`와 `<PageRenderer>`, `<ComponentSwitch>` 3단 계층.

컴포넌트는 hex 색상을 하드코딩하지 않고 반드시 `var(--doc-*)` CSS 변수만 참조한다.
