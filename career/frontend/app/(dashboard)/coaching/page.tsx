'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/authContext';
import { ArrowLeft, MessageSquare, Target, CheckSquare } from 'lucide-react';
import Link from 'next/link';
import CoachingChatSection from '@/components/sections/CoachingChatSection';
import GoalManagementSection from '@/components/sections/GoalManagementSection';

export default function CoachingPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'chat' | 'goals'>('chat');

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
    { id: 'chat', label: 'AI 코치', icon: <MessageSquare className="w-4 h-4" /> },
    { id: 'goals', label: '목표 관리', icon: <Target className="w-4 h-4" /> },
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
            <h1 className="text-2xl font-bold text-text">AI 코칭</h1>
            <p className="text-sm text-muted mt-1">
              AI 코치와 대화하고 목표를 관리하세요
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'chat' | 'goals')}
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
        {activeTab === 'chat' ? (
          <CoachingChatSection studentId={user.studentId} />
        ) : (
          <GoalManagementSection studentId={user.studentId} />
        )}
      </div>
    </main>
  );
}
