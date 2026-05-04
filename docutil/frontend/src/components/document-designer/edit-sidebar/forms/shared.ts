/**
 * shared.ts — edit-sidebar/forms/ 내부에서만 쓰는 공통 타입/스타일 상수
 *
 * Phase 4 S1 D4 산출물. 폼 6종이 반복 사용하는 Props 시그니처와 사이드바 컨테이너
 * 스타일을 이곳에 모아 DRY 하게 유지한다.
 */

import type { Component } from "@/types/document-schema";

/**
 * 모든 폼 컴포넌트가 공유하는 Props 시그니처.
 *
 * - `onLocalPatch` : 즉시 iframe 프리뷰에 반영될 낙관적 patch. 호출자 책임은
 *   `PreviewPaneHandle.sendSchemaPatch({ patchType: "component", ... })` 로
 *   wiring (edit-sidebar 컨테이너에서 수행).
 * - `onCommitPatch`: 서버 PATCH 에 사용될 patch. 기본적으로 `useFormPatch.commit`
 *   에 연결되어 500ms debounce 후 flush.
 *
 * 두 patch 의 타입은 의도적으로 동일(Partial<C>)하게 유지한다. D3 확정 결정
 * (`docs/phase1_decisions.md` v1.2 Q10)에 따라 낙관적 UI / 서버 PATCH body 가
 * 같은 구조를 공유하기 때문이다.
 */
export interface FormProps<C extends Component> {
  component: C;
  pageId: string;
  onLocalPatch: (patch: Partial<C>) => void;
  onCommitPatch: (patch: Partial<C>) => void;
}

/**
 * 사이드바 내부 폼의 기본 컨테이너 클래스.
 * Tailwind + `var(--doc-*)` 토큰 혼용. hex 하드코딩 금지.
 */
export const FORM_SECTION_CLASS = "space-y-3";
export const FORM_FIELD_CLASS = "space-y-1.5";

/** 2열 그리드(예: label, value 묶음)에 쓰는 유틸 클래스. */
export const FORM_GRID_CLASS = "grid grid-cols-2 gap-2";

/** 읽기 전용 설명 텍스트(placeholder hint 등)에 공통 적용. */
export const FORM_HINT_STYLE: React.CSSProperties = {
  fontSize: "var(--doc-font-size-xs)",
  color: "var(--doc-text-muted)",
};

/** `data-locked=true` 컴포넌트를 편집할 때 전체 폼을 읽기 전용으로 표시. */
export const FORM_DISABLED_STYLE: React.CSSProperties = {
  opacity: 0.65,
  pointerEvents: "none",
};
