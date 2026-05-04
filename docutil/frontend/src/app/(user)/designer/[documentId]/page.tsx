"use client";

/**
 * Designer — 기존 문서 편집 진입점 (`/designer/[documentId]`)
 *
 * Phase 4 S1 D10-A 산출물.
 *
 * 역할:
 *   - URL 경로의 `documentId` 를 받아 `DocumentSchema` 를 서버에서 로드하고
 *     `<DesignerShell />` 3분할 편집기로 주입하는 얇은 래퍼.
 *   - Mode A 진입 (`/designer/create`) 에서 문서 생성 후 `router.replace` 로
 *     이동하는 목적지.
 *   - Mode B 진입 (`/designer/fill/[templateId]`) 에서도 최종적으로 이 경로로
 *     리다이렉트될 예정 (Phase 4 S4).
 *
 * 데이터 흐름:
 *   1. Next.js 16 App Router 의 `params: Promise<...>` 규약에 따라 `use()` 로 언랩.
 *   2. UUID 형식 검증 실패 시 `notFound()` 로 전역 404 화면으로 폴백.
 *   3. `useDocument(documentId)` 훅이 내부적으로 `GET /v2/documents/{id}` 호출.
 *      - apiClient 경유 (anti-patterns.md: fetch 직접 호출 금지).
 *      - 성공 시 `useDocumentStore` 에 스냅샷 주입 → 3분할 패널이 공유.
 *   4. 로딩 중: shadcn/ui `Skeleton` 으로 레이아웃 placeholder 표시.
 *   5. 에러: 백엔드가 반환하는 Korean detail 메시지 (`요청한 문서를 찾을 수
 *      없습니다.`, `다른 조직의 문서에는 접근할 수 없습니다.`) 키워드로
 *      404 / 403 UX 를 분기.
 *   6. 성공: `<DesignerShell initialDocumentId={documentId} />` 렌더.
 *
 * 인증:
 *   `(user)/layout.tsx` 에서 isAuthenticated 게이트를 이미 적용하므로 본
 *   페이지에서는 추가 체크를 하지 않는다 (DRY). 미로그인 사용자는 layout
 *   단에서 `/login` 으로 리다이렉트된다.
 *
 * 제약 (CLAUDE.md / anti-patterns.md):
 *   - fetch 직접 호출 금지 — `useDocument` 가 apiClient 를 경유.
 *   - 새 UI 컴포넌트 생성 금지 — shadcn/ui `Skeleton` + `Button` 재사용.
 *   - 하드코딩 URL 금지 — `/login` 등의 라우트 상수만 inline.
 */

import Link from "next/link";
import { notFound, useRouter } from "next/navigation";
import { use, useEffect } from "react";

import { DesignerShell } from "@/components/document-designer/designer-shell";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDocumentStore } from "@/lib/document-schema/document-store";
import { useDocument } from "@/lib/document-schema/use-document";

// ─── 상수 ──────────────────────────────────────────────────────────────────

/**
 * UUIDv4 형식 검사 정규식. 서버가 동일한 포맷을 강제하므로 클라이언트에서
 * 선제 검증하면 잘못된 경로로 진입하는 API 호출 자체를 차단할 수 있다.
 * 대소문자는 허용하되 버전 비트(`4`) 와 variant(`8/9/a/b`) 까지 체크.
 */
const UUID_V4_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** 백엔드가 반환하는 "문서 없음" detail 메시지 키워드. */
const NOT_FOUND_KEYWORDS = ["찾을 수 없", "존재하지 않"];
/** 백엔드가 반환하는 "권한 거부" detail 메시지 키워드. */
const FORBIDDEN_KEYWORDS = ["접근할 수 없", "권한이 없"];

// ─── 타입 ──────────────────────────────────────────────────────────────────

interface DesignerPageProps {
  /** Next.js 16 규약: 동적 세그먼트는 Promise 로 전달된다. */
  params: Promise<{ documentId: string }>;
}

// ─── 컴포넌트 ─────────────────────────────────────────────────────────────

export default function DesignerDocumentPage({ params }: DesignerPageProps) {
  // Next.js 16: params 를 동기적으로 언랩. `fill/[templateId]/page.tsx` 와 동일 패턴.
  const { documentId } = use(params);

  // UUID 가 아니면 서버 왕복 전에 즉시 404. notFound 는 Next.js 의
  // `app/not-found.tsx` (없으면 전역 기본값) 로 폴백한다.
  if (!UUID_V4_PATTERN.test(documentId)) {
    notFound();
  }

  const { document, isLoading, error } = useDocument(documentId);
  const resetStore = useDocumentStore((s) => s.reset);

  // 언마운트 시 store 를 초기화하여 다른 문서로 진입해도 이전 문서의 잔상이
  // 남지 않게 한다. (document_id 가 바뀌면 useDocument 가 덮어쓰지만,
  // designer → 다른 탭 이동 후 다시 designer 복귀 시 stale 이슈 방지.)
  useEffect(() => {
    return () => {
      resetStore();
    };
  }, [resetStore]);

  // ── 에러 분기 ─────────────────────────────────────────────────────────
  if (error) {
    const message = error.message ?? "";
    const isNotFound = NOT_FOUND_KEYWORDS.some((k) => message.includes(k));
    const isForbidden = FORBIDDEN_KEYWORDS.some((k) => message.includes(k));

    if (isNotFound) {
      return <DocumentNotFoundView documentId={documentId} />;
    }
    if (isForbidden) {
      return <DocumentForbiddenView />;
    }
    // 그 외 일반 에러 — 네트워크 실패 등. 사용자에게 재시도 경로를 제공.
    return <DocumentErrorView message={message} />;
  }

  // ── 로딩 (초기) ──────────────────────────────────────────────────────
  // 문서가 아직 store 에 없고 로딩 중이면 skeleton. 이미 store 에 동일 id 가
  // 있으면 useDocument 가 GET 을 skip 하므로 `document` 가 즉시 반환되어
  // skeleton 을 건너뛴다.
  if (!document && isLoading) {
    return <DesignerSkeleton />;
  }

  // ── 로드는 끝났는데 document 가 없는 엣지케이스 ─────────────────────
  // 네트워크 상 OK 인데 빈 응답이 온 경우. 실 환경에선 거의 발생하지 않지만
  // 타입 좁히기 겸 안전장치.
  if (!document) {
    return <DesignerSkeleton />;
  }

  // ── 정상 경로 ────────────────────────────────────────────────────────
  return (
    <DesignerShell
      initialDocumentId={documentId}
      dataTestId="designer-shell"
      className="h-[calc(100vh-4rem)]"
    />
  );
}

// ─── 서브 뷰 (파일 내부 전용) ─────────────────────────────────────────

/** 3분할 shell 의 초기 로딩 placeholder. 실제 grid 비율 (30/55/15) 과 맞춤. */
function DesignerSkeleton() {
  return (
    <div
      data-testid="designer-page-skeleton"
      aria-busy="true"
      aria-label="문서 로딩 중"
      className="grid h-[calc(100vh-10rem)] w-full gap-4"
      style={{ gridTemplateColumns: "30% 55% 15%" }}
    >
      <div className="flex flex-col gap-3 p-4">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-2/3" />
      </div>
      <div className="p-4">
        <Skeleton className="h-full w-full" />
      </div>
      <div className="flex flex-col gap-3 p-4">
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-full" />
        <Skeleton className="h-6 w-3/4" />
      </div>
    </div>
  );
}

/** 문서 없음(404) 화면. 홈/my-documents 로 복귀 경로 제공. */
function DocumentNotFoundView({ documentId }: { documentId: string }) {
  return (
    <div
      role="alert"
      data-testid="designer-page-not-found"
      className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center"
    >
      <h1 className="text-xl font-semibold">문서를 찾을 수 없습니다</h1>
      <p className="text-muted-foreground text-sm">
        요청하신 문서가 존재하지 않거나 삭제되었을 수 있습니다.
      </p>
      <p className="bg-muted text-muted-foreground rounded px-2 py-1 font-mono text-xs break-all">
        {documentId}
      </p>
      <div className="flex gap-2">
        <Button asChild variant="outline">
          <Link href="/my-documents">내 문서로 이동</Link>
        </Button>
        <Button asChild>
          <Link href="/designer/create">새 문서 생성</Link>
        </Button>
      </div>
    </div>
  );
}

/** 권한 부족(403) 화면. 재로그인/다른 문서 탐색 안내. */
function DocumentForbiddenView() {
  return (
    <div
      role="alert"
      data-testid="designer-page-forbidden"
      className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center"
    >
      <h1 className="text-xl font-semibold">접근 권한이 없습니다</h1>
      <p className="text-muted-foreground text-sm">
        이 문서는 다른 조직 또는 비공개 범위로 설정되어 있어 열람할 수 없습니다.
      </p>
      <Button asChild variant="outline">
        <Link href="/my-documents">내 문서로 이동</Link>
      </Button>
    </div>
  );
}

/** 네트워크/서버 일반 오류 화면. 수동 재시도 제공. */
function DocumentErrorView({ message }: { message: string }) {
  const router = useRouter();
  return (
    <div
      role="alert"
      data-testid="designer-page-error"
      className="mx-auto flex max-w-md flex-col items-center gap-4 py-16 text-center"
    >
      <h1 className="text-xl font-semibold">문서를 불러오지 못했습니다</h1>
      <p className="text-muted-foreground text-sm">
        {message || "네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
      </p>
      <Button variant="outline" onClick={() => router.refresh()}>
        다시 시도
      </Button>
    </div>
  );
}
