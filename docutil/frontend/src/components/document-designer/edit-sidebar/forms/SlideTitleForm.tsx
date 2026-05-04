/**
 * SlideTitleForm — `SlideTitle` 컴포넌트 편집 폼
 *
 * Phase 4 S1 D4 산출물. Schema 상 SlideTitle 은 `text: string` 1개 필드만 가진다
 * (부록 B). D4 작업지시서의 `subtitle?` 필드는 현행 스키마에 존재하지 않아
 * 편집 UI 에서 다루지 않는다. 부제는 별도 `SlideSubtitle` 컴포넌트로 관리된다.
 *
 * UX:
 *   - onChange → onLocalPatch(즉시 프리뷰) + onCommitPatch(500ms debounce)
 *   - blur 시 pending patch flush 는 호출자(useFormPatch.flush) 책임.
 *   - locked=true 면 전체 폼 disabled.
 */

"use client";

import type { ChangeEvent } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { SlideTitleComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type SlideTitleFormProps = FormProps<SlideTitleComponent>;

export function SlideTitleForm({ component, onLocalPatch, onCommitPatch }: SlideTitleFormProps) {
  const handleTextChange = (e: ChangeEvent<HTMLInputElement>) => {
    const next = e.target.value;
    const patch: Partial<SlideTitleComponent> = { text: next };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const inputId = `slide-title-text-${component.id}`;

  return (
    <section
      aria-label="슬라이드 제목 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="SlideTitle"
      data-component-id={component.id}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={inputId}>제목</Label>
        <Input
          id={inputId}
          value={component.text}
          onChange={handleTextChange}
          placeholder="슬라이드 제목을 입력하세요"
          disabled={component.locked}
          maxLength={200}
          autoComplete="off"
        />
      </div>
    </section>
  );
}

export default SlideTitleForm;
