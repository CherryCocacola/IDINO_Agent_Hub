/**
 * ImageGrid — 2~4장 이미지 그리드 컴포넌트
 *
 * DocumentSchema catalog #13 (S3 D3 추가). `images[]` 배열을 CSS Grid 로 렌더하되,
 * 이미지 장수에 따라 자동으로 열 수가 결정된다.
 *   - 2장 → 2열 × 1행
 *   - 3장 → 3열 × 1행
 *   - 4장 → 2열 × 2행 (정사각 타일)
 *
 * 각 아이템은 `<figure>` 구조로 감싸고, `src` 존재 여부에 따라
 *   - src 있음: `<img>` 를 `object-fit: cover` 로 렌더
 *   - src 없음(prompt 만 있음): placeholder `<div>` + alt 텍스트로 생성 대기 상태 표시
 * caption 이 있으면 `<figcaption>` 으로 하단에 표시한다.
 *
 * 디자인 규약:
 *   - 모든 색상은 `var(--doc-*)` 토큰 (hex 하드코딩 금지 — anti-patterns.md)
 *   - gap 은 `var(--doc-spacing-sm)` 고정
 *   - aspect-ratio: 4장 → 1/1, 2~3장 → 4/3 (시각적 균형 고려)
 *   - <a href> 하드코딩 없이 순수 이미지만 렌더
 */

import { ImageOff, Lock } from "lucide-react";

import type { ImageGridComponent } from "@/types/document-schema";

import { AutoSelectedBadge } from "./AutoSelectedBadge";

export interface ImageGridProps {
  component: ImageGridComponent;
  isSelected?: boolean;
  onSelect?: (componentId: string) => void;
}

/** images.length → grid-template-columns 매핑. */
function resolveColumns(count: number): number {
  if (count <= 2) return 2;
  if (count === 3) return 3;
  return 2; // 4장: 2×2
}

/** images.length → aspect-ratio 매핑. */
function resolveAspectRatio(count: number): string {
  return count === 4 ? "1 / 1" : "4 / 3";
}

export function ImageGrid({ component, isSelected, onSelect }: ImageGridProps) {
  const images = component.images;
  const columns = resolveColumns(images.length);
  const aspectRatio = resolveAspectRatio(images.length);

  const handleClick = () => onSelect?.(component.id);
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect?.(component.id);
    }
  };

  return (
    <div
      data-component="ImageGrid"
      data-component-id={component.id}
      data-image-count={images.length}
      data-locked={component.locked}
      data-selected={isSelected}
      role="group"
      tabIndex={0}
      aria-label={`이미지 그리드 — ${images.length}장`}
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
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${columns}, 1fr)`,
          gap: "var(--doc-spacing-sm)",
        }}
      >
        {images.map((item, idx) => (
          <figure
            key={`${component.id}-img-${idx}`}
            data-image-index={idx}
            data-has-src={item.src !== null && item.src !== ""}
            style={{
              margin: 0,
              display: "flex",
              flexDirection: "column",
              gap: "var(--doc-spacing-xs)",
            }}
          >
            {item.src ? (
              // 자동 선택 배지를 오버레이하기 위해 <img> 를 상대 컨테이너로 감싼다.
              // Lock 아이콘과 동일한 absolute positioning 컨벤션.
              <div style={{ position: "relative", width: "100%" }}>
                {/* next/image 대신 <img> 를 쓰는 이유:
                  1) MinIO/외부 URL 을 remotePatterns 에 매번 등록하는 비용 회피
                  2) 프리뷰 전용이라 최적화(LCP) 이득이 낮음
                  3) iframe 내부 렌더라 Next 이미지 로더 접근이 불가한 경우 존재 */}
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={item.src}
                  alt={item.alt}
                  style={{
                    width: "100%",
                    aspectRatio,
                    objectFit: "cover",
                    borderRadius: "var(--doc-radius-sm)",
                    display: "block",
                    background: "var(--doc-surface)",
                  }}
                />
                <AutoSelectedBadge src={item.src} prompt={item.prompt} />
              </div>
            ) : (
              <div
                role="img"
                aria-label={item.alt || "이미지 생성 대기 중"}
                style={{
                  width: "100%",
                  aspectRatio,
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
                <span style={{ wordBreak: "keep-all" }}>{item.alt || "이미지 생성 대기"}</span>
              </div>
            )}
            {item.caption && (
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
                {item.caption}
              </figcaption>
            )}
          </figure>
        ))}
      </div>
    </div>
  );
}

export default ImageGrid;
