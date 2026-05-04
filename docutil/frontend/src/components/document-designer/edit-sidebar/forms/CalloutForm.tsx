/**
 * CalloutForm — `Callout` 컴포넌트 편집 폼
 *
 * Phase 4 S3 D2 산출물. 필수 필드:
 *   - `text`(Textarea): 강조 메시지 본문. 2~3줄 권장.
 *   - `variant`(Select): info / warning / success / danger 중 하나.
 *
 * UX:
 *   - variant 변경 시 Callout 프리뷰의 배경·아이콘이 즉시 바뀐다(낙관적).
 *   - locked=true 면 전체 폼 disabled.
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
import type { CalloutComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type CalloutFormProps = FormProps<CalloutComponent>;

const VARIANT_OPTIONS: { value: CalloutComponent["variant"]; label: string }[] = [
  { value: "info", label: "정보 (파랑)" },
  { value: "warning", label: "주의 (주황)" },
  { value: "success", label: "성공 (초록)" },
  { value: "danger", label: "위험 (빨강)" },
];

function isVariant(value: string): value is CalloutComponent["variant"] {
  return value === "info" || value === "warning" || value === "success" || value === "danger";
}

export function CalloutForm({ component, onLocalPatch, onCommitPatch }: CalloutFormProps) {
  const handleTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const patch: Partial<CalloutComponent> = { text: e.target.value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleVariantChange = (value: string) => {
    if (!isVariant(value)) return;
    const patch: Partial<CalloutComponent> = { variant: value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const textId = `callout-text-${component.id}`;
  const variantId = `callout-variant-${component.id}`;

  return (
    <section
      aria-label="강조 박스 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="Callout"
      data-component-id={component.id}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={textId}>강조 메시지</Label>
        <Textarea
          id={textId}
          value={component.text}
          onChange={handleTextChange}
          placeholder="독자에게 전달할 강조 문구"
          disabled={component.locked}
          rows={3}
          maxLength={500}
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={variantId}>유형</Label>
        <Select
          value={component.variant}
          onValueChange={handleVariantChange}
          disabled={component.locked}
        >
          <SelectTrigger id={variantId} aria-label="강조 유형">
            <SelectValue placeholder="유형을 선택하세요" />
          </SelectTrigger>
          <SelectContent>
            {VARIANT_OPTIONS.map((opt) => (
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

export default CalloutForm;
