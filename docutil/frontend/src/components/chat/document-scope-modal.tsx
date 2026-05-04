"use client";

import { X, FileText, Check } from "lucide-react";
import { useState, useCallback, useEffect } from "react";

import {
  DocumentSelector,
  fetchDocumentTree,
  flattenNodes,
  type DocumentNode,
} from "@/components/documents/document-selector";
import { cn } from "@/lib/utils/cn";

// ── Types ──────────────────────────────────────────────────────────────────

interface DocumentScopeModalProps {
  open: boolean;
  onClose: () => void;
  // 선택된 문서 ID 배열과 문서명 기반 세션 제목을 함께 전달한다
  onConfirm: (selectedIds: string[], generatedTitle: string) => void;
  nodes?: DocumentNode[];
  initialSelectedIds?: string[];
  title?: string;
  description?: string;
}

// ── Component ──────────────────────────────────────────────────────────────

export function DocumentScopeModal({
  open,
  onClose,
  onConfirm,
  nodes,
  initialSelectedIds = [],
  title = "Select Documents",
  description = "Choose the documents you want to include in this chat session.",
}: DocumentScopeModalProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>(initialSelectedIds);
  // 문서 트리 데이터를 모달에서 직접 관리하여 선택된 문서명을 조회할 수 있게 한다
  const [treeNodes, setTreeNodes] = useState<DocumentNode[]>(nodes ?? []);

  // 모달이 열릴 때 트리 데이터를 가져온다 (외부에서 nodes를 주지 않은 경우)
  useEffect(() => {
    if (open && !nodes) {
      fetchDocumentTree().then(setTreeNodes);
    }
  }, [open, nodes]);

  // 외부에서 nodes가 전달되면 그것을 사용한다
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (nodes) setTreeNodes(nodes);
  }, [nodes]);

  const handleConfirm = useCallback(() => {
    // 선택된 문서 ID에 해당하는 문서명을 트리에서 찾아 세션 제목을 생성한다
    const allDocs = flattenNodes(treeNodes).filter((n) => n.type === "document");
    const selectedNames = selectedIds
      .map((id) => allDocs.find((d) => d.id === id)?.name)
      .filter(Boolean) as string[];

    // 제목 생성: 문서가 1~2개면 이름 나열, 3개 이상이면 처음 2개 + "외 N개"
    let generatedTitle: string;
    if (selectedNames.length === 0) {
      generatedTitle = "새 채팅";
    } else if (selectedNames.length <= 2) {
      generatedTitle = selectedNames.join(", ");
    } else {
      generatedTitle = `${selectedNames.slice(0, 2).join(", ")} 외 ${selectedNames.length - 2}개`;
    }

    // 제목이 너무 길면 잘라낸다 (백엔드 title 최대 255자)
    if (generatedTitle.length > 100) {
      generatedTitle = generatedTitle.slice(0, 97) + "...";
    }

    onConfirm(selectedIds, generatedTitle);
  }, [selectedIds, treeNodes, onConfirm]);

  const handleClose = useCallback(() => {
    setSelectedIds(initialSelectedIds);
    onClose();
  }, [initialSelectedIds, onClose]);

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50 transition-opacity"
        onClick={handleClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="relative flex max-h-[85vh] w-full max-w-lg flex-col rounded-xl bg-white shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
              <p className="mt-0.5 text-sm text-gray-500">{description}</p>
            </div>
            <button
              onClick={handleClose}
              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto px-6 py-4">
            <DocumentSelector
              nodes={treeNodes.length > 0 ? treeNodes : nodes}
              selectedIds={selectedIds}
              onChange={setSelectedIds}
              mode="multi"
              className="border-0"
            />
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4">
            {/* Selected count */}
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <FileText className="h-4 w-4" />
              <span>
                <strong className="text-gray-900">{selectedIds.length}</strong> document
                {selectedIds.length !== 1 ? "s" : ""} selected
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleClose}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={selectedIds.length === 0}
                className={cn(
                  "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors",
                  selectedIds.length > 0
                    ? "bg-blue-600 hover:bg-blue-700"
                    : "cursor-not-allowed bg-blue-300",
                )}
              >
                <Check className="h-4 w-4" />
                Confirm Selection
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
