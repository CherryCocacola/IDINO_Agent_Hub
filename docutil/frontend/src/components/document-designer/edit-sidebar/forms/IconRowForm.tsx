/**
 * IconRowForm — `IconRow` 컴포넌트 편집 폼
 *
 * Phase 4 S3 D3 산출물. 필수 동작:
 *   - `items[]` 추가 / 삭제 / 재정렬(▲▼)
 *   - 각 item 의 `icon`(Select — allowlist), `label`(Input), `description`(Input, optional)
 *
 * 제약:
 *   - 아이콘은 IconRow 컴포넌트에서 export 한 `ICON_ALLOWLIST_NAMES` (30종) 중에서만 선택
 *   - 최대 `ICON_ROW_MAX_ITEMS` (8) — 초과 시 추가 비활성화
 *   - description 빈 문자열은 schema `null` 로 정규화
 */

"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import type { ChangeEvent } from "react";

import {
  ICON_ALLOWLIST_NAMES,
  ICON_ROW_MAX_ITEMS,
} from "@/components/document-schema/components/IconRow";
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
import type { IconRowComponent, IconRowItem } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type IconRowFormProps = FormProps<IconRowComponent>;

/** 신규 아이템 기본값 — 가장 범용적인 "Star" 아이콘을 기본 제시. */
function createEmptyItem(): IconRowItem {
  return { icon: "Star", label: "", description: null };
}

/** Select 값이 allowlist 에 속하는지 확인 — 비속 시 변경 무시. */
function isAllowedIcon(value: string): boolean {
  return (ICON_ALLOWLIST_NAMES as readonly string[]).includes(value);
}

export function IconRowForm({ component, onLocalPatch, onCommitPatch }: IconRowFormProps) {
  const applyItems = (nextItems: IconRowItem[]) => {
    const patch: Partial<IconRowComponent> = { items: nextItems };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleIconChange = (index: number) => (value: string) => {
    if (!isAllowedIcon(value)) return;
    const next = component.items.map((it, i) => (i === index ? { ...it, icon: value } : it));
    applyItems(next);
  };

  const handleLabelChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = component.items.map((it, i) =>
      i === index ? { ...it, label: e.target.value } : it,
    );
    applyItems(next);
  };

  const handleDescriptionChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const normalized = raw.trim().length === 0 ? null : raw;
    const next = component.items.map((it, i) =>
      i === index ? { ...it, description: normalized } : it,
    );
    applyItems(next);
  };

  const handleAddItem = () => {
    if (component.items.length >= ICON_ROW_MAX_ITEMS) return;
    applyItems([...component.items, createEmptyItem()]);
  };

  const handleRemoveItem = (index: number) => () => {
    const next = component.items.filter((_, i) => i !== index);
    applyItems(next);
  };

  const handleMoveItem = (index: number, direction: -1 | 1) => () => {
    const target = index + direction;
    if (target < 0 || target >= component.items.length) return;
    const next = component.items.slice();
    const [moved] = next.splice(index, 1);
    next.splice(target, 0, moved);
    applyItems(next);
  };

  const atMax = component.items.length >= ICON_ROW_MAX_ITEMS;

  return (
    <section
      aria-label="아이콘 행 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="IconRow"
      data-component-id={component.id}
      data-item-count={component.items.length}
    >
      <div className={FORM_FIELD_CLASS}>
        <div className="flex items-center justify-between">
          <Label>
            항목 ({component.items.length}/{ICON_ROW_MAX_ITEMS})
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddItem}
            disabled={component.locked || atMax}
            aria-label="아이콘 항목 추가"
          >
            <Plus aria-hidden="true" />
            추가
          </Button>
        </div>

        <ol className="space-y-3" aria-label="아이콘 항목 목록">
          {component.items.length === 0 ? (
            <li style={FORM_HINT_STYLE}>항목이 없습니다. 추가 버튼으로 첫 아이콘을 등록하세요.</li>
          ) : (
            component.items.map((item, index) => {
              const iconId = `iconrow-icon-${component.id}-${index}`;
              const labelId = `iconrow-label-${component.id}-${index}`;
              const descId = `iconrow-desc-${component.id}-${index}`;
              return (
                <li
                  key={`${component.id}-item-${index}`}
                  className="flex flex-col gap-1.5 rounded-md border p-2"
                  style={{ borderColor: "var(--doc-border)" }}
                  data-item-index={index}
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
                        onClick={handleMoveItem(index, -1)}
                        disabled={component.locked || index === 0}
                        aria-label={`${index + 1}번째 항목 위로 이동`}
                      >
                        <ArrowUp aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleMoveItem(index, 1)}
                        disabled={component.locked || index === component.items.length - 1}
                        aria-label={`${index + 1}번째 항목 아래로 이동`}
                      >
                        <ArrowDown aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleRemoveItem(index)}
                        disabled={component.locked}
                        aria-label={`${index + 1}번째 항목 삭제`}
                      >
                        <Trash2 aria-hidden="true" />
                      </Button>
                    </div>
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={iconId} style={FORM_HINT_STYLE}>
                      아이콘
                    </Label>
                    <Select
                      value={item.icon}
                      onValueChange={handleIconChange(index)}
                      disabled={component.locked}
                    >
                      <SelectTrigger
                        id={iconId}
                        className="h-8"
                        aria-label={`${index + 1}번째 항목 아이콘`}
                      >
                        <SelectValue placeholder="아이콘 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        {ICON_ALLOWLIST_NAMES.map((name) => (
                          <SelectItem key={name} value={name}>
                            {name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={labelId} style={FORM_HINT_STYLE}>
                      라벨
                    </Label>
                    <Input
                      id={labelId}
                      aria-label={`${index + 1}번째 항목 라벨`}
                      value={item.label}
                      onChange={handleLabelChange(index)}
                      placeholder="짧은 제목"
                      disabled={component.locked}
                      maxLength={40}
                    />
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={descId} style={FORM_HINT_STYLE}>
                      설명 (선택)
                    </Label>
                    <Input
                      id={descId}
                      aria-label={`${index + 1}번째 항목 설명`}
                      value={item.description ?? ""}
                      onChange={handleDescriptionChange(index)}
                      placeholder="한 줄 보조 설명"
                      disabled={component.locked}
                      maxLength={120}
                    />
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

export default IconRowForm;
