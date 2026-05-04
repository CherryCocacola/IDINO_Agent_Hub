/**
 * Paragraph — 본문 단락 컴포넌트
 *
 * DocumentSchema catalog #4 (MVP). `<p>` 요소 단일 렌더이며, `emphasis`에
 * 따라 굵기·기울임을 변주한다. 한글 본문 가독성을 위해 `word-break: keep-all`,
 * `line-height: var(--doc-line-height-normal)` 를 기본값으로 둔다.
 *
 * `[cite: xxx]` 인라인 마커 치환은 Phase 4 S6에서 별도 변환 유틸로 처리한다.
 * 현재는 원문 그대로 출력한다.
 */

import { Lock } from "lucide-react";

import type { ParagraphComponent } from "@/types/document-schema";

export interface ParagraphProps {
  component: ParagraphComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

const EMPHASIS_STYLE: Record<
  ParagraphComponent["emphasis"],
  { fontWeight: number; fontStyle: "normal" | "italic" }
> = {
  normal: { fontWeight: 400, fontStyle: "normal" },
  bold: { fontWeight: 600, fontStyle: "normal" },
  italic: { fontWeight: 400, fontStyle: "italic" },
};

export function Paragraph({ component, isSelected, onSelect }: ParagraphProps) {
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };
  const emphasisStyle = EMPHASIS_STYLE[component.emphasis];

  return (
    <div
      data-component="Paragraph"
      data-component-id={component.id}
      data-emphasis={component.emphasis}
      data-locked={component.locked}
      data-selected={isSelected}
      role="button"
      tabIndex={0}
      aria-label="본문 단락"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full transition-colors outline-none"
      style={{
        padding: "var(--doc-spacing-xs) var(--doc-spacing-sm)",
        marginBottom: "var(--doc-spacing-md)",
        outline: isSelected ? "2px solid var(--doc-primary)" : undefined,
        outlineOffset: isSelected ? "2px" : undefined,
        borderRadius: "var(--doc-radius-sm)",
        cursor: component.locked ? "not-allowed" : "pointer",
        opacity: component.locked ? 0.85 : 1,
      }}
    >
      {component.locked && (
        <Lock
          aria-hidden="true"
          className="absolute top-2 right-2 h-3.5 w-3.5"
          style={{ color: "var(--doc-text-muted)" }}
        />
      )}
      <p
        style={{
          color: "var(--doc-text)",
          fontFamily: "var(--doc-font-family)",
          fontSize: "var(--doc-font-size-base)",
          lineHeight: "var(--doc-line-height-normal)",
          wordBreak: "keep-all",
          margin: 0,
          ...emphasisStyle,
        }}
      >
        {component.text}
      </p>
    </div>
  );
}

export default Paragraph;
