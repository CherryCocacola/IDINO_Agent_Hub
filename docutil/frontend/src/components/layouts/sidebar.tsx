"use client";

import {
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  ExternalLink,
  ArrowLeftCircle,
} from "lucide-react";
import { useState, useEffect } from "react";

// ────────────────────────────────────────────────────────────────────────
// 트랙 A1 Phase E (2026-05-26): DocUtil 운영자 사이드바 완전 deprecate.
// 운영자 페이지 15개는 AgentHub `/admin/docutil-*` 로 흡수되었으며 next.config.ts
// 의 redirects() 가 서버 단계에서 302 처리한다. 본 사이드바는 클라이언트가
// 직접 URL 진입한 경우의 fallback UI — AgentHub 콘솔로 이동 + 사용자 화면 복귀
// 두 가지 액션만 노출한다.
// ────────────────────────────────────────────────────────────────────────

const AGENTHUB_URL =
  process.env.NEXT_PUBLIC_AGENTHUB_URL || "http://192.168.10.39:64005";

const APP_VERSION = "V1.0.0";

export function AdminSidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // ESC 키로 모바일 사이드바 닫기
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMobileOpen(false);
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  const sidebarContent = (
    <div className="border-border flex h-full flex-col border-r bg-white">
      {/* 헤더 — 로고 + 토글 */}
      <div className="border-border flex h-14 items-center justify-between border-b px-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <img
              src="/idino-logo.png"
              alt="IDINO"
              className="h-7 w-7 rounded object-contain"
            />
            <h1 className="text-foreground text-lg font-semibold tracking-tight">
              DocUtil
            </h1>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-muted-foreground hover:bg-muted hover:text-foreground hidden items-center gap-2 rounded-md p-2 lg:flex"
          aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
        {/* 모바일 닫기 */}
        <button
          onClick={() => setMobileOpen(false)}
          className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-2 lg:hidden"
          aria-label="사이드바 닫기"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* 본문 — AgentHub 콘솔 이동 안내 + 사용자 화면 복귀 */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {!collapsed && (
          <div className="mb-4 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            <p className="font-semibold">운영자 콘솔 통합 안내</p>
            <p className="mt-1">
              DocUtil 운영자 페이지는 AgentHub 운영자 콘솔로 통합되었습니다.
              아래 버튼을 통해 이동해 주세요.
            </p>
          </div>
        )}

        <ul className="space-y-2">
          <li>
            <a
              href={`${AGENTHUB_URL}/admin/docutil-dashboard`}
              target="_blank"
              rel="noopener noreferrer"
              className={`bg-primary text-primary-foreground hover:bg-primary/90 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                collapsed ? "justify-center" : ""
              }`}
              title={
                collapsed
                  ? "AgentHub 운영자 콘솔 (새 창)"
                  : undefined
              }
            >
              <ExternalLink className="h-5 w-5 shrink-0" />
              {!collapsed && <span>AgentHub 운영자 콘솔</span>}
            </a>
          </li>
          <li>
            <a
              href="/search"
              className={`text-foreground hover:bg-muted flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                collapsed ? "justify-center" : ""
              }`}
              title={collapsed ? "사용자 화면으로 돌아가기" : undefined}
            >
              <ArrowLeftCircle className="h-5 w-5 shrink-0" />
              {!collapsed && <span>사용자 화면으로</span>}
            </a>
          </li>
        </ul>
      </nav>

      {/* 버전 */}
      <div className="border-border border-t px-3 py-4">
        {!collapsed && (
          <p className="text-muted-foreground px-3 text-xs">{APP_VERSION}</p>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* 모바일 햄버거 버튼 */}
      <button
        onClick={() => setMobileOpen(true)}
        className="text-muted-foreground hover:text-foreground fixed top-4 left-4 z-40 rounded-md bg-white p-2 shadow-md lg:hidden"
        aria-label="사이드바 열기"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* 모바일 오버레이 */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* 모바일 사이드바 */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-200 ease-in-out lg:hidden ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {sidebarContent}
      </aside>

      {/* 데스크톱 사이드바 */}
      <aside
        className={`hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-30 lg:block ${
          collapsed ? "lg:w-[72px]" : "lg:w-64"
        } transition-all duration-200`}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
