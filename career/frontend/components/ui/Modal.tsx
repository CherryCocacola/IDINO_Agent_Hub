'use client';

import { useEffect } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
};

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}: ModalProps) {
  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={clsx(
          'modal-content animate-fadeIn',
          sizeClasses[size]
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-text">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-muted" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

// Course Detail Modal
interface CourseDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  courses: Array<{
    course_name: string;
    course_code: string;
    semester: string;
    credits: number;
    grade: string;
    course_type: string;
  }>;
}

export function CourseDetailModal({ isOpen, onClose, courses }: CourseDetailModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="이수 교과목 상세" size="lg">
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>학기</th>
              <th>과목명</th>
              <th>구분</th>
              <th>학점</th>
              <th>성적</th>
            </tr>
          </thead>
          <tbody>
            {courses.map((course, index) => (
              <tr key={index}>
                <td>{course.semester}</td>
                <td>
                  <div>
                    <p className="font-medium">{course.course_name}</p>
                    <p className="text-xs text-muted">{course.course_code}</p>
                  </div>
                </td>
                <td>
                  <span className={clsx(
                    'badge',
                    course.course_type.includes('전공') ? 'badge-primary' : 'badge-secondary'
                  )}>
                    {course.course_type}
                  </span>
                </td>
                <td>{course.credits}</td>
                <td>
                  <span className={clsx(
                    'badge',
                    course.grade.startsWith('A') && 'badge-primary',
                    course.grade.startsWith('B') && 'badge-secondary',
                    course.grade.startsWith('C') && 'badge-warning'
                  )}>
                    {course.grade}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}

// Activities Detail Modal
interface ActivitiesModalProps {
  isOpen: boolean;
  onClose: () => void;
  activities: Array<{
    activity_name: string;
    activity_type: string;
    start_date?: string;
    end_date?: string;
    status: string;
    hours?: number;
    description?: string;
  }>;
}

export function ActivitiesModal({ isOpen, onClose, activities }: ActivitiesModalProps) {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="badge badge-primary">완료</span>;
      case 'in_progress':
        return <span className="badge badge-secondary">진행중</span>;
      case 'planned':
        return <span className="badge badge-warning">예정</span>;
      default:
        return <span className="badge">{status}</span>;
    }
  };

  const getTypeBadge = (type: string) => {
    const typeMap: Record<string, string> = {
      internship: '인턴십',
      volunteer: '봉사활동',
      competition: '대회/공모전',
      club: '동아리',
      study: '스터디',
      project: '프로젝트',
      seminar: '세미나/워크샵',
    };
    return typeMap[type] || type;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="비교과활동 상세" size="lg">
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {activities.length === 0 ? (
          <div className="text-center py-8 text-muted">
            <p>등록된 비교과활동이 없습니다.</p>
          </div>
        ) : (
          activities.map((activity, index) => (
            <div
              key={index}
              className="p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h4 className="font-semibold text-text">{activity.activity_name}</h4>
                  <p className="text-sm text-muted">{getTypeBadge(activity.activity_type)}</p>
                </div>
                {getStatusBadge(activity.status)}
              </div>
              <div className="flex items-center gap-4 text-xs text-muted mt-2">
                <span>📅 {activity.start_date || '미정'} ~ {activity.end_date || '진행중'}</span>
                {activity.hours && <span>⏱️ {activity.hours}시간</span>}
              </div>
              {activity.description && (
                <p className="text-sm text-muted mt-2">{activity.description}</p>
              )}
            </div>
          ))
        )}
      </div>
    </Modal>
  );
}

// Achievements Detail Modal
interface AchievementsModalProps {
  isOpen: boolean;
  onClose: () => void;
  achievements: Array<{
    achievement_nm?: string;
    achievement_name?: string;
    achievement_type: string;
    issue_date?: string;
    issuer?: string;
    issuing_org?: string;
    score?: string;
    level?: string;
    description?: string;
  }>;
}

export function AchievementsModal({ isOpen, onClose, achievements }: AchievementsModalProps) {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'certification':
      case 'certificate':
        return '🏆';
      case 'award':
        return '🥇';
      case 'language':
        return '🌍';
      case 'competition':
        return '🎯';
      default:
        return '📜';
    }
  };

  const getTypeName = (type: string) => {
    const typeMap: Record<string, string> = {
      certification: '자격증',
      certificate: '자격증',
      award: '수상',
      language: '어학',
      competition: '대회입상',
    };
    return typeMap[type] || type;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="자격증/수상 상세" size="lg">
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>구분</th>
              <th>명칭</th>
              <th>발급기관</th>
              <th>취득일</th>
              <th>점수/등급</th>
            </tr>
          </thead>
          <tbody>
            {achievements.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-8 text-muted">
                  등록된 자격증/수상 내역이 없습니다.
                </td>
              </tr>
            ) : (
              achievements.map((achievement, index) => (
                <tr key={index}>
                  <td>
                    <span className="flex items-center gap-1">
                      {getTypeIcon(achievement.achievement_type)}
                      {getTypeName(achievement.achievement_type)}
                    </span>
                  </td>
                  <td>
                    <p className="font-medium">{achievement.achievement_nm || achievement.achievement_name || '-'}</p>
                    {achievement.description && (
                      <p className="text-xs text-muted">{achievement.description}</p>
                    )}
                  </td>
                  <td>{achievement.issuing_org || achievement.issuer || '-'}</td>
                  <td>{achievement.issue_date || '-'}</td>
                  <td>{achievement.score ? parseFloat(String(achievement.score)).toFixed(1) : achievement.level || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}

// Action Detail Modal
interface ActionDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExecute?: (action: {
    id: number;
    title: string;
    description: string;
    priority: string;
    deadline?: string;
    competency?: string;
    reasoning?: string;
  }) => void;
  action: {
    id: number;
    title: string;
    description: string;
    priority: string;
    deadline?: string;
    competency?: string;
    reasoning?: string;
  } | null;
}

export function ActionDetailModal({ isOpen, onClose, onExecute, action }: ActionDetailModalProps) {
  if (!action) return null;

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case 'high':
        return { label: '긴급', className: 'badge-error' };
      case 'medium':
        return { label: '권장', className: 'badge-warning' };
      default:
        return { label: '선택', className: '' };
    }
  };

  const { label, className } = getPriorityLabel(action.priority);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="AI 추천 액션 상세" size="md">
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold text-text">{action.title}</h3>
          <span className={clsx('badge', className)}>{label}</span>
        </div>

        <p className="text-muted">{action.description}</p>

        <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl">
          <div>
            <p className="text-xs text-muted mb-1">마감기한</p>
            <p className="font-medium">⏰ {action.deadline || '미정'}</p>
          </div>
          <div>
            <p className="text-xs text-muted mb-1">연관 역량</p>
            <p className="font-medium">🎯 {action.competency || '-'}</p>
          </div>
        </div>

        {action.reasoning && (
          <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
            <p className="text-xs text-blue-600 mb-1">💡 AI 분석 근거</p>
            <p className="text-sm text-blue-800">{action.reasoning}</p>
          </div>
        )}

        <div className="flex gap-2 pt-4">
          <button
            onClick={onClose}
            className="flex-1 py-2 px-4 bg-gray-100 text-text rounded-lg hover:bg-gray-200 transition-colors"
          >
            닫기
          </button>
          <button
            onClick={() => {
              if (onExecute) {
                onExecute(action);
              }
              onClose();
            }}
            className="flex-1 py-2 px-4 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            실행하기
          </button>
        </div>
      </div>
    </Modal>
  );
}

// Worknet Job Detail Modal
interface WorknetJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: {
    job_name: string;
    job_code?: string;
    description?: string;
    required_skills?: string[];
    average_salary?: number | string;
    employment_outlook?: string;
    employment_trend?: string;
  } | null;
}

export function WorknetJobModal({ isOpen, onClose, job }: WorknetJobModalProps) {
  if (!job) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="워크넷 직업 상세" size="md">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-text">{job.job_name}</h3>
          {job.job_code && (
            <p className="text-xs text-muted">직업코드: {job.job_code}</p>
          )}
        </div>

        {job.description && (
          <div className="p-4 bg-gray-50 rounded-xl">
            <p className="text-xs text-muted mb-1">직업 설명</p>
            <p className="text-sm text-text">{job.description}</p>
          </div>
        )}

        {job.required_skills && job.required_skills.length > 0 && (
          <div>
            <p className="text-xs text-muted mb-2">필요 역량</p>
            <div className="flex flex-wrap gap-2">
              {job.required_skills.map((skill, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {job.average_salary && (
            <div className="p-3 bg-green-50 rounded-lg">
              <p className="text-xs text-green-600 mb-1">💰 평균 연봉</p>
              <p className="font-medium text-green-800">
                {typeof job.average_salary === 'number'
                  ? `${job.average_salary.toLocaleString()}만원`
                  : job.average_salary}
              </p>
            </div>
          )}
          {(job.employment_outlook || job.employment_trend) && (
            <div className="p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-600 mb-1">📈 고용 전망</p>
              <p className="font-medium text-blue-800">{job.employment_outlook || job.employment_trend}</p>
            </div>
          )}
        </div>

        <div className="flex gap-2 pt-4">
          <button
            onClick={onClose}
            className="flex-1 py-2 px-4 bg-gray-100 text-text rounded-lg hover:bg-gray-200 transition-colors"
          >
            닫기
          </button>
          <a
            href={`https://www.work.go.kr/consltJobCarpa/srch/jobInfoSrch/srchJobInfo.do?jobNm=${encodeURIComponent(job.job_name)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 py-2 px-4 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-center"
          >
            워크넷에서 보기
          </a>
        </div>
      </div>
    </Modal>
  );
}

// Credit Detail Modal (for credit breakdown and course list)
interface CreditDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: {
    major_credits: number;
    liberal_credits: number;
    elective_credits: number;
    completed_credits: number;
  } | null;
  courses: Array<{
    course_name: string;
    course_code: string;
    semester: string;
    credits: number;
    grade: string;
    course_type: string;
  }>;
}

export function CreditDetailModal({ isOpen, onClose, summary, courses }: CreditDetailModalProps) {
  // Group courses by type
  const majorCourses = courses.filter(c => c.course_type.includes('전공') || c.course_type === 'major');
  const liberalCourses = courses.filter(c => c.course_type.includes('교양') || c.course_type === 'liberal');
  const electiveCourses = courses.filter(c =>
    !c.course_type.includes('전공') && c.course_type !== 'major' &&
    !c.course_type.includes('교양') && c.course_type !== 'liberal'
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="이수학점 상세" size="lg">
      <div className="space-y-6">
        {/* Credit Summary */}
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 bg-primary/10 rounded-xl text-center">
            <p className="text-xs text-muted mb-1">총 이수</p>
            <p className="text-2xl font-bold text-primary">{summary?.completed_credits || 0}</p>
          </div>
          <div className="p-4 bg-blue-50 rounded-xl text-center">
            <p className="text-xs text-muted mb-1">전공</p>
            <p className="text-2xl font-bold text-blue-600">{summary?.major_credits || 0}</p>
          </div>
          <div className="p-4 bg-green-50 rounded-xl text-center">
            <p className="text-xs text-muted mb-1">교양</p>
            <p className="text-2xl font-bold text-green-600">{summary?.liberal_credits || 0}</p>
          </div>
          <div className="p-4 bg-orange-50 rounded-xl text-center">
            <p className="text-xs text-muted mb-1">자유선택</p>
            <p className="text-2xl font-bold text-orange-600">{summary?.elective_credits || 0}</p>
          </div>
        </div>

        {/* Course List by Category */}
        <div className="max-h-96 overflow-y-auto space-y-4">
          {/* 전공 Courses */}
          {majorCourses.length > 0 && (
            <div>
              <h4 className="font-semibold text-blue-600 mb-2 flex items-center gap-2">
                📚 전공 ({summary?.major_credits || 0}학점)
              </h4>
              <div className="space-y-2">
                {majorCourses.map((course, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div>
                      <p className="font-medium text-text">{course.course_name}</p>
                      <p className="text-xs text-muted">{course.semester} · {course.course_code}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted">{course.credits}학점</span>
                      <span className={clsx(
                        'badge',
                        course.grade?.startsWith('A') && 'badge-primary',
                        course.grade?.startsWith('B') && 'badge-secondary',
                        course.grade?.startsWith('C') && 'badge-warning'
                      )}>
                        {course.grade || '-'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 교양 Courses */}
          {liberalCourses.length > 0 && (
            <div>
              <h4 className="font-semibold text-green-600 mb-2 flex items-center gap-2">
                🎨 교양 ({summary?.liberal_credits || 0}학점)
              </h4>
              <div className="space-y-2">
                {liberalCourses.map((course, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div>
                      <p className="font-medium text-text">{course.course_name}</p>
                      <p className="text-xs text-muted">{course.semester} · {course.course_code}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted">{course.credits}학점</span>
                      <span className={clsx(
                        'badge',
                        course.grade?.startsWith('A') && 'badge-primary',
                        course.grade?.startsWith('B') && 'badge-secondary',
                        course.grade?.startsWith('C') && 'badge-warning'
                      )}>
                        {course.grade || '-'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 기타 Courses */}
          {electiveCourses.length > 0 && (
            <div>
              <h4 className="font-semibold text-orange-600 mb-2 flex items-center gap-2">
                📝 자유선택 ({summary?.elective_credits || 0}학점)
              </h4>
              <div className="space-y-2">
                {electiveCourses.map((course, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                    <div>
                      <p className="font-medium text-text">{course.course_name}</p>
                      <p className="text-xs text-muted">{course.semester} · {course.course_code}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted">{course.credits}학점</span>
                      <span className={clsx(
                        'badge',
                        course.grade?.startsWith('A') && 'badge-primary',
                        course.grade?.startsWith('B') && 'badge-secondary',
                        course.grade?.startsWith('C') && 'badge-warning'
                      )}>
                        {course.grade || '-'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {courses.length === 0 && (
            <div className="text-center py-8 text-muted">
              <p>이수한 교과목이 없습니다.</p>
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 px-4 bg-gray-100 text-text rounded-lg hover:bg-gray-200 transition-colors"
        >
          닫기
        </button>
      </div>
    </Modal>
  );
}

// Competency Detail Modal (for HeatStrip click)
interface CompetencyDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  competency: {
    name: string;
    monthlyScores: number[];
    color: string;
  } | null;
  selectedMonth?: number;
}

export function CompetencyDetailModal({ isOpen, onClose, competency, selectedMonth }: CompetencyDetailModalProps) {
  if (!competency) return null;

  const months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
  const currentScore = selectedMonth !== undefined ? competency.monthlyScores[selectedMonth] : competency.monthlyScores[competency.monthlyScores.length - 1];
  const avgScore = Math.round(competency.monthlyScores.reduce((a, b) => a + b, 0) / competency.monthlyScores.length);
  const trend = competency.monthlyScores[competency.monthlyScores.length - 1] - competency.monthlyScores[0];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`${competency.name} 역량 상세`} size="md">
      <div className="space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div className="p-4 bg-gray-50 rounded-xl text-center">
            <p className="text-xs text-muted mb-1">현재 점수</p>
            <p className="text-2xl font-bold" style={{ color: competency.color }}>{currentScore}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl text-center">
            <p className="text-xs text-muted mb-1">평균 점수</p>
            <p className="text-2xl font-bold text-text">{avgScore}</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-xl text-center">
            <p className="text-xs text-muted mb-1">성장률</p>
            <p className={clsx('text-2xl font-bold', trend >= 0 ? 'text-green-600' : 'text-red-600')}>
              {trend >= 0 ? '+' : ''}{trend}
            </p>
          </div>
        </div>

        {selectedMonth !== undefined && (
          <div className="p-4 bg-primary/5 rounded-xl">
            <p className="text-sm">
              📅 <strong>{months[selectedMonth]}</strong> 점수: <strong>{currentScore}점</strong>
            </p>
          </div>
        )}

        <div className="p-4 bg-gray-50 rounded-xl">
          <p className="text-xs text-muted mb-3">월별 추이</p>
          <div className="flex items-end gap-1 h-24">
            {competency.monthlyScores.map((score, index) => (
              <div
                key={index}
                className={clsx(
                  'flex-1 rounded-t transition-all',
                  selectedMonth === index && 'ring-2 ring-primary'
                )}
                style={{
                  height: `${score}%`,
                  backgroundColor: competency.color,
                  opacity: selectedMonth === index ? 1 : 0.6,
                }}
                title={`${months[index]}: ${score}점`}
              />
            ))}
          </div>
          <div className="flex text-xs text-muted mt-1">
            {months.map((m, i) => (
              <div key={i} className="flex-1 text-center">{m.replace('월', '')}</div>
            ))}
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 px-4 bg-gray-100 text-text rounded-lg hover:bg-gray-200 transition-colors"
        >
          닫기
        </button>
      </div>
    </Modal>
  );
}
