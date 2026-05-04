/**
 * PromptInput — PromptBox 상단 입력 영역
 *
 * Phase 4 S1 D6 산출물. 자연어 프롬프트 textarea + DocumentType Select + "생성" 버튼.
 *
 * UX 규약 (D6 작업지시서):
 *   - 빈 프롬프트 → "생성" 버튼 disabled.
 *   - 로딩 중 → 입력 disable + 버튼 스피너.
 *   - Ctrl/Cmd + Enter → 제출 트리거 (Shift+Enter 는 줄바꿈 기본 동작).
 *
 * 접근성:
 *   - textarea, select 는 `<Label htmlFor>` 로 연결.
 *   - 로딩 중 aria-busy=true.
 */

"use client";

import { Loader2, Sparkles } from "lucide-react";
import type { KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { DocumentType } from "@/types/document-schema";

import { DOCUMENT_TYPE_OPTIONS, PROMPT_MAX_LENGTH } from "./constants";

export interface PromptInputProps {
  value: string;
  onChange: (next: string) => void;
  documentType: DocumentType;
  onDocumentTypeChange: (next: DocumentType) => void;
  isLoading: boolean;
  onSubmit: () => void;
  /** 외부에서 버튼 disable 조건 추가 (예: validation 실패). 기본은 내부 규칙만 사용. */
  disabled?: boolean;
}

/** macOS 는 Cmd, 그 외는 Ctrl — 둘 다 받아 제출. */
function isSubmitShortcut(event: KeyboardEvent<HTMLTextAreaElement>): boolean {
  return event.key === "Enter" && (event.ctrlKey || event.metaKey);
}

export function PromptInput({
  value,
  onChange,
  documentType,
  onDocumentTypeChange,
  isLoading,
  onSubmit,
  disabled,
}: PromptInputProps) {
  const trimmed = value.trim();
  const isEmpty = trimmed.length === 0;
  const submitDisabled = isEmpty || isLoading || Boolean(disabled);

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (isSubmitShortcut(event)) {
      event.preventDefault();
      if (!submitDisabled) {
        onSubmit();
      }
    }
  };

  return (
    <section
      aria-label="문서 생성 프롬프트"
      aria-busy={isLoading || undefined}
      className="space-y-3"
      data-testid="prompt-input"
    >
      <div className="space-y-1.5">
        <Label htmlFor="prompt-box-textarea">프롬프트</Label>
        <Textarea
          id="prompt-box-textarea"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="생성할 문서의 주제, 목적, 주요 내용을 자연어로 입력하세요. (Ctrl + Enter 로 생성)"
          disabled={isLoading}
          maxLength={PROMPT_MAX_LENGTH}
          rows={5}
          className="resize-none"
          data-testid="prompt-textarea"
        />
      </div>

      <div className="flex items-end gap-2">
        <div className="flex-1 space-y-1.5">
          <Label htmlFor="prompt-box-document-type">문서 유형</Label>
          <Select
            value={documentType}
            onValueChange={(next) => onDocumentTypeChange(next as DocumentType)}
            disabled={isLoading}
          >
            <SelectTrigger id="prompt-box-document-type" data-testid="document-type-select">
              <SelectValue placeholder="문서 유형 선택" />
            </SelectTrigger>
            <SelectContent>
              {DOCUMENT_TYPE_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button
          type="button"
          onClick={onSubmit}
          disabled={submitDisabled}
          data-testid="prompt-submit"
          aria-label="문서 생성"
          className="gap-1.5"
        >
          {isLoading ? (
            <>
              <Loader2 className="animate-spin" aria-hidden="true" />
              <span>생성 중</span>
            </>
          ) : (
            <>
              <Sparkles aria-hidden="true" />
              <span>생성</span>
            </>
          )}
        </Button>
      </div>
    </section>
  );
}

export default PromptInput;
