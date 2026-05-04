/**
 * PromptBox — Designer Shell 좌측 상단 문서 생성 프롬프트 박스
 *
 * Phase 4 S1 D6 산출물 (roadmap §2.1 S1 D6).
 *
 * 역할:
 *   - 자연어 프롬프트 + DocumentType + 기준문서 + 에이전트 입력을 받아
 *     `POST /v2/documents` (Mode A) 를 호출.
 *   - 성공 시 반환된 `DocumentSchema` 를 상위에 전달하고, 선택적으로 `<PreviewPane>`
 *     iframe 에 초기 페이지 patch 를 주입한다.
 *
 * D6 범위 외 (향후 Story 에서 연결):
 *   - D7: 백엔드 `router.py` 연동 (현재 훅은 시그니처 완성 상태).
 *   - D8: PATCH (updatePage) 훅 확장.
 *   - 컴포넌트 선택 상태에서 regenerate-component 전환 (README §2) — D7/D8 이후.
 *
 * 제약 (CLAUDE.md / anti-patterns.md):
 *   - apiClient 외 fetch 금지, hex 하드코딩 금지, 절대 import(@/..) 사용.
 *   - SWR / React Query 미사용 (Q10 결정).
 */

"use client";

import type { RefObject } from "react";
import { useCallback, useState } from "react";

import { isApiError } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";
import type { DocumentSchema, DocumentType, UUID } from "@/types/document-schema";

import type { PreviewPaneHandle } from "../preview-pane";

import { PromptInput } from "./PromptInput";
import { PromptOptions } from "./PromptOptions";
import { useDocumentMutation } from "./useDocumentMutation";
import { ValidationFeedback } from "./ValidationFeedback";

// ─── Props ────────────────────────────────────────────────────────────────

export interface PromptBoxProps {
  /** 생성 성공 시 호출. 상위에서 useDocument 캐시/state 에 주입. */
  onDocumentGenerated: (document: DocumentSchema) => void;
  /**
   * PreviewPane ref. 성공 시 첫 페이지 schema patch 를 iframe 으로 전송한다.
   * 선택사항 — 미지정 시 postMessage 전송은 생략.
   */
  previewPaneRef?: RefObject<PreviewPaneHandle | null>;
  /** 초기 문서 유형. 기본값은 slide_report. */
  defaultDocumentType?: DocumentType;
  /** 컨테이너 클래스 override (Designer Shell grid 에서 조정). */
  className?: string;
  dataTestId?: string;
}

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────

export function PromptBox({
  onDocumentGenerated,
  previewPaneRef,
  defaultDocumentType = "slide_report",
  className,
  dataTestId,
}: PromptBoxProps) {
  const [prompt, setPrompt] = useState("");
  const [documentType, setDocumentType] = useState<DocumentType>(defaultDocumentType);
  const [sourceDocumentIds, setSourceDocumentIds] = useState<UUID[]>([]);
  const [agentId, setAgentId] = useState<UUID | null>(null);

  const mutation = useDocumentMutation();
  const { toast } = useToast();

  const handleGenerate = useCallback(async () => {
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt || mutation.isPending) return;

    let result: DocumentSchema;
    try {
      result = await mutation.mutateAsync({
        prompt: trimmedPrompt,
        documentType,
        sourceDocumentIds,
        agentId,
      });
    } catch (err) {
      // Phase 4 S3 D5: 이미지 쿼터 초과 (403 + 한국어 "쿼터" 감지) 는
      // 일반 ValidationFeedback 위에 전용 토스트를 띄워 가시성 향상.
      // 이외 에러는 mutation.error → ValidationFeedback 경로 그대로 유지.
      if (isApiError(err) && err.status === 403 && err.detail.includes("쿼터")) {
        toast({
          title: "이미지 생성 쿼터 초과",
          description: err.detail,
          variant: "destructive",
        });
      }
      return;
    }

    // 상위 콜백 — state 반영.
    onDocumentGenerated(result);

    // 첫 페이지를 iframe 프리뷰에 주입 (없으면 생략).
    const firstPage = result.pages?.[0];
    if (firstPage && previewPaneRef?.current) {
      previewPaneRef.current.sendSchemaPatch({
        patchType: "page",
        pageId: firstPage.id,
        data: firstPage,
      });
    }
  }, [
    agentId,
    documentType,
    mutation,
    onDocumentGenerated,
    previewPaneRef,
    prompt,
    sourceDocumentIds,
    toast,
  ]);

  const handleRetry = useCallback(() => {
    mutation.reset();
    void handleGenerate();
  }, [handleGenerate, mutation]);

  return (
    <section
      aria-label="문서 생성 프롬프트"
      className={className ?? "space-y-4 p-4"}
      data-testid={dataTestId ?? "prompt-box"}
    >
      <PromptInput
        value={prompt}
        onChange={setPrompt}
        documentType={documentType}
        onDocumentTypeChange={setDocumentType}
        isLoading={mutation.isPending}
        onSubmit={handleGenerate}
      />

      <PromptOptions
        documentType={documentType}
        sourceDocumentIds={sourceDocumentIds}
        onSourceChange={setSourceDocumentIds}
        agentId={agentId}
        onAgentChange={setAgentId}
        disabled={mutation.isPending}
      />

      <ValidationFeedback mutationError={mutation.error} onRetry={handleRetry} />
    </section>
  );
}

export default PromptBox;
