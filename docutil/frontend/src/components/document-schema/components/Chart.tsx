/**
 * Chart — bar/line/pie 차트 컴포넌트
 *
 * DocumentSchema catalog #10 (S3 D4 추가). Recharts 를 활용해 세 가지 기본
 * 차트 유형을 렌더한다. IDINO 팔레트를 순환해 시리즈마다 색상을 배정한다.
 *
 * 제약:
 *   - HWPX 빌더에서는 이미지(PNG) 로 degrade — 프런트엔드는 React 렌더만 담당.
 *   - pie 차트는 데이터 구조상 여러 시리즈를 그릴 수 없으므로 `series[0]` 만 사용.
 *   - 시리즈가 1개면 Legend 를 숨겨 노이즈 제거, 2개 이상일 때만 표시.
 *
 * 디자인 규약:
 *   - 모든 색상은 `CHART_PALETTE` 상수로 관리 (hex 하드코딩 허용 범위는 IDINO 팔레트 8색)
 *   - ResponsiveContainer 로 width 100% 확보, height 는 props 또는 기본 300
 *   - 축/그리드/툴팁 텍스트는 `var(--doc-*)` 경유
 */

"use client";

import { Lock } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { ChartComponent } from "@/types/document-schema";

export interface ChartProps {
  component: ChartComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
  /** 차트 높이(px). 기본 300. */
  height?: number;
}

/**
 * IDINO 팔레트 — 차트 시리즈 색상 순환 용도.
 *
 * primary/accent 는 `--doc-primary`/`--doc-accent` 와 동일. Recharts 가 ref 기반
 * 계산에서 CSS 변수를 직접 읽지 못하는 경우가 있어 hex 리터럴로 고정 (예외적으로 허용).
 */
export const CHART_PALETTE: readonly string[] = [
  "#0A4FC2", // IDINO primary
  "#FF6B35", // IDINO accent
  "#10B981", // emerald-500
  "#6B7280", // gray-500
  "#F59E0B", // amber-500
  "#8B5CF6", // violet-500
  "#14B8A6", // teal-500
  "#EC4899", // pink-500
];

/** 팔레트를 시리즈 index 로 순환 조회. */
function paletteColor(idx: number): string {
  return CHART_PALETTE[idx % CHART_PALETTE.length];
}

/** 기본 차트 높이. */
const DEFAULT_CHART_HEIGHT = 300;

/**
 * Recharts 의 `data` 배열 형태로 변환.
 * labels + 여러 시리즈를 [{label, series1, series2, ...}] 의 long-form 으로.
 */
function toBarLineData(component: ChartComponent): Record<string, string | number>[] {
  const { labels, series } = component.data;
  return labels.map((label, i) => {
    const row: Record<string, string | number> = { label };
    series.forEach((s) => {
      row[s.name] = s.values[i] ?? 0;
    });
    return row;
  });
}

/** pie 전용: 첫 시리즈만 사용해 `[{name, value}]` 변환. */
function toPieData(component: ChartComponent): { name: string; value: number }[] {
  const { labels, series } = component.data;
  const first = series[0];
  if (!first) return [];
  return labels.map((label, i) => ({
    name: label,
    value: first.values[i] ?? 0,
  }));
}

export function Chart({ component, isSelected, onSelect, height }: ChartProps) {
  const chartHeight = height ?? DEFAULT_CHART_HEIGHT;
  const seriesCount = component.data.series.length;
  const showLegend = seriesCount >= 2 || component.chart_type === "pie";

  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <figure
      data-component="Chart"
      data-component-id={component.id}
      data-chart-type={component.chart_type}
      data-series-count={seriesCount}
      data-locked={component.locked}
      data-selected={isSelected}
      role="group"
      tabIndex={0}
      aria-label={component.title || `${component.chart_type} 차트`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full outline-none"
      style={{
        margin: 0,
        marginTop: "var(--doc-spacing-md)",
        marginBottom: "var(--doc-spacing-lg)",
        padding: "var(--doc-spacing-md)",
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
      {component.title && (
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
          {component.title}
        </figcaption>
      )}
      <div style={{ width: "100%", height: chartHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart(component, showLegend)}
        </ResponsiveContainer>
      </div>
    </figure>
  );
}

/**
 * chart_type 분기 — 각 유형에 맞는 Recharts JSX 반환.
 * ResponsiveContainer 의 children 은 단일 Element 여야 하므로 분기 함수로 분리.
 */
function renderChart(component: ChartComponent, showLegend: boolean): React.ReactElement {
  const gridColor = "var(--doc-border)";
  const axisColor = "var(--doc-text-muted)";

  switch (component.chart_type) {
    case "bar": {
      const data = toBarLineData(component);
      return (
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            stroke={axisColor}
            tick={{ fontSize: 12, fill: "var(--doc-text-muted)" }}
          />
          <YAxis
            stroke={axisColor}
            tick={{ fontSize: 12, fill: "var(--doc-text-muted)" }}
            allowDecimals={false}
          />
          <Tooltip
            cursor={{ fill: "var(--doc-primary-soft)" }}
            contentStyle={{
              borderRadius: 6,
              border: "1px solid var(--doc-border)",
              background: "var(--doc-background)",
              color: "var(--doc-text)",
              fontSize: 12,
            }}
          />
          {showLegend && <Legend wrapperStyle={{ fontSize: 12 }} />}
          {component.data.series.map((s, i) => (
            <Bar
              key={s.name}
              dataKey={s.name}
              fill={paletteColor(i)}
              radius={[4, 4, 0, 0]}
              maxBarSize={48}
            />
          ))}
        </BarChart>
      );
    }
    case "line": {
      const data = toBarLineData(component);
      return (
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="label"
            stroke={axisColor}
            tick={{ fontSize: 12, fill: "var(--doc-text-muted)" }}
          />
          <YAxis
            stroke={axisColor}
            tick={{ fontSize: 12, fill: "var(--doc-text-muted)" }}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              borderRadius: 6,
              border: "1px solid var(--doc-border)",
              background: "var(--doc-background)",
              color: "var(--doc-text)",
              fontSize: 12,
            }}
          />
          {showLegend && <Legend wrapperStyle={{ fontSize: 12 }} />}
          {component.data.series.map((s, i) => (
            <Line
              key={s.name}
              type="monotone"
              dataKey={s.name}
              stroke={paletteColor(i)}
              strokeWidth={2}
              dot={{ r: 3, fill: paletteColor(i) }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      );
    }
    case "pie": {
      const data = toPieData(component);
      return (
        <PieChart>
          <Tooltip
            contentStyle={{
              borderRadius: 6,
              border: "1px solid var(--doc-border)",
              background: "var(--doc-background)",
              color: "var(--doc-text)",
              fontSize: 12,
            }}
          />
          {showLegend && <Legend wrapperStyle={{ fontSize: 12 }} />}
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            outerRadius="80%"
            label={{ fontSize: 12, fill: "var(--doc-text)" }}
          >
            {data.map((_, i) => (
              <Cell key={`cell-${i}`} fill={paletteColor(i)} />
            ))}
          </Pie>
        </PieChart>
      );
    }
    default: {
      // exhaustive check — 새로운 chart_type 추가 시 컴파일 에러 유도.
      const _exhaustive: never = component.chart_type;
      return <g data-exhaustive={String(_exhaustive)} />;
    }
  }
}

export default Chart;
