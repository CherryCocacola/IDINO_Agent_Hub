/**
 * useDocumentMutation — DocumentSchema 생성(Mode A) 전용 mutation 훅
 *
 * Phase 4 S1 D6 산출물. 문서 designer 의 좌측 상단 `<PromptBox>` 에서 호출된다.
 *
 * 결정 사항 (phase1_decisions.md v1.2 Q10):
 *   - SWR / React Query 를 사용하지 않는다. 단순 `useState` 기반 상태 머신.
 *   - 전역 cache invalidation 은 하지 않는다. 호출자가 반환된 `DocumentSchema` 를
 *     상위 state 에 그대로 주입한다.
 *
 * 제약:
 *   - `apiClient` 외의 HTTP 수단 금지 (hardcoded fetch 금지).
 *   - request body 는 backend snake_case 로 전송, response 또한 snake_case 로 받는다.
 *   - 에러는 "Error" 인스턴스로 표준화. 호출자는 `ValidationFeedback` 에서 Korean
 *     메시지로 노출.
 *
 * D8 에서 동일 패턴으로 PATCH(updatePage) 훅이 추가될 예정. 시그니처를 참고.
 */

"use client";

import { useCallback, useState } from "react";

import apiClient, { isApiError } from "@/lib/api/client";
import type { DocumentSchema, DocumentType, UUID } from "@/types/document-schema";

// ─── I/O 타입 ──────────────────────────────────────────────────────────────

/**
 * `<PromptBox>` 폼 입력을 그대로 받는다. snake_case 매핑은 이 훅 내부에서 처리.
 */
export interface UseDocumentMutationInput {
  prompt: string;
  documentType: DocumentType;
  sourceDocumentIds: UUID[];
  agentId: UUID | null;
}

/**
 * `POST /v2/documents` 의 응답 타입. Phase 1 기준으로 DocumentSchema 전체가 반환된다.
 * 현 훅에서는 별칭만 두고 타입을 재사용.
 */
export type GenerateDocumentResponse = DocumentSchema;

export interface UseDocumentMutationState {
  /** 요청 진행 중이면 true. */
  isPending: boolean;
  /** 직전 실패. 새 요청이 시작되면 null 로 리셋. */
  error: Error | null;
  /** 직전 성공 응답. */
  data: GenerateDocumentResponse | null;
}

export interface UseDocumentMutationResult extends UseDocumentMutationState {
  /** 생성 요청을 실행. 성공 시 data 세팅 + 응답 반환, 실패 시 예외를 throw. */
  mutateAsync: (input: UseDocumentMutationInput) => Promise<GenerateDocumentResponse>;
  /** state 를 초기값으로 되돌린다. */
  reset: () => void;
}

// ─── 상수 ──────────────────────────────────────────────────────────────────

/** 백엔드 documents_v2 라우터 prefix. apiClient 가 `/api/v1` 을 붙인다. */
const DOCUMENTS_V2_BASE = "/v2/documents";

const INITIAL_STATE: UseDocumentMutationState = {
  isPending: false,
  error: null,
  data: null,
};

// ─── 훅 본체 ───────────────────────────────────────────────────────────────

/**
 * 전체 문서 생성(Mode A) mutation.
 *
 * 사용 예:
 * ```tsx
 * const mutation = useDocumentMutation();
 * const handleSubmit = async () => {
 *   const doc = await mutation.mutateAsync({ prompt, documentType, sourceDocumentIds, agentId });
 *   onDocumentGenerated(doc);
 * };
 * ```
 */
export function useDocumentMutation(): UseDocumentMutationResult {
  const [state, setState] = useState<UseDocumentMutationState>(INITIAL_STATE);

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  const mutateAsync = useCallback(
    async (input: UseDocumentMutationInput): Promise<GenerateDocumentResponse> => {
      setState({ isPending: true, error: null, data: null });
      try {
        const response = await apiClient.post<GenerateDocumentResponse>(DOCUMENTS_V2_BASE, {
          mode: "free_generation",
          type: input.documentType,
          prompt: input.prompt,
          source_document_ids: input.sourceDocumentIds,
          agent_id: input.agentId,
        });
        setState({ isPending: false, error: null, data: response });
        return response;
      } catch (err) {
        // ApiError 는 status/detail 을 보존해 상위에서 403 쿼터 토스트 등
        // 특화 처리를 할 수 있게 그대로 재던진다 (Phase 4 S3 D5).
        if (isApiError(err)) {
          setState({ isPending: false, error: err, data: null });
          throw err;
        }
        const error = err instanceof Error ? err : new Error("문서 생성 요청이 실패했습니다.");
        setState({ isPending: false, error, data: null });
        throw error;
      }
    },
    [],
  );

  return {
    ...state,
    mutateAsync,
    reset,
  };
}

export default useDocumentMutation;
