/**
 * FontTokenSelect — font_family 프리셋 선택
 *
 * Phase 4 S1 D5. DesignTokens.font_family 는 3종 리터럴 union 이므로 임의
 * 문자열 입력을 허용하지 않고 Select 컴포넌트로만 전환한다.
 *
 * UX:
 *   - 각 옵션 라벨 옆에 실제 fontStack 적용 미리보기.
 *   - 선택 즉시 onPreview + onCommit 둘 다 호출 (드래그가 없는 discrete 입력).
 */

"use client";

import { useCallback } from "react";

import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { DesignTokens } from "@/types/document-schema";

import { FONT_FAMILY_OPTIONS } from "./tokens";

export interface FontTokenSelectProps {
  value: DesignTokens["font_family"];
  onPreview: (value: DesignTokens["font_family"]) => void;
  onCommit: (value: DesignTokens["font_family"]) => void;
  disabled?: boolean;
}

function parseFontFamily(raw: string): DesignTokens["font_family"] | null {
  if (raw === "Pretendard" || raw === "NotoSansKR" || raw === "System") return raw;
  return null;
}

export function FontTokenSelect({
  value,
  onPreview,
  onCommit,
  disabled = false,
}: FontTokenSelectProps) {
  const handleChange = useCallback(
    (raw: string) => {
      const parsed = parseFontFamily(raw);
      if (!parsed) return; // 방어: 알 수 없는 값 무시
      onPreview(parsed);
      onCommit(parsed);
    },
    [onCommit, onPreview],
  );

  const triggerId = "design-token-font-family";

  return (
    <div className="space-y-1.5" data-token-field="font_family">
      <Label htmlFor={triggerId}>폰트</Label>
      <Select value={value} onValueChange={handleChange} disabled={disabled}>
        <SelectTrigger id={triggerId} aria-label="폰트 선택">
          <SelectValue placeholder="폰트 선택" />
        </SelectTrigger>
        <SelectContent>
          {FONT_FAMILY_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              <span style={{ fontFamily: opt.fontStack }}>{opt.label}</span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export default FontTokenSelect;
