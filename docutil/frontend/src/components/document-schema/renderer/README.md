# document-schema/renderer

`DocumentSchema` → React 트리 변환의 **최상위 진입점**. 3단 계층:

1. `DocumentRenderer` — schema 전체 + `design_tokens` 주입(CSS 변수 스타일).
2. `PageRenderer` — Page 1개 + layout enum → `layouts/`의 적절한 래퍼 선택.
3. `ComponentSwitch` — Component discriminated union의 `type` 필드를 보고 22개 React 컴포넌트 중 하나를 렌더.

**원칙**
- 분기는 `type` 필드 map 디스패치로. switch-case 대신 `{ [k]: Component }` 레지스트리.
- schema → React는 **순수 함수**. 사이드 이펙트 금지(데이터 페칭·상태 조작은 훅에서만).
- 알 수 없는 `type`은 Phase 0 graceful degradation 원칙에 따라 `<UnsupportedComponent>` 플레이스홀더로 대체 + 콘솔 경고.

Phase 4 S1에서 `DocumentRenderer` + `PageRenderer` + `ComponentSwitch` 모두 구현.
