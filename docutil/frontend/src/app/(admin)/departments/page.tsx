"use client";

import {
  Plus,
  Search,
  Pencil,
  Trash2,
  ChevronRight,
  ChevronDown,
  Building2,
  Users,
  UserPlus,
  UserMinus,
  Crown,
  Loader2,
  Check,
  X,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";

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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

interface Department {
  id: string;
  name: string;
  parent_id: string | null;
  head_user_id: string | null;
  head_user_name: string | null;
  member_count: number;
  children: Department[];
}

interface DepartmentMember {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface UserOption {
  id: string;
  username: string;
  email: string;
}

interface DepartmentFormData {
  name: string;
  parent_id: string | null;
}

// ---------- Helpers ----------

function flattenDepartments(departments: Department[]): Department[] {
  const result: Department[] = [];
  function walk(deps: Department[]) {
    for (const d of deps) {
      result.push(d);
      if (d.children?.length) walk(d.children);
    }
  }
  walk(departments);
  return result;
}

// ---------- Component ----------

export default function DepartmentsPage() {
  const { user } = useAuth();
  const { addToast } = useToast();

  const orgId = user?.organization_id;

  // 조직(회사) 이름
  const [orgName, setOrgName] = useState<string>("");
  const [orgExpanded, setOrgExpanded] = useState(true);

  // 회사명 인라인 수정 상태
  const [orgEditing, setOrgEditing] = useState(false);
  const [orgEditName, setOrgEditName] = useState("");
  const [orgEditSaving, setOrgEditSaving] = useState(false);

  // Tree data
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  // Selected department for detail
  const [selectedDeptId, setSelectedDeptId] = useState<string | null>(null);
  const [members, setMembers] = useState<DepartmentMember[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);

  // Department CRUD dialog
  const [deptDialogOpen, setDeptDialogOpen] = useState(false);
  const [editingDept, setEditingDept] = useState<Department | null>(null);
  const [deptForm, setDeptForm] = useState<DepartmentFormData>({ name: "", parent_id: null });
  const [deptSaving, setDeptSaving] = useState(false);

  // Delete confirmation
  const [deleteDept, setDeleteDept] = useState<Department | null>(null);

  // Head assignment dialog
  const [headDialogOpen, setHeadDialogOpen] = useState(false);
  const [headTargetDept, setHeadTargetDept] = useState<Department | null>(null);
  const [selectedHeadUserId, setSelectedHeadUserId] = useState<string>("");
  const [headSaving, setHeadSaving] = useState(false);

  // Add member dialog
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [selectedAddUserId, setSelectedAddUserId] = useState<string>("");
  const [addMemberSaving, setAddMemberSaving] = useState(false);

  // All users for select dropdowns
  const [allUsers, setAllUsers] = useState<UserOption[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

  // Search
  const [searchQuery, setSearchQuery] = useState("");

  // ---------- Fetch departments (tree) ----------

  const fetchDepartments = useCallback(async () => {
    if (!orgId) return;
    try {
      const data = await apiClient.get<Department[]>(`/organizations/${orgId}/departments`, {
        tree: "true",
      });
      setDepartments(data || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "부서 목록을 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [orgId, addToast]);

  // 조직(회사) 이름 조회
  const fetchOrgName = useCallback(async () => {
    if (!orgId) return;
    try {
      const data = await apiClient.get<{ name: string }>(`/organizations/${orgId}`);
      setOrgName(data.name || "");
    } catch {
      // 조직 이름 조회 실패 시 무시
    }
  }, [orgId]);

  // 회사명 수정 저장
  const handleSaveOrgName = async () => {
    if (!orgId || !orgEditName.trim()) {
      addToast("회사명을 입력해주세요", "error");
      return;
    }
    setOrgEditSaving(true);
    try {
      await apiClient.put(`/organizations/${orgId}`, { name: orgEditName.trim() });
      setOrgName(orgEditName.trim());
      setOrgEditing(false);
      addToast("회사명이 수정되었습니다", "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "회사명 수정에 실패했습니다", "error");
    } finally {
      setOrgEditSaving(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
    fetchOrgName();
  }, [fetchDepartments, fetchOrgName]);

  // ---------- Fetch members ----------

  const fetchMembers = useCallback(
    async (deptId: string) => {
      if (!orgId) return;
      setMembersLoading(true);
      try {
        // 백엔드가 배열을 직접 반환하므로 바로 사용
        const data = await apiClient.get<DepartmentMember[]>(
          `/organizations/${orgId}/departments/${deptId}/members`,
        );
        setMembers(Array.isArray(data) ? data : []);
      } catch (err) {
        addToast(err instanceof Error ? err.message : "멤버 목록을 불러오지 못했습니다", "error");
      } finally {
        setMembersLoading(false);
      }
    },
    [orgId, addToast],
  );

  useEffect(() => {
    if (selectedDeptId) {
      fetchMembers(selectedDeptId);
    } else {
      setMembers([]);
    }
  }, [selectedDeptId, fetchMembers]);

  // ---------- Fetch all users ----------

  const fetchAllUsers = useCallback(async () => {
    if (!orgId) return;
    setUsersLoading(true);
    try {
      // 트랙 #106 — FastAPI redirect_slashes=False, trailing slash 제거
      const data = await apiClient.get<{ items: UserOption[] }>("/users", { org_id: orgId! });
      setAllUsers(data.items || []);
    } catch {
      // ignore
    } finally {
      setUsersLoading(false);
    }
  }, [orgId]);

  // ---------- Department CRUD ----------

  const openCreateDept = (parentId: string | null = null) => {
    setEditingDept(null);
    setDeptForm({ name: "", parent_id: parentId });
    setDeptDialogOpen(true);
  };

  const openEditDept = (dept: Department) => {
    setEditingDept(dept);
    setDeptForm({ name: dept.name, parent_id: dept.parent_id });
    setDeptDialogOpen(true);
  };

  const handleSaveDept = async () => {
    if (!orgId) return;
    if (!deptForm.name.trim()) {
      addToast("부서명을 입력해주세요", "error");
      return;
    }
    setDeptSaving(true);
    try {
      if (editingDept) {
        await apiClient.put(`/organizations/${orgId}/departments/${editingDept.id}`, deptForm);
        addToast("부서가 수정되었습니다", "success");
      } else {
        await apiClient.post(`/organizations/${orgId}/departments`, deptForm);
        addToast("부서가 생성되었습니다", "success");
      }
      setDeptDialogOpen(false);
      fetchDepartments();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "부서 저장에 실패했습니다", "error");
    } finally {
      setDeptSaving(false);
    }
  };

  const handleDeleteDept = async () => {
    if (!orgId || !deleteDept) return;
    try {
      await apiClient.delete(`/organizations/${orgId}/departments/${deleteDept.id}`);
      addToast("부서가 삭제되었습니다", "success");
      setDeleteDept(null);
      if (selectedDeptId === deleteDept.id) {
        setSelectedDeptId(null);
      }
      fetchDepartments();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "부서 삭제에 실패했습니다", "error");
    }
  };

  // ---------- Head assignment ----------

  const openHeadDialog = (dept: Department) => {
    setHeadTargetDept(dept);
    setSelectedHeadUserId(dept.head_user_id || "");
    setHeadDialogOpen(true);
    fetchAllUsers();
  };

  const handleAssignHead = async () => {
    if (!orgId || !headTargetDept) return;
    setHeadSaving(true);
    try {
      await apiClient.put(`/organizations/${orgId}/departments/${headTargetDept.id}/head`, {
        user_id: selectedHeadUserId || null,
      });
      addToast("부서장이 지정되었습니다", "success");
      setHeadDialogOpen(false);
      fetchDepartments();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "부서장 지정에 실패했습니다", "error");
    } finally {
      setHeadSaving(false);
    }
  };

  // ---------- Member management ----------

  const openAddMember = () => {
    setSelectedAddUserId("");
    setAddMemberDialogOpen(true);
    fetchAllUsers();
  };

  const handleAddMember = async () => {
    if (!orgId || !selectedDeptId || !selectedAddUserId) return;
    setAddMemberSaving(true);
    try {
      await apiClient.post(`/organizations/${orgId}/departments/${selectedDeptId}/members`, {
        user_id: selectedAddUserId,
      });
      addToast("멤버가 추가되었습니다", "success");
      setAddMemberDialogOpen(false);
      fetchMembers(selectedDeptId);
      fetchDepartments();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "멤버 추가에 실패했습니다", "error");
    } finally {
      setAddMemberSaving(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    if (!orgId || !selectedDeptId) return;
    try {
      await apiClient.delete(
        `/organizations/${orgId}/departments/${selectedDeptId}/members/${userId}`,
      );
      addToast("멤버가 제거되었습니다", "success");
      fetchMembers(selectedDeptId);
      fetchDepartments();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "멤버 제거에 실패했습니다", "error");
    }
  };

  // ---------- Tree toggle ----------

  const toggleNode = (id: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // ---------- Get selected department info ----------

  const allFlat = flattenDepartments(departments);
  const selectedDept = allFlat.find((d) => d.id === selectedDeptId);

  // ---------- Filter for parent select ----------

  const parentOptions = allFlat.filter((d) => !editingDept || d.id !== editingDept.id);

  // ---------- Tree Node Renderer ----------

  function renderTreeNode(dept: Department, level: number = 0) {
    const isExpanded = expandedNodes.has(dept.id);
    const hasChildren = dept.children && dept.children.length > 0;
    const isSelected = selectedDeptId === dept.id;

    const matchesSearch =
      !searchQuery.trim() || dept.name.toLowerCase().includes(searchQuery.toLowerCase());

    // If searching and this node/subtree doesn't match, hide it
    const childMatches = dept.children?.some((c) => hasMatchInSubtree(c, searchQuery));
    if (searchQuery.trim() && !matchesSearch && !childMatches) return null;

    return (
      <div key={dept.id}>
        {/* Node */}
        <div
          className={`group flex cursor-pointer items-center gap-1 rounded-lg px-2 py-2 text-sm transition-colors ${
            isSelected ? "bg-primary/10 text-primary" : "hover:bg-muted text-foreground"
          }`}
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={() => setSelectedDeptId(dept.id)}
        >
          {/* Expand/collapse */}
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleNode(dept.id);
              }}
              className="hover:bg-muted-foreground/10 shrink-0 rounded p-0.5"
              aria-label={isExpanded ? "접기" : "펼치기"}
            >
              {isExpanded ? (
                <ChevronDown className="text-muted-foreground h-4 w-4" />
              ) : (
                <ChevronRight className="text-muted-foreground h-4 w-4" />
              )}
            </button>
          ) : (
            <span className="inline-block w-5" />
          )}

          {/* Department icon */}
          <Building2 className="text-muted-foreground h-4 w-4 shrink-0" />

          {/* Name */}
          <span className="flex-1 truncate font-medium">{dept.name}</span>

          {/* Head indicator */}
          {dept.head_user_name && (
            <span className="text-muted-foreground hidden items-center gap-1 text-xs group-hover:flex">
              <Crown className="h-3 w-3" />
              {dept.head_user_name}
            </span>
          )}

          {/* Member count */}
          <Badge variant="secondary" className="ml-1 text-[10px]">
            {dept.member_count}
          </Badge>

          {/* Action buttons */}
          <div className="hidden items-center gap-0.5 group-hover:flex">
            <button
              onClick={(e) => {
                e.stopPropagation();
                openCreateDept(dept.id);
              }}
              className="text-muted-foreground hover:bg-muted hover:text-foreground rounded p-1"
              aria-label="하위 부서 추가"
              title="하위 부서 추가"
            >
              <Plus className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                openEditDept(dept);
              }}
              className="text-muted-foreground hover:bg-muted hover:text-foreground rounded p-1"
              aria-label="부서 수정"
              title="부서 수정"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                openHeadDialog(dept);
              }}
              className="text-muted-foreground hover:bg-muted hover:text-foreground rounded p-1"
              aria-label="부서장 지정"
              title="부서장 지정"
            >
              <Crown className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setDeleteDept(dept);
              }}
              className="text-muted-foreground hover:bg-muted hover:text-destructive rounded p-1"
              aria-label="부서 삭제"
              title="부서 삭제"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Connector line + children */}
        {hasChildren && isExpanded && (
          <div className="relative">
            {/* Vertical connector line */}
            <div
              className="border-muted absolute top-0 bottom-0 border-l-2"
              style={{ left: `${level * 20 + 18}px` }}
            />
            {dept.children.map((child) => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  }

  function hasMatchInSubtree(dept: Department, query: string): boolean {
    if (!query.trim()) return true;
    if (dept.name.toLowerCase().includes(query.toLowerCase())) return true;
    return dept.children?.some((c) => hasMatchInSubtree(c, query)) ?? false;
  }

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">부서/조직 관리</h1>
          <p className="text-muted-foreground mt-1 text-sm">부서를 관리하고 조직도를 확인합니다</p>
        </div>
        <Button
          onClick={() => openCreateDept(selectedDeptId)}
          className="bg-primary hover:bg-primary/90"
        >
          <Plus className="mr-2 h-4 w-4" />
          부서 생성
        </Button>
      </div>

      <div className="flex gap-6">
        {/* Left: Org chart tree */}
        <Card className="w-96 shrink-0">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Building2 className="h-4 w-4" />
              조직도
            </CardTitle>
            <div className="relative mt-2">
              <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
              <Input
                placeholder="부서 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[calc(100vh-18rem)]">
              <div className="px-2 pb-4">
                {loading ? (
                  <div className="space-y-2 p-4">
                    {Array.from({ length: 6 }).map((_, i) => (
                      <Skeleton key={i} className="h-8 w-full" />
                    ))}
                  </div>
                ) : departments.length === 0 ? (
                  <div className="text-muted-foreground py-10 text-center text-sm">
                    등록된 부서가 없습니다
                  </div>
                ) : (
                  <>
                    {/* 최상단 회사(조직) 노드 — 인라인 수정 가능 */}
                    {orgName && (
                      <div>
                        <div
                          className="group text-foreground flex items-center gap-1 rounded-lg px-2 py-2 text-sm"
                          style={{ paddingLeft: "8px" }}
                        >
                          <button
                            onClick={() => setOrgExpanded((prev) => !prev)}
                            className="hover:bg-muted-foreground/10 shrink-0 rounded p-0.5"
                            aria-label={orgExpanded ? "접기" : "펼치기"}
                          >
                            {orgExpanded ? (
                              <ChevronDown className="text-muted-foreground h-4 w-4" />
                            ) : (
                              <ChevronRight className="text-muted-foreground h-4 w-4" />
                            )}
                          </button>
                          <Building2 className="text-primary h-4 w-4 shrink-0" />

                          {/* 인라인 수정 모드 */}
                          {orgEditing ? (
                            <div className="flex flex-1 items-center gap-1">
                              <Input
                                autoFocus
                                value={orgEditName}
                                onChange={(e) => setOrgEditName(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleSaveOrgName();
                                  if (e.key === "Escape") setOrgEditing(false);
                                }}
                                className="h-7 text-sm font-bold"
                                disabled={orgEditSaving}
                              />
                              <button
                                onClick={handleSaveOrgName}
                                disabled={orgEditSaving}
                                className="text-primary hover:bg-primary/10 shrink-0 rounded p-1"
                                aria-label="회사명 저장"
                                title="저장 (Enter)"
                              >
                                {orgEditSaving ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                  <Check className="h-3.5 w-3.5" />
                                )}
                              </button>
                              <button
                                onClick={() => setOrgEditing(false)}
                                disabled={orgEditSaving}
                                className="text-muted-foreground hover:bg-muted hover:text-foreground shrink-0 rounded p-1"
                                aria-label="수정 취소"
                                title="취소 (ESC)"
                              >
                                <X className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          ) : (
                            <>
                              <span className="text-primary flex-1 truncate font-bold">
                                {orgName}
                              </span>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setOrgEditName(orgName);
                                  setOrgEditing(true);
                                }}
                                className="text-muted-foreground hover:bg-muted hover:text-foreground hidden shrink-0 rounded p-1 group-hover:block"
                                aria-label="회사명 수정"
                                title="회사명 수정"
                              >
                                <Pencil className="h-3.5 w-3.5" />
                              </button>
                            </>
                          )}
                        </div>
                        {orgExpanded && (
                          <div className="relative">
                            <div
                              className="border-muted absolute top-0 bottom-0 border-l-2"
                              style={{ left: "18px" }}
                            />
                            {departments.map((dept) => renderTreeNode(dept, 1))}
                          </div>
                        )}
                      </div>
                    )}
                    {/* orgName이 아직 로딩 안 됐으면 기존 방식으로 표시 */}
                    {!orgName && departments.map((dept) => renderTreeNode(dept, 0))}
                  </>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Right: Department detail / members */}
        <div className="flex-1">
          {selectedDept ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Building2 className="h-5 w-5" />
                      {selectedDept.name}
                    </CardTitle>
                    {selectedDept.head_user_name && (
                      <p className="text-muted-foreground mt-1 flex items-center gap-1 text-sm">
                        <Crown className="h-3.5 w-3.5" />
                        부서장: {selectedDept.head_user_name}
                      </p>
                    )}
                  </div>
                  <Button onClick={openAddMember} variant="outline" size="sm">
                    <UserPlus className="mr-2 h-4 w-4" />
                    멤버 추가
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <h3 className="text-muted-foreground mb-3 flex items-center gap-2 text-sm font-semibold">
                  <Users className="h-4 w-4" />
                  멤버 ({members.length})
                </h3>
                {membersLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 3 }).map((_, i) => (
                      <Skeleton key={i} className="h-12 w-full" />
                    ))}
                  </div>
                ) : members.length === 0 ? (
                  <div className="text-muted-foreground rounded-lg border border-dashed py-8 text-center text-sm">
                    이 부서에 등록된 멤버가 없습니다
                  </div>
                ) : (
                  <div className="space-y-2">
                    {members.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center justify-between rounded-lg border px-4 py-3"
                      >
                        <div>
                          <p className="text-foreground text-sm font-medium">
                            {member.username}
                            {selectedDept.head_user_id === member.id && (
                              <Badge variant="info" className="ml-2 text-[10px]">
                                부서장
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
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-20">
                <Building2 className="text-muted-foreground/30 h-12 w-12" />
                <p className="text-muted-foreground mt-4 text-sm font-medium">
                  부서를 선택하면 상세 정보를 확인할 수 있습니다
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* ---- Department Create/Edit Dialog ---- */}
      <Dialog open={deptDialogOpen} onOpenChange={setDeptDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingDept ? "부서 수정" : "부서 생성"}</DialogTitle>
            <DialogDescription>
              {editingDept ? "부서 정보를 수정합니다." : "새로운 부서를 생성합니다."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="dept-name">부서명</Label>
              <Input
                id="dept-name"
                value={deptForm.name}
                onChange={(e) => setDeptForm((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="부서명을 입력하세요"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dept-parent">상위 부서</Label>
              <select
                id="dept-parent"
                value={deptForm.parent_id || ""}
                onChange={(e) =>
                  setDeptForm((prev) => ({
                    ...prev,
                    parent_id: e.target.value || null,
                  }))
                }
                className="border-input bg-background ring-offset-background focus:ring-ring w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
              >
                <option value="">없음 (최상위)</option>
                {parentOptions.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeptDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSaveDept} disabled={deptSaving}>
              {deptSaving ? "저장 중..." : editingDept ? "수정" : "생성"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Head Assignment Dialog ---- */}
      <Dialog open={headDialogOpen} onOpenChange={setHeadDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>부서장 지정</DialogTitle>
            <DialogDescription>
              {headTargetDept?.name} 부서의 부서장을 지정합니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="head-user">부서장</Label>
              {usersLoading ? (
                <div className="text-muted-foreground flex items-center gap-2 py-2 text-sm">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  사용자 목록 로딩 중...
                </div>
              ) : (
                <select
                  id="head-user"
                  value={selectedHeadUserId}
                  onChange={(e) => setSelectedHeadUserId(e.target.value)}
                  className="border-input bg-background ring-offset-background focus:ring-ring w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
                >
                  <option value="">지정 안함</option>
                  {allUsers.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.username} ({u.email})
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setHeadDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleAssignHead} disabled={headSaving}>
              {headSaving ? "저장 중..." : "지정"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Add Member Dialog ---- */}
      <Dialog open={addMemberDialogOpen} onOpenChange={setAddMemberDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>멤버 추가</DialogTitle>
            <DialogDescription>{selectedDept?.name} 부서에 멤버를 추가합니다.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="add-member-user">사용자 선택</Label>
              {usersLoading ? (
                <div className="text-muted-foreground flex items-center gap-2 py-2 text-sm">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  사용자 목록 로딩 중...
                </div>
              ) : (
                <select
                  id="add-member-user"
                  value={selectedAddUserId}
                  onChange={(e) => setSelectedAddUserId(e.target.value)}
                  className="border-input bg-background ring-offset-background focus:ring-ring w-full rounded-md border px-3 py-2 text-sm focus:ring-2 focus:ring-offset-2 focus:outline-none"
                >
                  <option value="">사용자를 선택하세요</option>
                  {allUsers.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.username} ({u.email})
                    </option>
                  ))}
                </select>
              )}
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
      <AlertDialog open={!!deleteDept} onOpenChange={() => setDeleteDept(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>부서를 삭제하시겠습니까?</AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{deleteDept?.name}&quot; 부서를 삭제합니다. 이 작업은 되돌릴 수 없습니다.
              {deleteDept?.children && deleteDept.children.length > 0 && (
                <span className="text-destructive mt-1 block">
                  하위 부서가 있는 경우 함께 삭제될 수 있습니다.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteDept}>삭제</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
