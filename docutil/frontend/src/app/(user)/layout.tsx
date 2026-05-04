"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Header } from "@/components/layouts/header";
import { ToastContainer } from "@/components/layouts/toast-container";
import { UserSidebar } from "@/components/layouts/user-sidebar";
import { useAuth } from "@/lib/hooks/use-auth";

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, _hasHydrated } = useAuth();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    // Zustand persist 하이드레이션 완료 전까지 인증 상태를 확인하지 않음
    // (하이드레이션 전에 확인하면 로그인된 사용자가 로그인 페이지로 리다이렉트됨)
    if (!_hasHydrated) return;

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChecked(true);
  }, [isAuthenticated, router, _hasHydrated]);

  // Show nothing while checking authentication
  if (!checked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
          <p className="text-sm text-gray-500">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
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
