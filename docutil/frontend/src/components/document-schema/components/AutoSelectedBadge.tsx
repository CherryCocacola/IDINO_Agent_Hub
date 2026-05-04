/**
 * AutoSelectedBadge — 자동 선택된 이미지 배지
 *
 * Phase 4 S3 D7 산출물 (phase3_execution_roadmap.md §2.3).
 *
 * 역할:
 *   - 프리뷰 렌더 시 이미지 `src` 도메인을 파싱해 자동 생성 provider 를 추론.
 *   - provider 별 한국어 라벨을 작은 배지로 우측 상단에 오버레이.
 *   - `prompt` 가 있으면 hover 툴팁(`title`) + `aria-label` 로 전달 — 접근성 준수.
 *
 * 감지 규칙 (휴리스틱 — 서버가 명시 provider 메타를 주기 전까지의 임시 기준):
 *   1. `src` 가 빈 값/URL 아님 → "자동" 여부 판정 불가, 배지 숨김.
 *   2. 호스트가 `images.unsplash.com` 또는 포함 → Unsplash.
 *   3. 경로에 `generated_images/` 포함 또는 호스트에 `openai` 포함 → DALL-E 3.
 *   4. 그 외 URL → 배지 숨김 (사용자가 직접 넣은 URL 로 간주).
 *
 * 디자인:
 *   - 토큰 사용 (`var(--doc-*)`). 하드코딩 금지 (anti-patterns.md).
 *   - 접근성: role/aria-label 제공, 포커스 가능은 Image 부모 컴포넌트에 위임.
 */

import { Sparkles } from "lucide-react";

export type AutoSelectedProvider = "unsplash" | "dalle" | null;

/** provider → 한국어 라벨. null 이면 배지 미표시. */
const PROVIDER_LABEL: Record<Exclude<AutoSelectedProvider, null>, string> = {
  unsplash: "Unsplash",
  dalle: "DALL-E 3",
};

/**
 * src URL 로부터 자동 선택 provider 를 추정.
 * 실패 시 null 반환 → 호출부에서 배지 숨김.
 */
export function detectAutoSelectedProvider(src: string | null | undefined): AutoSelectedProvider {
  if (!src || src.trim().length === 0) return null;

  const lowered = src.toLowerCase();

  // Unsplash — 공식 CDN 또는 사이트.
  if (lowered.includes("images.unsplash.com") || lowered.includes("unsplash.com/photos")) {
    return "unsplash";
  }

  // DALL-E 3 경로 — 서버가 MinIO 에 저장할 때 prefix 로 generated_images/ 를 사용.
  // 또는 OpenAI 임시 URL (`oaidalleapiprodscus`) 등을 임시 프리뷰로 주는 경우.
  if (
    lowered.includes("/generated_images/") ||
    lowered.includes("oaidalleapiprodscus") ||
    lowered.includes("openai")
  ) {
    return "dalle";
  }

  return null;
}

export interface AutoSelectedBadgeProps {
  /** 이미지 원본 URL. 자동 감지의 입력. */
  src: string | null | undefined;
  /** 자동 생성 프롬프트. 툴팁/aria-label 에 사용 (없어도 무방). */
  prompt?: string | null;
  /**
   * 명시 provider 가 있다면 휴리스틱 대신 우선 사용.
   * (서버가 향후 명시 필드를 추가할 경우의 확장 포인트.)
   */
  providerHint?: AutoSelectedProvider;
}

/** 자동 선택된 이미지에 붙이는 작은 배지 컴포넌트. 감지 실패 시 null 을 반환. */
export function AutoSelectedBadge({ src, prompt, providerHint }: AutoSelectedBadgeProps) {
  const provider = providerHint ?? detectAutoSelectedProvider(src);
  if (!provider) return null;

  const label = PROVIDER_LABEL[provider];
  const promptSnippet = prompt?.trim();
  // 너무 긴 prompt 는 툴팁에서 잘라낸다 (브라우저별 tooltip 길이 제한 회피).
  const truncatedPrompt =
    promptSnippet && promptSnippet.length > 160 ? `${promptSnippet.slice(0, 160)}…` : promptSnippet;

  const ariaLabel = truncatedPrompt
    ? `자동 선택 (${label}) — 프롬프트: ${truncatedPrompt}`
    : `자동 선택 (${label})`;

  return (
    <span
      role="img"
      aria-label={ariaLabel}
      title={ariaLabel}
      data-auto-badge={provider}
      className="pointer-events-none absolute top-1 right-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold shadow-sm"
      style={{
        background: "var(--doc-surface)",
        color: "var(--doc-primary)",
        border: "1px solid var(--doc-border)",
        lineHeight: 1,
      }}
    >
      <Sparkles aria-hidden="true" style={{ width: 10, height: 10 }} />
      {label}
    </span>
  );
}

export default AutoSelectedBadge;
