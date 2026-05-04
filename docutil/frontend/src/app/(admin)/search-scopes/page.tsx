"use client";

import {
  Plus,
  Search,
  Pencil,
  Trash2,
  MessageSquare,
  HelpCircle,
  Hash,
  Bot,
  Copy,
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
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
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
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { WarningBanner } from "@/components/ui/warning-banner";
import { apiClient } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";

// ---------- Types ----------

interface SearchScope {
  id: string;
  name: string;
  description: string;
  project_id: string | null;
  board_id: string | null;
  folder_id: string | null;
  location_path: string;
  chatbot_enabled: boolean;
  qa_enabled: boolean;
  keyword_search_enabled: boolean;
  agent_enabled: boolean;
  chunk_size: number;
  chunk_overlap: number;
  title_weight: number;
  keyword_weight: number;
  content_weight: number;
  max_results: number;
  similarity_threshold: number;
  created_at: string;
}

interface LocationOption {
  id: string;
  name: string;
  type: "project" | "board" | "folder";
  path: string;
}

interface ScopeFormData {
  name: string;
  description: string;
  location_type: "project" | "board" | "folder";
  location_id: string;
  chatbot_enabled: boolean;
  qa_enabled: boolean;
  keyword_search_enabled: boolean;
  agent_enabled: boolean;
  chunk_size: number;
  chunk_overlap: number;
  title_weight: number;
  keyword_weight: number;
  content_weight: number;
  max_results: number;
  similarity_threshold: number;
}

const defaultFormData: ScopeFormData = {
  name: "",
  description: "",
  location_type: "project",
  location_id: "",
  chatbot_enabled: true,
  qa_enabled: true,
  keyword_search_enabled: true,
  agent_enabled: false,
  chunk_size: 512,
  chunk_overlap: 50,
  title_weight: 0.3,
  keyword_weight: 0.3,
  content_weight: 0.4,
  max_results: 10,
  similarity_threshold: 0.7,
};

// ---------- Component ----------

export default function SearchScopesPage() {
  const { addToast } = useToast();

  const [scopes, setScopes] = useState<SearchScope[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingScope, setEditingScope] = useState<SearchScope | null>(null);
  const [formData, setFormData] = useState<ScopeFormData>(defaultFormData);
  const [saving, setSaving] = useState(false);

  // Location options
  const [locations, setLocations] = useState<LocationOption[]>([]);

  // Delete state
  const [deleteScope, setDeleteScope] = useState<SearchScope | null>(null);

  // ---------- Fetch ----------

  const fetchScopes = useCallback(async () => {
    try {
      const response = await apiClient.get<{ items: SearchScope[]; total: number }>(
        "/search-scopes",
      );
      setScopes(response.items || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "검색 범위를 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  const fetchLocations = useCallback(
    async (type: "project" | "board" | "folder") => {
      try {
        const data = await apiClient.get<LocationOption[]>("/search-scopes/locations", {
          location_type: type,
        });
        setLocations(data);
      } catch (err) {
        addToast(err instanceof Error ? err.message : "위치를 불러오지 못했습니다", "error");
      }
    },
    [addToast],
  );

  useEffect(() => {
    fetchScopes();
  }, [fetchScopes]);

  // ---------- Create / Edit ----------

  const openCreate = () => {
    setEditingScope(null);
    setFormData(defaultFormData);
    fetchLocations("project");
    setDialogOpen(true);
  };

  const openEdit = (scope: SearchScope) => {
    setEditingScope(scope);
    const locType = scope.folder_id ? "folder" : scope.board_id ? "board" : "project";
    const locId = scope.folder_id || scope.board_id || scope.project_id || "";
    setFormData({
      name: scope.name,
      description: scope.description,
      location_type: locType,
      location_id: locId,
      chatbot_enabled: scope.chatbot_enabled,
      qa_enabled: scope.qa_enabled,
      keyword_search_enabled: scope.keyword_search_enabled,
      agent_enabled: scope.agent_enabled,
      chunk_size: scope.chunk_size,
      chunk_overlap: scope.chunk_overlap,
      title_weight: scope.title_weight,
      keyword_weight: scope.keyword_weight,
      content_weight: scope.content_weight,
      max_results: scope.max_results,
      similarity_threshold: scope.similarity_threshold,
    });
    fetchLocations(locType);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      addToast("범위 이름은 필수입니다", "error");
      return;
    }
    if (!formData.location_id) {
      addToast("위치는 필수입니다", "error");
      return;
    }
    setSaving(true);
    try {
      // Transform location_type/location_id to project_id/board_id/folder_id
      const { location_type, location_id, ...rest } = formData;
      const payload: Record<string, unknown> = { ...rest };
      if (location_type === "project") payload.project_id = location_id;
      else if (location_type === "board") payload.board_id = location_id;
      else if (location_type === "folder") payload.folder_id = location_id;

      if (editingScope) {
        await apiClient.put(`/search-scopes/${editingScope.id}`, payload);
        addToast("검색 범위가 수정되었습니다", "success");
      } else {
        await apiClient.post("/search-scopes", payload);
        addToast("검색 범위가 생성되었습니다", "success");
      }
      setDialogOpen(false);
      fetchScopes();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "검색 범위 저장에 실패했습니다", "error");
    } finally {
      setSaving(false);
    }
  };

  // ---------- Delete ----------

  const handleDelete = async () => {
    if (!deleteScope) return;
    try {
      await apiClient.delete(`/search-scopes/${deleteScope.id}`);
      addToast("검색 범위가 삭제되었습니다", "success");
      setDeleteScope(null);
      fetchScopes();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "검색 범위 삭제에 실패했습니다", "error");
    }
  };

  // ---------- Copy ID ----------

  const copyEmbeddingId = (id: string) => {
    navigator.clipboard.writeText(id);
    addToast("임베딩 ID가 클립보드에 복사되었습니다", "success");
  };

  // ---------- Filter ----------

  const filteredScopes = scopes.filter(
    (s) =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // ---------- Feature badges ----------

  const featureBadges = (scope: SearchScope) => {
    const features: { enabled: boolean; label: string; icon: React.ReactNode }[] = [
      {
        enabled: scope.chatbot_enabled,
        label: "챗봇",
        icon: <MessageSquare className="h-3 w-3" />,
      },
      { enabled: scope.qa_enabled, label: "Q&A", icon: <HelpCircle className="h-3 w-3" /> },
      {
        enabled: scope.keyword_search_enabled,
        label: "키워드",
        icon: <Hash className="h-3 w-3" />,
      },
      { enabled: scope.agent_enabled, label: "에이전트", icon: <Bot className="h-3 w-3" /> },
    ];
    return features
      .filter((f) => f.enabled)
      .map((f) => (
        <Badge key={f.label} variant="secondary" className="gap-1 text-xs">
          {f.icon}
          {f.label}
        </Badge>
      ));
  };

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">검색 범위</h1>
          <p className="text-muted-foreground mt-1 text-sm">검색 범위를 설정하고 관리합니다</p>
        </div>
        <Button onClick={openCreate} className="bg-primary hover:bg-primary/90">
          <Plus className="mr-2 h-4 w-4" />
          범위 생성
        </Button>
      </div>

      {/* Warning Banner */}
      <WarningBanner title="검색 범위 설정 안내" dismissible>
        검색 범위는 문서 검색의 대상이 되는 프로젝트, 보드, 또는 폴더를 지정합니다. 적절한 범위
        설정은 검색 성능과 정확도에 영향을 미칩니다.
      </WarningBanner>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
        <Input
          placeholder="범위 검색..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Scope cards */}
      {loading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48 w-full rounded-lg" />
          ))}
        </div>
      ) : filteredScopes.length === 0 ? (
        <div className="text-muted-foreground py-12 text-center">
          검색 범위가 없습니다. 새로 생성해주세요.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredScopes.map((scope) => (
            <Card key={scope.id} className="flex flex-col">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">{scope.name}</CardTitle>
                    <CardDescription className="mt-1 text-xs">
                      {scope.location_path}
                    </CardDescription>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => openEdit(scope)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive h-8 w-8"
                      onClick={() => setDeleteScope(scope)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col justify-between gap-3">
                {scope.description && (
                  <p className="text-muted-foreground line-clamp-2 text-sm">{scope.description}</p>
                )}
                <div className="flex flex-wrap gap-1">{featureBadges(scope)}</div>
                <div className="bg-muted flex items-center gap-2 rounded-md px-3 py-2 text-xs">
                  <span className="text-muted-foreground truncate font-mono">ID: {scope.id}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 shrink-0"
                    onClick={() => copyEmbeddingId(scope.id)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ---- Create/Edit Dialog ---- */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-h-[85vh] max-w-2xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingScope ? "검색 범위 수정" : "검색 범위 생성"}</DialogTitle>
            <DialogDescription>검색 범위 설정을 구성합니다.</DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="basic" className="w-full">
            <TabsList className="w-full">
              <TabsTrigger value="basic" className="flex-1">
                기본
              </TabsTrigger>
              <TabsTrigger value="environment" className="flex-1">
                환경
              </TabsTrigger>
              <TabsTrigger value="advanced" className="flex-1">
                고급
              </TabsTrigger>
            </TabsList>

            {/* Basic tab */}
            <TabsContent value="basic" className="space-y-4 pt-4">
              <div className="space-y-2">
                <Label htmlFor="scope-name">이름</Label>
                <Input
                  id="scope-name"
                  value={formData.name}
                  onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="범위 이름을 입력하세요"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="scope-desc">설명</Label>
                <Textarea
                  id="scope-desc"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, description: e.target.value }))
                  }
                  placeholder="범위 설명을 입력하세요"
                />
              </div>
              <div className="space-y-2">
                <Label>위치 유형</Label>
                <Select
                  value={formData.location_type}
                  onValueChange={(val: "project" | "board" | "folder") => {
                    setFormData((prev) => ({ ...prev, location_type: val, location_id: "" }));
                    fetchLocations(val);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="유형 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="project">프로젝트</SelectItem>
                    <SelectItem value="board">보드</SelectItem>
                    <SelectItem value="folder">폴더</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>위치</Label>
                <Select
                  value={formData.location_id}
                  onValueChange={(val) => setFormData((prev) => ({ ...prev, location_id: val }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="위치 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    {locations.map((loc) => (
                      <SelectItem key={loc.id} value={loc.id}>
                        {loc.path || loc.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </TabsContent>

            {/* Environment tab */}
            <TabsContent value="environment" className="space-y-4 pt-4">
              <div className="space-y-4">
                {[
                  {
                    key: "chatbot_enabled" as const,
                    label: "챗봇",
                    desc: "챗봇 스타일 검색을 활성화합니다",
                  },
                  {
                    key: "qa_enabled" as const,
                    label: "Q&A",
                    desc: "질의응답 모드를 활성화합니다",
                  },
                  {
                    key: "keyword_search_enabled" as const,
                    label: "키워드 검색",
                    desc: "키워드 기반 검색을 활성화합니다",
                  },
                  {
                    key: "agent_enabled" as const,
                    label: "에이전트",
                    desc: "AI 에이전트 모드를 활성화합니다",
                  },
                ].map((item) => (
                  <div
                    key={item.key}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="text-muted-foreground text-sm">{item.desc}</p>
                    </div>
                    <Switch
                      checked={formData[item.key]}
                      onCheckedChange={(checked) =>
                        setFormData((prev) => ({ ...prev, [item.key]: checked }))
                      }
                    />
                  </div>
                ))}
              </div>
            </TabsContent>

            {/* Advanced tab */}
            <TabsContent value="advanced" className="space-y-6 pt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>청크 크기</Label>
                  <Input
                    type="number"
                    value={formData.chunk_size}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, chunk_size: Number(e.target.value) }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label>청크 오버랩</Label>
                  <Input
                    type="number"
                    value={formData.chunk_overlap}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        chunk_overlap: Number(e.target.value),
                      }))
                    }
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>제목 가중치</Label>
                    <span className="text-muted-foreground text-sm">
                      {formData.title_weight.toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    value={[formData.title_weight * 100]}
                    onValueChange={([val]) =>
                      setFormData((prev) => ({ ...prev, title_weight: val / 100 }))
                    }
                    min={0}
                    max={100}
                    step={5}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>키워드 가중치</Label>
                    <span className="text-muted-foreground text-sm">
                      {formData.keyword_weight.toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    value={[formData.keyword_weight * 100]}
                    onValueChange={([val]) =>
                      setFormData((prev) => ({ ...prev, keyword_weight: val / 100 }))
                    }
                    min={0}
                    max={100}
                    step={5}
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>콘텐츠 가중치</Label>
                    <span className="text-muted-foreground text-sm">
                      {formData.content_weight.toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    value={[formData.content_weight * 100]}
                    onValueChange={([val]) =>
                      setFormData((prev) => ({ ...prev, content_weight: val / 100 }))
                    }
                    min={0}
                    max={100}
                    step={5}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>최대 결과 수</Label>
                  <Input
                    type="number"
                    value={formData.max_results}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        max_results: Number(e.target.value),
                      }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>유사도 임계값</Label>
                    <span className="text-muted-foreground text-sm">
                      {formData.similarity_threshold.toFixed(2)}
                    </span>
                  </div>
                  <Slider
                    value={[formData.similarity_threshold * 100]}
                    onValueChange={([val]) =>
                      setFormData((prev) => ({
                        ...prev,
                        similarity_threshold: val / 100,
                      }))
                    }
                    min={0}
                    max={100}
                    step={5}
                  />
                </div>
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              취소
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "저장 중..." : editingScope ? "수정" : "생성"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ---- Delete Confirmation ---- */}
      <AlertDialog open={!!deleteScope} onOpenChange={() => setDeleteScope(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>검색 범위를 삭제하시겠습니까?</AlertDialogTitle>
            <AlertDialogDescription>
              &quot;{deleteScope?.name}&quot;을(를) 삭제합니다. 범위 설정 및 관련 임베딩이
              제거됩니다.
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
