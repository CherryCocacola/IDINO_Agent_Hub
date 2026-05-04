/**
 * PromptOptions — 소스 문서 다중선택 + 에이전트 선택 영역
 *
 * Phase 4 S1 D6 산출물.
 *
 * 구현 원칙:
 *   - Dialog + checkbox list 로 다중선택 UX 구성 (shadcn/ui 기존 컴포넌트).
 *   - 최대 10개 제한 (constants.MAX_SOURCE_DOCUMENTS).
 *   - 에이전트 목록은 현재 documentType 에 맞춰 자동 필터 (DOCUMENT_TYPE_TO_AGENT_TYPES).
 *   - API 호출은 전부 `apiClient` 경유, 절대 fetch 직호출 금지.
 */

"use client";

import { FileText, Users, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import apiClient from "@/lib/api/client";
import type { DocumentType, UUID } from "@/types/document-schema";

import {
  DOCUMENT_TYPE_TO_AGENT_TYPES,
  MAX_SOURCE_DOCUMENTS,
  SOURCE_DOCUMENTS_LIMIT,
} from "./constants";

// ─── 외부 타입 ────────────────────────────────────────────────────────────

export interface PromptOptionsProps {
  documentType: DocumentType;
  sourceDocumentIds: UUID[];
  onSourceChange: (next: UUID[]) => void;
  agentId: UUID | null;
  onAgentChange: (next: UUID | null) => void;
  disabled?: boolean;
}

// ─── 내부 타입 (API 응답 스키마) ──────────────────────────────────────────

interface DocumentListItem {
  id: string;
  // 백엔드 DocumentResponse 의 정식 필드 (snake_case)
  name?: string;
  original_filename?: string;
  file_size_bytes?: number;
  // legacy 호환 (옛 응답 또는 다른 엔드포인트에서 올 수 있는 필드명)
  title?: string;
  filename?: string;
  file_size?: number;
}

interface DocumentListResponse {
  items: DocumentListItem[];
  total?: number;
}

interface AgentListItem {
  id: string;
  name: string;
  description?: string | null;
}

interface AgentListResponse {
  items: AgentListItem[];
}

// ─── 공용 상수 ────────────────────────────────────────────────────────────

const NO_AGENT_VALUE = "__none__";

// ─── helpers ──────────────────────────────────────────────────────────────

function getDocumentLabel(item: DocumentListItem): string {
  // 백엔드 DocumentResponse 는 name(표시명) + original_filename(원본 파일명) 을 보냄.
  // legacy 응답이 title/filename 을 보낼 수도 있으니 fallback chain 으로 처리한다.
  return (
    item.name ??
    item.title ??
    item.original_filename ??
    item.filename ??
    `문서 ${item.id.slice(0, 8)}`
  );
}

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────

export function PromptOptions({
  documentType,
  sourceDocumentIds,
  onSourceChange,
  agentId,
  onAgentChange,
  disabled,
}: PromptOptionsProps) {
  const [documents, setDocuments] = useState<DocumentListItem[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [agentsError, setAgentsError] = useState<string | null>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // ── 소스 문서 리스트 조회 ──────────────────────────────────────────────

  const loadDocuments = useCallback(async () => {
    setDocumentsLoading(true);
    setDocumentsError(null);
    try {
      // 백엔드 페이지네이션 파라미터는 page/size (limit 미지원 → 무시되어 default 20).
      // 사용자 화면이므로 as_user_view=true 로 본인 권한 문서만 가져온다.
      const response = await apiClient.get<DocumentListResponse>("/documents", {
        size: String(SOURCE_DOCUMENTS_LIMIT),
        as_user_view: "true",
      });
      setDocuments(response.items ?? []);
    } catch (err) {
      const message = err instanceof Error ? err.message : "문서 목록 조회 실패";
      setDocumentsError(message);
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  // Dialog 를 처음 열 때 한 번만 로드. 이후는 캐시 재사용.
  useEffect(() => {
    if (dialogOpen && documents.length === 0 && !documentsError) {
      void loadDocuments();
    }
  }, [dialogOpen, documents.length, documentsError, loadDocuments]);

  // ── 에이전트 리스트 조회 (documentType 변경 시) ────────────────────────

  useEffect(() => {
    const agentTypes = DOCUMENT_TYPE_TO_AGENT_TYPES[documentType] ?? [];
    const params: Record<string, string> = {};
    if (agentTypes.length > 0) {
      params.agent_type = agentTypes.join(",");
    }

    let cancelled = false;
    (async () => {
      try {
        const response = await apiClient.get<AgentListResponse>("/agents", params);
        if (cancelled) return;
        setAgents(response.items ?? []);
        setAgentsError(null);
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "에이전트 목록 조회 실패";
        setAgentsError(message);
        setAgents([]);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [documentType]);

  // 현재 선택된 agent 가 목록에서 사라지면(유형 변경 등) 선택 해제.
  useEffect(() => {
    if (agentId && !agents.some((agent) => agent.id === agentId)) {
      onAgentChange(null);
    }
  }, [agentId, agents, onAgentChange]);

  // ── 소스 문서 선택 토글 ────────────────────────────────────────────────

  const toggleDocument = useCallback(
    (documentId: UUID) => {
      const isSelected = sourceDocumentIds.includes(documentId);
      if (isSelected) {
        onSourceChange(sourceDocumentIds.filter((id) => id !== documentId));
        return;
      }
      if (sourceDocumentIds.length >= MAX_SOURCE_DOCUMENTS) {
        return;
      }
      onSourceChange([...sourceDocumentIds, documentId]);
    },
    [onSourceChange, sourceDocumentIds],
  );

  const removeDocument = useCallback(
    (documentId: UUID) => {
      onSourceChange(sourceDocumentIds.filter((id) => id !== documentId));
    },
    [onSourceChange, sourceDocumentIds],
  );

  // ── 검색 필터 ──────────────────────────────────────────────────────────

  const filteredDocuments = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return documents;
    return documents.filter((doc) => getDocumentLabel(doc).toLowerCase().includes(term));
  }, [documents, searchTerm]);

  const selectedDocumentMap = useMemo(() => {
    const map = new Map<string, DocumentListItem>();
    documents.forEach((doc) => {
      if (sourceDocumentIds.includes(doc.id)) map.set(doc.id, doc);
    });
    return map;
  }, [documents, sourceDocumentIds]);

  // ── 렌더 ───────────────────────────────────────────────────────────────

  const sourceLimitReached = sourceDocumentIds.length >= MAX_SOURCE_DOCUMENTS;

  return (
    <section aria-label="생성 옵션" className="space-y-3" data-testid="prompt-options">
      {/* 소스 문서 선택 */}
      <div className="space-y-1.5">
        <Label htmlFor="prompt-box-source-documents">
          기준 문서 <span className="text-muted-foreground">(최대 {MAX_SOURCE_DOCUMENTS}개)</span>
        </Label>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button
              type="button"
              variant="outline"
              id="prompt-box-source-documents"
              disabled={disabled}
              className="w-full justify-start gap-2"
              data-testid="source-documents-trigger"
            >
              <FileText aria-hidden="true" />
              <span>
                {sourceDocumentIds.length === 0
                  ? "기준 문서 선택"
                  : `${sourceDocumentIds.length}개 선택됨`}
              </span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>기준 문서 선택</DialogTitle>
              <DialogDescription>
                RAG 기반 생성에 참고할 문서를 최대 {MAX_SOURCE_DOCUMENTS}개까지 선택할 수 있습니다.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-3">
              <Input
                type="search"
                placeholder="문서 제목으로 검색"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                aria-label="문서 검색"
              />

              <div
                role="listbox"
                aria-multiselectable="true"
                aria-label="기준 문서 목록"
                className="max-h-72 overflow-y-auto rounded-md border"
                data-testid="source-documents-list"
              >
                {documentsLoading && (
                  <p className="text-muted-foreground p-3 text-sm">문서 목록을 불러오는 중…</p>
                )}
                {documentsError && (
                  <p className="text-destructive p-3 text-sm" role="alert">
                    {documentsError}
                  </p>
                )}
                {!documentsLoading && !documentsError && filteredDocuments.length === 0 && (
                  <p className="text-muted-foreground p-3 text-sm">문서가 없습니다.</p>
                )}
                {filteredDocuments.map((doc) => {
                  const checked = sourceDocumentIds.includes(doc.id);
                  const itemDisabled = !checked && sourceLimitReached;
                  const label = getDocumentLabel(doc);
                  const checkboxId = `source-doc-${doc.id}`;
                  return (
                    <label
                      key={doc.id}
                      htmlFor={checkboxId}
                      className="hover:bg-accent flex cursor-pointer items-center gap-3 border-b px-3 py-2 last:border-b-0 aria-disabled:cursor-not-allowed aria-disabled:opacity-60"
                      aria-disabled={itemDisabled || undefined}
                    >
                      <Checkbox
                        id={checkboxId}
                        checked={checked}
                        disabled={itemDisabled}
                        onCheckedChange={() => toggleDocument(doc.id)}
                        aria-label={label}
                      />
                      <span className="text-sm">{label}</span>
                    </label>
                  );
                })}
              </div>

              {sourceLimitReached && (
                <p className="text-muted-foreground text-xs">
                  최대 {MAX_SOURCE_DOCUMENTS}개까지 선택할 수 있습니다.
                </p>
              )}
            </div>

            <DialogFooter>
              <Button type="button" onClick={() => setDialogOpen(false)}>
                완료
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {sourceDocumentIds.length > 0 && (
          <ul
            className="flex flex-wrap gap-1.5"
            aria-label="선택된 기준 문서"
            data-testid="selected-sources"
          >
            {sourceDocumentIds.map((id) => {
              const doc = selectedDocumentMap.get(id);
              const label = doc ? getDocumentLabel(doc) : `문서 ${id.slice(0, 8)}`;
              return (
                <li key={id}>
                  <span className="bg-secondary text-secondary-foreground inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs">
                    <FileText className="size-3" aria-hidden="true" />
                    <span className="max-w-[10rem] truncate" title={label}>
                      {label}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeDocument(id)}
                      className="hover:text-destructive"
                      aria-label={`${label} 제거`}
                    >
                      <X className="size-3" aria-hidden="true" />
                    </button>
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* 에이전트 선택 */}
      <div className="space-y-1.5">
        <Label htmlFor="prompt-box-agent">에이전트</Label>
        <Select
          value={agentId ?? NO_AGENT_VALUE}
          onValueChange={(value) => onAgentChange(value === NO_AGENT_VALUE ? null : value)}
          disabled={disabled}
        >
          <SelectTrigger id="prompt-box-agent" data-testid="agent-select">
            <SelectValue placeholder="에이전트 선택 (선택사항)">
              <span className="flex items-center gap-1.5">
                <Users className="size-3.5" aria-hidden="true" />
                {agentId
                  ? (agents.find((a) => a.id === agentId)?.name ?? "선택된 에이전트")
                  : "에이전트 미선택"}
              </span>
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={NO_AGENT_VALUE}>에이전트 미선택</SelectItem>
            {agents.map((agent) => (
              <SelectItem key={agent.id} value={agent.id}>
                {agent.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {agentsError && (
          <p className="text-destructive text-xs" role="alert">
            {agentsError}
          </p>
        )}
      </div>
    </section>
  );
}

export default PromptOptions;
