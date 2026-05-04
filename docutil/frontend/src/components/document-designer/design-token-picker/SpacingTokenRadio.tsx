/**
 * SpacingTokenRadio — spacing 토큰 3종 라디오 선택 (compact/normal/relaxed)
 *
 * Phase 4 S1 D5. 프로젝트 shadcn/ui 에 RadioGroup 이 아직 없어 네이티브
 * `<input type="radio">` + `<label>` 조합을 `role="radiogroup"` 컨테이너로
 * 감싼다. 키보드 접근성은 브라우저 기본 동작(Tab/Space/Arrow)으로 충족.
 */

"use client";

import { useCallback, type ChangeEvent } from "react";

import { cn } from "@/lib/utils/cn";
import type { DesignTokens } from "@/types/document-schema";

import { SPACING_OPTIONS } from "./tokens";

export interface SpacingTokenRadioProps {
  value: DesignTokens["spacing"];
  onPreview: (value: DesignTokens["spacing"]) => void;
  onCommit: (value: DesignTokens["spacing"]) => void;
  disabled?: boolean;
}

function parseSpacing(raw: string): DesignTokens["spacing"] | null {
  if (raw === "compact" || raw === "normal" || raw === "relaxed") return raw;
  return null;
}

export function SpacingTokenRadio({
  value,
  onPreview,
  onCommit,
  disabled = false,
}: SpacingTokenRadioProps) {
  const handleChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const parsed = parseSpacing(event.target.value);
      if (!parsed) return;
      onPreview(parsed);
      onCommit(parsed);
    },
    [onCommit, onPreview],
  );

  const groupId = "design-token-spacing";

  return (
    <fieldset className="space-y-1.5" data-token-field="spacing" disabled={disabled}>
      <legend className="text-sm leading-none font-medium" id={`${groupId}-legend`}>
        간격
      </legend>
      <div
        role="radiogroup"
        aria-labelledby={`${groupId}-legend`}
        className="grid grid-cols-3 gap-2"
      >
        {SPACING_OPTIONS.map((opt) => {
          const selected = value === opt.value;
          const inputId = `${groupId}-${opt.value}`;
          return (
            <label
              key={opt.value}
              htmlFor={inputId}
              className={cn(
                "flex cursor-pointer flex-col items-center gap-1 rounded-md border px-2 py-2 text-xs transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                selected
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-input bg-background text-muted-foreground",
                disabled && "cursor-not-allowed opacity-50",
              )}
            >
              <input
                id={inputId}
                type="radio"
                name={groupId}
                value={opt.value}
                checked={selected}
                onChange={handleChange}
                disabled={disabled}
                className="sr-only"
                aria-describedby={`${inputId}-desc`}
              />
              <span className="font-medium">{opt.label}</span>
              <span id={`${inputId}-desc`} className="text-[10px] opacity-80">
                {opt.description}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export default SpacingTokenRadio;
