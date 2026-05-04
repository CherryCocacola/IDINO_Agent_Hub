/**
 * useDebouncedTokenSync — 디자인 토큰 변경을 두 개의 독립된 debounce 파이프에 흘리는 훅
 *
 * Phase 4 S1 D5 산출물. `edit-sidebar/forms/useFormPatch.ts` 와 역할이 겹치지
 * 않는다: 편집 폼은 "필드 편집 → 서버 저장" 단일 파이프지만, token picker 는
 * 두 개의 파이프를 동시에 돌린다.
 *
 *   1. **preview** — 50ms debounce. 슬라이더를 드래그하는 동안 iframe CSS 변수
 *      (`--doc-primary` 등) 를 즉시 override. UX 상 사용자가 색 변화를 "끊기지
 *      않는 라이브 프리뷰" 로 체감해야 한다. 50ms 는 60fps 프레임(~16ms) 보다
 *      넉넉해 이벤트 폭주로 인한 메인 스레드 점유를 막으면서도 육안으로 지연이
 *      느껴지지 않는 한계선.
 *   2. **commit** — 500ms debounce. 드래그가 끝난 뒤 마지막 값만 서버에 PATCH
 *      (schema-patch-local/tokens). 편집 폼과 동일한 500ms 로 맞춰 UX 일관성
 *      확보 (`FORM_PATCH_DEBOUNCE_MS`).
 *
 * 두 파이프는 **누적 병합** 된다: 드래그 도중 primary 와 accent 를 연속으로
 * 만진 뒤 멈추면, commit 은 `{ primary, accent }` 하나로 flush.
 *
 * 왜 `useFormPatch` 를 재사용하지 않는가:
 *   - useFormPatch 는 단일 delay, 단일 onPatch. 이곳은 이중 debounce 가 필요.
 *   - preview 는 componentId / pageId 가 없다 (문서 전역 토큰 단위).
 *   - 반면 cancel / flush / 누적 병합 / 언마운트 flush 같은 "디바운스 보일러
 *     플레이트" 는 구조가 같아 내부 구현 패턴만 따라한다.
 *
 * @see docs/phase1_decisions.md v1.2 Q10 (schema-patch-local vs token-update)
 * @see docs/phase3_execution_roadmap.md §2.1 S1 D5
 */

"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";

import type { DesignTokens } from "@/types/document-schema";

/** 라이브 프리뷰 debounce — 60fps 프레임(16ms) 보다 여유, 인지 지연 한계선. */
export const TOKEN_PREVIEW_DEBOUNCE_MS = 50;
/** 서버 저장 debounce — 편집 폼과 동일한 500ms 로 일관성 유지. */
export const TOKEN_COMMIT_DEBOUNCE_MS = 500;

export interface UseDebouncedTokenSyncOptions {
  /**
   * iframe CSS 변수 override 파이프. 50ms debounce 로 실행.
   * 호출자는 `PreviewPaneHandle.sendTokenUpdate(patch)` 를 연결한다.
   */
  onPreview: (patch: Partial<DesignTokens>) => void;
  /**
   * 서버 PATCH 파이프. 500ms debounce 로 실행.
   * 호출자는 D8 에서 `apiClient.patch(/v2/documents/{id})` 를 연결한다.
   */
  onCommit: (patch: Partial<DesignTokens>) => void;
  /** preview debounce (ms). 테스트에서 0/custom 으로 override. */
  previewDelayMs?: number;
  /** commit debounce (ms). 테스트에서 0/custom 으로 override. */
  commitDelayMs?: number;
}

export interface UseDebouncedTokenSyncResult {
  /** 50ms 이내 preview flush 예약. 즉시 반영이 필요하면 `flushPreview()`. */
  preview: (patch: Partial<DesignTokens>) => void;
  /** 500ms 이내 commit flush 예약. */
  commit: (patch: Partial<DesignTokens>) => void;
  /** preview 대기 중이면 즉시 flush. */
  flushPreview: () => void;
  /** commit 대기 중이면 즉시 flush. */
  flushCommit: () => void;
  /** 양쪽 파이프 모두 즉시 flush (예: 다른 문서로 이동 직전). */
  flush: () => void;
  /** 양쪽 파이프 대기 취소 (rollback 시). */
  cancel: () => void;
}

/**
 * 별개 debounce 타이머 2개로 preview / commit 파이프를 독립적으로 관리.
 *
 * 구현 노트:
 *   - timer/pending 은 모두 ref 기반. 렌더 간 유지, React 19 의 ref mutation
 *     규칙 준수 (render 중 쓰지 않음).
 *   - 언마운트 시 commit 대기 flush → 드래그 직후 언마운트돼도 서버 저장이
 *     보장된다. preview 는 이미 iframe 에 반영됐거나 곧 폐기되므로 flush 불필요.
 */
export function useDebouncedTokenSync(
  options: UseDebouncedTokenSyncOptions,
): UseDebouncedTokenSyncResult {
  const {
    onPreview,
    onCommit,
    previewDelayMs = TOKEN_PREVIEW_DEBOUNCE_MS,
    commitDelayMs = TOKEN_COMMIT_DEBOUNCE_MS,
  } = options;

  // 콜백은 ref 로 최신 값을 참조해 preview/commit identity 를 안정시킨다.
  const onPreviewRef = useRef(onPreview);
  const onCommitRef = useRef(onCommit);
  useEffect(() => {
    onPreviewRef.current = onPreview;
  }, [onPreview]);
  useEffect(() => {
    onCommitRef.current = onCommit;
  }, [onCommit]);

  const previewTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const commitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingPreviewRef = useRef<Partial<DesignTokens> | null>(null);
  const pendingCommitRef = useRef<Partial<DesignTokens> | null>(null);

  const flushPreview = useCallback(() => {
    if (previewTimerRef.current === null) return;
    clearTimeout(previewTimerRef.current);
    previewTimerRef.current = null;
    const pending = pendingPreviewRef.current;
    pendingPreviewRef.current = null;
    if (pending) onPreviewRef.current(pending);
  }, []);

  const flushCommit = useCallback(() => {
    if (commitTimerRef.current === null) return;
    clearTimeout(commitTimerRef.current);
    commitTimerRef.current = null;
    const pending = pendingCommitRef.current;
    pendingCommitRef.current = null;
    if (pending) onCommitRef.current(pending);
  }, []);

  const flush = useCallback(() => {
    flushPreview();
    flushCommit();
  }, [flushPreview, flushCommit]);

  const cancel = useCallback(() => {
    if (previewTimerRef.current !== null) {
      clearTimeout(previewTimerRef.current);
      previewTimerRef.current = null;
    }
    if (commitTimerRef.current !== null) {
      clearTimeout(commitTimerRef.current);
      commitTimerRef.current = null;
    }
    pendingPreviewRef.current = null;
    pendingCommitRef.current = null;
  }, []);

  const preview = useCallback(
    (patch: Partial<DesignTokens>) => {
      pendingPreviewRef.current = { ...(pendingPreviewRef.current ?? {}), ...patch };
      if (previewTimerRef.current !== null) clearTimeout(previewTimerRef.current);
      previewTimerRef.current = setTimeout(() => {
        previewTimerRef.current = null;
        const pending = pendingPreviewRef.current;
        pendingPreviewRef.current = null;
        if (pending) onPreviewRef.current(pending);
      }, previewDelayMs);
    },
    [previewDelayMs],
  );

  const commit = useCallback(
    (patch: Partial<DesignTokens>) => {
      pendingCommitRef.current = { ...(pendingCommitRef.current ?? {}), ...patch };
      if (commitTimerRef.current !== null) clearTimeout(commitTimerRef.current);
      commitTimerRef.current = setTimeout(() => {
        commitTimerRef.current = null;
        const pending = pendingCommitRef.current;
        pendingCommitRef.current = null;
        if (pending) onCommitRef.current(pending);
      }, commitDelayMs);
    },
    [commitDelayMs],
  );

  // 언마운트 정리: commit 만 flush(데이터 유실 방지), preview 는 drop.
  useEffect(() => {
    return () => {
      if (previewTimerRef.current !== null) {
        clearTimeout(previewTimerRef.current);
        previewTimerRef.current = null;
      }
      if (commitTimerRef.current !== null) {
        clearTimeout(commitTimerRef.current);
        commitTimerRef.current = null;
        const pending = pendingCommitRef.current;
        pendingCommitRef.current = null;
        if (pending) onCommitRef.current(pending);
      }
      pendingPreviewRef.current = null;
    };
  }, []);

  return useMemo(
    () => ({ preview, commit, flushPreview, flushCommit, flush, cancel }),
    [preview, commit, flushPreview, flushCommit, flush, cancel],
  );
}

export default useDebouncedTokenSync;
