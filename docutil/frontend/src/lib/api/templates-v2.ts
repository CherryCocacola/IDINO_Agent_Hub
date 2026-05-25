/**
 * templates-v2.ts — DocumentV2Template (Mode B 양식 채우기 템플릿) API 클라이언트
 *
 * Phase 4 S4 D4 산출물. `(admin)/template-designer/` 라우트에서 사용한다.
 *
 * 백엔드 매핑
 * ----------
 * 본 클라이언트는 향후 추가될 `tb_documents_v2_templates` CRUD 라우트 (예:
 * `/v2/templates`) 를 호출한다. D4 단계에서는 라우트 구현이 부분적이므로
 * 호출 시 404/501 이 반환될 수 있다. FE 는 이 경우 read-only placeholder UI
 * 로 fallback 한다.
 *
 * 제약 (CLAUDE.md / anti-patterns.md):
 *   - `fetch(...)` 직접 호출 금지 — `apiClient` 만 사용.
 *   - 응답은 snake_case 그대로 반환 (boundary 매핑은 호출자 책임).
 */

import apiClient from "@/lib/api/client";
import type { DocumentSchema, UUID } from "@/types/document-schema";

/** 백엔드 documents_v2 templates prefix. apiClient 가 `/api/v1` 을 자동으로 붙인다. */
const TEMPLATES_V2_BASE = "/v2/templates";

// ─── 타입 ────────────────────────────────────────────────────────────────────

/**
 * `tb_documents_v2_templates` 한 행을 표현하는 응답 모델.
 * 백엔드 모델 컬럼과 1:1 (snake_case).
 */
export interface DocumentV2Template {
  id: UUID;
  organization_id: UUID;
  name: string;
  description: string | null;
  document_type: string;
  schema_version: number;
  /** DocumentSchema skeleton — 일부 컴포넌트는 locked=true 로 잠겨 있다. */
  skeleton_schema: DocumentSchema;
  /** 슬롯 메타. category in {session_auto, user_input, ai_generated}. */
  slot_definitions: Array<{
    anchor: string;
    category: string;
    description: string | null;
    default_value: string | null;
    required: boolean;
  }> | null;
  sample_prompt: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ListTemplatesParams {
  /** 활성 템플릿만 조회. 기본 true. */
  is_active?: boolean;
  /** document_type 필터 (예: "minutes"). */
  document_type?: string;
  limit?: number;
  offset?: number;
}

export interface PaginatedTemplatesResponse {
  items: DocumentV2Template[];
  total: number;
  limit: number;
  offset: number;
}

export interface CreateTemplateInput {
  name: string;
  description?: string | null;
  document_type: string;
  skeleton_schema: DocumentSchema;
  slot_definitions?: DocumentV2Template["slot_definitions"];
  sample_prompt?: string | null;
  is_active?: boolean;
}

export interface UpdateTemplateInput {
  name?: string;
  description?: string | null;
  skeleton_schema?: DocumentSchema;
  slot_definitions?: DocumentV2Template["slot_definitions"];
  sample_prompt?: string | null;
  is_active?: boolean;
}

// ─── 1. 단건 조회 ────────────────────────────────────────────────────────────

export async function getTemplate(templateId: UUID): Promise<DocumentV2Template> {
  return apiClient.get<DocumentV2Template>(`${TEMPLATES_V2_BASE}/${templateId}`);
}

// ─── 2. 목록 조회 ────────────────────────────────────────────────────────────

export async function listTemplates(
  params: ListTemplatesParams = {},
): Promise<PaginatedTemplatesResponse> {
  const query: Record<string, string> = {};
  if (params.is_active !== undefined) query.is_active = String(params.is_active);
  if (params.document_type) query.document_type = params.document_type;
  if (params.limit !== undefined) query.limit = String(params.limit);
  if (params.offset !== undefined) query.offset = String(params.offset);
  return apiClient.get<PaginatedTemplatesResponse>(TEMPLATES_V2_BASE, query);
}

// ─── 3. 생성 ─────────────────────────────────────────────────────────────────

export async function createTemplate(input: CreateTemplateInput): Promise<DocumentV2Template> {
  return apiClient.post<DocumentV2Template>(TEMPLATES_V2_BASE, input);
}

// ─── 4. 수정 ─────────────────────────────────────────────────────────────────

export async function updateTemplate(
  templateId: UUID,
  input: UpdateTemplateInput,
): Promise<DocumentV2Template> {
  return apiClient.patch<DocumentV2Template>(`${TEMPLATES_V2_BASE}/${templateId}`, input);
}

// ─── 5. 비활성화 (소프트 삭제) ───────────────────────────────────────────────

export async function deactivateTemplate(templateId: UUID): Promise<DocumentV2Template> {
  return apiClient.patch<DocumentV2Template>(`${TEMPLATES_V2_BASE}/${templateId}`, {
    is_active: false,
  });
}
