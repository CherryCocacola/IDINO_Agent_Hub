"use client";

/**
 * /preview-host — 디자이너 iframe 내부 라우트
 *
 * 역할:
 *  - DesignerShell 의 `<iframe src="/preview-host">` 가 로드하는 Next.js 라우트
 *  - 부모 창(PreviewPane)에서 postMessage 로 전달하는 DocumentSchema 를
 *    `PreviewHost` 컴포넌트가 수신·렌더하고, 사용자가 컴포넌트를 클릭하면
 *    `docutil/element-select` 메시지를 부모로 전송한다.
 *
 * 왜 별도 라우트인가:
 *  - `sandbox="allow-scripts allow-same-origin"` + same-origin 라우트 전략
 *    (phase1_decisions.md Q10 참조)
 *  - Next.js 번들 청크를 부모와 공유해 컴포넌트 추가 시 번들 증분을 최소화
 */

import { PreviewHost } from "@/components/document-designer/preview-pane/preview-host";
import { DEFAULT_DESIGN_TOKENS } from "@/components/document-designer/design-token-picker/tokens";
import type { DocumentSchema } from "@/types/document-schema";

/**
 * 최소 빈 Schema — 부모가 schema-patch-local 메시지로 실제 Schema 를 주입하기 전
 * 초기 상태. pages 는 빈 배열이라 아무 내용도 렌더되지 않는다.
 */
const EMPTY_INITIAL_SCHEMA = {
  schema_version: 1,
  document_id: "00000000-0000-0000-0000-000000000000",
  type: "slide_report",
  mode: "free_generation",
  template_id: null,
  design_tokens: DEFAULT_DESIGN_TOKENS,
  pages: [],
  metadata: {
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    generated_by_user_id: null,
    organization_id: null,
    llm_provider: null,
    llm_model: null,
    token_usage: null,
    citations: [],
  },
} as unknown as DocumentSchema;

export default function PreviewHostPage() {
  return <PreviewHost initialSchema={EMPTY_INITIAL_SCHEMA} />;
}
