/**
 * tokens.ts — design-token-picker 내부에서 공유하는 상수·헬퍼
 *
 * Phase 4 S1 D5. 여기 정의한 상수는 picker 내부에서만 사용한다 (외부 노출 X).
 * 외부에는 `index.tsx` 의 DesignTokenPicker 만 export.
 */

import type { DesignTokens } from "@/types/document-schema";

// ─── 기본값 ────────────────────────────────────────────────────────────────

/**
 * idino_default 프리셋에 대응하는 토큰 값.
 * document-tokens.css :root 의 기본값과 동일해야 한다 (단일 진실원본은 CSS지만,
 * 토큰 상태를 리셋하거나 객체로 전달할 때 필요해 TS 에 복제).
 */
export const DEFAULT_DESIGN_TOKENS: DesignTokens = {
  primary_color: "#0A4FC2",
  accent_color: "#FF6B35",
  text_color: "#1F2937",
  background_color: "#FFFFFF",
  font_family: "Pretendard",
  spacing: "normal",
  brand_preset: "idino_default",
};

// ─── 브랜드 프리셋 테이블 ──────────────────────────────────────────────────

export interface BrandPresetDefinition {
  /** `DesignTokens.brand_preset` 값. */
  id: DesignTokens["brand_preset"];
  /** UI 버튼 라벨 (한국어). */
  label: string;
  /** 미리보기 스와치용 primary/accent hex. */
  swatch: { primary: string; accent: string };
  /** 클릭 시 교체할 전체 토큰. */
  tokens: DesignTokens;
}

/**
 * 선택 가능한 브랜드 프리셋 목록.
 * `custom` 은 picker UI 가 아닌 "사용자 임의 편집 중" 상태 마커이므로 버튼에
 * 노출하지 않는다.
 */
export const BRAND_PRESETS: readonly BrandPresetDefinition[] = [
  {
    id: "idino_default",
    label: "IDINO 기본",
    swatch: { primary: "#0A4FC2", accent: "#FF6B35" },
    tokens: { ...DEFAULT_DESIGN_TOKENS },
  },
  {
    id: "idino_mono",
    label: "IDINO 모노",
    swatch: { primary: "#2B2B2B", accent: "#666666" },
    tokens: {
      ...DEFAULT_DESIGN_TOKENS,
      primary_color: "#2B2B2B",
      accent_color: "#666666",
      brand_preset: "idino_mono",
    },
  },
  {
    // idino_mono 가 첫번째 신규 아니므로 'navy' 가 "1개 신규" 요건 충족.
    // 타입상 brand_preset 은 3종 literal 이라 neu 프리셋은 custom 으로 매핑.
    id: "custom",
    label: "네이비",
    swatch: { primary: "#0F2F5A", accent: "#D4A017" },
    tokens: {
      ...DEFAULT_DESIGN_TOKENS,
      primary_color: "#0F2F5A",
      accent_color: "#D4A017",
      brand_preset: "custom",
    },
  },
] as const;

// ─── 색상 토큰 메타 ────────────────────────────────────────────────────────

export type ColorTokenKey = "primary_color" | "accent_color" | "text_color" | "background_color";

export interface ColorTokenMeta {
  key: ColorTokenKey;
  label: string;
  /** CSS 변수 이름 (picker UI 안 미리보기 스와치에 쓰일 때). */
  cssVariable: string;
}

export const COLOR_TOKENS: readonly ColorTokenMeta[] = [
  { key: "primary_color", label: "프라이머리", cssVariable: "--doc-primary" },
  { key: "accent_color", label: "액센트", cssVariable: "--doc-accent" },
  { key: "text_color", label: "본문 텍스트", cssVariable: "--doc-text" },
  { key: "background_color", label: "배경", cssVariable: "--doc-background" },
] as const;

// ─── 폰트 패밀리 프리셋 ────────────────────────────────────────────────────

export interface FontFamilyOption {
  value: DesignTokens["font_family"];
  label: string;
  /** Select 드롭다운에 미리보기용으로 적용할 font-family 문자열. */
  fontStack: string;
}

export const FONT_FAMILY_OPTIONS: readonly FontFamilyOption[] = [
  {
    value: "Pretendard",
    label: "Pretendard (기본)",
    fontStack: "'Pretendard', 'Noto Sans KR', sans-serif",
  },
  {
    value: "NotoSansKR",
    label: "나눔고딕 (Noto Sans KR)",
    fontStack: "'Noto Sans KR', 'Pretendard', sans-serif",
  },
  {
    value: "System",
    label: "시스템 기본 (System UI)",
    fontStack: "ui-sans-serif, system-ui, sans-serif",
  },
] as const;

// ─── spacing 라디오 옵션 ───────────────────────────────────────────────────

export interface SpacingOption {
  value: DesignTokens["spacing"];
  label: string;
  description: string;
}

export const SPACING_OPTIONS: readonly SpacingOption[] = [
  { value: "compact", label: "좁게", description: "정보 밀도 우선" },
  { value: "normal", label: "보통", description: "표준 간격" },
  { value: "relaxed", label: "넓게", description: "여백 많이" },
] as const;

// ─── HEX 유효성 검증 ──────────────────────────────────────────────────────

/** `#RRGGBB` 또는 `#RGB` 형태만 통과. 대/소문자 모두 허용. */
const HEX_COLOR_PATTERN = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

export function isValidHexColor(value: string): boolean {
  return HEX_COLOR_PATTERN.test(value);
}

/**
 * 입력 문자열을 `#RRGGBB` 로 정규화. 유효하지 않으면 null.
 * - `#fff` → `#FFFFFF`
 * - `#0A4FC2` → `#0A4FC2`
 * - `0A4FC2` → null (selfhealing 금지: 사용자에게 명시적 에러 유도)
 */
export function normalizeHexColor(value: string): string | null {
  const trimmed = value.trim();
  if (!isValidHexColor(trimmed)) return null;
  if (trimmed.length === 4) {
    const [, r, g, b] = trimmed;
    return `#${r}${r}${g}${g}${b}${b}`.toUpperCase();
  }
  return trimmed.toUpperCase();
}

// ─── 브랜드 프리셋 잠금 헬퍼 ──────────────────────────────────────────────

/**
 * 개별 색상 편집이 허용되는지 판정.
 * `idino_*` 프리셋 사용 중에는 color slider 를 readOnly.
 * custom 프리셋일 때만 자유 편집.
 */
export function isColorEditingLocked(brandPreset: DesignTokens["brand_preset"]): boolean {
  return brandPreset !== "custom";
}
