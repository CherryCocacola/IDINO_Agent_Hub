"use client";

import { format } from "date-fns";
import {
  Plus,
  Pencil,
  Trash2,
  Loader2,
  FileText,
  CheckCircle2,
  XCircle,
  X,
  Upload,
  Sparkles,
  File,
  HardDrive,
  Image,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  TableProperties,
  Check,
  Settings2,
  RefreshCw,
} from "lucide-react";
import { useState, useEffect, useCallback, useRef } from "react";

import VariableMappingEditor from "@/components/templates/variable-mapping-editor";
import { apiClient } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";
import { cn } from "@/lib/utils/cn";

// ---------- Types ----------

/** 업로드 후 서버에서 반환하는 변수 정보 */
interface TemplateVariable {
  name: string;
  type: string;
  label: string;
  required: boolean;
}

/** 렌더링 모드: Jinja2 / Structured(AI) / regex(단순 치환) */
type RenderingMode = "jinja2" | "structured" | "regex";

/** 이미지 AI 설정 */
type ImageSource = "dalle3" | "unsplash";

/** 서버에서 가져오는 템플릿 데이터 */
interface Template {
  id: string;
  name: string;
  description: string | null;
  template_type: string; // 자유 텍스트로 변경
  tone: "formal" | "casual" | "business" | "academic";
  output_format: string;
  rendering_mode: RenderingMode | null;
  // BE 는 image_generation_config: {provider, enabled} 형태의 JSONB 로 저장한다.
  // FE 의 image_source 단일 문자열은 이 중 provider 값에 해당하며,
  // 편집 시 image_generation_config?.provider 에서 복원한다.
  image_generation_config: { provider?: ImageSource; enabled?: boolean } | null;
  template_storage_path: string | null;
  schema: Record<string, any> | null;
  sample_prompt: string | null;
  is_active: boolean;
  variables: TemplateVariable[] | null;
  created_at: string;
  updated_at: string;
}

/** 생성/수정 폼 데이터 */
interface TemplateFormData {
  name: string;
  description: string;
  template_type: string; // 자유 텍스트
  tone: "formal" | "casual" | "business" | "academic";
  output_format: string;
  rendering_mode: RenderingMode;
  image_source: ImageSource;
  schema: string;
  sample_prompt: string;
  is_active: boolean;
}

/** 스마트 업로드 응답 — 파일을 분석하여 렌더링 모드/변수를 자동 판별 */
interface SmartUploadResponse {
  id: string; // 서버에서 생성된 템플릿 ID
  name: string; // 파일명 기반 자동 이름
  output_format: string; // 감지된 출력 형식 (docx, pptx 등)
  rendering_mode: string; // 자동 판별된 렌더링 모드
  variables: TemplateVariable[]; // 추출된 변수 목록
  template_type?: string; // 추측된 유형 (보고서, 제안서 등)
}

const EMPTY_FORM: TemplateFormData = {
  name: "",
  description: "",
  template_type: "",
  tone: "formal",
  output_format: "docx",
  rendering_mode: "jinja2",
  image_source: "dalle3",
  schema: "",
  sample_prompt: "",
  is_active: true,
};

/** 필터 탭 — 이제 자유 텍스트이므로 전체만 기본 유지, 동적 필터는 input으로 */
type TypeFilter = "all" | string;

const TONE_LABELS: Record<string, string> = {
  formal: "격식체",
  casual: "비격식체",
  business: "비즈니스",
  academic: "학술",
};

const TONE_OPTIONS: { value: TemplateFormData["tone"]; label: string }[] = [
  { value: "formal", label: "격식체" },
  { value: "casual", label: "비격식체" },
  { value: "business", label: "비즈니스" },
  { value: "academic", label: "학술" },
];

/** 렌더링 모드 라벨 */
const RENDERING_MODE_LABELS: Record<RenderingMode, string> = {
  jinja2: "Jinja2 템플릿",
  structured: "Structured (AI 자유형)",
  regex: "단순 치환 (레거시)",
};

/** 렌더링 모드 뱃지 색상 */
const RENDERING_MODE_BADGE: Record<RenderingMode, string> = {
  jinja2: "bg-blue-50 text-blue-700",
  structured: "bg-blue-50 text-blue-800",
  regex: "bg-gray-100 text-gray-600",
};

/** (레거시 — 수정 모드 호환용) */

// ---------- 파일 크기를 사람이 읽기 좋은 형식으로 변환 ----------
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ---------- Component ----------

export default function TemplatesPage() {
  const { addToast } = useToast();

  // 사용 가이드 패널 (기본 접힌 상태)
  const [guideOpen, setGuideOpen] = useState(false);

  // 목록 데이터
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, _setTypeFilter] = useState<TypeFilter>("all");
  const [typeFilterInput, setTypeFilterInput] = useState(""); // 유형 검색 필터

  // 생성/수정 다이얼로그
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<TemplateFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  // ---------- 파일 업로드 관련 상태 (생성 다이얼로그에서만 사용) ----------

  // 기존 호환용 (수정 모드에서 사용)
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedVariables, setUploadedVariables] = useState<TemplateVariable[]>([]);
  const [uploadedTemplateId, setUploadedTemplateId] = useState<string | null>(null);
  // 4단계 생성 플로우 전용 상태
  const [uploadStep, setUploadStep] = useState<1 | 2 | 3 | 4>(1); // 현재 단계 (1=파일업로드, 2=기본정보, 3=변수매핑, 4=저장)
  const [smartUploadResult, setSmartUploadResult] = useState<SmartUploadResponse | null>(null); // 스마트 업로드 결과
  const [advancedOpen, setAdvancedOpen] = useState(false); // 고급 설정 접이식 상태
  const [_variableMappingDirty, setVariableMappingDirty] = useState(false); // 변수 매핑이 수정되었는지 여부
  const smartFileInputRef = useRef<HTMLInputElement>(null); // 스마트 업로드 파일 input 참조
  const [isDragOver, setIsDragOver] = useState(false); // 드래그 오버 시각 피드백

  // ---------- 수정 모드 전용 상태 ----------
  /** 수정 모드에서 "파일 교체" 버튼 클릭 시 사용하는 숨겨진 파일 input */
  const editFileInputRef = useRef<HTMLInputElement>(null);
  /** 수정 모드 파일 교체 진행 중 여부 */
  const [editFileUploading, setEditFileUploading] = useState(false);
  /** 수정 모드 고급 설정 접이식 열림 여부 */
  const [editAdvancedOpen, setEditAdvancedOpen] = useState(false);
  /** 수정 모드에서 변수 매핑 에디터를 다이얼로그로 열 때 사용 */
  const [editMappingOpen, setEditMappingOpen] = useState(false);
  /** 수정 중인 템플릿의 원본 데이터 (파일 정보, 렌더링 모드 등 표시용) */
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);

  // 삭제 확인 다이얼로그
  const [deleteTarget, setDeleteTarget] = useState<Template | null>(null);

  // 변수 매핑 에디터 상태
  const [mappingEditorOpen, setMappingEditorOpen] = useState(false);
  const [mappingTemplateId, setMappingTemplateId] = useState<string>("");
  const [mappingTemplateName, setMappingTemplateName] = useState<string>("");

  // ---------- Fetch ----------

  const fetchTemplates = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      if (typeFilter !== "all") params.template_type = typeFilter;
      const response = await apiClient.get<{ items: Template[]; total: number }>(
        "/templates",
        params,
      );
      setTemplates(response.items || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "템플릿을 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, typeFilter]);

  useEffect(() => {
    setLoading(true);
    fetchTemplates();
  }, [fetchTemplates]);

  // ---------- Create / Edit ----------

  /** 생성 다이얼로그 열기 — 모든 생성 관련 상태를 초기화 */
  const openCreate = () => {
    setEditingId(null);
    setFormData(EMPTY_FORM);
    setUploadFile(null);
    setUploadedVariables([]);
    setUploadedTemplateId(null);
    // 4단계 플로우 상태 초기화
    setUploadStep(1);
    setSmartUploadResult(null);
    setAdvancedOpen(false);
    setVariableMappingDirty(false);
    setIsDragOver(false);
    setDialogOpen(true);
  };

  /** 수정 다이얼로그 열기 — 기존 데이터를 폼에 채우고 수정 모드 상태 초기화 */
  const openEdit = (tpl: Template) => {
    setEditingId(tpl.id);
    setEditingTemplate(tpl); // 원본 템플릿 데이터 보관 (파일 정보 표시용)
    setFormData({
      name: tpl.name,
      description: tpl.description || "",
      template_type: tpl.template_type,
      tone: tpl.tone,
      output_format: tpl.output_format,
      rendering_mode: tpl.rendering_mode || "jinja2",
      // image_generation_config.provider 에서 복원. null 이면 기본값 "dalle3"
      image_source: tpl.image_generation_config?.provider || "dalle3",
      schema: tpl.schema ? JSON.stringify(tpl.schema, null, 2) : "",
      sample_prompt: tpl.sample_prompt || "",
      is_active: tpl.is_active,
    });
    // 수정 모드에서는 기존 변수를 읽기 전용으로 표시
    setUploadedVariables(tpl.variables || []);
    setUploadFile(null);
    setUploadedTemplateId(null);
    // 수정 모드 전용 상태 초기화
    setEditAdvancedOpen(false);
    setEditMappingOpen(false);
    setEditFileUploading(false);
    setDialogOpen(true);
  };

  /** 수정 모드 저장 — editingId가 있을 때 기존 템플릿의 메타데이터를 PUT으로 업데이트 */
  const handleSave = async () => {
    if (!formData.name.trim()) {
      addToast("이름은 필수입니다", "error");
      return;
    }

    let parsedSchema: Record<string, any> | null = null;
    if (formData.schema.trim()) {
      try {
        parsedSchema = JSON.parse(formData.schema);
      } catch {
        addToast("폼 스키마가 올바른 JSON 형식이 아닙니다", "error");
        return;
      }
    }

    const body = {
      name: formData.name,
      description: formData.description || null,
      template_type: formData.template_type,
      tone: formData.tone,
      output_format: formData.output_format,
      rendering_mode: formData.rendering_mode,
      // BE schema 는 image_generation_config: dict | None 만 받는다. image_source 문자열로
      // 보내면 Pydantic extra='ignore' 로 무시되어 DALL-E/Unsplash 가 활성화되지 않는다.
      image_generation_config: formData.image_source
        ? { provider: formData.image_source, enabled: true }
        : null,
      schema: parsedSchema,
      sample_prompt: formData.sample_prompt || null,
      is_active: formData.is_active,
      variables: uploadedVariables.length > 0 ? uploadedVariables : undefined,
    };

    setSaving(true);
    try {
      if (editingId) {
        await apiClient.put(`/templates/${editingId}`, body);
        addToast("템플릿이 수정되었습니다", "success");
      } else if (uploadedTemplateId) {
        await apiClient.put(`/templates/${uploadedTemplateId}`, body);
        addToast("템플릿이 수정되었습니다", "success");
      } else {
        await apiClient.post("/templates", body);
        addToast("템플릿이 추가되었습니다", "success");
      }
      setDialogOpen(false);
      fetchTemplates();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "템플릿 저장에 실패했습니다", "error");
    } finally {
      setSaving(false);
    }
  };

  // ---------- File Upload ----------

  /**
   * 스마트 업로드 — 파일 하나만으로 서버가 자동으로 모든 것을 판별
   *
   * 흐름:
   * 1. 사용자가 파일을 선택(드래그앤드롭 또는 클릭)
   * 2. 즉시 POST /templates/upload-smart 호출
   * 3. 서버 응답(id, name, rendering_mode, variables 등)을 받아서 다음 단계로 진행
   */
  const handleSmartUpload = async (file: File) => {
    // 확장자 검증
    const allowedExtensions = [".docx", ".pptx"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      addToast("DOCX 또는 PPTX 파일만 업로드할 수 있습니다", "error");
      return;
    }

    // 업로드 시작
    setUploadFile(file);
    setUploading(true);

    try {
      // FormData에 파일만 담아서 전송 (이름/유형 등은 Step 2에서 입력)
      const fd = new FormData();
      fd.append("file", file);

      const result = await apiClient.upload<SmartUploadResponse>("/templates/upload-smart", fd);

      // 서버 응답을 상태에 저장
      setSmartUploadResult(result);
      setUploadedTemplateId(result.id);
      setUploadedVariables(result.variables || []);

      // 파일명에서 확장자 제거하여 기본 이름으로 설정
      const baseName = file.name.replace(/\.[^/.]+$/, "");
      setFormData((prev) => ({
        ...prev,
        name: result.name || baseName,
        output_format: result.output_format || prev.output_format,
        rendering_mode: (result.rendering_mode as RenderingMode) || prev.rendering_mode,
        template_type: result.template_type || prev.template_type,
      }));

      addToast("파일 분석이 완료되었습니다. 기본 정보를 확인해주세요.", "success");

      // Step 2(기본 정보)로 자동 이동
      setUploadStep(2);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "파일 업로드에 실패했습니다", "error");
    } finally {
      setUploading(false);
    }
  };

  /**
   * Step 4: 최종 저장 — 스마트 업로드로 생성된 템플릿의 메타데이터를 업데이트
   *
   * upload-smart에서 이미 템플릿이 생성되어 있으므로,
   * PUT으로 이름/유형/말투/설명 등 메타데이터만 갱신합니다.
   * 변수 매핑을 수정했으면 apply-mapping도 추가 호출합니다.
   */
  const handleStepSave = async () => {
    // 이름 필수 검증
    if (!formData.name.trim()) {
      addToast("이름은 필수입니다", "error");
      return;
    }

    // 스마트 업로드 결과가 없으면 저장 불가
    if (!smartUploadResult || !uploadedTemplateId) {
      addToast("먼저 파일을 업로드해주세요", "error");
      return;
    }

    setSaving(true);
    try {
      // 메타데이터 업데이트 (PUT /templates/{id})
      const body = {
        name: formData.name,
        description: formData.description || null,
        template_type: formData.template_type,
        tone: formData.tone,
        output_format: formData.output_format,
        rendering_mode: formData.rendering_mode,
        // BE 가 기대하는 image_generation_config 스키마로 매핑 (image_source 는 무시됨)
        image_generation_config: formData.image_source
          ? { provider: formData.image_source, enabled: true }
          : null,
        sample_prompt: formData.sample_prompt || null,
        is_active: formData.is_active,
      };
      await apiClient.put(`/templates/${uploadedTemplateId}`, body);

      addToast("템플릿이 저장되었습니다", "success");
      setDialogOpen(false);
      fetchTemplates();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "템플릿 저장에 실패했습니다", "error");
    } finally {
      setSaving(false);
    }
  };

  /**
   * 수정 모드: 파일 교체 — 기존 템플릿의 파일을 새 파일로 교체
   *
   * upload-smart를 호출하면 기존 이름과 동일한 이름으로 upsert되므로,
   * 기존 템플릿 ID에 새 파일이 연결됩니다.
   * 교체 후 변수 목록도 새 파일 기준으로 갱신됩니다.
   */
  const handleReplaceFile = async (file: File) => {
    // 허용 확장자 검증
    const allowedExtensions = [".docx", ".pptx"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      addToast("DOCX 또는 PPTX 파일만 업로드할 수 있습니다", "error");
      return;
    }

    setEditFileUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      // 기존 템플릿 이름을 함께 전송하여 upsert 처리
      fd.append("name", formData.name);

      const result = await apiClient.upload<SmartUploadResponse>("/templates/upload-smart", fd);

      // 새 파일에서 추출된 변수로 갱신
      setUploadedVariables(result.variables || []);
      // 출력형식과 렌더링 모드도 새 파일 기준으로 갱신
      setFormData((prev) => ({
        ...prev,
        output_format: result.output_format || prev.output_format,
        rendering_mode: (result.rendering_mode as RenderingMode) || prev.rendering_mode,
      }));

      addToast("파일이 교체되었습니다", "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "파일 교체에 실패했습니다", "error");
    } finally {
      setEditFileUploading(false);
    }
  };

  /** 변수 테이블에서 인라인 편집 */
  const _updateVariable = (
    index: number,
    field: keyof TemplateVariable,
    value: string | boolean,
  ) => {
    setUploadedVariables((prev) =>
      prev.map((v, i) => (i === index ? { ...v, [field]: value } : v)),
    );
  };

  // ---------- Delete ----------

  const handleDelete = async () => {
    if (!deleteTarget) return;
    const targetId = deleteTarget.id;
    // 다이얼로그를 먼저 닫아 UI 응답성 확보
    setDeleteTarget(null);
    try {
      await apiClient.delete(`/templates/${targetId}`);
      addToast("템플릿이 삭제되었습니다", "success");
      // 삭제 완료 후 목록에서 즉시 제거 (서버 응답 기다리지 않고 UI 반영)
      setTemplates((prev) => prev.filter((t) => t.id !== targetId));
      // 서버에서 최신 목록도 다시 가져온다
      await fetchTemplates();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "템플릿 삭제에 실패했습니다", "error");
      // 실패 시 목록 복원
      await fetchTemplates();
    }
  };

  // ---------- Filtered data ----------
  // 유형 검색 input이 있으면 해당 문자열로 필터링
  const filteredTemplates = typeFilterInput.trim()
    ? templates.filter((t) => t.template_type.toLowerCase().includes(typeFilterInput.toLowerCase()))
    : templates;

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      {/* 상단 헤더: 타이틀 + 추가 버튼 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">템플릿 관리</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            보고서, 제안서, 회의록 등 다양한 템플릿을 관리합니다
          </p>
        </div>
        <button
          onClick={openCreate}
          className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          템플릿 추가
        </button>
      </div>

      {/* Jinja2 템플릿 사용 가이드 (접이식) */}
      <div className="border-border rounded-lg border bg-white">
        <button
          type="button"
          onClick={() => setGuideOpen((prev) => !prev)}
          className="hover:bg-muted/30 flex w-full items-center justify-between px-4 py-3 text-left transition-colors"
          aria-expanded={guideOpen}
        >
          <span className="text-foreground inline-flex items-center gap-2 text-sm font-semibold">
            <HelpCircle className="text-primary h-4 w-4" />
            Jinja2 템플릿 사용 가이드
          </span>
          {guideOpen ? (
            <ChevronUp className="text-muted-foreground h-4 w-4" />
          ) : (
            <ChevronDown className="text-muted-foreground h-4 w-4" />
          )}
        </button>

        {guideOpen && (
          <div className="border-border text-foreground space-y-4 border-t px-4 pt-3 pb-4 text-sm">
            {/* 기본 변수 삽입 */}
            <div>
              <h3 className="mb-1 text-sm font-semibold">기본 변수 삽입</h3>
              <p className="text-muted-foreground mb-2">
                Word/PowerPoint 문서에 아래와 같이 입력하세요:
              </p>
              <pre className="rounded bg-gray-50 p-3 font-mono text-sm leading-relaxed whitespace-pre dark:bg-gray-800">
                {`{{ 제목 }}      → 텍스트 변수
{{ 작성자 }}    → 텍스트 변수
{{ 작성일 }}    → 날짜 변수`}
              </pre>
            </div>

            {/* 반복 (목록/표 행) */}
            <div>
              <h3 className="mb-1 text-sm font-semibold">반복 (목록/표 행)</h3>
              <pre className="rounded bg-gray-50 p-3 font-mono text-sm leading-relaxed whitespace-pre dark:bg-gray-800">
                {`{% for item in 항목 %}
  - {{ item.이름 }}: {{ item.설명 }}
{% endfor %}`}
              </pre>
            </div>

            {/* 조건부 표시 */}
            <div>
              <h3 className="mb-1 text-sm font-semibold">조건부 표시</h3>
              <pre className="rounded bg-gray-50 p-3 font-mono text-sm leading-relaxed whitespace-pre dark:bg-gray-800">
                {`{% if 승인여부 %}
  승인됨: {{ 승인자 }}
{% else %}
  미승인
{% endif %}`}
              </pre>
            </div>

            {/* 이미지 삽입 */}
            <div>
              <h3 className="mb-1 text-sm font-semibold">이미지 삽입</h3>
              <pre className="rounded bg-gray-50 p-3 font-mono text-sm leading-relaxed whitespace-pre dark:bg-gray-800">
                {`{{ 대표이미지 }}
→ 변수 타입을 'image'로 설정하면
  AI가 DALL-E로 자동 생성합니다`}
              </pre>
            </div>

            {/* 빈 양식 자동 변환 */}
            <div>
              <h3 className="mb-1 text-sm font-semibold">빈 양식 자동 변환</h3>
              <p className="text-muted-foreground mb-2">
                제목/항목만 있는 빈 문서를 업로드하면 AI가 자동으로 구조를 파악합니다.
              </p>
              <pre className="rounded bg-gray-50 p-3 font-mono text-sm leading-relaxed whitespace-pre dark:bg-gray-800">
                {`1. 사업 개요
   (빈칸 -> AI가 자동 감지)
2. 추진 전략
   (빈칸 -> AI가 자동 감지)`}
              </pre>
            </div>

            {/* 사용 팁 */}
            <div>
              <h3 className="mb-1 inline-flex items-center gap-1.5 text-sm font-semibold">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                사용 팁
              </h3>
              <ul className="text-muted-foreground mt-1 list-disc space-y-1 pl-5">
                <li>Word/PowerPoint에서 직접 위 문법을 입력 후 업로드하세요</li>
                <li>
                  또는 기존 완성 문서를 &quot;예제 → AI 변환&quot;으로 업로드하면 자동 변환됩니다
                </li>
                <li>
                  빈 양식(제목만 있는 문서)은 &quot;빈 양식 → 자동 변환&quot;으로 업로드하면 AI가
                  구조를 파악하여 변수를 추출합니다
                </li>
                <li>샘플 템플릿을 다운로드하여 참고할 수 있습니다</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* 유형 필터: 자유 텍스트 검색으로 변경 */}
      <div className="flex items-center gap-3">
        <input
          type="text"
          value={typeFilterInput}
          onChange={(e) => setTypeFilterInput(e.target.value)}
          placeholder="유형으로 검색 (예: 보고서, 제안서, 회의록 ...)"
          className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full max-w-sm rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
        />
        {typeFilterInput && (
          <button
            onClick={() => setTypeFilterInput("")}
            className="text-muted-foreground hover:text-foreground text-sm"
          >
            초기화
          </button>
        )}
      </div>

      {/* 목록 테이블 */}
      <div className="border-border overflow-hidden rounded-lg border bg-white">
        {loading ? (
          /* 로딩 스켈레톤 */
          <div className="space-y-3 p-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-muted h-12 w-full animate-pulse rounded" />
            ))}
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-border bg-muted/50 border-b">
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">이름</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">유형</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">렌더링</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">말투</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">출력형식</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">파일</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">상태</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">생성일</th>
                <th className="text-muted-foreground w-28 px-4 py-3 text-left font-medium">작업</th>
              </tr>
            </thead>
            <tbody>
              {filteredTemplates.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-muted-foreground py-12 text-center">
                    <FileText className="mx-auto mb-2 h-8 w-8 opacity-40" />
                    등록된 템플릿이 없습니다. 새로 추가해주세요.
                  </td>
                </tr>
              ) : (
                filteredTemplates.map((tpl) => (
                  <tr
                    key={tpl.id}
                    className="border-border hover:bg-muted/30 border-b transition-colors last:border-b-0"
                  >
                    {/* 이름 + 설명 */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="text-muted-foreground h-4 w-4" />
                        <span className="text-foreground font-medium">{tpl.name}</span>
                      </div>
                      {tpl.description && (
                        <p className="text-muted-foreground mt-0.5 line-clamp-1 text-xs">
                          {tpl.description}
                        </p>
                      )}
                    </td>

                    {/* 유형 — 자유 텍스트이므로 그대로 표시 */}
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                        {tpl.template_type}
                      </span>
                    </td>

                    {/* 렌더링 모드 뱃지 */}
                    <td className="px-4 py-3">
                      {tpl.rendering_mode ? (
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                            RENDERING_MODE_BADGE[tpl.rendering_mode] || "bg-gray-100 text-gray-600",
                          )}
                        >
                          {RENDERING_MODE_LABELS[tpl.rendering_mode] || tpl.rendering_mode}
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-xs">-</span>
                      )}
                    </td>

                    {/* 말투 */}
                    <td className="text-muted-foreground px-4 py-3">{TONE_LABELS[tpl.tone]}</td>

                    {/* 출력형식 */}
                    <td className="px-4 py-3">
                      <span className="bg-muted rounded px-2 py-0.5 font-mono text-xs uppercase">
                        {tpl.output_format}
                      </span>
                    </td>

                    {/* 파일 유무: template_storage_path가 있으면 파일 아이콘 표시 */}
                    <td className="px-4 py-3">
                      {tpl.template_storage_path ? (
                        <span title="파일 있음">
                          <HardDrive className="h-4 w-4 text-green-600" />
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-xs">-</span>
                      )}
                    </td>

                    {/* 상태 */}
                    <td className="px-4 py-3">
                      {tpl.is_active ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-600">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          활성
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-400">
                          <XCircle className="h-3.5 w-3.5" />
                          비활성
                        </span>
                      )}
                    </td>

                    {/* 생성일 */}
                    <td className="text-muted-foreground px-4 py-3">
                      {format(new Date(tpl.created_at), "yyyy-MM-dd")}
                    </td>

                    {/* 작업 버튼 */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        {/* 변수 매핑 에디터 — jinja2 + docx 템플릿에만 표시 */}
                        {tpl.rendering_mode === "jinja2" && tpl.output_format === "docx" && (
                          <button
                            onClick={() => {
                              setMappingTemplateId(tpl.id);
                              setMappingTemplateName(tpl.name);
                              setMappingEditorOpen(true);
                            }}
                            className="rounded-md p-1.5 text-blue-600 transition-colors hover:bg-blue-50 hover:text-blue-800"
                          >
                            <span title="변수 매핑 에디터">
                              <TableProperties className="h-4 w-4" />
                            </span>
                          </button>
                        )}
                        <button
                          onClick={() => openEdit(tpl)}
                          className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-1.5 transition-colors"
                          title="수정"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(tpl)}
                          className="text-muted-foreground rounded-md p-1.5 transition-colors hover:bg-red-50 hover:text-red-600"
                          title="삭제"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* ======== 생성 / 수정 다이얼로그 ======== */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* 배경 오버레이 — 클릭하면 다이얼로그 닫힘 */}
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setDialogOpen(false)}
            aria-hidden="true"
          />

          {/* ---------- 수정 모드: 리디자인된 직관적 폼 ---------- */}
          {editingId ? (
            <div className="border-border relative z-50 w-full max-w-2xl rounded-lg border bg-white shadow-xl">
              {/* ── 수정 모드 헤더: 템플릿 이름 + 닫기 버튼 ── */}
              <div className="border-border flex items-center justify-between border-b px-6 py-4">
                <div className="min-w-0 flex-1">
                  <h2 className="text-foreground truncate text-lg font-semibold">
                    {editingTemplate?.name || "템플릿"} 수정
                  </h2>
                  <p className="text-muted-foreground mt-0.5 text-sm">
                    기본 정보, 파일, 변수를 수정할 수 있습니다
                  </p>
                </div>
                <button
                  onClick={() => setDialogOpen(false)}
                  className="text-muted-foreground hover:bg-muted hover:text-foreground shrink-0 rounded-md p-1.5 transition-colors"
                  aria-label="닫기"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* ── 수정 모드 본문 (스크롤 가능) ── */}
              <div className="max-h-[70vh] space-y-6 overflow-y-auto px-6 py-5">
                {/* ━━━━ 섹션 1: 기본 정보 ━━━━ */}
                <section>
                  <h3 className="text-foreground mb-3 flex items-center gap-2 text-sm font-semibold">
                    <FileText className="text-primary h-4 w-4" />
                    기본 정보
                  </h3>

                  <div className="space-y-4">
                    {/* 이름 + 유형 (2열 배치) */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* 이름: 필수 입력 필드 */}
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">
                          이름 <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) =>
                            setFormData((prev) => ({ ...prev, name: e.target.value }))
                          }
                          placeholder="템플릿 이름을 입력하세요"
                          className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                        />
                      </div>
                      {/* 유형: 자유 텍스트 입력 (보고서, 제안서, 회의록 등) */}
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">유형</label>
                        <input
                          type="text"
                          value={formData.template_type}
                          onChange={(e) =>
                            setFormData((prev) => ({ ...prev, template_type: e.target.value }))
                          }
                          placeholder="보고서, 제안서, 회의록 등"
                          list="edit-type-suggestions"
                          className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                        />
                        {/* 유형 자동완성 제안 목록 */}
                        <datalist id="edit-type-suggestions">
                          <option value="회의록" />
                          <option value="보고서" />
                          <option value="제안서" />
                          <option value="기획서" />
                          <option value="기타" />
                        </datalist>
                      </div>
                    </div>

                    {/* 말투 + 활성 상태 (2열 배치) */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* 말투: 드롭다운으로 선택 (격식체, 비격식체 등) */}
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">말투</label>
                        <select
                          value={formData.tone}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              tone: e.target.value as TemplateFormData["tone"],
                            }))
                          }
                          className="border-border text-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                        >
                          {TONE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      {/* 활성 여부: 체크박스로 토글 */}
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">상태</label>
                        <div className="border-border flex items-center gap-2.5 rounded-md border bg-white px-3 py-2">
                          <input
                            type="checkbox"
                            id="edit-active-toggle"
                            checked={formData.is_active}
                            onChange={(e) =>
                              setFormData((prev) => ({ ...prev, is_active: e.target.checked }))
                            }
                            className="border-border text-primary focus:ring-primary h-4 w-4 rounded"
                          />
                          <label
                            htmlFor="edit-active-toggle"
                            className="text-foreground cursor-pointer text-sm select-none"
                          >
                            {formData.is_active ? "활성" : "비활성"}
                          </label>
                        </div>
                      </div>
                    </div>

                    {/* 설명: 선택 입력 */}
                    <div className="space-y-1.5">
                      <label className="text-foreground text-sm font-medium">
                        설명 <span className="text-muted-foreground text-xs">(선택)</span>
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) =>
                          setFormData((prev) => ({ ...prev, description: e.target.value }))
                        }
                        placeholder="이 템플릿에 대한 설명을 입력하세요"
                        rows={2}
                        className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full resize-none rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                      />
                    </div>
                  </div>
                </section>

                {/* ━━━━ 섹션 2: 파일 관리 ━━━━ */}
                <section>
                  <h3 className="text-foreground mb-3 flex items-center gap-2 text-sm font-semibold">
                    <HardDrive className="text-primary h-4 w-4" />
                    파일 관리
                  </h3>

                  <div className="border-border bg-muted/20 space-y-3 rounded-lg border p-4">
                    {/* 현재 파일 정보 표시 */}
                    <div className="flex items-center gap-3">
                      {/* 파일 아이콘: 파일 유무에 따라 색상 변경 */}
                      <div
                        className={cn(
                          "flex h-10 w-10 shrink-0 items-center justify-center rounded-lg",
                          editingTemplate?.template_storage_path
                            ? "bg-green-100 text-green-600"
                            : "bg-gray-100 text-gray-400",
                        )}
                      >
                        <File className="h-5 w-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        {editingTemplate?.template_storage_path ? (
                          <>
                            {/* 파일이 있는 경우: 파일 경로에서 이름 추출하여 표시 */}
                            <p className="text-foreground truncate text-sm font-medium">
                              {editingTemplate.template_storage_path.split("/").pop() ||
                                "업로드된 파일"}
                            </p>
                            <p className="text-muted-foreground text-xs">
                              {/* 출력형식과 렌더링 모드를 간략히 표시 */}
                              {formData.output_format.toUpperCase()} 형식
                              {formData.rendering_mode && (
                                <> / {RENDERING_MODE_LABELS[formData.rendering_mode]}</>
                              )}
                            </p>
                          </>
                        ) : (
                          <>
                            {/* 파일이 없는 경우: 안내 메시지 */}
                            <p className="text-muted-foreground text-sm">연결된 파일이 없습니다</p>
                            <p className="text-muted-foreground text-xs">
                              파일을 업로드하면 변수가 자동으로 추출됩니다
                            </p>
                          </>
                        )}
                      </div>
                    </div>

                    {/* 파일 교체 + 변수 매핑 에디터 버튼 */}
                    <div className="flex items-center gap-2">
                      {/* 숨겨진 파일 입력 — "파일 교체" 버튼 클릭 시 활성화 */}
                      <input
                        ref={editFileInputRef}
                        type="file"
                        accept=".docx,.pptx"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleReplaceFile(file);
                          // 같은 파일을 다시 선택할 수 있도록 값 초기화
                          e.target.value = "";
                        }}
                      />
                      {/* 파일 교체 버튼 */}
                      <button
                        type="button"
                        onClick={() => editFileInputRef.current?.click()}
                        disabled={editFileUploading}
                        className="border-border text-foreground hover:bg-muted inline-flex items-center gap-1.5 rounded-md border bg-white px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50"
                      >
                        {editFileUploading ? (
                          <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                          <RefreshCw className="h-3.5 w-3.5" />
                        )}
                        {editFileUploading ? "교체 중..." : "파일 교체"}
                      </button>

                      {/* 변수 매핑 에디터 열기 버튼 — jinja2 + docx일 때만 표시 */}
                      {formData.rendering_mode === "jinja2" &&
                        formData.output_format === "docx" &&
                        editingId && (
                          <button
                            type="button"
                            onClick={() => setEditMappingOpen(true)}
                            className="inline-flex items-center gap-1.5 rounded-md border border-blue-200 bg-blue-50 px-3 py-1.5 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100"
                          >
                            <TableProperties className="h-3.5 w-3.5" />
                            변수 매핑 에디터
                          </button>
                        )}
                    </div>
                  </div>
                </section>

                {/* ━━━━ 섹션 3: 변수 목록 (읽기 전용 요약) ━━━━ */}
                {uploadedVariables.length > 0 && (
                  <section>
                    <h3 className="text-foreground mb-3 flex items-center gap-2 text-sm font-semibold">
                      <Sparkles className="text-primary h-4 w-4" />
                      변수 목록
                      {/* 변수 개수 표시 */}
                      <span className="text-muted-foreground text-xs font-normal">
                        ({uploadedVariables.length}개)
                      </span>
                    </h3>

                    {/* 변수를 카테고리별 색상 배지로 읽기 전용 표시 */}
                    <div className="flex flex-wrap gap-1.5">
                      {uploadedVariables.map((v, i) => {
                        // 카테고리별 색상 정의
                        const categoryColors: Record<string, string> = {
                          user_input: "bg-green-100 text-green-700 border-green-200",
                          session_auto: "bg-blue-100 text-blue-700 border-blue-200",
                          ai_generated: "bg-blue-100 text-blue-800 border-blue-200",
                        };
                        // 카테고리 한글 라벨
                        const categoryLabels: Record<string, string> = {
                          user_input: "사용자 입력",
                          session_auto: "자동 채움",
                          ai_generated: "AI 생성",
                        };
                        // 변수의 타입(type 필드)을 카테고리로 사용
                        const colorClass =
                          categoryColors[v.type] || "bg-gray-100 text-gray-600 border-gray-200";
                        const categoryLabel = categoryLabels[v.type] || v.type;

                        return (
                          <span
                            key={i}
                            className={cn(
                              "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium",
                              colorClass,
                            )}
                            title={`${v.label || v.name} (${categoryLabel})`}
                          >
                            {/* 변수명 표시 */}
                            {v.label || v.name}
                            {/* 카테고리 약어 표시 */}
                            <span className="text-[10px] opacity-60">
                              {v.type === "user_input"
                                ? "입력"
                                : v.type === "session_auto"
                                  ? "자동"
                                  : v.type === "ai_generated"
                                    ? "AI"
                                    : v.type}
                            </span>
                          </span>
                        );
                      })}
                    </div>
                  </section>
                )}

                {/* ━━━━ 섹션 4: 고급 설정 (접이식, 기본 닫힘) ━━━━ */}
                <section>
                  <details
                    open={editAdvancedOpen}
                    onToggle={(e) => setEditAdvancedOpen((e.target as HTMLDetailsElement).open)}
                  >
                    {/* 접이식 헤더: 클릭하면 열리고 닫힘 */}
                    <summary className="text-muted-foreground hover:text-foreground flex cursor-pointer items-center gap-2 rounded-md bg-gray-50 px-3 py-2 text-sm font-medium transition-colors select-none hover:bg-gray-100">
                      <Settings2 className="h-4 w-4" />
                      고급 설정
                      {editAdvancedOpen ? (
                        <ChevronUp className="ml-auto h-3.5 w-3.5" />
                      ) : (
                        <ChevronDown className="ml-auto h-3.5 w-3.5" />
                      )}
                    </summary>

                    {/* 고급 설정 내용: 렌더링 모드, 이미지 소스, 예시 프롬프트 */}
                    <div className="mt-3 space-y-4 rounded-lg border border-gray-200 bg-gray-50/50 p-4">
                      {/* 렌더링 모드 선택 (라디오 버튼) */}
                      <div className="space-y-2">
                        <label className="text-foreground text-sm font-medium">렌더링 모드</label>
                        <div className="flex flex-wrap gap-2">
                          {(
                            [
                              { value: "jinja2", label: "Jinja2 템플릿" },
                              { value: "structured", label: "Structured (AI)" },
                              { value: "regex", label: "단순 치환" },
                            ] as const
                          ).map((m) => (
                            <label
                              key={m.value}
                              className={cn(
                                "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors",
                                formData.rendering_mode === m.value
                                  ? "border-primary bg-primary/5 font-medium"
                                  : "border-gray-200 bg-white hover:bg-gray-50",
                              )}
                            >
                              <input
                                type="radio"
                                name="edit_rendering_mode"
                                value={m.value}
                                checked={formData.rendering_mode === m.value}
                                onChange={(e) =>
                                  setFormData((prev) => ({
                                    ...prev,
                                    rendering_mode: e.target.value as RenderingMode,
                                  }))
                                }
                                className="text-primary focus:ring-primary h-3.5 w-3.5"
                              />
                              {m.label}
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* 이미지 소스 선택 (DALL-E 3 또는 Unsplash) */}
                      <div className="space-y-2">
                        <label className="text-foreground text-sm font-medium">이미지 소스</label>
                        <div className="flex gap-3">
                          {(
                            [
                              { value: "dalle3", label: "DALL-E 3", icon: Sparkles },
                              { value: "unsplash", label: "Unsplash", icon: Image },
                            ] as const
                          ).map((opt) => (
                            <label
                              key={opt.value}
                              className={cn(
                                "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors",
                                formData.image_source === opt.value
                                  ? "border-primary bg-primary/5 font-medium"
                                  : "border-gray-200 bg-white hover:bg-gray-50",
                              )}
                            >
                              <input
                                type="radio"
                                name="edit_image_source"
                                value={opt.value}
                                checked={formData.image_source === opt.value}
                                onChange={(e) =>
                                  setFormData((prev) => ({
                                    ...prev,
                                    image_source: e.target.value as ImageSource,
                                  }))
                                }
                                className="text-primary focus:ring-primary h-3.5 w-3.5"
                              />
                              <opt.icon className="text-muted-foreground h-3.5 w-3.5" />
                              {opt.label}
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* 예시 프롬프트 입력 — 보고서 생성 시 기본 프롬프트로 사용 */}
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">예시 프롬프트</label>
                        <textarea
                          value={formData.sample_prompt}
                          onChange={(e) =>
                            setFormData((prev) => ({ ...prev, sample_prompt: e.target.value }))
                          }
                          placeholder="이 템플릿에 사용할 예시 프롬프트를 입력하세요"
                          rows={2}
                          className="text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full resize-none rounded-md border border-gray-200 bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                        />
                      </div>
                    </div>
                  </details>
                </section>
              </div>

              {/* ── 수정 모드 푸터: 취소 + 저장 ── */}
              <div className="border-border flex items-center justify-end gap-3 border-t px-6 py-4">
                <button
                  onClick={() => setDialogOpen(false)}
                  className="border-border text-foreground hover:bg-muted rounded-md border px-4 py-2 text-sm font-medium transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || !formData.name.trim()}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                  {saving ? "저장 중..." : "저장"}
                </button>
              </div>

              {/* ── 수정 모드 전용: 변수 매핑 에디터 다이얼로그 ── */}
              {/* "변수 매핑 에디터" 버튼 클릭 시 VariableMappingEditor를 dialog 모드로 표시 */}
              {editMappingOpen && editingId && (
                <VariableMappingEditor
                  templateId={editingId}
                  templateName={formData.name || "템플릿"}
                  open={editMappingOpen}
                  onClose={() => setEditMappingOpen(false)}
                  onSaved={() => {
                    setEditMappingOpen(false);
                    // 변수 매핑 저장 후 목록을 새로고침하여 최신 변수 반영
                    fetchTemplates();
                    addToast("변수 매핑이 저장되었습니다", "success");
                  }}
                />
              )}
            </div>
          ) : (
            /* ========================================================= */
            /* ========  생성 모드: 4단계 파일 중심 플로우  ======== */
            /* ========================================================= */
            <div className="border-border relative z-50 w-full max-w-3xl rounded-lg border bg-white shadow-xl">
              {/* 다이얼로그 헤더 */}
              <div className="border-border flex items-center justify-between border-b px-6 py-4">
                <div>
                  <h2 className="text-foreground text-lg font-semibold">템플릿 추가</h2>
                  <p className="text-muted-foreground mt-0.5 text-sm">
                    파일을 업로드하면 자동으로 분석합니다
                  </p>
                </div>
                <button
                  onClick={() => setDialogOpen(false)}
                  className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-1.5 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* ---------- 스텝 인디케이터 ---------- */}
              {/* 현재 진행 단계를 시각적으로 표시하는 상단 바 */}
              <div className="border-border bg-muted/20 flex items-center gap-0 border-b px-6 py-3">
                {[
                  { step: 1 as const, label: "파일 업로드" },
                  { step: 2 as const, label: "기본 정보" },
                  { step: 3 as const, label: "변수 확인" },
                  { step: 4 as const, label: "저장" },
                ].map((s, idx) => (
                  <div key={s.step} className="flex items-center">
                    {/* 각 스텝 원형 번호 + 라벨 */}
                    <button
                      type="button"
                      onClick={() => {
                        // Step 1은 항상 이동 가능, 나머지는 업로드 완료 후에만
                        if (s.step === 1 || smartUploadResult) setUploadStep(s.step);
                      }}
                      disabled={s.step > 1 && !smartUploadResult}
                      className={cn(
                        "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors",
                        // 현재 단계: 파란 배경에 흰 글씨
                        uploadStep === s.step && "bg-primary text-primary-foreground",
                        // 완료된 단계: 초록 체크 표시
                        uploadStep > s.step && "bg-green-100 text-green-700",
                        // 아직 도달하지 않은 단계: 회색
                        uploadStep < s.step && "bg-gray-100 text-gray-400",
                        // 비활성 상태: 클릭 불가
                        s.step > 1 && !smartUploadResult && "cursor-not-allowed opacity-50",
                      )}
                    >
                      {/* 완료된 단계는 체크 아이콘, 나머지는 숫자 */}
                      {uploadStep > s.step ? <Check className="h-3 w-3" /> : <span>{s.step}</span>}
                      {s.label}
                    </button>
                    {/* 스텝 사이 연결선 (마지막 제외) */}
                    {idx < 3 && (
                      <div
                        className={cn(
                          "mx-1 h-px w-8",
                          uploadStep > s.step ? "bg-green-300" : "bg-gray-200",
                        )}
                      />
                    )}
                  </div>
                ))}
              </div>

              {/* ---------- 다이얼로그 본문 (스크롤 가능) ---------- */}
              <div className="max-h-[65vh] space-y-5 overflow-y-auto px-6 py-5">
                {/* ==================== Step 1: 파일 업로드 ==================== */}
                {/* 가장 먼저 보이는 화면 — 큰 드래그앤드롭 영역 */}
                {uploadStep === 1 && (
                  <div className="space-y-4">
                    <div className="space-y-1">
                      <h3 className="text-foreground text-base font-semibold">
                        양식 파일을 업로드하세요
                      </h3>
                      <p className="text-muted-foreground text-sm">
                        DOCX 또는 PPTX 파일을 업로드하면 자동으로 구조를 분석하고 변수를 추출합니다.
                      </p>
                    </div>

                    {/* 큰 드래그앤드롭 영역 */}
                    <div
                      onDragOver={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setIsDragOver(true);
                      }}
                      onDragLeave={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setIsDragOver(false);
                      }}
                      onDrop={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setIsDragOver(false);
                        const file = e.dataTransfer.files?.[0];
                        if (file) handleSmartUpload(file);
                      }}
                      onClick={() => smartFileInputRef.current?.click()}
                      className={cn(
                        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-8 py-16 transition-all",
                        // 업로드 중: 로딩 표시
                        uploading && "border-primary/50 bg-primary/5 cursor-wait",
                        // 드래그 오버: 강조 표시
                        !uploading && isDragOver && "border-primary bg-primary/10 scale-[1.01]",
                        // 기본 상태
                        !uploading &&
                          !isDragOver &&
                          "border-border hover:border-primary/40 hover:bg-muted/30",
                      )}
                    >
                      {/* 숨겨진 파일 선택 input */}
                      <input
                        ref={smartFileInputRef}
                        type="file"
                        accept=".docx,.pptx"
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) handleSmartUpload(file);
                          e.target.value = "";
                        }}
                      />

                      {uploading ? (
                        /* 업로드 진행 중 — 스피너 표시 */
                        <>
                          <Loader2 className="text-primary h-12 w-12 animate-spin" />
                          <p className="text-primary text-sm font-medium">
                            파일을 분석하고 있습니다...
                          </p>
                          <p className="text-muted-foreground text-xs">
                            구조 파악, 변수 추출, 렌더링 모드 판별 중
                          </p>
                        </>
                      ) : (
                        /* 파일 미선택 — 안내 */
                        <>
                          <Upload className="text-muted-foreground h-12 w-12" />
                          <div className="text-center">
                            <p className="text-foreground text-base font-medium">
                              파일을 드래그하거나 클릭하여 업로드
                            </p>
                            <p className="text-muted-foreground mt-1 text-sm">
                              허용 형식: DOCX, PPTX
                            </p>
                          </div>
                        </>
                      )}
                    </div>

                    {/* 파일 형식별 안내 카드 */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-3">
                        <p className="mb-1 text-xs font-medium text-blue-700">DOCX (Word)</p>
                        <p className="text-xs text-blue-600">
                          표 양식 → Jinja2 변수 자동 감지. 빈 양식도 AI가 구조를 파악합니다.
                        </p>
                      </div>
                      <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-3">
                        <p className="mb-1 text-xs font-medium text-blue-800">
                          PPTX (PowerPoint)
                        </p>
                        <p className="text-xs text-blue-700">
                          슬라이드마스터로 사용. AI가 내용을 자유롭게 생성합니다.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* ==================== Step 2: 기본 정보 ==================== */}
                {/* 업로드 완료 후 자동으로 표시됨. 서버 응답값이 자동 채워져 있음 */}
                {uploadStep === 2 && smartUploadResult && (
                  <div className="space-y-5">
                    {/* 업로드된 파일 정보 요약 카드 */}
                    <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-3">
                      <CheckCircle2 className="h-5 w-5 shrink-0 text-green-600" />
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium text-green-800">
                          {uploadFile?.name}
                        </p>
                        <p className="text-xs text-green-600">
                          {uploadFile && formatFileSize(uploadFile.size)} /{" "}
                          {RENDERING_MODE_LABELS[
                            smartUploadResult.rendering_mode as RenderingMode
                          ] || smartUploadResult.rendering_mode}{" "}
                          모드 감지 / {smartUploadResult.variables.length}개 변수 추출
                        </p>
                      </div>
                      {/* 다른 파일로 교체하기 버튼 */}
                      <button
                        type="button"
                        onClick={() => {
                          setUploadStep(1);
                          setSmartUploadResult(null);
                          setUploadFile(null);
                          setUploadedTemplateId(null);
                          setFormData(EMPTY_FORM);
                        }}
                        className="shrink-0 text-xs text-green-700 underline hover:text-green-900"
                      >
                        다시 업로드
                      </button>
                    </div>

                    <h3 className="text-foreground text-base font-semibold">기본 정보</h3>

                    {/* 2열 그리드: 이름 + 유형 */}
                    <div className="grid grid-cols-2 gap-4">
                      {/* 이름 — 파일명에서 확장자를 제거한 값이 자동 채워져 있음 */}
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">
                          이름 <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) =>
                            setFormData((prev) => ({ ...prev, name: e.target.value }))
                          }
                          placeholder="템플릿 이름"
                          className={cn(
                            "text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full rounded-md border px-3 py-2 text-sm focus:ring-1 focus:outline-none",
                            // 서버에서 자동 채워진 값은 연한 파란 배경으로 구분
                            smartUploadResult.name
                              ? "border-blue-200 bg-blue-50/30"
                              : "border-border bg-white",
                          )}
                        />
                      </div>

                      {/* 유형 — 서버 추측값을 select로 표시, 자유 입력도 가능 */}
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">유형</label>
                        <input
                          type="text"
                          value={formData.template_type}
                          onChange={(e) =>
                            setFormData((prev) => ({ ...prev, template_type: e.target.value }))
                          }
                          placeholder="보고서, 제안서, 회의록, 기획서 등"
                          list="template-type-suggestions"
                          className={cn(
                            "text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full rounded-md border px-3 py-2 text-sm focus:ring-1 focus:outline-none",
                            smartUploadResult.template_type
                              ? "border-blue-200 bg-blue-50/30"
                              : "border-border bg-white",
                          )}
                        />
                        {/* 유형 자동완성 제안 목록 */}
                        <datalist id="template-type-suggestions">
                          <option value="회의록" />
                          <option value="보고서" />
                          <option value="제안서" />
                          <option value="기획서" />
                          <option value="기타" />
                        </datalist>
                      </div>
                    </div>

                    {/* 2열 그리드: 말투 + 출력형식 (자동 감지됨) */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">말투</label>
                        <select
                          value={formData.tone}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              tone: e.target.value as TemplateFormData["tone"],
                            }))
                          }
                          className="border-border text-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                        >
                          {TONE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="space-y-1.5">
                        <label className="text-foreground text-sm font-medium">출력형식</label>
                        <div
                          className={cn(
                            "rounded-md border px-3 py-2 font-mono text-sm uppercase",
                            "text-foreground border-blue-200 bg-blue-50/30",
                          )}
                        >
                          {formData.output_format}
                        </div>
                        <p className="text-muted-foreground text-xs">파일에서 자동 감지됨</p>
                      </div>
                    </div>

                    {/* 설명 (선택) */}
                    <div className="space-y-1.5">
                      <label className="text-foreground text-sm font-medium">
                        설명 <span className="text-muted-foreground text-xs">(선택)</span>
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) =>
                          setFormData((prev) => ({ ...prev, description: e.target.value }))
                        }
                        placeholder="이 템플릿에 대한 설명을 입력하세요"
                        rows={2}
                        className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full resize-none rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                      />
                    </div>

                    {/* ---- 고급 설정 (접이식, 기본 닫힘) ---- */}
                    <details
                      open={advancedOpen}
                      onToggle={(e) => setAdvancedOpen((e.target as HTMLDetailsElement).open)}
                    >
                      <summary className="text-muted-foreground hover:text-foreground flex cursor-pointer items-center gap-2 rounded-md bg-gray-50 px-3 py-2 text-sm font-medium transition-colors select-none hover:bg-gray-100">
                        <Settings2 className="h-4 w-4" />
                        고급 설정
                        {advancedOpen ? (
                          <ChevronUp className="ml-auto h-3.5 w-3.5" />
                        ) : (
                          <ChevronDown className="ml-auto h-3.5 w-3.5" />
                        )}
                      </summary>

                      <div className="mt-3 space-y-4 rounded-lg border border-gray-200 bg-gray-50/50 p-4">
                        {/* 렌더링 모드 수동 변경 */}
                        <div className="space-y-2">
                          <label className="text-foreground text-sm font-medium">렌더링 모드</label>
                          <p className="text-muted-foreground text-xs">
                            서버가 자동 판별한 값입니다. 필요시 수동으로 변경하세요.
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {(
                              [
                                { value: "jinja2", label: "Jinja2 템플릿" },
                                { value: "structured", label: "Structured (AI)" },
                                { value: "regex", label: "단순 치환" },
                              ] as const
                            ).map((m) => (
                              <label
                                key={m.value}
                                className={cn(
                                  "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors",
                                  formData.rendering_mode === m.value
                                    ? "border-primary bg-primary/5 font-medium"
                                    : "border-gray-200 bg-white hover:bg-gray-50",
                                )}
                              >
                                <input
                                  type="radio"
                                  name="create_rendering_mode"
                                  value={m.value}
                                  checked={formData.rendering_mode === m.value}
                                  onChange={(e) =>
                                    setFormData((prev) => ({
                                      ...prev,
                                      rendering_mode: e.target.value as RenderingMode,
                                    }))
                                  }
                                  className="text-primary focus:ring-primary h-3.5 w-3.5"
                                />
                                {m.label}
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* 이미지 소스 */}
                        <div className="space-y-2">
                          <label className="text-foreground text-sm font-medium">이미지 소스</label>
                          <div className="flex gap-3">
                            {(
                              [
                                { value: "dalle3", label: "DALL-E 3", icon: Sparkles },
                                { value: "unsplash", label: "Unsplash", icon: Image },
                              ] as const
                            ).map((opt) => (
                              <label
                                key={opt.value}
                                className={cn(
                                  "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors",
                                  formData.image_source === opt.value
                                    ? "border-primary bg-primary/5 font-medium"
                                    : "border-gray-200 bg-white hover:bg-gray-50",
                                )}
                              >
                                <input
                                  type="radio"
                                  name="create_image_source"
                                  value={opt.value}
                                  checked={formData.image_source === opt.value}
                                  onChange={(e) =>
                                    setFormData((prev) => ({
                                      ...prev,
                                      image_source: e.target.value as ImageSource,
                                    }))
                                  }
                                  className="text-primary focus:ring-primary h-3.5 w-3.5"
                                />
                                <opt.icon className="text-muted-foreground h-3.5 w-3.5" />
                                {opt.label}
                              </label>
                            ))}
                          </div>
                        </div>

                        {/* 예시 프롬프트 */}
                        <div className="space-y-1.5">
                          <label className="text-foreground text-sm font-medium">
                            예시 프롬프트
                          </label>
                          <textarea
                            value={formData.sample_prompt}
                            onChange={(e) =>
                              setFormData((prev) => ({ ...prev, sample_prompt: e.target.value }))
                            }
                            placeholder="이 템플릿에 사용할 예시 프롬프트를 입력하세요"
                            rows={2}
                            className="text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full resize-none rounded-md border border-gray-200 bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                          />
                        </div>
                      </div>
                    </details>
                  </div>
                )}

                {/* ==================== Step 3: 변수 매핑 ==================== */}
                {uploadStep === 3 && smartUploadResult && (
                  <div className="space-y-4">
                    {/* Jinja2 모드: 변수 매핑 에디터를 인라인으로 표시 */}
                    {formData.rendering_mode === "jinja2" && uploadedTemplateId && (
                      <>
                        <div className="space-y-1">
                          <h3 className="text-foreground text-base font-semibold">
                            변수 매핑 확인
                          </h3>
                          <p className="text-muted-foreground text-sm">
                            서버가 감지한 변수를 확인하세요. 수정이 필요하면 셀을 클릭하여 편집할 수
                            있습니다.
                          </p>
                        </div>

                        {/* 감지된 변수 요약 카드 */}
                        {uploadedVariables.length > 0 && (
                          <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-3">
                            <p className="mb-1 text-sm font-medium text-blue-800">
                              감지된 변수 {uploadedVariables.length}개
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {uploadedVariables.map((v, i) => (
                                <span
                                  key={i}
                                  className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 font-mono text-xs text-blue-700"
                                >
                                  {"{{ "}
                                  {v.name}
                                  {" }}"}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* VariableMappingEditor를 인라인 모드로 삽입 */}
                        <VariableMappingEditor
                          templateId={uploadedTemplateId}
                          templateName={formData.name || "새 템플릿"}
                          open={true}
                          onClose={() => {
                            /* 인라인 모드에서는 사용 안 함 */
                          }}
                          onSaved={() => {
                            setVariableMappingDirty(false);
                            addToast("변수 매핑이 저장되었습니다", "success");
                          }}
                          mode="inline"
                        />
                      </>
                    )}

                    {/* Structured 모드: AI 안내 카드 */}
                    {formData.rendering_mode === "structured" && (
                      <div className="space-y-3">
                        <h3 className="text-foreground text-base font-semibold">
                          AI 자유 생성 모드
                        </h3>
                        <div className="rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-6 text-center">
                          <Sparkles className="mx-auto mb-3 h-10 w-10 text-blue-400" />
                          <p className="mb-1 text-sm font-medium text-blue-900">
                            AI가 내용을 자유롭게 생성합니다
                          </p>
                          <p className="text-xs text-blue-700">
                            Structured 모드에서는 AI가 슬라이드/문서 구조를 직접 결정합니다. 별도의
                            변수 매핑이 필요하지 않습니다.
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Regex 모드: 간단한 안내 */}
                    {formData.rendering_mode === "regex" && (
                      <div className="space-y-3">
                        <h3 className="text-foreground text-base font-semibold">단순 치환 모드</h3>
                        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                          <p className="text-muted-foreground text-sm">
                            {"{{ 변수명 }}"} 패턴을 정규식으로 단순 치환합니다. 감지된 변수{" "}
                            {uploadedVariables.length}개가 사용됩니다.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* ==================== Step 4: 저장 확인 ==================== */}
                {uploadStep === 4 && smartUploadResult && (
                  <div className="space-y-4">
                    <h3 className="text-foreground text-base font-semibold">최종 확인</h3>
                    <p className="text-muted-foreground text-sm">
                      아래 내용을 확인한 후 저장 버튼을 눌러주세요.
                    </p>

                    {/* 최종 요약 카드 */}
                    <div className="border-border bg-muted/20 space-y-3 rounded-lg border p-4">
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">이름:</span>
                          <span className="text-foreground ml-2 font-medium">
                            {formData.name || "(미입력)"}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">유형:</span>
                          <span className="text-foreground ml-2 font-medium">
                            {formData.template_type || "(미입력)"}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">말투:</span>
                          <span className="text-foreground ml-2 font-medium">
                            {TONE_LABELS[formData.tone]}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">출력형식:</span>
                          <span className="text-foreground ml-2 font-mono font-medium uppercase">
                            {formData.output_format}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">렌더링:</span>
                          <span
                            className={cn(
                              "ml-2 inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                              RENDERING_MODE_BADGE[formData.rendering_mode] ||
                                "bg-gray-100 text-gray-600",
                            )}
                          >
                            {RENDERING_MODE_LABELS[formData.rendering_mode] ||
                              formData.rendering_mode}
                          </span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">변수:</span>
                          <span className="text-foreground ml-2 font-medium">
                            {uploadedVariables.length}개
                          </span>
                        </div>
                      </div>
                      {formData.description && (
                        <div className="border-border border-t pt-2 text-sm">
                          <span className="text-muted-foreground">설명:</span>
                          <span className="text-foreground ml-2">{formData.description}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* ---------- 다이얼로그 푸터 (스텝별 버튼) ---------- */}
              <div className="border-border flex items-center justify-between border-t px-6 py-4">
                {/* 좌측: 취소 또는 이전 단계 버튼 */}
                <div>
                  {uploadStep === 1 ? (
                    <button
                      onClick={() => setDialogOpen(false)}
                      className="border-border text-foreground hover:bg-muted rounded-md border px-4 py-2 text-sm font-medium transition-colors"
                    >
                      취소
                    </button>
                  ) : (
                    <button
                      onClick={() =>
                        setUploadStep((prev) => Math.max(1, prev - 1) as 1 | 2 | 3 | 4)
                      }
                      className="border-border text-foreground hover:bg-muted inline-flex items-center gap-1.5 rounded-md border px-4 py-2 text-sm font-medium transition-colors"
                    >
                      <ChevronUp className="h-4 w-4 rotate-[-90deg]" />
                      이전
                    </button>
                  )}
                </div>

                {/* 우측: 다음 단계 또는 저장 버튼 */}
                <div className="flex items-center gap-3">
                  {/* Step 1에서는 버튼 없음 (파일 업로드가 자동으로 다음 단계로 이동) */}

                  {/* Step 2: 다음 (변수 확인으로) */}
                  {uploadStep === 2 && (
                    <button
                      onClick={() => setUploadStep(3)}
                      disabled={!formData.name.trim()}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-1.5 rounded-md px-5 py-2 text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      다음
                      <ChevronDown className="h-4 w-4 rotate-[-90deg]" />
                    </button>
                  )}

                  {/* Step 3: 다음 (저장 확인으로) */}
                  {uploadStep === 3 && (
                    <button
                      onClick={() => setUploadStep(4)}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-1.5 rounded-md px-5 py-2 text-sm font-medium transition-colors"
                    >
                      다음
                      <ChevronDown className="h-4 w-4 rotate-[-90deg]" />
                    </button>
                  )}

                  {/* Step 4: 최종 저장 버튼 */}
                  {uploadStep === 4 && (
                    <button
                      onClick={handleStepSave}
                      disabled={saving || !formData.name.trim()}
                      className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-2 rounded-md px-6 py-2 text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      {saving ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                      {saving ? "저장 중..." : "저장"}
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ======== 변수 매핑 에디터 ======== */}
      <VariableMappingEditor
        templateId={mappingTemplateId}
        templateName={mappingTemplateName}
        open={mappingEditorOpen}
        onClose={() => setMappingEditorOpen(false)}
        onSaved={() => {
          setMappingEditorOpen(false);
          fetchTemplates();
        }}
      />

      {/* ======== 삭제 확인 다이얼로그 ======== */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setDeleteTarget(null)}
            aria-hidden="true"
          />
          <div className="border-border relative z-50 w-full max-w-md rounded-lg border bg-white p-6 shadow-xl">
            <h2 className="text-foreground text-lg font-semibold">템플릿을 삭제하시겠습니까?</h2>
            <p className="text-muted-foreground mt-2 text-sm">
              &ldquo;{deleteTarget.name}&rdquo; 템플릿을 삭제합니다. 이 작업은 되돌릴 수 없습니다.
            </p>
            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                onClick={() => setDeleteTarget(null)}
                className="border-border text-foreground hover:bg-muted rounded-md border px-4 py-2 text-sm font-medium transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleDelete}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
