'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/authContext';
import { ArrowLeft, Network, TrendingUp, Target } from 'lucide-react';
import Link from 'next/link';
import SkillGraphSection from '@/components/sections/SkillGraphSection';
import SkillGapSection from '@/components/sections/SkillGapSection';

export default function SkillsPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'graph' | 'gap'>('graph');
  const [selectedRole, setSelectedRole] = useState<string>('');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  if (authLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted">로딩 중...</p>
        </div>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  const tabs = [
    { id: 'graph', label: '스킬 그래프', icon: <Network className="w-4 h-4" /> },
    { id: 'gap', label: '갭 분석', icon: <TrendingUp className="w-4 h-4" /> },
  ];

  return (
    <main className="min-h-screen pb-20">
      {/* Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center gap-4 mb-6">
          <Link
            href="/"
            className="p-2 rounded-lg hover:bg-hover transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-text">스킬 관리</h1>
            <p className="text-sm text-muted mt-1">
              스킬 그래프 시각화 및 목표 역할 대비 갭 분석
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'graph' | 'gap')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-primary text-white'
                  : 'bg-card hover:bg-hover text-text'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {activeTab === 'graph' ? (
          <SkillGraphSection
            studentId={user.studentId}
            selectedRole={selectedRole}
            onRoleChange={setSelectedRole}
          />
        ) : (
          <SkillGapSection
            studentId={user.studentId}
            selectedRole={selectedRole}
            onRoleChange={setSelectedRole}
          />
        )}
      </div>
    </main>
  );
}
