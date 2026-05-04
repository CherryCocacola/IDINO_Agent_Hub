"use client";

import { ChevronDown, ChevronUp, Bot, User, FileText } from "lucide-react";
import { useState, useMemo } from "react";
import ReactMarkdown from "react-markdown";

import { cn } from "@/lib/utils/cn";

// ── Types ──────────────────────────────────────────────────────────────────

export interface Citation {
  id: string;
  documentName: string;
  chunkText: string;
  pageNumber?: number | null;
  score?: number | null;
}

interface ChatMessageProps {
  role: "user" | "assistant" | "system";
  content: string;
  citations?: Citation[];
  modelUsed?: string;
  hallucinationScore?: number;
  isStreaming?: boolean;
  timestamp?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

/** 환각 점수에 따른 표시 정보 (한국어) */
function getHallucinationIndicator(score: number) {
  if (score < 0.3) {
    return {
      label: "환각 위험 낮음",
      color: "text-green-600",
      bgColor: "bg-green-50 border-green-200",
      dotColor: "bg-green-500",
    };
  }
  if (score <= 0.6) {
    return {
      label: "환각 위험 보통",
      color: "text-yellow-600",
      bgColor: "bg-yellow-50 border-yellow-200",
      dotColor: "bg-yellow-500",
    };
  }
  return {
    label: "환각 위험 높음",
    color: "text-red-600",
    bgColor: "bg-red-50 border-red-200",
    dotColor: "bg-red-500",
  };
}

/** 유사도 점수에 따른 뱃지 스타일 */
function getScoreBadgeStyle(score: number): string {
  const pct = score * 100;
  if (pct >= 80) return "bg-green-50 text-green-700 border-green-200";
  if (pct >= 60) return "bg-blue-50 text-blue-700 border-blue-200";
  return "bg-gray-50 text-gray-600 border-gray-200";
}

// ── Typing indicator ───────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <span className="inline-flex items-center gap-1">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
    </span>
  );
}

// ── Citation Card ──────────────────────────────────────────────────────────

/**
 * 개별 출처 카드.
 *
 * UX 컴팩트화 (기본 접힘):
 *   - 닫힌 상태: 문서명 + 페이지 + 유사도만 한 줄 (~32px)
 *   - 펼친 상태: 본문 발췌 노출 (line-clamp 없음)
 *   - 카드 클릭 또는 우측 화살표로 토글
 *
 * 이전에는 line-clamp-5 로 카드마다 ~5줄을 차지해 답변보다 출처가 더 큰 화면을
 * 점유하는 문제가 있어 기본 접힘으로 변경했다.
 */
function CitationCard({ citation }: { citation: Citation }) {
  const [expanded, setExpanded] = useState(false);
  const hasText = Boolean(citation.chunkText);

  return (
    <button
      type="button"
      onClick={() => setExpanded((prev) => !prev)}
      aria-expanded={expanded}
      className="w-full cursor-pointer rounded-md border border-gray-200 bg-white px-2.5 py-1.5 text-left text-xs transition-colors hover:border-gray-300 hover:bg-gray-50"
    >
      {/* 상단: 문서명 + 페이지 + 유사도 + 펼치기 화살표 */}
      <div className="flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5 font-semibold text-gray-800">
          <FileText className="h-3.5 w-3.5 shrink-0 text-gray-400" />
          <span className="truncate">{citation.documentName}</span>
        </span>
        <div className="flex shrink-0 items-center gap-2">
          {citation.pageNumber !== null && citation.pageNumber !== undefined && (
            <span className="text-gray-500">p.{citation.pageNumber}</span>
          )}
          {citation.score !== null && citation.score !== undefined && (
            <span
              className={cn(
                "rounded border px-1.5 py-0.5 font-medium",
                getScoreBadgeStyle(citation.score),
              )}
            >
              {(citation.score * 100).toFixed(0)}%
            </span>
          )}
          {hasText &&
            (expanded ? (
              <ChevronUp className="h-3 w-3 text-gray-400" />
            ) : (
              <ChevronDown className="h-3 w-3 text-gray-400" />
            ))}
        </div>
      </div>

      {/* 하단: 인용 텍스트 — 펼친 경우에만 노출 */}
      {hasText && expanded && (
        <p className="mt-1.5 leading-relaxed whitespace-pre-wrap text-gray-600">
          {citation.chunkText}
        </p>
      )}
    </button>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

export function ChatMessage({
  role,
  content,
  citations,
  modelUsed,
  hallucinationScore,
  isStreaming,
  timestamp,
}: ChatMessageProps) {
  // 기본 접힘 — 답변 가독성을 우선시한다 (사용자가 필요 시 출처 N건 버튼 클릭).
  const [citationsExpanded, setCitationsExpanded] = useState(false);

  const hallucinationInfo = useMemo(() => {
    if (hallucinationScore === null || hallucinationScore === undefined) return null;
    return getHallucinationIndicator(hallucinationScore);
  }, [hallucinationScore]);

  // 유효한 citations만 필터 (빈 배열이면 표시하지 않음)
  const validCitations = citations && citations.length > 0 ? citations : null;

  // ── System message ───────────────────────────────────────────────────────
  if (role === "system") {
    return (
      <div className="flex justify-center py-2">
        <span className="rounded-full bg-gray-100 px-4 py-1.5 text-xs text-gray-500">
          {content}
        </span>
      </div>
    );
  }

  // ── User message ─────────────────────────────────────────────────────────
  if (role === "user") {
    return (
      <div className="flex justify-end py-2">
        <div className="flex max-w-[75%] items-end gap-2">
          <div className="rounded-2xl rounded-br-md bg-blue-600 px-4 py-2.5 text-sm text-white">
            <p className="whitespace-pre-wrap">{content}</p>
            {timestamp && <p className="mt-1 text-right text-[10px] text-blue-200">{timestamp}</p>}
          </div>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white">
            <User className="h-4 w-4" />
          </div>
        </div>
      </div>
    );
  }

  // ── Assistant message ────────────────────────────────────────────────────
  return (
    <div className="flex justify-start py-2">
      <div className="flex max-w-[80%] items-start gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-600">
          <Bot className="h-4 w-4" />
        </div>

        <div className="flex flex-col gap-2">
          {/* 메시지 본문 */}
          <div className="rounded-2xl rounded-tl-md bg-gray-100 px-4 py-2.5">
            {isStreaming && !content ? (
              <TypingIndicator />
            ) : (
              <div className="prose prose-sm max-w-none text-gray-800">
                <ReactMarkdown>{content}</ReactMarkdown>
              </div>
            )}

            {/* 스트리밍 커서 */}
            {isStreaming && content && (
              <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-gray-600" />
            )}

            {timestamp && <p className="mt-1 text-[10px] text-gray-400">{timestamp}</p>}
          </div>

          {/* 모델 및 환각 정보 */}
          {(modelUsed || hallucinationInfo) && (
            <div className="flex flex-wrap items-center gap-2 px-1">
              {modelUsed && (
                <span className="rounded bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-500">
                  {modelUsed}
                </span>
              )}
              {hallucinationInfo && (
                <span
                  className={cn(
                    "flex items-center gap-1.5 rounded border px-2 py-0.5 text-[10px] font-medium",
                    hallucinationInfo.bgColor,
                    hallucinationInfo.color,
                  )}
                >
                  <span
                    className={cn(
                      "inline-block h-1.5 w-1.5 rounded-full",
                      hallucinationInfo.dotColor,
                    )}
                  />
                  {hallucinationScore !== null &&
                    hallucinationScore !== undefined &&
                    `${(hallucinationScore * 100).toFixed(0)}% - `}
                  {hallucinationInfo.label}
                </span>
              )}
            </div>
          )}

          {/* 출처 (Citations) 섹션 */}
          {validCitations && (
            <div className="px-1">
              <button
                onClick={() => setCitationsExpanded(!citationsExpanded)}
                className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700"
              >
                <FileText className="h-3 w-3" />
                출처 {validCitations.length}건
                {citationsExpanded ? (
                  <ChevronUp className="h-3 w-3" />
                ) : (
                  <ChevronDown className="h-3 w-3" />
                )}
              </button>

              {citationsExpanded && (
                <div className="mt-2 space-y-2">
                  {validCitations.map((citation, idx) => (
                    <CitationCard key={citation.id || `citation-${idx}`} citation={citation} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
