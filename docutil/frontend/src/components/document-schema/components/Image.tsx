/**
 * Image — 단일 이미지 컴포넌트 (DocumentSchema catalog #12)
 *
 * Phase 4 S3 D7 산출물. `ImageComponent` (`type: "Image"`) 를 위한 프리뷰 렌더러.
 * `ImageGrid` 가 `ImageGridItem[]` 을 그리드로 배치하는 반면, 본 컴포넌트는
 * 단일 이미지를 풀블리드에 가까운 비율로 표시한다.
 *
 * 자동 선택 시각화 (S3 D7-a):
 *   - `src` 도메인을 분석해 `AutoSelectedBadge` 오버레이.
 *   - `prompt` 가 있으면 hover 툴팁 + `aria-label` 로 노출 (D7-b).
 *
 * 디자인 토큰 준수 — 색상/간격 모두 `var(--doc-*)` 참조.
 */

import { ImageOff, Lock } from "lucide-react";

import type { ImageComponent } from "@/types/document-schema";

import { AutoSelectedBadge } from "./AutoSelectedBadge";

export interface ImageProps {
  component: ImageComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

/** 단일 이미지의 기본 비율 — 16:9 로 세로 공간을 합리적으로 확보. */
const SINGLE_IMAGE_ASPECT_RATIO = "16 / 9";

export function Image({ component, isSelected, onSelect }: ImageProps) {
  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  const hasSrc = component.src !== null && component.src !== "";

  return (
    <div
      data-component="Image"
      data-component-id={component.id}
      data-has-src={hasSrc}
      data-locked={component.locked}
      data-selected={isSelected}
      role="group"
      tabIndex={0}
      aria-label={component.alt || "이미지"}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className="relative w-full outline-none"
      style={{
        padding: "var(--doc-spacing-sm)",
        marginTop: "var(--doc-spacing-md)",
        marginBottom: "var(--doc-spacing-md)",
        borderRadius: "var(--doc-radius-md)",
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

      <figure
        style={{
          margin: 0,
          display: "flex",
          flexDirection: "column",
          gap: "var(--doc-spacing-xs)",
        }}
      >
        {hasSrc ? (
          <div style={{ position: "relative", width: "100%" }}>
            {/* next/image 대신 <img> — ImageGrid 와 동일한 이유. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={component.src as string}
              alt={component.alt}
              style={{
                width: "100%",
                aspectRatio: SINGLE_IMAGE_ASPECT_RATIO,
                objectFit: "cover",
                borderRadius: "var(--doc-radius-sm)",
                display: "block",
                background: "var(--doc-surface)",
              }}
            />
            <AutoSelectedBadge src={component.src} prompt={component.prompt} />
          </div>
        ) : (
          <div
            role="img"
            aria-label={component.alt || "이미지 생성 대기 중"}
            style={{
              width: "100%",
              aspectRatio: SINGLE_IMAGE_ASPECT_RATIO,
              borderRadius: "var(--doc-radius-sm)",
              background: "var(--doc-surface)",
              border: "1px dashed var(--doc-border)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "var(--doc-spacing-xs)",
              color: "var(--doc-text-muted)",
              fontFamily: "var(--doc-font-family)",
              fontSize: "var(--doc-font-size-xs)",
              padding: "var(--doc-spacing-sm)",
              textAlign: "center",
            }}
          >
            <ImageOff aria-hidden="true" className="h-5 w-5" />
            <span style={{ wordBreak: "keep-all" }}>{component.alt || "이미지 생성 대기"}</span>
          </div>
        )}
        {component.caption && (
          <figcaption
            style={{
              fontSize: "var(--doc-font-size-xs)",
              color: "var(--doc-text-muted)",
              fontFamily: "var(--doc-font-family)",
              lineHeight: "var(--doc-line-height-normal)",
              wordBreak: "keep-all",
              textAlign: "center",
            }}
          >
            {component.caption}
          </figcaption>
        )}
      </figure>
    </div>
  );
}

export default Image;
