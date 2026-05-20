"use client";

import {
  Search,
  Upload,
  MessageSquare,
  FileOutput,
  Sparkles,
  Menu,
  X,
  LogOut,
  ChevronLeft,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

import { useAuth } from "@/lib/hooks/use-auth";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { label: "문서 검색", href: "/search", icon: Search },
  { label: "문서 업로드", href: "/my-documents", icon: Upload },
  { label: "챗봇", href: "/chat", icon: MessageSquare },
  { label: "보고서", href: "/reports", icon: FileOutput },
  // Phase 4 S1: Mode A 자유 생성 디자이너 (DocumentSchema 기반 신규 시스템)
  // 기존 /reports 와 공존. /reports 는 S7 에서 폐기 예정.
  { label: "문서 디자이너 (Beta)", href: "/designer/create", icon: Sparkles },
];

export function UserSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile sidebar on route change
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMobileOpen(false);
  }, [pathname]);

  // Close mobile sidebar on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMobileOpen(false);
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  const isActive = (href: string) => {
    return pathname.startsWith(href);
  };

  const sidebarContent = (
    <div className="flex h-full flex-col bg-gray-900 text-gray-100">
      {/* Logo / Title */}
      <div className="flex h-16 items-center justify-between border-b border-gray-700 px-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <img src="/g2-logo.png" alt="G2 SOFT" className="h-7 w-7 rounded object-contain" />
            <h1 className="text-lg font-semibold tracking-tight text-white">DocUtil</h1>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden rounded-md p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white lg:block"
          aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
        >
          <ChevronLeft
            className={`h-5 w-5 transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`}
          />
        </button>
        {/* Mobile close button */}
        <button
          onClick={() => setMobileOpen(false)}
          className="rounded-md p-1.5 text-gray-400 hover:bg-gray-800 hover:text-white lg:hidden"
          aria-label="사이드바 닫기"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  } ${collapsed ? "justify-center" : ""}`}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User info + Logout */}
      <div className="border-t border-gray-700 px-3 py-4">
        {!collapsed && user && (
          <div className="mb-3 px-3">
            <p className="truncate text-sm font-medium text-white">{user.username}</p>
            <p className="truncate text-xs text-gray-400">{user.email}</p>
          </div>
        )}
        <button
          onClick={logout}
          className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-300 transition-colors hover:bg-gray-800 hover:text-white ${
            collapsed ? "justify-center" : ""
          }`}
          title={collapsed ? "로그아웃" : undefined}
        >
          <LogOut className="h-5 w-5 shrink-0" />
          {!collapsed && <span>로그아웃</span>}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-40 rounded-md bg-gray-900 p-2 text-gray-400 hover:text-white lg:hidden"
        aria-label="사이드바 열기"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-200 ease-in-out lg:hidden ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Desktop sidebar */}
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
