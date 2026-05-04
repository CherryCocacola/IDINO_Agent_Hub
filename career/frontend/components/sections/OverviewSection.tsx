'use client';

import { useState } from 'react';
import { BookOpen, Award, Briefcase, TrendingUp } from 'lucide-react';
import { WorknetJobModal, CreditDetailModal, AchievementsModal } from '@/components/ui/Modal';
import type { Student, CourseRecord, Activity, Achievement, WorknetJob, StudentDetail } from '@/types';

interface OverviewSectionProps {
  student: Student | null;
  courses: CourseRecord[];
  activities: Activity[];
  achievements: Achievement[];
  jobs: WorknetJob[];
  onTileClick?: (type: string) => void;
}

export default function OverviewSection({
  student,
  courses,
  activities,
  achievements,
  jobs,
  onTileClick,
}: OverviewSectionProps) {
  // State for Worknet job modal
  const [selectedJob, setSelectedJob] = useState<WorknetJob | null>(null);
  const [showJobModal, setShowJobModal] = useState(false);

  // State for Credit detail modal
  const [showCreditModal, setShowCreditModal] = useState(false);

  // State for Achievements modal
  const [showAchievementsModal, setShowAchievementsModal] = useState(false);

  // Handle job tag click
  const handleJobClick = (job: WorknetJob) => {
    setSelectedJob(job);
    setShowJobModal(true);
  };

  // Calculate statistics - prefer backend calculated values
  // Backend provides completed_credits directly from GPA calculation
  const studentDetail = student as StudentDetail | null;
  const totalCredits = studentDetail?.completed_credits || courses.reduce((sum, c) => sum + c.credits, 0);
  const completedActivities = activities.filter(a => a.status === 'completed').length;

  // Get certifications list for display
  const certifications = achievements.filter(a => a.achievement_type === 'certification' || a.achievement_type === 'certificate');
  const certificationCount = certifications.length;

  // Get credit breakdown from summary
  const summary = studentDetail?.summary || {
    completed_credits: totalCredits,
    major_credits: 0,
    liberal_credits: 0,
    elective_credits: 0,
  };

  // Format certification names for display (max 3, then +N)
  const displayCertNames = certifications.slice(0, 3).map(c => c.achievement_nm);
  const remainingCerts = certificationCount - 3;

  // Debug logging for troubleshooting
  console.log('📊 OverviewSection data:', {
    totalCredits,
    backendCredits: studentDetail?.completed_credits,
    courseCredits: courses.reduce((sum, c) => sum + c.credits, 0),
    gpa: student?.gpa,
    activitiesCount: activities.length,
    completedActivities,
    achievementsCount: achievements.length,
    certificationCount,
    summary: {
      major: summary.major_credits,
      liberal: summary.liberal_credits,
      elective: summary.elective_credits,
      rawSummary: studentDetail?.summary,
    },
  });

  return (
    <section id="overview" className="section animate-fadeIn">
      <h2 className="section-title">
        📊 전체 개요
      </h2>

      <div className="grid grid-cols-1 gap-6">
        {/* Tiles Grid */}
        <div>
          <div className="grid-tiles">
            {/* 이수학점 Tile - Enhanced with breakdown */}
            <div
              className="tile cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => setShowCreditModal(true)}
            >
              <div className="tile-header">
                <div className="tile-icon bg-primary">
                  <BookOpen className="w-5 h-5" />
                </div>
              </div>
              <p className="tile-label">이수학점</p>
              <p className="tile-value">{totalCredits}학점</p>
              <p className="text-sm text-muted mt-1">
                목표 130학점 중 {Math.round((totalCredits / 130) * 100)}%
              </p>
              {/* Credit Breakdown */}
              {(summary.major_credits > 0 || summary.liberal_credits > 0) && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <div className="flex gap-2 text-xs">
                    <span className="text-blue-600">전공 {summary.major_credits}</span>
                    <span className="text-gray-300">|</span>
                    <span className="text-green-600">교양 {summary.liberal_credits}</span>
                    {summary.elective_credits > 0 && (
                      <>
                        <span className="text-gray-300">|</span>
                        <span className="text-orange-600">기타 {summary.elective_credits}</span>
                      </>
                    )}
                  </div>
                </div>
              )}
              <p className="text-xs text-primary mt-1">클릭하여 상세보기 →</p>
            </div>

            {/* 평균학점 Tile */}
            <div className="tile">
              <div className="tile-header">
                <div className="tile-icon bg-secondary">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <span className="text-sm font-medium text-green-500">↑</span>
              </div>
              <p className="tile-label">평균학점</p>
              <p className="tile-value">{student?.gpa?.toFixed(2) || '0.00'}</p>
              <p className="text-sm text-muted mt-1">4.5 만점 기준</p>
            </div>

            {/* 비교과활동 Tile */}
            <div
              className="tile cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => onTileClick?.('activities')}
            >
              <div className="tile-header">
                <div className="tile-icon bg-accent">
                  <Award className="w-5 h-5" />
                </div>
              </div>
              <p className="tile-label">비교과활동</p>
              <p className="tile-value">{completedActivities}건</p>
              {activities.length > completedActivities && (
                <p className="text-sm text-muted mt-1">
                  진행중 {activities.length - completedActivities}건
                </p>
              )}
            </div>

            {/* 자격증 Tile - Enhanced with names */}
            <div
              className="tile cursor-pointer hover:shadow-lg transition-shadow"
              onClick={() => setShowAchievementsModal(true)}
            >
              <div className="tile-header">
                <div className="tile-icon bg-ethics">
                  <Briefcase className="w-5 h-5" />
                </div>
              </div>
              <p className="tile-label">자격증</p>
              <p className="tile-value">{certificationCount}개</p>
              {/* Certification Names List */}
              {certificationCount > 0 ? (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <div className="space-y-1">
                    {displayCertNames.map((name, idx) => (
                      <p key={idx} className="text-xs text-muted truncate flex items-center gap-1">
                        <span className="text-primary">•</span>
                        {name}
                      </p>
                    ))}
                    {remainingCerts > 0 && (
                      <p className="text-xs text-primary font-medium">
                        +{remainingCerts}개 더보기
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted mt-1">취득 자격증</p>
              )}
              <p className="text-xs text-primary mt-1">클릭하여 상세보기 →</p>
            </div>
          </div>

          {/* Worknet Job Info */}
          <div className="mt-6 p-4 bg-gradient-to-r from-primary/5 to-secondary/5 rounded-xl">
            <h3 className="font-semibold text-text mb-3 flex items-center gap-2">
              🔍 워크넷 관심 직업
            </h3>
            <div className="flex flex-wrap gap-2">
              {jobs.slice(0, 5).map((job, index) => (
                <span
                  key={index}
                  onClick={() => handleJobClick(job)}
                  className="px-3 py-1.5 bg-white rounded-lg text-sm text-text border border-border hover:border-primary hover:bg-primary/5 cursor-pointer transition-colors"
                >
                  {job.job_name}
                </span>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* Worknet Job Modal */}
      <WorknetJobModal
        isOpen={showJobModal}
        onClose={() => setShowJobModal(false)}
        job={selectedJob}
      />

      {/* Credit Detail Modal */}
      <CreditDetailModal
        isOpen={showCreditModal}
        onClose={() => setShowCreditModal(false)}
        summary={summary}
        courses={courses}
      />

      {/* Achievements Modal */}
      <AchievementsModal
        isOpen={showAchievementsModal}
        onClose={() => setShowAchievementsModal(false)}
        achievements={achievements.map(a => ({
          achievement_name: a.achievement_nm,
          achievement_type: a.achievement_type,
          issue_date: a.issue_date || '',
          issuer: a.issuing_org,
          score: a.score || a.level,
        }))}
      />
    </section>
  );
}
