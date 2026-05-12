"use client";

import { format } from "date-fns";
import {
  Plus,
  Key,
  Trash2,
  CheckCircle2,
  XCircle,
  Loader2,
  ShieldCheck,
  Eye,
  EyeOff,
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
import { Card, CardContent } from "@/components/ui/card";
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
import { WarningBanner } from "@/components/ui/warning-banner";
import { apiClient } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

interface ApiKey {
  id: string;
  llm_name: string;
  api_key_prefix: string;
  is_verified: boolean;
  registered_by: string;
  registered_by_name: string | null;
  created_at: string;
  updated_at: string;
}

interface ApiKeyFormData {
  llm_name: string;
  api_key: string;
}

interface VerifyResult {
  is_valid: boolean;
  message: string;
}

// AI 프로바이더 옵션
const PROVIDER_OPTIONS = [
  { value: "openai", label: "OpenAI" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "anthropic", label: "Anthropic Claude" },
  { value: "gemini", label: "Google Gemini" },
  { value: "custom", label: "직접 입력" },
];

// ---------- Component ----------

export default function ApiKeysPage() {
  const { addToast } = useToast();

  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);

  // Register dialog
  const [registerOpen, setRegisterOpen] = useState(false);
  const [formData, setFormData] = useState<ApiKeyFormData>({
    llm_name: "",
    api_key: "",
  });
  const [saving, setSaving] = useState(false);
  const [showKey, setShowKey] = useState(false);

  // Delete
  const [deleteKey, setDeleteKey] = useState<ApiKey | null>(null);

  // Verify
  const [verifyingId, setVerifyingId] = useState<string | null>(null);

  // ---------- Fetch ----------

  const fetchApiKeys = useCallback(async () => {
    try {
      const response = await apiClient.get<{ items: ApiKey[]; total: number }>("/api-keys");
      setApiKeys(response.items || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "API 키를 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchApiKeys();
  }, [fetchApiKeys]);

  // ---------- Register ----------

  const openRegister = () => {
    setFormData({ llm_name: "", api_key: "" });
    setShowKey(false);
    setRegisterOpen(true);
  };

  const handleRegister = async () => {
    if (!formData.llm_name) {
      addToast("LLM 이름은 필수입니다", "error");
      return;
    }
    if (!formData.api_key.trim()) {
      addToast("API 키는 필수입니다", "error");
      return;
    }
    setSaving(true);
    try {
      await apiClient.post("/api-keys", formData);
      addToast("API 키가 등록되었습니다", "success");
      setRegisterOpen(false);
      fetchApiKeys();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "API 키 등록에 실패했습니다", "error");
    } finally {
      setSaving(false);
    }
  };

  // ---------- Verify ----------

  const handleVerify = async (key: ApiKey) => {
    setVerifyingId(key.id);
    try {
      const result = await apiClient.post<VerifyResult>(`/api-keys/${key.id}/verify`);
      if (result.is_valid) {
        addToast(`${key.llm_name} 키가 검증되었습니다`, "success");
      } else {
        addToast(`검증 실패: ${result.message}`, "error");
      }
      fetchApiKeys();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "검증에 실패했습니다", "error");
    } finally {
      setVerifyingId(null);
    }
  };

  // ---------- Delete ----------

  const handleDelete = async () => {
    if (!deleteKey) return;
    try {
      await apiClient.delete(`/api-keys/${deleteKey.id}`);
      addToast("API 키가 삭제되었습니다", "success");
      setDeleteKey(null);
      fetchApiKeys();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "API 키 삭제에 실패했습니다", "error");
    }
  };

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">
            API 키 <span className="text-muted-foreground text-base font-normal">(deprecated)</span>
          </h1>
          <p className="text-muted-foreground mt-1 text-sm">
            LLM API 키를 등록하고 관리합니다 — Phase 7 R2 이후 AgentHub 운영자 콘솔로 이전 권장
          </p>
        </div>
        <Button onClick={openRegister} className="bg-primary hover:bg-primary/90">
          <Plus className="mr-2 h-4 w-4" />키 등록
        </Button>
      </div>

      {/* Deprecation Banner — 트랙 #69 (Phase 7 R2) */}
      <WarningBanner title="이 페이지는 Phase 7 R2 이후 deprecate 되었습니다 (트랙 #69)">
        DocUtil 의 LLM 호출은 AgentHub 의 단일 진입점(`/v1/chat/completions`)을 위임 호출하므로,
        운영자 키 발급/검증/회전은 <strong>AgentHub 운영자 콘솔</strong> (
        <a
          href="https://agenthub.idino.local/admin/api-keys"
          className="underline decoration-yellow-700 underline-offset-2 hover:text-yellow-900"
          target="_blank"
          rel="noreferrer"
        >
          /admin/api-keys
        </a>
        ) 로 이전하세요. 본 화면은 운영 데이터 보존 목적으로만 유지되며, 신규 키 등록은 권장되지
        않습니다. 자세한 사항은 <code>user_mig/TECHSPEC.md §16</code> 참조.
      </WarningBanner>

      {/* Warning Banner */}
      <WarningBanner title="API 키 보안 안내" dismissible>
        API 키는 등록 후 마스킹되어 표시되며, 다시 확인할 수 없습니다. 키를 분실한 경우 새로운 키를
        등록해야 합니다.
      </WarningBanner>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="space-y-3 p-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>LLM 이름</TableHead>
                  <TableHead>API 키</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>등록자</TableHead>
                  <TableHead>날짜</TableHead>
                  <TableHead className="w-32">작업</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {apiKeys.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-muted-foreground py-8 text-center">
                      등록된 API 키가 없습니다. 새로 등록해주세요.
                    </TableCell>
                  </TableRow>
                ) : (
                  apiKeys.map((key) => (
                    <TableRow key={key.id}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Key className="text-muted-foreground h-4 w-4" />
                          <span className="font-medium">{key.llm_name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="bg-muted rounded px-2 py-1 text-sm">
                          {key.api_key_prefix}
                        </code>
                      </TableCell>
                      <TableCell>
                        {key.is_verified ? (
                          <Badge variant="success" className="gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            검증됨
                          </Badge>
                        ) : (
                          <Badge variant="warning" className="gap-1">
                            <XCircle className="h-3 w-3" />
                            미검증
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {key.registered_by_name || key.registered_by}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {format(new Date(key.created_at), "yyyy-MM-dd")}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleVerify(key)}
                            disabled={verifyingId === key.id}
                          >
                            {verifyingId === key.id ? (
                              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                            ) : (
                              <ShieldCheck className="mr-1 h-3 w-3" />
                            )}
                            검증
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-destructive h-8 w-8"
                            onClick={() => setDeleteKey(key)}
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
        </CardContent>
      </Card>

      {/* ---- Register Dialog ---- */}
      <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>API 키 등록</DialogTitle>
            <DialogDescription>
              새 LLM API 키를 등록합니다. 키는 안전하게 저장되며 등록 후 전체 키를 다시 볼 수
              없습니다.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label>LLM 제공사</Label>
              <Select
                value={formData.llm_name}
                onValueChange={(val) => setFormData((prev) => ({ ...prev, llm_name: val }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="LLM 제공사 선택" />
                </SelectTrigger>
                <SelectContent>
                  {PROVIDER_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="api-key-input">API 키</Label>
              <div className="relative">
                <Input
                  id="api-key-input"
                  type={showKey ? "text" : "password"}
                  value={formData.api_key}
                  onChange={(e) => setFormData((prev) => ({ ...prev, api_key: e.target.value }))}
                  placeholder="API 키를 입력하세요 (예: sk-...)"
                  className="pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute top-0 right-0 h-full px-3"
                  onClick={() => setShowKey(!showKey)}
                >
                  {showKey ? (
                    <EyeOff className="text-muted-foreground h-4 w-4" />
                  ) : (
                    <Eye className="text-muted-foreground h-4 w-4" />
                  )}
                </Button>
              </div>
              <p className="text-muted-foreground text-xs">
                API 키는 등록 후 마스킹되며 다시 확인할 수 없습니다.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRegisterOpen(false)}>
              취소
            </Button>
            <Button onClick={handleRegister} disabled={saving}>
              {saving ? "등록 중..." : "등록"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Delete Confirmation ---- */}
      <AlertDialog open={!!deleteKey} onOpenChange={() => setDeleteKey(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>API 키를 삭제하시겠습니까?</AlertDialogTitle>
            <AlertDialogDescription>
              {deleteKey?.llm_name} API 키 ({deleteKey?.api_key_prefix})를 삭제합니다. 이 작업은
              되돌릴 수 없습니다.
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
