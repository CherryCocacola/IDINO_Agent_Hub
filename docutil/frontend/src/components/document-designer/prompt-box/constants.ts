/**
 * constants.ts — prompt-box 내부 공용 상수
 *
 * Phase 4 S1 D6. 다른 파일에서는 이 모듈에서만 import.
 * 여기 없는 값은 각 파일의 private 상수로 둔다.
 */

import type { DocumentType } from "@/types/document-schema";

/**
 * DocumentType 7종 Select 옵션 매핑 (domain-model.md 도메인 용어 준수).
 * 순서는 사용자 관점에서 자주 쓰는 유형을 먼저 노출.
 */
export const DOCUMENT_TYPE_OPTIONS: ReadonlyArray<{
  value: DocumentType;
  label: string;
}> = [
  { value: "slide_report", label: "슬라이드 보고서" },
  { value: "docx_report", label: "서술형 보고서" },
  { value: "minutes", label: "회의록" },
  { value: "proposal", label: "제안서" },
  { value: "one_pager", label: "원페이저" },
  { value: "weekly_status", label: "주간 현황" },
  { value: "freeform_doc", label: "자유 문서" },
];

/**
 * `agent_type` 필터에 쓰는 값. 백엔드 `/agents?agent_type=...` 는 복수 값을
 * 쉼표 구분으로 받는다 (기존 reports/chat 에서 동일 패턴 사용).
 *
 * 문서 유형별로 노출할 에이전트 종류를 제한한다. 매핑되지 않는 유형은 전체 노출.
 */
export const DOCUMENT_TYPE_TO_AGENT_TYPES: Readonly<Record<DocumentType, readonly string[]>> = {
  slide_report: ["report"],
  docx_report: ["report"],
  minutes: ["minutes"],
  proposal: ["proposal"],
  one_pager: ["report"],
  weekly_status: ["report"],
  freeform_doc: ["freeform_doc", "report", "proposal", "minutes"],
};

/** 프롬프트 최대 입력 길이. 과도한 입력으로 LLM 토큰이 폭주하는 것을 방지. */
export const PROMPT_MAX_LENGTH = 4000;

/** 소스 문서 최대 선택 개수 (backend `/v2/documents` 제약과 일치). */
export const MAX_SOURCE_DOCUMENTS = 10;

/** 소스 문서 리스트 기본 조회 개수. */
export const SOURCE_DOCUMENTS_LIMIT = 50;
