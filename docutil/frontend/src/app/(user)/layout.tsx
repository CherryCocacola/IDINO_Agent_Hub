"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Header } from "@/components/layouts/header";
import { ToastContainer } from "@/components/layouts/toast-container";
import { UserSidebar } from "@/components/layouts/user-sidebar";
// 트랙 1-5 SSO 옵션 A (2026-05-26): AgentHub → DocUtil JWT 수신 컴포넌트.
import { SsoBootstrap } from "@/components/providers/sso-bootstrap";
import { useAuth } from "@/lib/hooks/use-auth";

/**
 * SSO 진입 가능성을 빠르게 판정.
 *
 * 트랙 1-5 SSO (2026-05-26): URL fragment 또는 cookie 에 SSO 토큰이 있으면
 * 본 layout 의 인증 체크를 잠시 보류한다 (SsoBootstrap 이 토큰을 처리하고
 * isAuthenticated=true 로 만들 때까지). 그렇지 않으면 SSO 진입 사용자가
 * 토큰이 적용되기 전에 /login 으로 리다이렉트되는 race 발생.
 */
function detectSsoEntry(): boolean {
  if (typeof window === "undefined") return false;
  // fragment 확인
  if (window.location.hash.includes("sso_token=")) return true;
  // cookie 확인
  if (typeof document !== "undefined" && document.cookie.includes("du_sso_token=")) {
    return true;
  }
  return false;
}

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, _hasHydrated } = useAuth();
  const [checked, setChecked] = useState(false);
  // SSO 진입 시 SsoBootstrap 의 비동기 처리(/users/me 호출) 가 완료될 때까지 대기.
  // 처음 한 번만 검사하면 충분 (URL fragment / cookie 는 SsoBootstrap 이 즉시 제거).
  const [ssoPending] = useState<boolean>(detectSsoEntry);

  useEffect(() => {
    // Zustand persist 하이드레이션 완료 전까지 인증 상태를 확인하지 않음
    // (하이드레이션 전에 확인하면 로그인된 사용자가 로그인 페이지로 리다이렉트됨)
    if (!_hasHydrated) return;

    // SSO 진입이 진행 중이면 인증 결과를 기다린다 (최대 ~3초).
    // SsoBootstrap 이 isAuthenticated=true 로 만들면 본 effect 가 재실행되어 setChecked(true).
    if (ssoPending && !isAuthenticated) {
      const timeoutId = window.setTimeout(() => {
        // 3초 안에 SSO 처리가 끝나지 않으면 기존 동작 (로그인 화면) 으로 fallback
        if (!useAuth.getState().isAuthenticated) {
          router.replace("/login");
        }
      }, 3000);
      return () => window.clearTimeout(timeoutId);
    }

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChecked(true);
  }, [isAuthenticated, router, _hasHydrated, ssoPending]);

  // Show nothing while checking authentication
  if (!checked) {
    return (
      <>
        {/* SSO 진입 시에도 즉시 마운트되어 토큰을 처리해야 함 */}
        <SsoBootstrap />
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
            <p className="text-sm text-gray-500">
              {ssoPending ? "AgentHub 인증 처리 중..." : "로딩 중..."}
            </p>
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* SSO bootstrap — 새 SSO 진입이 발생할 경우에도 즉시 처리.
          이미 처리된 진입은 useRef 가드로 중복 실행되지 않음. */}
      <SsoBootstrap />
      <UserSidebar />

      {/* Main content area - offset by sidebar width */}
      <div className="lg:pl-64">
        <Header />
        <main className="p-4 sm:p-6 lg:p-8">{children}</main>
      </div>

      <ToastContainer />
    </div>
  );
}
