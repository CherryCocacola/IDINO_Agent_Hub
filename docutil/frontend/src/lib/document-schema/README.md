# lib/document-schema

`DocumentSchema`를 클라이언트에서 조작하는 **훅·유틸·토큰 주입 로직**. 라우터/페이지 컴포넌트는 이 모듈의 훅만 import한다 — `apiClient`를 직접 호출하는 것은 금지(P4 데이터 흐름 원칙).

- `use-document.ts` — `useDocument`, `useDocumentMutation`, `useComponentRegeneration` 3종 훅 시그니처. 실제 구현은 Phase 4 S1.
- `design-tokens.ts` (Phase 4) — `DesignTokens` → CSS 변수 dict 변환(iframe 주입용).
- `schema-validators.ts` (Phase 4) — 클라이언트 가드(페이지 수 상한·컴포넌트 수 상한). 서버 Pydantic이 정답이며 여기서는 UX용 사전 차단만.

훅의 반환 타입은 `@/types/document-schema`에서만 import한다.
