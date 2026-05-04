"use client";

import { use } from "react";

/**
 * Mode B — 양식 채우기 진입점 (`/designer/fill/[templateId]`)
 *
 * Phase 1 기준: 라우트만 예약. 템플릿 로드 + 슬롯 채우기 UI는 Phase 4 S4에서 구현.
 *
 * 기대 동작(Phase 4 S4):
 *  1) `templateId`로 `GET /api/v1/v2/documents/templates/{templateId}` 호출
 *  2) 응답 `DocumentSchema`에서 `mode=template_fill`, `locked=true` 페이지를 구분하여
 *     편집 가능 슬롯만 프롬프트 박스에 노출
 *  3) `POST /api/v1/v2/documents` (body에 template_id 포함) → `/designer/[documentId]`로 이동
 */
interface PageParams {
  params: Promise<{ templateId: string }>;
}

export default function DesignerFillPage({ params }: PageParams) {
  // Next.js 15+ 권장 패턴: params는 Promise로 전달됨
  const { templateId } = use(params);

  // TODO(Phase 4 S4): DocumentDesignerShell(Mode B, templateId 주입) 렌더링.
  // 현재는 안내 placeholder. 사용자가 /designer/fill 경로로 직접 진입했을 때
  // 기능 준비 상태와 대체 경로(Mode A 자유 생성)를 명시한다.
  return (
    <div
      data-page="designer-fill"
      data-template-id={templateId}
      className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center gap-3 px-6 text-center"
    >
      <h2 className="text-lg font-semibold text-foreground">
        양식 채우기 모드는 준비 중입니다
      </h2>
      <p className="text-sm text-muted-foreground">
        템플릿 기반 Mode B 는 Phase 4 S4 스프린트에서 활성화됩니다. 지금은 자유 생성
        모드(<span className="font-mono">/designer/create</span>)를 이용해 디자이너에서
        문서를 생성·편집·내보낼 수 있습니다.
      </p>
      <p className="text-xs text-muted-foreground">템플릿 ID: {templateId}</p>
      <a
        href="/designer/create"
        className="mt-2 inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
      >
        자유 생성 모드로 이동
      </a>
    </div>
  );
}
