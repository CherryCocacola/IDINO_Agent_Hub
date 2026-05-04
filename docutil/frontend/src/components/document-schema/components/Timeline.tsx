/**
 * Timeline — 시간순 이벤트 타임라인 컴포넌트
 *
 * DocumentSchema catalog #11 (S3 D2 추가). `events[]` 배열을 세로 타임라인으로
 * 렌더한다. 각 이벤트는 좌측에 accent 컬러의 원형 마커 + 세로 연결선, 우측에
 * 날짜(muted) / 제목(bold) / 설명(muted small) 의 3단 정보로 구성된다.
 *
 * 디자인 규약:
 *   - 세로선: 마커 원 중심을 관통하는 `position: absolute` 선. 첫/마지막 이벤트는
 *     연결선이 위/아래로 자연스럽게 잘리도록 `::before` 대신 명시 span 사용.
 *   - 색상: 마커와 연결선 모두 `var(--doc-accent)` / 연결선은 반투명 접근은 지양.
 *   - 반응형: width 100%, 좌측 마커 영역은 고정 32px, 나머지 flex 1.
 *   - `<ol>` + `<li>` semantic 구조 (스크린리더가 이벤트 개수를 인식)
 */

import { Lock } from "lucide-react";

import type { TimelineComponent } from "@/types/document-schema";

export interface TimelineProps {
  component: TimelineComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

/** 좌측 마커 영역 고정 폭 (px). 마커 원과 연결선이 함께 차지. */
const MARKER_COLUMN_WIDTH = 32;
/** 마커 원 지름 (px). */
const MARKER_SIZE = 12;

export function Timeline({ component, isSelected, onSelect }: TimelineProps) {
  const events = component.events;
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="Timeline"
      data-component-id={component.id}
      data-event-count={events.length}
      data-locked={component.locked}
      data-selected={isSelected}
      role="group"
      tabIndex={0}
      aria-label={`타임라인 — 이벤트 ${events.length}개`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full outline-none"
      style={{
        padding: "var(--doc-spacing-sm)",
        marginTop: "var(--doc-spacing-md)",
        marginBottom: "var(--doc-spacing-md)",
        outline: isSelected ? "2px solid var(--doc-primary)" : undefined,
        outlineOffset: isSelected ? "2px" : undefined,
        borderRadius: "var(--doc-radius-md)",
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
      <ol
        style={{
          listStyle: "none",
          margin: 0,
          padding: 0,
          fontFamily: "var(--doc-font-family)",
        }}
      >
        {events.map((event, idx) => {
          const isFirst = idx === 0;
          const isLast = idx === events.length - 1;
          return (
            <li
              key={`${component.id}-event-${idx}`}
              data-event-index={idx}
              style={{
                position: "relative",
                display: "flex",
                alignItems: "flex-start",
                gap: "var(--doc-spacing-md)",
                paddingBottom: isLast ? 0 : "var(--doc-spacing-lg)",
                minHeight: MARKER_COLUMN_WIDTH,
              }}
            >
              {/* 좌측 마커 영역: 원 + (첫/마지막 제외한) 연결선 */}
              <div
                aria-hidden="true"
                style={{
                  position: "relative",
                  width: MARKER_COLUMN_WIDTH,
                  flexShrink: 0,
                  alignSelf: "stretch",
                }}
              >
                {/* 세로 연결선 — 첫 이벤트는 위쪽 절반, 마지막 이벤트는 아래쪽이 없음 */}
                {!isLast && (
                  <span
                    style={{
                      position: "absolute",
                      left: MARKER_COLUMN_WIDTH / 2 - 1,
                      top: MARKER_SIZE + 4,
                      bottom: 0,
                      width: 2,
                      background: "var(--doc-accent)",
                      opacity: 0.4,
                    }}
                  />
                )}
                {/* 마커 원 */}
                <span
                  style={{
                    position: "absolute",
                    top: 4,
                    left: MARKER_COLUMN_WIDTH / 2 - MARKER_SIZE / 2,
                    width: MARKER_SIZE,
                    height: MARKER_SIZE,
                    borderRadius: "50%",
                    background: "var(--doc-accent)",
                    border: isFirst ? "2px solid var(--doc-background)" : "none",
                    boxShadow: "0 0 0 2px var(--doc-accent-soft)",
                  }}
                />
              </div>

              {/* 우측 본문: 날짜 / 제목 / 설명 */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <time
                  style={{
                    display: "block",
                    color: "var(--doc-text-muted)",
                    fontSize: "var(--doc-font-size-xs)",
                    fontWeight: 500,
                    marginBottom: "var(--doc-spacing-xs)",
                  }}
                >
                  {event.date}
                </time>
                <h4
                  style={{
                    color: "var(--doc-text)",
                    fontSize: "var(--doc-font-size-base)",
                    fontWeight: 700,
                    lineHeight: "var(--doc-line-height-tight)",
                    margin: 0,
                    marginBottom: event.description ? "var(--doc-spacing-xs)" : 0,
                    wordBreak: "keep-all",
                  }}
                >
                  {event.title}
                </h4>
                {event.description && (
                  <p
                    style={{
                      color: "var(--doc-text-muted)",
                      fontSize: "var(--doc-font-size-sm)",
                      lineHeight: "var(--doc-line-height-normal)",
                      margin: 0,
                      wordBreak: "keep-all",
                    }}
                  >
                    {event.description}
                  </p>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export default Timeline;
