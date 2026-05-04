/**
 * documents-v2.ts — DocumentSchema API 클라이언트 (Phase 1 시그니처 스켈레톤)
 *
 * 기준: docs/phase1_architecture.md §4.3 (데이터 흐름도), §5.4 (부분 재생성).
 *
 * **반드시 준수할 원칙** (anti-patterns.md):
 *   - 절대 `fetch("http://.../api/...")`를 직접 호출하지 않는다.
 *     모든 호출은 `@/lib/api/client`의 `apiClient`를 경유한다.
 *   - API 경로는 백엔드 `modules/documents_v2/router.py`의 prefix `/v2/documents`와 일치.
 *   - 응답은 snake_case로 들어오며, 필요 시 훅 레이어에서 camelCase 매핑한다
 *     (본 파일에서는 백엔드 snake_case 타입을 그대로 반환).
 *
 * 본 파일의 모든 함수는 Phase 1에서는 **시그니처만 확정**한다.
 * Phase 4 S1 DoD: `generateDocument`, `fetchDocument`, `exportDocument` 3개 함수 완성.
 */

import type { ExportStatusResponse } from "@/components/document-designer/export-menu/types";
import apiClient from "@/lib/api/client";
import type {
  ExportDocumentInput,
  ExportDocumentResult,
  FillTemplateInput,
  GenerateDocumentInput,
  RegenerateComponentInput,
  RegeneratePageInput,
  UpdatePageInput,
} from "@/lib/document-schema/use-document";
import type { Component, DocumentSchema, ExportFormat, Page, UUID } from "@/types/document-schema";

// ─── 공통 경로 상수 (constants 모듈로 분리하지 않는 이유: 이 파일에서만 쓰인다) ───

/** 백엔드 documents_v2 라우터 prefix. 전역 /api/v1은 apiClient가 붙여준다. */
const DOCUMENTS_V2_BASE = "/v2/documents";

// ─── 1. 전체 문서 생성 (Mode A) ─────────────────────────────────────────────

/**
 * Mode A 자유 생성. LLM이 Structured Output으로 DocumentSchema 전체를 구성.
 *
 * - 백엔드: POST /v2/documents (202 Accepted + DocumentV2Response 반환)
 * - 동기 HTTP 경로로 동작한다 (서비스 레이어에서 LLM 호출 완료 후 응답). 5~15초 소요.
 * - 긴 생성용 SSE 는 Phase 4 S7 예정.
 *
 * 요청 / 응답 매핑
 * ----------------
 * - FE input ``type`` → BE ``document_type``
 * - FE ``agent_id`` 가 null 이면 필드 자체를 누락해 백엔드의 ``extra='forbid'`` 를 피한다.
 * - BE 응답 ``DocumentV2Response.document_schema`` 가 실제 DocumentSchema.
 *
 * @returns 생성된 DocumentSchema. document_id 로 `/designer/[documentId]` 이동.
 */
export async function generateDocument(input: GenerateDocumentInput): Promise<DocumentSchema> {
  // 백엔드 GenerateDocumentRequest 에 맞춰 payload 구성. null 필드는 누락한다
  // (Pydantic ``extra='forbid'`` + ``Optional`` 필드는 미포함 시 None 기본값).
  const payload: Record<string, unknown> = {
    mode: "free_generation",
    document_type: input.type,
    prompt: input.prompt,
  };
  if (input.source_document_ids && input.source_document_ids.length > 0) {
    payload.source_document_ids = input.source_document_ids;
  }
  if (input.agent_id) {
    payload.agent_id = input.agent_id;
  }

  // 백엔드 응답은 DocumentV2Response — 최상위는 DB 메타이고 document_schema 필드가
  // 실제 Pydantic DocumentSchema JSON (id/pages/metadata 등).
  const response = await apiClient.post<{
    id: string;
    document_schema: DocumentSchema;
  }>(DOCUMENTS_V2_BASE, payload);
  return response.document_schema;
}

// ─── 2. 템플릿 기반 생성 (Mode B) ───────────────────────────────────────────

/**
 * Mode B 양식 채우기. 템플릿의 DocumentSchema에서 `locked=false` 슬롯만 LLM이 채운다.
 */
export async function fillTemplate(_input: FillTemplateInput): Promise<DocumentSchema> {
  // TODO(Phase 4 S4):
  //   return apiClient.post<DocumentSchema>(DOCUMENTS_V2_BASE, {
  //     mode: "template_fill",
  //     template_id: _input.template_id,
  //     slot_inputs: _input.slot_inputs,
  //     source_document_ids: _input.source_document_ids ?? [],
  //   });
  throw new Error(`fillTemplate: Phase 4 S4에서 구현 예정 (${DOCUMENTS_V2_BASE})`);
}

// ─── 3. 단건 조회 ──────────────────────────────────────────────────────────

export async function fetchDocument(_documentId: UUID): Promise<DocumentSchema> {
  // TODO(Phase 4 S1):
  //   return apiClient.get<DocumentSchema>(`${DOCUMENTS_V2_BASE}/${_documentId}`);
  throw new Error("fetchDocument: Phase 4 S1에서 구현 예정");
}

// ─── 4. Page 덮어쓰기 (편집 사이드바 저장) ───────────────────────────────────

export async function updatePage(_input: UpdatePageInput): Promise<DocumentSchema> {
  // TODO(Phase 4 S1):
  //   return apiClient.put<DocumentSchema>(
  //     `${DOCUMENTS_V2_BASE}/${_input.document_id}/pages/${_input.page_id}`,
  //     _input.page,
  //   );
  throw new Error("updatePage: Phase 4 S1에서 구현 예정");
}

// ─── 5. 부분 재생성 ─────────────────────────────────────────────────────────

export async function regenerateComponent(_input: RegenerateComponentInput): Promise<Component> {
  // TODO(Phase 4 S7):
  //   return apiClient.post<Component>(
  //     `${DOCUMENTS_V2_BASE}/${_input.document_id}/regenerate-component`,
  //     {
  //       page_id: _input.page_id,
  //       component_id: _input.component_id,
  //       instruction: _input.instruction,
  //     },
  //   );
  throw new Error("regenerateComponent: Phase 4 S7에서 구현 예정");
}

export async function regeneratePage(_input: RegeneratePageInput): Promise<Page> {
  // TODO(Phase 4 S7):
  //   return apiClient.post<Page>(
  //     `${DOCUMENTS_V2_BASE}/${_input.document_id}/regenerate-page`,
  //     {
  //       page_id: _input.page_id,
  //       instruction: _input.instruction,
  //       preserve_component_ids: _input.preserve_component_ids ?? [],
  //     },
  //   );
  throw new Error("regeneratePage: Phase 4 S7에서 구현 예정");
}

// ─── 6. 삭제 ───────────────────────────────────────────────────────────────

export async function deleteDocument(_documentId: UUID): Promise<void> {
  // TODO(Phase 4 S1):
  //   return apiClient.delete<void>(`${DOCUMENTS_V2_BASE}/${_documentId}`);
  throw new Error("deleteDocument: Phase 4 S1에서 구현 예정");
}

// ─── 7. Export (Celery 비동기 + 폴링) ───────────────────────────────────────

/**
 * 파일 포맷 Export.
 *
 * 흐름 (phase1_architecture.md §4.3·§4.4):
 *   1) POST `/v2/documents/{id}/export?format=pptx` → `{ job_id }`
 *   2) GET `/v2/documents/exports/{job_id}` 폴링(1초 간격, 최대 120초)
 *   3) 상태 `completed`이면 `{ download_url, degraded_components }` 반환.
 *
 * HTML 포맷은 서버 왕복 없이 클라이언트에서 `DocumentRenderer`를 serialize하는 것이 원칙
 * (Phase 4 S7 결정 예정). 현재 스켈레톤은 5종 모두 서버 경로를 가정.
 */
export async function exportDocument(_input: ExportDocumentInput): Promise<ExportDocumentResult> {
  // TODO(Phase 4 S1):
  //   const { job_id } = await apiClient.post<{ job_id: string }>(
  //     `${DOCUMENTS_V2_BASE}/${_input.document_id}/export`,
  //     { format: _input.format },
  //   );
  //   return pollExportJob(job_id);
  throw new Error("exportDocument: Phase 4 S1에서 구현 예정");
}

/**
 * Export job 폴링 유틸. exportDocument 내부에서 호출 (Phase 4 S1 구현).
 * @internal
 */
export async function pollExportJob(
  _jobId: string,
  _options?: { intervalMs?: number; timeoutMs?: number },
): Promise<ExportDocumentResult> {
  // TODO(Phase 4 S1): setInterval + AbortController로 폴링 구현.
  throw new Error("pollExportJob: Phase 4 S1에서 구현 예정");
}

// ─── 7-b. Export (저수준, Phase 4 S2 D2 UI 훅 연계용) ────────────────────────
//
// `exportDocument` 는 "요청 + 폴링 + downloadUrl" 을 한 번에 반환하는 고수준
// API 다. export-menu UI 는 진행률/취소 UX 를 위해 두 단계를 분리해서 호출
// 해야 하므로 아래 저수준 쌍을 추가로 제공한다. 백엔드 엔드포인트 자체는
// Phase 4 S2 D5 에서 완성 예정 — 현재는 호출 시 404/501 이 반환될 수 있다.

/**
 * Celery export 작업을 큐잉한다.
 *
 * `POST /v2/documents/{id}/export?format=pptx` → `{ job_id }`.
 * 실제 파일은 `getExportStatus(job_id).download_url` 로 접근한다.
 */
export async function requestExportJob(params: {
  documentId: UUID;
  format: ExportFormat;
}): Promise<{ jobId: string }> {
  const response = await apiClient.post<{ job_id: string }>(
    `${DOCUMENTS_V2_BASE}/${params.documentId}/export`,
    { format: params.format },
  );
  return { jobId: response.job_id };
}

/**
 * export job 의 현재 상태를 조회한다.
 *
 * `GET /v2/documents/exports/{job_id}` — snake_case 응답.
 * `useExportStatus` 훅이 2 초 간격으로 호출한다.
 */
export async function getExportStatus(jobId: string): Promise<ExportStatusResponse> {
  return apiClient.get<ExportStatusResponse>(`${DOCUMENTS_V2_BASE}/exports/${jobId}`);
}

// ─── 8. 지원 포맷 목록 (UI 메뉴 렌더링) ──────────────────────────────────────

/**
 * Export 메뉴에 노출할 포맷 목록. HWP는 제외(techspec §7.3.1).
 * `hwpx` 항목은 Phase 4 S5 전까지 비활성(disabled=true)으로 노출.
 */
export const EXPORT_FORMATS: Array<{
  format: ExportFormat;
  label: string;
  disabled: boolean;
  hint?: string;
}> = [
  { format: "pptx", label: "PowerPoint (PPTX)", disabled: false },
  { format: "docx", label: "Word (DOCX)", disabled: false },
  {
    format: "hwpx",
    label: "한글 HWPX",
    disabled: true,
    hint: "Phase 4 S5부터 지원 (한컴 2020+ 에서 열림)",
  },
  { format: "pdf", label: "PDF", disabled: false },
  { format: "html", label: "HTML", disabled: false },
];
