/**
 * SlideSubtitle — 슬라이드 부제 컴포넌트
 *
 * DocumentSchema catalog #2 (S3 D1 추가). SlideTitle 바로 아래 배치되는 보조
 * 텍스트로, 타이틀 대비 한 단계 작고 차분한 톤(`--doc-text-muted`)으로 표시해
 * 시각적 위계를 만든다. 중앙 정렬·`keep-all` 기본값으로 한글 가독성을 확보한다.
 *
 * 디자인 규약:
 *   - 색상: `var(--doc-text-muted)` 만 참조 — hex 하드코딩 금지 (anti-patterns.md)
 *   - 폰트 크기: `var(--doc-font-size-xl)` (타이틀 3xl 보다 한 단계 작음, 대략 20pt)
 *   - lineHeight: `var(--doc-line-height-snug)` 로 줄간격 다소 여유있게.
 */

import { Lock } from "lucide-react";

import type { SlideSubtitleComponent } from "@/types/document-schema";

export interface SlideSubtitleProps {
  component: SlideSubtitleComponent;
  /** 현재 사이드바에서 선택된 컴포넌트 ID 와 본 컴포넌트 id 가 같으면 하이라이트. */
  isSelected?: boolean;
  /** 컴포넌트 클릭 시 편집 사이드바로 신호 전달. iframe 에서는 postMessage bridging. */
  onSelect?: (componentId: string) => void;
}

export function SlideSubtitle({ component, isSelected, onSelect }: SlideSubtitleProps) {
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="SlideSubtitle"
      data-component-id={component.id}
      data-locked={component.locked}
      data-selected={isSelected}
      role="button"
      tabIndex={0}
      aria-label={`슬라이드 부제: ${component.text}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative flex w-full flex-col items-center justify-center text-center transition-colors outline-none"
      style={{
        padding: "var(--doc-spacing-md) var(--doc-spacing-lg)",
        outline: isSelected ? "2px solid var(--doc-primary)" : undefined,
        outlineOffset: isSelected ? "4px" : undefined,
        borderRadius: "var(--doc-radius-md)",
        cursor: component.locked ? "not-allowed" : "pointer",
        opacity: component.locked ? 0.85 : 1,
      }}
    >
      {component.locked && (
        <Lock
          aria-hidden="true"
          className="absolute top-3 right-3 h-4 w-4"
          style={{ color: "var(--doc-text-muted)" }}
        />
      )}
      <p
        style={{
          color: "var(--doc-text-muted)",
          fontFamily: "var(--doc-font-family)",
          fontSize: "var(--doc-font-size-xl)",
          fontWeight: 500,
          lineHeight: "var(--doc-line-height-tight)",
          wordBreak: "keep-all",
          margin: 0,
        }}
      >
        {component.text}
      </p>
    </div>
  );
}

export default SlideSubtitle;
