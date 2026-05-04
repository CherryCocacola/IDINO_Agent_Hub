/**
 * useFormPatch — 폼 필드 변경을 500ms debounce 로 서버 PATCH 에 반영하는 훅
 *
 * Phase 4 S1 D4 산출물. D4 범위에서는 실제 `apiClient.patch(...)` 호출은 연결하지
 * 않고 console.log 로 대체한다 (D8 에서 `/v2/documents/{id}` PATCH 와 결선).
 *
 * 설계:
 *   - 즉시 프리뷰 반영은 호출자가 직접 `onLocalPatch(...)` 로 처리한다.
 *   - 본 훅은 "debounce 된 서버 저장" 파이프만 제공한다 (관심사 분리).
 *   - `commit(patch)` 를 여러 번 호출하면 마지막 호출 기준 500ms 후 1회만 flush.
 *     같은 필드를 연타 입력해도 불필요한 PATCH 가 중복되지 않는다.
 *   - 컴포넌트 언마운트 시 대기 중 타이머를 정리해 메모리 누수를 방지한다.
 *
 * 왜 lodash.debounce 를 쓰지 않는가:
 *   - 프로젝트 package.json 의존성에 lodash 가 없고, 단순한 debounce 하나를 위해
 *     번들 비용을 올릴 이유가 없다. 자체 구현이 20 줄 이내.
 *
 * @see docs/phase1_decisions.md v1.2 Q10 (Partial DocumentSchema PATCH)
 * @see docs/phase3_execution_roadmap.md §2.1 S1 D4
 */

"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";

/** 서버 PATCH debounce 대기 시간. UX 가이드: 150~500ms, D4 에서 500ms 확정. */
export const FORM_PATCH_DEBOUNCE_MS = 500;

export interface UseFormPatchResult<C> {
  /**
   * debounce 된 서버 PATCH 호출. 즉시 프리뷰 반영은 호출자가 `onLocalPatch` 로
   * 별도 처리한다.
   * 마지막 호출 기준 `FORM_PATCH_DEBOUNCE_MS` 후에 1회만 실행된다.
   */
  commit: (patch: Partial<C>) => void;
  /** 대기 중인 flush 를 즉시 실행 (blur 이벤트 등에서 사용). */
  flush: () => void;
  /** 대기 중인 flush 를 취소 (편집 롤백 시 사용). */
  cancel: () => void;
}

export interface UseFormPatchOptions {
  /** debounce 간격 (ms). 기본 500ms. 테스트에서 0 으로 덮을 수 있다. */
  delayMs?: number;
  /**
   * 실제 PATCH 동작. D4 에서는 주입 없이 console.log 로 대체.
   * D8 에서 `apiClient.patch(...)` 를 여기에 wiring.
   */
  onPatch?: (args: { componentId: string; pageId: string; patch: unknown }) => void;
}

/**
 * 컴포넌트 편집 폼 전용 debounce 훅.
 *
 * @param componentId 편집 대상 컴포넌트 id (로그/PATCH url 구성)
 * @param pageId      소속 페이지 id
 * @param options     debounce 간격 / 실제 PATCH 콜백 주입
 */
export function useFormPatch<C>(
  componentId: string,
  pageId: string,
  options: UseFormPatchOptions = {},
): UseFormPatchResult<C> {
  const { delayMs = FORM_PATCH_DEBOUNCE_MS, onPatch } = options;

  // 대기 중인 타이머 id. 렌더 사이에 유지되어야 하므로 ref.
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // 가장 최근에 받은 patch. flush 시점에 실제 반영된다.
  const pendingPatchRef = useRef<Partial<C> | null>(null);
  // 콜백은 ref 로 최신 값을 참조해 `commit` 의 identity 를 안정시킨다.
  // React 19 규칙상 ref.current 는 render 중 mutation 금지 → useEffect 로 동기화.
  const onPatchRef = useRef<UseFormPatchOptions["onPatch"]>(onPatch);
  useEffect(() => {
    onPatchRef.current = onPatch;
  }, [onPatch]);

  const runPatch = useCallback(
    (patch: Partial<C>) => {
      if (onPatchRef.current) {
        onPatchRef.current({ componentId, pageId, patch });
        return;
      }
      // D4 default — 실제 서버 PATCH 는 D8 에서 연결.
      // eslint-disable-next-line no-console -- 개발용 placeholder 로그
      console.info("[FormPatch]", { componentId, pageId, patch });
    },
    [componentId, pageId],
  );

  const cancel = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    pendingPatchRef.current = null;
  }, []);

  const flush = useCallback(() => {
    if (timerRef.current === null) return;
    clearTimeout(timerRef.current);
    timerRef.current = null;
    const pending = pendingPatchRef.current;
    pendingPatchRef.current = null;
    if (pending) runPatch(pending);
  }, [runPatch]);

  const commit = useCallback(
    (patch: Partial<C>) => {
      // 이전 patch 와 병합해 같은 edit 세션 안에서 필드가 누락되지 않게 한다.
      pendingPatchRef.current = { ...(pendingPatchRef.current ?? {}), ...patch };
      if (timerRef.current !== null) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        const pending = pendingPatchRef.current;
        pendingPatchRef.current = null;
        if (pending) runPatch(pending);
      }, delayMs);
    },
    [delayMs, runPatch],
  );

  // 언마운트 시 타이머 정리 + 가장 최근 patch flush (데이터 유실 방지).
  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
        const pending = pendingPatchRef.current;
        pendingPatchRef.current = null;
        if (pending) runPatch(pending);
      }
    };
  }, [runPatch]);

  return useMemo(() => ({ commit, flush, cancel }), [commit, flush, cancel]);
}

export default useFormPatch;
