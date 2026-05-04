"use client";

import {
  ChevronRight,
  ChevronDown,
  Folder,
  FolderOpen,
  FileText,
  FileSpreadsheet,
  FileImage,
  File,
  Search,
  Check,
  Minus,
  LayoutGrid,
  Loader2,
} from "lucide-react";
import { useState, useMemo, useCallback, useEffect } from "react";

import apiClient from "@/lib/api/client";
import { cn } from "@/lib/utils/cn";

// ── Types ──────────────────────────────────────────────────────────────────

export interface DocumentNode {
  id: string;
  name: string;
  type: "project" | "board" | "folder" | "document";
  format?: string; // pdf, docx, xlsx, hwp, etc.
  children?: DocumentNode[];
}

interface DocumentSelectorProps {
  nodes?: DocumentNode[];
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  mode: "single" | "multi";
  className?: string;
  placeholder?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const FORMAT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  pdf: FileText,
  docx: FileText,
  doc: FileText,
  xlsx: FileSpreadsheet,
  xls: FileSpreadsheet,
  csv: FileSpreadsheet,
  png: FileImage,
  jpg: FileImage,
  jpeg: FileImage,
  hwp: FileText,
};

function getIcon(node: DocumentNode) {
  if (node.type === "document") {
    const Icon = FORMAT_ICONS[node.format?.toLowerCase() || ""] || File;
    return Icon;
  }
  if (node.type === "project") return LayoutGrid;
  if (node.type === "board") return Folder;
  return Folder;
}

/** Collect all document IDs underneath a node (recursive). */
function collectDocumentIds(node: DocumentNode): string[] {
  if (node.type === "document") return [node.id];
  return (node.children ?? []).flatMap(collectDocumentIds);
}

/** 트리를 평탄화하여 모든 노드를 일차원 배열로 반환한다. */
export function flattenNodes(nodes: DocumentNode[]): DocumentNode[] {
  const result: DocumentNode[] = [];
  const walk = (list: DocumentNode[]) => {
    for (const n of list) {
      result.push(n);
      if (n.children) walk(n.children);
    }
  };
  walk(nodes);
  return result;
}

/** MIME type 또는 파일 확장자에서 짧은 포맷 문자열을 추출한다. */
function extractFormat(name: string, format?: string): string | undefined {
  // 확장자에서 추출 시도
  const extMatch = name.match(/\.(\w+)$/i);
  if (extMatch) return extMatch[1].toLowerCase();
  // MIME type에서 추출
  if (format) {
    const mimeMap: Record<string, string> = {
      "application/pdf": "pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
      "application/octet-stream": "hwpx",
    };
    return mimeMap[format] || undefined;
  }
  return undefined;
}

/** API에서 프로젝트 트리 + 문서 목록을 가져와 DocumentNode[] 로 변환한다. */
export async function fetchDocumentTree(): Promise<DocumentNode[]> {
  try {
    // 프로젝트 트리와 문서 목록을 병렬로 가져온다
    const [treeData, docsData] = await Promise.all([
      apiClient.get<
        Array<{
          id: string;
          name: string;
          boards: Array<{
            id: string;
            name: string;
            folders: Array<{ id: string; name: string }>;
          }>;
        }>
      >("/projects/tree"),
      apiClient.get<{
        items: Array<{
          id: string;
          name: string;
          format?: string;
          project_id?: string | null;
          board_id?: string | null;
          folder_id?: string | null;
        }>;
      }>("/documents", { size: "100" }),
    ]);

    const documents = docsData?.items || [];

    // 문서를 folder_id / board_id / project_id 별로 그룹핑
    const docsByFolder = new Map<string, DocumentNode[]>();
    const docsByBoard = new Map<string, DocumentNode[]>();
    const docsByProject = new Map<string, DocumentNode[]>();
    const unassignedDocs: DocumentNode[] = [];

    for (const doc of documents) {
      const docNode: DocumentNode = {
        id: doc.id,
        name: doc.name || "제목 없음",
        type: "document",
        format: extractFormat(doc.name || "", doc.format),
      };
      if (doc.folder_id) {
        const list = docsByFolder.get(doc.folder_id) || [];
        list.push(docNode);
        docsByFolder.set(doc.folder_id, list);
      } else if (doc.board_id) {
        const list = docsByBoard.get(doc.board_id) || [];
        list.push(docNode);
        docsByBoard.set(doc.board_id, list);
      } else if (doc.project_id) {
        const list = docsByProject.get(doc.project_id) || [];
        list.push(docNode);
        docsByProject.set(doc.project_id, list);
      } else {
        unassignedDocs.push(docNode);
      }
    }

    // 트리에 실제로 매핑된 folder/board/project ID를 추적한다
    const mappedFolderIds = new Set<string>();
    const mappedBoardIds = new Set<string>();
    const mappedProjectIds = new Set<string>();

    // 프로젝트 트리 구성
    const tree: DocumentNode[] = (treeData || []).map((proj) => {
      mappedProjectIds.add(proj.id);
      return {
        id: proj.id,
        name: proj.name,
        type: "project" as const,
        children: [
          ...(proj.boards || []).map((board) => {
            mappedBoardIds.add(board.id);
            return {
              id: board.id,
              name: board.name,
              type: "board" as const,
              children: [
                ...(board.folders || []).map((folder) => {
                  mappedFolderIds.add(folder.id);
                  return {
                    id: folder.id,
                    name: folder.name,
                    type: "folder" as const,
                    children: docsByFolder.get(folder.id) || [],
                  };
                }),
                ...(docsByBoard.get(board.id) || []),
              ],
            };
          }),
          ...(docsByProject.get(proj.id) || []),
        ],
      };
    });

    // 트리에 매핑되지 않은 문서를 미분류로 이동
    // (사용자가 접근 가능한 문서이지만 해당 프로젝트/폴더가 트리에 없는 경우)
    for (const [folderId, docs] of docsByFolder) {
      if (!mappedFolderIds.has(folderId)) {
        unassignedDocs.push(...docs);
      }
    }
    for (const [boardId, docs] of docsByBoard) {
      if (!mappedBoardIds.has(boardId)) {
        unassignedDocs.push(...docs);
      }
    }
    for (const [projectId, docs] of docsByProject) {
      if (!mappedProjectIds.has(projectId)) {
        unassignedDocs.push(...docs);
      }
    }

    // 프로젝트에 속하지 않거나 매핑 안 된 문서가 있으면 별도 그룹으로 추가
    if (unassignedDocs.length > 0) {
      tree.push({
        id: "__unassigned__",
        name: "미분류 문서",
        type: "project",
        children: unassignedDocs,
      });
    }

    return tree;
  } catch (err) {
    console.error("Failed to fetch document tree:", err);
    return [];
  }
}

// ── Tree Node Component ────────────────────────────────────────────────────

interface TreeNodeProps {
  node: DocumentNode;
  selectedIds: string[];
  onChange: (ids: string[]) => void;
  mode: "single" | "multi";
  depth: number;
  filter: string;
}

function TreeNode({ node, selectedIds, onChange, mode, depth, filter }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(depth < 1);
  const hasChildren = node.children && node.children.length > 0;
  const isDocument = node.type === "document";
  const Icon = useMemo(() => getIcon(node), [node]);

  // For folders/projects: gather all child document ids
  const childDocIds = useMemo(() => collectDocumentIds(node), [node]);

  // Check state for multi-mode
  const isChecked = isDocument
    ? selectedIds.includes(node.id)
    : childDocIds.length > 0 && childDocIds.every((id) => selectedIds.includes(id));

  const isIndeterminate =
    !isDocument && !isChecked && childDocIds.some((id) => selectedIds.includes(id));

  // Filter matching
  const matchesFilter = !filter || node.name.toLowerCase().includes(filter.toLowerCase());
  const childrenMatchFilter =
    !filter ||
    (node.children ?? []).some(
      (child) =>
        child.name.toLowerCase().includes(filter.toLowerCase()) ||
        (child.children ?? []).some((gc) => gc.name.toLowerCase().includes(filter.toLowerCase())),
    );

  if (filter && !matchesFilter && !childrenMatchFilter && !isDocument) {
    // check deep match
    const flat = flattenNodes(node.children ?? []);
    const anyDeepMatch = flat.some((n) => n.name.toLowerCase().includes(filter.toLowerCase()));
    if (!anyDeepMatch) return null;
  }

  if (filter && isDocument && !matchesFilter) return null;

  const handleToggle = () => {
    if (isDocument) {
      if (mode === "single") {
        onChange(selectedIds.includes(node.id) ? [] : [node.id]);
      } else {
        onChange(
          selectedIds.includes(node.id)
            ? selectedIds.filter((id) => id !== node.id)
            : [...selectedIds, node.id],
        );
      }
    } else if (mode === "multi") {
      if (isChecked) {
        onChange(selectedIds.filter((id) => !childDocIds.includes(id)));
      } else {
        const newIds = new Set([...selectedIds, ...childDocIds]);
        onChange(Array.from(newIds));
      }
    }
  };

  return (
    <div>
      <div
        className={cn(
          "group flex cursor-pointer items-center gap-1 rounded-md px-1 py-1 text-sm hover:bg-gray-100",
          isDocument && selectedIds.includes(node.id) && "bg-blue-50 hover:bg-blue-100",
        )}
        style={{ paddingLeft: `${depth * 16 + 4}px` }}
      >
        {/* Expand toggle */}
        {hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="shrink-0 rounded p-0.5 text-gray-400 hover:text-gray-600"
          >
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        ) : (
          <span className="w-5 shrink-0" />
        )}

        {/* Checkbox */}
        <button
          onClick={handleToggle}
          className={cn(
            "flex h-4 w-4 shrink-0 items-center justify-center rounded border transition-colors",
            isChecked
              ? "border-blue-600 bg-blue-600 text-white"
              : isIndeterminate
                ? "border-blue-600 bg-blue-100"
                : "border-gray-300 hover:border-gray-400",
          )}
        >
          {isChecked && <Check className="h-3 w-3" />}
          {isIndeterminate && <Minus className="h-3 w-3 text-blue-600" />}
        </button>

        {/* Icon */}
        <span className="ml-1 shrink-0 text-gray-500">
          {hasChildren && expanded ? (
            <FolderOpen className="h-4 w-4 text-yellow-500" />
          ) : (
            // eslint-disable-next-line react-hooks/static-components
            <Icon className={cn("h-4 w-4", isDocument ? "text-gray-400" : "text-yellow-500")} />
          )}
        </span>

        {/* Label */}
        <span
          className={cn(
            "ml-1 truncate",
            isDocument ? "text-gray-700" : "font-medium text-gray-800",
          )}
          onClick={handleToggle}
        >
          {node.name}
        </span>
      </div>

      {/* Children */}
      {hasChildren && expanded && (
        <div>
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              selectedIds={selectedIds}
              onChange={onChange}
              mode={mode}
              depth={depth + 1}
              filter={filter}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────

export function DocumentSelector({
  nodes,
  selectedIds,
  onChange,
  mode,
  className,
  placeholder = "Search documents...",
}: DocumentSelectorProps) {
  const [filter, setFilter] = useState("");
  const [apiNodes, setApiNodes] = useState<DocumentNode[]>([]);
  const [loading, setLoading] = useState(false);

  // nodes prop이 없으면 API에서 실제 데이터를 로드한다
  useEffect(() => {
    if (!nodes) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoading(true);
      fetchDocumentTree()
        .then(setApiNodes)
        .finally(() => setLoading(false));
    }
  }, [nodes]);

  const treeData = nodes ?? apiNodes;

  const totalDocuments = useMemo(() => {
    return flattenNodes(treeData).filter((n) => n.type === "document").length;
  }, [treeData]);

  const handleClearAll = useCallback(() => {
    onChange([]);
  }, [onChange]);

  return (
    <div className={cn("flex flex-col rounded-lg border border-gray-200 bg-white", className)}>
      {/* Search bar */}
      <div className="flex items-center gap-2 border-b border-gray-200 px-3 py-2">
        <Search className="h-4 w-4 shrink-0 text-gray-400" />
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder={placeholder}
          className="flex-1 bg-transparent text-sm text-gray-900 placeholder-gray-400 outline-none"
        />
        {selectedIds.length > 0 && (
          <button
            onClick={handleClearAll}
            className="shrink-0 text-xs text-gray-500 hover:text-red-600"
          >
            Clear
          </button>
        )}
      </div>

      {/* Selected count */}
      <div className="flex items-center justify-between border-b border-gray-100 px-3 py-1.5 text-xs text-gray-500">
        <span>
          {selectedIds.length} of {totalDocuments} documents selected
        </span>
        {mode === "multi" && selectedIds.length > 0 && (
          <button onClick={handleClearAll} className="text-blue-600 hover:text-blue-700">
            Deselect all
          </button>
        )}
      </div>

      {/* Tree */}
      <div className="max-h-80 overflow-y-auto px-1 py-1">
        {loading ? (
          <div className="flex items-center justify-center py-8 text-gray-400">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            <span className="text-sm">문서 목록 불러오는 중...</span>
          </div>
        ) : treeData.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-400">문서가 없습니다</div>
        ) : (
          treeData.map((node) => (
            <TreeNode
              key={node.id}
              node={node}
              selectedIds={selectedIds}
              onChange={onChange}
              mode={mode}
              depth={0}
              filter={filter}
            />
          ))
        )}
      </div>
    </div>
  );
}
