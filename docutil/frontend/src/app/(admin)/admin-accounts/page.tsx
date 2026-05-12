"use client";

import { format } from "date-fns";
import {
  Plus,
  Search,
  MoreHorizontal,
  Pencil,
  ShieldCheck,
  ShieldOff,
  Unlock,
  UserCog,
} from "lucide-react";
import { useState, useEffect, useCallback } from "react";

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
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

type UserRole = "super_admin" | "admin" | "member" | "viewer";

interface AdminUser {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  status: "active" | "inactive" | "locked";
  last_login_at: string | null;
  created_at: string;
  department_id: string | null;
}

interface UserFormData {
  username: string;
  email: string;
  password: string;
  role: UserRole;
  organization_id: string;
  department_id: string | null;
}

interface Department {
  id: string;
  name: string;
  parent_id: string | null;
  depth: number;
  path: string;
}

interface PaginationMeta {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

const emptyForm: UserFormData = {
  username: "",
  email: "",
  password: "",
  role: "member",
  organization_id: "",
  department_id: null,
};

// ---------- Helpers ----------

function roleBadge(role: AdminUser["role"]) {
  switch (role) {
    case "super_admin":
      return <Badge variant="default">최고 관리자</Badge>;
    case "admin":
      return <Badge variant="secondary">관리자</Badge>;
    case "member":
      return <Badge variant="outline">일반 사용자</Badge>;
    case "viewer":
      return (
        <Badge variant="outline" className="text-muted-foreground">
          뷰어
        </Badge>
      );
    default:
      return <Badge variant="outline">{role}</Badge>;
  }
}

function statusBadge(status: AdminUser["status"]) {
  switch (status) {
    case "active":
      return <Badge variant="success">활성</Badge>;
    case "inactive":
      return <Badge variant="warning">비활성</Badge>;
    case "locked":
      return <Badge variant="destructive">잠금</Badge>;
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}

// ---------- Component ----------

export default function AdminAccountsPage() {
  const { addToast } = useToast();
  const { user: currentUser } = useAuth();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [pagination, setPagination] = useState<PaginationMeta>({
    total: 0,
    page: 1,
    per_page: 20,
    total_pages: 1,
  });

  // Dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [formData, setFormData] = useState<UserFormData>(emptyForm);
  const [saving, setSaving] = useState(false);

  // Departments
  const [departments, setDepartments] = useState<Department[]>([]);

  // ---------- Fetch ----------

  const fetchUsers = useCallback(async () => {
    if (!currentUser?.organization_id) return;

    setLoading(true);
    try {
      const params: Record<string, string> = {
        org_id: currentUser.organization_id,
        page: String(pagination.page),
        size: String(pagination.per_page),
      };
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (roleFilter !== "all") params.role = roleFilter;

      // 트랙 #88-7 — FastAPI redirect_slashes=False 이므로 trailing slash 제거.
      // 라우터 prefix `/api/v1/users` + route `""` → 정확히 `/api/v1/users` 일치.
      const data = await apiClient.get<{
        items: AdminUser[];
        total: number;
        page: number;
        size: number;
      }>("/users", params);
      setUsers(data.items || []);
      setPagination({
        total: data.total || 0,
        page: data.page || 1,
        per_page: data.size || 20,
        total_pages: Math.ceil((data.total || 0) / (data.size || 20)),
      });
    } catch (err) {
      addToast(err instanceof Error ? err.message : "사용자 목록을 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [
    pagination.page,
    pagination.per_page,
    searchQuery,
    roleFilter,
    addToast,
    currentUser?.organization_id,
  ]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // ---------- Fetch departments ----------

  useEffect(() => {
    if (!currentUser?.organization_id) return;
    const fetchDepartments = async () => {
      try {
        const data = await apiClient.get<Department[]>(
          `/organizations/${currentUser.organization_id}/departments`,
        );
        setDepartments(data || []);
      } catch {
        // Departments are optional; silently ignore fetch errors
      }
    };
    fetchDepartments();
  }, [currentUser?.organization_id]);

  // ---------- Create / Edit ----------

  const openCreate = () => {
    setEditingUser(null);
    setFormData({
      ...emptyForm,
      organization_id: currentUser?.organization_id ?? "",
    });
    setDialogOpen(true);
  };

  const openEdit = (user: AdminUser) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      password: "",
      role: user.role,
      organization_id: currentUser?.organization_id ?? "",
      department_id: user.department_id ?? null,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formData.username.trim() || !formData.email.trim()) {
      addToast("사용자명과 이메일은 필수입니다", "error");
      return;
    }
    if (!editingUser && !formData.password) {
      addToast("새 사용자의 비밀번호는 필수입니다", "error");
      return;
    }
    setSaving(true);
    try {
      if (editingUser) {
        const updateData: Record<string, string | null> = {
          username: formData.username,
          email: formData.email,
          role: formData.role,
          department_id: formData.department_id,
        };
        if (formData.password) updateData.password = formData.password;
        await apiClient.put(`/users/${editingUser.id}`, updateData);
        addToast("사용자가 수정되었습니다", "success");
      } else {
        const createData: Record<string, string | null> = {
          username: formData.username,
          email: formData.email,
          password: formData.password,
          role: formData.role,
          organization_id: formData.organization_id,
          department_id: formData.department_id,
        };
        // trailing slash 필수 (FastAPI router "/" 등록)
        await apiClient.post("/users", createData);
        addToast("사용자가 생성되었습니다", "success");
      }
      setDialogOpen(false);
      fetchUsers();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "사용자 저장에 실패했습니다", "error");
    } finally {
      setSaving(false);
    }
  };

  // ---------- Status actions ----------

  const handleActivate = async (user: AdminUser) => {
    try {
      await apiClient.put(`/users/${user.id}/status`, { status: "active" });
      addToast(`${user.username} 활성화되었습니다`, "success");
      fetchUsers();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "사용자 활성화에 실패했습니다", "error");
    }
  };

  const handleDeactivate = async (user: AdminUser) => {
    try {
      await apiClient.put(`/users/${user.id}/status`, { status: "inactive" });
      addToast(`${user.username} 비활성화되었습니다`, "success");
      fetchUsers();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "사용자 비활성화에 실패했습니다", "error");
    }
  };

  const handleUnlock = async (user: AdminUser) => {
    try {
      await apiClient.put(`/users/${user.id}/status`, { status: "active" });
      addToast(`${user.username} 잠금 해제되었습니다`, "success");
      fetchUsers();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "사용자 잠금 해제에 실패했습니다", "error");
    }
  };

  // ---------- Pagination ----------

  const goToPage = (page: number) => {
    setPagination((prev) => ({ ...prev, page }));
  };

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">사용자 관리</h1>
          <p className="text-muted-foreground mt-1 text-sm">사용자 계정을 생성하고 관리합니다</p>
        </div>
        <Button onClick={openCreate} className="bg-primary hover:bg-primary/90">
          <Plus className="mr-2 h-4 w-4" />
          사용자 등록
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative max-w-sm flex-1">
          <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
          <Input
            placeholder="사용자 검색..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPagination((prev) => ({ ...prev, page: 1 }));
            }}
            className="pl-9"
          />
        </div>
        <Tabs
          value={roleFilter}
          onValueChange={(val) => {
            setRoleFilter(val);
            setPagination((prev) => ({ ...prev, page: 1 }));
          }}
        >
          <TabsList>
            <TabsTrigger value="all">전체</TabsTrigger>
            <TabsTrigger value="super_admin">최고 관리자</TabsTrigger>
            <TabsTrigger value="admin">관리자</TabsTrigger>
            <TabsTrigger value="member">일반 사용자</TabsTrigger>
            <TabsTrigger value="viewer">뷰어</TabsTrigger>
          </TabsList>
        </Tabs>
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
                  <TableHead>사용자명</TableHead>
                  <TableHead>이메일</TableHead>
                  <TableHead>역할</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>최근 로그인</TableHead>
                  <TableHead className="w-12">작업</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-muted-foreground py-8 text-center">
                      사용자가 없습니다
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <UserCog className="text-muted-foreground h-4 w-4" />
                          {user.username}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{user.email}</TableCell>
                      <TableCell>{roleBadge(user.role)}</TableCell>
                      <TableCell>{statusBadge(user.status)}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {user.last_login_at
                          ? format(new Date(user.last_login_at), "yyyy-MM-dd HH:mm")
                          : "없음"}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openEdit(user)}>
                              <Pencil className="mr-2 h-4 w-4" />
                              수정
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {user.status === "active" ? (
                              <DropdownMenuItem onClick={() => handleDeactivate(user)}>
                                <ShieldOff className="mr-2 h-4 w-4" />
                                비활성화
                              </DropdownMenuItem>
                            ) : user.status === "inactive" ? (
                              <DropdownMenuItem onClick={() => handleActivate(user)}>
                                <ShieldCheck className="mr-2 h-4 w-4" />
                                활성화
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem onClick={() => handleUnlock(user)}>
                                <Unlock className="mr-2 h-4 w-4" />
                                잠금 해제
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {pagination.total_pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-muted-foreground text-sm">
            {pagination.total}명 중 {(pagination.page - 1) * pagination.per_page + 1}~
            {Math.min(pagination.page * pagination.per_page, pagination.total)} 표시
          </p>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page <= 1}
              onClick={() => goToPage(pagination.page - 1)}
            >
              이전
            </Button>
            {Array.from({ length: pagination.total_pages }, (_, i) => i + 1)
              .filter(
                (p) =>
                  p === 1 || p === pagination.total_pages || Math.abs(p - pagination.page) <= 1,
              )
              .map((page, idx, arr) => (
                <span key={page} className="flex items-center">
                  {idx > 0 && arr[idx - 1] !== page - 1 && (
                    <span className="text-muted-foreground px-2">...</span>
                  )}
                  <Button
                    variant={pagination.page === page ? "default" : "outline"}
                    size="sm"
                    onClick={() => goToPage(page)}
                  >
                    {page}
                  </Button>
                </span>
              ))}
            <Button
              variant="outline"
              size="sm"
              disabled={pagination.page >= pagination.total_pages}
              onClick={() => goToPage(pagination.page + 1)}
            >
              다음
            </Button>
          </div>
        </div>
      )}

      {/* ---- Create / Edit Dialog ---- */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingUser ? "사용자 수정" : "사용자 생성"}</DialogTitle>
            <DialogDescription>
              {editingUser ? "사용자 정보를 수정합니다." : "새 사용자의 정보를 입력합니다."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="user-username">사용자명</Label>
              <Input
                id="user-username"
                value={formData.username}
                onChange={(e) => setFormData((prev) => ({ ...prev, username: e.target.value }))}
                placeholder="사용자명을 입력하세요"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-email">이메일</Label>
              <Input
                id="user-email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
                placeholder="이메일 주소를 입력하세요"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-password">
                비밀번호{editingUser && " (변경하지 않으려면 비워두세요)"}
              </Label>
              <Input
                id="user-password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
                placeholder={editingUser ? "변경하지 않으려면 비워두세요" : "비밀번호를 입력하세요"}
              />
            </div>
            <div className="space-y-2">
              <Label>역할</Label>
              <Select
                value={formData.role}
                onValueChange={(val: UserRole) => setFormData((prev) => ({ ...prev, role: val }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="역할 선택" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="super_admin">최고 관리자</SelectItem>
                  <SelectItem value="admin">관리자</SelectItem>
                  <SelectItem value="member">일반 사용자</SelectItem>
                  <SelectItem value="viewer">뷰어</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="user-department">부서</Label>
              <Select
                value={formData.department_id ?? "none"}
                onValueChange={(val) =>
                  setFormData((prev) => ({
                    ...prev,
                    department_id: val === "none" ? null : val,
                  }))
                }
              >
                <SelectTrigger id="user-department">
                  <SelectValue placeholder="부서 선택 (선택사항)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">없음</SelectItem>
                  {departments.map((dept) => (
                    <SelectItem key={dept.id} value={dept.id}>
                      {dept.depth > 0 ? `${"  ".repeat(dept.depth)}${dept.name}` : dept.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "저장 중..." : editingUser ? "수정" : "생성"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
