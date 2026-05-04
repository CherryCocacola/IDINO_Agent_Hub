'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/authContext';
import { ArrowLeft, Briefcase, Star, ClipboardList } from 'lucide-react';
import Link from 'next/link';
import OpportunityListSection from '@/components/sections/OpportunityListSection';

export default function OpportunitiesPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'all' | 'recommended' | 'applications'>('recommended');

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
    { id: 'recommended', label: '추천', icon: <Star className="w-4 h-4" /> },
    { id: 'all', label: '전체 목록', icon: <Briefcase className="w-4 h-4" /> },
    { id: 'applications', label: '내 지원', icon: <ClipboardList className="w-4 h-4" /> },
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
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100">
              <Briefcase className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-text">기회 마켓플레이스</h1>
              <p className="text-sm text-muted mt-1">
                인턴십, 공모전, 자격증 등 다양한 기회를 탐색하세요
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'all' | 'recommended' | 'applications')}
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
        <OpportunityListSection
          studentId={user.studentId}
          viewMode={activeTab}
        />
      </div>
    </main>
  );
}
