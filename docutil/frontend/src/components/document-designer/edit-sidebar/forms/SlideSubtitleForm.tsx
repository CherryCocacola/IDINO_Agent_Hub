/**
 * SlideSubtitleForm — `SlideSubtitle` 컴포넌트 편집 폼
 *
 * Phase 4 S3 D1 산출물. Schema 상 SlideSubtitle 은 `text: string` 1개 필드만 가진다
 * (부록 B). 부제는 본문 계열이라 줄바꿈 편집이 있을 수 있어 Input 대신 Textarea 를
 * 사용해 2줄 가량 보여준다.
 *
 * UX:
 *   - onChange → onLocalPatch(즉시 프리뷰) + onCommitPatch(500ms debounce)
 *   - locked=true 면 전체 폼 disabled.
 */

"use client";

import type { ChangeEvent } from "react";

import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { SlideSubtitleComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type SlideSubtitleFormProps = FormProps<SlideSubtitleComponent>;

export function SlideSubtitleForm({
  component,
  onLocalPatch,
  onCommitPatch,
}: SlideSubtitleFormProps) {
  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const patch: Partial<SlideSubtitleComponent> = { text: e.target.value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const inputId = `slide-subtitle-text-${component.id}`;

  return (
    <section
      aria-label="슬라이드 부제 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="SlideSubtitle"
      data-component-id={component.id}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={inputId}>부제</Label>
        <Textarea
          id={inputId}
          value={component.text}
          onChange={handleTextChange}
          placeholder="부제 텍스트를 입력하세요"
          disabled={component.locked}
          rows={2}
          maxLength={300}
        />
      </div>
    </section>
  );
}

export default SlideSubtitleForm;
