"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/hooks/use-auth";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user, _hasHydrated } = useAuth();

  useEffect(() => {
    // Zustand persist 하이드레이션 완료 전까지 대기
    if (!_hasHydrated) return;

    if (isAuthenticated && user) {
      // 관리자 역할은 대시보드로, 일반 사용자는 검색 페이지로 리다이렉트
      const adminRoles = ["super_admin", "admin", "org_admin"];
      if (adminRoles.includes(user.role)) {
        router.replace("/dashboard");
      } else {
        router.replace("/search");
      }
    } else {
      // 미인증 사용자는 로그인 페이지로 리다이렉트
      router.replace("/login");
    }
  }, [router, isAuthenticated, user, _hasHydrated]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-muted-foreground">Loading...</div>
    </div>
  );
}
