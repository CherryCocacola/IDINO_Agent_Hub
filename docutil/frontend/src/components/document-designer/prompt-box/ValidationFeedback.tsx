/**
 * ValidationFeedback — 프롬프트 입력 / 생성 요청 에러 표시
 *
 * Phase 4 S1 D6 산출물. 두 가지 경로의 에러를 한 곳에 모아 사용자에게 노출한다.
 *
 * 1. 입력 검증 실패 (`inputError`): 프롬프트 빈칸, 유형 미선택 등 프런트 검증.
 *    실제로는 `PromptInput` 에서 버튼이 disabled 되므로, 기본적으로 hint 용도.
 * 2. 서버 요청 실패 (`mutationError`): `useDocumentMutation` 에서 발생한 Error.
 *    사용자에게 재시도 버튼을 제공.
 *
 * 접근성:
 *   - `role="alert"` 로 스크린리더에 즉시 전달.
 *   - 에러가 없을 때는 아무것도 렌더하지 않아 DOM 오염 방지.
 */

"use client";

import { AlertCircle, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

export interface ValidationFeedbackProps {
  /** 요청 단계에서 발생한 에러 (server / network). */
  mutationError: Error | null;
  /** 프런트 검증 에러 메시지 (hint). */
  inputError?: string | null;
  /** 재시도 버튼 콜백. 미지정 시 버튼 숨김. */
  onRetry?: () => void;
}

export function ValidationFeedback({
  mutationError,
  inputError,
  onRetry,
}: ValidationFeedbackProps) {
  if (!mutationError && !inputError) {
    return null;
  }

  return (
    <div
      role="alert"
      aria-live="polite"
      className="border-destructive/50 bg-destructive/10 text-destructive flex items-start gap-2 rounded-md border p-3 text-sm"
      data-testid="validation-feedback"
    >
      <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <div className="flex-1 space-y-2">
        {inputError && <p data-testid="validation-input-error">{inputError}</p>}
        {mutationError && (
          <>
            <p data-testid="validation-mutation-error">
              문서 생성에 실패했습니다: {mutationError.message}
            </p>
            {onRetry && (
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={onRetry}
                className="gap-1.5"
                data-testid="validation-retry"
              >
                <RefreshCw aria-hidden="true" />
                다시 시도
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ValidationFeedback;
