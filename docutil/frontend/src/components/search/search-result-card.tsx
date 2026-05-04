"use client";

import {
  FileText,
  FileSpreadsheet,
  FileImage,
  File,
  ChevronDown,
  ChevronUp,
  BookOpen,
  Hash,
  Download,
} from "lucide-react";
import { useState, useMemo } from "react";

import { apiClient } from "@/lib/api/client";
import { cn } from "@/lib/utils/cn";

// ── Types ──────────────────────────────────────────────────────────────────

export interface SearchResult {
  id: string;
  documentName: string;
  documentFormat?: string;
  chunkText: string;
  score: number;
  pageNumber?: number;
  sectionTitle?: string;
  documentId?: string;
}

interface SearchResultCardProps {
  result: SearchResult;
  queryTerms: string[];
  onClick?: (result: SearchResult) => void;
  className?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const FORMAT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  pdf: FileText,
  docx: FileText,
  doc: FileText,
  xlsx: FileSpreadsheet,
  xls: FileSpreadsheet,
  csv: FileSpreadsheet,
  png: FileImage,
  jpg: FileImage,
  jpeg: FileImage,
  hwp: FileText,
};

function getFormatIcon(format?: string) {
  if (!format) return File;
  return FORMAT_ICONS[format.toLowerCase()] || File;
}

function getFormatColor(format?: string): string {
  const f = format?.toLowerCase();
  if (f === "pdf") return "text-red-500";
  if (f === "docx" || f === "doc") return "text-blue-500";
  if (f === "xlsx" || f === "xls" || f === "csv") return "text-green-500";
  if (f === "hwp") return "text-sky-500";
  if (f === "png" || f === "jpg" || f === "jpeg") return "text-blue-500";
  return "text-gray-400";
}

function getScoreBadge(score: number) {
  if (score >= 0.8)
    return { label: "Excellent", color: "bg-green-100 text-green-700 border-green-200" };
  if (score >= 0.6) return { label: "Good", color: "bg-blue-100 text-blue-700 border-blue-200" };
  if (score >= 0.4)
    return { label: "Fair", color: "bg-yellow-100 text-yellow-700 border-yellow-200" };
  return { label: "Low", color: "bg-gray-100 text-gray-600 border-gray-200" };
}

/** Highlight query terms within text. Returns JSX spans. */
function highlightText(text: string, queryTerms: string[]): React.ReactNode[] {
  if (!queryTerms.length) return [text];

  const escaped = queryTerms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`(${escaped.join("|")})`, "gi");
  const parts = text.split(regex);

  return parts.map((part, i) => {
    const isMatch = queryTerms.some((term) => part.toLowerCase() === term.toLowerCase());
    return isMatch ? (
      <mark key={i} className="rounded bg-yellow-200 px-0.5 font-bold text-yellow-900">
        {part}
      </mark>
    ) : (
      <span key={i}>{part}</span>
    );
  });
}

// ── Component ──────────────────────────────────────────────────────────────

export function SearchResultCard({
  result,
  queryTerms,
  onClick,
  className,
}: SearchResultCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [downloading, setDownloading] = useState(false);

  // 원본 문서 다운로드 핸들러
  const handleDownload = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!result.documentId || downloading) return;
    setDownloading(true);
    try {
      const blob = await apiClient.getBlob(`/documents/${result.documentId}/download`);
      // Blob을 파일로 저장하기 위해 임시 a 태그 생성
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = result.documentName || "download";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      // 다운로드 실패 시 무시 (토스트는 상위 컴포넌트에서 처리)
    } finally {
      setDownloading(false);
    }
  };

  const FormatIcon = getFormatIcon(result.documentFormat);
  const formatColor = getFormatColor(result.documentFormat);
  const scoreBadge = useMemo(() => getScoreBadge(result.score), [result.score]);

  const previewText =
    result.chunkText.length > 200 ? result.chunkText.slice(0, 200) + "..." : result.chunkText;

  const highlightedPreview = useMemo(
    () => highlightText(previewText, queryTerms),
    [previewText, queryTerms],
  );

  const highlightedFull = useMemo(
    () => highlightText(result.chunkText, queryTerms),
    [result.chunkText, queryTerms],
  );

  return (
    <div
      className={cn(
        "group rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md",
        onClick && "cursor-pointer",
        className,
      )}
      onClick={() => onClick?.(result)}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <FormatIcon className={cn("h-5 w-5 shrink-0", formatColor)} />
          <h3 className="truncate text-sm font-semibold text-gray-900">{result.documentName}</h3>
          {result.documentFormat && (
            <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 uppercase">
              {result.documentFormat}
            </span>
          )}
        </div>

        {/* 다운로드 버튼 + 점수 배지 */}
        <div className="flex shrink-0 items-center gap-2">
          {result.documentId && (
            <button
              onClick={handleDownload}
              disabled={downloading}
              title="원본 문서 다운로드"
              className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50"
            >
              <Download className={cn("h-4 w-4", downloading && "animate-pulse")} />
            </button>
          )}
          <span
            className={cn(
              "rounded-full border px-2.5 py-0.5 text-xs font-medium",
              scoreBadge.color,
            )}
          >
            {(result.score * 100).toFixed(0)}% {scoreBadge.label}
          </span>
        </div>
      </div>

      {/* Meta info: page number, section */}
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
        {result.pageNumber !== null && result.pageNumber !== undefined && (
          <span className="flex items-center gap-1">
            <BookOpen className="h-3 w-3" />
            Page {result.pageNumber}
          </span>
        )}
        {result.sectionTitle && (
          <span className="flex items-center gap-1">
            <Hash className="h-3 w-3" />
            {result.sectionTitle}
          </span>
        )}
      </div>

      {/* Matched text */}
      <div className="mt-3">
        <p className="text-sm leading-relaxed text-gray-700">
          {expanded ? highlightedFull : highlightedPreview}
        </p>
      </div>

      {/* Expand / Collapse (only if text was truncated) */}
      {result.chunkText.length > 200 && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="mt-2 flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
        >
          {expanded ? (
            <>
              Show less <ChevronUp className="h-3 w-3" />
            </>
          ) : (
            <>
              Show full chunk <ChevronDown className="h-3 w-3" />
            </>
          )}
        </button>
      )}
    </div>
  );
}
