"use client";

import {
  LayoutDashboard,
  Building2,
  FolderTree,
  FileText,
  Target,
  Users,
  Key,
  Settings,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  LayoutTemplate,
  Bot,
  Activity,
  Gauge,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: "모니터링",
    items: [{ label: "대시보드", href: "/dashboard", icon: LayoutDashboard }],
  },
  {
    title: "조직 및 프로젝트 관리",
    items: [
      { label: "부서/조직 관리", href: "/departments", icon: Building2 },
      { label: "프로젝트 관리", href: "/projects", icon: FolderTree },
      { label: "문서 관리", href: "/documents", icon: FileText },
    ],
  },
  {
    title: "시스템 설정",
    items: [
      { label: "사용자 관리", href: "/admin-accounts", icon: Users },
      { label: "검색 범위 설정", href: "/search-scopes", icon: Target },
      { label: "API 키 관리", href: "/api-keys", icon: Key },
      { label: "템플릿 관리", href: "/templates", icon: LayoutTemplate },
      { label: "에이전트 관리", href: "/agents", icon: Bot },
      { label: "AI 품질 평가", href: "/evaluation", icon: Activity },
      { label: "쿼터 관리", href: "/quotas", icon: Gauge },
      { label: "설정", href: "/settings", icon: Settings },
    ],
  },
];

const APP_VERSION = "V1.0.0";

export function AdminSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMobileOpen(false);
  }, [pathname]);

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
    if (href === "/dashboard") {
      return pathname === "/dashboard";
    }
    return pathname.startsWith(href);
  };

  const sidebarContent = (
    <div className="border-border flex h-full flex-col border-r bg-white">
      {/* Collapse toggle */}
      <div className="border-border flex h-14 items-center justify-between border-b px-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <img src="/idino-logo.png" alt="IDINO" className="h-7 w-7 rounded object-contain" />
            <h1 className="text-foreground text-lg font-semibold tracking-tight">DocUtil</h1>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-muted-foreground hover:bg-muted hover:text-foreground hidden items-center gap-2 rounded-md p-2 lg:flex"
          aria-label={collapsed ? "사이드바 펼치기" : "사이드바 접기"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
        {/* Mobile close button */}
        <button
          onClick={() => setMobileOpen(false)}
          className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-2 lg:hidden"
          aria-label="사이드바 닫기"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {navSections.map((section) => (
          <div key={section.title} className="mb-6">
            {!collapsed && (
              <h3 className="text-muted-foreground mb-2 px-3 text-xs font-semibold tracking-wider uppercase">
                {section.title}
              </h3>
            )}
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                        active
                          ? "bg-primary text-primary-foreground"
                          : "text-foreground hover:bg-muted"
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
          </div>
        ))}
      </nav>

      {/* Version */}
      <div className="border-border border-t px-3 py-4">
        {!collapsed && <p className="text-muted-foreground px-3 text-xs">{APP_VERSION}</p>}
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="text-muted-foreground hover:text-foreground fixed top-4 left-4 z-40 rounded-md bg-white p-2 shadow-md lg:hidden"
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
