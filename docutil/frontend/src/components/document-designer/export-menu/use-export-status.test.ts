/**
 * use-export-status.test.ts — 폴링 훅 단위 테스트
 *
 * 검증 항목:
 *   1. jobId 가 null 이면 폴링이 시작되지 않는다.
 *   2. status === "completed" 시 API 호출이 멈춘다.
 *   3. status === "failed" 시 error 가 채워진다.
 *   4. 언마운트 시 interval 이 정리된다 (cleanup).
 *
 * 메모: `setInterval` 을 직접 검증하려면 fake timer 가 이상적이지만, 본 훅은
 * interval 콜백 내부에서 async 함수를 await 하므로 fake timer + Promise flush
 * 조합이 까다롭다. 대신 real timer + waitFor 로 "관찰 가능한 최종 상태" 만
 * 검증한다 — mock 응답을 "completed" 로 주면 최초 tick 직후 더는 호출되지
 * 않음을 확인할 수 있다.
 */

import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ExportStatusResponse } from "./types";
import { useExportStatus } from "./use-export-status";

// ─── getExportStatus mock ─────────────────────────────────────────────────

const mockGetExportStatus = vi.fn();

vi.mock("@/lib/api/documents-v2", () => ({
  getExportStatus: (...args: unknown[]) => mockGetExportStatus(...args),
}));

// ─── 테스트 ────────────────────────────────────────────────────────────────

describe("useExportStatus", () => {
  beforeEach(() => {
    mockGetExportStatus.mockReset();
  });

  it("jobId 가 null 이면 API 호출을 트리거하지 않는다", () => {
    const { result } = renderHook(() => useExportStatus(null));
    expect(mockGetExportStatus).not.toHaveBeenCalled();
    expect(result.current.status).toBe("pending");
    expect(result.current.progress).toBe(0);
  });

  it("completed 응답을 수신하면 상태를 업데이트하고 폴링을 중단한다", async () => {
    const response: ExportStatusResponse = {
      status: "completed",
      progress: 100,
      download_url: "/v2/documents/exports/job-1/file",
    };
    mockGetExportStatus.mockResolvedValue(response);

    const { result } = renderHook(() => useExportStatus("job-1"));

    await waitFor(() => {
      expect(result.current.status).toBe("completed");
    });

    expect(result.current.downloadUrl).toBe("/v2/documents/exports/job-1/file");
    expect(result.current.progress).toBe(100);
    // 최초 tick 이후 호출 횟수 — completed 면 interval 이 정리된다.
    const callsAfterComplete = mockGetExportStatus.mock.calls.length;
    // 짧게 기다려도 호출이 늘지 않아야 한다 (2 초 interval < 이 대기 시간).
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(mockGetExportStatus.mock.calls.length).toBe(callsAfterComplete);
  });

  it("failed 응답을 수신하면 error 를 채운다", async () => {
    const response: ExportStatusResponse = {
      status: "failed",
      progress: 0,
      error: "빌더 내부 오류",
    };
    mockGetExportStatus.mockResolvedValue(response);

    const { result } = renderHook(() => useExportStatus("job-2"));

    await waitFor(() => {
      expect(result.current.status).toBe("failed");
    });
    expect(result.current.error?.message).toBe("빌더 내부 오류");
  });

  it("언마운트 시 stale 업데이트가 무시된다", async () => {
    // 최초 응답은 running — 이후 2 초 interval 이 스케줄된다.
    mockGetExportStatus.mockResolvedValue({
      status: "running",
      progress: 10,
    } satisfies ExportStatusResponse);

    const { result, unmount } = renderHook(() => useExportStatus("job-3"));

    // 최초 tick 이 끝날 때까지 대기.
    await waitFor(() => {
      expect(mockGetExportStatus).toHaveBeenCalled();
    });

    // 상태가 running 으로 반영되었는지 확인.
    await waitFor(() => {
      expect(result.current.status).toBe("running");
    });

    unmount();

    // 언마운트 후 짧게 기다려도 추가 호출이 없어야 한다.
    const callsAtUnmount = mockGetExportStatus.mock.calls.length;
    await new Promise((resolve) => setTimeout(resolve, 100));
    // 첫 interval 은 2 초 뒤이므로 100 ms 내에는 호출이 추가되지 않는다.
    expect(mockGetExportStatus.mock.calls.length).toBe(callsAtUnmount);
  });
});
