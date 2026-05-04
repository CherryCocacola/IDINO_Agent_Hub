'use client';

import { X, User, Mail, Phone, Calendar, BookOpen, Award, Briefcase } from 'lucide-react';
import type { StudentDetail } from '@/types';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  student: StudentDetail | null;
}

export default function ProfileModal({ isOpen, onClose, student }: ProfileModalProps) {
  if (!isOpen) return null;

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={handleOverlayClick}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto animate-fadeIn">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary to-secondary p-6 rounded-t-2xl relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 bg-white/20 hover:bg-white/30 rounded-full text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-4">
            <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-10 h-10 text-white" />
            </div>
            <div className="text-white">
              <h2 className="text-2xl font-bold">{student?.student_nm || '이름 없음'}</h2>
              <p className="text-white/80">{student?.student_id || ''}</p>
              <p className="text-white/80 text-sm mt-1">
                {student?.department?.department_nm || student?.department_cd || student?.department_id || ''} · {student?.current_grade || student?.grade || 0}학년 {student?.current_semester || student?.semester || 1}학기
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <User className="w-5 h-5 text-primary" />
              기본 정보
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <InfoItem label="영문명" value={student?.student_nm_en || '-'} />
              <InfoItem label="입학년도" value={student?.admission_year ? `${student.admission_year}년` : '-'} />
              <InfoItem label="졸업예정" value={student?.expected_graduation || '-'} />
              <InfoItem label="상태" value={getStatusLabel(student?.status_cd)} />
            </div>
          </section>

          {/* Contact Info */}
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Mail className="w-5 h-5 text-primary" />
              연락처
            </h3>
            <div className="space-y-2">
              <div className="flex items-center gap-3 text-gray-600">
                <Mail className="w-4 h-4 text-muted" />
                <span>{student?.email || '-'}</span>
              </div>
              <div className="flex items-center gap-3 text-gray-600">
                <Phone className="w-4 h-4 text-muted" />
                <span>{student?.phone || '-'}</span>
              </div>
            </div>
          </section>

          {/* Academic Info */}
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary" />
              학업 정보
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <InfoItem
                label="평점"
                value={student?.gpa != null ? `${student.gpa.toFixed(2)} / 4.5` : '-'}
              />
              <InfoItem
                label="총 이수학점"
                value={student?.total_credits != null ? `${student.total_credits}학점` : '-'}
              />
              {student?.summary && (
                <>
                  <InfoItem label="전공학점" value={`${student.summary.major_credits}학점`} />
                  <InfoItem label="교양학점" value={`${student.summary.liberal_credits}학점`} />
                  <InfoItem label="선택학점" value={`${student.summary.elective_credits}학점`} />
                  <InfoItem
                    label="졸업 준비도"
                    value={student.summary.graduation_readiness_pct != null
                      ? `${student.summary.graduation_readiness_pct.toFixed(1)}%`
                      : '-'}
                  />
                </>
              )}
            </div>
          </section>

          {/* Career Goal */}
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-primary" />
              진로 목표
            </h3>
            <div className="bg-gray-50 rounded-xl p-4">
              <p className="text-gray-700">{student?.career_goal || '목표가 설정되지 않았습니다.'}</p>
            </div>
          </section>

          {/* Activity Summary */}
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Award className="w-5 h-5 text-primary" />
              활동 현황
            </h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-primary/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-primary">{student?.enrollment_count || 0}</p>
                <p className="text-sm text-muted">수강 과목</p>
              </div>
              <div className="bg-secondary/10 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-secondary">{student?.activity_count || 0}</p>
                <p className="text-sm text-muted">활동 참여</p>
              </div>
              <div className="bg-accent/10 rounded-xl p-4 text-center">
                <p className="text-2xl font-bold text-accent">{student?.achievement_count || 0}</p>
                <p className="text-sm text-muted">자격/성취</p>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="p-6 pt-0">
          <button
            onClick={onClose}
            className="w-full py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-medium transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-muted">{label}</p>
      <p className="text-gray-800 font-medium">{value}</p>
    </div>
  );
}

function getStatusLabel(status?: string): string {
  const statusMap: Record<string, string> = {
    'ENROLLED': '재학',
    'ON_LEAVE': '휴학',
    'GRADUATED': '졸업',
    'WITHDRAWN': '자퇴',
  };
  return statusMap[status || ''] || status || '-';
}
