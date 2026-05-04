/**
 * export-menu/types.ts — Export 메뉴 전용 UI 타입
 *
 * Phase 4 S2 D2 — 프론트 단독 시그니처 확정.
 * 백엔드 `/v2/documents/{id}/export?format=...` (POST) 와
 * `/v2/documents/exports/{job_id}` (GET) 는 S2 D5 에서 완성된다.
 *
 * 설계 메모:
 *   - `ExportFormat` 은 `types/document-schema.ts` 의 정의를 재수출해
 *     문자열 리터럴을 한 곳에서만 관리한다 (P1 Single Implementation).
 *   - `ExportJobStatus` 는 Celery 작업의 4-단계 상태 머신. `pending → running`
 *     전이는 백엔드 큐 픽업 타이밍, `running → completed|failed` 는 빌더 종료.
 *   - UI 에서 노출될 진행률은 0–100 정수. 백엔드가 공급 전이면 0 으로 고정.
 */

import type { ExportFormat as SchemaExportFormat } from "@/types/document-schema";

/** Export 요청 포맷. S5 까지 `pptx` 만 활성. HWPX/PDF 는 비활성 메뉴로 노출. */
export type ExportFormat = SchemaExportFormat;

/** Celery job 의 상태 머신. */
export type ExportJobStatus = "pending" | "running" | "completed" | "failed";

/**
 * `useExportStatus` 훅이 노출하는 viewmodel.
 *
 * - `status` 는 jobId 가 null 이거나 조회 직후에는 "pending" 로 초기화.
 * - `progress` 는 0–100 범위. 백엔드가 값을 주지 않으면 0 유지.
 * - `downloadUrl` 은 `status === "completed"` 일 때만 서버에서 발급된다.
 * - `error` 는 폴링 자체의 실패 또는 빌더의 실패 메시지(한국어 가정).
 */
export interface ExportStatusView {
  status: ExportJobStatus;
  progress: number;
  downloadUrl: string | null;
  error: Error | null;
}

/**
 * 백엔드 `GET /v2/documents/exports/{job_id}` 응답 (snake_case).
 * 훅 내부에서 `ExportStatusView` 로 camelCase 매핑한다.
 */
export interface ExportStatusResponse {
  status: ExportJobStatus;
  progress: number;
  download_url?: string | null;
  error?: string | null;
}
