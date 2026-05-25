/**
 * use-template.ts — DocumentV2Template 클라이언트 훅
 *
 * Phase 4 S4 D4 산출물. `(admin)/template-designer/[templateId]` 라우트에서
 * 템플릿 단건을 조회할 때 사용한다. `useDocument` (`use-document.ts`) 의
 * 패턴을 그대로 차용해 4-state (loading / error / not-found / success) 분기를
 * 라우트 페이지가 동일한 구조로 처리할 수 있도록 한다.
 *
 * 제약 (CLAUDE.md / anti-patterns.md):
 *   - `fetch(...)` 직접 호출 금지. `templates-v2.ts` 의 `getTemplate` 만 사용.
 *   - SWR / React Query 미사용 (use-document 와 일관 — phase1_decisions.md v1.2 Q10).
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getTemplate, type DocumentV2Template } from "@/lib/api/templates-v2";
import type { UUID } from "@/types/document-schema";

export interface UseTemplateResult {
  /** 현재 서버의 DocumentV2Template 스냅샷. 로딩/에러 시 null. */
  template: DocumentV2Template | null;
  isLoading: boolean;
  error: Error | null;
  /** 수동 재조회. */
  reload: () => Promise<void>;
}

/**
 * 지정한 `templateId` 의 DocumentV2Template 을 조회한다.
 *
 * 동작:
 *   - `templateId === null` 이면 API 호출 없이 초기 상태 반환.
 *   - 언마운트 또는 templateId 변경 시 stale 응답을 무시 (요청 토큰 가드).
 *   - 동일 id 재요청은 skip (수동 재조회는 `reload()` 사용).
 */
export function useTemplate(templateId: UUID | null): UseTemplateResult {
  const [template, setTemplate] = useState<DocumentV2Template | null>(null);
  const [state, setState] = useState<{ isLoading: boolean; error: Error | null }>({
    isLoading: false,
    error: null,
  });

  const requestTokenRef = useRef(0);
  const lastFetchedIdRef = useRef<UUID | null>(null);

  const fetchOnce = useCallback(async (id: UUID): Promise<void> => {
    const token = ++requestTokenRef.current;
    await Promise.resolve();
    if (requestTokenRef.current !== token) return;
    setState({ isLoading: true, error: null });
    try {
      const result = await getTemplate(id);
      if (requestTokenRef.current !== token) return;
      setTemplate(result);
      lastFetchedIdRef.current = id;
      setState({ isLoading: false, error: null });
    } catch (err) {
      if (requestTokenRef.current !== token) return;
      const error = err instanceof Error ? err : new Error("템플릿 조회에 실패했습니다.");
      setState({ isLoading: false, error });
    }
  }, []);

  useEffect(() => {
    if (!templateId) {
      requestTokenRef.current += 1;
      return;
    }
    if (lastFetchedIdRef.current === templateId) {
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void fetchOnce(templateId);
    return () => {
      requestTokenRef.current += 1;
    };
  }, [templateId, fetchOnce]);

  const reload = useCallback(async () => {
    if (!templateId) return;
    await fetchOnce(templateId);
  }, [templateId, fetchOnce]);

  return {
    template,
    isLoading: state.isLoading,
    error: state.error,
    reload,
  };
}
