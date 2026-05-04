/**
 * ColorTokenSlider — 개별 색상 토큰 1건을 편집하는 HTML5 color picker + hex input
 *
 * Phase 4 S1 D5. 프로젝트 의존성에 react-colorful 이 없으므로 HTML5 `<input
 * type="color">` 를 기본 picker 로 쓰고, 옆에 HEX Input 을 두어 키보드로도 정확한
 * hex 값을 입력할 수 있게 한다.
 *
 * 동작:
 *   - color 입력 onChange (드래그 중 연속 발생) → `onPreview(hex)` 로 흘려 picker
 *     훅의 50ms debounce 에 실린다.
 *   - color 입력 onBlur / hex Input onBlur → `onCommit(hex)` 로 흘려 500ms
 *     debounce 에 실린다 (실제 서버 저장은 마지막 호출 후 한 번).
 *   - hex Input 에서 잘못된 문자열이 blur 될 경우 값을 원복하고 aria-invalid 표시.
 *
 * 접근성:
 *   - label ↔ input 명시적 연결 (`htmlFor` + `id`).
 *   - aria-describedby 로 hex hint 연결.
 *   - disabled 상태(`locked`) 는 브랜드 프리셋 `idino_*` 사용 중일 때 활성.
 */

"use client";

import { useCallback, useState, type ChangeEvent, type FocusEvent } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { isValidHexColor, normalizeHexColor, type ColorTokenKey } from "./tokens";

export interface ColorTokenSliderProps {
  /** UI 라벨 (한국어). */
  label: string;
  /** DesignTokens 안에서의 키 (primary_color 등). */
  tokenKey: ColorTokenKey;
  /** 현재 hex 값 (예: "#0A4FC2"). 대문자 정규화 권장. */
  value: string;
  /** 드래그·타이핑 중 라이브 프리뷰 파이프 (50ms debounce 훅으로 연결). */
  onPreview: (hex: string) => void;
  /** 입력 확정 시 서버 저장 파이프 (500ms debounce 훅으로 연결). */
  onCommit: (hex: string) => void;
  /** 브랜드 프리셋 잠금 상태. true 면 input readOnly + aria-disabled. */
  locked?: boolean;
  /** 접근성 힌트 텍스트 (예: "브랜드 프리셋 사용 중 — 커스텀 모드에서 편집"). */
  lockedHint?: string;
}

export function ColorTokenSlider({
  label,
  tokenKey,
  value,
  onPreview,
  onCommit,
  locked = false,
  lockedHint,
}: ColorTokenSliderProps) {
  // 외부 value 가 변해도 local hex input 이 덮어써지지 않도록 동기화 상태 관리.
  // React 공식 권장 패턴 (https://react.dev/reference/react/useState#storing-information-from-previous-renders):
  // 이전 prop 값을 state 로 기록하고, render 중 차이를 감지하면 setState 한다.
  // useEffect 동기화는 react-hooks/set-state-in-effect 규칙에 걸리고, ref 접근은
  // react-hooks/refs 규칙에 걸리므로 "state 로 이전값 기억" 패턴이 유일한 정답.
  const [hexText, setHexText] = useState(value);
  const [isDirty, setIsDirty] = useState(false);
  const [lastSyncedValue, setLastSyncedValue] = useState(value);
  if (lastSyncedValue !== value) {
    setLastSyncedValue(value);
    if (!isDirty) setHexText(value);
  }

  const pickerId = `color-picker-${tokenKey}`;
  const hexInputId = `color-hex-${tokenKey}`;
  const hintId = `color-hint-${tokenKey}`;

  const handlePickerChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      const raw = event.target.value;
      const normalized = normalizeHexColor(raw);
      if (!normalized) return;
      setHexText(normalized);
      setIsDirty(false); // picker 는 dirty 상태를 만들지 않는다 (항상 유효).
      // 드래그 중 연속 호출되는 change 이벤트에서도 preview 와 commit 을 둘 다 쏜다.
      // 각 파이프는 서로 다른 debounce (50ms / 500ms) 로 합쳐지므로 사용자가
      // 손을 뗄 때 자동으로 마지막 값 1회만 서버에 반영된다. 별도 blur 대기는 불필요.
      onPreview(normalized);
      onCommit(normalized);
    },
    [onCommit, onPreview],
  );

  const handleHexChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    setIsDirty(true);
    setHexText(event.target.value);
  }, []);

  const handleHexBlur = useCallback(
    (event: FocusEvent<HTMLInputElement>) => {
      const raw = event.target.value;
      const normalized = normalizeHexColor(raw);
      if (normalized) {
        setHexText(normalized);
        setIsDirty(false);
        onPreview(normalized);
        onCommit(normalized);
      } else {
        // invalid hex → 마지막 유효값으로 롤백.
        setHexText(value);
        setIsDirty(false);
      }
    },
    [onCommit, onPreview, value],
  );

  const handleHexKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLInputElement>) => {
      if (event.key === "Enter") {
        event.currentTarget.blur();
      } else if (event.key === "Escape") {
        setHexText(value);
        setIsDirty(false);
        event.currentTarget.blur();
      }
    },
    [value],
  );

  const hexIsInvalid = isDirty && !isValidHexColor(hexText);

  return (
    <div className="space-y-1.5" data-color-token={tokenKey} aria-disabled={locked || undefined}>
      <Label htmlFor={pickerId}>{label}</Label>
      <div className="flex items-center gap-2">
        {/*
         * color picker — 브라우저 기본 색상 패널. 드래그 중에도 onChange 가
         * 발생하므로 onPreview 에 직접 연결.
         */}
        <input
          id={pickerId}
          type="color"
          value={isValidHexColor(hexText) ? hexText : value}
          onChange={handlePickerChange}
          disabled={locked}
          aria-describedby={locked ? hintId : undefined}
          aria-label={`${label} 색상 선택`}
          className="border-input bg-background h-10 w-14 shrink-0 cursor-pointer rounded-md border p-1 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <Input
          id={hexInputId}
          type="text"
          value={hexText}
          onChange={handleHexChange}
          onBlur={handleHexBlur}
          onKeyDown={handleHexKeyDown}
          disabled={locked}
          readOnly={locked}
          aria-invalid={hexIsInvalid || undefined}
          aria-describedby={locked ? hintId : undefined}
          aria-label={`${label} HEX 값`}
          placeholder="#0A4FC2"
          spellCheck={false}
          autoComplete="off"
          maxLength={7}
          className="font-mono uppercase"
        />
      </div>
      {locked && lockedHint ? (
        <p
          id={hintId}
          style={{ fontSize: "var(--doc-font-size-xs)", color: "var(--doc-text-muted)" }}
        >
          {lockedHint}
        </p>
      ) : null}
      {hexIsInvalid ? (
        <p role="alert" style={{ fontSize: "var(--doc-font-size-xs)", color: "var(--doc-danger)" }}>
          올바른 HEX 코드(#RRGGBB)를 입력하세요
        </p>
      ) : null}
    </div>
  );
}

export default ColorTokenSlider;
