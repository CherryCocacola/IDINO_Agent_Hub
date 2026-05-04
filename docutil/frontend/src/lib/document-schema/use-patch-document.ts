/**
 * use-patch-document.ts — PATCH /v2/documents/{id} 전용 mutation 훅 barrel
 *
 * Phase 4 S1 D8 산출물. 실제 구현은 `use-document.ts` 에 모여 있다 (같은 훅
 * 가족을 한 파일에 두어 테스트/리뷰가 용이). 본 파일은 roadmap §2.1 S1 D8 의
 * 파일 구조 요건을 만족시키기 위한 barrel.
 *
 * `useFormPatch.onPatch` 콜백과 연결하면 edit-sidebar 폼 변경이 500ms debounce
 * 후 서버로 전송된다:
 *
 *   const { patchComponent } = usePatchDocument(documentId);
 *   const formPatch = useFormPatch(componentId, pageId, {
 *     onPatch: ({ patch }) => patchComponent(pageId, componentId, patch as Partial<Component>),
 *   });
 *
 * @see docs/phase1_decisions.md v1.2 Q10
 * @see docs/phase3_execution_roadmap.md §2.1 S1 D8
 */

export {
  usePatchDocument,
  type UsePatchDocumentResult,
  type DocumentPatchBody,
} from "./use-document";
