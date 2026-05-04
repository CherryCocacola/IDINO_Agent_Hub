/**
 * use-component-regeneration.ts — 컴포넌트 부분 재생성 훅 (S7 엔드포인트 대비 스텁)
 *
 * Phase 4 S1 D8 산출물. 실제 LLM 재생성 엔드포인트
 * (`POST /v2/documents/{id}/regenerate-component` 및 `.../regenerate-page`) 는
 * S7 에서 구현 예정. D8 에서는 mutation state 와 시그니처만 확립한다.
 *
 * 구현 본체는 `use-document.ts` 에 모여 있다. 본 파일은 Roadmap §2.1 S1 D8 의
 * 파일 구조를 맞추기 위한 barrel export — 호출자는
 *   `import { useComponentRegeneration } from "@/lib/document-schema/use-component-regeneration"`
 * 또는
 *   `import { useComponentRegeneration } from "@/lib/document-schema"`
 * 중 편한 쪽을 사용할 수 있다.
 *
 * @see docs/phase3_execution_roadmap.md §2.1 S1 D8
 */

export {
  useComponentRegeneration,
  type UseComponentRegenerationResult,
  type RegenerateComponentInput,
  type RegeneratePageInput,
} from "./use-document";
