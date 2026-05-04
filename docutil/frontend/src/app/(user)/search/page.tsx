"use client";

import {
  Search,
  X,
  Clock,
  FileText,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Loader2,
  SlidersHorizontal,
  Tag,
  Calendar,
  Bot,
  ExternalLink,
  FileOutput,
  Sparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useCallback, useEffect, useMemo, FormEvent } from "react";

import { SearchResultCard, type SearchResult } from "@/components/search/search-result-card";
import { DatePicker } from "@/components/ui/date-picker";
import apiClient from "@/lib/api/client";
import { generateDocument } from "@/lib/api/documents-v2";
import { useToast } from "@/lib/hooks/use-toast";
import { cn } from "@/lib/utils/cn";
import type { DocumentType as V2DocumentType } from "@/types/document-schema";

// ── Types ──────────────────────────────────────────────────────────────────

type SearchType = "all" | "qa" | "keyword";

interface SearchFilters {
  dateFrom: string;
  dateTo: string;
  formats: string[];
  tags: string[];
}

interface QAAnswer {
  answer: string;
  citations: Array<{
    id: string;
    documentName: string;
    chunkText: string;
    pageNumber?: number;
    score?: number;
  }>;
  hallucinationScore: number;
  modelUsed: string;
}

interface SearchState {
  results: SearchResult[];
  qaAnswer: QAAnswer | null;
  totalCount: number;
  page: number;
  pageSize: number;
  loading: boolean;
}

// ── Constants ──────────────────────────────────────────────────────────────

const SEARCH_TYPES: { value: SearchType; label: string; description: string }[] = [
  { value: "all", label: "전체", description: "모든 콘텐츠에서 검색" },
  { value: "qa", label: "Q&A", description: "AI 생성 답변 받기" },
  { value: "keyword", label: "키워드", description: "키워드 정확 매칭" },
];

const FORMAT_OPTIONS = ["pdf", "docx", "xlsx", "hwp", "csv", "pptx"];

const TAG_OPTIONS = ["engineering", "research", "report", "specification", "design", "meeting"];

const MAX_HISTORY = 10;
const PAGE_SIZE_OPTIONS = [10, 20, 50];

/** DB 템플릿 정보를 담는 인터페이스 */
interface ReportTemplateItem {
  id: string;
  name: string;
  description: string | null;
  template_type: string;
  output_format: string;
  rendering_mode: string;
}

/** Jinja2 변수 메타데이터 (GET /templates/{id}/variables 응답) */
interface Jinja2Variable {
  name: string;
  var_type: "string" | "array" | "boolean" | "image" | "date";
  label: string | null;
  description: string | null;
  required: boolean;
  /** 변수 카테고리: user_input(직접 입력), session_auto(세션 자동), ai_generated(AI 생성) */
  category?: "user_input" | "session_auto" | "ai_generated";
}

// ── Component ──────────────────────────────────────────────────────────────

export default function SearchPage() {
  const { addToast } = useToast();
  // 문서 생성 완료 후 디자이너로 이동시키기 위한 라우터 핸들
  const router = useRouter();

  // Search state
  const [query, setQuery] = useState("");
  const [searchType, setSearchType] = useState<SearchType>("all");
  const [filters, setFilters] = useState<SearchFilters>({
    dateFrom: "",
    dateTo: "",
    formats: [],
    tags: [],
  });
  const [showFilterSidebar, setShowFilterSidebar] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  // Results state
  const [state, setState] = useState<SearchState>({
    results: [],
    qaAnswer: null,
    totalCount: 0,
    page: 1,
    pageSize: 10,
    loading: false,
  });

  // Report generation
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportTitle, setReportTitle] = useState("");
  const [reportType, setReportType] = useState<"report" | "minutes">("report");
  const [selectedResultIds, setSelectedResultIds] = useState<Set<string>>(new Set());
  const [reportGenerating, setReportGenerating] = useState(false);
  // DB 템플릿 목록 (올바른 타입 사용)
  const [reportTemplates, setReportTemplates] = useState<ReportTemplateItem[]>([]);
  const [selectedReportTemplateId, setSelectedReportTemplateId] = useState<string | null>(null);
  const [includeCharts, setIncludeCharts] = useState(false);
  const [includeTables, setIncludeTables] = useState(true);
  const [includeImages, setIncludeImages] = useState(false);
  // Jinja2 템플릿 변수 관련 상태 (검색 페이지 보고서 다이얼로그용)
  const [jinja2Variables, setJinja2Variables] = useState<Jinja2Variable[]>([]);
  const [jinja2Values, setJinja2Values] = useState<Record<string, unknown>>({});
  const [jinja2VarsLoading, setJinja2VarsLoading] = useState(false);

  // Load search history from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("search-history");
      if (stored) setSearchHistory(JSON.parse(stored));
    } catch {
      // ignore
    }
  }, []);

  // Read initial query from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (q) {
      setQuery(q);
      handleSearch(q, 1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save search to history
  const addToHistory = useCallback(
    (q: string) => {
      const updated = [q, ...searchHistory.filter((h) => h !== q)].slice(0, MAX_HISTORY);
      setSearchHistory(updated);
      try {
        localStorage.setItem("search-history", JSON.stringify(updated));
      } catch {
        // ignore
      }
    },
    [searchHistory],
  );

  // Execute search
  const handleSearch = useCallback(
    async (q?: string, page?: number, overridePageSize?: number) => {
      const searchQuery = q ?? query;
      if (!searchQuery.trim()) return;

      addToHistory(searchQuery.trim());

      const effectivePageSize = overridePageSize ?? state.pageSize;
      setState((prev) => ({
        ...prev,
        loading: true,
        page: page ?? 1,
        ...(overridePageSize ? { pageSize: overridePageSize } : {}),
      }));

      try {
        // 백엔드 SearchRequest 스키마에 맞는 요청 본문을 구성한다
        const requestBody: Record<string, unknown> = {
          query: searchQuery.trim(),
          max_results: effectivePageSize,
          search_type: searchType === "all" ? "hybrid" : searchType,
        };

        // 필터 적용
        const activeFilters: Record<string, unknown> = {};
        if (filters.dateFrom) activeFilters.date_from = filters.dateFrom;
        if (filters.dateTo) activeFilters.date_to = filters.dateTo;
        if (filters.formats.length > 0) activeFilters.formats = filters.formats;
        if (filters.tags.length > 0) activeFilters.tags = filters.tags;
        if (Object.keys(activeFilters).length > 0) {
          requestBody.filters = activeFilters;
        }

        const data = await apiClient.post<{
          results: Array<{
            document_id?: string;
            document_name?: string;
            chunk_id?: string;
            chunk_index?: number;
            content?: string;
            score?: number;
            page_number?: number;
            section_title?: string;
            chunk_type?: string;
            highlights?: string[] | null;
          }>;
          qa_answer?: QAAnswer;
          total_results: number;
          search_type?: string;
          latency_ms?: number;
        }>("/search", requestBody);

        // Map snake_case API response to camelCase frontend interface
        const mappedResults: SearchResult[] = (data.results || []).map((r) => ({
          id: r.chunk_id || r.document_id || "",
          documentName: r.document_name || "제목 없음",
          documentFormat: undefined,
          chunkText: r.content || "",
          score: r.score || 0,
          pageNumber: r.page_number ?? undefined,
          sectionTitle: r.section_title ?? undefined,
          documentId: r.document_id,
        }));

        setState((prev) => ({
          ...prev,
          results: mappedResults,
          qaAnswer: data.qa_answer ?? null,
          totalCount: data.total_results ?? mappedResults.length,
          loading: false,
        }));

        // Update URL
        const url = new URL(window.location.href);
        url.searchParams.set("q", searchQuery.trim());
        url.searchParams.set("type", searchType);
        window.history.replaceState({}, "", url.toString());
      } catch (_err) {
        addToast("검색에 실패했습니다. 다시 시도해주세요.", "error");
        setState((prev) => ({ ...prev, loading: false }));
      }
    },
    [query, searchType, filters, state.pageSize, addToHistory, addToast],
  );

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSearch();
  };

  const totalPages = Math.ceil(state.totalCount / state.pageSize);
  const queryTerms = useMemo(() => query.trim().split(/\s+/).filter(Boolean), [query]);

  // Hallucination score indicator helper
  const getHallucinationColor = (score: number) => {
    if (score < 0.3) return "text-green-600 bg-green-50 border-green-200";
    if (score <= 0.6) return "text-yellow-600 bg-yellow-50 border-yellow-200";
    return "text-red-600 bg-red-50 border-red-200";
  };

  const getHallucinationLabel = (score: number) => {
    if (score < 0.3) return "낮은 위험";
    if (score <= 0.6) return "보통 위험";
    return "높은 위험";
  };

  // Report generation handlers
  // 보고서 작성 다이얼로그를 열고, DB 템플릿 목록을 로드한다
  const openReportDialog = async () => {
    setReportTitle("");
    setReportType("report");
    setSelectedReportTemplateId(null);
    setJinja2Variables([]);
    setJinja2Values({});
    setSelectedResultIds(new Set(state.results.map((r) => r.id)));
    setShowReportDialog(true);
    // DB 템플릿 목록을 서버에서 가져온다
    try {
      const res = await apiClient.get<{ items: ReportTemplateItem[] }>(
        "/templates?page=1&size=100",
      );
      setReportTemplates(res.items || []);
    } catch {
      // 템플릿 로드 실패 시 빈 목록으로 처리 (기본 AI 자유형 모드로 동작)
    }
  };

  // 검색 보고서 다이얼로그에서 Jinja2 템플릿 선택 시 변수 목록을 로드한다
  const handleReportTemplateChange = async (templateId: string | null) => {
    setSelectedReportTemplateId(templateId);
    setJinja2Variables([]);
    setJinja2Values({});

    if (!templateId) return;

    // 선택한 템플릿이 Jinja2 렌더링 모드인지 확인
    const tpl = reportTemplates.find((t) => t.id === templateId);
    if (!tpl || tpl.rendering_mode !== "jinja2") return;

    // Jinja2 변수 목록을 서버에서 가져온다
    setJinja2VarsLoading(true);
    try {
      const vars = await apiClient.get<Jinja2Variable[]>(`/templates/${templateId}/variables`);
      const variableList = Array.isArray(vars) ? vars : [];
      setJinja2Variables(variableList);

      // 변수 초기값 설정 (사용자 입력 카테고리만 표시하므로 빈 값으로 초기화)
      const initialValues: Record<string, unknown> = {};
      variableList.forEach((v) => {
        if (v.var_type === "boolean") {
          initialValues[v.name] = false;
        } else {
          initialValues[v.name] = "";
        }
      });
      setJinja2Values(initialValues);
    } catch {
      // 변수 로드 실패 시 무시 (서버에서 AI가 자동 생성)
    } finally {
      setJinja2VarsLoading(false);
    }
  };

  const toggleResultSelection = (id: string) => {
    setSelectedResultIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleGenerateReport = async () => {
    if (!reportTitle.trim()) {
      addToast("보고서 제목을 입력해주세요.", "error");
      return;
    }
    if (selectedResultIds.size === 0) {
      addToast("포함할 문서를 선택해주세요.", "error");
      return;
    }
    setReportGenerating(true);
    try {
      // 선택된 템플릿 정보를 찾는다
      const selectedTpl = reportTemplates.find((t) => t.id === selectedReportTemplateId);
      const isJinja2 = selectedTpl?.rendering_mode === "jinja2";

      // Jinja2 템플릿: user_input 카테고리 변수값을 custom_context로 전달한다
      // ai_generated 카테고리는 서버에서 소스 문서 기반으로 자동 생성한다
      const customContext: Record<string, unknown> = {};
      if (isJinja2 && jinja2Variables.length > 0) {
        jinja2Variables.forEach((v) => {
          // AI가 자동 생성하는 변수는 포함하지 않는다
          if (v.category === "ai_generated") return;
          const rawValue = jinja2Values[v.name];
          if (v.var_type === "array" && typeof rawValue === "string") {
            // 줄바꿈으로 구분된 텍스트를 배열로 변환
            customContext[v.name] = rawValue
              .split("\n")
              .map((s) => s.trim())
              .filter(Boolean);
          } else {
            customContext[v.name] = rawValue;
          }
        });
      }

      // ─── Phase 4 S3 이관: /reports/generate(410 Gone) → /v2/documents(Mode A) ───
      //
      // 검색 결과에서의 보고서 생성도 documents_v2 Mode A 로 일원화한다.
      // 템플릿 기반 Mode B 는 S4 예정이므로 템플릿 선택 여부와 무관하게
      // 현재는 Mode A 로 생성한 뒤 디자이너로 이동시킨다.

      // 1) 템플릿 선택(Mode B 의도) 안내
      if (selectedReportTemplateId) {
        addToast(
          "양식 채우기 모드는 준비 중입니다. 자유 생성(Mode A)으로 진행합니다.",
          "info",
        );
      }

      // 2) DocumentType 매핑 — search 화면은 report/minutes 만 노출
      //    report 는 템플릿 출력 포맷에 따라 slide_report(pptx) 또는 docx_report
      const outputFormat = selectedTpl?.output_format || "docx";
      const v2DocType: V2DocumentType =
        reportType === "minutes"
          ? "minutes"
          : outputFormat === "pptx"
            ? "slide_report"
            : "docx_report";

      // 3) 프롬프트 합성: 검색 쿼리 + 템플릿 힌트 + Jinja2 변수값(참고)
      const promptParts: string[] = [];
      promptParts.push(`제목: ${reportTitle.trim()}`);
      if (query.trim()) promptParts.push(`검색어/지시사항: ${query.trim()}`);
      if (selectedTpl?.name) promptParts.push(`참고 양식: ${selectedTpl.name}`);
      if (Object.keys(customContext).length > 0) {
        promptParts.push(
          `입력 값: ${Object.entries(customContext)
            .map(([k, v]) => `${k}=${Array.isArray(v) ? v.join(", ") : String(v)}`)
            .join("; ")}`,
        );
      }
      const flags: string[] = [];
      if (includeCharts) flags.push("차트 포함");
      if (includeTables) flags.push("표 포함");
      if (includeImages) flags.push("이미지 포함");
      if (flags.length > 0) promptParts.push(flags.join(", "));

      // 4) Mode A 생성 호출 — 검색에서 선택한 문서를 소스로 사용
      const generated = await generateDocument({
        type: v2DocType,
        prompt: promptParts.join("\n"),
        source_document_ids: Array.from(selectedResultIds),
      });

      addToast("문서 생성이 완료되었습니다. 디자이너로 이동합니다.", "success");
      setShowReportDialog(false);
      setSelectedReportTemplateId(null);
      setJinja2Variables([]);
      setJinja2Values({});

      // 5) 디자이너로 이동 — Export 는 우측 메뉴에서 진행
      router.push(`/designer/${generated.document_id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "보고서 생성에 실패했습니다.";
      addToast(message, "error");
    } finally {
      setReportGenerating(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl">
      {/* ── Search Header ─────────────────────────────────────────────── */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900">문서 검색</h1>
        <p className="mt-2 text-gray-500">AI 기반 검색으로 모든 문서를 검색합니다</p>
      </div>

      {/* ── Search Bar (Google style) ─────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="mx-auto mb-6 max-w-2xl">
        <div className="relative">
          <Search className="absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="검색어를 입력하세요..."
            className="w-full rounded-full border border-gray-300 bg-white py-3.5 pr-24 pl-12 text-base text-gray-900 placeholder-gray-400 shadow-sm transition-shadow focus:border-blue-400 focus:shadow-md focus:ring-2 focus:ring-blue-100 focus:outline-none"
            autoFocus
          />
          <div className="absolute top-1/2 right-2 flex -translate-y-1/2 items-center gap-1">
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                aria-label="검색어 지우기"
              >
                <X className="h-4 w-4" />
              </button>
            )}
            <button
              type="submit"
              disabled={!query.trim() || state.loading}
              className="rounded-full bg-blue-600 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {state.loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "검색"}
            </button>
          </div>
        </div>
      </form>

      {/* ── Search Type Tabs ──────────────────────────────────────────── */}
      <div className="mx-auto mb-4 flex max-w-2xl items-center justify-center gap-1">
        {SEARCH_TYPES.map((type) => (
          <button
            key={type.value}
            onClick={() => setSearchType(type.value)}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
              searchType === type.value
                ? "bg-blue-600 text-white"
                : "text-gray-600 hover:bg-gray-100",
            )}
          >
            {type.label}
          </button>
        ))}
        <div className="mx-2 h-6 w-px bg-gray-200" />
        <button
          onClick={() => setShowFilterSidebar(!showFilterSidebar)}
          className={cn(
            "flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors lg:hidden",
            "text-gray-600 hover:bg-gray-100",
          )}
        >
          <SlidersHorizontal className="h-4 w-4" />
          필터
        </button>
      </div>

      {/* ── Search History Chips ──────────────────────────────────────── */}
      {searchHistory.length > 0 && !state.results.length && !state.loading && (
        <div className="mx-auto mb-8 max-w-2xl">
          <div className="mb-2 flex items-center gap-2 text-xs text-gray-500">
            <Clock className="h-3.5 w-3.5" />
            최근 검색
          </div>
          <div className="flex flex-wrap gap-2">
            {searchHistory.map((h, i) => (
              <button
                key={`${h}-${i}`}
                onClick={() => {
                  setQuery(h);
                  handleSearch(h);
                }}
                className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-700 transition-colors hover:border-blue-300 hover:bg-blue-50 hover:text-blue-600"
              >
                {h}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Main Content Area ─────────────────────────────────────────── */}
      <div className="flex gap-6">
        {/* Results */}
        <div className="min-w-0 flex-1">
          {/* Loading */}
          {state.loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <p className="mt-3 text-sm text-gray-500">검색 중...</p>
            </div>
          )}

          {/* QA Answer (for Q&A mode) */}
          {!state.loading && state.qaAnswer && searchType === "qa" && (
            <div className="mb-6 rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-6 shadow-sm">
              <div className="mb-3 flex items-center gap-2">
                <Bot className="h-5 w-5 text-blue-600" />
                <span className="text-sm font-semibold text-blue-900">AI 생성 답변</span>
                {state.qaAnswer.modelUsed && (
                  <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-600">
                    {state.qaAnswer.modelUsed}
                  </span>
                )}
              </div>

              <div className="prose prose-sm max-w-none text-gray-800">
                <p className="whitespace-pre-wrap">{state.qaAnswer.answer}</p>
              </div>

              {/* Hallucination Score */}
              <div className="mt-4 flex items-center gap-3">
                <div
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium",
                    getHallucinationColor(state.qaAnswer.hallucinationScore),
                  )}
                >
                  <AlertTriangle className="h-3.5 w-3.5" />
                  환각 지수: {(state.qaAnswer.hallucinationScore * 100).toFixed(0)}%{" - "}
                  {getHallucinationLabel(state.qaAnswer.hallucinationScore)}
                </div>
              </div>

              {/* Citations */}
              {state.qaAnswer.citations.length > 0 && (
                <div className="mt-4">
                  <p className="mb-2 text-xs font-semibold text-gray-500 uppercase">출처</p>
                  <div className="space-y-2">
                    {state.qaAnswer.citations.map((citation) => (
                      <div
                        key={citation.id}
                        className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-200 bg-white p-3 text-sm transition-colors hover:border-blue-300"
                      >
                        <FileText className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-medium text-gray-800">
                              {citation.documentName}
                            </span>
                            <div className="flex shrink-0 items-center gap-2">
                              {citation.pageNumber !== null &&
                                citation.pageNumber !== undefined && (
                                  <span className="text-xs text-gray-400">
                                    p.{citation.pageNumber}
                                  </span>
                                )}
                              <ExternalLink className="h-3 w-3 text-gray-400" />
                            </div>
                          </div>
                          <p className="mt-1 line-clamp-2 text-xs text-gray-600">
                            {citation.chunkText}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Results list */}
          {!state.loading && state.results.length > 0 && (
            <>
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  <strong>{state.totalCount}</strong>건의 결과
                </p>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs text-gray-500">표시</span>
                    <select
                      value={state.pageSize}
                      onChange={(e) => {
                        const newSize = Number(e.target.value);
                        handleSearch(undefined, 1, newSize);
                      }}
                      className="rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                    >
                      {PAGE_SIZE_OPTIONS.map((size) => (
                        <option key={size} value={size}>
                          {size}건
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={openReportDialog}
                    className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                  >
                    <FileOutput className="h-4 w-4" />
                    보고서 작성
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {state.results.map((result) => (
                  <SearchResultCard key={result.id} result={result} queryTerms={queryTerms} />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-center gap-2">
                  <button
                    onClick={() => handleSearch(undefined, state.page - 1)}
                    disabled={state.page <= 1}
                    className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    이전
                  </button>

                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    let pageNum: number;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (state.page <= 3) {
                      pageNum = i + 1;
                    } else if (state.page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = state.page - 2 + i;
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handleSearch(undefined, pageNum)}
                        className={cn(
                          "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                          pageNum === state.page
                            ? "bg-blue-600 text-white"
                            : "text-gray-700 hover:bg-gray-100",
                        )}
                      >
                        {pageNum}
                      </button>
                    );
                  })}

                  <button
                    onClick={() => handleSearch(undefined, state.page + 1)}
                    disabled={state.page >= totalPages}
                    className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    다음
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              )}
            </>
          )}

          {/* No results */}
          {!state.loading &&
            state.results.length === 0 &&
            query.trim() &&
            state.totalCount === 0 && (
              <div className="flex flex-col items-center justify-center py-20">
                <Search className="h-12 w-12 text-gray-300" />
                <p className="mt-4 text-lg font-medium text-gray-700">검색 결과가 없습니다</p>
                <p className="mt-1 text-sm text-gray-500">
                  다른 키워드를 시도하거나 필터를 조정해보세요
                </p>
              </div>
            )}

          {/* Empty state (no query yet) */}
          {!state.loading &&
            !query.trim() &&
            state.results.length === 0 &&
            searchHistory.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20">
                <Search className="h-16 w-16 text-gray-200" />
                <p className="mt-4 text-lg font-medium text-gray-600">검색을 시작하세요</p>
                <p className="mt-1 text-sm text-gray-400">
                  위에 검색어를 입력하여 문서를 검색하세요
                </p>
              </div>
            )}
        </div>

        {/* ── Filter Sidebar ────────────────────────────────────────────── */}
        <aside className={cn("w-64 shrink-0", showFilterSidebar ? "block" : "hidden lg:block")}>
          <div className="sticky top-24 rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900">
              <SlidersHorizontal className="h-4 w-4" />
              필터
            </h3>

            {/* Date Range */}
            <div className="mt-4">
              <label className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-gray-600">
                <Calendar className="h-3.5 w-3.5" />
                날짜 범위
              </label>
              <div className="space-y-2">
                <input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters((f) => ({ ...f, dateFrom: e.target.value }))}
                  className="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-xs text-gray-700 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  placeholder="From"
                />
                <input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters((f) => ({ ...f, dateTo: e.target.value }))}
                  className="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-xs text-gray-700 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                  placeholder="To"
                />
              </div>
            </div>

            {/* Document Format */}
            <div className="mt-4">
              <label className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-gray-600">
                <FileText className="h-3.5 w-3.5" />
                문서 형식
              </label>
              <div className="space-y-1">
                {FORMAT_OPTIONS.map((fmt) => (
                  <label
                    key={fmt}
                    className="flex cursor-pointer items-center gap-2 rounded px-1 py-0.5 text-xs text-gray-700 hover:bg-gray-50"
                  >
                    <input
                      type="checkbox"
                      checked={filters.formats.includes(fmt)}
                      onChange={(e) => {
                        setFilters((f) => ({
                          ...f,
                          formats: e.target.checked
                            ? [...f.formats, fmt]
                            : f.formats.filter((v) => v !== fmt),
                        }));
                      }}
                      className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="uppercase">{fmt}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Tags */}
            <div className="mt-4">
              <label className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-gray-600">
                <Tag className="h-3.5 w-3.5" />
                태그
              </label>
              <div className="flex flex-wrap gap-1.5">
                {TAG_OPTIONS.map((tag) => (
                  <button
                    key={tag}
                    onClick={() =>
                      setFilters((f) => ({
                        ...f,
                        tags: f.tags.includes(tag)
                          ? f.tags.filter((t) => t !== tag)
                          : [...f.tags, tag],
                      }))
                    }
                    className={cn(
                      "rounded-full border px-2.5 py-1 text-xs transition-colors",
                      filters.tags.includes(tag)
                        ? "border-blue-300 bg-blue-50 text-blue-600"
                        : "border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50",
                    )}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>

            {/* Clear filters */}
            {(filters.dateFrom ||
              filters.dateTo ||
              filters.formats.length > 0 ||
              filters.tags.length > 0) && (
              <button
                onClick={() =>
                  setFilters({
                    dateFrom: "",
                    dateTo: "",
                    formats: [],
                    tags: [],
                  })
                }
                className="mt-4 w-full rounded-lg border border-gray-200 py-1.5 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-50"
              >
                필터 초기화
              </button>
            )}
          </div>
        </aside>
      </div>

      {/* ── Report Generation Dialog ──────────────────────────────────── */}
      {showReportDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setShowReportDialog(false)}
            aria-hidden="true"
          />
          <div className="relative z-50 w-full max-w-lg rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
              <FileOutput className="h-5 w-5 text-blue-600" />
              보고서 작성
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              검색 결과를 기반으로 보고서 또는 회의록을 생성합니다.
            </p>

            <div className="mt-4 space-y-4">
              {/* Report title */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  제목 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  maxLength={500}
                  placeholder="보고서 제목을 입력하세요 (최대 500자)"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                />
              </div>

              {/* Report type */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">유형</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setReportType("report")}
                    className={cn(
                      "rounded-lg border-2 px-4 py-2 text-sm font-medium transition-all",
                      reportType === "report"
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300",
                    )}
                  >
                    보고서
                  </button>
                  <button
                    onClick={() => setReportType("minutes")}
                    className={cn(
                      "rounded-lg border-2 px-4 py-2 text-sm font-medium transition-all",
                      reportType === "minutes"
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300",
                    )}
                  >
                    회의록
                  </button>
                </div>
              </div>

              {/* 템플릿 선택 (DB 템플릿이 있을 때만 표시) */}
              {reportTemplates.length > 0 && (
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    템플릿 선택{" "}
                    <span className="text-xs font-normal text-gray-400">(선택사항)</span>
                  </label>
                  <div className="max-h-48 space-y-1 overflow-y-auto rounded-lg border border-gray-200 p-2">
                    {/* 기본 (AI 자유형) 옵션 — 템플릿 없이 AI가 자유 형식으로 생성 */}
                    <label className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-gray-50">
                      <input
                        type="radio"
                        name="report-template"
                        checked={selectedReportTemplateId === null}
                        onChange={() => handleReportTemplateChange(null)}
                        className="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-gray-700">기본 (AI 자유형)</span>
                    </label>
                    {/* DB에 등록된 템플릿 목록 */}
                    {reportTemplates.map((tpl) => (
                      <label
                        key={tpl.id}
                        className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-gray-50"
                      >
                        <input
                          type="radio"
                          name="report-template"
                          checked={selectedReportTemplateId === tpl.id}
                          onChange={() => handleReportTemplateChange(tpl.id)}
                          className="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="truncate text-gray-700">{tpl.name}</span>
                        {tpl.rendering_mode && (
                          <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500">
                            {tpl.rendering_mode}
                          </span>
                        )}
                        {tpl.output_format && (
                          <span className="shrink-0 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-600 uppercase">
                            {tpl.output_format}
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Jinja2 템플릿 선택 시 사용자 입력 변수 폼 (user_input 카테고리만 표시) */}
              {selectedReportTemplateId && jinja2Variables.length > 0 && (
                <div>
                  <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-gray-700">
                    <Sparkles className="h-4 w-4 text-blue-500" />
                    템플릿 변수 입력
                  </label>
                  {jinja2VarsLoading ? (
                    <div className="flex items-center gap-2 py-4 text-sm text-gray-400">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      변수 정보를 불러오는 중...
                    </div>
                  ) : (
                    <div className="max-h-48 space-y-3 overflow-y-auto rounded-lg border border-gray-200 p-3">
                      {/* user_input 및 카테고리 미지정 변수만 입력 폼으로 표시 */}
                      {jinja2Variables
                        .filter((v) => v.category === "user_input" || !v.category)
                        .map((v) => (
                          <div key={v.name}>
                            <label className="mb-1 flex items-center gap-1.5 text-xs font-medium text-gray-600">
                              {v.label || v.name}
                              {v.required && <span className="text-red-500">*</span>}
                            </label>
                            {v.var_type === "array" ? (
                              <textarea
                                value={(jinja2Values[v.name] as string) || ""}
                                onChange={(e) =>
                                  setJinja2Values((prev) => ({ ...prev, [v.name]: e.target.value }))
                                }
                                placeholder="항목을 줄바꿈으로 구분하여 입력하세요"
                                rows={2}
                                className="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-xs text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                              />
                            ) : v.var_type === "boolean" ? (
                              <label className="flex cursor-pointer items-center gap-2">
                                <input
                                  type="checkbox"
                                  checked={Boolean(jinja2Values[v.name])}
                                  onChange={(e) =>
                                    setJinja2Values((prev) => ({
                                      ...prev,
                                      [v.name]: e.target.checked,
                                    }))
                                  }
                                  className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-xs text-gray-600">사용</span>
                              </label>
                            ) : v.var_type === "date" ? (
                              <DatePicker
                                value={(jinja2Values[v.name] as string) || ""}
                                onChange={(val) =>
                                  setJinja2Values((prev) => ({ ...prev, [v.name]: val }))
                                }
                                placeholder="날짜 선택"
                              />
                            ) : (
                              <input
                                type="text"
                                value={(jinja2Values[v.name] as string) || ""}
                                onChange={(e) =>
                                  setJinja2Values((prev) => ({ ...prev, [v.name]: e.target.value }))
                                }
                                placeholder={
                                  v.description || `${v.label || v.name}을(를) 입력하세요`
                                }
                                className="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-xs text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                              />
                            )}
                          </div>
                        ))}
                      {/* AI 자동 생성 항목이 있으면 안내 문구 표시 */}
                      {jinja2Variables.some((v) => v.category === "ai_generated") && (
                        <p className="text-[10px] text-blue-500">
                          * 나머지 항목은 AI가 소스 문서 기반으로 자동 생성합니다
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Document selection */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  포함할 문서 ({selectedResultIds.size}/{state.results.length})
                </label>
                <div className="max-h-48 overflow-y-auto rounded-lg border border-gray-200 p-2">
                  {state.results.map((result) => (
                    <label
                      key={result.id}
                      className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-gray-50"
                    >
                      <input
                        type="checkbox"
                        checked={selectedResultIds.has(result.id)}
                        onChange={() => toggleResultSelection(result.id)}
                        className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <FileText className="h-3.5 w-3.5 shrink-0 text-gray-400" />
                      <span className="truncate text-gray-700">
                        {result.documentName || result.id}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              {/* 컨텐츠 옵션 */}
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">
                  컨텐츠 옵션
                </label>
                <div className="flex flex-wrap gap-4">
                  <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={includeCharts}
                      onChange={(e) => setIncludeCharts(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    차트 포함
                  </label>
                  <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={includeTables}
                      onChange={(e) => setIncludeTables(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    표 포함
                  </label>
                  <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-700">
                    <input
                      type="checkbox"
                      checked={includeImages}
                      onChange={(e) => setIncludeImages(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    이미지 포함
                  </label>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setShowReportDialog(false)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleGenerateReport}
                disabled={reportGenerating}
                className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {reportGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    생성 중...
                  </>
                ) : (
                  "생성"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
