/**
 * QuoteForm — `Quote` 컴포넌트 편집 폼
 *
 * Phase 4 S3 D1 산출물. 필수 필드:
 *   - `text`(Textarea): 인용 본문. 여러 줄 허용.
 *   - `author`(Input, optional): 출처. 빈 문자열은 `null` 로 정규화해 patch 전송.
 *
 * UX:
 *   - 본문 변경은 Textarea, 출처는 Input (한 줄).
 *   - locked=true 면 전체 폼 disabled.
 */

"use client";

import type { ChangeEvent } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { QuoteComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type QuoteFormProps = FormProps<QuoteComponent>;

export function QuoteForm({ component, onLocalPatch, onCommitPatch }: QuoteFormProps) {
  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const patch: Partial<QuoteComponent> = { text: e.target.value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleAuthorChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // 빈 문자열은 schema 상 `null` 로 정규화 (Pydantic Optional[str] 호환).
    const nextAuthor = value.trim().length === 0 ? null : value;
    const patch: Partial<QuoteComponent> = { author: nextAuthor };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const textId = `quote-text-${component.id}`;
  const authorId = `quote-author-${component.id}`;

  return (
    <section
      aria-label="인용 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="Quote"
      data-component-id={component.id}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={textId}>인용 본문</Label>
        <Textarea
          id={textId}
          value={component.text}
          onChange={handleTextChange}
          placeholder="인용 내용을 입력하세요"
          disabled={component.locked}
          rows={4}
          maxLength={1000}
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={authorId}>출처</Label>
        <Input
          id={authorId}
          value={component.author ?? ""}
          onChange={handleAuthorChange}
          placeholder="선택 입력 (예: 홍길동, 2026년)"
          disabled={component.locked}
          maxLength={120}
          autoComplete="off"
        />
        <span style={FORM_HINT_STYLE}>비워두면 출처 라인이 표시되지 않습니다.</span>
      </div>
    </section>
  );
}

export default QuoteForm;
