'use client';

import { useState } from 'react';
import { GraduationCap, Target, TrendingUp, ChevronRight, LogOut } from 'lucide-react';
import { useAuth } from '@/lib/auth/authContext';
import type { StudentDetail } from '@/types';
import ProfileModal from './ProfileModal';

interface HeroProps {
  student: StudentDetail | null;
  loading?: boolean;
}

export default function Hero({ student, loading }: HeroProps) {
  const { user, logout } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  if (loading) {
    return (
      <div className="hero animate-pulse">
        <div className="h-8 bg-white/20 rounded w-1/3 mb-4"></div>
        <div className="h-6 bg-white/20 rounded w-1/2"></div>
      </div>
    );
  }

  // Use auth user data as fallback if student data is incomplete
  // Support both backend field names (department_cd, current_grade) and frontend aliases (department_id, grade)
  const displayName = student?.student_nm || user?.name || '이름 없음';
  const displayStudentId = student?.student_id || user?.studentId || '';
  const displayDepartment = student?.department?.department_nm
    || user?.departmentName
    || student?.department_cd
    || student?.department_id
    || '';
  const displayGrade = student?.current_grade || student?.grade || user?.grade || 0;

  return (
    <>
      <div className="hero">
        <div className="flex items-start justify-between">
          {/* Left: Profile Info - Clickable */}
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => setShowProfile(true)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && setShowProfile(true)}
          >
            <div className="w-14 h-14 bg-white/20 rounded-xl flex items-center justify-center group-hover:bg-white/30 transition-colors">
              <GraduationCap className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="hero-title">{displayName}</h1>
                <ChevronRight className="w-5 h-5 opacity-60 group-hover:opacity-100 group-hover:translate-x-1 transition-all" />
              </div>
              <p className="hero-subtitle">
                {displayStudentId} · {displayDepartment} · {displayGrade}학년
              </p>
            </div>
          </div>

          {/* Right: Stats & Logout */}
          <div className="flex items-center gap-6">
            <div className="flex gap-6 text-white/90">
              <div className="text-center">
                <div className="flex items-center gap-1 text-sm opacity-80">
                  <Target className="w-4 h-4" />
                  <span>목표 진로</span>
                </div>
                <p className="font-semibold mt-1">{student?.career_goal || '미설정'}</p>
              </div>
              <div className="text-center">
                <div className="flex items-center gap-1 text-sm opacity-80">
                  <TrendingUp className="w-4 h-4" />
                  <span>학점</span>
                </div>
                <p className="font-semibold mt-1">
                  {student?.gpa != null ? student.gpa.toFixed(2) : '0.00'} / 4.5
                </p>
              </div>
              <div className="text-center">
                <div className="text-sm opacity-80">이수학점</div>
                <p className="font-semibold mt-1">{student?.completed_credits || student?.summary?.completed_credits || student?.total_credits || 0}학점</p>
              </div>
            </div>

            {/* Logout Button */}
            <button
              onClick={logout}
              className="flex items-center gap-1 px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white/80 hover:text-white text-sm transition-colors"
              title="로그아웃"
            >
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">로그아웃</span>
            </button>
          </div>
        </div>
      </div>

      {/* Profile Modal */}
      <ProfileModal
        isOpen={showProfile}
        onClose={() => setShowProfile(false)}
        student={student}
      />
    </>
  );
}
