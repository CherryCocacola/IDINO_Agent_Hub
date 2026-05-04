/**
 * DesignTokenPicker — Designer Shell 우측 15% 영역 하단의 디자인 토큰 조정 UI
 *
 * Phase 4 S1 D5 산출물. 상단 Export 드롭다운(별도 컴포넌트) 아래 세로로 배치된다.
 *
 * 구성:
 *   1. **상단**: 브랜드 프리셋 버튼 row (클릭 → 전체 토큰 교체)
 *   2. **중간**: 개별 토큰 편집
 *      - 색상 4종 (primary/accent/text/background) — 브랜드 프리셋 `idino_*`
 *        사용 중에는 잠금, custom 에서만 편집 가능.
 *      - 폰트 Select (Pretendard / NotoSansKR / System).
 *      - spacing 라디오 (compact/normal/relaxed).
 *   3. **하단**: "기본값 복원" 버튼 (idino_default 프리셋 적용).
 *
 * Debounce 파이프:
 *   - 슬라이더 드래그 중: `onPreview` (50ms) → iframe CSS 변수 override
 *     (token-update 메시지).
 *   - 드래그 완료/blur: `onCommit` (500ms) → 서버 PATCH
 *     (schema-patch-local/tokens). 실제 호출은 D8 에서 wiring.
 *
 * 주의:
 *   - 본 컴포넌트는 preview-pane / edit-sidebar 를 직접 알지 못한다. 호출자
 *     (Designer shell) 가 ref 로 PreviewPane 을 잡고, onPreview/onCommit 콜백
 *     안에서 sendTokenUpdate 와 apiClient.patch 를 연결한다.
 *   - hex 값은 토큰 자체이므로 허용. 컴포넌트 내부 스타일은 var(--doc-*) 만 사용.
 */

"use client";

import { useCallback } from "react";

import { Button } from "@/components/ui/button";
import type { DesignTokens } from "@/types/document-schema";

import { BrandPresetButtons } from "./BrandPresetButtons";
import { ColorTokenSlider } from "./ColorTokenSlider";
import { FontTokenSelect } from "./FontTokenSelect";
import { SpacingTokenRadio } from "./SpacingTokenRadio";
import { COLOR_TOKENS, DEFAULT_DESIGN_TOKENS, isColorEditingLocked } from "./tokens";
import { useDebouncedTokenSync } from "./useDebouncedTokenSync";

export interface DesignTokenPickerProps {
  /** 현재 문서의 디자인 토큰 스냅샷. 부모에서 문서 상태를 관리. */
  tokens: DesignTokens;
  /**
   * iframe 라이브 프리뷰 파이프. 50ms debounce 후 호출.
   * 호출자 책임: `previewRef.current?.sendTokenUpdate(patch)`.
   */
  onPreview: (patch: Partial<DesignTokens>) => void;
  /**
   * 서버 PATCH 파이프. 500ms debounce 후 호출.
   * 호출자 책임 (D8): `apiClient.patch('/v2/documents/{id}', { patchType: 'tokens', data: mergedTokens })`.
   * 부모의 "문서 상태" 업데이트도 여기서 병행한다.
   */
  onCommit: (patch: Partial<DesignTokens>) => void;
  /** picker 전체 비활성 (예: 문서 로딩 중). */
  disabled?: boolean;
  className?: string;
  dataTestId?: string;
}

export function DesignTokenPicker({
  tokens,
  onPreview,
  onCommit,
  disabled = false,
  className,
  dataTestId,
}: DesignTokenPickerProps) {
  const sync = useDebouncedTokenSync({ onPreview, onCommit });

  const colorLocked = isColorEditingLocked(tokens.brand_preset);
  const lockedHint = colorLocked ? "IDINO 브랜드 프리셋 사용 중 — 커스텀 모드에서 편집" : undefined;

  // ─── 핸들러 ─────────────────────────────────────────────────────────────

  /**
   * 프리셋 / 기본값 복원 등 "전체 토큰 교체" 경로.
   * preview 와 commit 모두 flush 타이밍 맞추기 위해 동기 호출.
   * commit 은 500ms debounce 이므로 실제 PATCH 는 사용자가 잠시 멈춘 뒤 발생.
   */
  const applyFullTokens = useCallback(
    (next: DesignTokens) => {
      sync.preview(next);
      sync.commit(next);
    },
    [sync],
  );

  const handleColorPreview = useCallback(
    (key: keyof DesignTokens, hex: string) => {
      // custom 프리셋이 아니면 picker 가 disabled 이므로 사실상 호출되지 않음.
      // 방어적으로 brand_preset 도 custom 으로 승격해 preview 에 싣는다.
      const patch: Partial<DesignTokens> = { [key]: hex };
      if (tokens.brand_preset !== "custom") patch.brand_preset = "custom";
      sync.preview(patch);
    },
    [sync, tokens.brand_preset],
  );

  const handleColorCommit = useCallback(
    (key: keyof DesignTokens, hex: string) => {
      const patch: Partial<DesignTokens> = { [key]: hex };
      if (tokens.brand_preset !== "custom") patch.brand_preset = "custom";
      sync.commit(patch);
    },
    [sync, tokens.brand_preset],
  );

  const handleFontPreview = useCallback(
    (value: DesignTokens["font_family"]) => sync.preview({ font_family: value }),
    [sync],
  );
  const handleFontCommit = useCallback(
    (value: DesignTokens["font_family"]) => sync.commit({ font_family: value }),
    [sync],
  );
  const handleSpacingPreview = useCallback(
    (value: DesignTokens["spacing"]) => sync.preview({ spacing: value }),
    [sync],
  );
  const handleSpacingCommit = useCallback(
    (value: DesignTokens["spacing"]) => sync.commit({ spacing: value }),
    [sync],
  );

  const handleReset = useCallback(() => {
    applyFullTokens(DEFAULT_DESIGN_TOKENS);
  }, [applyFullTokens]);

  // ─── 렌더 ────────────────────────────────────────────────────────────────

  return (
    <section
      aria-label="디자인 토큰 편집"
      data-testid={dataTestId ?? "design-token-picker"}
      data-design-token-picker
      className={className}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--doc-spacing-md)",
        padding: "var(--doc-spacing-md)",
      }}
    >
      {/* 문서 로드 전에는 picker 전체가 disabled 로 비활성된다. 사용자가
          "왜 회색인지" 오해하지 않도록 상단에 이유를 명시한다. */}
      {disabled ? (
        <p
          role="status"
          style={{
            fontSize: "var(--doc-font-size-xs)",
            color: "var(--doc-text-muted)",
            lineHeight: 1.4,
          }}
        >
          문서를 먼저 생성하면 디자인 토큰을 편집할 수 있습니다.
        </p>
      ) : null}

      {/* 1) 브랜드 프리셋 */}
      <div className="space-y-2">
        <h3 className="text-sm leading-none font-semibold">브랜드 프리셋</h3>
        <BrandPresetButtons
          activePreset={tokens.brand_preset}
          activePrimary={tokens.primary_color}
          onApply={applyFullTokens}
          disabled={disabled}
        />
      </div>

      {/* 2) 개별 토큰 */}
      <div className="space-y-3">
        <h3 className="text-sm leading-none font-semibold">색상</h3>
        <div className="space-y-3">
          {COLOR_TOKENS.map((meta) => (
            <ColorTokenSlider
              key={meta.key}
              label={meta.label}
              tokenKey={meta.key}
              value={tokens[meta.key]}
              locked={colorLocked || disabled}
              lockedHint={lockedHint}
              onPreview={(hex) => handleColorPreview(meta.key, hex)}
              onCommit={(hex) => handleColorCommit(meta.key, hex)}
            />
          ))}
        </div>
      </div>

      <FontTokenSelect
        value={tokens.font_family}
        onPreview={handleFontPreview}
        onCommit={handleFontCommit}
        disabled={disabled}
      />

      <SpacingTokenRadio
        value={tokens.spacing}
        onPreview={handleSpacingPreview}
        onCommit={handleSpacingCommit}
        disabled={disabled}
      />

      {/* 3) 기본값 복원 */}
      <div className="pt-1">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleReset}
          disabled={disabled}
          aria-label="디자인 토큰 기본값으로 복원"
          className="w-full"
        >
          기본값 복원
        </Button>
      </div>
    </section>
  );
}

export default DesignTokenPicker;
