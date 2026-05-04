/**
 * HeadingForm — `Heading` 컴포넌트 편집 폼
 *
 * Phase 4 S1 D4 산출물. 필수 필드: `text`(Input), `level`(1/2/3 Select).
 * level 변경 시 Heading 렌더러가 semantic 태그(h1/h2/h3)를 재생성한다.
 */

"use client";

import type { ChangeEvent } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { HeadingComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type HeadingFormProps = FormProps<HeadingComponent>;

const LEVEL_OPTIONS: { value: HeadingComponent["level"]; label: string }[] = [
  { value: 1, label: "H1 (대제목)" },
  { value: 2, label: "H2 (중제목)" },
  { value: 3, label: "H3 (소제목)" },
];

function parseLevel(value: string): HeadingComponent["level"] {
  if (value === "1" || value === "2" || value === "3") {
    return Number(value) as HeadingComponent["level"];
  }
  // 방어: 알 수 없는 값은 기본값 2 로 강제.
  return 2;
}

export function HeadingForm({ component, onLocalPatch, onCommitPatch }: HeadingFormProps) {
  const handleTextChange = (e: ChangeEvent<HTMLInputElement>) => {
    const patch: Partial<HeadingComponent> = { text: e.target.value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleLevelChange = (value: string) => {
    const patch: Partial<HeadingComponent> = { level: parseLevel(value) };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const textId = `heading-text-${component.id}`;
  const levelId = `heading-level-${component.id}`;

  return (
    <section
      aria-label="섹션 제목 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="Heading"
      data-component-id={component.id}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={textId}>제목 텍스트</Label>
        <Input
          id={textId}
          value={component.text}
          onChange={handleTextChange}
          placeholder="섹션 제목을 입력하세요"
          disabled={component.locked}
          maxLength={200}
          autoComplete="off"
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={levelId}>레벨</Label>
        <Select
          value={String(component.level)}
          onValueChange={handleLevelChange}
          disabled={component.locked}
        >
          <SelectTrigger id={levelId} aria-label="제목 레벨">
            <SelectValue placeholder="레벨을 선택하세요" />
          </SelectTrigger>
          <SelectContent>
            {LEVEL_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={String(opt.value)}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </section>
  );
}

export default HeadingForm;
