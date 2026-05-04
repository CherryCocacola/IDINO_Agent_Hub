/**
 * ParagraphForm — `Paragraph` 컴포넌트 편집 폼
 *
 * Phase 4 S1 D4 산출물. 필수 필드: `text`(Textarea), `emphasis`(normal/bold/italic).
 * 한글 본문 특성상 줄바꿈 편집이 잦으므로 Input 이 아닌 Textarea 를 사용한다.
 */

"use client";

import type { ChangeEvent } from "react";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { ParagraphComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type ParagraphFormProps = FormProps<ParagraphComponent>;

const EMPHASIS_OPTIONS: { value: ParagraphComponent["emphasis"]; label: string }[] = [
  { value: "normal", label: "일반" },
  { value: "bold", label: "굵게" },
  { value: "italic", label: "기울임" },
];

function isEmphasis(value: string): value is ParagraphComponent["emphasis"] {
  return value === "normal" || value === "bold" || value === "italic";
}

export function ParagraphForm({ component, onLocalPatch, onCommitPatch }: ParagraphFormProps) {
  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const patch: Partial<ParagraphComponent> = { text: e.target.value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleEmphasisChange = (value: string) => {
    if (!isEmphasis(value)) return;
    const patch: Partial<ParagraphComponent> = { emphasis: value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const textId = `paragraph-text-${component.id}`;
  const emphasisId = `paragraph-emphasis-${component.id}`;

  return (
    <section
      aria-label="본문 단락 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="Paragraph"
      data-component-id={component.id}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={textId}>본문</Label>
        <Textarea
          id={textId}
          value={component.text}
          onChange={handleTextChange}
          placeholder="단락 내용을 입력하세요"
          disabled={component.locked}
          rows={5}
          maxLength={4000}
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={emphasisId}>강조</Label>
        <Select
          value={component.emphasis}
          onValueChange={handleEmphasisChange}
          disabled={component.locked}
        >
          <SelectTrigger id={emphasisId} aria-label="본문 강조">
            <SelectValue placeholder="강조 스타일" />
          </SelectTrigger>
          <SelectContent>
            {EMPHASIS_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </section>
  );
}

export default ParagraphForm;
