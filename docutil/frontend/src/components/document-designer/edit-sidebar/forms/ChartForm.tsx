/**
 * ChartForm — `Chart` 컴포넌트 편집 폼
 *
 * Phase 4 S3 D4 산출물. Chart 는 구조가 복잡(labels + 다중 시리즈)하므로
 * "과한 추상화 금지" 원칙에 따라 간소화된 편집 UX 를 제공한다.
 *   - chart_type (Select): bar / line / pie
 *   - title (Input)
 *   - labels: 콤마 구분 문자열로 편집 ("Q1, Q2, Q3, Q4")
 *   - series: 각 시리즈 name + values(콤마 구분 숫자) 을 한 행으로 편집
 *
 * 콤마 편집 방식을 선택한 이유:
 *   - BulletList / Timeline 스타일의 "한 항목당 한 행" 인라인 편집은 labels × series 2차원이어서
 *     S3 범위 (1일) 내에 견고하게 구현하기 어렵다.
 *   - JSON 직접편집은 사용자 실수 위험이 크다.
 *   - 콤마는 한국어 사용자에게 친숙하고 파싱이 명확하다.
 *
 * 파싱 규약:
 *   - labels: `split(",")` + `trim()`, 빈 문자열 제거
 *   - values: `split(",")` + `trim()`, `Number()` 로 변환 실패 시 0 fallback + 경고 표시
 *   - labels.length 와 각 series.values.length 는 서버 검증을 맡기고, 폼은 사용자 수정 중
 *     길이 불일치를 허용한다 (편집 중간 상태).
 */

"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import { useMemo } from "react";
import type { ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ChartComponent, ChartSeries } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type ChartFormProps = FormProps<ChartComponent>;

/** UX 상한 — 과도한 입력 방지. */
export const CHART_MAX_SERIES = 5;
/** UX 상한 — 라벨 수 (X축 카테고리). */
export const CHART_MAX_LABELS = 20;

const CHART_TYPE_OPTIONS: { value: ChartComponent["chart_type"]; label: string }[] = [
  { value: "bar", label: "막대 (Bar)" },
  { value: "line", label: "선 (Line)" },
  { value: "pie", label: "원형 (Pie)" },
];

function isChartType(value: string): value is ChartComponent["chart_type"] {
  return value === "bar" || value === "line" || value === "pie";
}

/** 콤마 구분 문자열 → 문자열 배열 (빈 항목 제거). */
function parseLabels(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

/** 콤마 구분 문자열 → 숫자 배열. 변환 불가는 0 으로 치환. */
function parseValues(raw: string): number[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map((s) => {
      const n = Number(s);
      return Number.isFinite(n) ? n : 0;
    });
}

/** 숫자 배열 → 콤마 구분 문자열. */
function formatValues(values: number[]): string {
  return values.join(", ");
}

/** 시리즈 기본값. */
function createEmptySeries(): ChartSeries {
  return { name: "시리즈", values: [] };
}

export function ChartForm({ component, onLocalPatch, onCommitPatch }: ChartFormProps) {
  const labelsText = useMemo(() => component.data.labels.join(", "), [component.data.labels]);

  const applyData = (next: ChartComponent["data"]) => {
    const patch: Partial<ChartComponent> = { data: next };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleTypeChange = (value: string) => {
    if (!isChartType(value)) return;
    const patch: Partial<ChartComponent> = { chart_type: value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleTitleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const patch: Partial<ChartComponent> = { title: e.target.value };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleLabelsChange = (e: ChangeEvent<HTMLInputElement>) => {
    const parsed = parseLabels(e.target.value).slice(0, CHART_MAX_LABELS);
    applyData({ ...component.data, labels: parsed });
  };

  const handleSeriesNameChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = component.data.series.map((s, i) =>
      i === index ? { ...s, name: e.target.value } : s,
    );
    applyData({ ...component.data, series: next });
  };

  const handleSeriesValuesChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const nextValues = parseValues(e.target.value);
    const next = component.data.series.map((s, i) =>
      i === index ? { ...s, values: nextValues } : s,
    );
    applyData({ ...component.data, series: next });
  };

  const handleAddSeries = () => {
    if (component.data.series.length >= CHART_MAX_SERIES) return;
    applyData({
      ...component.data,
      series: [...component.data.series, createEmptySeries()],
    });
  };

  const handleRemoveSeries = (index: number) => () => {
    const next = component.data.series.filter((_, i) => i !== index);
    applyData({ ...component.data, series: next });
  };

  const handleMoveSeries = (index: number, direction: -1 | 1) => () => {
    const target = index + direction;
    if (target < 0 || target >= component.data.series.length) return;
    const next = component.data.series.slice();
    const [moved] = next.splice(index, 1);
    next.splice(target, 0, moved);
    applyData({ ...component.data, series: next });
  };

  const typeId = `chart-type-${component.id}`;
  const titleId = `chart-title-${component.id}`;
  const labelsId = `chart-labels-${component.id}`;
  const labelCount = component.data.labels.length;
  const atMaxSeries = component.data.series.length >= CHART_MAX_SERIES;

  return (
    <section
      aria-label="차트 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="Chart"
      data-component-id={component.id}
      data-chart-type={component.chart_type}
      data-series-count={component.data.series.length}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={typeId}>차트 유형</Label>
        <Select
          value={component.chart_type}
          onValueChange={handleTypeChange}
          disabled={component.locked}
        >
          <SelectTrigger id={typeId} aria-label="차트 유형">
            <SelectValue placeholder="유형 선택" />
          </SelectTrigger>
          <SelectContent>
            {CHART_TYPE_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={titleId}>제목</Label>
        <Input
          id={titleId}
          value={component.title}
          onChange={handleTitleChange}
          placeholder="차트 제목"
          disabled={component.locked}
          maxLength={120}
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={labelsId}>
          라벨 (X축 · {labelCount}/{CHART_MAX_LABELS})
        </Label>
        <Input
          id={labelsId}
          value={labelsText}
          onChange={handleLabelsChange}
          placeholder="예: Q1, Q2, Q3, Q4"
          disabled={component.locked}
          maxLength={400}
          aria-describedby={`${labelsId}-hint`}
        />
        <span id={`${labelsId}-hint`} style={FORM_HINT_STYLE}>
          콤마(,)로 구분해 입력하세요.
        </span>
      </div>

      <div className={FORM_FIELD_CLASS}>
        <div className="flex items-center justify-between">
          <Label>
            데이터 시리즈 ({component.data.series.length}/{CHART_MAX_SERIES})
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddSeries}
            disabled={component.locked || atMaxSeries}
            aria-label="시리즈 추가"
          >
            <Plus aria-hidden="true" />
            추가
          </Button>
        </div>

        {component.chart_type === "pie" && component.data.series.length > 1 && (
          <span style={FORM_HINT_STYLE}>
            원형 차트는 첫 번째 시리즈만 사용됩니다. 나머지는 무시돼요.
          </span>
        )}

        <ol className="space-y-3" aria-label="시리즈 목록">
          {component.data.series.length === 0 ? (
            <li style={FORM_HINT_STYLE}>시리즈가 없습니다. 추가 버튼으로 첫 시리즈를 만드세요.</li>
          ) : (
            component.data.series.map((series, index) => {
              const nameId = `chart-series-name-${component.id}-${index}`;
              const valuesId = `chart-series-values-${component.id}-${index}`;
              const valuesText = formatValues(series.values);
              const mismatch =
                labelCount > 0 && series.values.length > 0 && series.values.length !== labelCount;
              return (
                <li
                  key={`${component.id}-series-${index}`}
                  className="flex flex-col gap-1.5 rounded-md border p-2"
                  style={{ borderColor: "var(--doc-border)" }}
                  data-series-index={index}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span
                      aria-hidden="true"
                      style={{
                        fontSize: "var(--doc-font-size-xs)",
                        fontWeight: 600,
                        color: "var(--doc-text-muted)",
                      }}
                    >
                      #{index + 1}
                    </span>
                    <div className="flex items-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleMoveSeries(index, -1)}
                        disabled={component.locked || index === 0}
                        aria-label={`${index + 1}번째 시리즈 위로 이동`}
                      >
                        <ArrowUp aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleMoveSeries(index, 1)}
                        disabled={component.locked || index === component.data.series.length - 1}
                        aria-label={`${index + 1}번째 시리즈 아래로 이동`}
                      >
                        <ArrowDown aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleRemoveSeries(index)}
                        disabled={component.locked}
                        aria-label={`${index + 1}번째 시리즈 삭제`}
                      >
                        <Trash2 aria-hidden="true" />
                      </Button>
                    </div>
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={nameId} style={FORM_HINT_STYLE}>
                      시리즈 이름
                    </Label>
                    <Input
                      id={nameId}
                      aria-label={`${index + 1}번째 시리즈 이름`}
                      value={series.name}
                      onChange={handleSeriesNameChange(index)}
                      placeholder="예: 매출, 비용"
                      disabled={component.locked}
                      maxLength={40}
                    />
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={valuesId} style={FORM_HINT_STYLE}>
                      값 ({series.values.length}개)
                    </Label>
                    <Input
                      id={valuesId}
                      aria-label={`${index + 1}번째 시리즈 값 목록`}
                      value={valuesText}
                      onChange={handleSeriesValuesChange(index)}
                      placeholder="예: 120, 150, 180, 210"
                      disabled={component.locked}
                      maxLength={400}
                      inputMode="decimal"
                    />
                    {mismatch && (
                      <span
                        role="alert"
                        style={{
                          ...FORM_HINT_STYLE,
                          color: "var(--doc-danger)",
                        }}
                      >
                        값 개수({series.values.length})가 라벨 개수({labelCount})와 다릅니다.
                      </span>
                    )}
                  </div>
                </li>
              );
            })
          )}
        </ol>
      </div>
    </section>
  );
}

export default ChartForm;
