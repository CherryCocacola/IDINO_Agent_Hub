'use client';

import { useState, useEffect, useCallback } from 'react';
import { studentService } from '@/lib/api/student';
import { competencyService } from '@/lib/api/competency';
import { alumniService } from '@/lib/api/alumni';
import { integrationService } from '@/lib/api/integration';
import type {
  StudentDetail,
  EnrollmentWithGrade,
  Participation,
  Achievement,
  CompetencyReport,
  StudentComparison,
  SuccessPattern,
  WorknetJob,
  CourseRecord,
  Activity,
  ActivityResponse,
} from '@/types';

interface DashboardState {
  student: StudentDetail | null;
  enrollments: EnrollmentWithGrade[];
  activityResponses: ActivityResponse[];  // From backend tb_activity
  participations: Participation[];  // Legacy format
  achievements: Achievement[];
  // Legacy formats for backward compatibility
  courses: CourseRecord[];
  activities: Activity[];
  // Additional data
  competencyReport: CompetencyReport | null;
  alumniComparison: StudentComparison | null;
  successPatterns: SuccessPattern[];
  worknetJobs: WorknetJob[];
  loading: boolean;
  error: string | null;
  dataSource: 'database' | 'mock';
}

const initialState: DashboardState = {
  student: null,
  enrollments: [],
  activityResponses: [],
  participations: [],
  achievements: [],
  courses: [],
  activities: [],
  competencyReport: null,
  alumniComparison: null,
  successPatterns: [],
  worknetJobs: [],
  loading: true,
  error: null,
  dataSource: 'mock',
};

// Mock data for when API is not available
// Uses both backend field names (department_cd, current_grade) and frontend aliases for compatibility
const mockStudent: StudentDetail = {
  student_id: 'STU001',
  student_nm: '김민준',
  student_nm_en: 'Kim Minjun',
  // Backend field names
  department_cd: 'CS001',
  current_grade: 3,
  current_semester: 1,
  // Frontend aliases (for backward compatibility)
  department_id: 'CS001',
  grade: 3,
  semester: 1,
  total_credits: 95,
  gpa: 3.8,
  career_goal: '백엔드 개발자',
  target_job_codes: ['JOB001', 'JOB002'],
  status_cd: 'ENROLLED',
  status: 'enrolled',
  email: 'minjun@university.ac.kr',
  admission_year: 2022,
  expected_graduation: '2026-02',
  department: {
    department_cd: 'CS001',
    department_id: 'CS001',
    department_nm: '컴퓨터공학과',
    department_nm_en: 'Computer Science',
  },
  enrollment_count: 12,
  activity_count: 3,
  achievement_count: 2,
  summary: {
    completed_credits: 95,
    remaining_credits: 45,
    major_credits: 60,
    liberal_credits: 25,
    elective_credits: 10,
    graduation_readiness_pct: 67.8,
  },
};

const mockEnrollments: EnrollmentWithGrade[] = [
  { enrollment_id: '1', course_nm: '프로그래밍 기초', course_cd: 'CS101', credits: 3, academic_year: 2023, semester: 1, letter_grade: 'A+', grade_point: 4.5, status_cd: 'COMPLETED' },
  { enrollment_id: '2', course_nm: '자료구조', course_cd: 'CS201', credits: 3, academic_year: 2023, semester: 2, letter_grade: 'A', grade_point: 4.0, status_cd: 'COMPLETED' },
  { enrollment_id: '3', course_nm: '알고리즘', course_cd: 'CS301', credits: 3, academic_year: 2024, semester: 1, letter_grade: 'A+', grade_point: 4.5, status_cd: 'COMPLETED' },
  { enrollment_id: '4', course_nm: '데이터베이스', course_cd: 'CS401', credits: 3, academic_year: 2024, semester: 1, letter_grade: 'A', grade_point: 4.0, status_cd: 'COMPLETED' },
];

const mockParticipations: Participation[] = [
  { participation_id: '1', student_id: 'STU001', program_id: 'PRG001', program: { program_id: 'PRG001', program_nm: '프로그래밍 동아리', program_type: 'club' }, hours_completed: 100 },
  { participation_id: '2', student_id: 'STU001', program_id: 'PRG002', program: { program_id: 'PRG002', program_nm: '교내 해커톤', program_type: 'competition' }, hours_completed: 24 },
  { participation_id: '3', student_id: 'STU001', program_id: 'PRG003', program: { program_id: 'PRG003', program_nm: '멘토링 프로그램', program_type: 'mentoring' }, hours_completed: 30 },
];

const mockAchievements: Achievement[] = [
  { achievement_id: '1', student_id: 'STU001', achievement_type: 'certification', achievement_nm: '정보처리기사', issuing_org: '한국산업인력공단', issue_date: '2024-08-15', verified_fg: 'Y' },
  { achievement_id: '2', student_id: 'STU001', achievement_type: 'certification', achievement_nm: 'SQLD', issuing_org: '한국데이터산업진흥원', issue_date: '2024-05-20', verified_fg: 'Y' },
];

// Category-based mock jobs for different department types
const mockJobsByCategory: Record<string, WorknetJob[]> = {
  IT: [
    { job_code: 'JOB001', job_name: '백엔드 개발자', job_category: 'IT', required_skills: ['Java', 'Spring', 'SQL'], required_certifications: ['정보처리기사'], employment_trend: 'growing', related_majors: ['컴퓨터공학'] },
    { job_code: 'JOB002', job_name: '프론트엔드 개발자', job_category: 'IT', required_skills: ['JavaScript', 'React', 'CSS'], required_certifications: [], employment_trend: 'growing', related_majors: ['컴퓨터공학'] },
    { job_code: 'JOB003', job_name: '데이터 분석가', job_category: 'IT', required_skills: ['Python', 'SQL', '통계'], required_certifications: ['빅데이터 분석기사'], employment_trend: 'growing', related_majors: ['컴퓨터공학', '통계학'] },
  ],
  MEDICAL: [
    { job_code: 'JOB101', job_name: '의사', job_category: '의료', required_skills: ['진료', '진단', '처방'], required_certifications: ['의사면허'], employment_trend: 'stable', related_majors: ['의예과', '의학'] },
    { job_code: 'JOB102', job_name: '간호사', job_category: '의료', required_skills: ['환자간호', '의료기록', '응급처치'], required_certifications: ['간호사면허'], employment_trend: 'growing', related_majors: ['간호학'] },
    { job_code: 'JOB103', job_name: '물리치료사', job_category: '의료', required_skills: ['재활치료', '운동치료', '물리치료'], required_certifications: ['물리치료사면허'], employment_trend: 'growing', related_majors: ['물리치료학'] },
  ],
  HEALTH: [
    { job_code: 'JOB104', job_name: '임상병리사', job_category: '보건', required_skills: ['검체분석', '진단검사', '품질관리'], required_certifications: ['임상병리사면허'], employment_trend: 'stable', related_majors: ['임상병리학', '보건학'] },
    { job_code: 'JOB105', job_name: '치과위생사', job_category: '보건', required_skills: ['구강관리', '스케일링', '예방치료'], required_certifications: ['치과위생사면허'], employment_trend: 'growing', related_majors: ['치위생학'] },
    { job_code: 'JOB106', job_name: '보건행정사', job_category: '보건', required_skills: ['보건정책', '의료행정', '건강관리'], required_certifications: ['보건교육사'], employment_trend: 'stable', related_majors: ['보건행정학'] },
  ],
  EDUCATION: [
    { job_code: 'JOB201', job_name: '초등교사', job_category: '교육', required_skills: ['교육과정설계', '학생지도', '학급운영'], required_certifications: ['초등교사자격증'], employment_trend: 'stable', related_majors: ['초등교육'] },
    { job_code: 'JOB202', job_name: '중등교사', job_category: '교육', required_skills: ['교과지도', '생활지도', '교육평가'], required_certifications: ['중등교사자격증'], employment_trend: 'stable', related_majors: ['사범대학'] },
    { job_code: 'JOB203', job_name: '교육행정가', job_category: '교육', required_skills: ['교육정책', '행정관리', '예산운영'], required_certifications: ['교육행정직공무원'], employment_trend: 'stable', related_majors: ['교육학'] },
  ],
  ARTS: [
    { job_code: 'JOB301', job_name: '그래픽디자이너', job_category: '예술/디자인', required_skills: ['Photoshop', 'Illustrator', '시각디자인'], required_certifications: ['컴퓨터그래픽스운용기능사'], employment_trend: 'growing', related_majors: ['시각디자인', '미술학'] },
    { job_code: 'JOB302', job_name: '영상편집자', job_category: '예술/디자인', required_skills: ['Premiere', 'After Effects', '영상제작'], required_certifications: ['멀티미디어콘텐츠제작전문가'], employment_trend: 'growing', related_majors: ['영상학', '방송영상'] },
    { job_code: 'JOB303', job_name: '실내디자이너', job_category: '예술/디자인', required_skills: ['CAD', '3D 모델링', '공간설계'], required_certifications: ['실내건축기사'], employment_trend: 'stable', related_majors: ['실내디자인', '건축학'] },
  ],
  BUSINESS: [
    { job_code: 'JOB401', job_name: '회계사', job_category: '경영', required_skills: ['재무분석', '감사', '세무'], required_certifications: ['공인회계사'], employment_trend: 'stable', related_majors: ['회계학', '경영학'] },
    { job_code: 'JOB402', job_name: '금융분석가', job_category: '경영', required_skills: ['투자분석', '리스크관리', '포트폴리오'], required_certifications: ['CFA', '투자자산운용사'], employment_trend: 'growing', related_majors: ['경제학', '금융학'] },
    { job_code: 'JOB403', job_name: '인사관리자', job_category: '경영', required_skills: ['채용', '인사평가', '조직관리'], required_certifications: ['경영지도사'], employment_trend: 'stable', related_majors: ['경영학', '인적자원관리'] },
  ],
  SOCIAL: [
    { job_code: 'JOB404', job_name: '사회복지사', job_category: '사회복지', required_skills: ['사례관리', '상담', '프로그램기획'], required_certifications: ['사회복지사1급'], employment_trend: 'growing', related_majors: ['사회복지학'] },
    { job_code: 'JOB405', job_name: '심리상담사', job_category: '사회복지', required_skills: ['심리상담', '심리평가', '치료계획'], required_certifications: ['상담심리사', '임상심리사'], employment_trend: 'growing', related_majors: ['심리학', '상담학'] },
    { job_code: 'JOB406', job_name: '공무원', job_category: '공공행정', required_skills: ['행정업무', '정책분석', '민원처리'], required_certifications: ['공무원시험'], employment_trend: 'stable', related_majors: ['행정학', '정치외교학'] },
  ],
  SCIENCE: [
    { job_code: 'JOB501', job_name: '연구원', job_category: '과학', required_skills: ['실험설계', '데이터분석', '논문작성'], required_certifications: ['박사학위'], employment_trend: 'stable', related_majors: ['자연과학', '공학'] },
    { job_code: 'JOB502', job_name: '바이오엔지니어', job_category: '과학', required_skills: ['생명공학', '유전자분석', '세포배양'], required_certifications: ['생물공학기사'], employment_trend: 'growing', related_majors: ['생명공학', '생물학'] },
    { job_code: 'JOB503', job_name: '환경전문가', job_category: '과학', required_skills: ['환경영향평가', '오염분석', '환경관리'], required_certifications: ['환경기사'], employment_trend: 'growing', related_majors: ['환경공학', '환경학'] },
  ],
  ENGINEERING: [
    { job_code: 'JOB601', job_name: '기계공학자', job_category: '공학', required_skills: ['CAD/CAM', '기계설계', '열역학'], required_certifications: ['기계기사'], employment_trend: 'stable', related_majors: ['기계공학'] },
    { job_code: 'JOB602', job_name: '전기공학자', job_category: '공학', required_skills: ['회로설계', '전력시스템', '제어공학'], required_certifications: ['전기기사'], employment_trend: 'stable', related_majors: ['전기공학'] },
    { job_code: 'JOB603', job_name: '토목기술자', job_category: '공학', required_skills: ['구조해석', '토목설계', '시공관리'], required_certifications: ['토목기사'], employment_trend: 'stable', related_majors: ['토목공학', '건축공학'] },
  ],
  HUMANITIES: [
    { job_code: 'JOB701', job_name: '기자/언론인', job_category: '인문', required_skills: ['취재', '기사작성', '편집'], required_certifications: ['언론홍보인증'], employment_trend: 'stable', related_majors: ['신문방송학', '국어국문학'] },
    { job_code: 'JOB702', job_name: '번역가', job_category: '인문', required_skills: ['번역', '통역', '외국어'], required_certifications: ['번역능력인정시험'], employment_trend: 'stable', related_majors: ['영어영문학', '외국어'] },
    { job_code: 'JOB703', job_name: '학예연구사', job_category: '인문', required_skills: ['전시기획', '유물관리', '연구조사'], required_certifications: ['학예사자격증'], employment_trend: 'stable', related_majors: ['역사학', '고고학', '미술사학'] },
  ],
  GENERAL: [
    { job_code: 'JOB901', job_name: '공무원', job_category: '공공행정', required_skills: ['행정업무', '정책분석', '민원처리'], required_certifications: ['공무원시험'], employment_trend: 'stable', related_majors: ['행정학', '일반'] },
    { job_code: 'JOB902', job_name: '사무행정원', job_category: '사무', required_skills: ['문서작성', '데이터관리', '커뮤니케이션'], required_certifications: ['컴퓨터활용능력'], employment_trend: 'stable', related_majors: ['일반'] },
    { job_code: 'JOB903', job_name: '영업관리자', job_category: '영업', required_skills: ['고객관리', '협상', '시장분석'], required_certifications: ['유통관리사'], employment_trend: 'stable', related_majors: ['경영학', '일반'] },
  ],
};

// Map department codes/names to categories
function getDepartmentCategory(departmentCd: string | undefined, departmentNm?: string | undefined): string {
  // Check both department code and name for better matching
  const checkStrings = [
    departmentCd?.toUpperCase() || '',
    departmentNm || '',
  ].filter(Boolean);

  if (checkStrings.length === 0) return 'GENERAL'; // Default fallback

  // Helper to check if any keyword matches any of the check strings
  const matchesAny = (keywords: string[]) =>
    keywords.some(keyword =>
      checkStrings.some(str => str.toUpperCase().includes(keyword.toUpperCase()))
    );

  // Medical departments (check first - higher priority)
  if (matchesAny(['MED', 'MEDI', '의예', '의학', 'MD', '의과'])) {
    return 'MEDICAL';
  }
  // Health departments
  if (matchesAny(['HEALTH', 'NURS', '보건', '간호', '치위생', '임상', '약학', '제약', '물리치료', '헬스케어'])) {
    return 'HEALTH';
  }
  // IT/Computer Science departments
  if (matchesAny(['CS001', 'CS', 'SE', 'IT', 'CSE', 'SWE', '컴퓨터', '소프트웨어', '정보'])) {
    return 'IT';
  }
  // Education departments
  if (matchesAny(['EDU', 'TEACH', '교육', '사범'])) {
    return 'EDUCATION';
  }
  // Arts/Design departments
  if (matchesAny(['ART', 'DESIGN', 'MUSIC', 'FILM', '예술', '디자인', '미술', '음악', '영상'])) {
    return 'ARTS';
  }
  // Business/Economics departments
  if (matchesAny(['BUS', 'ECON', 'MGMT', 'ACC', 'FIN', '경영', '경제', '회계', '금융'])) {
    return 'BUSINESS';
  }
  // Social Science departments
  if (matchesAny(['SOC', 'PSY', 'POL', 'ADM', '사회', '심리', '정치', '행정', '복지'])) {
    return 'SOCIAL';
  }
  // Natural Science departments
  if (matchesAny(['SCI', 'BIO', 'CHEM', 'PHYS', 'ENV', '자연', '생명', '화학', '물리', '환경'])) {
    return 'SCIENCE';
  }
  // Engineering departments (non-IT)
  if (matchesAny(['ENG', 'MECH', 'ELEC', 'CIVIL', '공학', '기계', '전기', '전자', '토목', '건축'])) {
    return 'ENGINEERING';
  }
  // Humanities departments
  if (matchesAny(['HUM', 'LIT', 'LANG', 'HIST', 'PHIL', '인문', '문학', '어문', '역사', '철학'])) {
    return 'HUMANITIES';
  }
  return 'GENERAL'; // Default fallback
}

// Get mock jobs based on student's department
function getMockJobsForDepartment(departmentCd: string | undefined, departmentNm?: string | undefined): WorknetJob[] {
  const category = getDepartmentCategory(departmentCd, departmentNm);
  return mockJobsByCategory[category] || mockJobsByCategory.IT;
}

// Default mock jobs (for backward compatibility)
const mockJobs: WorknetJob[] = mockJobsByCategory.IT;

// Category-based mock success patterns for different department types
// Field names match SuccessPattern interface: pattern_id, department_id, job_category, pattern_description, required_activities, success_rate, sample_size
const mockPatternsByCategory: Record<string, SuccessPattern[]> = {
  IT: [
    { pattern_id: 'P001', department_id: 'CS', job_category: '응용소프트웨어개발자', pattern_description: '프로젝트 경험 3회 이상 + 인턴십 1회 + 정보처리기사', required_activities: ['캡스톤 프로젝트', '교내/외 해커톤', '개발 인턴십', '정보처리기사 취득'], success_rate: 85, sample_size: 120 },
    { pattern_id: 'P002', department_id: 'CS', job_category: '데이터분석가', pattern_description: '데이터 관련 자격증 2개 + 분석 프로젝트 경험', required_activities: ['빅데이터분석기사', 'ADsP 자격증', '데이터 분석 프로젝트', '통계 관련 수업'], success_rate: 78, sample_size: 85 },
  ],
  MEDICAL: [
    { pattern_id: 'P101', department_id: 'MED', job_category: '전문의', pattern_description: '의사국가고시 합격 + 전공의 수련 4년', required_activities: ['의사국가고시 합격', '인턴 1년', '레지던트 수련', '전문의 자격 취득'], success_rate: 92, sample_size: 200 },
    { pattern_id: 'P102', department_id: 'MED', job_category: '의학연구원', pattern_description: '기초의학 석박사 + 연구 프로젝트 참여', required_activities: ['대학원 진학', '연구실 인턴', '학술논문 발표', 'SCI 논문 게재'], success_rate: 75, sample_size: 65 },
  ],
  HEALTH: [
    { pattern_id: 'P201', department_id: 'HEALTH', job_category: '간호사', pattern_description: '간호사 면허 취득 + 병원 임상실습 우수', required_activities: ['간호사국가고시 합격', '임상실습 이수', '병원 인턴십', 'BLS 자격'], success_rate: 88, sample_size: 150 },
    { pattern_id: 'P202', department_id: 'HEALTH', job_category: '물리치료사', pattern_description: '물리치료사 면허 + 재활병원 실습 경험', required_activities: ['물리치료사국가고시', '재활병원 실습', '도수치료 교육', '스포츠재활 자격'], success_rate: 82, sample_size: 95 },
  ],
  EDUCATION: [
    { pattern_id: 'P301', department_id: 'EDU', job_category: '초등교사', pattern_description: '교원임용시험 합격 + 교육실습 우수', required_activities: ['교원임용시험 합격', '교육실습', '교육봉사', '학습지도안 작성'], success_rate: 80, sample_size: 180 },
    { pattern_id: 'P302', department_id: 'EDU', job_category: '중등교사', pattern_description: '교원임용시험 합격 + 전공 심화', required_activities: ['교원임용시험 합격', '전공 교육실습', '교과 연구', '동아리 지도 경험'], success_rate: 75, sample_size: 150 },
  ],
  BUSINESS: [
    { pattern_id: 'P401', department_id: 'BUS', job_category: '공인회계사', pattern_description: 'CPA 시험 합격 + 실무수습 완료', required_activities: ['CPA 1차/2차 합격', '회계법인 실무수습', '재무제표 분석 실습', '세무 실무'], success_rate: 70, sample_size: 95 },
    { pattern_id: 'P402', department_id: 'BUS', job_category: '금융분석가', pattern_description: 'CFA/투자자산운용사 + 금융권 인턴', required_activities: ['CFA Level 1', '투자자산운용사', '증권사 인턴', '포트폴리오 분석'], success_rate: 76, sample_size: 85 },
  ],
  ARTS: [
    { pattern_id: 'P501', department_id: 'ART', job_category: '그래픽디자이너', pattern_description: '디자인 포트폴리오 + GTQ 자격증', required_activities: ['GTQ 1급', '포트폴리오 제작', '디자인 공모전', '에이전시 인턴'], success_rate: 72, sample_size: 110 },
    { pattern_id: 'P502', department_id: 'ART', job_category: '영상편집자', pattern_description: '영상제작 경험 + 멀티미디어 자격', required_activities: ['멀티미디어콘텐츠제작전문가', '영상 프로젝트', '유튜브 채널 운영', '편집 포트폴리오'], success_rate: 68, sample_size: 80 },
  ],
  SOCIAL: [
    { pattern_id: 'P601', department_id: 'SOC', job_category: '사회복지사', pattern_description: '사회복지사 1급 + 현장실습 우수', required_activities: ['사회복지사 1급', '기관 현장실습', '사례관리 경험', '자원봉사 활동'], success_rate: 85, sample_size: 130 },
    { pattern_id: 'P602', department_id: 'SOC', job_category: '상담심리사', pattern_description: '상담심리사 자격 + 상담 실습 이수', required_activities: ['상담심리사 2급', '상담실습 200시간', '심리검사 교육', '사례 수퍼비전'], success_rate: 74, sample_size: 75 },
  ],
  SCIENCE: [
    { pattern_id: 'P701', department_id: 'SCI', job_category: '연구원', pattern_description: '석박사 학위 + 연구 논문 실적', required_activities: ['대학원 진학', '연구 프로젝트', '학회 발표', '논문 게재'], success_rate: 82, sample_size: 90 },
    { pattern_id: 'P702', department_id: 'SCI', job_category: '바이오연구원', pattern_description: '생명공학 전공 + 실험실 경험', required_activities: ['생물공학기사', '연구실 인턴', '실험 프로젝트', '특허 출원'], success_rate: 78, sample_size: 60 },
  ],
  ENGINEERING: [
    { pattern_id: 'P801', department_id: 'ENG', job_category: '기계공학자', pattern_description: '기계기사 + 설계 프로젝트 경험', required_activities: ['일반기계기사', 'CAD/CAM 실습', '설계 프로젝트', '제조업 인턴'], success_rate: 85, sample_size: 170 },
    { pattern_id: 'P802', department_id: 'ENG', job_category: '전기전자공학자', pattern_description: '전기/전자기사 + 반도체 관련 경험', required_activities: ['전기기사/전자기사', '회로설계 프로젝트', '반도체 인턴', '임베디드 개발'], success_rate: 83, sample_size: 145 },
  ],
  HUMANITIES: [
    { pattern_id: 'P901', department_id: 'HUM', job_category: '기자/PD', pattern_description: '언론사 인턴 + 기사/영상 제작 경험', required_activities: ['언론사 인턴', '교내 언론사', '기사 작성', '영상 제작'], success_rate: 65, sample_size: 70 },
    { pattern_id: 'P902', department_id: 'HUM', job_category: '학예연구사', pattern_description: '석사 학위 + 박물관/미술관 실습', required_activities: ['대학원 진학', '학예실습', '전시 기획', '문화재 조사'], success_rate: 58, sample_size: 45 },
  ],
  GENERAL: [
    { pattern_id: 'PG01', department_id: 'GEN', job_category: '공무원/공공기관', pattern_description: '공무원시험 합격 + 행정 인턴 경험', required_activities: ['공무원 시험 준비', '행정 인턴', '자격증 취득', '봉사활동'], success_rate: 72, sample_size: 100 },
    { pattern_id: 'PG02', department_id: 'GEN', job_category: '사무/행정직', pattern_description: '컴퓨터활용능력 + 인턴십 경험', required_activities: ['컴퓨터활용능력 자격증', '기업 인턴십', '비교과활동', 'TOEIC 700+'], success_rate: 68, sample_size: 85 },
  ],
};

// Get mock success patterns based on student's department
function getMockPatternsForDepartment(departmentCd: string | undefined, departmentNm?: string | undefined): SuccessPattern[] {
  const category = getDepartmentCategory(departmentCd, departmentNm);
  return mockPatternsByCategory[category] || mockPatternsByCategory.IT;
}

// Map numeric/string course_type to Korean category for display
function mapCourseType(courseType?: string): string {
  if (!courseType) return '';
  const typeMap: Record<string, string> = {
    '1': '전공필수', '2': '전공선택', '3': '교양필수', '4': '교양선택', '5': '자유선택',
    '전공필수': '전공필수', '전공선택': '전공선택', '교양필수': '교양필수', '교양선택': '교양선택',
    'major_required': '전공필수', 'major_elective': '전공선택',
    'general_required': '교양필수', 'general_elective': '교양선택',
  };
  return typeMap[courseType] || courseType;
}

// Convert enrollment to legacy course format
function enrollmentToCourse(e: EnrollmentWithGrade, idx: number, studentId: string): CourseRecord {
  // Backend returns term_nm (e.g. "2024-1학기"), use it directly
  // Fall back to academic_year-semester if term_nm is not available
  const semesterStr = e.term_nm || (e.academic_year && e.semester ? `${e.academic_year}-${e.semester}` : '');
  return {
    id: idx + 1,
    student_id: studentId,
    course_code: e.course_cd,
    course_name: e.course_nm,
    semester: semesterStr,
    credits: e.credits,
    grade: e.letter_grade || '',
    grade_point: e.grade_point || 0,
    course_type: mapCourseType(e.course_type),
  };
}

// Convert participation to legacy activity format
function participationToActivity(p: Participation, idx: number): Activity {
  return {
    id: idx + 1,
    student_id: p.student_id,
    activity_name: p.program?.program_nm || '',
    activity_type: p.program?.program_type || '',
    status: 'completed',
    hours_completed: p.hours_completed,
  };
}

// Map numeric activity_type codes to string names
const activityTypeMap: Record<string, string> = {
  '1': 'internship', '2': 'volunteer', '3': 'competition',
  '4': 'club', '5': 'study', '6': 'project', '7': 'seminar',
};

// Map numeric status codes to string names
const activityStatusMap: Record<string, string> = {
  '1': 'planned', '2': 'in_progress', '3': 'completed',
};

// Convert ActivityResponse (from backend) to legacy Activity format
function activityResponseToActivity(a: ActivityResponse, idx: number): Activity {
  const rawType = String(a.activity_type || '');
  const rawStatus = String(a.status || 'completed');
  return {
    id: idx + 1,
    student_id: a.student_id,
    activity_name: a.title || '',
    activity_type: activityTypeMap[rawType] || rawType,
    status: activityStatusMap[rawStatus] || rawStatus,
    start_date: a.start_date,
    end_date: a.end_date,
    hours_completed: a.hours,
  };
}

export function useDashboard(studentId: string | null) {
  const [state, setState] = useState<DashboardState>(initialState);

  const fetchData = useCallback(async () => {
    // Don't fetch if no studentId (not authenticated)
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      let student: StudentDetail | null = null;
      let enrollments: EnrollmentWithGrade[] = [];
      let activityResponses: ActivityResponse[] = [];
      let participations: Participation[] = [];
      let achievements: Achievement[] = [];
      let competencyReport: CompetencyReport | null = null;
      let alumniComparison: StudentComparison | null = null;
      let successPatterns: SuccessPattern[] = [];
      let worknetJobs: WorknetJob[] = mockJobs;
      let dataSource: 'database' | 'mock' = 'mock';

      // Try to fetch from dashboard API first (most efficient - single call)
      try {
        const dashboard = await studentService.getDashboard(studentId);
        student = dashboard.student;
        enrollments = dashboard.enrollments;
        // Backend returns ActivityResponse[] in dashboard.activities
        activityResponses = dashboard.activities as ActivityResponse[];
        achievements = dashboard.achievements;
        dataSource = 'database';
        console.log('✅ Dashboard data loaded from database');
        console.log('📊 Activities count:', activityResponses.length);
        console.log('📊 Achievements count:', achievements.length);
        console.log('📊 Enrollments count:', enrollments.length);
      } catch (e) {
        console.warn('Dashboard API not available, falling back to individual calls:', e);

        // Fall back to individual API calls
        try {
          student = await studentService.getStudent(studentId);
          dataSource = 'database';
        } catch (e2) {
          console.warn('Using mock student data:', e2);
          student = mockStudent;
        }

        try {
          enrollments = await studentService.getEnrollments(studentId);
        } catch (e2) {
          console.warn('Using mock enrollments data:', e2);
          enrollments = mockEnrollments;
        }

        try {
          // getParticipations actually returns ActivityResponse[] from /students/{id}/activities
          const apiActivities = await studentService.getParticipations(studentId);
          activityResponses = apiActivities as unknown as ActivityResponse[];
        } catch (e2) {
          console.warn('Using mock participations data:', e2);
          participations = mockParticipations;
        }

        try {
          achievements = await studentService.getAchievements(studentId);
        } catch (e2) {
          console.warn('Using mock achievements data:', e2);
          achievements = mockAchievements;
        }
      }

      // Try competency service - no mock fallback, null means section hidden
      try {
        competencyReport = await competencyService.getReport(studentId);
      } catch (e) {
        console.warn('Competency API not available:', e);
        competencyReport = null;
      }

      // Try alumni service
      try {
        alumniComparison = await alumniService.compareWithAlumni(studentId);
      } catch (e) {
        console.warn('Alumni API not available:', e);
      }

      try {
        const deptCd = student?.department_cd || student?.department_id;
        if (deptCd) {
          successPatterns = await alumniService.getPatterns(deptCd);
        }
      } catch (e) {
        console.warn('Success patterns API not available, using mock data:', e);
        // Use department-specific mock success patterns as fallback
        successPatterns = getMockPatternsForDepartment(
          student?.department_cd || student?.department_id,
          student?.department?.department_nm
        );
      }

      // Try integration service (worknet jobs) - pass department for filtering
      try {
        const departmentNm = student?.department?.department_nm || '';
        worknetJobs = await integrationService.getJobs(departmentNm);
      } catch (e) {
        console.warn('Using mock jobs data:', e);
        // Use department-specific mock jobs based on student's department (code + name)
        worknetJobs = getMockJobsForDepartment(
          student?.department_cd || student?.department_id,
          student?.department?.department_nm
        );
      }

      // Convert to legacy formats
      const courses = enrollments.map((e, idx) => enrollmentToCourse(e, idx, studentId));
      // Use activityResponses if available (from database), otherwise fall back to participations (from mock)
      const activities = activityResponses.length > 0
        ? activityResponses.map((a, idx) => activityResponseToActivity(a, idx))
        : participations.map((p, idx) => participationToActivity(p, idx));

      // Sync alumni comparison student_data with dashboard values (single source of truth)
      if (alumniComparison) {
        const sd = student as StudentDetail | null;
        const syncCredits = sd?.completed_credits || enrollments.reduce((sum, e) => sum + e.credits, 0);
        const syncActivities = activities.filter(a => a.status === 'completed').length;
        const syncCerts = achievements.filter(a => a.achievement_type === 'certification' || a.achievement_type === 'certificate').length;
        const syncGpa = student?.gpa ?? alumniComparison.student_data?.gpa ?? 0;

        alumniComparison = {
          ...alumniComparison,
          student_data: {
            ...alumniComparison.student_data,
            gpa: syncGpa,
            credits: syncCredits,
            certifications: syncCerts,
            activities: syncActivities,
          },
          gap_analysis: {
            ...alumniComparison.gap_analysis,
            gpa_gap: syncGpa - (alumniComparison.alumni_average?.gpa ?? 0),
            credits_gap: syncCredits - (alumniComparison.alumni_average?.credits ?? 0),
          },
        };
      }

      setState({
        student,
        enrollments,
        activityResponses,
        participations,
        achievements,
        courses,
        activities,
        competencyReport,
        alumniComparison,
        successPatterns,
        worknetJobs,
        loading: false,
        error: null,
        dataSource,
      });
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      // Use all mock data on complete failure
      // Get department-specific mock jobs based on mockStudent's department (code + name)
      const fallbackJobs = getMockJobsForDepartment(
        mockStudent.department_cd,
        mockStudent.department?.department_nm
      );
      setState({
        student: mockStudent,
        enrollments: mockEnrollments,
        activityResponses: [],
        participations: mockParticipations,
        achievements: mockAchievements,
        courses: mockEnrollments.map((e, idx) => enrollmentToCourse(e, idx, 'STU001')),
        activities: mockParticipations.map((p, idx) => participationToActivity(p, idx)),
        competencyReport: null,
        alumniComparison: null,
        successPatterns: [],
        worknetJobs: fallbackJobs,
        loading: false,
        error: 'API 연결 실패 - Mock 데이터를 사용합니다.',
        dataSource: 'mock',
      });
    }
  }, [studentId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    ...state,
    refetch: fetchData,
    // Helper to check if using real data
    isUsingRealData: state.dataSource === 'database',
  };
}
