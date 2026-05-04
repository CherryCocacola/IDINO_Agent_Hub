"use client";

import { format } from "date-fns";
import {
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  Trash2,
  ChevronRight,
  ChevronDown,
  FolderOpen,
  LayoutGrid,
  Folder,
  Users,
  UserPlus,
  UserMinus,
  Building2,
  Crown,
  Loader2,
} from "lucide-react";
import { useState, useEffect, useCallback, Fragment } from "react";

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
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

interface FolderItem {
  id: string;
  name: string;
  board_id: string;
  created_at: string;
}

interface Board {
  id: string;
  name: string;
  project_id: string;
  folders: FolderItem[];
  created_at: string;
}

interface DepartmentRef {
  id: string;
  name: string;
  parent_id: string | null;
  depth: number;
}

interface ProjectMember {
  id: string;
  user_id: string;
  username: string;
  email: string;
  role: string;
  is_manager: boolean;
}

interface Project {
  id: string;
  name: string;
  description: string;
  allow_original_download: boolean;
  doc_count: number;
  boards: Board[];
  departments: DepartmentRef[];
  created_at: string;
}

interface ProjectFormData {
  name: string;
  description: string;
  allow_original_download: boolean;
  department_ids: string[];
}

interface BoardFormData {
  name: string;
}

interface FolderFormData {
  name: string;
}

interface UserOption {
  id: string;
  username: string;
  email: string;
}

const emptyProjectForm: ProjectFormData = {
  name: "",
  description: "",
  allow_original_download: false,
  department_ids: [],
};

// ---------- Component ----------

export default function ProjectsPage() {
  const { user } = useAuth();
  const { addToast } = useToast();

  const orgId = user?.organization_id;

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // All departments for multi-select
  const [allDepartments, setAllDepartments] = useState<DepartmentRef[]>([]);

  // Project dialog
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectForm, setProjectForm] = useState<ProjectFormData>(emptyProjectForm);
  const [projectSaving, setProjectSaving] = useState(false);

  // Board dialog
  const [boardDialogOpen, setBoardDialogOpen] = useState(false);
  const [editingBoard, setEditingBoard] = useState<Board | null>(null);
  const [boardParentProjectId, setBoardParentProjectId] = useState<string>("");
  const [boardForm, setBoardForm] = useState<BoardFormData>({ name: "" });
  const [boardSaving, setBoardSaving] = useState(false);

  // Folder dialog
  const [folderDialogOpen, setFolderDialogOpen] = useState(false);
  const [editingFolder, setEditingFolder] = useState<FolderItem | null>(null);
  const [folderParentBoardId, setFolderParentBoardId] = useState<string>("");
  const [folderForm, setFolderForm] = useState<FolderFormData>({ name: "" });
  const [folderSaving, setFolderSaving] = useState(false);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<{
    type: "project" | "board" | "folder";
    id: string;
    name: string;
    parentId?: string;
  } | null>(null);

  // Expanded rows
  const [expandedProjects, setExpandedProjects] = useState<Set<string>>(new Set());
  const [expandedBoards, setExpandedBoards] = useState<Set<string>>(new Set());

  // Members dialog
  const [membersDialogOpen, setMembersDialogOpen] = useState(false);
  const [membersProjectId, setMembersProjectId] = useState<string>("");
  const [membersProjectName, setMembersProjectName] = useState<string>("");
  const [projectMembers, setProjectMembers] = useState<ProjectMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);

  // Add member
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [allUsers, setAllUsers] = useState<UserOption[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [selectedAddUserId, setSelectedAddUserId] = useState<string>("");
  const [addAsManager, setAddAsManager] = useState(false);
  const [memberSearchQuery, setMemberSearchQuery] = useState("");
  const [addMemberSaving, setAddMemberSaving] = useState(false);

  // Breadcrumb
  const [breadcrumb, setBreadcrumb] = useState<string[]>(["프로젝트"]);

  // ---------- Fetch ----------

  const fetchProjects = useCallback(async () => {
    try {
      const response = await apiClient.get<{ items: Project[]; total: number }>("/projects");
      setProjects(response.items || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "프로젝트 목록을 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const fetchDepartments = useCallback(async () => {
    if (!orgId) return;
    try {
      const data = await apiClient.get<DepartmentRef[]>(`/organizations/${orgId}/departments`);
      setAllDepartments(data || []);
    } catch {
      // ignore
    }
  }, [orgId]);

  useEffect(() => {
    fetchProjects();
    fetchDepartments();
  }, [fetchProjects, fetchDepartments]);

  // ---------- Project CRUD ----------

  const openCreateProject = () => {
    setEditingProject(null);
    setProjectForm(emptyProjectForm);
    setProjectDialogOpen(true);
  };

  const openEditProject = (project: Project) => {
    setEditingProject(project);
    setProjectForm({
      name: project.name,
      description: project.description,
      allow_original_download: project.allow_original_download,
      department_ids: project.departments?.map((d) => d.id) || [],
    });
    setProjectDialogOpen(true);
  };

  const handleSaveProject = async () => {
    if (!projectForm.name.trim()) {
      addToast("프로젝트 이름을 입력해주세요", "error");
      return;
    }
    setProjectSaving(true);
    try {
      if (editingProject) {
        await apiClient.put(`/projects/${editingProject.id}`, projectForm);
        addToast("프로젝트가 수정되었습니다", "success");
      } else {
        await apiClient.post("/projects", projectForm);
        addToast("프로젝트가 생성되었습니다", "success");
      }
      setProjectDialogOpen(false);
      fetchProjects();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "프로젝트 저장에 실패했습니다", "error");
    } finally {
      setProjectSaving(false);
    }
  };

  // ---------- Board CRUD ----------

  const openCreateBoard = (projectId: string) => {
    setEditingBoard(null);
    setBoardParentProjectId(projectId);
    setBoardForm({ name: "" });
    setBoardDialogOpen(true);
  };

  const openEditBoard = (board: Board) => {
    setEditingBoard(board);
    setBoardParentProjectId(board.project_id);
    setBoardForm({ name: board.name });
    setBoardDialogOpen(true);
  };

  const handleSaveBoard = async () => {
    if (!boardForm.name.trim()) {
      addToast("보드 이름을 입력해주세요", "error");
      return;
    }
    setBoardSaving(true);
    try {
      if (editingBoard) {
        await apiClient.put(
          `/projects/${boardParentProjectId}/boards/${editingBoard.id}`,
          boardForm,
        );
        addToast("보드가 수정되었습니다", "success");
      } else {
        await apiClient.post(`/projects/${boardParentProjectId}/boards`, boardForm);
        addToast("보드가 생성되었습니다", "success");
      }
      setBoardDialogOpen(false);
      fetchProjects();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "보드 저장에 실패했습니다", "error");
    } finally {
      setBoardSaving(false);
    }
  };

  // ---------- Folder CRUD ----------

  const openCreateFolder = (boardId: string) => {
    setEditingFolder(null);
    setFolderParentBoardId(boardId);
    setFolderForm({ name: "" });
    setFolderDialogOpen(true);
  };

  const openEditFolder = (folder: FolderItem) => {
    setEditingFolder(folder);
    setFolderParentBoardId(folder.board_id);
    setFolderForm({ name: folder.name });
    setFolderDialogOpen(true);
  };

  const handleSaveFolder = async () => {
    if (!folderForm.name.trim()) {
      addToast("폴더 이름을 입력해주세요", "error");
      return;
    }
    setFolderSaving(true);
    try {
      if (editingFolder) {
        await apiClient.put(
          `/boards/${folderParentBoardId}/folders/${editingFolder.id}`,
          folderForm,
        );
        addToast("폴더가 수정되었습니다", "success");
      } else {
        await apiClient.post(`/boards/${folderParentBoardId}/folders`, folderForm);
        addToast("폴더가 생성되었습니다", "success");
      }
      setFolderDialogOpen(false);
      fetchProjects();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "폴더 저장에 실패했습니다", "error");
    } finally {
      setFolderSaving(false);
    }
  };

  // ---------- Delete ----------

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      if (deleteTarget.type === "project") {
        await apiClient.delete(`/projects/${deleteTarget.id}`);
      } else if (deleteTarget.type === "board") {
        await apiClient.delete(`/projects/${deleteTarget.parentId}/boards/${deleteTarget.id}`);
      } else {
        await apiClient.delete(`/boards/${deleteTarget.parentId}/folders/${deleteTarget.id}`);
      }
      addToast("삭제되었습니다", "success");
      setDeleteTarget(null);
      fetchProjects();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "삭제에 실패했습니다", "error");
    }
  };

  // ---------- Members ----------

  const openMembersDialog = async (project: Project) => {
    setMembersProjectId(project.id);
    setMembersProjectName(project.name);
    setMembersDialogOpen(true);
    setMembersLoading(true);
    try {
      const data = await apiClient.get<ProjectMember[] | { members: ProjectMember[] }>(
        `/projects/${project.id}/members`,
      );
      setProjectMembers(Array.isArray(data) ? data : data.members || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "멤버 목록을 불러오지 못했습니다", "error");
    } finally {
      setMembersLoading(false);
    }
  };

  const fetchAllUsers = useCallback(async () => {
    if (!orgId) return;
    setUsersLoading(true);
    try {
      const data = await apiClient.get<{ items: UserOption[] }>("/users/", { org_id: orgId });
      setAllUsers(data.items || []);
    } catch {
      // ignore
    } finally {
      setUsersLoading(false);
    }
  }, [orgId]);

  const openAddMember = () => {
    setSelectedAddUserId("");
    setAddAsManager(false);
    setMemberSearchQuery("");
    setAddMemberDialogOpen(true);
    fetchAllUsers();
  };

  const handleAddMember = async () => {
    if (!membersProjectId || !selectedAddUserId) return;
    setAddMemberSaving(true);
    try {
      await apiClient.post(`/projects/${membersProjectId}/members`, {
        user_id: selectedAddUserId,
        role: addAsManager ? "manager" : "member",
      });
      addToast("멤버가 추가되었습니다", "success");
      setAddMemberDialogOpen(false);
      // Refresh members
      const data = await apiClient.get<{ members: ProjectMember[] }>(
        `/projects/${membersProjectId}/members`,
      );
      setProjectMembers(data.members || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "멤버 추가에 실패했습니다", "error");
    } finally {
      setAddMemberSaving(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!membersProjectId) return;
    try {
      await apiClient.delete(`/projects/${membersProjectId}/members/${userId}`);
      addToast("멤버가 제거되었습니다", "success");
      setProjectMembers((prev) => prev.filter((m) => m.id !== userId));
    } catch (err) {
      addToast(err instanceof Error ? err.message : "멤버 제거에 실패했습니다", "error");
    }
  };

  // ---------- Department multi-select toggle ----------

  const getDescendantIds = (parentId: string): string[] => {
    const children = allDepartments.filter((d) => d.parent_id === parentId);
    return children.flatMap((c) => [c.id, ...getDescendantIds(c.id)]);
  };

  const toggleDepartment = (deptId: string) => {
    setProjectForm((prev) => {
      const isSelected = prev.department_ids.includes(deptId);
      const descendantIds = getDescendantIds(deptId);
      const targetIds = [deptId, ...descendantIds];

      if (isSelected) {
        // 해제: 자신 + 하위 부서 모두 해제
        return {
          ...prev,
          department_ids: prev.department_ids.filter((id) => !targetIds.includes(id)),
        };
      } else {
        // 선택: 자신 + 하위 부서 모두 선택
        const merged = new Set([...prev.department_ids, ...targetIds]);
        return { ...prev, department_ids: Array.from(merged) };
      }
    });
  };

  // ---------- Expand / collapse ----------

  const toggleProjectExpand = (id: string, projectName: string) => {
    setExpandedProjects((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        setBreadcrumb(["프로젝트"]);
      } else {
        next.add(id);
        setBreadcrumb(["프로젝트", projectName]);
      }
      return next;
    });
  };

  const toggleBoardExpand = (id: string, projectName: string, boardName: string) => {
    setExpandedBoards((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        setBreadcrumb(["프로젝트", projectName]);
      } else {
        next.add(id);
        setBreadcrumb(["프로젝트", projectName, boardName]);
      }
      return next;
    });
  };

  // ---------- Filter ----------

  const filteredProjects = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="text-muted-foreground flex items-center space-x-1 text-sm">
        {breadcrumb.map((crumb, idx) => (
          <span key={idx} className="flex items-center">
            {idx > 0 && <ChevronRight className="mx-1 h-4 w-4" />}
            <span className={idx === breadcrumb.length - 1 ? "text-foreground font-medium" : ""}>
              {crumb}
            </span>
          </span>
        ))}
      </nav>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">프로젝트</h1>
          <p className="text-muted-foreground mt-1 text-sm">프로젝트, 보드, 폴더를 관리합니다</p>
        </div>
        <Button onClick={openCreateProject} className="bg-primary hover:bg-primary/90">
          <Plus className="mr-2 h-4 w-4" />
          프로젝트 생성
        </Button>
      </div>

      {/* Search bar */}
      <div className="relative max-w-sm">
        <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
        <Input
          placeholder="프로젝트 검색..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Table */}
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
                  <TableHead className="w-10" />
                  <TableHead>이름</TableHead>
                  <TableHead>설명</TableHead>
                  <TableHead>참여 부서</TableHead>
                  <TableHead className="text-center">문서</TableHead>
                  <TableHead>생성일</TableHead>
                  <TableHead className="w-12" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProjects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-muted-foreground py-8 text-center">
                      프로젝트가 없습니다
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredProjects.map((project) => (
                    <Fragment key={project.id}>
                      {/* Project row */}
                      <TableRow className="cursor-pointer">
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => toggleProjectExpand(project.id, project.name)}
                          >
                            {expandedProjects.has(project.id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </Button>
                        </TableCell>
                        <TableCell className="font-medium">{project.name}</TableCell>
                        <TableCell className="text-muted-foreground max-w-xs truncate">
                          {project.description}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {project.departments?.length > 0 ? (
                              project.departments.map((dept) => (
                                <Badge key={dept.id} variant="secondary" className="text-[10px]">
                                  <Building2 className="mr-1 h-3 w-3" />
                                  {dept.name}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-muted-foreground text-xs">-</span>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-center">{project.doc_count}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {format(new Date(project.created_at), "yyyy-MM-dd")}
                        </TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => openEditProject(project)}>
                                <Pencil className="mr-2 h-4 w-4" />
                                수정
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => openMembersDialog(project)}>
                                <Users className="mr-2 h-4 w-4" />
                                멤버 관리
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => openCreateBoard(project.id)}>
                                <LayoutGrid className="mr-2 h-4 w-4" />
                                보드 추가
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() =>
                                  setDeleteTarget({
                                    type: "project",
                                    id: project.id,
                                    name: project.name,
                                  })
                                }
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                삭제
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>

                      {/* Expanded boards */}
                      {expandedProjects.has(project.id) &&
                        project.boards?.map((board) => (
                          <Fragment key={board.id}>
                            <TableRow className="bg-muted/30">
                              <TableCell />
                              <TableCell colSpan={4}>
                                <div className="flex items-center pl-6">
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="mr-2 h-6 w-6"
                                    onClick={() =>
                                      toggleBoardExpand(board.id, project.name, board.name)
                                    }
                                  >
                                    {expandedBoards.has(board.id) ? (
                                      <ChevronDown className="h-3 w-3" />
                                    ) : (
                                      <ChevronRight className="h-3 w-3" />
                                    )}
                                  </Button>
                                  <LayoutGrid className="text-muted-foreground mr-2 h-4 w-4" />
                                  <span className="font-medium">{board.name}</span>
                                </div>
                              </TableCell>
                              <TableCell className="text-muted-foreground">
                                {format(new Date(board.created_at), "yyyy-MM-dd")}
                              </TableCell>
                              <TableCell>
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="icon" className="h-7 w-7">
                                      <MoreHorizontal className="h-4 w-4" />
                                    </Button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={() => openEditBoard(board)}>
                                      <Pencil className="mr-2 h-4 w-4" />
                                      수정
                                    </DropdownMenuItem>
                                    <DropdownMenuItem onClick={() => openCreateFolder(board.id)}>
                                      <FolderOpen className="mr-2 h-4 w-4" />
                                      폴더 추가
                                    </DropdownMenuItem>
                                    <DropdownMenuItem
                                      className="text-destructive"
                                      onClick={() =>
                                        setDeleteTarget({
                                          type: "board",
                                          id: board.id,
                                          name: board.name,
                                          parentId: project.id,
                                        })
                                      }
                                    >
                                      <Trash2 className="mr-2 h-4 w-4" />
                                      삭제
                                    </DropdownMenuItem>
                                  </DropdownMenuContent>
                                </DropdownMenu>
                              </TableCell>
                            </TableRow>

                            {/* Expanded folders */}
                            {expandedBoards.has(board.id) &&
                              board.folders?.map((folder) => (
                                <TableRow key={folder.id} className="bg-muted/10">
                                  <TableCell />
                                  <TableCell colSpan={4}>
                                    <div className="flex items-center pl-14">
                                      <Folder className="text-muted-foreground mr-2 h-4 w-4" />
                                      <span>{folder.name}</span>
                                    </div>
                                  </TableCell>
                                  <TableCell className="text-muted-foreground">
                                    {format(new Date(folder.created_at), "yyyy-MM-dd")}
                                  </TableCell>
                                  <TableCell>
                                    <DropdownMenu>
                                      <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" size="icon" className="h-7 w-7">
                                          <MoreHorizontal className="h-4 w-4" />
                                        </Button>
                                      </DropdownMenuTrigger>
                                      <DropdownMenuContent align="end">
                                        <DropdownMenuItem onClick={() => openEditFolder(folder)}>
                                          <Pencil className="mr-2 h-4 w-4" />
                                          수정
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                          className="text-destructive"
                                          onClick={() =>
                                            setDeleteTarget({
                                              type: "folder",
                                              id: folder.id,
                                              name: folder.name,
                                              parentId: board.id,
                                            })
                                          }
                                        >
                                          <Trash2 className="mr-2 h-4 w-4" />
                                          삭제
                                        </DropdownMenuItem>
                                      </DropdownMenuContent>
                                    </DropdownMenu>
                                  </TableCell>
                                </TableRow>
                              ))}
                          </Fragment>
                        ))}
                    </Fragment>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* ---- Project Dialog ---- */}
      <Dialog open={projectDialogOpen} onOpenChange={setProjectDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingProject ? "프로젝트 수정" : "프로젝트 생성"}</DialogTitle>
            <DialogDescription>
              {editingProject ? "프로젝트 정보를 수정합니다." : "새 프로젝트를 생성합니다."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="project-name">이름</Label>
              <Input
                id="project-name"
                value={projectForm.name}
                onChange={(e) => setProjectForm((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="프로젝트 이름을 입력하세요"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-desc">설명</Label>
              <Textarea
                id="project-desc"
                value={projectForm.description}
                onChange={(e) =>
                  setProjectForm((prev) => ({ ...prev, description: e.target.value }))
                }
                placeholder="프로젝트 설명을 입력하세요"
              />
            </div>
            <div className="space-y-2">
              <Label>참여 부서</Label>
              <div className="max-h-40 overflow-y-auto rounded-md border p-2">
                {allDepartments.length === 0 ? (
                  <p className="text-muted-foreground py-2 text-center text-xs">
                    등록된 부서가 없습니다
                  </p>
                ) : (
                  <div className="space-y-1">
                    {allDepartments.map((dept) => (
                      <label
                        key={dept.id}
                        className="hover:bg-muted flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm"
                        style={{ paddingLeft: `${(dept.depth || 0) * 20 + 8}px` }}
                      >
                        <input
                          type="checkbox"
                          checked={projectForm.department_ids.includes(dept.id)}
                          onChange={() => toggleDepartment(dept.id)}
                          className="text-primary focus:ring-primary h-4 w-4 rounded border-gray-300"
                        />
                        <Building2 className="text-muted-foreground h-3.5 w-3.5" />
                        {dept.name}
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="allow-download"
                checked={projectForm.allow_original_download}
                onCheckedChange={(checked) =>
                  setProjectForm((prev) => ({
                    ...prev,
                    allow_original_download: checked,
                  }))
                }
              />
              <Label htmlFor="allow-download">원본 문서 다운로드 허용</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setProjectDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSaveProject} disabled={projectSaving}>
              {projectSaving ? "저장 중..." : editingProject ? "수정" : "생성"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Board Dialog ---- */}
      <Dialog open={boardDialogOpen} onOpenChange={setBoardDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingBoard ? "보드 수정" : "보드 생성"}</DialogTitle>
            <DialogDescription>
              {editingBoard ? "보드 이름을 수정합니다." : "새 보드의 이름을 입력하세요."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="board-name">이름</Label>
              <Input
                id="board-name"
                value={boardForm.name}
                onChange={(e) => setBoardForm({ name: e.target.value })}
                placeholder="보드 이름을 입력하세요"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBoardDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSaveBoard} disabled={boardSaving}>
              {boardSaving ? "저장 중..." : editingBoard ? "수정" : "생성"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Folder Dialog ---- */}
      <Dialog open={folderDialogOpen} onOpenChange={setFolderDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingFolder ? "폴더 수정" : "폴더 생성"}</DialogTitle>
            <DialogDescription>
              {editingFolder ? "폴더 이름을 수정합니다." : "새 폴더의 이름을 입력하세요."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="folder-name">이름</Label>
              <Input
                id="folder-name"
                value={folderForm.name}
                onChange={(e) => setFolderForm({ name: e.target.value })}
                placeholder="폴더 이름을 입력하세요"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFolderDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSaveFolder} disabled={folderSaving}>
              {folderSaving ? "저장 중..." : editingFolder ? "수정" : "생성"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Members Dialog ---- */}
      <Dialog open={membersDialogOpen} onOpenChange={setMembersDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              {membersProjectName} - 멤버 관리
            </DialogTitle>
            <DialogDescription>프로젝트 멤버를 추가하거나 제거합니다.</DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground text-sm">
                {projectMembers.length}명의 멤버
              </span>
              <Button onClick={openAddMember} variant="outline" size="sm">
                <UserPlus className="mr-2 h-4 w-4" />
                멤버 추가
              </Button>
            </div>
            {membersLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : projectMembers.length === 0 ? (
              <div className="text-muted-foreground rounded-lg border border-dashed py-6 text-center text-sm">
                등록된 멤버가 없습니다
              </div>
            ) : (
              <div className="max-h-80 space-y-2 overflow-y-auto">
                {projectMembers.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between rounded-lg border px-4 py-3"
                  >
                    <div>
                      <p className="text-foreground text-sm font-medium">
                        {member.username}
                        {member.is_manager && (
                          <Badge variant="info" className="ml-2 text-[10px]">
                            <Crown className="mr-1 h-3 w-3" />
                            프로젝트 매니저
                          </Badge>
                        )}
                      </p>
                      <p className="text-muted-foreground text-xs">{member.email}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive h-8 w-8"
                      onClick={() => handleRemoveMember(member.id)}
                      aria-label="멤버 제거"
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

      {/* ---- Add Member to Project Dialog ---- */}
      <Dialog open={addMemberDialogOpen} onOpenChange={setAddMemberDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>멤버 추가</DialogTitle>
            <DialogDescription>프로젝트에 멤버를 추가합니다.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="add-project-member">사용자 선택</Label>
              {usersLoading ? (
                <div className="text-muted-foreground flex items-center gap-2 py-2 text-sm">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  사용자 목록 로딩 중...
                </div>
              ) : (
                <>
                  <div className="relative">
                    <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
                    <Input
                      placeholder="이름 또는 이메일로 검색..."
                      value={memberSearchQuery}
                      onChange={(e) => setMemberSearchQuery(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <select
                    id="add-project-member"
                    value={selectedAddUserId}
                    onChange={(e) => setSelectedAddUserId(e.target.value)}
                    className="border-input bg-background ring-offset-background focus:ring-ring w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
                    size={6}
                  >
                    <option value="">사용자를 선택하세요</option>
                    {allUsers
                      .filter((u) => !projectMembers.some((m) => m.user_id === u.id))
                      .filter((u) => {
                        if (!memberSearchQuery.trim()) return true;
                        const q = memberSearchQuery.toLowerCase();
                        return (
                          u.username.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
                        );
                      })
                      .map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.username} ({u.email})
                        </option>
                      ))}
                  </select>
                </>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Switch id="is-manager" checked={addAsManager} onCheckedChange={setAddAsManager} />
              <Label htmlFor="is-manager">프로젝트 매니저로 지정</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddMemberDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleAddMember} disabled={addMemberSaving || !selectedAddUserId}>
              {addMemberSaving ? "추가 중..." : "추가"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Delete Confirmation ---- */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {deleteTarget?.type === "project"
                ? "프로젝트"
                : deleteTarget?.type === "board"
                  ? "보드"
                  : "폴더"}
              를 삭제하시겠습니까?
            </AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{deleteTarget?.name}&quot;을(를) 삭제합니다. 이 작업은 되돌릴 수 없습니다.
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
