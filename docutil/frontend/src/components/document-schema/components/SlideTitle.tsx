/**
 * SlideTitle — 슬라이드 표제 컴포넌트
 *
 * DocumentSchema catalog #1 (docs/phase1_architecture.md §3.2, 부록 B).
 * `title_slide` 레이아웃 중앙에 배치되는 대형 타이틀. IDINO primary 색상으로
 * 강조되며 화면 중앙 정렬·font-size 3xl 기준으로 렌더한다.
 *
 * 디자인 규약:
 *   - 색상: `var(--doc-primary)` / `var(--doc-text)` 만 참조.
 *   - 폰트 크기: `var(--doc-font-size-3xl)`.
 *   - hex 하드코딩 금지 (anti-patterns.md).
 */

import { Lock } from "lucide-react";

import type { SlideTitleComponent } from "@/types/document-schema";

export interface SlideTitleProps {
  component: SlideTitleComponent;
  /**
   * 현재 사이드바에서 선택된 컴포넌트 ID와 본 컴포넌트 id가 같으면 하이라이트.
   * Phase 4 S1에서 <PageRenderer>가 주입.
   */
  isSelected?: boolean;
  /** 컴포넌트 클릭 시 편집 사이드바로 신호. iframe에서는 postMessage로 bridging. */
  onSelect?: (componentId: string) => void;
}

export function SlideTitle({ component, isSelected, onSelect }: SlideTitleProps) {
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="SlideTitle"
      data-component-id={component.id}
      data-locked={component.locked}
      data-selected={isSelected}
      role="button"
      tabIndex={0}
      aria-label={`슬라이드 제목: ${component.text}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative flex w-full flex-col items-center justify-center text-center transition-colors outline-none"
      style={{
        padding: "var(--doc-spacing-2xl) var(--doc-spacing-lg)",
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
      <h1
        style={{
          color: "var(--doc-primary)",
          fontFamily: "var(--doc-font-family)",
          fontSize: "var(--doc-font-size-3xl)",
          fontWeight: 700,
          lineHeight: "var(--doc-line-height-tight)",
          wordBreak: "keep-all",
          margin: 0,
        }}
      >
        {component.text}
      </h1>
    </div>
  );
}

export default SlideTitle;
