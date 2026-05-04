/**
 * document-store.ts — Designer Shell 전역 문서 상태 Zustand 스토어
 *
 * Phase 4 S1 D8 산출물. 3분할 셸 (prompt-box / preview-pane / edit-sidebar /
 * design-token-picker) 이 공유하는 "현재 편집 중인 DocumentSchema 스냅샷" 을
 * 담는다.
 *
 * 설계 결정 (phase1_decisions.md v1.2 Q10):
 *   - SWR / React Query 미사용. `useState` 혹은 Zustand 로 순수 상태만 관리.
 *   - 본 스토어는 persist 하지 않는다 (서버가 단일 진실원본 — 새로고침 시
 *     useDocument 로 재조회).
 *   - 스토어는 "schema JSONB 의 현재 스냅샷" 만 담으며, 네트워크 요청이나
 *     debounce 는 각 패널의 훅에서 책임진다 (관심사 분리).
 *
 * 왜 Zustand 인가:
 *   - `use-auth.ts` 에서 이미 사용 중 → 의존성 신규 도입 없음.
 *   - 3패널이 하나의 schema 를 읽고, edit-sidebar·token-picker 가 부분 패치를
 *     다시 스토어에 쓰는 구조라 prop drilling 이 과해진다.
 *
 * 제약:
 *   - 이 파일은 "상태 holder" 만 담당. API 호출 / postMessage / debounce 로직은
 *     금지 (관련 훅에서 처리).
 *   - 모든 mutation 은 immutable. 기존 배열·객체를 직접 mutate 하지 않고 새
 *     인스턴스를 반환한다 (React 리렌더 트리거 + 테스트 용이성).
 */

"use client";

import { create } from "zustand";

import type { Component, DesignTokens, DocumentSchema, Page, UUID } from "@/types/document-schema";

// ─── 상태 인터페이스 ───────────────────────────────────────────────────────

/**
 * 현재 편집 중인 문서의 선택 상태.
 * - `selected` 는 edit-sidebar 활성화 트리거.
 * - preview-pane 의 `docutil/element-select` 수신 시 갱신.
 */
export interface SelectedElement {
  pageId: string;
  componentId: string;
}

export interface DocumentStoreState {
  /** 현재 로드된 문서. null 이면 아직 미로드 또는 생성 전. */
  document: DocumentSchema | null;
  /** 현재 사이드바에서 편집 중인 컴포넌트. */
  selected: SelectedElement | null;
}

export interface DocumentStoreActions {
  /** 새 문서 스냅샷으로 전체 교체 (생성 / 재조회 직후). */
  setDocument: (document: DocumentSchema | null) => void;
  /** element-select 메시지 수신 시 호출. */
  setSelected: (selection: SelectedElement | null) => void;
  /** 스토어를 초기 상태로. 로그아웃/라우트 이탈 시. */
  reset: () => void;

  // ── Partial patch mutators ─────────────────────────────────────────────
  /**
   * 단일 Page 의 일부 필드를 병합.
   * 서버 PATCH 성공 후 또는 낙관적 업데이트용.
   */
  patchPage: (pageId: string, patch: Partial<Page>) => void;
  /** 단일 Component 의 일부 필드를 병합. */
  patchComponent: (pageId: string, componentId: string, patch: Partial<Component>) => void;
  /** 디자인 토큰 전체 교체. */
  setTokens: (tokens: DesignTokens) => void;
  /** 디자인 토큰 부분 병합 (token-picker 의 custom 편집 중 사용). */
  patchTokens: (patch: Partial<DesignTokens>) => void;
}

export type DocumentStore = DocumentStoreState & DocumentStoreActions;

// ─── 초기값 ────────────────────────────────────────────────────────────────

const INITIAL_STATE: DocumentStoreState = {
  document: null,
  selected: null,
};

// ─── 내부 헬퍼 (immutable) ─────────────────────────────────────────────────

/** 지정 pageId 를 찾아 patch 를 병합한 새 document 를 반환. */
function applyPagePatch(
  document: DocumentSchema,
  pageId: string,
  patch: Partial<Page>,
): DocumentSchema {
  let changed = false;
  const nextPages = document.pages.map((page) => {
    if (page.id !== pageId) return page;
    changed = true;
    return { ...page, ...patch } as Page;
  });
  if (!changed) return document;
  return { ...document, pages: nextPages };
}

/** 지정 component 를 찾아 patch 를 병합한 새 document 를 반환. */
function applyComponentPatch(
  document: DocumentSchema,
  pageId: string,
  componentId: string,
  patch: Partial<Component>,
): DocumentSchema {
  let docChanged = false;
  const nextPages = document.pages.map((page) => {
    if (page.id !== pageId) return page;
    let pageChanged = false;
    const nextComponents = page.components.map((component) => {
      if (component.id !== componentId) return component;
      pageChanged = true;
      // discriminated union 을 유지하기 위해 type 은 보존한다.
      return { ...component, ...patch, type: component.type } as Component;
    });
    if (!pageChanged) return page;
    docChanged = true;
    return { ...page, components: nextComponents };
  });
  if (!docChanged) return document;
  return { ...document, pages: nextPages };
}

// ─── Zustand 스토어 ────────────────────────────────────────────────────────

export const useDocumentStore = create<DocumentStore>((set) => ({
  ...INITIAL_STATE,

  setDocument: (document) => {
    set({ document, selected: null });
  },

  setSelected: (selection) => {
    set({ selected: selection });
  },

  reset: () => {
    set({ ...INITIAL_STATE });
  },

  patchPage: (pageId, patch) => {
    set((state) => {
      if (!state.document) return state;
      const nextDocument = applyPagePatch(state.document, pageId, patch);
      if (nextDocument === state.document) return state;
      return { ...state, document: nextDocument };
    });
  },

  patchComponent: (pageId, componentId, patch) => {
    set((state) => {
      if (!state.document) return state;
      const nextDocument = applyComponentPatch(state.document, pageId, componentId, patch);
      if (nextDocument === state.document) return state;
      return { ...state, document: nextDocument };
    });
  },

  setTokens: (tokens) => {
    set((state) => {
      if (!state.document) return state;
      return {
        ...state,
        document: { ...state.document, design_tokens: tokens },
      };
    });
  },

  patchTokens: (patch) => {
    set((state) => {
      if (!state.document) return state;
      const merged = { ...state.document.design_tokens } as DesignTokens;
      (Object.keys(patch) as Array<keyof DesignTokens>).forEach((key) => {
        const next = patch[key];
        if (next !== undefined) {
          // 각 필드는 string / literal union. 타입 브리지는 unknown 경유.
          (merged as unknown as Record<string, unknown>)[key as string] = next;
        }
      });
      return {
        ...state,
        document: { ...state.document, design_tokens: merged },
      };
    });
  },
}));

// ─── 조회 헬퍼 (훅 / 컴포넌트에서 재사용) ────────────────────────────────

/**
 * DocumentSchema 안에서 특정 컴포넌트를 찾는다. 컨테이너 내부(TwoColumn.left 등)까지
 * 재귀로 탐색한다. 찾지 못하면 null.
 *
 * 본 유틸은 store 와 별개로 pure fn 으로 두어 테스트·다른 패널에서도 사용 가능.
 */
export function findComponent(
  schema: DocumentSchema | null,
  selection: SelectedElement | null,
): Component | null {
  if (!schema || !selection) return null;
  const page = schema.pages.find((p) => p.id === selection.pageId);
  if (!page) return null;
  return findComponentInList(page.components, selection.componentId);
}

function findComponentInList(components: Component[], componentId: string): Component | null {
  for (const c of components) {
    if (c.id === componentId) return c;
    // 컨테이너형 컴포넌트는 재귀.
    if (c.type === "TwoColumn") {
      const hit =
        findComponentInList(c.left, componentId) ?? findComponentInList(c.right, componentId);
      if (hit) return hit;
    } else if (c.type === "ThreeColumn") {
      for (const col of c.columns) {
        const hit = findComponentInList(col, componentId);
        if (hit) return hit;
      }
    }
  }
  return null;
}

/** 현재 로드된 문서의 ID. null-safe 헬퍼. */
export function selectDocumentId(state: DocumentStoreState): UUID | null {
  return state.document?.document_id ?? null;
}
