/**
 * ModeSwitcher — Mode A ↔ Mode B 전환 UI (Phase 4 S4 D6)
 *
 * 동작
 * ----
 *   - 현재 모드가 free_generation 일 때:
 *       템플릿 목록 (활성/조직 범위) 을 listTemplates 로 로드 → 드롭다운에 노출 →
 *       사용자가 템플릿 + conflict_policy radio 선택 → "전환" 버튼.
 *   - 현재 모드가 template_fill 일 때:
 *       단순 confirm UI + conflict_policy 선택 (preserve_user_edits 권장).
 *
 * API 호출 후
 *   응답의 새 DocumentSchema 를 useDocumentStore 에 주입한다.
 *   unmapped_anchors 가 있으면 onUnmapped 콜백에 전달 — 호출자가 toast 안내.
 *
 * 위치
 *   `(user)/designer/[documentId]` 우측 패널 또는 상단 도구 모음에 배치 권장.
 *   본 컴포넌트는 시각/위치를 고정하지 않고 단순 카드 UI 로만 노출한다.
 */

"use client";

import { Lock, Repeat } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { switchDocumentMode } from "@/lib/api/documents-v2";
import { listTemplates, type DocumentV2Template } from "@/lib/api/templates-v2";
import { useDocumentStore } from "@/lib/document-schema/document-store";
import type { DocumentSchema, UUID } from "@/types/document-schema";

type ConflictPolicy = "enforce_template" | "preserve_user_edits" | "manual";

const CONFLICT_POLICY_LABEL: Record<ConflictPolicy, string> = {
  enforce_template: "양식 강제 (locked 영역 덮어쓰기)",
  preserve_user_edits: "사용자 편집 우선",
  manual: "수동 (충돌 슬롯 사용자 선택)",
};

export interface ModeSwitcherProps {
  /** 현재 편집 중인 문서 ID. null 이면 비활성. */
  documentId: UUID | null;
  /** 현재 mode. document.mode 와 1:1. */
  currentMode: "free_generation" | "template_fill" | null;
  /**
   * 매핑되지 않은 슬롯 anchor 가 발생하면 호출됨. 호출자가 toast 등으로 안내.
   * unmapped 가 비어있으면 호출되지 않는다.
   */
  onUnmapped?: (unmappedAnchors: string[]) => void;
  /** 전환 성공 후 호출됨 (UI 닫기 등). */
  onSwitched?: (newMode: "free_generation" | "template_fill") => void;
}

export function ModeSwitcher({
  documentId,
  currentMode,
  onUnmapped,
  onSwitched,
}: ModeSwitcherProps) {
  const setDocument = useDocumentStore((s) => s.setDocument);
  const [templates, setTemplates] = useState<DocumentV2Template[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<UUID | "">("");
  const [policy, setPolicy] = useState<ConflictPolicy>("enforce_template");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // free → template 일 때만 템플릿 목록 로드.
  useEffect(() => {
    if (!documentId) return;
    if (currentMode !== "free_generation") return;
    let cancelled = false;
    (async () => {
      try {
        const result = await listTemplates({ is_active: true, limit: 100 });
        if (!cancelled) setTemplates(result.items);
      } catch (err) {
        // 템플릿 목록 조회 실패는 치명적이지 않음 — 빈 목록 유지.
        // 트랙 #106 — backend `/v2/templates` endpoint 가 Mode B 작업 진행 중이라
        // 404 응답이 정상. 404 는 silent, 그 외 에러만 warn 출력.
        const isNotFound =
          err instanceof Error &&
          ((err as { status?: number }).status === 404 ||
            err.message.toLowerCase().includes("not found"));
        if (!isNotFound) {
          // eslint-disable-next-line no-console
          console.warn("[ModeSwitcher] 템플릿 목록 로드 실패", err);
        }
        if (!cancelled) setTemplates([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [documentId, currentMode]);

  const targetMode: "free_generation" | "template_fill" =
    currentMode === "free_generation" ? "template_fill" : "free_generation";

  const handleSubmit = useCallback(async () => {
    if (!documentId || !currentMode) return;
    if (targetMode === "template_fill" && !selectedTemplateId) {
      setError("전환할 템플릿을 선택해주세요.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await switchDocumentMode({
        documentId,
        target_mode: targetMode,
        template_id: targetMode === "template_fill" ? (selectedTemplateId as UUID) : null,
        conflict_policy: policy,
      });
      // store 갱신 — 새 DocumentSchema 로 교체.
      const newSchema: DocumentSchema = result.document.document_schema;
      setDocument(newSchema);
      if (result.unmapped_anchors.length > 0) {
        onUnmapped?.(result.unmapped_anchors);
      }
      onSwitched?.(targetMode);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Mode 전환에 실패했습니다.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, [
    documentId,
    currentMode,
    targetMode,
    selectedTemplateId,
    policy,
    setDocument,
    onUnmapped,
    onSwitched,
  ]);

  if (!documentId || !currentMode) {
    return null;
  }

  return (
    <section
      data-testid="mode-switcher"
      aria-label="Mode 전환 도구"
      className="flex flex-col gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm"
    >
      <header className="flex items-center gap-2 text-amber-900">
        <Repeat className="h-4 w-4" />
        <strong>Mode 전환</strong>
        <span className="ml-auto text-xs text-amber-700">
          현재: {currentMode === "free_generation" ? "자유 생성" : "양식 채우기"}
        </span>
      </header>

      {targetMode === "template_fill" && (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="mode-switcher-template">전환할 템플릿</Label>
          <Select
            value={selectedTemplateId}
            onValueChange={(v) => setSelectedTemplateId(v as UUID | "")}
            disabled={isSubmitting || templates.length === 0}
          >
            <SelectTrigger id="mode-switcher-template" aria-label="템플릿 선택">
              <SelectValue
                placeholder={
                  templates.length === 0
                    ? "활성 템플릿 없음 — 관리자가 템플릿을 만들어야 합니다"
                    : "템플릿을 선택하세요"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {templates.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.name} ({t.document_type})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      <div className="flex flex-col gap-1.5">
        <Label htmlFor="mode-switcher-policy">충돌 정책</Label>
        <Select
          value={policy}
          onValueChange={(v) => setPolicy(v as ConflictPolicy)}
          disabled={isSubmitting}
        >
          <SelectTrigger id="mode-switcher-policy" aria-label="conflict_policy 선택">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(CONFLICT_POLICY_LABEL) as ConflictPolicy[]).map((p) => (
              <SelectItem key={p} value={p}>
                {CONFLICT_POLICY_LABEL[p]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {error && (
        <p role="alert" className="text-xs text-red-700">
          {error}
        </p>
      )}

      <Button
        onClick={handleSubmit}
        disabled={
          isSubmitting ||
          (targetMode === "template_fill" && !selectedTemplateId)
        }
        className="self-end"
      >
        {isSubmitting
          ? "전환 중..."
          : targetMode === "template_fill"
            ? "양식 채우기로 전환"
            : "자유 생성으로 전환"}
      </Button>

      {currentMode === "template_fill" && (
        <p className="flex items-center gap-1 text-xs text-amber-800">
          <Lock className="h-3 w-3" />
          현재 잠긴 영역은 양식의 고정값입니다. 전환 후 정책에 따라 처리됩니다.
        </p>
      )}
    </section>
  );
}

export default ModeSwitcher;
