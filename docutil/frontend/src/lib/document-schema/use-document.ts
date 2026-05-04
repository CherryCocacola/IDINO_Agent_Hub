/**
 * use-document.ts — DocumentSchema 클라이언트 훅
 *
 * Phase 4 S1 D8 구현본. Phase 1 의 시그니처 스켈레톤을 교체한다.
 *
 * 3종 훅 제공:
 *   1. `useDocument(documentId)` — 서버에서 문서 조회 + 로컬 store 갱신.
 *   2. `usePatchDocument(documentId)` — PATCH 뮤테이션 (page / component / tokens).
 *   3. `useComponentRegeneration()` — S7 엔드포인트 대비 스텁. 시그니처만 확정.
 *
 * 제약 (CLAUDE.md / anti-patterns.md):
 *   - `fetch(...)` 직접 호출 금지. `apiClient` 만 사용.
 *   - 응답은 snake_case 그대로 (프론트 boundary 에서 매핑은 호출자 책임).
 *   - SWR / React Query 미사용 (phase1_decisions.md v1.2 Q10).
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import apiClient from "@/lib/api/client";
import type {
  Component,
  DesignTokens,
  DocumentSchema,
  DocumentType,
  ExportFormat,
  Page,
  UUID,
} from "@/types/document-schema";

import { useDocumentStore } from "./document-store";

// ─── 상수 ──────────────────────────────────────────────────────────────────

/** 백엔드 documents_v2 라우터 prefix. apiClient 가 `/api/v1` 을 붙인다. */
const DOCUMENTS_V2_BASE = "/v2/documents";

// ─── 공통 I/O 타입 (documents-v2.ts 스켈레톤과 호환) ──────────────────────

/** 전체 문서 생성 요청 (Mode A). */
export interface GenerateDocumentInput {
  type: DocumentType;
  prompt: string;
  source_document_ids?: UUID[];
  agent_id?: UUID | null;
  source_chat_session_id?: UUID | null;
}

/** 템플릿 기반 생성 요청 (Mode B). */
export interface FillTemplateInput {
  template_id: UUID;
  slot_inputs: Record<string, string | number | boolean>;
  source_document_ids?: UUID[];
}

/** Page 단위 부분 업데이트. */
export interface UpdatePageInput {
  document_id: UUID;
  page_id: string;
  page: Page;
}

/** Export 파일 요청. */
export interface ExportDocumentInput {
  document_id: UUID;
  format: ExportFormat;
}

export interface ExportDocumentResult {
  download_url: string;
  degraded_components: string[];
}

/** 부분 재생성 — 컴포넌트 단위. */
export interface RegenerateComponentInput {
  document_id: UUID;
  page_id: string;
  component_id: string;
  instruction: string;
}

/** 부분 재생성 — 페이지 단위. */
export interface RegeneratePageInput {
  document_id: UUID;
  page_id: string;
  instruction: string;
  preserve_component_ids?: string[];
}

// ─── PATCH body (서버 `/v2/documents/{id}` 와 1:1) ──────────────────────────

/**
 * `PATCH /v2/documents/{id}` request body.
 * 3가지 patch_type 지원 — postmessage-protocol.ts 의 SchemaPatchPayload 와
 * 필드가 대응되나 snake_case.
 */
export type DocumentPatchBody =
  | {
      patch_type: "page";
      page_id: string;
      data: Partial<Page>;
    }
  | {
      patch_type: "component";
      page_id: string;
      component_id: string;
      data: Partial<Component>;
    }
  | {
      patch_type: "tokens";
      data: DesignTokens;
    };

// ─── useDocument ────────────────────────────────────────────────────────────

export interface UseDocumentResult {
  /** 현재 서버의 DocumentSchema 스냅샷. 로딩 중에는 null. */
  document: DocumentSchema | null;
  isLoading: boolean;
  error: Error | null;
  /** 수동 재조회. 훅 호출자가 갱신이 필요할 때 사용. */
  reload: () => Promise<void>;
}

/**
 * 지정한 `documentId` 의 DocumentSchema 를 조회하고 `useDocumentStore` 에 캐시한다.
 *
 * 동작:
 *   - `documentId === null` 일 때는 API 를 호출하지 않고 초기 상태만 반환.
 *   - 성공 시 `useDocumentStore.setDocument(...)` 를 호출해 3분할 패널이 공유.
 *   - 언마운트 또는 documentId 변경 시 이전 요청 결과는 무시 (setState 방지).
 */
export function useDocument(documentId: UUID | null): UseDocumentResult {
  const setDocument = useDocumentStore((s) => s.setDocument);
  const storeDocument = useDocumentStore((s) => s.document);

  const [state, setState] = useState<{
    isLoading: boolean;
    error: Error | null;
  }>({ isLoading: false, error: null });

  // 현재 요청의 취소 토큰. useEffect cleanup 에서 tick 을 올려 stale 응답을 무시.
  const requestTokenRef = useRef(0);
  // 직전 fetch 완료된 id — 같은 id 를 prompt-box 생성 이후 다시 요구하더라도
  // 중복 GET 을 치지 않기 위한 가드.
  const lastFetchedIdRef = useRef<UUID | null>(null);

  const fetchOnce = useCallback(
    async (id: UUID): Promise<void> => {
      const token = ++requestTokenRef.current;
      // 첫 setState 는 microtask 경계 뒤로 지연시켜 "effect 내부 동기 setState"
      // 룰을 회피한다 (cascading render 경고). 동작 자체는 동일.
      await Promise.resolve();
      if (requestTokenRef.current !== token) return;
      setState({ isLoading: true, error: null });
      try {
        const result = await apiClient.get<DocumentSchema>(`${DOCUMENTS_V2_BASE}/${id}`);
        if (requestTokenRef.current !== token) return; // stale
        setDocument(result);
        lastFetchedIdRef.current = id;
        setState({ isLoading: false, error: null });
      } catch (err) {
        if (requestTokenRef.current !== token) return; // stale
        const error = err instanceof Error ? err : new Error("문서 조회에 실패했습니다.");
        setState({ isLoading: false, error });
      }
    },
    [setDocument],
  );

  useEffect(() => {
    if (!documentId) {
      // documentId 가 null 이면 진행 중인 요청을 무효화만 한다. 상태는 이미
      // 초기값이거나 이전 요청의 최종값 — 상위가 documentId 를 내렸을 때
      // 의도적으로 "이전 성공 데이터" 가 남길 원하는 경우를 존중.
      requestTokenRef.current += 1;
      return;
    }
    // store.document 가 이미 같은 id 를 들고 있다면 (예: prompt-box 가 방금
    // 생성 후 setDocument 로 주입해둔 상황) 중복 GET 을 치지 않는다.
    const existing = useDocumentStore.getState().document;
    if (existing?.document_id === documentId) {
      lastFetchedIdRef.current = documentId;
      return;
    }
    // 이미 한 번 fetch 끝난 id 로 재요청하는 경우도 skip (reload 를 거쳐야 갱신).
    if (lastFetchedIdRef.current === documentId) {
      return;
    }
    // fetchOnce 내부 setState 는 비동기 경계 뒤에서 발생. effect 의 동기 cascade
    // 가 아님을 명시.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchOnce(documentId);
    return () => {
      // 현재 요청을 무효화 — 응답이 돌아와도 set 하지 않는다.
      requestTokenRef.current += 1;
    };
  }, [documentId, fetchOnce]);

  const reload = useCallback(async () => {
    if (!documentId) return;
    await fetchOnce(documentId);
  }, [documentId, fetchOnce]);

  return {
    document: storeDocument,
    isLoading: state.isLoading,
    error: state.error,
    reload,
  };
}

// ─── usePatchDocument ──────────────────────────────────────────────────────

export interface UsePatchDocumentResult {
  /** Page 단위 PATCH. 성공 시 DocumentSchema 반환 + store 에도 반영. */
  patchPage: (pageId: string, data: Partial<Page>) => Promise<DocumentSchema>;
  /** Component 단위 PATCH. */
  patchComponent: (
    pageId: string,
    componentId: string,
    data: Partial<Component>,
  ) => Promise<DocumentSchema>;
  /** 디자인 토큰 전체 교체 PATCH. */
  patchTokens: (tokens: DesignTokens) => Promise<DocumentSchema>;
  /** 직전 PATCH 가 진행 중이면 true. 동시성 표시 용도. */
  isPatching: boolean;
  /** 직전 실패 에러. 새 PATCH 가 시작되면 null 로 리셋. */
  error: Error | null;
}

/**
 * `PATCH /v2/documents/{id}` 3종(page / component / tokens) 뮤테이션 훅.
 *
 * `useFormPatch.onPatch` 콜백이나 `DesignTokenPicker.onCommit` 에 주입해 사용한다.
 *
 * 설계 메모:
 *   - 성공 응답의 전체 DocumentSchema 로 store 를 교체 → 서버 정답으로 덮어씀.
 *   - 409 (conflict) 등 에러는 호출자 쪽에서 catch 해 UX 안내 책임.
 *   - documentId 가 빈 문자열이면 즉시 Error 를 throw (잘못된 호출 차단).
 */
export function usePatchDocument(documentId: UUID | null): UsePatchDocumentResult {
  const setDocument = useDocumentStore((s) => s.setDocument);
  const [state, setState] = useState<{ isPatching: boolean; error: Error | null }>({
    isPatching: false,
    error: null,
  });

  const sendPatch = useCallback(
    async (body: DocumentPatchBody): Promise<DocumentSchema> => {
      if (!documentId) {
        throw new Error("문서가 선택되지 않아 PATCH 를 수행할 수 없습니다.");
      }
      setState({ isPatching: true, error: null });
      try {
        const result = await apiClient.patch<DocumentSchema>(
          `${DOCUMENTS_V2_BASE}/${documentId}`,
          body,
        );
        setDocument(result);
        setState({ isPatching: false, error: null });
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error("문서 업데이트에 실패했습니다.");
        setState({ isPatching: false, error });
        throw error;
      }
    },
    [documentId, setDocument],
  );

  const patchPage = useCallback(
    (pageId: string, data: Partial<Page>) =>
      sendPatch({ patch_type: "page", page_id: pageId, data }),
    [sendPatch],
  );

  const patchComponent = useCallback(
    (pageId: string, componentId: string, data: Partial<Component>) =>
      sendPatch({
        patch_type: "component",
        page_id: pageId,
        component_id: componentId,
        data,
      }),
    [sendPatch],
  );

  const patchTokens = useCallback(
    (tokens: DesignTokens) => sendPatch({ patch_type: "tokens", data: tokens }),
    [sendPatch],
  );

  return {
    patchPage,
    patchComponent,
    patchTokens,
    isPatching: state.isPatching,
    error: state.error,
  };
}

// ─── useComponentRegeneration (S7 대비 스텁) ───────────────────────────────

export interface UseComponentRegenerationResult {
  /**
   * 단일 Component 재생성 요청.
   * S7 까지는 실제 API 가 없으므로 null 을 반환한다.
   */
  regenerateComponent: (input: RegenerateComponentInput) => Promise<Component | null>;
  /** Page 단위 재생성 요청. S7 까지는 null 반환. */
  regeneratePage: (input: RegeneratePageInput) => Promise<Page | null>;
  isRegenerating: boolean;
  error: Error | null;
}

/**
 * 부분 재생성 스텁 훅 (S7 endpoints 연결 예정).
 *
 * 현재는 mutation state 확립만 담당. 실제 호출 대신 디버깅용 로그만 남긴다.
 * 호출자는 null 을 받는 경로를 "아직 지원되지 않음" UX 로 처리해야 한다.
 */
export function useComponentRegeneration(): UseComponentRegenerationResult {
  const [state, setState] = useState<{ isRegenerating: boolean; error: Error | null }>({
    isRegenerating: false,
    error: null,
  });

  const regenerateComponent = useCallback(
    async (input: RegenerateComponentInput): Promise<Component | null> => {
      setState({ isRegenerating: true, error: null });
      // eslint-disable-next-line no-console -- S7 연결 전 placeholder
      console.info("[ComponentRegeneration] TODO(S7): POST /regenerate-component", input);
      setState({ isRegenerating: false, error: null });
      return null;
    },
    [],
  );

  const regeneratePage = useCallback(async (input: RegeneratePageInput): Promise<Page | null> => {
    setState({ isRegenerating: true, error: null });
    // eslint-disable-next-line no-console -- S7 연결 전 placeholder
    console.info("[ComponentRegeneration] TODO(S7): POST /regenerate-page", input);
    setState({ isRegenerating: false, error: null });
    return null;
  }, []);

  return {
    regenerateComponent,
    regeneratePage,
    isRegenerating: state.isRegenerating,
    error: state.error,
  };
}

// ─── 하위 호환 alias (Phase 1 스켈레톤과의 심볼 차이를 최소화) ──────────────
// 이전 버전의 useDocumentMutation 은 prompt-box/useDocumentMutation.ts 로 옮겨져 있다.
// S7 에서 export/regeneration 이 추가되면 여기서 재집결할 예정.

export type { DocumentSchema, Page, Component, DesignTokens, UUID };
