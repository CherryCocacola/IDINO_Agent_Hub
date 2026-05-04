'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/authContext';
import { ArrowLeft, LayoutList, Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import SprintBoardSection from '@/components/sections/SprintBoardSection';

export default function SprintPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [currentWeek, setCurrentWeek] = useState(1);

  // Get current semester info
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;
  const semester = month >= 3 && month <= 8 ? 1 : 2;
  const semesterLabel = `${year}-${semester}`;

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

  const handlePrevWeek = () => {
    if (currentWeek > 1) {
      setCurrentWeek(currentWeek - 1);
    }
  };

  const handleNextWeek = () => {
    if (currentWeek < 16) {
      setCurrentWeek(currentWeek + 1);
    }
  };

  return (
    <main className="min-h-screen pb-20">
      {/* Header */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="p-2 rounded-lg hover:bg-hover transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <LayoutList className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-text">학기 스프린트</h1>
                <p className="text-sm text-muted mt-1">
                  주간 할 일을 관리하고 목표를 달성하세요
                </p>
              </div>
            </div>
          </div>

          {/* Semester & Week Selector */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="w-4 h-4 text-muted" />
              <span className="font-medium">{semesterLabel} 학기</span>
            </div>
            <div className="flex items-center gap-2 bg-card rounded-lg p-1">
              <button
                onClick={handlePrevWeek}
                disabled={currentWeek === 1}
                className="p-1 rounded hover:bg-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="px-3 font-medium">{currentWeek}주차</span>
              <button
                onClick={handleNextWeek}
                disabled={currentWeek === 16}
                className="p-1 rounded hover:bg-hover disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <SprintBoardSection
          studentId={user.studentId}
          semester={semesterLabel}
          weekNumber={currentWeek}
        />
      </div>
    </main>
  );
}
