"use client";

/**
 * Mode A — 자유 생성 진입점 (`/designer/create`)
 *
 * Phase 4 S1 D10-A 에서 "생성 완료 후 `/designer/[documentId]` 로 replace"
 * 자동 이동 로직을 추가.
 *
 * 화면 구성 (3분할):
 *  - 좌측 30%: PromptBox + (컴포넌트 선택 시) EditSidebar
 *  - 중앙 55%: PreviewPane (iframe → /preview-host)
 *  - 우측 15%: DesignTokenPicker
 *
 * 사용자 흐름:
 *  1) 프롬프트·DocumentType 입력 후 "생성" → POST /api/v1/v2/documents
 *     (PromptBox 내부 useDocumentMutation → setDocument 로 store 주입)
 *  2) useEffect 가 store 변화를 감지하여 `router.replace(/designer/{id})` 로
 *     canonical URL 로 자동 이동 → 새로고침·공유·뒤로가기가 의미를 갖게 됨.
 *  3) 이동 직후에는 `[documentId]/page.tsx` 가 동일 DesignerShell 을 그대로
 *     렌더 (store 에 이미 같은 id 가 있으므로 useDocument 가 중복 GET 을 skip).
 *
 * replace 이유 (push 가 아닌 이유):
 *   - `/designer/create` 는 "생성 유도" 화면이지 뒤로가기 대상이 아니다.
 *   - push 를 쓰면 생성 완료 → 뒤로가기 → 다시 /create 로 돌아가 "또 생성?"
 *     을 유도하는 UX 모순이 생긴다.
 */

import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";

import { DesignerShell } from "@/components/document-designer/designer-shell";
import { useDocumentStore } from "@/lib/document-schema/document-store";

export default function DesignerCreatePage() {
  const router = useRouter();
  // 문서 id 만 구독 → 동일 id 변화에서 리렌더를 최소화.
  const documentId = useDocumentStore((s) => s.document?.document_id ?? null);

  // 한 번만 replace 하도록 가드. React StrictMode / 빠른 재렌더로 useEffect 가
  // 두 번 실행되더라도 중복 라우팅을 방지.
  const hasRedirectedRef = useRef(false);

  useEffect(() => {
    if (!documentId) return;
    if (hasRedirectedRef.current) return;
    hasRedirectedRef.current = true;
    router.replace(`/designer/${documentId}`);
  }, [documentId, router]);

  return <DesignerShell />;
}
