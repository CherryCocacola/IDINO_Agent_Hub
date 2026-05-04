/**
 * use-export-status.ts — Celery export 작업 상태 폴링 훅
 *
 * Phase 4 S2 D2 — FE 단독 구현. 백엔드 상태 엔드포인트는 D5 에 완성된다.
 * 본 훅은 그 전까지도 시그니처가 깨지지 않도록 **호출 자체의 실패도 에러로 전파**
 * 하며, `jobId === null` 일 때는 no-op 로 동작한다.
 *
 * 동작:
 *   - 2 초 간격 `setInterval` 로 `getExportStatus(jobId)` 호출.
 *   - `status` 가 "completed" 또는 "failed" 가 되면 interval 을 즉시 정리한다.
 *   - `jobId` 가 바뀌면 이전 interval 을 정리하고 상태를 리셋한다.
 *   - 언마운트 시 interval 정리 (메모리 누수 방지).
 *
 * 제약 (anti-patterns.md):
 *   - `fetch` 직접 호출 금지 — `documents-v2.ts` 의 `getExportStatus` 만 사용한다.
 *   - snake_case ↔ camelCase 매핑은 훅 경계에서 수행.
 */

"use client";

import { useEffect, useRef, useState } from "react";

import { getExportStatus } from "@/lib/api/documents-v2";

import type { ExportStatusView } from "./types";

// ─── 상수 ──────────────────────────────────────────────────────────────────

/** 상태 조회 폴링 주기. 2 초 — 체감 지연과 서버 부하의 타협점. */
const POLL_INTERVAL_MS = 2000;

/** 초기 viewmodel. jobId 가 null 일 때도 이 값으로 반환한다. */
const INITIAL_STATE: ExportStatusView = {
  status: "pending",
  progress: 0,
  downloadUrl: null,
  error: null,
};

// ─── 훅 ────────────────────────────────────────────────────────────────────

/**
 * 지정한 export job 의 상태를 2 초 간격으로 폴링한다.
 *
 * @param jobId - `exportDocument` 가 반환한 작업 ID. `null` 이면 폴링하지 않고
 *                초기 상태만 반환.
 *
 * 사용 예:
 * ```tsx
 * const { status, progress, downloadUrl, error } = useExportStatus(jobId);
 * ```
 */
export function useExportStatus(jobId: string | null): ExportStatusView {
  const [state, setState] = useState<ExportStatusView>(INITIAL_STATE);

  // 언마운트 또는 jobId 변경 후 도착한 stale 응답을 차단하기 위한 토큰.
  const tokenRef = useRef(0);

  useEffect(() => {
    // jobId 가 없으면 폴링을 시작하지 않고 상태를 리셋한다.
    if (!jobId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- 진입 시 1회 리셋.
      setState(INITIAL_STATE);
      return;
    }

    const myToken = ++tokenRef.current;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    // 단일 폴링 스텝. 완료 또는 실패 시 interval 을 정리한다.
    const tick = async () => {
      try {
        const res = await getExportStatus(jobId);
        // 다른 jobId 로 교체되었거나 언마운트된 경우 반영하지 않는다.
        if (tokenRef.current !== myToken) return;

        setState({
          status: res.status,
          progress: typeof res.progress === "number" ? res.progress : 0,
          downloadUrl: res.download_url ?? null,
          error: res.error ? new Error(res.error) : null,
        });

        if (res.status === "completed" || res.status === "failed") {
          if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
          }
        }
      } catch (err) {
        if (tokenRef.current !== myToken) return;
        const error = err instanceof Error ? err : new Error("내보내기 상태를 확인할 수 없습니다.");
        setState((prev) => ({ ...prev, status: "failed", error }));
        if (intervalId) {
          clearInterval(intervalId);
          intervalId = null;
        }
      }
    };

    // 최초 호출은 즉시 실행해 UX 지연을 줄이고, 이후 2 초 간격으로 반복.
    void tick();
    intervalId = setInterval(() => {
      void tick();
    }, POLL_INTERVAL_MS);

    // cleanup: jobId 변경 또는 언마운트 시 interval 정리 + stale 응답 차단.
    return () => {
      tokenRef.current += 1;
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };
  }, [jobId]);

  return state;
}
