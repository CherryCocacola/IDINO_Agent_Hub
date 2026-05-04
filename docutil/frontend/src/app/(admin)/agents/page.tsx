"use client";

import { format } from "date-fns";
import { Plus, Pencil, Trash2, Loader2, Bot, CheckCircle2, XCircle, X } from "lucide-react";
import { useState, useEffect, useCallback } from "react";

import { apiClient } from "@/lib/api/client";
import { useToast } from "@/lib/hooks/use-toast";
import { cn } from "@/lib/utils/cn";

// ---------- Types ----------

interface Agent {
  id: string;
  name: string;
  description: string | null;
  agent_type: string;
  system_prompt: string;
  llm_provider: string | null; // AI 프로바이더 (null = 시스템 기본값)
  llm_model: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface AgentFormData {
  name: string;
  description: string;
  agent_type: string;
  system_prompt: string;
  llm_provider: string | null; // AI 프로바이더 (null = 시스템 기본값)
  llm_model: string;
  temperature: number;
  max_tokens: number;
  is_active: boolean;
}

const EMPTY_FORM: AgentFormData = {
  name: "",
  description: "",
  agent_type: "chatbot",
  system_prompt: "",
  llm_provider: null, // 시스템 기본값 사용
  llm_model: "gpt-4o",
  temperature: 0.1,
  max_tokens: 4096,
  is_active: true,
};

// 에이전트 유형 — 기본 제공 유형 + 사용자 정의 유형 지원
// DB에서 가져온 유형이 이 목록에 없으면 원본 값 그대로 표시
const TYPE_LABELS: Record<string, string> = {
  chatbot: "챗봇",
  report: "보고서",
  proposal: "제안서",
  minutes: "회의록",
};

const TYPE_COLORS: Record<string, string> = {
  chatbot: "bg-green-50 text-green-700",
  report: "bg-blue-50 text-blue-700",
  proposal: "bg-blue-50 text-blue-800",
  minutes: "bg-orange-50 text-orange-700",
};

const TYPE_DESCRIPTIONS: Record<string, string> = {
  chatbot: "사용자 > 챗봇 화면에서 새 대화 시 에이전트 선택 가능",
  report: "사용자 > 보고서 생성 시 보고서 에이전트로 선택 가능",
  proposal: "사용자 > 제안서 생성 시 제안서 에이전트로 선택 가능",
  minutes: "사용자 > 회의록 생성 시 회의록 에이전트로 선택 가능",
};

// 기본 유형 목록 (드롭다운 + 직접 입력 지원)
const AGENT_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "chatbot", label: "챗봇" },
  { value: "report", label: "보고서" },
  { value: "proposal", label: "제안서" },
  { value: "minutes", label: "회의록" },
];

// 유형 라벨 헬퍼 — 알려진 유형은 한글, 나머지는 원본 표시
function getTypeLabel(type: string): string {
  return TYPE_LABELS[type] || type;
}

// 유형 색상 헬퍼 — 알려진 유형은 지정색, 나머지는 기본 회색
function getTypeColor(type: string): string {
  return TYPE_COLORS[type] || "bg-gray-50 text-gray-700";
}

// 유형 설명 헬퍼
function getTypeDescription(type: string): string {
  return TYPE_DESCRIPTIONS[type] || `커스텀 에이전트 유형: ${type}`;
}

// 프로바이더별 모델 옵션
const PROVIDER_MODEL_OPTIONS: Record<string, { value: string; label: string }[]> = {
  openai: [
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "gpt-4o-mini", label: "GPT-4o Mini" },
    { value: "gpt-4.1", label: "GPT-4.1" },
    { value: "gpt-4.1-mini", label: "GPT-4.1 Mini" },
  ],
  azure_openai: [{ value: "gpt-4o", label: "GPT-4o (Azure)" }],
  anthropic: [
    { value: "claude-sonnet-4-20250514", label: "Claude Sonnet 4" },
    { value: "claude-haiku-4-5-20251001", label: "Claude Haiku 4.5" },
  ],
  gemini: [
    { value: "gemini-2.0-flash", label: "Gemini 2.0 Flash" },
    { value: "gemini-2.5-pro-preview-05-06", label: "Gemini 2.5 Pro" },
    { value: "gemini-2.5-flash-preview-04-17", label: "Gemini 2.5 Flash" },
  ],
};

// 프로바이더 옵션 (시스템 기본값 포함)
const PROVIDER_OPTIONS = [
  { value: "__system__", label: "시스템 기본값" },
  { value: "openai", label: "OpenAI" },
  { value: "azure_openai", label: "Azure OpenAI" },
  { value: "anthropic", label: "Anthropic Claude" },
  { value: "gemini", label: "Google Gemini" },
];

// ---------- Component ----------

export default function AgentsPage() {
  const { addToast } = useToast();

  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [customType, setCustomType] = useState(""); // 직접 입력 유형

  // Dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<AgentFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  // Delete
  const [deleteTarget, setDeleteTarget] = useState<Agent | null>(null);

  // ---------- Fetch ----------

  const fetchAgents = useCallback(async () => {
    try {
      const params: Record<string, string> = {};
      const response = await apiClient.get<{ items: Agent[]; total: number }>("/agents", params);
      setAgents(response.items || []);
    } catch (err) {
      addToast(err instanceof Error ? err.message : "에이전트를 불러오지 못했습니다", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast, typeFilter]);

  useEffect(() => {
    setLoading(true);
    fetchAgents();
  }, [fetchAgents]);

  // ---------- Create / Edit ----------

  const openCreate = () => {
    setEditingId(null);
    setFormData(EMPTY_FORM);
    setDialogOpen(true);
  };

  const openEdit = (agent: Agent) => {
    setEditingId(agent.id);
    setFormData({
      name: agent.name,
      description: agent.description || "",
      agent_type: agent.agent_type,
      system_prompt: agent.system_prompt,
      llm_provider: agent.llm_provider,
      llm_model: agent.llm_model,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      is_active: agent.is_active,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      addToast("이름은 필수입니다", "error");
      return;
    }
    if (!formData.system_prompt.trim()) {
      addToast("시스템 프롬프트는 필수입니다", "error");
      return;
    }

    const body = {
      name: formData.name,
      description: formData.description || null,
      agent_type: formData.agent_type,
      system_prompt: formData.system_prompt,
      llm_provider: formData.llm_provider, // null이면 시스템 기본값 사용
      llm_model: formData.llm_model,
      temperature: formData.temperature,
      max_tokens: formData.max_tokens,
      is_active: formData.is_active,
    };

    setSaving(true);
    try {
      if (editingId) {
        await apiClient.put(`/agents/${editingId}`, body);
        addToast("에이전트가 수정되었습니다", "success");
      } else {
        await apiClient.post("/agents", body);
        addToast("에이전트가 추가되었습니다", "success");
      }
      setDialogOpen(false);
      fetchAgents();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "에이전트 저장에 실패했습니다", "error");
    } finally {
      setSaving(false);
    }
  };

  // ---------- Delete ----------

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await apiClient.delete(`/agents/${deleteTarget.id}`);
      addToast("에이전트가 삭제되었습니다", "success");
      setDeleteTarget(null);
      fetchAgents();
    } catch (err) {
      addToast(err instanceof Error ? err.message : "에이전트 삭제에 실패했습니다", "error");
    }
  };

  // ---------- Filtered data ----------

  // 클라이언트 사이드 유형 필터 (동적 유형 지원을 위해)
  const filteredAgents =
    typeFilter === "all" ? agents : agents.filter((a) => a.agent_type === typeFilter);

  // ---------- Render ----------

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-foreground text-2xl font-bold">에이전트 관리</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            챗봇 및 문서 생성 에이전트를 관리합니다
          </p>
        </div>
        <button
          onClick={openCreate}
          className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors"
        >
          <Plus className="h-4 w-4" />
          에이전트 추가
        </button>
      </div>

      {/* Type Filter Tabs — 기존 에이전트에서 유형을 동적으로 추출 */}
      <div className="border-border bg-muted/40 flex flex-wrap gap-1 rounded-lg border p-1">
        {[
          { value: "all", label: "전체" },
          ...Array.from(new Set(agents.map((a) => a.agent_type)))
            .sort()
            .map((t) => ({ value: t, label: getTypeLabel(t) })),
        ].map((tab) => (
          <button
            key={tab.value}
            onClick={() => setTypeFilter(tab.value)}
            className={cn(
              "rounded-md px-4 py-2 text-sm font-medium transition-colors",
              typeFilter === tab.value
                ? "text-foreground bg-white shadow-sm"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="border-border overflow-hidden rounded-lg border bg-white">
        {loading ? (
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
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">
                  프로바이더
                </th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">모델</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">온도</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">상태</th>
                <th className="text-muted-foreground px-4 py-3 text-left font-medium">생성일</th>
                <th className="text-muted-foreground w-28 px-4 py-3 text-left font-medium">작업</th>
              </tr>
            </thead>
            <tbody>
              {filteredAgents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-muted-foreground py-12 text-center">
                    <Bot className="mx-auto mb-2 h-8 w-8 opacity-40" />
                    등록된 에이전트가 없습니다. 새로 추가해주세요.
                  </td>
                </tr>
              ) : (
                filteredAgents.map((agent) => (
                  <tr
                    key={agent.id}
                    className="border-border hover:bg-muted/30 border-b transition-colors last:border-b-0"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Bot className="text-muted-foreground h-4 w-4" />
                        <span className="text-foreground font-medium">{agent.name}</span>
                      </div>
                      {agent.description && (
                        <p className="text-muted-foreground mt-0.5 line-clamp-1 text-xs">
                          {agent.description}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                          getTypeColor(agent.agent_type),
                        )}
                      >
                        {getTypeLabel(agent.agent_type)}
                      </span>
                      <p className="mt-0.5 text-[10px] text-gray-400">
                        {getTypeDescription(agent.agent_type)}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-muted rounded px-2 py-0.5 font-mono text-xs">
                        {agent.llm_provider
                          ? PROVIDER_OPTIONS.find((p) => p.value === agent.llm_provider)?.label ||
                            agent.llm_provider
                          : "시스템 기본값"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-muted rounded px-2 py-0.5 font-mono text-xs">
                        {agent.llm_model}
                      </span>
                    </td>
                    <td className="text-muted-foreground px-4 py-3">{agent.temperature}</td>
                    <td className="px-4 py-3">
                      {agent.is_active ? (
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
                    <td className="text-muted-foreground px-4 py-3">
                      {format(new Date(agent.created_at), "yyyy-MM-dd")}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => openEdit(agent)}
                          className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-1.5 transition-colors"
                          title="수정"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleteTarget(agent)}
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

      {/* ---- Create / Edit Dialog ---- */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setDialogOpen(false)}
            aria-hidden="true"
          />
          <div className="border-border relative z-50 w-full max-w-lg rounded-lg border bg-white shadow-xl">
            {/* Header */}
            <div className="border-border flex items-center justify-between border-b px-6 py-4">
              <div>
                <h2 className="text-foreground text-lg font-semibold">
                  {editingId ? "에이전트 수정" : "에이전트 추가"}
                </h2>
                <p className="text-muted-foreground mt-0.5 text-sm">
                  {editingId ? "에이전트 정보를 수정합니다" : "새 에이전트를 추가합니다"}
                </p>
              </div>
              <button
                onClick={() => setDialogOpen(false)}
                className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-1.5 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Body */}
            <div className="max-h-[60vh] space-y-4 overflow-y-auto px-6 py-4">
              {/* 이름 */}
              <div className="space-y-1.5">
                <label className="text-foreground text-sm font-medium">
                  이름 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="에이전트 이름을 입력하세요"
                  className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                />
              </div>

              {/* 설명 */}
              <div className="space-y-1.5">
                <label className="text-foreground text-sm font-medium">설명</label>
                <textarea
                  value={formData.description}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  placeholder="에이전트 설명을 입력하세요"
                  rows={2}
                  className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full resize-none rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                />
              </div>

              {/* 유형 — 기본 목록에서 선택하거나 직접 입력 */}
              <div className="space-y-1.5">
                <label className="text-foreground text-sm font-medium">유형</label>
                <div className="flex gap-2">
                  <select
                    value={
                      AGENT_TYPE_OPTIONS.some((o) => o.value === formData.agent_type)
                        ? formData.agent_type
                        : "__custom__"
                    }
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === "__custom__") {
                        setCustomType(formData.agent_type || "");
                      } else {
                        setFormData((prev) => ({ ...prev, agent_type: val }));
                        setCustomType("");
                      }
                    }}
                    className="border-border text-foreground focus:border-primary focus:ring-primary flex-1 rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                  >
                    {AGENT_TYPE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                    <option value="__custom__">직접 입력</option>
                  </select>
                  {(customType !== "" ||
                    !AGENT_TYPE_OPTIONS.some((o) => o.value === formData.agent_type)) && (
                    <input
                      type="text"
                      value={
                        AGENT_TYPE_OPTIONS.some((o) => o.value === formData.agent_type)
                          ? customType
                          : formData.agent_type
                      }
                      onChange={(e) => {
                        const val = e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "");
                        setCustomType(val);
                        setFormData((prev) => ({ ...prev, agent_type: val }));
                      }}
                      placeholder="영문 소문자 (예: summary)"
                      maxLength={20}
                      className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary flex-1 rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                    />
                  )}
                </div>
              </div>

              {/* 시스템 프롬프트 */}
              <div className="space-y-1.5">
                <label className="text-foreground text-sm font-medium">
                  시스템 프롬프트 <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.system_prompt}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      system_prompt: e.target.value,
                    }))
                  }
                  placeholder="이 에이전트의 역할과 행동 방식을 정의하세요..."
                  rows={6}
                  className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full resize-none rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                />
              </div>

              {/* AI 프로바이더 */}
              <div className="space-y-1.5">
                <label className="text-foreground text-sm font-medium">AI 프로바이더</label>
                <select
                  value={formData.llm_provider ?? "__system__"}
                  onChange={(e) => {
                    const val = e.target.value === "__system__" ? null : e.target.value;
                    // 프로바이더 변경 시 해당 프로바이더의 첫 번째 모델로 자동 설정
                    const models = val ? PROVIDER_MODEL_OPTIONS[val] : null;
                    const firstModel = models?.[0]?.value || "gpt-4o";
                    setFormData((prev) => ({
                      ...prev,
                      llm_provider: val,
                      llm_model: firstModel,
                    }));
                  }}
                  className="border-border text-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                >
                  {PROVIDER_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                <p className="text-muted-foreground text-xs">
                  시스템 기본값: 조직에 등록된 API 키의 프로바이더를 사용합니다
                </p>
              </div>

              {/* LLM 모델 */}
              <div className="space-y-1.5">
                <label className="text-foreground text-sm font-medium">LLM 모델</label>
                {formData.llm_provider && PROVIDER_MODEL_OPTIONS[formData.llm_provider] ? (
                  /* 프로바이더가 선택된 경우 드롭다운으로 모델 선택 */
                  <select
                    value={formData.llm_model}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        llm_model: e.target.value,
                      }))
                    }
                    className="border-border text-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                  >
                    {PROVIDER_MODEL_OPTIONS[formData.llm_provider].map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  /* 시스템 기본값인 경우 직접 입력 */
                  <input
                    type="text"
                    value={formData.llm_model}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        llm_model: e.target.value,
                      }))
                    }
                    placeholder="gpt-4o"
                    className="border-border text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                  />
                )}
              </div>

              {/* 온도 + 최대 토큰 (row) */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-foreground text-sm font-medium">온도</label>
                  <input
                    type="number"
                    value={formData.temperature}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        temperature: parseFloat(e.target.value) || 0,
                      }))
                    }
                    min={0}
                    max={1}
                    step={0.1}
                    className="border-border text-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                  />
                  <p className="text-muted-foreground text-xs">0 ~ 1 사이 값</p>
                </div>
                <div className="space-y-1.5">
                  <label className="text-foreground text-sm font-medium">최대 토큰</label>
                  <input
                    type="number"
                    value={formData.max_tokens}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        max_tokens: parseInt(e.target.value) || 0,
                      }))
                    }
                    min={1}
                    step={1}
                    className="border-border text-foreground focus:border-primary focus:ring-primary w-full rounded-md border bg-white px-3 py-2 text-sm focus:ring-1 focus:outline-none"
                  />
                </div>
              </div>

              {/* 활성 */}
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="agent-active"
                  checked={formData.is_active}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      is_active: e.target.checked,
                    }))
                  }
                  className="border-border text-primary focus:ring-primary h-4 w-4 rounded"
                />
                <label htmlFor="agent-active" className="text-foreground text-sm font-medium">
                  활성
                </label>
              </div>
            </div>

            {/* Footer */}
            <div className="border-border flex items-center justify-end gap-3 border-t px-6 py-4">
              <button
                onClick={() => setDialogOpen(false)}
                className="border-border text-foreground hover:bg-muted rounded-md border px-4 py-2 text-sm font-medium transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50"
              >
                {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                {saving ? "저장 중..." : editingId ? "수정" : "추가"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ---- Delete Confirmation Dialog ---- */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() => setDeleteTarget(null)}
            aria-hidden="true"
          />
          <div className="border-border relative z-50 w-full max-w-md rounded-lg border bg-white p-6 shadow-xl">
            <h2 className="text-foreground text-lg font-semibold">에이전트를 삭제하시겠습니까?</h2>
            <p className="text-muted-foreground mt-2 text-sm">
              &ldquo;{deleteTarget.name}&rdquo; 에이전트를 삭제합니다. 이 작업은 되돌릴 수 없습니다.
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
