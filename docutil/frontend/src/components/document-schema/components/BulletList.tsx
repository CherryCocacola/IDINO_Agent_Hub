/**
 * BulletList — 불릿(또는 번호) 목록 컴포넌트
 *
 * DocumentSchema catalog #5 (MVP). `numbered=true` 면 `<ol>`, 아니면 `<ul>`.
 * 각 항목은 2레벨까지 허용하며, `emphasis` 값에 따라 텍스트 굵기·하이라이트
 * 배경을 차등 적용한다. 서버 validator가 12개/2레벨을 차단하지만 프론트에서도
 * 방어적으로 12개까지 slice 하고 초과 시 console.warn 남긴다.
 */

import { Lock } from "lucide-react";

import type { BulletItem, BulletListComponent } from "@/types/document-schema";

export interface BulletListProps {
  component: BulletListComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

const MAX_ITEMS = 12;

const ITEM_EMPHASIS_STYLE: Record<
  BulletItem["emphasis"],
  { fontWeight: number; background: string; paddingInline: string }
> = {
  normal: { fontWeight: 400, background: "transparent", paddingInline: "0" },
  bold: { fontWeight: 600, background: "transparent", paddingInline: "0" },
  highlight: {
    fontWeight: 500,
    background: "var(--doc-accent-soft)",
    paddingInline: "var(--doc-spacing-sm)",
  },
};

export function BulletList({ component, isSelected, onSelect }: BulletListProps) {
  const items = component.items.slice(0, MAX_ITEMS);
  if (component.items.length > MAX_ITEMS) {
    console.warn(
      `[BulletList:${component.id}] items.length(${component.items.length}) > ${MAX_ITEMS}, truncated.`,
    );
  }

  const ListTag = component.numbered ? "ol" : "ul";
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="BulletList"
      data-component-id={component.id}
      data-numbered={component.numbered}
      data-item-count={items.length}
      data-locked={component.locked}
      data-selected={isSelected}
      role="button"
      tabIndex={0}
      aria-label={component.numbered ? "번호 목록" : "불릿 목록"}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full transition-colors outline-none"
      style={{
        padding: "var(--doc-spacing-sm)",
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
      <ListTag
        style={{
          color: "var(--doc-text)",
          fontFamily: "var(--doc-font-family)",
          fontSize: "var(--doc-font-size-base)",
          lineHeight: "var(--doc-line-height-normal)",
          paddingInlineStart: "var(--doc-spacing-xl)",
          margin: 0,
          listStyleType: component.numbered ? "decimal" : "disc",
        }}
      >
        {items.map((item, idx) => {
          const emp = ITEM_EMPHASIS_STYLE[item.emphasis];
          return (
            <li
              key={`${component.id}-item-${idx}`}
              style={{
                marginBottom: "var(--doc-spacing-xs)",
                wordBreak: "keep-all",
              }}
            >
              <span
                style={{
                  fontWeight: emp.fontWeight,
                  background: emp.background,
                  paddingInline: emp.paddingInline,
                  borderRadius: item.emphasis === "highlight" ? "var(--doc-radius-sm)" : undefined,
                }}
              >
                {item.text}
              </span>
              {item.sub_items.length > 0 && (
                <ul
                  style={{
                    marginTop: "var(--doc-spacing-xs)",
                    paddingInlineStart: "var(--doc-spacing-lg)",
                    listStyleType: "circle",
                    color: "var(--doc-text-muted)",
                    fontSize: "var(--doc-font-size-sm)",
                  }}
                >
                  {item.sub_items.map((sub, subIdx) => (
                    <li
                      key={`${component.id}-item-${idx}-sub-${subIdx}`}
                      style={{ wordBreak: "keep-all" }}
                    >
                      {sub}
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ListTag>
    </div>
  );
}

export default BulletList;
