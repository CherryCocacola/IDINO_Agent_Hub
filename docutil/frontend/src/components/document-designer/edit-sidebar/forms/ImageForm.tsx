/**
 * ImageForm — `Image` 단일 이미지 컴포넌트 편집 폼
 *
 * Phase 4 S3 D5 산출물 (phase3_execution_roadmap.md §2.3 S3 D5).
 *
 * 설계 요점 — 3 가지 선택 모드 (mutually exclusive radio):
 *   1. **URL 직접 입력**: `src` 에 URL 만 넣는다. prompt 는 null 로 정규화.
 *   2. **프롬프트로 자동 생성**: `prompt` 만 넣고 `src=null`. 서버가 Unsplash/
 *      DALL-E 를 호출해 채운다. alt 필수.
 *   3. **자동 선택 (권장)**: Mode 2 와 동일 (Unsplash 우선 → DALL-E fallback).
 *      UI 상 구분만 주어 추천 여부를 강조. 실제 서버 로직은 동일 경로.
 *
 * 제약:
 *   - Pydantic 스키마상 `src` 또는 `prompt` 중 하나는 반드시 있어야 한다.
 *     이를 UI 차원에서 모드 전환으로 강제한다.
 *   - 빈 문자열은 null 로 정규화 (schema 정합성 유지).
 *   - DALL-E 자동 생성 모드 선택 시 현재 쿼터 잔여량을 표시한다.
 *     (`useOrganizationQuotas` 훅이 조직별 쿼터를 로드.)
 *
 * 쿼터 표시 UX:
 *   - 로딩 중 → "이번 달 DALL-E 사용량 확인 중..." 힌트.
 *   - 잔여 > 0 → "이번 달 DALL-E 사용: {used}/{limit}" 표시 (green/amber).
 *   - 잔여 0 → "쿼터 소진 — 관리자에게 문의하세요." 빨간 힌트 + auto 모드 경고.
 *   - 훅 에러 → 표시 영역을 조용히 숨김 (UI 자체를 막지 않음).
 */

"use client";

import type { ChangeEvent } from "react";
import { useMemo } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useOrganizationQuotas } from "@/lib/hooks/use-organization-quotas";
import type { ImageComponent } from "@/types/document-schema";

import {
  FORM_DISABLED_STYLE,
  FORM_FIELD_CLASS,
  FORM_HINT_STYLE,
  FORM_SECTION_CLASS,
  type FormProps,
} from "./shared";

export type ImageFormProps = FormProps<ImageComponent> & {
  /** 현재 사용자 조직 ID. 쿼터 표시용. 없으면 쿼터 UI 숨김. */
  organizationId?: string;
};

/** 편집 모드 식별자. mutually exclusive. */
type ImageMode = "url" | "prompt" | "auto";

/** 빈 문자열을 null 로 정규화. */
function normalizeNullable(value: string): string | null {
  return value.trim().length === 0 ? null : value;
}

/** 컴포넌트의 현재 상태로부터 초기 모드를 추정한다. */
function detectMode(component: ImageComponent): ImageMode {
  if (component.src) return "url";
  if (component.prompt) return "auto"; // prompt-only 는 기본 auto (권장).
  return "auto";
}

export function ImageForm({
  component,
  onLocalPatch,
  onCommitPatch,
  organizationId,
}: ImageFormProps) {
  // URL/prompt 가 둘 다 있을 수는 있으나, UI 상 모드 변경시 비가시 필드는 비워둔다.
  const currentMode: ImageMode = useMemo(() => detectMode(component), [component]);

  const { quotas, isLoading: quotasLoading } = useOrganizationQuotas(organizationId);
  const dalleQuota = quotas?.dalle_monthly;
  const quotaExhausted = dalleQuota !== undefined && dalleQuota.remaining <= 0;

  // ── Patch 헬퍼 ──────────────────────────────────────────────────────────
  const applyPatch = (patch: Partial<ImageComponent>) => {
    onLocalPatch(patch);
    onCommitPatch(patch);
  };

  // ── 모드 전환 — mutually exclusive 필드 초기화 ────────────────────────
  const handleModeChange = (mode: ImageMode) => {
    if (mode === "url") {
      // URL 모드 — prompt 비움.
      applyPatch({ prompt: null });
    } else if (mode === "prompt" || mode === "auto") {
      // 생성 모드 — src 비움, prompt 는 유지 (비어 있으면 사용자가 곧 채울 것).
      applyPatch({ src: null });
    }
  };

  // ── 필드 onChange ─────────────────────────────────────────────────────
  const handleSrcChange = (e: ChangeEvent<HTMLInputElement>) => {
    applyPatch({ src: normalizeNullable(e.target.value) });
  };
  const handlePromptChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    applyPatch({ prompt: normalizeNullable(e.target.value) });
  };
  const handleAltChange = (e: ChangeEvent<HTMLInputElement>) => {
    applyPatch({ alt: e.target.value });
  };
  const handleCaptionChange = (e: ChangeEvent<HTMLInputElement>) => {
    applyPatch({ caption: normalizeNullable(e.target.value) });
  };

  // ── ID 접두어 ─────────────────────────────────────────────────────────
  const modeName = `image-mode-${component.id}`;
  const srcId = `image-src-${component.id}`;
  const promptId = `image-prompt-${component.id}`;
  const altId = `image-alt-${component.id}`;
  const captionId = `image-caption-${component.id}`;

  return (
    <section
      aria-label="이미지 편집"
      className={FORM_SECTION_CLASS}
      style={component.locked ? FORM_DISABLED_STYLE : undefined}
      data-form="Image"
      data-component-id={component.id}
      data-mode={currentMode}
    >
      {/* ── 모드 선택 ────────────────────────────────────────────────── */}
      <fieldset
        className={FORM_FIELD_CLASS}
        aria-label="이미지 소스 모드"
        disabled={component.locked}
      >
        <legend style={FORM_HINT_STYLE}>소스 모드</legend>
        <div className="flex flex-col gap-1.5">
          <label className="flex items-center gap-2 text-sm" htmlFor={`${modeName}-url`}>
            <input
              id={`${modeName}-url`}
              type="radio"
              name={modeName}
              value="url"
              checked={currentMode === "url"}
              onChange={() => handleModeChange("url")}
              disabled={component.locked}
              aria-label="URL 직접 입력"
            />
            <span>URL 직접 입력</span>
          </label>
          <label className="flex items-center gap-2 text-sm" htmlFor={`${modeName}-prompt`}>
            <input
              id={`${modeName}-prompt`}
              type="radio"
              name={modeName}
              value="prompt"
              checked={currentMode === "prompt"}
              onChange={() => handleModeChange("prompt")}
              disabled={component.locked}
              aria-label="프롬프트로 자동 생성"
            />
            <span>프롬프트로 자동 생성 (DALL-E)</span>
          </label>
          <label className="flex items-center gap-2 text-sm" htmlFor={`${modeName}-auto`}>
            <input
              id={`${modeName}-auto`}
              type="radio"
              name={modeName}
              value="auto"
              checked={currentMode === "auto"}
              onChange={() => handleModeChange("auto")}
              disabled={component.locked}
              aria-label="자동 선택 (Unsplash 우선, DALL-E fallback, 권장)"
            />
            <span>자동 선택 (Unsplash → DALL-E, 권장)</span>
          </label>
        </div>
      </fieldset>

      {/* ── 모드별 입력 필드 ────────────────────────────────────────── */}
      {currentMode === "url" && (
        <div className={FORM_FIELD_CLASS}>
          <Label htmlFor={srcId}>이미지 URL</Label>
          <Input
            id={srcId}
            value={component.src ?? ""}
            onChange={handleSrcChange}
            placeholder="https://..."
            disabled={component.locked}
            maxLength={500}
            inputMode="url"
            aria-label="이미지 URL"
          />
        </div>
      )}

      {(currentMode === "prompt" || currentMode === "auto") && (
        <div className={FORM_FIELD_CLASS}>
          <Label htmlFor={promptId}>
            생성 프롬프트
            {currentMode === "auto" ? (
              <span style={FORM_HINT_STYLE}> (Unsplash 에서 먼저 검색)</span>
            ) : null}
          </Label>
          <Textarea
            id={promptId}
            value={component.prompt ?? ""}
            onChange={handlePromptChange}
            placeholder={
              currentMode === "auto"
                ? "예: modern office team collaboration, bright lighting"
                : "예: futuristic city skyline at sunset"
            }
            disabled={component.locked}
            rows={3}
            maxLength={500}
            aria-label="이미지 생성 프롬프트"
          />

          {/* 쿼터 표시 (DALL-E fallback 가능성이 있는 모드에서만). */}
          {organizationId !== undefined && (
            <div aria-live="polite" data-testid="dalle-quota-hint">
              {quotasLoading ? (
                <span style={FORM_HINT_STYLE}>이번 달 DALL-E 사용량 확인 중...</span>
              ) : dalleQuota !== undefined ? (
                <span
                  style={{
                    ...FORM_HINT_STYLE,
                    color: quotaExhausted
                      ? "var(--doc-destructive, #dc2626)"
                      : "var(--doc-text-muted)",
                    fontWeight: quotaExhausted ? 600 : 400,
                  }}
                  data-quota-exhausted={quotaExhausted ? "true" : "false"}
                >
                  이번 달 DALL-E 사용: {dalleQuota.used_count}/{dalleQuota.monthly_limit}
                  {quotaExhausted
                    ? " · 쿼터 소진 — 관리자에게 문의하세요."
                    : ` (잔여 ${dalleQuota.remaining})`}
                </span>
              ) : null}
            </div>
          )}
        </div>
      )}

      {/* ── alt (공통, 필수) ─────────────────────────────────────────── */}
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={altId}>대체 텍스트 (alt, 필수)</Label>
        <Input
          id={altId}
          value={component.alt}
          onChange={handleAltChange}
          placeholder="이미지 설명 (스크린리더용)"
          disabled={component.locked}
          maxLength={200}
          aria-label="이미지 대체 텍스트"
          required
        />
      </div>

      {/* ── caption (공통, 선택) ─────────────────────────────────────── */}
      <div className={FORM_FIELD_CLASS}>
        <Label htmlFor={captionId}>캡션 (선택)</Label>
        <Input
          id={captionId}
          value={component.caption ?? ""}
          onChange={handleCaptionChange}
          placeholder="이미지 아래 표시될 짧은 설명"
          disabled={component.locked}
          maxLength={200}
          aria-label="이미지 캡션"
        />
      </div>
    </section>
  );
}

export default ImageForm;
