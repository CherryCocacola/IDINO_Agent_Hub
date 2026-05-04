/**
 * DataTable — 데이터 표 컴포넌트
 *
 * DocumentSchema catalog #9 (MVP). `<figure>`/`<table>` semantic 구조로
 * 렌더하며, 헤더 행은 IDINO primary 배경 + white 전경, 짝수 행 줄무늬는
 * surface 톤으로 IDINO 표 스타일을 구현한다. `emphasis_column_index` 가
 * 지정된 열은 accent-soft 배경으로 강조된다.
 *
 * 제약 방어 로직: rows > 20 또는 headers > 8 이면 잘라내고 console.warn.
 * 반응형: 좁은 iframe 대응을 위해 wrapper에 `overflow-x: auto` 적용.
 */

import { Lock } from "lucide-react";

import type { DataTableComponent } from "@/types/document-schema";

export interface DataTableProps {
  component: DataTableComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

const MAX_ROWS = 20;
const MAX_COLS = 8;

export function DataTable({ component, isSelected, onSelect }: DataTableProps) {
  const headers = component.headers.slice(0, MAX_COLS);
  const rows = component.rows.slice(0, MAX_ROWS).map((row) => row.slice(0, headers.length));

  if (component.headers.length > MAX_COLS) {
    console.warn(
      `[DataTable:${component.id}] headers.length(${component.headers.length}) > ${MAX_COLS}, truncated.`,
    );
  }
  if (component.rows.length > MAX_ROWS) {
    console.warn(
      `[DataTable:${component.id}] rows.length(${component.rows.length}) > ${MAX_ROWS}, truncated.`,
    );
  }

  const emphasisIdx = component.emphasis_column_index;
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <figure
      data-component="DataTable"
      data-component-id={component.id}
      data-locked={component.locked}
      data-selected={isSelected}
      data-row-count={rows.length}
      data-col-count={headers.length}
      role="group"
      tabIndex={0}
      aria-label={component.caption ?? "데이터 표"}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full outline-none"
      style={{
        margin: 0,
        marginBottom: "var(--doc-spacing-lg)",
        padding: "var(--doc-spacing-sm)",
        border: "1px solid var(--doc-border)",
        borderRadius: "var(--doc-radius-md)",
        background: "var(--doc-background)",
        outline: isSelected ? "2px solid var(--doc-primary)" : undefined,
        outlineOffset: isSelected ? "2px" : undefined,
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
      {component.caption && (
        <figcaption
          style={{
            fontSize: "var(--doc-font-size-lg)",
            fontWeight: 600,
            color: "var(--doc-text)",
            fontFamily: "var(--doc-font-family)",
            marginBottom: "var(--doc-spacing-sm)",
            wordBreak: "keep-all",
          }}
        >
          {component.caption}
        </figcaption>
      )}
      <div style={{ width: "100%", overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            fontFamily: "var(--doc-font-family)",
            fontSize: "var(--doc-font-size-sm)",
            color: "var(--doc-text)",
          }}
        >
          <thead>
            <tr>
              {headers.map((h, colIdx) => (
                <th
                  key={`${component.id}-h-${colIdx}`}
                  scope="col"
                  style={{
                    background: "var(--doc-primary)",
                    color: "var(--doc-primary-foreground)",
                    fontWeight: 600,
                    textAlign: "left",
                    padding: "var(--doc-spacing-sm) var(--doc-spacing-md)",
                    borderBottom: "1px solid var(--doc-border)",
                    wordBreak: "keep-all",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIdx) => (
              <tr
                key={`${component.id}-r-${rowIdx}`}
                style={{
                  background: rowIdx % 2 === 1 ? "var(--doc-surface)" : "var(--doc-background)",
                }}
              >
                {row.map((cell, colIdx) => {
                  const isEmphasis = emphasisIdx !== null && colIdx === emphasisIdx;
                  return (
                    <td
                      key={`${component.id}-r-${rowIdx}-c-${colIdx}`}
                      data-emphasis={isEmphasis || undefined}
                      style={{
                        padding: "var(--doc-spacing-sm) var(--doc-spacing-md)",
                        borderBottom: "1px solid var(--doc-border)",
                        background: isEmphasis ? "var(--doc-accent-soft)" : undefined,
                        fontWeight: isEmphasis ? 600 : 400,
                        wordBreak: "keep-all",
                        verticalAlign: "top",
                      }}
                    >
                      {cell}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

export default DataTable;
