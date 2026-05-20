"use client";

import { format } from "date-fns";
import {
  Upload,
  Search,
  Trash2,
  Download,
  FileText,
  FileSpreadsheet,
  FileImage,
  File,
  Loader2,
  ChevronRight,
  ChevronDown,
  FolderOpen,
  LayoutGrid,
  Folder,
  Eye,
  Shield,
  Filter,
  Building2,
  FolderTree,
  UserPlus,
  UserMinus,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import { useDropzone } from "react-dropzone";

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

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
  uploaded_by: string;
  uploaded_by_name?: string;
  created_at: string;
  folder_id: string;
  allow_original_download: boolean;
  visibility: Visibility;
  department_id?: string;
  department_name?: string;
  project_id?: string;
  project_name?: string;
  metadata?: Record<string, unknown>;
  chunk_count?: number;
  error_message?: string;
  // 단건 조회(GET /documents/{id}) 응답에만 채워지는 표시용 부가 정보.
  // 목록 응답에는 없으므로 상세 다이얼로그를 열 때 별도로 fetch 한다.
  visible_department_names?: string[];
  project_member_names?: string[];
  visibility_summary?: string;
}

interface FolderNode {
  id: string;
  name: string;
  board_id: string;
}

interface BoardNode {
  id: string;
  name: string;
  project_id: string;
  folders: FolderNode[];
}

interface ProjectNode {
  id: string;
  name: string;
  boards: BoardNode[];
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

interface UserOption {
  id: string;
  username: string;
  email: string;
}

// ---------- Constants ----------

const VISIBILITY_OPTIONS: { value: Visibility; label: string; color: string }[] = [
  { value: "public", label: "전체 공개", color: "bg-green-100 text-green-800" },
  { value: "all_departments", label: "전부서 공개", color: "bg-blue-100 text-blue-800" },
  { value: "department_only", label: "부서 내 공개", color: "bg-cyan-100 text-cyan-800" },
  { value: "project_only", label: "프로젝트 내 공개", color: "bg-blue-100 text-blue-900" },
  { value: "confidential", label: "비밀", color: "bg-red-100 text-red-800" },
  { value: "hidden", label: "숨김", color: "bg-gray-100 text-gray-800" },
];

const SORT_OPTIONS = [
  { value: "created_at_desc", label: "최신순" },
  { value: "created_at_asc", label: "오래된순" },
  { value: "name_asc", label: "이름 오름차순" },
  { value: "name_desc", label: "이름 내림차순" },
  { value: "size_desc", label: "크기 큰순" },
  { value: "size_asc", label: "크기 작은순" },
];

function getVisibilityOption(v: Visibility) {
  return VISIBILITY_OPTIONS.find((opt) => opt.value === v) || VISIBILITY_OPTIONS[0];
}

// ---------- Helpers ----------

const MIME_TO_SHORT: Record<string, string> = {
  "application/pdf": "PDF",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PPTX",
  "application/msword": "DOC",
  "application/vnd.ms-excel": "XLS",
  "application/vnd.ms-powerpoint": "PPT",
  "application/vnd.hancom.hwp": "HWP",
  "application/haansofthwp": "HWP",
  "application/x-hwp": "HWP",
  "application/octet-stream": "HWP",
  "text/plain": "TXT",
  "text/csv": "CSV",
  "text/html": "HTML",
  "text/markdown": "MD",
  "image/png": "PNG",
  "image/jpeg": "JPEG",
  "image/tiff": "TIFF",
  "image/bmp": "BMP",
};

function shortFormat(fmt: string | undefined): string {
  if (!fmt) return "—";
  // MIME type인 경우 짧은 이름으로 변환
  if (MIME_TO_SHORT[fmt]) return MIME_TO_SHORT[fmt];
  // "application/..." 등 매핑에 없는 MIME type이면 마지막 부분 추출
  if (fmt.includes("/")) {
    const sub = fmt.split("/").pop() || fmt;
    // "vnd.xxx.yyy" → 마지막 부분, 또는 짧은 subtype
    const last = sub.split(".").pop() || sub;
    return last.toUpperCase().slice(0, 6);
  }
  // 이미 짧은 확장자인 경우
  return fmt.toUpperCase().slice(0, 6);
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function getFormatIcon(fmt: string) {
  const short = shortFormat(fmt).toLowerCase();
  if (["pdf"].includes(short)) return <FileText className="h-4 w-4 text-red-500" />;
  if (["xlsx", "xls", "csv"].includes(short))
    return <FileSpreadsheet className="h-4 w-4 text-green-600" />;
  if (["png", "jpg", "jpeg", "gif", "svg", "tiff", "bmp"].includes(short))
    return <FileImage className="h-4 w-4 text-blue-500" />;
  if (["doc", "docx", "txt", "md", "hwp", "pptx", "ppt", "html"].includes(short))
    return <FileText className="h-4 w-4 text-blue-500" />;
  return <File className="h-4 w-4 text-gray-500" />;
}

function statusBadge(status: DocumentItem["status"]) {
  switch (status) {
    case "waiting":
      return <Badge variant="warning">대기</Badge>;
    case "processing":
      return (
        <Badge variant="info" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          처리 중
        </Badge>
      );
    case "completed":
      return <Badge variant="success">완료</Badge>;
    case "error":
      return <Badge variant="destructive">오류</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

function visibilityBadge(visibility: Visibility) {
  const opt = getVisibilityOption(visibility);
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${opt.color}`}
    >
      <Shield className="h-3 w-3" />
      {opt.label}
    </span>
  );
}

// ---------- Component ----------

export default function DocumentsPage() {
  const { user } = useAuth();
  const { addToast } = useToast();

  const orgId = user?.organization_id;

  // Tree / navigation
  const [treeData, setTreeData] = useState<ProjectNode[]>([]);
  const [expandedTreeNodes, setExpandedTreeNodes] = useState<Set<string>>(new Set());
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [selectedFolderPath, setSelectedFolderPath] = useState<string>("");

  // Documents
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [treeLoading, setTreeLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Visibility filter & sort & pagination
  const [visibilityFilter, setVisibilityFilter] = useState<Visibility | "">("");
  const [sortBy, setSortBy] = useState("created_at_desc");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalDocs, setTotalDocs] = useState(0);

  // Detail dialog
  const [detailDoc, setDetailDoc] = useState<DocumentItem | null>(null);

  // Delete dialog
  const [deleteDoc, setDeleteDoc] = useState<DocumentItem | null>(null);

  // Upload
  const [uploading, setUploading] = useState(false);

  // Upload options
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<globalThis.File[]>([]);
  const [uploadVisibility, setUploadVisibility] = useState<Visibility>("department_only");
  const [uploadDeptId, setUploadDeptId] = useState<string>("");
  const [uploadProjectId, setUploadProjectId] = useState<string>("");
  const [uploadTargetType, setUploadTargetType] = useState<"department" | "project">("department");

  // Departments and projects for upload scope
  const [allDepartments, setAllDepartments] = useState<DepartmentRef[]>([]);
  const [allProjects, setAllProjects] = useState<ProjectRef[]>([]);

  // 사용자 소속 부서 + 하위 부서만 필터
  const userDepartments = (() => {
    const userDeptId = user?.department_id;
    if (!userDeptId || allDepartments.length === 0) return allDepartments;
    const userDept = allDepartments.find((d) => d.id === userDeptId);
    if (!userDept) return allDepartments;
    // 자신의 path로 시작하는 부서 = 자신 + 하위 부서
    return allDepartments.filter((d) => d.path?.startsWith(userDept.path.replace(/\/$/, "")));
  })();

  // Confidential access management
  const [accessDialogOpen, setAccessDialogOpen] = useState(false);
  const [accessDocId, setAccessDocId] = useState<string>("");
  const [accessUsers, setAccessUsers] = useState<UserOption[]>([]);
  const [allUsers, setAllUsers] = useState<UserOption[]>([]);
  const [accessLoading, setAccessLoading] = useState(false);
  const [selectedAccessUserId, setSelectedAccessUserId] = useState<string>("");

  // ---------- Fetch tree ----------

  const fetchTree = useCallback(async () => {
    try {
      const data = await apiClient.get<ProjectNode[]>("/projects/tree");
      setTreeData(data);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "폴더 트리를 불러오지 못했습니다", "error");
    } finally {
      setTreeLoading(false);
    }
  }, [addToast]);

  // ---------- Fetch documents ----------

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {
        page: String(currentPage),
        size: String(pageSize),
      };
      if (selectedFolderId) params.folder_id = selectedFolderId;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (visibilityFilter) params.visibility = visibilityFilter;
      if (sortBy) params.sort_by = sortBy;

      const response = await apiClient.get<{ items: DocumentItem[]; total: number }>(
        "/documents",
        params,
      );
      setDocuments(response.items || []);
      setTotalDocs(response.total || 0);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "문서 목록을 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [selectedFolderId, searchQuery, visibilityFilter, sortBy, currentPage, pageSize, addToast]);

  // ---------- Fetch departments and projects ----------

  const fetchDepartmentsAndProjects = useCallback(async () => {
    try {
      if (orgId) {
        const depts = await apiClient.get<DepartmentRef[]>(`/organizations/${orgId}/departments`);
        setAllDepartments(depts || []);
      }
      const projs = await apiClient.get<{ items: ProjectRef[] }>("/projects");
      setAllProjects(projs.items || []);
    } catch {
      // ignore
    }
  }, [orgId]);

  useEffect(() => {
    fetchTree();
    fetchDepartmentsAndProjects();
  }, [fetchTree, fetchDepartmentsAndProjects]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // 필터/검색어/폴더 변경 시 1페이지로 리셋
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedFolderId, searchQuery, visibilityFilter, sortBy, pageSize]);

  const totalPages = Math.max(1, Math.ceil(totalDocs / pageSize));

  // ---------- Upload ----------

  const onDrop = useCallback(
    (acceptedFiles: globalThis.File[]) => {
      setUploadFiles(acceptedFiles);
      setUploadTargetType("department");
      setUploadVisibility("department_only");
      setUploadDeptId(user?.department_id || "");
      setUploadProjectId("");
      setUploadDialogOpen(true);
    },
    [user?.department_id],
  );

  const handleUploadConfirm = async () => {
    if (uploadFiles.length === 0) return;
    setUploading(true);
    setUploadDialogOpen(false);
    try {
      const params = new URLSearchParams();
      params.set("visibility", uploadVisibility);
      if (uploadDeptId) params.set("department_id", uploadDeptId);
      if (uploadProjectId) params.set("project_id", uploadProjectId);
      if (selectedFolderId) params.set("folder_id", selectedFolderId);

      const formData = new FormData();
      const isSingle = uploadFiles.length === 1;

      if (isSingle) {
        formData.append("file", uploadFiles[0]);
      } else {
        uploadFiles.forEach((file) => formData.append("files", file));
      }

      const endpoint = isSingle
        ? `/documents/upload?${params.toString()}`
        : `/documents/bulk-upload?${params.toString()}`;

      await apiClient.upload(endpoint, formData);
      addToast(`${uploadFiles.length}개 파일이 업로드되었습니다`, "success");
      setUploadFiles([]);
      fetchDocuments();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "업로드에 실패했습니다", "error");
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: false,
  });

  // ---------- Delete ----------

  const handleDelete = async () => {
    if (!deleteDoc) return;
    try {
      await apiClient.delete(`/documents/${deleteDoc.id}`);
      addToast("문서가 삭제되었습니다", "success");
      setDeleteDoc(null);
      fetchDocuments();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "문서 삭제에 실패했습니다", "error");
    }
  };

  // ---------- 상세 다이얼로그: 단건 fetch 로 표시용 부가 정보를 가져온다 ----------

  /**
   * 카드/Eye 버튼 클릭 시 호출. 즉시 목록 정보로 다이얼로그를 열고,
   * 비동기로 GET /documents/{id} 결과(visible_department_names 등)로 보강한다.
   */
  const openDetail = async (doc: DocumentItem) => {
    setDetailDoc(doc);
    try {
      const detail = await apiClient.get<DocumentItem>(`/documents/${doc.id}`);
      // 다이얼로그가 닫힌 사이 stale 응답으로 덮어쓰지 않도록 ID 일치 확인.
      setDetailDoc((prev) => (prev && prev.id === detail.id ? detail : prev));
    } catch {
      // 부가 정보 가져오기 실패 시 목록 정보만 그대로 노출 (핵심 동작은 유지)
    }
  };

  // ---------- Download ----------

  const handleDownload = async (doc: DocumentItem) => {
    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL || "/api/v1"}/documents/${doc.id}/download`;
      window.open(url, "_blank");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "다운로드에 실패했습니다", "error");
    }
  };

  // ---------- Confidential access management ----------

  const openAccessDialog = async (doc: DocumentItem) => {
    setAccessDocId(doc.id);
    setAccessDialogOpen(true);
    setAccessLoading(true);
    try {
      const [accessData, usersData] = await Promise.all([
        apiClient.get<{ users: UserOption[] }>(`/documents/${doc.id}/access`),
        apiClient.get<{ items: UserOption[] }>("/users", { org_id: orgId! }),
      ]);
      setAccessUsers(accessData.users || []);
      setAllUsers(usersData.items || []);
    } catch {
      addToast("접근 권한 정보를 불러오지 못했습니다", "error");
    } finally {
      setAccessLoading(false);
    }
  };

  const handleAddAccess = async () => {
    if (!accessDocId || !selectedAccessUserId) return;
    try {
      await apiClient.post(`/documents/${accessDocId}/access`, {
        user_id: selectedAccessUserId,
      });
      addToast("접근 권한이 추가되었습니다", "success");
      setSelectedAccessUserId("");
      const data = await apiClient.get<{ users: UserOption[] }>(`/documents/${accessDocId}/access`);
      setAccessUsers(data.users || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "접근 권한 추가에 실패했습니다", "error");
    }
  };

  const handleRemoveAccess = async (userId: string) => {
    if (!accessDocId) return;
    try {
      await apiClient.delete(`/documents/${accessDocId}/access/${userId}`);
      setAccessUsers((prev) => prev.filter((u) => u.id !== userId));
      addToast("접근 권한이 제거되었습니다", "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "접근 권한 제거에 실패했습니다", "error");
    }
  };

  // ---------- Tree toggle ----------

  const toggleTreeNode = (nodeId: string) => {
    setExpandedTreeNodes((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  };

  const selectFolder = (folderId: string, path: string) => {
    setSelectedFolderId(folderId);
    setSelectedFolderPath(path);
  };

  // ---------- Render ----------

  return (
    <div className="flex h-[calc(100vh-4rem)] gap-0">
      {/* Left sidebar -- folder tree */}
      <div className="w-64 flex-shrink-0 border-r">
        <div className="p-4">
          <h2 className="text-muted-foreground text-sm font-semibold tracking-wider uppercase">
            폴더
          </h2>
        </div>
        <Separator />
        <ScrollArea className="h-[calc(100vh-8rem)]">
          <div className="p-2">
            {treeLoading ? (
              <div className="space-y-2 p-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-6 w-full" />
                ))}
              </div>
            ) : (
              <>
                <Button
                  variant={selectedFolderId === null ? "secondary" : "ghost"}
                  className="w-full justify-start text-sm"
                  onClick={() => {
                    setSelectedFolderId(null);
                    setSelectedFolderPath("");
                  }}
                >
                  전체 문서
                </Button>

                {treeData.map((project) => (
                  <div key={project.id}>
                    <Button
                      variant="ghost"
                      className="w-full justify-start text-sm"
                      onClick={() => toggleTreeNode(`p-${project.id}`)}
                    >
                      {expandedTreeNodes.has(`p-${project.id}`) ? (
                        <ChevronDown className="mr-1 h-3 w-3" />
                      ) : (
                        <ChevronRight className="mr-1 h-3 w-3" />
                      )}
                      <FolderOpen className="text-muted-foreground mr-1.5 h-3.5 w-3.5" />
                      <span className="truncate">{project.name}</span>
                    </Button>

                    {expandedTreeNodes.has(`p-${project.id}`) &&
                      project.boards.map((board) => (
                        <div key={board.id} className="ml-4">
                          <Button
                            variant="ghost"
                            className="w-full justify-start text-sm"
                            onClick={() => toggleTreeNode(`b-${board.id}`)}
                          >
                            {expandedTreeNodes.has(`b-${board.id}`) ? (
                              <ChevronDown className="mr-1 h-3 w-3" />
                            ) : (
                              <ChevronRight className="mr-1 h-3 w-3" />
                            )}
                            <LayoutGrid className="text-muted-foreground mr-1.5 h-3.5 w-3.5" />
                            <span className="truncate">{board.name}</span>
                          </Button>

                          {expandedTreeNodes.has(`b-${board.id}`) &&
                            board.folders.map((folder) => (
                              <Button
                                key={folder.id}
                                variant={selectedFolderId === folder.id ? "secondary" : "ghost"}
                                className="ml-4 w-[calc(100%-1rem)] justify-start text-sm"
                                onClick={() =>
                                  selectFolder(
                                    folder.id,
                                    `${project.name} / ${board.name} / ${folder.name}`,
                                  )
                                }
                              >
                                <Folder className="text-muted-foreground mr-1.5 h-3.5 w-3.5" />
                                <span className="truncate">{folder.name}</span>
                              </Button>
                            ))}
                        </div>
                      ))}
                  </div>
                ))}
              </>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="space-y-4 p-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-foreground text-2xl font-bold">문서</h1>
              {selectedFolderPath ? (
                <p className="text-muted-foreground mt-1 text-sm">{selectedFolderPath}</p>
              ) : (
                <p className="text-muted-foreground mt-1 text-sm">문서를 업로드하고 관리합니다</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => document.getElementById("file-upload-input")?.click()}
                className="bg-primary hover:bg-primary/90"
              >
                <Upload className="mr-2 h-4 w-4" />
                문서 업로드
              </Button>
            </div>
          </div>

          {/* Search + Visibility Filter */}
          <div className="flex items-center gap-3">
            <div className="relative max-w-sm flex-1">
              <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
              <Input
                placeholder="문서 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="text-muted-foreground h-4 w-4" />
              <select
                value={visibilityFilter}
                onChange={(e) => setVisibilityFilter(e.target.value as Visibility | "")}
                className="border-input bg-background ring-offset-background focus:ring-ring rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
              >
                <option value="">전체</option>
                {VISIBILITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border-input bg-background ring-offset-background focus:ring-ring rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Drag-and-drop zone */}
          <div
            {...getRootProps()}
            className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
              isDragActive
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25 hover:border-muted-foreground/50"
            }`}
          >
            <input {...getInputProps()} id="file-upload-input" />
            {uploading ? (
              <div className="flex flex-col items-center gap-2">
                <Loader2 className="text-primary h-8 w-8 animate-spin" />
                <p className="text-muted-foreground text-sm">업로드 중...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <Upload className="text-muted-foreground h-8 w-8" />
                <p className="text-muted-foreground text-sm">
                  {isDragActive
                    ? "파일을 여기에 놓으세요..."
                    : "파일을 드래그하여 놓거나 클릭하여 선택하세요"}
                </p>
                <p className="text-muted-foreground text-xs">
                  PDF, DOCX, XLSX, TXT 등을 지원합니다. 일괄 업로드 가능합니다.
                </p>
              </div>
            )}
          </div>

          {/* Documents table */}
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="space-y-3 p-6">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>이름</TableHead>
                      <TableHead className="w-20">형식</TableHead>
                      <TableHead className="w-24">크기</TableHead>
                      <TableHead className="w-28">상태</TableHead>
                      <TableHead className="w-28">공개범위</TableHead>
                      <TableHead>업로드자</TableHead>
                      <TableHead>날짜</TableHead>
                      <TableHead className="w-28">작업</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documents.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={8} className="text-muted-foreground py-8 text-center">
                          문서가 없습니다
                        </TableCell>
                      </TableRow>
                    ) : (
                      documents.map((doc) => (
                        <TableRow
                          key={doc.id}
                          className="cursor-pointer"
                          onClick={() => openDetail(doc)}
                        >
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              {getFormatIcon(doc.format)}
                              <span className="max-w-xs truncate">{doc.name}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-muted-foreground text-xs whitespace-nowrap uppercase">
                            {shortFormat(doc.format)}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {formatFileSize(doc.file_size_bytes)}
                          </TableCell>
                          <TableCell>{statusBadge(doc.status)}</TableCell>
                          <TableCell>{visibilityBadge(doc.visibility)}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {doc.uploaded_by_name || "—"}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {format(new Date(doc.created_at), "yyyy-MM-dd")}
                          </TableCell>
                          <TableCell>
                            <div
                              className="flex items-center gap-1"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8"
                                onClick={() => openDetail(doc)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              {doc.visibility === "confidential" && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  onClick={() => openAccessDialog(doc)}
                                  title="접근 권한 관리"
                                >
                                  <Shield className="h-4 w-4" />
                                </Button>
                              )}
                              {doc.allow_original_download && (
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-8 w-8"
                                  onClick={() => handleDownload(doc)}
                                >
                                  <Download className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-destructive h-8 w-8"
                                onClick={() => setDeleteDoc(doc)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              )}

              {/* Pagination */}
              {!loading && totalDocs > 0 && (
                <div className="flex items-center justify-between border-t px-4 py-3">
                  <div className="text-muted-foreground flex items-center gap-2 text-sm">
                    <span>총 {totalDocs}건</span>
                    <span className="text-muted-foreground/50">|</span>
                    <span>페이지당</span>
                    <select
                      value={pageSize}
                      onChange={(e) => setPageSize(Number(e.target.value))}
                      className="border-input bg-background rounded border px-2 py-1 text-sm"
                    >
                      {[20, 50, 100].map((n) => (
                        <option key={n} value={n}>
                          {n}건
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage <= 1}
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    >
                      이전
                    </Button>
                    <span className="text-muted-foreground px-3 text-sm">
                      {currentPage} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={currentPage >= totalPages}
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    >
                      다음
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ---- Upload Options Dialog ---- */}
      <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>업로드 옵션</DialogTitle>
            <DialogDescription>
              {uploadFiles.length}개 파일의 공개범위와 대상을 설정합니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            {/* Upload target type selection */}
            <div className="flex gap-2">
              <Button
                variant={uploadTargetType === "department" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setUploadTargetType("department");
                  setUploadVisibility("department_only");
                  setUploadProjectId("");
                }}
              >
                <Building2 className="mr-1.5 h-4 w-4" />
                부서
              </Button>
              <Button
                variant={uploadTargetType === "project" ? "default" : "outline"}
                size="sm"
                onClick={() => {
                  setUploadTargetType("project");
                  setUploadVisibility("project_only");
                  setUploadDeptId("");
                }}
              >
                <FolderTree className="mr-1.5 h-4 w-4" />
                프로젝트
              </Button>
            </div>

            {/* 공개범위 - 대상에 따라 옵션 제한 */}
            <div className="space-y-2">
              <Label>공개범위</Label>
              <select
                value={uploadVisibility}
                onChange={(e) => {
                  const v = e.target.value as Visibility;
                  setUploadVisibility(v);
                  if (v === "public") setUploadDeptId("");
                }}
                className="border-input bg-background ring-offset-background focus:ring-ring w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
              >
                {uploadTargetType === "department" ? (
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

            {/* 부서 선택 - 부서 대상 + 전체공개 아닐 때만 표시 */}
            {uploadTargetType === "department" && uploadVisibility !== "public" && (
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Building2 className="h-3.5 w-3.5" />
                  대상 부서
                </Label>
                <select
                  value={uploadDeptId}
                  onChange={(e) => setUploadDeptId(e.target.value)}
                  className="border-input bg-background ring-offset-background focus:ring-ring w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
                >
                  <option value="">부서를 선택하세요</option>
                  {userDepartments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {"─".repeat(dept.depth || 0)} {dept.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* 프로젝트 선택 */}
            {uploadTargetType === "project" && (
              <>
                <div className="space-y-2">
                  <Label className="flex items-center gap-1">
                    <FolderTree className="h-3.5 w-3.5" />
                    대상 프로젝트
                  </Label>
                  <select
                    value={uploadProjectId}
                    onChange={(e) => setUploadProjectId(e.target.value)}
                    className="border-input bg-background ring-offset-background focus:ring-ring w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
                  >
                    <option value="">프로젝트를 선택하세요</option>
                    {allProjects.map((proj) => (
                      <option key={proj.id} value={proj.id}>
                        {proj.name}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedFolderId && selectedFolderPath && (
                  <div className="space-y-2">
                    <Label className="flex items-center gap-1">
                      <Folder className="h-3.5 w-3.5" />
                      대상 폴더
                    </Label>
                    <div className="border-input bg-muted/50 text-muted-foreground rounded-md border px-3 py-2 text-sm">
                      {selectedFolderPath}
                    </div>
                  </div>
                )}
              </>
            )}

            <div className="bg-muted text-muted-foreground rounded-md p-3 text-xs">
              <p className="font-medium">업로드 파일:</p>
              <ul className="mt-1 space-y-0.5">
                {uploadFiles.map((f, i) => (
                  <li key={i}>{f.name}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setUploadDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleUploadConfirm}>
              <Upload className="mr-2 h-4 w-4" />
              업로드
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* ---- Document Detail Dialog ---- */}
      <Dialog open={!!detailDoc} onOpenChange={() => setDetailDoc(null)}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {detailDoc && getFormatIcon(detailDoc.format)}
              {detailDoc?.name}
            </DialogTitle>
            <DialogDescription>문서 상세 정보</DialogDescription>
          </DialogHeader>
          {detailDoc && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground font-medium">형식</span>
                  <p className="uppercase">{shortFormat(detailDoc.format)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground font-medium">크기</span>
                  <p>{formatFileSize(detailDoc.file_size_bytes)}</p>
                </div>
                <div>
                  <span className="text-muted-foreground font-medium">상태</span>
                  <div className="mt-1">{statusBadge(detailDoc.status)}</div>
                </div>
                <div>
                  <span className="text-muted-foreground font-medium">공개범위</span>
                  <div className="mt-1">{visibilityBadge(detailDoc.visibility)}</div>
                </div>
                <div>
                  <span className="text-muted-foreground font-medium">업로드자</span>
                  {/* 백엔드 단건 조회 응답의 uploaded_by_name (한글 사용자명).
                      미반영 시(목록 첫 클릭 직후 짧은 순간 등) UUID 대신 "—" 로 표시. */}
                  <p>{detailDoc.uploaded_by_name || "—"}</p>
                </div>
                <div>
                  <span className="text-muted-foreground font-medium">업로드일</span>
                  <p>{format(new Date(detailDoc.created_at), "yyyy-MM-dd HH:mm")}</p>
                </div>
                <div>
                  <span className="text-muted-foreground font-medium">청크 수</span>
                  <p>{detailDoc.chunk_count ?? "N/A"}</p>
                </div>
                {detailDoc.department_name && (
                  <div>
                    <span className="text-muted-foreground font-medium">부서</span>
                    <p>{detailDoc.department_name}</p>
                  </div>
                )}
                {detailDoc.project_name && (
                  <div>
                    <span className="text-muted-foreground font-medium">프로젝트</span>
                    <p>{detailDoc.project_name}</p>
                  </div>
                )}
              </div>

              {/* 공개 범위 — 한 줄 요약 + 상세 대상 목록.
                  visibility 별로 다른 정보를 표시한다.
                  - department_only / all_departments → 가시 부서 이름들
                  - project_only → 프로젝트 멤버 이름들 */}
              {detailDoc.visibility_summary && (
                <div className="rounded-md border bg-muted/30 p-3 text-sm">
                  <div className="text-muted-foreground mb-1 text-xs font-medium">공개 범위</div>
                  <p className="font-medium">{detailDoc.visibility_summary}</p>
                </div>
              )}

              {(detailDoc.visibility === "department_only" ||
                detailDoc.visibility === "all_departments") && (
                <div>
                  <h4 className="text-muted-foreground mb-2 text-sm font-medium">
                    공개 대상 부서{" "}
                    <span className="text-xs">
                      ({detailDoc.visible_department_names?.length ?? 0}개)
                    </span>
                  </h4>
                  <div className="bg-muted max-h-40 overflow-auto rounded-md p-3 text-xs">
                    {detailDoc.visible_department_names &&
                    detailDoc.visible_department_names.length > 0 ? (
                      <ul className="space-y-0.5">
                        {detailDoc.visible_department_names.map((n) => (
                          <li key={n}>· {n}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted-foreground">
                        공개 대상 부서 정보 없음 (목록 조회 후 잠시만 기다려주세요)
                      </p>
                    )}
                  </div>
                </div>
              )}

              {detailDoc.visibility === "project_only" && (
                <div>
                  <h4 className="text-muted-foreground mb-2 text-sm font-medium">
                    공개 대상 사용자{" "}
                    <span className="text-xs">
                      ({detailDoc.project_member_names?.length ?? 0}명)
                    </span>
                  </h4>
                  <div className="bg-muted max-h-40 overflow-auto rounded-md p-3 text-xs">
                    {detailDoc.project_member_names &&
                    detailDoc.project_member_names.length > 0 ? (
                      <ul className="space-y-0.5">
                        {detailDoc.project_member_names.map((n) => (
                          <li key={n}>· {n}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-muted-foreground">
                        프로젝트에 직접/부서 참여 멤버가 없습니다. 관리자 페이지에서 멤버를 추가하면 표시됩니다.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {detailDoc.error_message && (
                <div className="bg-destructive/10 text-destructive rounded-md p-3 text-sm">
                  <strong>오류:</strong> {detailDoc.error_message}
                </div>
              )}

              {detailDoc.metadata && Object.keys(detailDoc.metadata).length > 0 && (
                <div>
                  <h4 className="text-muted-foreground mb-2 text-sm font-medium">메타데이터</h4>
                  <pre className="bg-muted max-h-40 overflow-auto rounded-md p-3 text-xs">
                    {JSON.stringify(detailDoc.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* ---- Confidential Access Dialog ---- */}
      <Dialog open={accessDialogOpen} onOpenChange={setAccessDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              접근 권한 관리
            </DialogTitle>
            <DialogDescription>비밀 문서에 대한 사용자 접근 권한을 관리합니다.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <select
                value={selectedAccessUserId}
                onChange={(e) => setSelectedAccessUserId(e.target.value)}
                className="border-input bg-background ring-offset-background focus:ring-ring flex-1 rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
              >
                <option value="">사용자를 선택하세요</option>
                {allUsers
                  .filter((u) => !accessUsers.some((au) => au.id === u.id))
                  .map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.username} ({u.email})
                    </option>
                  ))}
              </select>
              <Button onClick={handleAddAccess} disabled={!selectedAccessUserId} size="sm">
                <UserPlus className="mr-1 h-4 w-4" />
                추가
              </Button>
            </div>

            {accessLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 2 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : accessUsers.length === 0 ? (
              <div className="text-muted-foreground rounded-lg border border-dashed py-6 text-center text-sm">
                접근 권한이 부여된 사용자가 없습니다
              </div>
            ) : (
              <div className="max-h-60 space-y-2 overflow-y-auto">
                {accessUsers.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between rounded-lg border px-3 py-2"
                  >
                    <div>
                      <p className="text-sm font-medium">{u.username}</p>
                      <p className="text-muted-foreground text-xs">{u.email}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive h-7 w-7"
                      onClick={() => handleRemoveAccess(u.id)}
                      aria-label="접근 권한 제거"
                    >
                      <UserMinus className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* ---- Delete Confirmation ---- */}
      <AlertDialog open={!!deleteDoc} onOpenChange={() => setDeleteDoc(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>문서를 삭제하시겠습니까?</AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{deleteDoc?.name}&quot; 문서를 삭제합니다. 이 작업은 되돌릴 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>삭제</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
