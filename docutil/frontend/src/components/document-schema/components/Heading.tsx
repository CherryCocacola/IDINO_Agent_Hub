/**
 * Heading — 섹션 제목 (H1~H3) 컴포넌트
 *
 * DocumentSchema catalog #2 (MVP). `component.level` 값에 따라 h1/h2/h3
 * semantic 태그와 font-size가 달라지며, 좌측에 IDINO 시그니처인 4px primary
 * border-left 를 얹어 섹션의 시작 지점을 명확히 한다.
 *
 * 접근성: level에 맞는 heading 태그를 실제로 렌더하므로 aria-level은 명시하지
 * 않아도 자동 부여된다. 페이지 내 H1 중복 회피는 PageRenderer 책임.
 */

import { Lock } from "lucide-react";

import type { HeadingComponent } from "@/types/document-schema";

export interface HeadingProps {
  component: HeadingComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

const LEVEL_FONT_SIZE: Record<HeadingComponent["level"], string> = {
  1: "var(--doc-font-size-2xl)",
  2: "var(--doc-font-size-xl)",
  3: "var(--doc-font-size-lg)",
};

export function Heading({ component, isSelected, onSelect }: HeadingProps) {
  const Tag = `h${component.level}` as "h1" | "h2" | "h3";
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="Heading"
      data-component-id={component.id}
      data-level={component.level}
      data-locked={component.locked}
      data-selected={isSelected}
      role="button"
      tabIndex={0}
      aria-label={`섹션 제목 레벨 ${component.level}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full transition-colors outline-none"
      style={{
        paddingLeft: "var(--doc-spacing-md)",
        paddingTop: "var(--doc-spacing-sm)",
        paddingBottom: "var(--doc-spacing-sm)",
        borderLeft: "4px solid var(--doc-primary)",
        marginTop: "var(--doc-spacing-lg)",
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
      <Tag
        style={{
          color: "var(--doc-text)",
          fontFamily: "var(--doc-font-family)",
          fontSize: LEVEL_FONT_SIZE[component.level],
          fontWeight: component.level === 1 ? 700 : 600,
          lineHeight: "var(--doc-line-height-tight)",
          wordBreak: "keep-all",
          margin: 0,
        }}
      >
        {component.text}
      </Tag>
    </div>
  );
}

export default Heading;
