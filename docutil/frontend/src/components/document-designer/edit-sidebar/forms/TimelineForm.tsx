/**
 * TimelineForm — `Timeline` 컴포넌트 편집 폼
 *
 * Phase 4 S3 D2 산출물. 필수 동작:
 *   - `events[]` 추가 / 삭제 / 재정렬(▲▼)
 *   - 각 event 의 `date`(Input), `title`(Input), `description`(Textarea, optional) 인라인 편집
 *
 * 구현 패턴은 BulletListForm 의 배열 편집을 그대로 따른다 (agent-collaboration.md §"과한 추상화 금지").
 *
 * 제약:
 *   - 프론트엔드에서 공식 최대 개수는 정의되지 않았지만 UX 부담을 막기 위해 10개로 제한한다.
 *   - description 빈 문자열은 schema `null` 로 정규화.
 */

"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import type { ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { TimelineComponent, TimelineEvent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type TimelineFormProps = FormProps<TimelineComponent>;

/** UX 측면에서 권장하는 최대 이벤트 수. 서버 검증은 별도. */
export const TIMELINE_MAX_EVENTS = 10;

/** 새 이벤트 생성 시 기본값. date 는 오늘 날짜로 사전 채움 (사용자 수정 용이). */
function createEmptyEvent(): TimelineEvent {
  const today = new Date();
  const iso = today.toISOString().slice(0, 10); // YYYY-MM-DD
  return { date: iso, title: "", description: null };
}

export function TimelineForm({ component, onLocalPatch, onCommitPatch }: TimelineFormProps) {
  const applyEvents = (nextEvents: TimelineEvent[]) => {
    const patch: Partial<TimelineComponent> = { events: nextEvents };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleFieldChange =
    (index: number, field: "date" | "title") => (e: ChangeEvent<HTMLInputElement>) => {
      const next = component.events.map((ev, i) =>
        i === index ? { ...ev, [field]: e.target.value } : ev,
      );
      applyEvents(next);
    };

  const handleDescriptionChange = (index: number) => (e: ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    const normalized = value.trim().length === 0 ? null : value;
    const next = component.events.map((ev, i) =>
      i === index ? { ...ev, description: normalized } : ev,
    );
    applyEvents(next);
  };

  const handleAddEvent = () => {
    if (component.events.length >= TIMELINE_MAX_EVENTS) return;
    applyEvents([...component.events, createEmptyEvent()]);
  };

  const handleRemoveEvent = (index: number) => () => {
    const next = component.events.filter((_, i) => i !== index);
    applyEvents(next);
  };

  const handleMoveEvent = (index: number, direction: -1 | 1) => () => {
    const target = index + direction;
    if (target < 0 || target >= component.events.length) return;
    const next = component.events.slice();
    const [moved] = next.splice(index, 1);
    next.splice(target, 0, moved);
    applyEvents(next);
  };

  const atMax = component.events.length >= TIMELINE_MAX_EVENTS;

  return (
    <section
      aria-label="타임라인 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="Timeline"
      data-component-id={component.id}
      data-event-count={component.events.length}
    >
      <div className={FORM_FIELD_CLASS}>
        <div className="flex items-center justify-between">
          <Label>
            이벤트 ({component.events.length}/{TIMELINE_MAX_EVENTS})
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddEvent}
            disabled={component.locked || atMax}
            aria-label="이벤트 추가"
          >
            <Plus aria-hidden="true" />
            추가
          </Button>
        </div>

        <ol className="space-y-3" aria-label="타임라인 이벤트 목록">
          {component.events.length === 0 ? (
            <li style={FORM_HINT_STYLE}>이벤트가 없습니다. 추가 버튼으로 첫 이벤트를 만드세요.</li>
          ) : (
            component.events.map((event, index) => {
              const dateId = `timeline-date-${component.id}-${index}`;
              const titleId = `timeline-title-${component.id}-${index}`;
              const descId = `timeline-desc-${component.id}-${index}`;
              return (
                <li
                  key={`${component.id}-event-${index}`}
                  className="flex flex-col gap-1.5 rounded-md border p-2"
                  style={{ borderColor: "var(--doc-border)" }}
                  data-event-index={index}
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
                        onClick={handleMoveEvent(index, -1)}
                        disabled={component.locked || index === 0}
                        aria-label={`${index + 1}번째 이벤트 위로 이동`}
                      >
                        <ArrowUp aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleMoveEvent(index, 1)}
                        disabled={component.locked || index === component.events.length - 1}
                        aria-label={`${index + 1}번째 이벤트 아래로 이동`}
                      >
                        <ArrowDown aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleRemoveEvent(index)}
                        disabled={component.locked}
                        aria-label={`${index + 1}번째 이벤트 삭제`}
                      >
                        <Trash2 aria-hidden="true" />
                      </Button>
                    </div>
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={dateId} style={FORM_HINT_STYLE}>
                      날짜
                    </Label>
                    <Input
                      id={dateId}
                      aria-label={`${index + 1}번째 이벤트 날짜`}
                      value={event.date}
                      onChange={handleFieldChange(index, "date")}
                      placeholder="YYYY-MM-DD 또는 2026년 1분기"
                      disabled={component.locked}
                      maxLength={40}
                    />
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={titleId} style={FORM_HINT_STYLE}>
                      제목
                    </Label>
                    <Input
                      id={titleId}
                      aria-label={`${index + 1}번째 이벤트 제목`}
                      value={event.title}
                      onChange={handleFieldChange(index, "title")}
                      placeholder="이벤트 제목"
                      disabled={component.locked}
                      maxLength={120}
                    />
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={descId} style={FORM_HINT_STYLE}>
                      설명 (선택)
                    </Label>
                    <Textarea
                      id={descId}
                      aria-label={`${index + 1}번째 이벤트 설명`}
                      value={event.description ?? ""}
                      onChange={handleDescriptionChange(index)}
                      placeholder="세부 설명 — 비워두면 생략됩니다"
                      disabled={component.locked}
                      rows={2}
                      maxLength={400}
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

export default TimelineForm;
