/**
 * export-menu/index.tsx — Export 드롭다운 UI (Phase 4 S2 D2)
 *
 * 우측 패널 최상단에 배치되는 "내보내기" 드롭다운. 다섯 포맷 중 PPTX 만
 * 활성(S2 D5 백엔드 완성 시점), 나머지는 비활성 + 준비 중 안내.
 *
 * 동작:
 *   1. 메뉴 항목 클릭 → `requestExportJob({ documentId, format })` 호출 → jobId 획득
 *   2. `useExportStatus(jobId)` 훅이 2 초 간격 폴링
 *   3. 진행 중에는 버튼 옆 Loader2 스피너 + 진행률 텍스트
 *   4. 완료 시 `apiClient.getBlob(downloadUrl)` → 브라우저 자동 다운로드
 *   5. 실패 시 destructive toast
 *
 * 제약 (anti-patterns.md):
 *   - `fetch` 직접 호출 금지 — `apiClient.getBlob` 와 `documents-v2.ts` 만 사용.
 *   - 아이콘은 lucide-react 만 사용 (Download, Loader2).
 *   - shadcn DropdownMenu/Button 조합 재사용. 새 UI primitive 도입 금지.
 *
 * D5 미완성 상태에서 404/501 응답이 나오면 `useExportStatus` 가 실패 상태를
 * 반환하고 toast 가 "아직 준비 중" 메시지로 노출된다.
 */

"use client";

import { Download, Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import apiClient from "@/lib/api/client";
import { EXPORT_FORMATS, requestExportJob } from "@/lib/api/documents-v2";
import { useToast } from "@/lib/hooks/use-toast";
import type { ExportFormat as SchemaExportFormat, UUID } from "@/types/document-schema";

import type { ExportFormat } from "./types";
import { useExportStatus } from "./use-export-status";

// ─── Props ─────────────────────────────────────────────────────────────────

export interface ExportMenuProps {
  /** 편집 중 문서 ID. null 이면 메뉴 트리거가 비활성화된다. */
  documentId: UUID | null;
  className?: string;
  /** 테스트 식별자 커스터마이즈 (기본 "export-menu"). */
  dataTestId?: string;
}

// ─── 내부 유틸 ─────────────────────────────────────────────────────────────

/**
 * 백엔드가 반환한 download_url 은 상대 경로(`/v2/documents/...`) 또는 절대 URL
 * 형태 모두 가능하다. `apiClient.getBlob` 은 상대 경로만 허용하므로 origin 을
 * 제거해 상대 경로로 정규화한다.
 */
function toApiRelativePath(url: string): string {
  if (url.startsWith("/")) return url;
  try {
    const parsed = new URL(url);
    return parsed.pathname + parsed.search;
  } catch {
    return url;
  }
}

/**
 * 포맷별 권장 확장자. `downloadUrl` 이 쿼리스트링을 포함할 수 있으므로
 * 브라우저 저장 파일명 생성에 사용한다.
 */
function fileExtensionFor(format: ExportFormat): string {
  return format;
}

/** 다운로드 URL 에서 Blob 을 받아 브라우저에 저장 다이얼로그를 띄운다. */
async function triggerBlobDownload(url: string, filename: string): Promise<void> {
  const blob = await apiClient.getBlob(toApiRelativePath(url));
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  // 메모리 누수 방지 — 브라우저가 다운로드를 시작한 뒤 URL 을 해제.
  setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
}

// ─── 컴포넌트 ──────────────────────────────────────────────────────────────

export function ExportMenu({ documentId, className, dataTestId }: ExportMenuProps) {
  const { addToast } = useToast();

  // 진행 중 jobId (1 개만 동시). 새 export 요청이 들어오면 이전 job 은 사용자가
  // 취소한 것으로 간주하고 덮어쓴다.
  const [jobId, setJobId] = useState<string | null>(null);
  // 현재 요청 포맷 — 다운로드 파일명 계산용.
  const [activeFormat, setActiveFormat] = useState<ExportFormat | null>(null);
  // 드롭다운 버튼 disable 상태 (요청 직후 중복 클릭 방지).
  const [isSubmitting, setIsSubmitting] = useState(false);
  // 브라우저 다운로드가 1 회 트리거되었는지 — 상태가 completed 로 고정된 뒤
  // 재렌더가 발생해도 중복 다운로드 되지 않게 한다.
  const downloadedRef = useRef<string | null>(null);

  // 폴링 훅 — jobId 가 null 이면 no-op.
  const { status, progress, downloadUrl, error } = useExportStatus(jobId);

  // ── 완료 / 실패 부수효과 ────────────────────────────────────────────────
  useEffect(() => {
    if (!jobId) return;

    if (status === "completed" && downloadUrl) {
      // 같은 jobId 에 대해 한 번만 다운로드.
      if (downloadedRef.current === jobId) return;
      downloadedRef.current = jobId;

      const format = activeFormat ?? "pptx";
      const filename = `document-${jobId.slice(0, 8)}.${fileExtensionFor(format)}`;
      void triggerBlobDownload(downloadUrl, filename)
        .then(() => {
          addToast("내보내기가 완료되어 다운로드를 시작했습니다.", "success");
        })
        .catch((err: unknown) => {
          const message = err instanceof Error ? err.message : "다운로드에 실패했습니다.";
          addToast(`다운로드 실패: ${message}`, "error");
        })
        .finally(() => {
          setJobId(null);
          setActiveFormat(null);
        });
    } else if (status === "failed") {
      const message = error?.message ?? "내보내기 작업이 실패했습니다. 잠시 후 다시 시도해주세요.";
      addToast(message, "error");
      setJobId(null);
      setActiveFormat(null);
    }
  }, [status, downloadUrl, error, jobId, activeFormat, addToast]);

  // ── 항목 선택 핸들러 ───────────────────────────────────────────────────
  const handleSelect = useCallback(
    async (format: SchemaExportFormat) => {
      if (!documentId) {
        addToast("문서를 먼저 불러온 뒤 내보내기를 실행하세요.", "error");
        return;
      }
      if (isSubmitting || jobId) {
        // 이미 진행 중인 작업이 있으면 무시 (UI 상으로도 버튼이 disabled).
        return;
      }

      setIsSubmitting(true);
      setActiveFormat(format as ExportFormat);
      downloadedRef.current = null;

      try {
        const { jobId: newJobId } = await requestExportJob({
          documentId,
          format: format as ExportFormat,
        });
        setJobId(newJobId);
      } catch (err) {
        const message = err instanceof Error ? err.message : "내보내기 요청을 보낼 수 없습니다.";
        // D5 이전에는 대부분 404/501 — 사용자에게는 "준비 중" 맥락으로 안내.
        addToast(`내보내기 준비 중입니다: ${message}`, "error");
        setActiveFormat(null);
      } finally {
        setIsSubmitting(false);
      }
    },
    [documentId, isSubmitting, jobId, addToast],
  );

  // ── 렌더 ────────────────────────────────────────────────────────────────
  const isBusy = Boolean(jobId) || isSubmitting;
  const progressText =
    isBusy && status !== "failed"
      ? `생성 중... (${Math.min(Math.max(progress, 0), 100)}%)`
      : "내보내기";

  return (
    <div
      data-testid={dataTestId ?? "export-menu"}
      className={className}
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "flex-end",
        padding: "var(--doc-spacing-sm)",
      }}
    >
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            disabled={!documentId || isBusy}
            data-testid="export-menu-trigger"
            aria-label="내보내기 메뉴 열기"
            // 문서가 아직 없으면 "왜 회색인지" hover 툴팁으로 안내한다.
            // 사용자가 /designer/create 진입 직후 우측 메뉴가 비활성으로 보이는
            // 원인을 오해하지 않도록 명시적 힌트를 제공한다.
            title={
              !documentId
                ? "문서를 먼저 생성한 뒤 내보내기를 사용할 수 있습니다 (프롬프트 제출 후 활성화)."
                : isBusy
                  ? "내보내기 작업이 진행 중입니다."
                  : "포맷을 선택해 파일로 내보냅니다."
            }
          >
            {isBusy ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="h-4 w-4" aria-hidden="true" />
            )}
            <span>{progressText}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" data-testid="export-menu-content">
          <DropdownMenuLabel>포맷 선택</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {EXPORT_FORMATS.map((entry) => (
            <DropdownMenuItem
              key={entry.format}
              data-testid={`export-menu-item-${entry.format}`}
              disabled={entry.disabled || !documentId}
              onSelect={(event) => {
                // Radix 의 `onSelect` 는 기본 동작으로 드롭다운을 닫는다. 비동기
                // 요청 중에 닫혀도 UI 상 문제가 없으므로 기본 동작을 유지.
                event.preventDefault();
                void handleSelect(entry.format);
              }}
              title={entry.hint}
            >
              <span>{entry.label}</span>
              {entry.disabled ? (
                <span
                  style={{
                    marginLeft: "auto",
                    fontSize: "var(--doc-font-size-xs)",
                    color: "var(--doc-text-muted)",
                  }}
                >
                  준비 중
                </span>
              ) : null}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}

// 타입 재수출 — 테스트 및 상위 import 편의.
export type { ExportFormat, ExportJobStatus, ExportStatusView } from "./types";
export { useExportStatus } from "./use-export-status";
