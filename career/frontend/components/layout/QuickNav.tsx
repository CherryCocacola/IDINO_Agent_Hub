'use client';

import {
  LayoutDashboard,
  BarChart3,
  Map,
  Users,
  Zap
} from 'lucide-react';
import clsx from 'clsx';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

interface QuickNavProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const navItems: NavItem[] = [
  { id: 'overview', label: '전체 개요', icon: <LayoutDashboard className="w-4 h-4" /> },
  { id: 'competency', label: '역량 분석', icon: <BarChart3 className="w-4 h-4" /> },
  { id: 'roadmap', label: '학년 로드맵', icon: <Map className="w-4 h-4" /> },
  { id: 'alumni', label: '졸업생 비교', icon: <Users className="w-4 h-4" /> },
  { id: 'actions', label: 'AI 액션보드', icon: <Zap className="w-4 h-4" /> },
];

export default function QuickNav({ activeSection, onSectionChange }: QuickNavProps) {
  return (
    <nav className="quick-nav sticky top-4 z-10">
      {navItems.map((item) => (
        <button
          key={item.id}
          className={clsx(
            'quick-nav-item flex items-center gap-2',
            activeSection === item.id && 'active'
          )}
          onClick={() => onSectionChange(item.id)}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
