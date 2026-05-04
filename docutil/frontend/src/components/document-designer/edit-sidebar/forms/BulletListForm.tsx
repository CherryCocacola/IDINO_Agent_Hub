/**
 * BulletListForm — `BulletList` 컴포넌트 편집 폼
 *
 * Phase 4 S1 D4 산출물. 필수 동작:
 *   - `items[]` 추가 / 삭제 / 재정렬(▲▼)
 *   - `numbered` 체크박스 (ol / ul 전환)
 *   - 각 item 의 `text`, `emphasis` 인라인 편집
 *
 * 서버 검증 (최대 12개, 2레벨) 은 프리뷰 렌더러(BulletList.tsx) 에서도 방어적으로
 * 잘라내지만, 폼 단에서도 12개 도달 시 "추가" 버튼을 비활성화해 UX 일관성 유지.
 *
 * sub_items 편집은 D4 범위 외 (S3 이후). 현재 폼에서는 sub_items 길이만 표시하고
 * 값 자체는 유지한다(원본 보존).
 */

"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import type { ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { BulletItem, BulletListComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type BulletListFormProps = FormProps<BulletListComponent>;

/** 서버/렌더러와 동일한 상한. 초과 시 "추가" 버튼 비활성화. */
export const BULLET_LIST_MAX_ITEMS = 12;

const EMPHASIS_OPTIONS: { value: BulletItem["emphasis"]; label: string }[] = [
  { value: "normal", label: "일반" },
  { value: "bold", label: "굵게" },
  { value: "highlight", label: "하이라이트" },
];

function isItemEmphasis(value: string): value is BulletItem["emphasis"] {
  return value === "normal" || value === "bold" || value === "highlight";
}

function createEmptyItem(): BulletItem {
  return { text: "", sub_items: [], emphasis: "normal" };
}

export function BulletListForm({ component, onLocalPatch, onCommitPatch }: BulletListFormProps) {
  const applyItems = (nextItems: BulletItem[]) => {
    const patch: Partial<BulletListComponent> = { items: nextItems };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleNumberedChange = (checked: boolean | "indeterminate") => {
    const patch: Partial<BulletListComponent> = { numbered: checked === true };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleItemTextChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = component.items.map((it, i) =>
      i === index ? { ...it, text: e.target.value } : it,
    );
    applyItems(next);
  };

  const handleItemEmphasisChange = (index: number) => (value: string) => {
    if (!isItemEmphasis(value)) return;
    const next = component.items.map((it, i) => (i === index ? { ...it, emphasis: value } : it));
    applyItems(next);
  };

  const handleAddItem = () => {
    if (component.items.length >= BULLET_LIST_MAX_ITEMS) return;
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

  const numberedId = `bullet-numbered-${component.id}`;
  const atMax = component.items.length >= BULLET_LIST_MAX_ITEMS;

  return (
    <section
      aria-label="불릿 목록 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="BulletList"
      data-component-id={component.id}
      data-item-count={component.items.length}
    >
      <div className="flex items-center gap-2">
        <Checkbox
          id={numberedId}
          checked={component.numbered}
          onCheckedChange={handleNumberedChange}
          disabled={component.locked}
        />
        <Label htmlFor={numberedId} className="cursor-pointer">
          번호 목록으로 표시
        </Label>
      </div>

      <div className={FORM_FIELD_CLASS}>
        <div className="flex items-center justify-between">
          <Label>
            항목 ({component.items.length}/{BULLET_LIST_MAX_ITEMS})
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddItem}
            disabled={component.locked || atMax}
            aria-label="항목 추가"
          >
            <Plus aria-hidden="true" />
            추가
          </Button>
        </div>

        <ul className="space-y-2" aria-label="목록 항목">
          {component.items.length === 0 ? (
            <li style={FORM_HINT_STYLE}>항목이 없습니다. 추가 버튼으로 첫 항목을 만드세요.</li>
          ) : (
            component.items.map((item, index) => {
              const textId = `bullet-item-text-${component.id}-${index}`;
              const emphasisId = `bullet-item-emphasis-${component.id}-${index}`;
              return (
                <li
                  key={`${component.id}-item-${index}`}
                  className="flex flex-col gap-1.5 rounded-md border p-2"
                  style={{ borderColor: "var(--doc-border)" }}
                  data-item-index={index}
                >
                  <div className="flex items-center gap-1">
                    <Input
                      id={textId}
                      aria-label={`${index + 1}번째 항목 텍스트`}
                      value={item.text}
                      onChange={handleItemTextChange(index)}
                      placeholder="항목 내용"
                      disabled={component.locked}
                      maxLength={500}
                    />
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

                  <div className="flex items-center gap-2">
                    <Label htmlFor={emphasisId} style={FORM_HINT_STYLE}>
                      강조
                    </Label>
                    <Select
                      value={item.emphasis}
                      onValueChange={handleItemEmphasisChange(index)}
                      disabled={component.locked}
                    >
                      <SelectTrigger
                        id={emphasisId}
                        className="h-8"
                        aria-label={`${index + 1}번째 항목 강조`}
                      >
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EMPHASIS_OPTIONS.map((opt) => (
                          <SelectItem key={opt.value} value={opt.value}>
                            {opt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    {item.sub_items.length > 0 && (
                      <span style={FORM_HINT_STYLE}>하위 {item.sub_items.length}개</span>
                    )}
                  </div>
                </li>
              );
            })
          )}
        </ul>
      </div>
    </section>
  );
}

export default BulletListForm;
