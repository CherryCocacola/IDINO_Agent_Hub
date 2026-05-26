"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Header } from "@/components/layouts/header";
import { AdminSidebar } from "@/components/layouts/sidebar";
import { ToastContainer } from "@/components/layouts/toast-container";
import { useAuth } from "@/lib/hooks/use-auth";

// ────────────────────────────────────────────────────────────────────────
// 트랙 A1 Phase E (2026-05-26): DocUtil 운영자 페이지는 AgentHub 콘솔로 흡수됨.
// next.config.ts 의 redirects() 가 서버에서 302 처리하지만, 클라이언트 라우팅
// (Link 클릭 등) 으로 진입한 경우의 fallback 으로 본 layout 이 AgentHub 콘솔로
// 즉시 이동시킨다.
// ────────────────────────────────────────────────────────────────────────

const AGENTHUB_URL =
  process.env.NEXT_PUBLIC_AGENTHUB_URL || "http://192.168.10.39:64005";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, user, _hasHydrated } = useAuth();
  const [checked, setChecked] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  useEffect(() => {
    // hydration 전에는 검사를 건너뛴다
    if (!_hasHydrated) return;

    if (!isAuthenticated || !user) {
      router.replace("/login");
      return;
    }

    // 관리자 역할 정의
    const adminRoles = ["super_admin", "admin", "org_admin"];

    // 비-관리자는 사용자 화면으로 돌려보낸다
    if (!adminRoles.includes(user.role)) {
      console.log(
        `Access denied: user role "${user.role}" is not an admin role`,
      );
      router.replace("/search");
      return;
    }

    // 관리자라면 AgentHub 운영자 콘솔로 즉시 이동 (서버 redirects 보완)
    // 단, /admin 자체로 진입 시에만 (자식 페이지는 server-side redirect 가 가로챔)
    setRedirecting(true);
    if (typeof window !== "undefined") {
      window.location.href = `${AGENTHUB_URL}/admin/docutil-dashboard`;
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChecked(true);
  }, [isAuthenticated, user, router, _hasHydrated]);

  // 검사/리다이렉트 진행 중 — 안내 화면
  if (!checked || redirecting) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="flex max-w-md flex-col items-center gap-3 text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          {redirecting ? (
            <>
              <p className="text-sm font-medium text-gray-700">
                AgentHub 운영자 콘솔로 이동 중...
              </p>
              <p className="text-xs text-gray-500">
                DocUtil 운영자 페이지는 AgentHub 통합 콘솔로 흡수되었습니다.
                자동 이동되지 않으면{" "}
                <a
                  href={`${AGENTHUB_URL}/admin/docutil-dashboard`}
                  className="text-blue-600 underline"
                >
                  여기를 클릭
                </a>{" "}
                하세요.
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-500">Loading...</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-background min-h-screen">
      <AdminSidebar />

      {/* 본문 영역 — 사이드바 너비만큼 offset */}
      <div className="lg:pl-64">
        <Header />
        <main className="p-6">{children}</main>
      </div>

      <ToastContainer />
    </div>
  );
}
