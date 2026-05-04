/**
 * KPI — 핵심지표 카드 컴포넌트
 *
 * DocumentSchema catalog #6 (MVP). label/value/delta 삼단 구성의 카드형
 * 지표 블록. value는 primary 컬러로 가장 크게, delta는 방향(up/down/flat)에
 * 따라 success/danger/muted 색상과 화살표 아이콘을 함께 표시한다.
 *
 * 색상 규약 (CSS 변수 only):
 *   delta_direction=up   → var(--doc-success)
 *   delta_direction=down → var(--doc-danger)
 *   delta_direction=flat → var(--doc-text-muted)
 *   delta string 이 `+` 시작이면 up fallback, `-` 시작이면 down fallback.
 */

import { ArrowDown, ArrowUp, Lock, Minus } from "lucide-react";

import type { KPIComponent } from "@/types/document-schema";

export interface KPIProps {
  component: KPIComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

type Direction = "up" | "down" | "flat";

function resolveDirection(
  explicit: KPIComponent["delta_direction"],
  delta: string | null,
): Direction | null {
  if (explicit) return explicit;
  if (!delta) return null;
  const trimmed = delta.trim();
  if (trimmed.startsWith("+")) return "up";
  if (trimmed.startsWith("-")) return "down";
  return "flat";
}

const DIRECTION_COLOR: Record<Direction, string> = {
  up: "var(--doc-success)",
  down: "var(--doc-danger)",
  flat: "var(--doc-text-muted)",
};

const DIRECTION_LABEL: Record<Direction, string> = {
  up: "증가",
  down: "감소",
  flat: "변동 없음",
};

export function KPI({ component, isSelected, onSelect }: KPIProps) {
  const direction = resolveDirection(component.delta_direction, component.delta);
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  const ariaLabelParts = [component.label, component.value];
  if (component.delta && direction) {
    ariaLabelParts.push(`${DIRECTION_LABEL[direction]} ${component.delta}`);
  }

  return (
    <article
      data-component="KPI"
      data-component-id={component.id}
      data-locked={component.locked}
      data-selected={isSelected}
      data-delta-direction={direction ?? "none"}
      role="group"
      tabIndex={0}
      aria-label={ariaLabelParts.join(", ")}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative flex w-full flex-col gap-1 transition-shadow outline-none"
      style={{
        background: "var(--doc-surface)",
        border: "1px solid var(--doc-border)",
        borderRadius: "var(--doc-radius-lg)",
        padding: "var(--doc-spacing-lg)",
        boxShadow: isSelected ? "var(--doc-shadow-md)" : "var(--doc-shadow-sm)",
        outline: isSelected ? "2px solid var(--doc-primary)" : undefined,
        outlineOffset: isSelected ? "2px" : undefined,
        cursor: component.locked ? "not-allowed" : "pointer",
        opacity: component.locked ? 0.85 : 1,
        minWidth: 0,
      }}
    >
      {component.locked && (
        <Lock
          aria-hidden="true"
          className="absolute top-3 right-3 h-4 w-4"
          style={{ color: "var(--doc-text-muted)" }}
        />
      )}
      <span
        style={{
          fontSize: "var(--doc-font-size-sm)",
          color: "var(--doc-text-muted)",
          fontFamily: "var(--doc-font-family)",
          fontWeight: 500,
          wordBreak: "keep-all",
        }}
      >
        {component.label}
      </span>
      <span
        style={{
          fontSize: "var(--doc-font-size-2xl)",
          color: "var(--doc-primary)",
          fontFamily: "var(--doc-font-family)",
          fontWeight: 700,
          lineHeight: "var(--doc-line-height-tight)",
          wordBreak: "keep-all",
        }}
      >
        {component.value}
      </span>
      {component.delta && direction && (
        <span
          className="inline-flex items-center gap-1"
          style={{
            color: DIRECTION_COLOR[direction],
            fontSize: "var(--doc-font-size-sm)",
            fontWeight: 600,
          }}
        >
          {direction === "up" && <ArrowUp aria-hidden="true" className="h-4 w-4" />}
          {direction === "down" && <ArrowDown aria-hidden="true" className="h-4 w-4" />}
          {direction === "flat" && <Minus aria-hidden="true" className="h-4 w-4" />}
          <span>{component.delta}</span>
        </span>
      )}
      {component.description && (
        <p
          style={{
            marginTop: "var(--doc-spacing-xs)",
            fontSize: "var(--doc-font-size-xs)",
            color: "var(--doc-text-muted)",
            lineHeight: "var(--doc-line-height-normal)",
            wordBreak: "keep-all",
            margin: 0,
          }}
        >
          {component.description}
        </p>
      )}
    </article>
  );
}

export default KPI;
