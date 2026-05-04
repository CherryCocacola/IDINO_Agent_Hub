/**
 * Quote — 인용 블록 컴포넌트
 *
 * DocumentSchema catalog #5 (S3 D1 추가). 좌측 4px accent 세로선과 들여쓴
 * 패딩으로 본문과 구분되는 인용 영역을 만든다. `author` 필드가 있으면 하단에
 * `— {author}` 형태의 출처를 muted 톤으로 표시한다.
 *
 * 디자인 규약:
 *   - `border-left: 4px solid var(--doc-accent)` + `padding-left: var(--doc-spacing-md)`
 *   - 본문 폰트: `var(--doc-font-size-lg)`, `font-style: italic`
 *   - 출처: `var(--doc-font-size-sm)`, `var(--doc-text-muted)` — 이모지/hex 금지
 *   - `<blockquote>` + `<cite>` semantic 태그 사용 (스크린리더 친화적)
 */

import { Lock } from "lucide-react";

import type { QuoteComponent } from "@/types/document-schema";

export interface QuoteProps {
  component: QuoteComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

export function Quote({ component, isSelected, onSelect }: QuoteProps) {
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  const ariaLabel = component.author
    ? `인용: ${component.text}, 출처 ${component.author}`
    : `인용: ${component.text}`;

  return (
    <div
      data-component="Quote"
      data-component-id={component.id}
      data-has-author={component.author !== null && component.author !== ""}
      data-locked={component.locked}
      data-selected={isSelected}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full transition-colors outline-none"
      style={{
        marginTop: "var(--doc-spacing-md)",
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
      <blockquote
        style={{
          borderLeft: "4px solid var(--doc-accent)",
          paddingLeft: "var(--doc-spacing-md)",
          paddingTop: "var(--doc-spacing-sm)",
          paddingBottom: "var(--doc-spacing-sm)",
          margin: 0,
        }}
      >
        <p
          style={{
            color: "var(--doc-text)",
            fontFamily: "var(--doc-font-family)",
            fontSize: "var(--doc-font-size-lg)",
            fontStyle: "italic",
            fontWeight: 400,
            lineHeight: "var(--doc-line-height-normal)",
            wordBreak: "keep-all",
            margin: 0,
          }}
        >
          {component.text}
        </p>
        {component.author && (
          <cite
            style={{
              display: "block",
              marginTop: "var(--doc-spacing-xs)",
              color: "var(--doc-text-muted)",
              fontFamily: "var(--doc-font-family)",
              fontSize: "var(--doc-font-size-sm)",
              fontStyle: "normal",
              fontWeight: 500,
              wordBreak: "keep-all",
            }}
          >
            — {component.author}
          </cite>
        )}
      </blockquote>
    </div>
  );
}

export default Quote;
