/**
 * KPIForm — `KPI` 컴포넌트 편집 폼
 *
 * Phase 4 S1 D4 산출물. 필수 필드:
 *   - `label`, `value` (Input, 필수)
 *   - `delta` (Input, nullable)
 *   - `delta_direction` (up/down/flat + "자동추정") Select
 *
 * delta_direction 이 `null` 이면 렌더러(KPI.tsx) 가 delta 문자열의 `+`/`-` 접두어로
 * 자동 추정하므로, 폼에서는 "자동 추정" 이라는 sentinel 옵션을 노출한다.
 */

"use client";

import type { ChangeEvent } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { KPIComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type KPIFormProps = FormProps<KPIComponent>;

/** Select 의 "null" sentinel. Radix Select 는 빈 문자열 value 를 허용하지 않는다. */
const DIRECTION_AUTO = "__auto__" as const;

const DIRECTION_OPTIONS: { value: string; label: string }[] = [
  { value: DIRECTION_AUTO, label: "자동 추정" },
  { value: "up", label: "증가 (▲)" },
  { value: "down", label: "감소 (▼)" },
  { value: "flat", label: "변동 없음 (—)" },
];

function parseDirection(value: string): KPIComponent["delta_direction"] {
  if (value === "up" || value === "down" || value === "flat") return value;
  return null;
}

export function KPIForm({ component, onLocalPatch, onCommitPatch }: KPIFormProps) {
  const apply = (patch: Partial<KPIComponent>) => {
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleLabelChange = (e: ChangeEvent<HTMLInputElement>) => apply({ label: e.target.value });
  const handleValueChange = (e: ChangeEvent<HTMLInputElement>) => apply({ value: e.target.value });
  const handleDeltaChange = (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    apply({ delta: raw === "" ? null : raw });
  };
  const handleDirectionChange = (value: string) =>
    apply({ delta_direction: parseDirection(value) });
  const handleDescriptionChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const raw = e.target.value;
    apply({ description: raw === "" ? null : raw });
  };

  const labelId = `kpi-label-${component.id}`;
  const valueId = `kpi-value-${component.id}`;
  const deltaId = `kpi-delta-${component.id}`;
  const directionId = `kpi-direction-${component.id}`;
  const descriptionId = `kpi-description-${component.id}`;

  const directionSelectValue = component.delta_direction ?? DIRECTION_AUTO;

  return (
    <section
      aria-label="KPI 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="KPI"
      data-component-id={component.id}
    >
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={labelId}>지표명</Label>
        <Input
          id={labelId}
          value={component.label}
          onChange={handleLabelChange}
          placeholder="예: 월간 활성 사용자"
          disabled={component.locked}
          maxLength={100}
          autoComplete="off"
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={valueId}>값</Label>
        <Input
          id={valueId}
          value={component.value}
          onChange={handleValueChange}
          placeholder="예: 12,340"
          disabled={component.locked}
          maxLength={60}
          autoComplete="off"
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={deltaId}>변동치</Label>
        <Input
          id={deltaId}
          value={component.delta ?? ""}
          onChange={handleDeltaChange}
          placeholder="예: +8.2%"
          disabled={component.locked}
          maxLength={40}
          autoComplete="off"
        />
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={directionId}>변동 방향</Label>
        <Select
          value={directionSelectValue}
          onValueChange={handleDirectionChange}
          disabled={component.locked}
        >
          <SelectTrigger id={directionId} aria-label="변동 방향">
            <SelectValue placeholder="변동 방향" />
          </SelectTrigger>
          <SelectContent>
            {DIRECTION_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={descriptionId}>설명 (선택)</Label>
        <Textarea
          id={descriptionId}
          value={component.description ?? ""}
          onChange={handleDescriptionChange}
          placeholder="보조 설명을 입력하세요"
          disabled={component.locked}
          rows={2}
          maxLength={200}
        />
      </div>
    </section>
  );
}

export default KPIForm;
