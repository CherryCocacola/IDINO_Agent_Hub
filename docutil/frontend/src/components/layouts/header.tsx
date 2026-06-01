"use client";

import { User, LogOut, Plus, Shield, LayoutDashboard, Clock, ExternalLink } from "lucide-react";
import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import { useState, useRef, useEffect, useCallback } from "react";

import { useAuth } from "@/lib/hooks/use-auth";

/** 남은 밀리초를 MM:SS 형식으로 변환 */
function formatRemaining(ms: number): string {
  if (ms <= 0) return "00:00";
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

/** 남은 밀리초에 따른 색상 클래스 반환 */
function getTimerColor(ms: number): string {
  if (ms < 60_000) return "text-red-600"; // 1분 미만
  if (ms < 300_000) return "text-yellow-600"; // 5분 미만
  return "text-green-600"; // 5분 이상
}

export function Header() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout, tokenExpiresAt } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [remainingMs, setRemainingMs] = useState<number | null>(null);

  const adminRoles = ["super_admin", "admin", "org_admin"];
  const isAdmin = user?.role && adminRoles.includes(user.role);
  // 트랙 A1 Phase E (2026-06-01) — DocUtil 운영자 페이지 15개는 모두 AgentHub
  // 콘솔로 redirect 됨. 본 변수는 fallback UI(사이드바 deprecate 진입 직전) 판단용.
  const isAdminPage = [
    "/dashboard",
    "/departments",
    "/projects",
    "/documents",
    "/admin-accounts",
    "/search-scopes",
    "/api-keys",
    "/settings",
    "/templates",
    "/agents",
    "/search-test",
    "/help",
    "/quick-guide",
  ].some((p) => pathname.startsWith(p));

  // AgentHub 운영자 콘솔 URL (환경별 주입, next.config.ts 와 동일 키).
  const AGENTHUB_URL =
    process.env.NEXT_PUBLIC_AGENTHUB_URL || "http://192.168.10.39:64005";
  const menuRef = useRef<HTMLDivElement>(null);

  // 드롭다운 외부 클릭 감지
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = useCallback(() => {
    logout();
    router.push("/login");
  }, [logout, router]);

  // 세션 카운트다운 타이머
  useEffect(() => {
    if (!tokenExpiresAt) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setRemainingMs(null);
      return;
    }

    const tick = () => {
      const remaining = tokenExpiresAt - Date.now();
      if (remaining <= 0) {
        // 세션 만료 — 자동 로그아웃
        handleLogout();
        return;
      }
      setRemainingMs(remaining);
    };

    // 즉시 한 번 실행 후 1초 간격으로 갱신
    tick();
    const intervalId = setInterval(tick, 1000);
    return () => clearInterval(intervalId);
  }, [tokenExpiresAt, handleLogout]);

  return (
    <header className="border-border sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-white px-4 sm:px-6">
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        {/* Spacer for mobile hamburger */}
        <div className="w-8 lg:hidden" />

        {/* Logo */}
        <div className="flex items-center gap-2">
          <img src="/idino-logo.png" alt="IDINO" className="h-8 w-8 rounded object-contain" />
          <span className="text-foreground text-xl font-bold">DocUtil</span>
        </div>
      </div>

      {/* Right: Switch + Timer + User avatar and logout */}
      <div className="flex items-center gap-3">
        {/* Admin/User switch button — 트랙 A1 Phase E (2026-06-01):
            "관리자 화면" 은 새 탭에서 AgentHub 운영자 콘솔로 직접 이동.
            기존 router.push("/dashboard") → redirect 흐름은 같은 탭 navigation
            으로 사용자가 컨텍스트(DocUtil)를 잃어버림. 명시적 새 탭으로 컨텍스트 보존. */}
        {isAdmin && (
          <button
            onClick={() =>
              isAdminPage
                ? router.push("/search")
                : window.open(`${AGENTHUB_URL}/admin/docutil-dashboard`, "_blank", "noopener,noreferrer")
            }
            className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:bg-gray-50"
            title={isAdminPage ? "사용자 화면으로 돌아가기" : "AgentHub 운영자 콘솔 열기 (새 탭)"}
          >
            {isAdminPage ? (
              <>
                <LayoutDashboard className="h-4 w-4 text-blue-600" />
                <span className="hidden sm:inline">사용자 화면</span>
              </>
            ) : (
              <>
                <Shield className="h-4 w-4 text-orange-600" />
                <span className="hidden sm:inline">운영자 콘솔</span>
                <ExternalLink className="h-3.5 w-3.5 text-orange-600" />
              </>
            )}
          </button>
        )}

        {/* 세션 남은 시간 카운트다운 */}
        {remainingMs !== null && (
          <div
            className={`flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 font-mono text-sm font-medium tabular-nums ${getTimerColor(remainingMs)}`}
            title="세션 남은 시간"
            aria-label={`세션 남은 시간 ${formatRemaining(remainingMs)}`}
          >
            <Clock className="h-4 w-4" />
            <span>{formatRemaining(remainingMs)}</span>
          </div>
        )}

        {/* User menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="hover:bg-muted flex items-center gap-3 rounded-lg px-3 py-2"
            aria-label="사용자 메뉴"
            aria-expanded={userMenuOpen}
          >
            <div className="bg-primary text-primary-foreground flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium">
              {user?.username?.charAt(0).toUpperCase() || "U"}
            </div>
            <span className="text-foreground hidden text-sm font-medium md:block">
              {user?.username || "User"}
            </span>
          </button>

          {/* Dropdown menu */}
          {userMenuOpen && (
            <div className="border-border absolute right-0 mt-2 w-56 rounded-lg border bg-white py-1 shadow-lg">
              {/* User info */}
              <div className="border-border border-b px-4 py-3">
                <p className="text-foreground text-sm font-medium">{user?.username}</p>
                <p className="text-muted-foreground truncate text-xs">{user?.email}</p>
                <p className="text-muted-foreground mt-0.5 text-xs capitalize">
                  {user?.role?.replace("_", " ")}
                </p>
              </div>

              {/* Profile */}
              <button
                onClick={() => {
                  setUserMenuOpen(false);
                  router.push("/settings");
                }}
                className="text-foreground hover:bg-muted flex w-full items-center gap-3 px-4 py-2.5 text-sm"
              >
                <User className="h-4 w-4" />
                <span>프로필</span>
              </button>

              <div className="border-border border-t" />

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="text-destructive hover:bg-destructive/10 flex w-full items-center gap-3 px-4 py-2.5 text-sm"
              >
                <LogOut className="h-4 w-4" />
                <span>로그아웃</span>
              </button>
            </div>
          )}
        </div>

        {/* Logout button (always visible on desktop) */}
        <button
          onClick={handleLogout}
          className="text-muted-foreground hover:bg-muted hover:text-foreground hidden items-center gap-2 rounded-lg px-3 py-2 md:flex"
          aria-label="로그아웃"
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}
