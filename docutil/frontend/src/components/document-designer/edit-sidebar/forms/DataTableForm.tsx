/**
 * DataTableForm — `DataTable` 컴포넌트 편집 폼
 *
 * Phase 4 S1 D4 산출물. 필수 동작:
 *   - `headers[]` 열 추가 / 삭제 / 이름 편집
 *   - `rows[][]` 행 추가 / 삭제 / 셀 인라인 편집 (2D 그리드)
 *   - `caption` (nullable Input)
 *   - `emphasis_column_index` (nullable, "강조 없음" + 각 열 인덱스)
 *
 * 서버 제약 (최대 8열 × 20행) 과 동기화:
 *   - 열 추가 시 headers.length ≥ MAX_COLS 이면 버튼 disable.
 *   - 행 추가 시 rows.length ≥ MAX_ROWS 이면 버튼 disable.
 *   - 열 삭제 시 각 row 에서 동일 index 의 셀도 삭제해 행 길이 불변식 유지.
 *   - emphasis_column_index 가 삭제된 열을 가리키면 null 로 리셋.
 */

"use client";

import { Plus, Trash2 } from "lucide-react";
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
import type { DataTableComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type DataTableFormProps = FormProps<DataTableComponent>;

/** 서버/렌더러와 동일한 상한. */
export const DATA_TABLE_MAX_ROWS = 20;
export const DATA_TABLE_MAX_COLS = 8;

/** Radix Select 는 "" 값을 허용하지 않아 sentinel 로 처리. */
const EMPHASIS_NONE = "__none__" as const;

function normalizeRow(row: string[], colCount: number): string[] {
  if (row.length === colCount) return row;
  if (row.length > colCount) return row.slice(0, colCount);
  return [...row, ...Array.from({ length: colCount - row.length }, () => "")];
}

export function DataTableForm({ component, onLocalPatch, onCommitPatch }: DataTableFormProps) {
  const apply = (patch: Partial<DataTableComponent>) => {
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const colCount = component.headers.length;
  const atMaxCols = colCount >= DATA_TABLE_MAX_COLS;
  const atMaxRows = component.rows.length >= DATA_TABLE_MAX_ROWS;

  // ── Caption ─────────────────────────────────────────────────────────────
  const handleCaptionChange = (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    apply({ caption: raw === "" ? null : raw });
  };

  // ── Headers ─────────────────────────────────────────────────────────────
  const handleHeaderChange = (colIdx: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const nextHeaders = component.headers.map((h, i) => (i === colIdx ? e.target.value : h));
    apply({ headers: nextHeaders });
  };

  const handleAddColumn = () => {
    if (atMaxCols) return;
    const nextHeaders = [...component.headers, `열 ${colCount + 1}`];
    const nextRows = component.rows.map((row) => [...row, ""]);
    apply({ headers: nextHeaders, rows: nextRows });
  };

  const handleRemoveColumn = (colIdx: number) => () => {
    if (colCount === 0) return;
    const nextHeaders = component.headers.filter((_, i) => i !== colIdx);
    const nextRows = component.rows.map((row) => row.filter((_, i) => i !== colIdx));
    const nextEmphasis =
      component.emphasis_column_index === null
        ? null
        : component.emphasis_column_index === colIdx
          ? null
          : component.emphasis_column_index > colIdx
            ? component.emphasis_column_index - 1
            : component.emphasis_column_index;
    apply({
      headers: nextHeaders,
      rows: nextRows,
      emphasis_column_index: nextEmphasis,
    });
  };

  // ── Rows ────────────────────────────────────────────────────────────────
  const handleCellChange =
    (rowIdx: number, colIdx: number) => (e: ChangeEvent<HTMLInputElement>) => {
      const nextRows = component.rows.map((row, r) => {
        if (r !== rowIdx) return row;
        const normalized = normalizeRow(row, colCount);
        return normalized.map((cell, c) => (c === colIdx ? e.target.value : cell));
      });
      apply({ rows: nextRows });
    };

  const handleAddRow = () => {
    if (atMaxRows) return;
    const newRow = Array.from({ length: colCount }, () => "");
    apply({ rows: [...component.rows, newRow] });
  };

  const handleRemoveRow = (rowIdx: number) => () => {
    const nextRows = component.rows.filter((_, i) => i !== rowIdx);
    apply({ rows: nextRows });
  };

  // ── Emphasis column ─────────────────────────────────────────────────────
  const handleEmphasisChange = (value: string) => {
    if (value === EMPHASIS_NONE) {
      apply({ emphasis_column_index: null });
      return;
    }
    const idx = Number(value);
    if (!Number.isInteger(idx) || idx < 0 || idx >= colCount) return;
    apply({ emphasis_column_index: idx });
  };

  const captionId = `datatable-caption-${component.id}`;
  const emphasisId = `datatable-emphasis-${component.id}`;
  const emphasisSelectValue =
    component.emphasis_column_index === null || component.emphasis_column_index >= colCount
      ? EMPHASIS_NONE
      : String(component.emphasis_column_index);

  return (
    <section
      aria-label="데이터 표 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="DataTable"
      data-component-id={component.id}
      data-row-count={component.rows.length}
      data-col-count={colCount}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={captionId}>캡션 (선택)</Label>
        <Input
          id={captionId}
          value={component.caption ?? ""}
          onChange={handleCaptionChange}
          placeholder="표 캡션"
          disabled={component.locked}
          maxLength={200}
          autoComplete="off"
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <div className="flex items-center justify-between">
          <Label>
            헤더 ({colCount}/{DATA_TABLE_MAX_COLS})
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddColumn}
            disabled={component.locked || atMaxCols}
            aria-label="열 추가"
          >
            <Plus aria-hidden="true" />열 추가
          </Button>
        </div>

        {colCount === 0 ? (
          <p style={FORM_HINT_STYLE}>열이 없습니다. 열 추가 버튼을 눌러 표를 시작하세요.</p>
        ) : (
          <ul className="space-y-1.5" aria-label="헤더 목록">
            {component.headers.map((h, colIdx) => (
              <li key={`${component.id}-h-${colIdx}`} className="flex items-center gap-1">
                <Input
                  aria-label={`${colIdx + 1}번째 헤더`}
                  value={h}
                  onChange={handleHeaderChange(colIdx)}
                  placeholder={`열 ${colIdx + 1}`}
                  disabled={component.locked}
                  maxLength={100}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={handleRemoveColumn(colIdx)}
                  disabled={component.locked}
                  aria-label={`${colIdx + 1}번째 열 삭제`}
                >
                  <Trash2 aria-hidden="true" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={FORM_FIELD_CLASS}>
        <div className="flex items-center justify-between">
          <Label>
            행 ({component.rows.length}/{DATA_TABLE_MAX_ROWS})
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddRow}
            disabled={component.locked || atMaxRows || colCount === 0}
            aria-label="행 추가"
          >
            <Plus aria-hidden="true" />행 추가
          </Button>
        </div>

        {component.rows.length === 0 ? (
          <p style={FORM_HINT_STYLE}>행이 없습니다. 행 추가 버튼으로 첫 행을 만드세요.</p>
        ) : (
          <div
            className="overflow-x-auto rounded-md border"
            style={{ borderColor: "var(--doc-border)" }}
          >
            <table className="w-full text-sm" aria-label="표 데이터 편집 그리드">
              <thead>
                <tr>
                  {component.headers.map((h, colIdx) => (
                    <th
                      key={`${component.id}-gh-${colIdx}`}
                      scope="col"
                      className="px-1 py-1 text-left text-xs font-medium"
                      style={{ color: "var(--doc-text-muted)" }}
                    >
                      {h || `열 ${colIdx + 1}`}
                    </th>
                  ))}
                  <th scope="col" className="w-8" aria-label="행 삭제 열" />
                </tr>
              </thead>
              <tbody>
                {component.rows.map((row, rowIdx) => {
                  const normalized = normalizeRow(row, colCount);
                  return (
                    <tr key={`${component.id}-gr-${rowIdx}`} data-row-index={rowIdx}>
                      {normalized.map((cell, colIdx) => (
                        <td
                          key={`${component.id}-gr-${rowIdx}-c-${colIdx}`}
                          className="p-1"
                          data-col-index={colIdx}
                        >
                          <Input
                            aria-label={`${rowIdx + 1}행 ${colIdx + 1}열 셀`}
                            value={cell}
                            onChange={handleCellChange(rowIdx, colIdx)}
                            disabled={component.locked}
                            maxLength={500}
                            className="h-8"
                          />
                        </td>
                      ))}
                      <td className="p-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={handleRemoveRow(rowIdx)}
                          disabled={component.locked}
                          aria-label={`${rowIdx + 1}번째 행 삭제`}
                        >
                          <Trash2 aria-hidden="true" />
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={emphasisId}>강조 열</Label>
        <Select
          value={emphasisSelectValue}
          onValueChange={handleEmphasisChange}
          disabled={component.locked || colCount === 0}
        >
          <SelectTrigger id={emphasisId} aria-label="강조 열 선택">
            <SelectValue placeholder="강조 열" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={EMPHASIS_NONE}>강조 없음</SelectItem>
            {component.headers.map((h, colIdx) => (
              <SelectItem key={`${component.id}-emp-${colIdx}`} value={String(colIdx)}>
                {h || `열 ${colIdx + 1}`}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </section>
  );
}

export default DataTableForm;
