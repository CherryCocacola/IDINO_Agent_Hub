'use client';

import { useState, useEffect, lazy, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import Hero from '@/components/layout/Hero';
import QuickNav from '@/components/layout/QuickNav';
import Sidebar from '@/components/layout/Sidebar';
import OverviewSection from '@/components/sections/OverviewSection';
import CompetencySection from '@/components/sections/CompetencySection';
import RoadmapSection from '@/components/sections/RoadmapSection';
import AlumniSection from '@/components/sections/AlumniSection';
import { CourseDetailModal, ActivitiesModal, AchievementsModal } from '@/components/ui/Modal';
import { useDashboard } from '@/hooks/useDashboard';
import { useAuth } from '@/lib/auth/authContext';
import { Loader2, Zap, Menu, X, LogOut, User } from 'lucide-react';

// Lazy load ActionBoardSection to defer its loading after main content
const ActionBoardSection = lazy(() => import('@/components/sections/ActionBoardSection'));

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading: authLoading, logout } = useAuth();
  const [activeSection, setActiveSection] = useState('overview');
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [showActivitiesModal, setShowActivitiesModal] = useState(false);
  const [showAchievementsModal, setShowAchievementsModal] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Handle logout
  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  // Show loading or redirect while checking auth - MUST be before useDashboard
  // This prevents unauthorized data fetching
  const isAuthenticated = !authLoading && user !== null;

  // Fetch all dashboard data using authenticated user's studentId
  // Only fetch when authenticated to prevent unauthorized API calls
  const {
    student,
    courses,
    activities,
    achievements,
    competencyReport,
    alumniComparison,
    successPatterns,
    worknetJobs,
    loading,
    error,
  } = useDashboard(isAuthenticated ? user.studentId : null);

  // Show loading while checking auth
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

  // Don't render content if not authenticated (will redirect)
  if (!user) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted">로그인 페이지로 이동 중...</p>
        </div>
      </main>
    );
  }

  // Handle section navigation
  const scrollToSection = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Handle tile clicks
  const handleTileClick = (type: string) => {
    switch (type) {
      case 'courses':
        setShowCourseModal(true);
        break;
      case 'activities':
        setShowActivitiesModal(true);
        break;
      case 'achievements':
        setShowAchievementsModal(true);
        break;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-40 lg:hidden transform transition-transform ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar collapsed={false} />
      </div>

      {/* Main Content Area */}
      <div
        className={`transition-all duration-300 ${
          sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'
        }`}
      >
        {/* Top Bar */}
        <header className="sticky top-0 z-20 bg-white border-b border-gray-200 h-16">
          <div className="flex items-center justify-between h-full px-4">
            {/* Mobile Menu Button */}
            <button
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6 text-gray-600" />
              ) : (
                <Menu className="w-6 h-6 text-gray-600" />
              )}
            </button>

            {/* Page Title */}
            <div className="hidden lg:block">
              <span className="text-lg font-semibold text-gray-800">대시보드</span>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                  <User className="w-4 h-4 text-indigo-600" />
                </div>
                <div className="hidden sm:block">
                  <div className="font-medium text-gray-900">{user.name || user.studentId}</div>
                  <div className="text-xs text-gray-500">{user.studentId}</div>
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg hover:bg-gray-100 text-gray-500"
                title="로그아웃"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="min-h-screen pb-20 p-4 lg:p-6">
          {/* Header */}
          <div className="max-w-7xl mx-auto py-6">
            <Hero student={student} loading={loading} />
          </div>

          {/* Navigation */}
          <div className="max-w-7xl mx-auto mb-6">
            <QuickNav activeSection={activeSection} onSectionChange={scrollToSection} />
          </div>

          {/* Error Banner */}
          {error && (
            <div className="max-w-7xl mx-auto mb-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-800">
                ⚠️ {error}
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Overview Section */}
            <OverviewSection
              student={student}
              courses={courses}
              activities={activities}
              achievements={achievements}
              jobs={worknetJobs}
              onTileClick={handleTileClick}
            />

            {/* Competency Section */}
            <CompetencySection
              report={competencyReport}
              loading={loading}
            />

            {/* Roadmap Section */}
            <RoadmapSection student={student} />

            {/* Alumni Section */}
            <AlumniSection
              comparison={alumniComparison}
              patterns={successPatterns}
              loading={loading}
            />

            {/* Action Board Section - Deferred loading after main content */}
            {!loading && (
              <Suspense fallback={
                <section id="actions" className="section animate-fadeIn">
                  <h2 className="section-title">
                    <Zap className="w-5 h-5 text-primary" />
                    AI 액션보드
                    <Loader2 className="w-4 h-4 ml-2 animate-spin text-muted" />
                  </h2>
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-2" />
                      <p className="text-sm text-muted">AI 서비스 연결 중...</p>
                    </div>
                  </div>
                </section>
              }>
                <ActionBoardSection
                  studentId={user?.studentId}
                  departmentCd={student?.department_cd || student?.department_id}
                  departmentNm={student?.department?.department_nm}
                />
              </Suspense>
            )}
          </div>

          {/* Modals */}
          <CourseDetailModal
            isOpen={showCourseModal}
            onClose={() => setShowCourseModal(false)}
            courses={courses}
          />
          <ActivitiesModal
            isOpen={showActivitiesModal}
            onClose={() => setShowActivitiesModal(false)}
            activities={activities}
          />
          <AchievementsModal
            isOpen={showAchievementsModal}
            onClose={() => setShowAchievementsModal(false)}
            achievements={achievements}
          />

          {/* Footer */}
          <footer className="max-w-7xl mx-auto mt-12 py-6 border-t border-border">
            <div className="text-center text-sm text-muted">
              <p>AI 핵심역량 스튜디오 - CAREER V5</p>
              <p className="mt-1">© 2025 All rights reserved.</p>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
