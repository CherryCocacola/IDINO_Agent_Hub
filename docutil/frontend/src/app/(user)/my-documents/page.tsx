"use client";

import {
  Upload,
  FileText,
  FileSpreadsheet,
  FileImage,
  File,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
  Shield,
  Building2,
  FolderTree,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { useDropzone } from "react-dropzone";

import apiClient from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";
import { cn } from "@/lib/utils/cn";

// ── Types ──────────────────────────────────────────────────────────────────

type Visibility =
  | "public"
  | "all_departments"
  | "department_only"
  | "project_only"
  | "confidential"
  | "hidden";

interface DocumentItem {
  id: string;
  name: string;
  format: string;
  file_size_bytes: number;
  status: "waiting" | "processing" | "completed" | "error";
  visibility: Visibility;
  created_at: string;
  department_name?: string;
  project_name?: string;
  error_message?: string;
  // 단건 조회(GET /documents/{id}) 응답에만 채워지는 표시용 부가 정보.
  // 목록 응답에는 없으므로 카드 클릭 시 별도 fetch 한다.
  uploaded_by?: string;
  uploaded_by_name?: string;
  chunk_count?: number;
  metadata?: Record<string, unknown>;
  visible_department_names?: string[];
  project_member_names?: string[];
  visibility_summary?: string;
}

interface DepartmentRef {
  id: string;
  name: string;
  parent_id: string | null;
  depth: number;
  path: string;
}

interface ProjectRef {
  id: string;
  name: string;
}

type UploadTarget = "department" | "project";

// ── Constants ──────────────────────────────────────────────────────────────

const VISIBILITY_OPTIONS: { value: Visibility; label: string }[] = [
  { value: "public", label: "전체 공개" },
  { value: "all_departments", label: "전부서 공개" },
  { value: "department_only", label: "부서 내 공개" },
  { value: "project_only", label: "프로젝트 내 공개" },
  { value: "confidential", label: "비밀" },
  { value: "hidden", label: "숨김" },
];

// ── Helpers ────────────────────────────────────────────────────────────────

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function getFormatIcon(fmt: string | undefined) {
  const lower = (fmt || "").toLowerCase();
  if (["pdf"].includes(lower)) return <FileText className="h-5 w-5 text-red-500" />;
  if (["xlsx", "xls", "csv"].includes(lower))
    return <FileSpreadsheet className="h-5 w-5 text-green-600" />;
  if (["png", "jpg", "jpeg", "gif", "svg"].includes(lower))
    return <FileImage className="h-5 w-5 text-blue-500" />;
  if (["doc", "docx", "txt", "md", "hwp"].includes(lower))
    return <FileText className="h-5 w-5 text-blue-500" />;
  return <File className="h-5 w-5 text-gray-500" />;
}

function getStatusConfig(status: DocumentItem["status"]) {
  switch (status) {
    case "waiting":
      return {
        label: "대기",
        icon: Clock,
        className: "bg-yellow-100 text-yellow-700",
      };
    case "processing":
      return {
        label: "처리 중",
        icon: Loader2,
        className: "bg-blue-100 text-blue-700",
        spin: true,
      };
    case "completed":
      return {
        label: "완료",
        icon: CheckCircle,
        className: "bg-green-100 text-green-700",
      };
    case "error":
      return {
        label: "오류",
        icon: AlertCircle,
        className: "bg-red-100 text-red-700",
      };
  }
}

function getVisibilityBadgeClass(v: Visibility) {
  switch (v) {
    case "public":
      return "bg-green-100 text-green-700";
    case "all_departments":
      return "bg-blue-100 text-blue-700";
    case "department_only":
      return "bg-cyan-100 text-cyan-700";
    case "project_only":
      return "bg-blue-100 text-blue-800";
    case "confidential":
      return "bg-red-100 text-red-700";
    case "hidden":
      return "bg-gray-100 text-gray-600";
  }
}

function getVisibilityLabel(v: Visibility) {
  return VISIBILITY_OPTIONS.find((opt) => opt.value === v)?.label ?? v;
}

// ── Component ──────────────────────────────────────────────────────────────

export default function UserDocumentsPage() {
  const { user } = useAuth();
  const { addToast } = useToast();

  // Documents
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Upload state
  const [uploading, setUploading] = useState(false);
  // 다중 파일 업로드 진행 상태 (current/total). 0/0 이면 표시하지 않는다.
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const [uploadTarget, setUploadTarget] = useState<UploadTarget>("department");
  const [uploadVisibility, setUploadVisibility] = useState<Visibility>("department_only");
  const [uploadDeptId, setUploadDeptId] = useState<string>("");
  const [uploadProjectId, setUploadProjectId] = useState<string>("");

  // User's departments and projects
  const [allDepartments, setAllDepartments] = useState<DepartmentRef[]>([]);
  const [myProjects, setMyProjects] = useState<ProjectRef[]>([]);

  // 사용자 소속 부서 + 하위 부서만 필터
  const myDepartments = (() => {
    const userDeptId = user?.department_id;
    if (!userDeptId || allDepartments.length === 0) return allDepartments;
    const userDept = allDepartments.find((d) => d.id === userDeptId);
    if (!userDept) return allDepartments;
    return allDepartments.filter((d) => d.path?.startsWith(userDept.path.replace(/\/$/, "")));
  })();

  // Delete confirmation
  const [deleteDocId, setDeleteDocId] = useState<string | null>(null);

  // Detail dialog — 행 클릭 시 단건 GET 으로 부가 정보까지 노출한다.
  const [detailDoc, setDetailDoc] = useState<DocumentItem | null>(null);

  /**
   * 행 클릭 시 호출. 즉시 목록 정보로 다이얼로그를 열고, 비동기로
   * GET /documents/{id} 결과(visible_department_names 등)로 보강한다.
   */
  const openDetail = async (doc: DocumentItem) => {
    setDetailDoc(doc);
    try {
      // 사용자 화면이므로 as_user_view=true 로 본인 권한 검증을 받는다.
      const detail = await apiClient.get<DocumentItem>(`/documents/${doc.id}`, {
        as_user_view: "true",
      });
      // 다이얼로그가 닫힌 사이 stale 응답으로 덮어쓰지 않도록 ID 일치 확인.
      setDetailDoc((prev) => (prev && prev.id === detail.id ? detail : prev));
    } catch {
      // 부가 정보 fetch 실패 시 목록 정보만 그대로 노출
    }
  };

  // ── Fetch documents ──────────────────────────────────────────────────────

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      // 사용자 화면이므로 as_user_view=true — admin 계정이라도 본인 권한
      // (visibility scope) 으로만 보이도록 백엔드에 명시한다.
      const response = await apiClient.get<{ items: DocumentItem[]; total: number }>("/documents", {
        as_user_view: "true",
      });
      setDocuments(response.items || []);
    } catch {
      addToast("문서 목록을 불러오지 못했습니다.", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  // ── Fetch user's departments and projects ────────────────────────────────

  const fetchUserScope = useCallback(async () => {
    try {
      const orgId = user?.organization_id;
      if (orgId) {
        const depts = await apiClient.get<DepartmentRef[]>(`/organizations/${orgId}/departments`, {
          my: "true",
        });
        setAllDepartments(Array.isArray(depts) ? depts : []);
      }
      const projs = await apiClient.get<{ items: ProjectRef[] }>("/projects", {
        my: "true",
      });
      setMyProjects(projs.items || []);
    } catch {
      // fallback silently
    }
  }, [user?.organization_id]);

  useEffect(() => {
    fetchDocuments();
    fetchUserScope();
  }, [fetchDocuments, fetchUserScope]);

  // ── Auto-refresh for pending/processing docs ─────────────────────────────

  useEffect(() => {
    const hasPending = documents.some((d) => d.status === "waiting" || d.status === "processing");
    if (!hasPending) return;

    const interval = setInterval(fetchDocuments, 5000);
    return () => clearInterval(interval);
  }, [documents, fetchDocuments]);

  // ── Upload handler ────────────────────────────────────────────────────────

  const [pendingFiles, setPendingFiles] = useState<globalThis.File[]>([]);

  const onDrop = useCallback((acceptedFiles: globalThis.File[]) => {
    if (acceptedFiles.length === 0) return;
    setPendingFiles((prev) => [...prev, ...acceptedFiles]);
  }, []);

  const removePendingFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (pendingFiles.length === 0) {
      addToast("업로드할 파일을 선택해주세요.", "error");
      return;
    }
    if (uploadTarget === "department" && uploadVisibility !== "public" && !uploadDeptId) {
      addToast("업로드할 부서를 선택해주세요.", "error");
      return;
    }
    if (uploadTarget === "project" && !uploadProjectId) {
      addToast("업로드할 프로젝트를 선택해주세요.", "error");
      return;
    }

    setUploading(true);
    setUploadProgress({ current: 0, total: pendingFiles.length });
    // 업로드 시작 즉시 시작 토스트를 띄워 "지금 업로드 중" 임을 시각적으로 알린다.
    addToast(
      pendingFiles.length === 1
        ? "업로드를 시작합니다..."
        : `${pendingFiles.length}개 파일 업로드를 시작합니다...`,
      "info",
    );
    try {
      const params = new URLSearchParams();
      params.set("visibility", uploadVisibility);
      if (uploadTarget === "department" && uploadDeptId) {
        params.set("department_id", uploadDeptId);
      }
      if (uploadTarget === "project" && uploadProjectId) {
        params.set("project_id", uploadProjectId);
      }

      let successCount = 0;
      let failCount = 0;
      // 첫 번째 실패의 서버 detail 을 별도로 저장해 토스트에 노출한다.
      // (이전에는 catch 가 에러를 완전히 삼켜 사용자가 원인을 알 수 없었다.)
      let firstError: string | null = null;
      for (let i = 0; i < pendingFiles.length; i++) {
        const file = pendingFiles[i];
        // 진행 표시 갱신 — 화면 상단/버튼 영역에 "업로드 중 (i+1/N)" 형태로 표시된다.
        setUploadProgress({ current: i + 1, total: pendingFiles.length });
        try {
          const formData = new FormData();
          formData.append("file", file);
          await apiClient.upload(`/documents/upload?${params.toString()}`, formData);
          successCount++;
          // 업로드된 파일이 즉시 목록에 노출되도록 매 파일마다 fetchDocuments 호출.
          // (waiting/processing 상태로 표시되며 5 초 폴링이 자동 시작된다.)
          fetchDocuments();
        } catch (err) {
          failCount++;
          if (firstError === null) {
            firstError = err instanceof Error ? err.message : "알 수 없는 오류";
          }
        }
      }
      if (successCount > 0 && failCount === 0) {
        addToast(`${successCount}개 파일 업로드 완료`, "success");
      } else if (successCount > 0 && failCount > 0) {
        addToast(
          `${successCount}개 완료, ${failCount}개 실패${firstError ? `: ${firstError}` : ""}`,
          "default",
        );
      } else {
        addToast(firstError || "파일 업로드에 실패했습니다.", "error");
      }
      setPendingFiles([]);
      // 마지막 파일 업로드 후 백엔드 트랜잭션 커밋 시간을 1 초 정도 두고 한 번 더 갱신.
      // (간헐적으로 직후 fetch 가 빈 결과를 받는 케이스 보강)
      setTimeout(() => fetchDocuments(), 1000);
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : "파일 업로드에 실패했습니다.",
        "error",
      );
    } finally {
      setUploading(false);
      setUploadProgress({ current: 0, total: 0 });
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: false,
  });

  // ── Delete handler ────────────────────────────────────────────────────────

  const handleDelete = async () => {
    if (!deleteDocId) return;
    try {
      await apiClient.delete(`/documents/${deleteDocId}`);
      addToast("문서가 삭제되었습니다.", "success");
      setDeleteDocId(null);
      fetchDocuments();
    } catch {
      addToast("문서 삭제에 실패했습니다.", "error");
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">문서 업로드</h1>
        <p className="mt-1 text-sm text-gray-600">문서를 업로드하고 처리 상태를 확인합니다</p>
      </div>

      {/* Upload configuration */}
      <div className="space-y-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-800">업로드 설정</h2>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* 1. Upload target type */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">업로드 대상</label>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setUploadTarget("department");
                  setUploadVisibility("department_only");
                  setUploadProjectId("");
                }}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  uploadTarget === "department"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50",
                )}
              >
                <Building2 className="h-4 w-4" />
                부서
              </button>
              <button
                onClick={() => {
                  setUploadTarget("project");
                  setUploadVisibility("project_only");
                  setUploadDeptId("");
                }}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                  uploadTarget === "project"
                    ? "bg-blue-600 text-white"
                    : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50",
                )}
              >
                <FolderTree className="h-4 w-4" />
                프로젝트
              </button>
            </div>
          </div>

          {/* 2. Visibility - options depend on target type */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-700">공개범위</label>
            <select
              value={uploadVisibility}
              onChange={(e) => {
                const v = e.target.value as Visibility;
                setUploadVisibility(v);
                if (v === "public") setUploadDeptId("");
              }}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
            >
              {uploadTarget === "department" ? (
                <>
                  <option value="public">전체 공개</option>
                  <option value="all_departments">전부서 공개</option>
                  <option value="department_only">부서 내 공개</option>
                </>
              ) : (
                <>
                  <option value="public">전체 공개</option>
                  <option value="project_only">프로젝트 내 공개</option>
                </>
              )}
            </select>
          </div>

          {/* 3. Department or Project selector - conditional */}
          {uploadTarget === "department" && uploadVisibility !== "public" && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">부서 선택</label>
              <select
                value={uploadDeptId}
                onChange={(e) => setUploadDeptId(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
              >
                <option value="">부서를 선택하세요</option>
                {myDepartments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {"─".repeat(dept.depth || 0)} {dept.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          {uploadTarget === "project" && (
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">프로젝트 선택</label>
              <select
                value={uploadProjectId}
                onChange={(e) => setUploadProjectId(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-blue-400 focus:ring-1 focus:ring-blue-100 focus:outline-none"
              >
                <option value="">프로젝트를 선택하세요</option>
                {myProjects.map((proj) => (
                  <option key={proj.id} value={proj.id}>
                    {proj.name}
                  </option>
                ))}
              </select>
              {/* 프로젝트 업로드는 폴더 트리 UI가 없는 화면이어서, 폴더가 없는 프로젝트에는
                  자동으로 "자동 보관 폴더 (자동)" 이 만들어진다. 사용자에게 이 부수효과를 명시한다. */}
              <p className="mt-1.5 text-xs text-gray-500">
                폴더가 지정되지 않은 프로젝트는 "자동 보관 폴더(자동)"로 분류됩니다.
                상세 분류가 필요하면 관리자 화면에서 폴더를 먼저 만들어주세요.
              </p>
            </div>
          )}
        </div>

        {/* Drag & drop zone */}
        <div
          {...getRootProps()}
          className={cn(
            "cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors",
            isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400",
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-2">
            <Upload className="h-10 w-10 text-gray-300" />
            <p className="text-sm font-medium text-gray-700">
              {isDragActive ? "파일을 여기에 놓으세요" : "드래그 앤 드롭 또는 클릭하여 파일 선택"}
            </p>
            <p className="text-xs text-gray-500">PDF, DOCX, XLSX, HWP, CSV, PPTX 등을 지원합니다</p>
          </div>
        </div>

        {/* 선택된 파일 목록 + 업로드 버튼 */}
        {pendingFiles.length > 0 && (
          <div className="space-y-3">
            <div className="divide-y divide-gray-100 rounded-lg border border-gray-200">
              {pendingFiles.map((file, idx) => (
                <div
                  key={`${file.name}-${idx}`}
                  className="flex items-center justify-between px-4 py-2 text-sm"
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <FileText className="h-4 w-4 shrink-0 text-gray-400" />
                    <span className="truncate text-gray-700">{file.name}</span>
                    <span className="shrink-0 text-xs text-gray-400">
                      {(file.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </div>
                  <button
                    onClick={() => removePendingFile(idx)}
                    className="ml-2 shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">{pendingFiles.length}개 파일 선택됨</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPendingFiles([])}
                  disabled={uploading}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  전체 취소
                </button>
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {/* 다중 파일이면 진행 카운터 노출 (예: "업로드 중 2/5") */}
                      {uploadProgress.total > 1
                        ? `업로드 중 ${uploadProgress.current}/${uploadProgress.total}`
                        : "업로드 중..."}
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4" />
                      업로드
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Documents list */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-800">내 문서 목록</h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <FileText className="h-16 w-16 text-gray-300" />
            <p className="mt-4 text-lg font-medium text-gray-900">업로드한 문서가 없습니다</p>
            <p className="mt-1 text-sm text-gray-500">위에서 파일을 업로드하세요</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50/50">
                  <th className="px-4 py-3 text-left text-xs font-semibold tracking-wider text-gray-500 uppercase">
                    파일명
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold tracking-wider text-gray-500 uppercase">
                    크기
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold tracking-wider text-gray-500 uppercase">
                    상태
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold tracking-wider text-gray-500 uppercase">
                    공개범위
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold tracking-wider text-gray-500 uppercase">
                    대상
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold tracking-wider text-gray-500 uppercase">
                    업로드일
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold tracking-wider text-gray-500 uppercase">
                    작업
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {documents.map((doc) => {
                  const statusConfig = getStatusConfig(doc.status);
                  const StatusIcon = statusConfig.icon;

                  return (
                    <tr
                      key={doc.id}
                      onClick={() => openDetail(doc)}
                      className="cursor-pointer transition-colors even:bg-gray-50/50 hover:bg-gray-50"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {getFormatIcon(doc.format)}
                          <span className="max-w-xs truncate font-medium text-gray-900">
                            {doc.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {formatFileSize(doc.file_size_bytes)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                            statusConfig.className,
                          )}
                        >
                          <StatusIcon
                            className={cn(
                              "h-3 w-3",
                              "spin" in statusConfig && statusConfig.spin && "animate-spin",
                            )}
                          />
                          {statusConfig.label}
                        </span>
                        {doc.status === "error" && doc.error_message && (
                          <p className="mt-0.5 max-w-[120px] truncate text-[10px] text-red-500">
                            {doc.error_message}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-semibold",
                            getVisibilityBadgeClass(doc.visibility),
                          )}
                        >
                          <Shield className="h-3 w-3" />
                          {getVisibilityLabel(doc.visibility)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">
                        {doc.department_name || doc.project_name || "-"}
                      </td>
                      <td className="px-4 py-3 text-gray-600">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={(e) => {
                            // 행 클릭(상세 다이얼로그 열기)으로 이벤트가 전파되지 않게 막는다.
                            e.stopPropagation();
                            setDeleteDocId(doc.id);
                          }}
                          className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-500"
                          aria-label="문서 삭제"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 상세 보기 모달 — 행 클릭 시 노출. 관리자 화면과 동일한 정보를 보여준다 */}
      {detailDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setDetailDoc(null)}
            aria-hidden="true"
          />
          <div className="relative z-50 flex max-h-[85vh] w-full max-w-xl flex-col gap-4 overflow-hidden rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
            <div className="flex items-start justify-between gap-4">
              <h3 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
                {getFormatIcon(detailDoc.format)}
                <span className="truncate">{detailDoc.name}</span>
              </h3>
              <button
                onClick={() => setDetailDoc(null)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="닫기"
              >
                ✕
              </button>
            </div>

            <div className="overflow-auto pr-1">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-500">형식</span>
                  <p className="uppercase text-gray-900">{detailDoc.format}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-500">크기</span>
                  <p className="text-gray-900">{formatFileSize(detailDoc.file_size_bytes)}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-500">상태</span>
                  <p className="mt-1">
                    {(() => {
                      const c = getStatusConfig(detailDoc.status);
                      const Icon = c.icon;
                      return (
                        <span
                          className={cn(
                            "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
                            c.className,
                          )}
                        >
                          <Icon
                            className={cn(
                              "h-3 w-3",
                              "spin" in c && c.spin && "animate-spin",
                            )}
                          />
                          {c.label}
                        </span>
                      );
                    })()}
                  </p>
                </div>
                <div>
                  <span className="font-medium text-gray-500">공개범위</span>
                  <p className="mt-1">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-semibold",
                        getVisibilityBadgeClass(detailDoc.visibility),
                      )}
                    >
                      <Shield className="h-3 w-3" />
                      {getVisibilityLabel(detailDoc.visibility)}
                    </span>
                  </p>
                </div>
                <div>
                  <span className="font-medium text-gray-500">업로드자</span>
                  {/* 백엔드 단건 조회의 uploaded_by_name (한글 사용자명).
                      미반영 시(다이얼로그 열린 직후 짧은 순간) "—" 로 표시. */}
                  <p className="text-gray-900">{detailDoc.uploaded_by_name || "—"}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-500">업로드일</span>
                  <p className="text-gray-900">
                    {new Date(detailDoc.created_at).toLocaleString()}
                  </p>
                </div>
                {detailDoc.department_name && (
                  <div>
                    <span className="font-medium text-gray-500">부서</span>
                    <p className="text-gray-900">{detailDoc.department_name}</p>
                  </div>
                )}
                {detailDoc.project_name && (
                  <div>
                    <span className="font-medium text-gray-500">프로젝트</span>
                    <p className="text-gray-900">{detailDoc.project_name}</p>
                  </div>
                )}
              </div>

              {/* 공개 범위 한 줄 요약 */}
              {detailDoc.visibility_summary && (
                <div className="mt-4 rounded-md border bg-gray-50 p-3 text-sm">
                  <div className="mb-1 text-xs font-medium text-gray-500">공개 범위</div>
                  <p className="font-medium text-gray-900">{detailDoc.visibility_summary}</p>
                </div>
              )}

              {/* department_only / all_departments → 공개 대상 부서 목록 */}
              {(detailDoc.visibility === "department_only" ||
                detailDoc.visibility === "all_departments") && (
                <div className="mt-3">
                  <h4 className="mb-2 text-sm font-medium text-gray-500">
                    공개 대상 부서{" "}
                    <span className="text-xs">
                      ({detailDoc.visible_department_names?.length ?? 0}개)
                    </span>
                  </h4>
                  <div className="max-h-40 overflow-auto rounded-md bg-gray-50 p-3 text-xs">
                    {detailDoc.visible_department_names &&
                    detailDoc.visible_department_names.length > 0 ? (
                      <ul className="space-y-0.5">
                        {detailDoc.visible_department_names.map((n) => (
                          <li key={n} className="text-gray-800">
                            · {n}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-gray-500">잠시만 기다려주세요…</p>
                    )}
                  </div>
                </div>
              )}

              {/* project_only → 공개 대상 사용자 목록 */}
              {detailDoc.visibility === "project_only" && (
                <div className="mt-3">
                  <h4 className="mb-2 text-sm font-medium text-gray-500">
                    공개 대상 사용자{" "}
                    <span className="text-xs">
                      ({detailDoc.project_member_names?.length ?? 0}명)
                    </span>
                  </h4>
                  <div className="max-h-40 overflow-auto rounded-md bg-gray-50 p-3 text-xs">
                    {detailDoc.project_member_names &&
                    detailDoc.project_member_names.length > 0 ? (
                      <ul className="space-y-0.5">
                        {detailDoc.project_member_names.map((n) => (
                          <li key={n} className="text-gray-800">
                            · {n}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-gray-500">
                        프로젝트에 참여 멤버가 없습니다. 관리자 페이지에서 멤버를 추가하면 여기에 표시됩니다.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {detailDoc.error_message && (
                <div className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">
                  <strong>오류: </strong>
                  {detailDoc.error_message}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {deleteDocId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setDeleteDocId(null)}
            aria-hidden="true"
          />
          <div className="relative z-50 w-full max-w-sm rounded-xl border border-gray-200 bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">문서를 삭제하시겠습니까?</h3>
            <p className="mt-2 text-sm text-gray-500">이 작업은 되돌릴 수 없습니다.</p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() => setDeleteDocId(null)}
                className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={handleDelete}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
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
