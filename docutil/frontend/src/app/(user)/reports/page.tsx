"use client";

import {
  FileText,
  FileSpreadsheet,
  File,
  Download,
  Trash2,
  Loader2,
  Plus,
  CheckCircle,
  AlertCircle,
  Clock,
  RefreshCw,
  Play,
  MessageSquare,
  ChevronDown,
  Sparkles,
  FileOutput,
  Eye,
  Image,
  Archive,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect, useCallback } from "react";

import { DocumentSelector } from "@/components/documents/document-selector";
import { ModeAPromoBanner } from "@/components/layouts/mode-a-promo-banner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import { ToastAction } from "@/components/ui/toast";
import { WarningBanner } from "@/components/ui/warning-banner";
import apiClient, { isApiError } from "@/lib/api/client";
import { generateDocument } from "@/lib/api/documents-v2";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";
import { cn } from "@/lib/utils/cn";
import type { DocumentType as V2DocumentType } from "@/types/document-schema";

// ── Types ──────────────────────────────────────────────────────────────────

/** 보고서 템플릿 인터페이스 (DB 템플릿 전용) */
interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  format: string;
  schema: TemplateField[];
  /** 렌더링 방식: 'jinja2' 또는 'structured' */
  renderingMode?: "jinja2" | "structured";
}

/** 기존 매개변수 필드 (structured 템플릿용) */
interface TemplateField {
  name: string;
  label: string;
  type: "text" | "number" | "select" | "date" | "boolean" | "textarea";
  required?: boolean;
  options?: string[];
  defaultValue?: string;
  placeholder?: string;
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

/** 이미지 생성 방식 */
type ImageProvider = "dalle3" | "unsplash" | "none";

interface ReportRaw {
  id: string;
  title: string;
  template_id?: string;
  status: string;
  output_format: string;
  output_storage_path?: string;
  error_message?: string;
  created_at: string;
  completed_at?: string;
  generation_params?: Record<string, unknown>;
}

interface Report {
  id: string;
  title: string;
  templateName: string;
  status: "pending" | "generating" | "processing" | "completed" | "error";
  format: string;
  generatedAt: string;
  errorMessage?: string;
  downloadUrl?: string;
}

interface ChatSessionRef {
  id: string;
  title: string;
  createdAt: string;
}

type SourceMode = "documents" | "chat";

type OutputFormat = "docx" | "pptx" | "pdf" | "html" | "hwp";

type DocumentType = "report" | "proposal" | "minutes";

// ── Constants ──────────────────────────────────────────────────────────────

const OUTPUT_FORMATS: {
  value: OutputFormat;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}[] = [
  { value: "docx", label: "DOCX", icon: FileText },
  { value: "pptx", label: "PPTX", icon: FileOutput },
  { value: "pdf", label: "PDF", icon: FileText },
  { value: "html", label: "HTML", icon: File },
  { value: "hwp", label: "HWP", icon: FileText },
];

const DOCUMENT_TYPES: { value: DocumentType; label: string; description: string }[] = [
  { value: "report", label: "보고서", description: "선택한 문서를 기반으로 보고서를 생성합니다" },
  {
    value: "proposal",
    label: "제안서",
    description: "선택한 문서를 기반으로 제안서 초안을 작성합니다",
  },
  { value: "minutes", label: "회의록", description: "선택한 문서를 기반으로 회의록을 작성합니다" },
];

/** 이미지 생성 방식 옵션 */
const IMAGE_PROVIDERS: { value: ImageProvider; label: string; description: string }[] = [
  { value: "dalle3", label: "DALL-E 3 (AI 생성)", description: "프롬프트 기반 맞춤 이미지" },
  { value: "unsplash", label: "Unsplash (스톡 이미지)", description: "무료 스톡 이미지 검색" },
  { value: "none", label: "사용하지 않음", description: "이미지 없이 생성" },
];

// DB 템플릿만 사용 (하드코딩 템플릿은 완전 제거됨)

// ── 프로바이더 라벨 매핑 ─────────────────────────────────────────────────
const PROVIDER_SHORT_LABELS: Record<string, string> = {
  openai: "GPT",
  azure_openai: "Azure",
  anthropic: "Claude",
  gemini: "Gemini",
  vllm: "vLLM",
};

/** LLM 프로바이더 값을 짧은 라벨로 변환한다 (null이면 빈 문자열) */
function getProviderTag(provider: string | null | undefined): string {
  if (!provider) return "";
  return PROVIDER_SHORT_LABELS[provider] || provider;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function getFormatIcon(format: string | undefined) {
  const f = (format || "").toLowerCase();
  if (f === "xlsx" || f === "csv") return FileSpreadsheet;
  if (f === "pptx") return FileOutput;
  return FileText;
}

function getFormatColor(format: string | undefined) {
  const f = (format || "").toLowerCase();
  if (f === "pdf") return "text-red-500";
  if (f === "docx" || f === "doc") return "text-blue-500";
  if (f === "pptx") return "text-orange-500";
  if (f === "xlsx" || f === "csv") return "text-green-500";
  if (f === "hwp") return "text-sky-500";
  if (f === "html") return "text-orange-500";
  return "text-gray-400";
}

function getStatusBadge(status: string) {
  switch (status) {
    case "pending":
      return {
        label: "대기 중",
        icon: Clock,
        color: "bg-yellow-50 text-yellow-700 border-yellow-200",
        spin: false,
      };
    case "generating":
    case "processing":
      return {
        label: "생성 중",
        icon: Loader2,
        color: "bg-blue-50 text-blue-700 border-blue-200",
        spin: true,
      };
    case "completed":
      return {
        label: "완료",
        icon: CheckCircle,
        color: "bg-green-50 text-green-700 border-green-200",
        spin: false,
      };
    case "error":
      return {
        label: "오류",
        icon: AlertCircle,
        color: "bg-red-50 text-red-700 border-red-200",
        spin: false,
      };
    default:
      return {
        label: status,
        icon: Clock,
        color: "bg-gray-50 text-gray-600 border-gray-200",
        spin: false,
      };
  }
}

/** 렌더링 모드에 따른 뱃지 스타일을 반환한다 */
function getRenderingModeBadge(mode: string | undefined) {
  if (mode === "jinja2") {
    return { label: "Jinja2", color: "bg-blue-100 text-blue-700 border-blue-200" };
  }
  return { label: "Structured", color: "bg-blue-100 text-blue-800 border-blue-200" };
}

// ── Component ──────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const { addToast, toast } = useToast();
  const { user } = useAuth();
  const router = useRouter();

  /**
   * 410 Gone 응답을 디자이너 이관 안내 토스트로 변환한다.
   *
   * Phase 4 S2 D6: `POST /reports/generate`, `DELETE /reports/{id}` 등 쓰기 경로는
   * 410 Gone + `X-Deprecated-API: true` + 한국어 detail 메시지를 반환한다.
   * 이 핸들러는 에러가 410인 경우 서버 detail을 그대로 노출하고
   * "디자이너 열기" 액션 버튼을 포함한 토스트를 띄운다.
   *
   * @returns 410으로 처리된 경우 true, 그 외 에러면 false (호출 측이 기본 토스트 노출)
   */
  const handleApi410 = useCallback(
    (err: unknown): boolean => {
      if (isApiError(err) && err.status === 410) {
        toast({
          title: "이동된 기능입니다",
          description:
            err.detail ||
            "해당 기능은 /v2/documents 로 이관되었습니다. 디자이너(/designer/create) 를 사용하세요.",
          variant: "default",
          action: (
            <ToastAction altText="디자이너 열기" onClick={() => router.push("/designer/create")}>
              디자이너 열기
            </ToastAction>
          ),
        });
        return true;
      }
      return false;
    },
    [toast, router],
  );

  // Tab state
  const [activeTab, setActiveTab] = useState<"generate" | "my-reports">("generate");

  // ── Generate tab state ───────────────────────────────────────────────────
  const [documentType, setDocumentType] = useState<DocumentType>("report");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [sourceMode, setSourceMode] = useState<SourceMode>("documents");
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [selectedChatSessionId, setSelectedChatSessionId] = useState<string | null>(null);
  const [chatSessions, setChatSessions] = useState<ChatSessionRef[]>([]);
  const [chatSessionsLoading, setChatSessionsLoading] = useState(false);
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("docx");
  const [params, setParams] = useState<Record<string, string>>({});
  const [aiPrompt, setAiPrompt] = useState("");
  // 차트/표 포함 옵션 (PPTX, DOCX 형식에서만 사용)
  const [includeCharts, setIncludeCharts] = useState(false);
  const [includeTables, setIncludeTables] = useState(true); // 표는 기본 활성화
  // 이미지 생성 방식 (기본: DALL-E 3)
  const [imageProvider, setImageProvider] = useState<ImageProvider>("dalle3");
  const [generating, setGenerating] = useState(false);
  const [generateProgress, setGenerateProgress] = useState(0);
  const [previewLoading, setPreviewLoading] = useState<string | null>(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);

  // ── Jinja2 변수 관련 상태 ──────────────────────────────────────────────
  /** Jinja2 템플릿의 변수 메타데이터 목록 */
  const [jinja2Variables, setJinja2Variables] = useState<Jinja2Variable[]>([]);
  /** 사용자가 입력한 Jinja2 변수 값 */
  const [jinja2Values, setJinja2Values] = useState<Record<string, unknown>>({});
  /** 변수 목록 로딩 중 여부 */
  const [jinja2VarsLoading, setJinja2VarsLoading] = useState(false);
  // aiAutoFilling 상태 제거됨 (AI 미리보기 버튼 제거)
  /** image 타입 변수에서 선택한 이미지 소스(AI 생성 vs Unsplash) */
  const [imageVarSources, setImageVarSources] = useState<Record<string, "ai" | "unsplash">>({});

  // ── My Reports tab state ─────────────────────────────────────────────────
  const [reports, setReports] = useState<Report[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);

  // ── DB Templates & Agents ─────────────────────────────────────────────
  const [dbTemplates, setDbTemplates] = useState<ReportTemplate[]>([]);
  const [agents, setAgents] = useState<
    {
      id: string;
      name: string;
      description: string | null;
      agent_type: string;
      llm_provider?: string | null;
      llm_model?: string | null;
    }[]
  >([]);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  // Load DB templates (서버에 저장된 전체 템플릿을 가져와서 outputFormat으로 프론트 필터링)
  useEffect(() => {
    const loadDbTemplates = async () => {
      try {
        // template_type이 한글 자유 텍스트로 저장되어 있어 필터 제거, 전체 조회
        const data = await apiClient.get<{
          items: Array<{
            id: string;
            name: string;
            description: string | null;
            template_type: string;
            tone: string;
            output_format: string;
            schema: Record<string, unknown> | null;
            sample_prompt: string | null;
            rendering_mode: string;
          }>;
        }>("/templates?page=1&size=100");
        if (data.items?.length > 0) {
          setDbTemplates(
            data.items.map((t) => ({
              id: t.id,
              name: t.name,
              description: t.description || "",
              format: t.output_format,
              // DB 템플릿의 rendering_mode를 저장한다
              renderingMode: (t.rendering_mode === "jinja2" ? "jinja2" : "structured") as
                | "jinja2"
                | "structured",
              schema: t.schema
                ? Object.entries(t.schema).map(([key, val]) => ({
                    name: key,
                    label: (val as Record<string, string>)?.label || key,
                    type: ((val as Record<string, string>)?.type ||
                      "text") as TemplateField["type"],
                    required: (val as Record<string, boolean>)?.required || false,
                    placeholder: (val as Record<string, string>)?.placeholder || "",
                  }))
                : [],
            })),
          );
        } else {
          setDbTemplates([]);
        }
      } catch {
        setDbTemplates([]);
      }
    };
    loadDbTemplates();
  }, []); // 전체 조회이므로 documentType 의존성 제거

  // Load agents (사용 가능한 AI 에이전트 목록을 가져온다)
  useEffect(() => {
    const loadAgents = async () => {
      try {
        // 유형별 에이전트 필터: 보고서→report, 제안서→proposal, 회의록→minutes
        const typeMap =
          documentType === "report"
            ? "report"
            : documentType === "minutes"
              ? "minutes"
              : "proposal";
        const data = await apiClient.get<{ items: typeof agents }>("/agents", {
          agent_type: typeMap,
        });
        setAgents(data.items || []);
      } catch {
        setAgents([]);
      }
    };
    loadAgents();
  }, [documentType]);

  // DB에서 가져온 템플릿 목록을 그대로 사용한다
  const templates = dbTemplates;
  // 현재 선택된 템플릿 객체를 찾는다
  const selectedTemplate = templates.find((t) => t.id === selectedTemplateId) ?? null;

  // 현재 선택된 템플릿이 Jinja2 렌더링 방식인지 판별
  const isJinja2 = selectedTemplate?.renderingMode === "jinja2";

  // Reset template selection when document type changes (유형 변경 시 선택 초기화)
  useEffect(() => {
    setSelectedTemplateId(null);
    setSelectedAgentId(null);
    setParams({});
    setJinja2Variables([]);
    setJinja2Values({});
    setImageVarSources({});
  }, [documentType]);

  // ── Load Jinja2 variables (템플릿 선택 시 변수 목록 로드) ──────────────
  useEffect(() => {
    // Jinja2 템플릿이 아니면 변수를 로드하지 않는다
    if (!selectedTemplateId || !isJinja2) {
      setJinja2Variables([]);
      setJinja2Values({});
      setImageVarSources({});
      return;
    }

    const loadVariables = async () => {
      setJinja2VarsLoading(true);
      try {
        // GET /templates/{id}/variables 호출하여 변수 메타데이터를 가져온다
        const vars = await apiClient.get<Jinja2Variable[]>(
          `/templates/${selectedTemplateId}/variables`,
        );
        const variableList = Array.isArray(vars) ? vars : [];
        setJinja2Variables(variableList);

        // 변수 초기값 설정 (빈 값으로 초기화)
        const initialValues: Record<string, unknown> = {};
        const initialImageSources: Record<string, "ai" | "unsplash"> = {};
        variableList.forEach((v) => {
          if (v.var_type === "boolean") {
            initialValues[v.name] = false;
          } else if (v.var_type === "array") {
            initialValues[v.name] = "";
          } else if (v.var_type === "image") {
            initialValues[v.name] = ""; // 이미지 프롬프트
            initialImageSources[v.name] = "ai"; // 기본: AI 생성
          } else {
            initialValues[v.name] = "";
          }

          // session_auto 카테고리: 로그인 사용자 정보로 자동 채움
          if (v.category === "session_auto" && user) {
            const nameKey = v.name.toLowerCase();
            if (
              nameKey.includes("작성자") ||
              nameKey.includes("성명") ||
              nameKey.includes("author") ||
              nameKey.includes("name")
            ) {
              initialValues[v.name] = user.username || "";
            } else if (
              nameKey.includes("소속") ||
              nameKey.includes("부서") ||
              nameKey.includes("department") ||
              nameKey.includes("org")
            ) {
              // 조직명 + 부서명 결합 (예: "(주)아이디노 플랫폼사업팀")
              const orgN = user.organization_name || "";
              const deptN = user.department_name || "";
              initialValues[v.name] = orgN ? `${orgN} ${deptN}`.trim() : deptN;
            }
          }
        });
        setJinja2Values(initialValues);
        setImageVarSources(initialImageSources);
      } catch {
        setJinja2Variables([]);
        addToast("변수 정보를 불러오지 못했습니다.", "error");
      } finally {
        setJinja2VarsLoading(false);
      }
    };
    loadVariables();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTemplateId, isJinja2]);

  // ── Load chat sessions ───────────────────────────────────────────────────

  useEffect(() => {
    async function loadChatSessions() {
      setChatSessionsLoading(true);
      try {
        const data = await apiClient.get<{ items: ChatSessionRef[] }>("/chat/sessions");
        setChatSessions(data.items ?? []);
      } catch {
        // ignore
      } finally {
        setChatSessionsLoading(false);
      }
    }
    if (sourceMode === "chat") {
      loadChatSessions();
    }
  }, [sourceMode]);

  // ── Load reports ─────────────────────────────────────────────────────────

  const loadReports = useCallback(async () => {
    setReportsLoading(true);
    try {
      const data = await apiClient.get<{ items: ReportRaw[] }>("/reports");
      const mapped: Report[] = (data.items ?? []).map((r) => ({
        id: r.id,
        title: r.title,
        templateName: (r.generation_params?.template_name as string) || "—",
        status: r.status as Report["status"],
        format: r.output_format || "docx",
        generatedAt: r.created_at,
        errorMessage: r.error_message,
      }));
      setReports(mapped);
    } catch {
      addToast("보고서 목록을 불러오지 못했습니다.", "error");
    } finally {
      setReportsLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (activeTab === "my-reports") loadReports();
  }, [activeTab, loadReports]);

  // ── Auto-refresh for pending/generating reports ──────────────────────────

  useEffect(() => {
    if (activeTab !== "my-reports") return;
    const hasPending = reports.some(
      (r) => r.status === "pending" || r.status === "generating" || r.status === "processing",
    );
    if (!hasPending) return;
    const interval = setInterval(loadReports, 5000);
    return () => clearInterval(interval);
  }, [activeTab, reports, loadReports]);

  // ── Handle template select ───────────────────────────────────────────────

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplateId(templateId);
    const template = templates.find((t) => t.id === templateId);
    if (template) {
      const defaults: Record<string, string> = {};
      template.schema.forEach((field) => {
        if (field.defaultValue) defaults[field.name] = field.defaultValue;
      });
      setParams(defaults);
      setOutputFormat((template.format as OutputFormat) || "docx");
    }
  };

  const handleParamChange = (fieldName: string, value: string) => {
    setParams((prev) => ({ ...prev, [fieldName]: value }));
  };

  /** Jinja2 변수 값을 업데이트하는 핸들러 */
  const handleJinja2ValueChange = (varName: string, value: unknown) => {
    setJinja2Values((prev) => ({ ...prev, [varName]: value }));
  };

  /** image 타입 변수의 소스(AI/Unsplash)를 변경하는 핸들러 */
  const handleImageVarSourceChange = (varName: string, source: "ai" | "unsplash") => {
    setImageVarSources((prev) => ({ ...prev, [varName]: source }));
  };

  // DB 템플릿 미리보기: /templates/{id}/preview API를 호출하여 파일을 가져온다
  const handlePreview = async (templateId: string) => {
    setPreviewLoading(templateId);
    setPreviewBlobUrl(null);
    try {
      const blob = await apiClient.getBlob(`/templates/${templateId}/preview`);
      // 기존 Blob URL이 있으면 메모리 해제
      if (previewBlobUrl) window.URL.revokeObjectURL(previewBlobUrl);
      const url = window.URL.createObjectURL(blob);
      setPreviewBlobUrl(url);
    } catch {
      addToast("미리보기를 불러올 수 없습니다.", "error");
    } finally {
      setPreviewLoading(null);
    }
  };

  // ── Generate ─────────────────────────────────────────────────────────────

  const handleGenerate = async () => {
    if (!selectedTemplateId) {
      addToast("템플릿을 선택해주세요.", "info");
      return;
    }

    if (sourceMode === "documents" && selectedDocIds.length === 0) {
      addToast("문서를 하나 이상 선택해주세요.", "info");
      return;
    }

    if (sourceMode === "chat" && !selectedChatSessionId) {
      addToast("채팅 세션을 선택해주세요.", "info");
      return;
    }

    // Jinja2 템플릿: 필수 변수 검증 (ai_generated는 서버에서 생성하므로 검증 제외)
    if (isJinja2 && jinja2Variables.length > 0) {
      for (const v of jinja2Variables) {
        if (v.required && v.category !== "ai_generated") {
          const val = jinja2Values[v.name];
          if (val === undefined || val === null || val === "") {
            addToast(`"${v.label || v.name}" 항목은 필수입니다.`, "info");
            return;
          }
        }
      }
    }

    // Structured 템플릿: 기존 params 검증
    if (!isJinja2 && selectedTemplate) {
      for (const field of selectedTemplate.schema) {
        if (field.required && !params[field.name]?.trim()) {
          addToast(`"${field.label}" 항목은 필수입니다.`, "info");
          return;
        }
      }
    }

    // title은 params.title이 있으면 사용, 없으면 Jinja2 변수의 title, 그 다음 템플릿 이름
    const title =
      params.title?.trim() ||
      (typeof jinja2Values.title === "string" ? jinja2Values.title.trim() : "") ||
      selectedTemplate?.name ||
      "보고서";

    setGenerating(true);
    setGenerateProgress(0);

    const progressInterval = setInterval(() => {
      setGenerateProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    try {
      // Jinja2 템플릿: custom_context에 사용자 입력 변수값을 포함시킨다
      // Structured 템플릿: 기존 params를 그대로 전달
      const renderingMode = isJinja2 ? "jinja2" : "structured";

      // Jinja2 변수값을 서버에 맞는 형태로 변환한다
      // - array 타입: 줄바꿈으로 구분된 문자열을 배열로 변환
      // - image 타입: 프롬프트와 소스 정보를 포함
      // user_input + session_auto 값만 custom_context로 전달
      // ai_generated는 서버에서 소스 문서 기반으로 자동 생성
      const customContext: Record<string, unknown> = {};
      if (isJinja2) {
        jinja2Variables.forEach((v) => {
          // ai_generated 카테고리는 서버가 생성하므로 포함하지 않음
          if (v.category === "ai_generated") return;

          const rawValue = jinja2Values[v.name];
          if (v.var_type === "array" && typeof rawValue === "string") {
            // 줄바꿈으로 구분된 텍스트를 배열로 변환
            customContext[v.name] = rawValue
              .split("\n")
              .map((s) => s.trim())
              .filter(Boolean);
          } else if (v.var_type === "image") {
            // 이미지 변수: 프롬프트와 소스(ai/unsplash) 정보 포함
            customContext[v.name] = {
              prompt: rawValue || "",
              source: imageVarSources[v.name] || "ai",
            };
          } else {
            customContext[v.name] = rawValue;
          }
        });
      }

      // 이미지 설정: 이미지 생성 방식에 따라 설정
      const imageConfig =
        imageProvider !== "none"
          ? {
              provider: imageProvider === "dalle3" ? "dalle3" : "unsplash",
            }
          : undefined;

      // ─── Phase 4 S3 이관: /reports/generate(410 Gone) → /v2/documents(Mode A) ───
      //
      // 기존 보고서 파이프라인(`tb_generated_reports`)은 S2 에서 archive 로 전환되며
      // 410 Gone 을 반환한다. 신규 생성은 documents_v2 + 디자이너(Mode A)로만 가능.
      // 아래 로직은 기존 "보고서 화면" UX 를 유지하면서 백엔드만 교체한다 —
      // 생성 성공 시 `/designer/{id}` 로 이동하여 Export 단계에서 포맷을 선택한다.
      //
      // Mode B(양식 채우기, 템플릿 기반)는 Phase 4 S4 에서 제공 예정이므로,
      // 사용자가 템플릿을 선택한 경우에도 현재는 Mode A 로 우회 생성한다.

      // 1) 템플릿 선택(Mode B 의도) → S4 준비 중 안내 (생성은 Mode A 로 우회)
      if (selectedTemplateId) {
        addToast(
          "양식 채우기 모드는 준비 중입니다. 자유 생성(Mode A)으로 진행합니다.",
          "info",
        );
      }

      // 2) 기존 DocumentType("report"/"proposal"/"minutes") → V2 DocumentType 매핑
      //    - proposal / minutes 는 그대로
      //    - report 는 출력 포맷에 따라 slide_report(pptx) 또는 docx_report(그 외)
      const v2DocType: V2DocumentType =
        documentType === "proposal"
          ? "proposal"
          : documentType === "minutes"
            ? "minutes"
            : outputFormat === "pptx"
              ? "slide_report"
              : "docx_report";

      // 3) 프롬프트 합성: title + AI 지시사항 + Jinja2 변수값(참고)
      const promptParts: string[] = [];
      if (title) promptParts.push(`제목: ${title}`);
      if (aiPrompt?.trim()) promptParts.push(`지시사항: ${aiPrompt.trim()}`);
      if (selectedTemplate?.name) {
        promptParts.push(`참고 양식: ${selectedTemplate.name}`);
      }
      if (isJinja2 && Object.keys(customContext).length > 0) {
        promptParts.push(
          `입력 값: ${Object.entries(customContext)
            .map(([k, v]) => `${k}=${Array.isArray(v) ? v.join(", ") : String(v)}`)
            .join("; ")}`,
        );
      }
      if (!isJinja2 && Object.keys(params).length > 0) {
        promptParts.push(
          `매개변수: ${Object.entries(params)
            .map(([k, v]) => `${k}=${v}`)
            .join("; ")}`,
        );
      }
      if (imageConfig) {
        promptParts.push(
          imageConfig.provider === "dalle3"
            ? "이미지는 DALL-E 3 로 생성"
            : "이미지는 Unsplash 에서 선택",
        );
      }
      if (outputFormat === "pptx" || outputFormat === "docx") {
        const flags: string[] = [];
        if (includeCharts) flags.push("차트 포함");
        if (includeTables) flags.push("표 포함");
        if (imageProvider !== "none") flags.push("이미지 포함");
        if (flags.length > 0) promptParts.push(flags.join(", "));
      }

      // 4) Source 선택: 문서 모드만 직접 전달. chat 모드는 현재 문서 ID 로 변환
      //    경로가 없으므로 프롬프트에만 힌트로 포함 (S6 에서 Chat → 컨텍스트 결합 개선).
      const sourceDocumentIds =
        sourceMode === "documents" && selectedDocIds.length > 0
          ? selectedDocIds
          : undefined;
      if (sourceMode === "chat" && selectedChatSessionId) {
        promptParts.push(`(채팅 세션 ${selectedChatSessionId} 를 참고)`);
      }

      // 5) Mode A 생성 호출
      const generated = await generateDocument({
        type: v2DocType,
        prompt: promptParts.join("\n") || title || "문서 생성",
        source_document_ids: sourceDocumentIds,
        agent_id: selectedAgentId || undefined,
      });

      clearInterval(progressInterval);
      setGenerateProgress(100);
      addToast("문서 생성이 완료되었습니다. 디자이너로 이동합니다.", "success");

      // 6) 디자이너 편집 화면으로 이동 (우측 Export 메뉴에서 포맷 선택)
      setTimeout(() => {
        setGenerating(false);
        setGenerateProgress(0);
        router.push(`/designer/${generated.document_id}`);
      }, 600);
    } catch (err) {
      clearInterval(progressInterval);
      setGenerating(false);
      setGenerateProgress(0);
      // 410 Gone 은 구 경로 잔존 호출에서만 발생. 이관 후엔 정상 경로이므로 일반 오류로 처리.
      if (!handleApi410(err)) {
        // 트랙 #106 P0 — 422 ValidationError 는 LLM 일시적 형식 실패. 사용자 친화 메시지 +
        // 디자이너 열기 (혼란 유발) 대신 "재시도" 액션 제공.
        const isValidationError =
          err instanceof Error &&
          (err.message.includes("DocumentSchema 를 만족하지 못했습니다") ||
            err.message.includes("스키마 검증 실패") ||
            err.message.includes("422"));
        if (isValidationError) {
          toast({
            title: "LLM 응답이 일시적으로 형식을 맞추지 못했습니다",
            description:
              "내부 자동 재시도까지 모두 실패했습니다. 잠시 후 다시 시도해 주세요. 같은 프롬프트를 반복하면 동일 결과가 나올 수 있어 표현을 조금 바꿔 보시는 것을 권장합니다.",
            variant: "destructive",
            action: (
              <ToastAction altText="다시 시도" onClick={() => handleGenerate()}>
                다시 시도
              </ToastAction>
            ),
          });
        } else {
          const message = err instanceof Error ? err.message : "생성에 실패했습니다.";
          addToast(message, "error");
        }
      }
    }
  };

  // ── Delete / Download ────────────────────────────────────────────────────

  const handleDeleteReport = async (reportId: string) => {
    if (!confirm("이 항목을 삭제하시겠습니까?")) return;
    try {
      await apiClient.delete(`/reports/${reportId}`);
      setReports((prev) => prev.filter((r) => r.id !== reportId));
      addToast("삭제되었습니다.", "success");
    } catch (err) {
      // 410 Gone (아카이브 경로에서 삭제 시도) → 디자이너 안내 토스트
      if (!handleApi410(err)) {
        addToast("삭제에 실패했습니다.", "error");
      }
    }
  };

  const handleDownload = async (report: Report) => {
    try {
      const response = await apiClient.getBlob(`/reports/${report.id}/download`);
      const url = window.URL.createObjectURL(response);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${report.title}.${report.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      addToast("다운로드에 실패했습니다.", "error");
    }
  };

  // ── Step numbering (Jinja2 vs Structured에 따라 동적으로 변경) ──────────
  // Jinja2: 1.유형 → 2.템플릿 → 3.소스 → 4.변수입력 → 5.에이전트 → 6.AI지시사항 → 7.콘텐츠옵션 → 8.생성
  // Structured: 1.유형 → 2.템플릿 → 3.소스 → 4.매개변수(있으면) → 5.에이전트(있으면) → 6.AI지시사항 → 7.콘텐츠옵션 → 8.생성
  const hasParams = !isJinja2 && selectedTemplate && selectedTemplate.schema.length > 0;
  const hasJinja2Vars = isJinja2 && jinja2Variables.length > 0;
  const hasAgents = agents.length > 0;
  let stepNum = 2;
  const stepSource = ++stepNum; // 3: 소스 선택
  const stepJinja2Vars = hasJinja2Vars ? ++stepNum : -1; // 4: Jinja2 변수 입력 (Jinja2 전용)
  const stepParams = hasParams ? ++stepNum : -1; // 기존 매개변수 (Structured 전용)
  const stepAgent = hasAgents ? ++stepNum : -1; // 에이전트 선택
  const stepPrompt = ++stepNum; // AI 지시사항
  const stepContentOptions = outputFormat === "pptx" || outputFormat === "docx" ? ++stepNum : -1; // 콘텐츠 옵션

  return (
    <div className="mx-auto max-w-6xl">
      {/* 페이지 헤더 — Phase 4 S2 D7: 아카이브(읽기 전용) 상태를 배지로 명시 */}
      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">보고서 / 제안서</h1>
          {/* 보관 상태 배지: 이 페이지가 과거 방식 보고서 아카이브임을 명시 */}
          <Badge
            variant="secondary"
            className="gap-1.5 bg-amber-100 text-amber-800 hover:bg-amber-100"
          >
            <Archive className="h-3 w-3" aria-hidden="true" />
            보관됨 · 읽기 전용
          </Badge>
        </div>
        <p className="mt-1 text-sm text-gray-500">
          과거 방식으로 생성된 보고서 아카이브입니다. 새 보고서는 디자이너에서 작성해 주세요.
        </p>
      </div>

      {/* Phase 4 S2 D7: 아카이브 안내 경고 배너 (읽기 전용 + 디자이너 이동 CTA) */}
      <WarningBanner title="보관된 보고서 페이지" dismissible className="mb-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span>
            이 페이지는 과거 방식으로 생성된 보고서를 조회합니다. 새 보고서는 디자이너에서 만들어
            주세요.
          </span>
          <Button
            asChild
            size="sm"
            className="shrink-0 bg-yellow-600 text-white hover:bg-yellow-700"
          >
            <Link href="/designer/create">
              <ExternalLink className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
              디자이너로 이동
            </Link>
          </Button>
        </div>
      </WarningBanner>

      {/* Mode A Designer 이관 안내 배너 (Phase 4 S2 D1 — 레거시 /reports 병존 기간 동안 노출) */}
      <ModeAPromoBanner storageKey="docutil.banner.reports-modeA.dismissed" className="mb-6" />

      {/* 탭 전환 (생성 / 내 문서) */}
      <div className="mb-6 border-b border-gray-200">
        <div className="flex gap-0">
          <button
            onClick={() => setActiveTab("generate")}
            className={cn(
              "relative px-6 py-3 text-sm font-medium transition-colors",
              activeTab === "generate" ? "text-blue-600" : "text-gray-500 hover:text-gray-700",
            )}
          >
            <span className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              생성
            </span>
            {activeTab === "generate" && (
              <span className="absolute inset-x-0 bottom-0 h-0.5 bg-blue-600" />
            )}
          </button>
          <button
            onClick={() => setActiveTab("my-reports")}
            className={cn(
              "relative px-6 py-3 text-sm font-medium transition-colors",
              activeTab === "my-reports" ? "text-blue-600" : "text-gray-500 hover:text-gray-700",
            )}
          >
            <span className="flex items-center gap-2">
              <FileText className="h-4 w-4" />내 문서
            </span>
            {activeTab === "my-reports" && (
              <span className="absolute inset-x-0 bottom-0 h-0.5 bg-blue-600" />
            )}
          </button>
        </div>
      </div>

      {/* ── 생성 탭 ──────────────────────────────────────────────────── */}
      {activeTab === "generate" && (
        <div className="space-y-8">
          {/* Step 1: 유형 + 출력형식 선택 */}
          <section>
            <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
              1. 유형 및 문서 형식
            </h2>

            {/* 보고서/제안서 유형 토글 */}
            <div className="mb-4 flex items-center gap-2">
              {DOCUMENT_TYPES.map((dt) => (
                <button
                  key={dt.value}
                  onClick={() => setDocumentType(dt.value)}
                  className={cn(
                    "flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors",
                    documentType === dt.value
                      ? "bg-blue-600 text-white shadow-sm"
                      : "border border-gray-300 text-gray-600 hover:bg-gray-50",
                  )}
                >
                  {dt.value === "report" ? (
                    <FileText className="h-4 w-4" />
                  ) : (
                    <FileOutput className="h-4 w-4" />
                  )}
                  {dt.label}
                </button>
              ))}
            </div>

            {/* 출력 문서 형식 선택 (DOCX, PPTX, PDF 등) */}
            <p className="mb-2 text-xs text-gray-500">출력 문서 형식을 선택하세요</p>
            <div className="flex gap-2">
              {OUTPUT_FORMATS.map((fmt) => {
                const FmtIcon = fmt.icon;
                return (
                  <button
                    key={fmt.value}
                    onClick={() => setOutputFormat(fmt.value)}
                    className={cn(
                      "flex items-center gap-2 rounded-lg border-2 px-4 py-2.5 text-sm font-medium transition-all",
                      outputFormat === fmt.value
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300",
                    )}
                  >
                    <FmtIcon
                      className={cn(
                        "h-4 w-4",
                        outputFormat === fmt.value ? "text-blue-600" : "text-gray-400",
                      )}
                    />
                    {fmt.label}
                  </button>
                );
              })}
            </div>
          </section>

          {/* Step 2: 템플릿 선택 (출력형식에 맞게 필터링) + 미리보기 패널 */}
          <section>
            <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
              2. 템플릿 선택
            </h2>
            {(() => {
              const filteredTemplates = templates.filter(
                (t) => t.format === outputFormat || !t.format,
              );
              return filteredTemplates.length > 0 ? (
                <div className="flex gap-4">
                  {/* 왼쪽: 템플릿 카드 목록 */}
                  <div className="grid flex-1 grid-cols-2 gap-2">
                    {filteredTemplates.map((template) => {
                      const FormatIcon = getFormatIcon(template.format);
                      const formatColor = getFormatColor(template.format);
                      const selected = selectedTemplateId === template.id;
                      // 렌더링 모드 뱃지 (Jinja2: 파란색, Structured: 보라색)
                      const modeBadge = getRenderingModeBadge(template.renderingMode);

                      return (
                        <button
                          key={template.id}
                          onClick={() => {
                            handleTemplateSelect(template.id);
                            // 템플릿 선택 시 미리보기도 함께 로드한다
                            handlePreview(template.id);
                          }}
                          className={cn(
                            "flex flex-col rounded-lg border-2 p-3 text-left transition-all",
                            selected
                              ? "border-blue-600 bg-blue-50 shadow-sm"
                              : "border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm",
                          )}
                        >
                          <div className="flex items-center gap-2">
                            <FormatIcon className={cn("h-4 w-4 shrink-0", formatColor)} />
                            <span
                              className={cn(
                                "truncate text-sm font-semibold",
                                selected ? "text-blue-900" : "text-gray-900",
                              )}
                            >
                              {template.name}
                            </span>
                          </div>
                          <p className="mt-1 line-clamp-1 text-xs text-gray-500">
                            {template.description}
                          </p>
                          {/* 하단: 출력형식 뱃지 + 렌더링 모드 뱃지 */}
                          <div className="mt-1.5 flex items-center gap-1.5">
                            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500 uppercase">
                              {template.format}
                            </span>
                            <span
                              className={cn(
                                "rounded border px-1.5 py-0.5 text-[10px] font-medium",
                                modeBadge.color,
                              )}
                            >
                              {modeBadge.label}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* 오른쪽: 미리보기 패널 */}
                  <div className="w-80 shrink-0 overflow-hidden rounded-lg border border-gray-200 bg-gray-50">
                    {previewLoading ? (
                      <div className="flex h-64 items-center justify-center">
                        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
                      </div>
                    ) : previewBlobUrl && selectedTemplate ? (
                      <div className="flex h-full flex-col">
                        <div className="flex items-center justify-between border-b border-gray-200 bg-white px-3 py-2">
                          <span className="text-xs font-medium text-gray-700">미리보기</span>
                        </div>
                        <div className="flex flex-1 flex-col items-center justify-center gap-4 p-4">
                          {/* 템플릿 정보 */}
                          <div
                            className={cn(
                              "rounded-lg p-4 text-center",
                              getFormatColor(selectedTemplate.format)
                                .replace("text-", "bg-")
                                .replace("500", "50"),
                            )}
                          >
                            {(() => {
                              const I = getFormatIcon(selectedTemplate.format);
                              return (
                                <I
                                  className={cn(
                                    "mx-auto h-12 w-12",
                                    getFormatColor(selectedTemplate.format),
                                  )}
                                />
                              );
                            })()}
                          </div>
                          <div className="text-center">
                            <p className="text-sm font-semibold text-gray-900">
                              {selectedTemplate.name}
                            </p>
                            <p className="mt-1 text-xs text-gray-500">
                              {selectedTemplate.description}
                            </p>
                            <div className="mt-2 flex items-center justify-center gap-1.5">
                              <span className="inline-block rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 uppercase">
                                {selectedTemplate.format}
                              </span>
                              {(() => {
                                const badge = getRenderingModeBadge(selectedTemplate.renderingMode);
                                return (
                                  <span
                                    className={cn(
                                      "inline-block rounded border px-2 py-0.5 text-xs font-medium",
                                      badge.color,
                                    )}
                                  >
                                    {badge.label}
                                  </span>
                                );
                              })()}
                            </div>
                          </div>
                          {/* 템플릿 파일 다운로드 버튼 */}
                          <a
                            href={previewBlobUrl}
                            download={`${selectedTemplate.name}.${selectedTemplate.format}`}
                            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
                          >
                            <Download className="h-4 w-4" />
                            템플릿 다운로드
                          </a>
                          <p className="text-[10px] text-gray-400">
                            다운로드 후 Word/PowerPoint에서 확인하세요
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="flex h-64 flex-col items-center justify-center text-gray-400">
                        <Eye className="mb-2 h-8 w-8 opacity-40" />
                        <p className="text-xs">템플릿을 선택하면</p>
                        <p className="text-xs">미리보기가 표시됩니다</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 px-4 py-10 text-center">
                  <FileText className="mx-auto h-10 w-10 text-gray-300" />
                  <p className="mt-3 text-sm font-medium text-gray-600">
                    선택한 형식({outputFormat.toUpperCase()})에 맞는 템플릿이 없습니다
                  </p>
                  <p className="mt-1 text-xs text-gray-400">관리자에게 템플릿 등록을 요청하세요</p>
                </div>
              );
            })()}
          </section>

          {/* Step 3: 소스 선택 (문서 또는 채팅 세션) */}
          <section>
            <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
              {stepSource}. 소스 선택
            </h2>

            <div className="mb-4 flex items-center gap-2">
              <button
                onClick={() => setSourceMode("documents")}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  sourceMode === "documents"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-600 hover:bg-gray-50",
                )}
              >
                <FileText className="h-4 w-4" />
                문서에서
              </button>
              <button
                onClick={() => setSourceMode("chat")}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  sourceMode === "chat"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 text-gray-600 hover:bg-gray-50",
                )}
              >
                <MessageSquare className="h-4 w-4" />
                채팅 세션에서
              </button>
            </div>

            {sourceMode === "documents" ? (
              <DocumentSelector
                selectedIds={selectedDocIds}
                onChange={setSelectedDocIds}
                mode="multi"
                className="max-w-2xl"
              />
            ) : (
              <div className="max-w-2xl">
                {chatSessionsLoading ? (
                  <div className="flex items-center gap-2 py-4 text-sm text-gray-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    채팅 세션 로딩 중...
                  </div>
                ) : chatSessions.length === 0 ? (
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-8 text-center text-sm text-gray-500">
                    사용 가능한 채팅 세션이 없습니다
                  </div>
                ) : (
                  <div className="space-y-2">
                    {chatSessions.map((session) => (
                      <button
                        key={session.id}
                        onClick={() => setSelectedChatSessionId(session.id)}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-lg border-2 px-4 py-3 text-left transition-all",
                          selectedChatSessionId === session.id
                            ? "border-blue-600 bg-blue-50"
                            : "border-gray-200 bg-white hover:border-gray-300",
                        )}
                      >
                        <MessageSquare
                          className={cn(
                            "h-5 w-5 shrink-0",
                            selectedChatSessionId === session.id
                              ? "text-blue-600"
                              : "text-gray-400",
                          )}
                        />
                        <div>
                          <p className="text-sm font-medium text-gray-800">{session.title}</p>
                          <p className="text-xs text-gray-400">
                            {new Date(session.createdAt).toLocaleDateString()}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>

          {/* ── Step: Jinja2 변수 입력 (Jinja2 템플릿 전용) ──────────────── */}
          {/* Jinja2 템플릿을 선택한 경우에만 이 섹션이 나타난다 */}
          {hasJinja2Vars && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
                {stepJinja2Vars}. 템플릿 변수 입력
              </h2>

              {/* 변수 로딩 중일 때 스피너 표시 */}
              {jinja2VarsLoading ? (
                <div className="flex items-center gap-2 py-8 text-sm text-gray-400">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  변수 정보를 불러오는 중...
                </div>
              ) : (
                <div className="max-w-2xl space-y-4">
                  {/* 카테고리별 Jinja2 변수 입력 폼 */}
                  {(() => {
                    const userInputVars = jinja2Variables.filter(
                      (v) => v.category === "user_input",
                    );
                    const sessionAutoVars = jinja2Variables.filter(
                      (v) => v.category === "session_auto",
                    );
                    const aiGeneratedVars = jinja2Variables.filter(
                      (v) => v.category === "ai_generated",
                    );
                    // 카테고리 미지정 변수는 user_input으로 취급
                    const uncategorizedVars = jinja2Variables.filter((v) => !v.category);

                    // 변수 입력 필드를 렌더링하는 공통 함수
                    const renderVariableInput = (
                      variable: Jinja2Variable,
                      isSessionAuto = false,
                    ) => (
                      <div key={variable.name}>
                        <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-gray-700">
                          {variable.label || variable.name}
                          {variable.required && variable.category !== "ai_generated" && (
                            <span className="text-red-500">*</span>
                          )}
                          {isSessionAuto && (
                            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-500">
                              자동
                            </span>
                          )}
                        </label>
                        {variable.description && (
                          <p className="mb-2 text-xs text-gray-400">{variable.description}</p>
                        )}

                        {/* string 타입 */}
                        {variable.var_type === "string" && (
                          <input
                            type="text"
                            value={(jinja2Values[variable.name] as string) || ""}
                            onChange={(e) => handleJinja2ValueChange(variable.name, e.target.value)}
                            placeholder={`${variable.label || variable.name}을(를) 입력하세요`}
                            className={cn(
                              "w-full rounded-lg border px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none",
                              isSessionAuto ? "border-gray-200 bg-gray-50" : "border-gray-300",
                            )}
                          />
                        )}

                        {/* date 타입 — 팝업 달력에서 날짜 선택 */}
                        {variable.var_type === "date" && (
                          <DatePicker
                            value={(jinja2Values[variable.name] as string) || ""}
                            onChange={(val) => handleJinja2ValueChange(variable.name, val)}
                            placeholder="날짜를 선택하세요"
                            disabled={isSessionAuto}
                            className={isSessionAuto ? "border-gray-200 bg-gray-50" : ""}
                          />
                        )}

                        {/* array 타입 */}
                        {variable.var_type === "array" && (
                          <>
                            <textarea
                              value={(jinja2Values[variable.name] as string) || ""}
                              onChange={(e) =>
                                handleJinja2ValueChange(variable.name, e.target.value)
                              }
                              placeholder={`항목을 줄바꿈으로 구분하여 입력하세요\n예:\n항목 1\n항목 2\n항목 3`}
                              rows={4}
                              className={cn(
                                "w-full rounded-lg border px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none",
                                isSessionAuto ? "border-gray-200 bg-gray-50" : "border-gray-300",
                              )}
                            />
                            <p className="mt-1 text-xs text-gray-400">
                              각 항목을 줄바꿈으로 구분하세요
                            </p>
                          </>
                        )}

                        {/* boolean 타입 */}
                        {variable.var_type === "boolean" && (
                          <label className="flex cursor-pointer items-center gap-2">
                            <input
                              type="checkbox"
                              checked={Boolean(jinja2Values[variable.name])}
                              onChange={(e) =>
                                handleJinja2ValueChange(variable.name, e.target.checked)
                              }
                              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="text-sm text-gray-600">사용</span>
                          </label>
                        )}

                        {/* image 타입 */}
                        {variable.var_type === "image" && (
                          <div className="space-y-3">
                            <div className="flex items-center gap-4">
                              <label className="flex cursor-pointer items-center gap-2">
                                <input
                                  type="radio"
                                  name={`img-source-${variable.name}`}
                                  checked={imageVarSources[variable.name] === "ai"}
                                  onChange={() => handleImageVarSourceChange(variable.name, "ai")}
                                  className="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <Image className="h-4 w-4 text-blue-500" />
                                <span className="text-sm text-gray-700">AI 생성</span>
                              </label>
                              <label className="flex cursor-pointer items-center gap-2">
                                <input
                                  type="radio"
                                  name={`img-source-${variable.name}`}
                                  checked={imageVarSources[variable.name] === "unsplash"}
                                  onChange={() =>
                                    handleImageVarSourceChange(variable.name, "unsplash")
                                  }
                                  className="h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-700">Unsplash 검색</span>
                              </label>
                            </div>
                            <input
                              type="text"
                              value={(jinja2Values[variable.name] as string) || ""}
                              onChange={(e) =>
                                handleJinja2ValueChange(variable.name, e.target.value)
                              }
                              placeholder={
                                imageVarSources[variable.name] === "ai"
                                  ? "이미지를 설명하는 프롬프트를 입력하세요 (예: 현대적인 사무실 전경)"
                                  : "검색할 키워드를 입력하세요 (예: office building)"
                              }
                              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                            />
                          </div>
                        )}
                      </div>
                    );

                    return (
                      <div className="space-y-5">
                        {/* 기본 정보 (직접 입력) */}
                        {(userInputVars.length > 0 || uncategorizedVars.length > 0) && (
                          <div className="rounded-lg border border-gray-200 bg-white p-5">
                            <h3 className="mb-4 text-sm font-semibold text-gray-800">
                              기본 정보 (직접 입력)
                            </h3>
                            <div className="space-y-4">
                              {[...userInputVars, ...uncategorizedVars].map((v) =>
                                renderVariableInput(v),
                              )}
                            </div>
                          </div>
                        )}

                        {/* 자동 채움 (세션 정보) */}
                        {sessionAutoVars.length > 0 && (
                          <div className="rounded-lg border border-blue-100 bg-blue-50/30 p-5">
                            <h3 className="mb-1 text-sm font-semibold text-gray-800">
                              자동 채움 (세션 정보)
                            </h3>
                            <p className="mb-4 text-xs text-gray-400">
                              로그인 정보에서 자동으로 채워집니다. 필요 시 수정할 수 있습니다.
                            </p>
                            <div className="space-y-4">
                              {sessionAutoVars.map((v) => renderVariableInput(v, true))}
                            </div>
                          </div>
                        )}

                        {/* AI 자동 생성 항목 안내 */}
                        {aiGeneratedVars.length > 0 && (
                          <div className="rounded-lg border border-blue-100 bg-blue-50/30 p-5">
                            <h3 className="mb-2 text-sm font-semibold text-gray-800">
                              AI 자동 생성 항목
                            </h3>
                            <p className="mb-3 text-xs text-gray-500">
                              생성 버튼을 누르면 소스 문서를 기반으로 AI가 자동 작성합니다. 별도
                              입력이 필요하지 않습니다.
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {aiGeneratedVars.map((v) => (
                                <span
                                  key={v.name}
                                  className="inline-flex items-center rounded-full border border-blue-200 bg-white px-3 py-1 text-xs font-medium text-blue-800"
                                >
                                  {v.label || v.name}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}
            </section>
          )}

          {/* Step: 매개변수 입력 (Structured 템플릿 전용, 기존 로직 유지) */}
          {hasParams && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
                {stepParams}. 매개변수
              </h2>
              <div className="max-w-2xl space-y-4 rounded-lg border border-gray-200 bg-white p-5">
                {selectedTemplate!.schema.map((field) => (
                  <div key={field.name}>
                    <label className="mb-1.5 block text-sm font-medium text-gray-700">
                      {field.label}
                      {field.required && <span className="ml-1 text-red-500">*</span>}
                    </label>

                    {field.type === "text" && (
                      <input
                        type="text"
                        value={params[field.name] || ""}
                        onChange={(e) => handleParamChange(field.name, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                      />
                    )}

                    {field.type === "number" && (
                      <input
                        type="number"
                        value={params[field.name] || ""}
                        onChange={(e) => handleParamChange(field.name, e.target.value)}
                        placeholder={field.placeholder}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                      />
                    )}

                    {field.type === "date" && (
                      <DatePicker
                        value={params[field.name] || ""}
                        onChange={(val) => handleParamChange(field.name, val)}
                        placeholder="날짜를 선택하세요"
                      />
                    )}

                    {field.type === "textarea" && (
                      <textarea
                        value={params[field.name] || ""}
                        onChange={(e) => handleParamChange(field.name, e.target.value)}
                        placeholder={field.placeholder}
                        rows={3}
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                      />
                    )}

                    {field.type === "select" && (
                      <div className="relative">
                        <select
                          value={params[field.name] || ""}
                          onChange={(e) => handleParamChange(field.name, e.target.value)}
                          className="w-full appearance-none rounded-lg border border-gray-300 px-3 py-2 pr-8 text-sm text-gray-900 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
                        >
                          <option value="">선택...</option>
                          {field.options?.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                        <ChevronDown className="pointer-events-none absolute top-1/2 right-2.5 h-4 w-4 -translate-y-1/2 text-gray-400" />
                      </div>
                    )}

                    {field.type === "boolean" && (
                      <label className="flex cursor-pointer items-center gap-2">
                        <input
                          type="checkbox"
                          checked={params[field.name] === "true"}
                          onChange={(e) =>
                            handleParamChange(field.name, e.target.checked ? "true" : "false")
                          }
                          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-600">사용</span>
                      </label>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Step: AI 에이전트 선택 (에이전트가 있을 때만 표시) */}
          {hasAgents && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
                {stepAgent}. AI 에이전트 선택{" "}
                <span className="text-xs font-normal text-gray-400">(선택)</span>
              </h2>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedAgentId(null)}
                  className={cn(
                    "rounded-lg border-2 px-4 py-2.5 text-sm font-medium transition-all",
                    !selectedAgentId
                      ? "border-blue-600 bg-blue-50 text-blue-700"
                      : "border-gray-200 text-gray-600 hover:border-gray-300",
                  )}
                >
                  기본 (시스템 기본)
                </button>
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgentId(agent.id)}
                    className={cn(
                      "rounded-lg border-2 px-4 py-2.5 text-sm font-medium transition-all",
                      selectedAgentId === agent.id
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-200 text-gray-600 hover:border-gray-300",
                    )}
                    title={agent.description || ""}
                  >
                    {agent.name}
                    {agent.agent_type && (
                      <span className="ml-1 text-xs text-gray-400">
                        [
                        {{
                          report: "보고서",
                          proposal: "제안서",
                          minutes: "회의록",
                          chatbot: "챗봇",
                        }[agent.agent_type] || agent.agent_type}
                        ]
                      </span>
                    )}
                    {getProviderTag(agent.llm_provider) && (
                      <span className="ml-1 text-xs text-gray-400">
                        [{getProviderTag(agent.llm_provider)}]
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </section>
          )}

          {/* Step: AI 작성 지시사항 (추가 프롬프트 입력) */}
          <section>
            <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
              {stepPrompt}. AI 작성 지시사항{" "}
              <span className="text-xs font-normal text-gray-400">(선택)</span>
            </h2>
            <div className="max-w-2xl">
              <div className="relative rounded-lg border border-gray-200 bg-white">
                <div className="flex items-center gap-2 border-b border-gray-100 px-4 py-2">
                  <Sparkles className="h-4 w-4 text-blue-500" />
                  <span className="text-xs font-medium text-gray-500">
                    AI에게 추가 지시사항을 입력하면 더 정확한 결과를 얻을 수 있습니다
                  </span>
                </div>
                <textarea
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  placeholder={
                    documentType === "report"
                      ? "예: 핵심 성과 지표를 표와 차트로 정리하고, 각 섹션에 개선 방안을 포함해주세요."
                      : "예: 제안서의 차별성을 강조하고, 비용 대비 효과를 차트로 분석해주세요."
                  }
                  rows={4}
                  className="w-full border-0 bg-transparent px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:ring-0 focus:outline-none"
                />
              </div>
            </div>
          </section>

          {/* Step: 콘텐츠 옵션 — 차트/표/이미지 (PPTX, DOCX 형식일 때만 표시) */}
          {(outputFormat === "pptx" || outputFormat === "docx") && (
            <section>
              <h2 className="mb-3 text-sm font-semibold tracking-wider text-gray-500 uppercase">
                {stepContentOptions}. 콘텐츠 옵션
              </h2>
              <div className="max-w-2xl space-y-4 rounded-lg border border-gray-200 bg-white p-5">
                {/* 차트/표 포함 체크박스 */}
                <div className="flex flex-wrap gap-4">
                  <label className="flex cursor-pointer items-center gap-2 select-none">
                    <input
                      type="checkbox"
                      checked={includeCharts}
                      onChange={(e) => setIncludeCharts(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">차트 포함</span>
                  </label>
                  <label className="flex cursor-pointer items-center gap-2 select-none">
                    <input
                      type="checkbox"
                      checked={includeTables}
                      onChange={(e) => setIncludeTables(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">표 포함</span>
                  </label>
                </div>

                {/* 이미지 생성 방식 라디오 (기존 체크박스 대신) */}
                <div>
                  <p className="mb-2 text-sm font-medium text-gray-700">이미지 생성 방식</p>
                  <div className="space-y-2">
                    {IMAGE_PROVIDERS.map((provider) => (
                      <label
                        key={provider.value}
                        className={cn(
                          "flex cursor-pointer items-start gap-3 rounded-lg border-2 p-3 transition-all",
                          imageProvider === provider.value
                            ? "border-blue-600 bg-blue-50"
                            : "border-gray-200 bg-white hover:border-gray-300",
                        )}
                      >
                        <input
                          type="radio"
                          name="image-provider"
                          checked={imageProvider === provider.value}
                          onChange={() => setImageProvider(provider.value)}
                          className="mt-0.5 h-4 w-4 border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div>
                          <span
                            className={cn(
                              "text-sm font-medium",
                              imageProvider === provider.value ? "text-blue-900" : "text-gray-700",
                            )}
                          >
                            {provider.label}
                          </span>
                          <p className="text-xs text-gray-400">{provider.description}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* 생성 버튼 */}
          <section>
            {generating && (
              <div className="mb-4 max-w-2xl">
                <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
                  <span>{documentType === "report" ? "보고서" : "제안서"} 생성 중...</span>
                  <span>{generateProgress}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-full rounded-full bg-blue-600 transition-all duration-500"
                    style={{ width: `${generateProgress}%` }}
                  />
                </div>
              </div>
            )}
            <button
              onClick={handleGenerate}
              disabled={generating || !selectedTemplateId}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  생성 중...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  {documentType === "report" ? "보고서 생성" : "제안서 생성"}
                </>
              )}
            </button>
          </section>
        </div>
      )}

      {/* ── 내 보고서 탭 ────────────────────────────────────────────── */}
      {activeTab === "my-reports" && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm text-gray-500">{reports.length}개 문서</p>
            <button
              onClick={loadReports}
              disabled={reportsLoading}
              className="flex items-center gap-1.5 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition-colors hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", reportsLoading && "animate-spin")} />
              새로고침
            </button>
          </div>

          {reportsLoading && reports.length === 0 ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : reports.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg border border-gray-200 bg-white py-20">
              <FileText className="h-12 w-12 text-gray-200" />
              <p className="mt-4 text-sm font-medium text-gray-500">아직 생성된 문서가 없습니다</p>
              <p className="mt-1 text-xs text-gray-400">생성 탭에서 보고서나 제안서를 생성하세요</p>
              <button
                onClick={() => setActiveTab("generate")}
                className="mt-4 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                <Plus className="h-4 w-4" />
                새로 생성
              </button>
            </div>
          ) : (
            <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left font-medium text-gray-600">제목</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">템플릿</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">상태</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">형식</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-600">생성일</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-600">작업</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {reports.map((report) => {
                    const statusBadge = getStatusBadge(report.status);
                    const StatusIcon = statusBadge.icon;
                    const FormatIcon = getFormatIcon(report.format);
                    const formatColor = getFormatColor(report.format);

                    return (
                      <tr key={report.id} className="transition-colors hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <span className="font-medium text-gray-900">{report.title}</span>
                        </td>
                        <td className="px-4 py-3 text-gray-600">{report.templateName}</td>
                        <td className="px-4 py-3">
                          <span
                            className={cn(
                              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
                              statusBadge.color,
                            )}
                          >
                            <StatusIcon
                              className={cn(
                                "h-3 w-3",
                                "spin" in statusBadge && statusBadge.spin && "animate-spin",
                              )}
                            />
                            {statusBadge.label}
                          </span>
                          {report.status === "error" && report.errorMessage && (
                            <p className="mt-1 text-[10px] text-red-500">{report.errorMessage}</p>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className="flex items-center gap-1.5">
                            <FormatIcon className={cn("h-4 w-4", formatColor)} />
                            <span className="text-gray-600 uppercase">{report.format}</span>
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-500">
                          {new Date(report.generatedAt).toLocaleString()}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            {report.status === "completed" && (
                              <button
                                onClick={() => handleDownload(report)}
                                className="rounded-lg p-2 text-blue-600 transition-colors hover:bg-blue-50"
                                aria-label="다운로드"
                              >
                                <Download className="h-4 w-4" />
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteReport(report.id)}
                              className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500"
                              aria-label="삭제"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
