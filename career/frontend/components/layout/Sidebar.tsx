'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Zap,
  Target,
  MessageCircle,
  AlertTriangle,
  Briefcase,
  Calendar,
  FlaskConical,
  Award,
  Users,
  FolderKanban,
  Map,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import clsx from 'clsx';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  badge?: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    title: '메인',
    items: [
      { id: 'dashboard', label: '대시보드', icon: <LayoutDashboard className="w-5 h-5" />, href: '/' },
    ],
  },
  {
    title: 'P1 기능',
    items: [
      { id: 'skills', label: '스킬 관리', icon: <Zap className="w-5 h-5" />, href: '/skills' },
      { id: 'coaching', label: 'AI 코칭', icon: <MessageCircle className="w-5 h-5" />, href: '/coaching' },
      { id: 'risks', label: '위험 알림', icon: <AlertTriangle className="w-5 h-5" />, href: '/risks' },
      { id: 'opportunities', label: '기회 탐색', icon: <Briefcase className="w-5 h-5" />, href: '/opportunities' },
      { id: 'sprint', label: '스프린트', icon: <Calendar className="w-5 h-5" />, href: '/sprint' },
    ],
  },
  {
    title: 'P2 기능',
    items: [
      { id: 'simulation', label: 'What-if 시뮬레이션', icon: <FlaskConical className="w-5 h-5" />, href: '/simulation' },
      { id: 'passport', label: '스킬 패스포트', icon: <Award className="w-5 h-5" />, href: '/passport' },
      { id: 'advisor', label: '지도교수', icon: <Users className="w-5 h-5" />, href: '/advisor', badge: '교수용' },
      { id: 'portfolio', label: '포트폴리오', icon: <FolderKanban className="w-5 h-5" />, href: '/portfolio' },
      { id: 'roadmap-planner', label: '로드맵 플래너', icon: <Map className="w-5 h-5" />, href: '/roadmap-planner' },
    ],
  },
];

interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}

export default function Sidebar({ collapsed = false, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(collapsed);

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
    onToggle?.();
  };

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 h-screen bg-white border-r border-gray-200 transition-all duration-300 z-40',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
        {!isCollapsed && (
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Target className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-gray-900">CAREER V5</span>
          </Link>
        )}
        <button
          onClick={toggleSidebar}
          className={clsx(
            'p-2 rounded-lg hover:bg-gray-100 text-gray-500',
            isCollapsed && 'mx-auto'
          )}
        >
          {isCollapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
        </button>
      </div>

      {/* Navigation */}
      <nav className="p-2 space-y-4 overflow-y-auto h-[calc(100vh-4rem)]">
        {navGroups.map(group => (
          <div key={group.title}>
            {!isCollapsed && (
              <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {group.title}
              </div>
            )}
            <div className="space-y-1">
              {group.items.map(item => (
                <Link
                  key={item.id}
                  href={item.href}
                  className={clsx(
                    'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors relative',
                    isActive(item.href)
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-700 hover:bg-gray-100',
                    isCollapsed && 'justify-center'
                  )}
                  title={isCollapsed ? item.label : undefined}
                >
                  {item.icon}
                  {!isCollapsed && (
                    <>
                      <span className="flex-1">{item.label}</span>
                      {item.badge && (
                        <span className="px-1.5 py-0.5 text-xs bg-yellow-100 text-yellow-700 rounded">
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                  {isCollapsed && item.badge && (
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-400 rounded-full" />
                  )}
                </Link>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
