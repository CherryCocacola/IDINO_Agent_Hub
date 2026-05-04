/**
 * Callout — 강조 박스 컴포넌트
 *
 * DocumentSchema catalog #6 (S3 D2 추가). 본문 흐름에서 특히 주목해야 할
 * 정보·주의·성공·위험 메시지를 시각적으로 분리해 표시한다. `variant` 값에 따라
 * 배경/테두리/아이콘이 달라진다 (4종: info / warning / success / danger).
 *
 * 디자인 규약:
 *   - 색상은 모두 `var(--doc-*)` 토큰 경유 — hex 하드코딩 금지 (anti-patterns.md)
 *   - info → primary tone, warning → accent tone, success → success, danger → danger
 *   - lucide-react 아이콘 사용 (Info / AlertTriangle / CheckCircle2 / AlertOctagon)
 *   - `role="note"` + `aria-label` 로 스크린리더에 분류 통지
 */

import { AlertOctagon, AlertTriangle, CheckCircle2, Info, Lock } from "lucide-react";
import type { ComponentType, SVGProps } from "react";

import type { CalloutComponent } from "@/types/document-schema";

export interface CalloutProps {
  component: CalloutComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

type Variant = CalloutComponent["variant"];

/**
 * variant 별 디자인 스펙.
 * background / borderColor / iconColor 모두 `var(--doc-*)` 참조.
 * `*-soft` 토큰은 globals.css 에서 정의된 연한 배경용 파생 변수.
 */
const VARIANT_STYLE: Record<
  Variant,
  {
    background: string;
    borderColor: string;
    iconColor: string;
    icon: ComponentType<SVGProps<SVGSVGElement>>;
    label: string;
  }
> = {
  info: {
    background: "var(--doc-primary-soft)",
    borderColor: "var(--doc-primary)",
    iconColor: "var(--doc-primary)",
    icon: Info,
    label: "정보",
  },
  warning: {
    background: "var(--doc-accent-soft)",
    borderColor: "var(--doc-accent)",
    iconColor: "var(--doc-accent)",
    icon: AlertTriangle,
    label: "주의",
  },
  success: {
    background: "var(--doc-success-soft)",
    borderColor: "var(--doc-success)",
    iconColor: "var(--doc-success)",
    icon: CheckCircle2,
    label: "성공",
  },
  danger: {
    background: "var(--doc-danger-soft)",
    borderColor: "var(--doc-danger)",
    iconColor: "var(--doc-danger)",
    icon: AlertOctagon,
    label: "위험",
  },
};

export function Callout({ component, isSelected, onSelect }: CalloutProps) {
  const style = VARIANT_STYLE[component.variant];
  const Icon = style.icon;

  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="Callout"
      data-component-id={component.id}
      data-variant={component.variant}
      data-locked={component.locked}
      data-selected={isSelected}
      role="note"
      tabIndex={0}
      aria-label={`${style.label} 강조: ${component.text}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative flex w-full items-start gap-3 transition-colors outline-none"
      style={{
        background: style.background,
        border: `1px solid ${style.borderColor}`,
        borderLeftWidth: "4px",
        borderRadius: "var(--doc-radius-md)",
        padding: "var(--doc-spacing-md)",
        marginTop: "var(--doc-spacing-md)",
        marginBottom: "var(--doc-spacing-md)",
        outline: isSelected ? "2px solid var(--doc-primary)" : undefined,
        outlineOffset: isSelected ? "2px" : undefined,
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
      <Icon
        aria-hidden="true"
        className="h-5 w-5 shrink-0"
        style={{ color: style.iconColor, marginTop: "2px" }}
      />
      <p
        style={{
          color: "var(--doc-text)",
          fontFamily: "var(--doc-font-family)",
          fontSize: "var(--doc-font-size-base)",
          lineHeight: "var(--doc-line-height-normal)",
          fontWeight: 500,
          wordBreak: "keep-all",
          margin: 0,
          flex: 1,
        }}
      >
        {component.text}
      </p>
    </div>
  );
}

export default Callout;
