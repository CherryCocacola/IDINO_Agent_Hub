/**
 * BrandPresetButtons — 상단 row 에 배치되는 브랜드 프리셋 토글 버튼 그룹
 *
 * Phase 4 S1 D5. 프리셋 클릭 시 `DesignTokens` 전체를 교체해야 하므로
 * (schema-patch-local/tokens 와 매칭) onApply 는 Partial 이 아닌 DesignTokens
 * 전체를 받는다.
 *
 * UX:
 *   - 각 버튼은 primary/accent 2색 스와치 + 라벨.
 *   - 현재 active 프리셋은 aria-pressed="true" 로 표시 + primary 외곽선.
 *   - 클릭 시 onApply(tokens) → 호출자는 preview 와 commit 두 파이프 모두에
 *     전체 토큰을 흘린다.
 */

"use client";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils/cn";
import type { DesignTokens } from "@/types/document-schema";

import { BRAND_PRESETS, type BrandPresetDefinition } from "./tokens";

export interface BrandPresetButtonsProps {
  /** 현재 활성 브랜드 프리셋. custom 이면 어떤 버튼도 active 아님. */
  activePreset: DesignTokens["brand_preset"];
  /**
   * 현재 primary_color — "custom" 프리셋에서도 BRAND_PRESETS 의 커스텀 슬롯을
   * 보고 활성 표시할 수 있도록 활용 가능 (현재는 단순 비교만).
   */
  activePrimary?: string;
  /** 프리셋 클릭 시 전체 토큰 교체. */
  onApply: (tokens: DesignTokens) => void;
  disabled?: boolean;
}

function isPresetActive(
  preset: BrandPresetDefinition,
  activePreset: DesignTokens["brand_preset"],
  activePrimary?: string,
): boolean {
  if (preset.id !== "custom") {
    return preset.id === activePreset;
  }
  // custom 슬롯은 brand_preset === "custom" 이면서 primary 가 해당 스와치와
  // 일치할 때만 활성으로 본다 (여러 custom 프리셋을 버튼으로 노출할 수 있도록).
  return (
    activePreset === "custom" &&
    activePrimary !== undefined &&
    activePrimary.toUpperCase() === preset.swatch.primary.toUpperCase()
  );
}

export function BrandPresetButtons({
  activePreset,
  activePrimary,
  onApply,
  disabled = false,
}: BrandPresetButtonsProps) {
  return (
    <div
      role="group"
      aria-label="브랜드 프리셋"
      className="flex flex-wrap gap-2"
      data-token-field="brand_preset"
    >
      {BRAND_PRESETS.map((preset) => {
        const active = isPresetActive(preset, activePreset, activePrimary);
        return (
          <Button
            key={`${preset.id}-${preset.label}`}
            type="button"
            variant={active ? "default" : "outline"}
            size="sm"
            onClick={() => onApply(preset.tokens)}
            disabled={disabled}
            aria-pressed={active}
            aria-label={`${preset.label} 프리셋 적용`}
            data-preset-id={preset.id}
            data-preset-label={preset.label}
            className={cn("flex items-center gap-2", active && "ring-primary ring-2 ring-offset-1")}
          >
            <span
              aria-hidden="true"
              className="border-border flex h-4 w-8 overflow-hidden rounded-sm border"
            >
              <span className="h-full w-1/2" style={{ backgroundColor: preset.swatch.primary }} />
              <span className="h-full w-1/2" style={{ backgroundColor: preset.swatch.accent }} />
            </span>
            <span className="text-xs font-medium">{preset.label}</span>
          </Button>
        );
      })}
    </div>
  );
}

export default BrandPresetButtons;
