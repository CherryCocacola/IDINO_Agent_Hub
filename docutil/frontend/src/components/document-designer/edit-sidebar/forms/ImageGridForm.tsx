/**
 * ImageGridForm — `ImageGrid` 컴포넌트 편집 폼
 *
 * Phase 4 S3 D3 산출물. 필수 동작:
 *   - `images[]` 추가 / 삭제 / 재정렬(▲▼)
 *   - 각 item 의 `src`(URL Input), `alt`(Input, 필수), `caption`(Input, optional), `prompt`(Input, optional)
 *
 * 제약:
 *   - 최대 4장 (schema 정의) — 초과 시 "추가" 버튼 비활성화
 *   - 최소 2장 권장이지만 편집 중간 상태에서는 1장/0장 허용 (서버가 최종 검증)
 *   - src 와 prompt 중 하나는 있어야 한다는 규칙은 서버에서 최종 검증
 *   - 빈 문자열은 schema `null` 로 정규화해 저장
 */

"use client";

import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";
import type { ChangeEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ImageGridComponent, ImageGridItem } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type ImageGridFormProps = FormProps<ImageGridComponent>;

/** schema 가 강제하는 이미지 장수 상한. */
export const IMAGE_GRID_MAX_IMAGES = 4;

/** 새 아이템 기본값. 최초 상태는 prompt-only(생성 대기). */
function createEmptyImage(): ImageGridItem {
  return { src: null, prompt: null, alt: "", caption: null };
}

/** 빈 문자열을 null 로 정규화. */
function normalizeNullable(value: string): string | null {
  return value.trim().length === 0 ? null : value;
}

export function ImageGridForm({ component, onLocalPatch, onCommitPatch }: ImageGridFormProps) {
  const applyImages = (nextImages: ImageGridItem[]) => {
    const patch: Partial<ImageGridComponent> = { images: nextImages };
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  const handleSrcChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = component.images.map((img, i) =>
      i === index ? { ...img, src: normalizeNullable(e.target.value) } : img,
    );
    applyImages(next);
  };

  const handleAltChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = component.images.map((img, i) =>
      i === index ? { ...img, alt: e.target.value } : img,
    );
    applyImages(next);
  };

  const handleCaptionChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = component.images.map((img, i) =>
      i === index ? { ...img, caption: normalizeNullable(e.target.value) } : img,
    );
    applyImages(next);
  };

  const handlePromptChange = (index: number) => (e: ChangeEvent<HTMLInputElement>) => {
    const next = component.images.map((img, i) =>
      i === index ? { ...img, prompt: normalizeNullable(e.target.value) } : img,
    );
    applyImages(next);
  };

  const handleAddImage = () => {
    if (component.images.length >= IMAGE_GRID_MAX_IMAGES) return;
    applyImages([...component.images, createEmptyImage()]);
  };

  const handleRemoveImage = (index: number) => () => {
    const next = component.images.filter((_, i) => i !== index);
    applyImages(next);
  };

  const handleMoveImage = (index: number, direction: -1 | 1) => () => {
    const target = index + direction;
    if (target < 0 || target >= component.images.length) return;
    const next = component.images.slice();
    const [moved] = next.splice(index, 1);
    next.splice(target, 0, moved);
    applyImages(next);
  };

  const atMax = component.images.length >= IMAGE_GRID_MAX_IMAGES;

  return (
    <section
      aria-label="이미지 그리드 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="ImageGrid"
      data-component-id={component.id}
      data-image-count={component.images.length}
    >
      <div className={FORM_FIELD_CLASS}>
        <div className="flex items-center justify-between">
          <Label>
            이미지 ({component.images.length}/{IMAGE_GRID_MAX_IMAGES})
          </Label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleAddImage}
            disabled={component.locked || atMax}
            aria-label="이미지 추가"
          >
            <Plus aria-hidden="true" />
            추가
          </Button>
        </div>

        <ol className="space-y-3" aria-label="이미지 목록">
          {component.images.length === 0 ? (
            <li style={FORM_HINT_STYLE}>
              이미지가 없습니다. 추가 버튼으로 첫 이미지를 만드세요 (2~4장 권장).
            </li>
          ) : (
            component.images.map((image, index) => {
              const srcId = `imggrid-src-${component.id}-${index}`;
              const altId = `imggrid-alt-${component.id}-${index}`;
              const captionId = `imggrid-caption-${component.id}-${index}`;
              const promptId = `imggrid-prompt-${component.id}-${index}`;
              return (
                <li
                  key={`${component.id}-image-${index}`}
                  className="flex flex-col gap-1.5 rounded-md border p-2"
                  style={{ borderColor: "var(--doc-border)" }}
                  data-image-index={index}
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
                        onClick={handleMoveImage(index, -1)}
                        disabled={component.locked || index === 0}
                        aria-label={`${index + 1}번째 이미지 위로 이동`}
                      >
                        <ArrowUp aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleMoveImage(index, 1)}
                        disabled={component.locked || index === component.images.length - 1}
                        aria-label={`${index + 1}번째 이미지 아래로 이동`}
                      >
                        <ArrowDown aria-hidden="true" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleRemoveImage(index)}
                        disabled={component.locked}
                        aria-label={`${index + 1}번째 이미지 삭제`}
                      >
                        <Trash2 aria-hidden="true" />
                      </Button>
                    </div>
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={srcId} style={FORM_HINT_STYLE}>
                      이미지 URL (선택)
                    </Label>
                    <Input
                      id={srcId}
                      aria-label={`${index + 1}번째 이미지 URL`}
                      value={image.src ?? ""}
                      onChange={handleSrcChange(index)}
                      placeholder="https://... 또는 비워두면 프롬프트로 자동생성"
                      disabled={component.locked}
                      maxLength={500}
                      inputMode="url"
                    />
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={altId} style={FORM_HINT_STYLE}>
                      대체 텍스트 (alt)
                    </Label>
                    <Input
                      id={altId}
                      aria-label={`${index + 1}번째 이미지 대체 텍스트`}
                      value={image.alt}
                      onChange={handleAltChange(index)}
                      placeholder="이미지 설명 (스크린리더용)"
                      disabled={component.locked}
                      maxLength={200}
                    />
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={captionId} style={FORM_HINT_STYLE}>
                      캡션 (선택)
                    </Label>
                    <Input
                      id={captionId}
                      aria-label={`${index + 1}번째 이미지 캡션`}
                      value={image.caption ?? ""}
                      onChange={handleCaptionChange(index)}
                      placeholder="이미지 아래 표시될 짧은 설명"
                      disabled={component.locked}
                      maxLength={200}
                    />
                  </div>

                  <div className={FORM_FIELD_CLASS}>
                    <Label htmlFor={promptId} style={FORM_HINT_STYLE}>
                      생성 프롬프트 (선택)
                    </Label>
                    <Input
                      id={promptId}
                      aria-label={`${index + 1}번째 이미지 생성 프롬프트`}
                      value={image.prompt ?? ""}
                      onChange={handlePromptChange(index)}
                      placeholder="Unsplash / DALL-E 검색 키워드"
                      disabled={component.locked}
                      maxLength={500}
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

export default ImageGridForm;
