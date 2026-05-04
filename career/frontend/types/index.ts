// Student Types - matches backend schema
export interface Student {
  student_id: string;
  student_nm: string;  // 학생 이름
  student_nm_en?: string;
  // Backend uses department_cd, frontend alias as department_id for compatibility
  department_cd?: string;
  department_id?: string;  // Alias for department_cd
  // Backend uses current_grade, frontend alias as grade for compatibility
  current_grade?: number;
  grade?: number;  // Alias for current_grade
  current_semester?: number;
  semester?: number;  // Alias for current_semester
  total_credits?: number;
  gpa?: number;
  career_goal?: string;
  target_job_codes?: string[];
  status_cd?: string;
  status?: string;  // Alias for status_cd
  ins_dt?: string;
  upd_dt?: string;
}

export interface StudentDetail extends Student {
  university_cd?: string;
  email?: string;
  phone?: string;
  admission_year?: number;
  birth_date?: string;
  gender?: string;
  expected_graduation?: string;
  department?: DepartmentInfo;
  enrollment_count: number;
  activity_count: number;
  achievement_count: number;
  // Directly from backend (not nested in summary)
  completed_credits?: number;  // Sum of earned credits from tb_grade
  // gpa is already in Student base interface
  summary?: StudentSummary;
}

export interface StudentSummary {
  completed_credits: number;
  remaining_credits?: number;
  major_credits: number;
  liberal_credits: number;
  elective_credits: number;
  graduation_readiness_pct?: number;
}

export interface DepartmentInfo {
  // Backend uses department_cd, frontend alias as department_id for compatibility
  department_cd?: string;
  department_id?: string;  // Alias for department_cd
  department_nm: string;
  department_nm_en?: string;
  college?: CollegeInfo;
}

export interface CollegeInfo {
  // Backend uses college_cd, frontend alias as college_id for compatibility
  college_cd?: string;
  college_id?: string;  // Alias for college_cd
  college_nm: string;
  college_nm_en?: string;
}

// Enrollment/Course Types (matches backend EnrollmentWithGradeResponse)
export interface EnrollmentWithGrade {
  enrollment_id: string;
  course_nm: string;
  course_cd: string;
  credits: number;
  course_type?: string;  // e.g. '1'=전공필수, '2'=전공선택, '3'=교양필수, '4'=교양선택
  term_nm?: string;  // Backend returns term_nm (e.g. "2024-1학기")
  // Legacy fields for backward compatibility
  academic_year?: number;
  semester?: number;
  letter_grade?: string;
  grade_point?: number;
  status_cd: string;
}

// Legacy alias for backward compatibility
export interface CourseRecord {
  id: number;
  student_id: string;
  course_code: string;
  course_name: string;
  semester: string;
  credits: number;
  grade: string;
  grade_point: number;
  course_type: string;
  competency_mappings?: Record<string, number>;
}

// Program/Activity Types
export interface ProgramInfo {
  program_id: string;
  program_nm: string;
  program_nm_en?: string;
  program_type?: string;
  host_organization?: string;
  description?: string;
}

// Backend ActivityResponse type (from tb_activity table)
export interface ActivityResponse {
  activity_id: string;
  student_id: string;
  program_cd?: string;
  activity_type: string;
  title?: string;
  description?: string;
  start_date?: string;
  end_date?: string;
  hours?: number;
  achievement?: string;
  status: string;
  verified: string;
  ins_dt?: string;
}

// Legacy Participation type (for backward compatibility)
export interface Participation {
  participation_id: string;
  student_id: string;
  program_id: string;
  program?: ProgramInfo;
  participation_date?: string;
  hours_completed: number;
  score?: number;
  certificate_url?: string;
  feedback?: string;
  ins_dt?: string;
}

// Legacy alias
export interface Activity {
  id: number;
  student_id: string;
  activity_name: string;
  activity_type: string;
  status: string;
  start_date?: string;
  end_date?: string;
  hours_completed?: number;
  competency_gains?: Record<string, number>;
}

// Achievement Types
export interface Achievement {
  achievement_id: string;
  student_id: string;
  achievement_type: string;
  achievement_nm: string;
  issuing_org?: string;
  issue_date?: string;
  expiry_date?: string;
  level?: string;
  score?: string;
  certificate_url?: string;
  verified_fg: string;
  ins_dt?: string;
}

// Dashboard Summary (matches backend DashboardSummary response)
export interface DashboardSummary {
  student: StudentDetail;
  enrollments: EnrollmentWithGrade[];
  activities: ActivityResponse[];  // Backend returns ActivityResponse, not Participation
  achievements: Achievement[];
}

// Competency Types
export interface CompetencyDefinition {
  competency_id: string;
  competency_nm: string;
  competency_nm_en?: string;
  department_id?: string;
  competency_type?: string;
  weight?: number;
  description?: string;
}

export interface CompetencyScore {
  competency_id: string;
  competency_nm: string;
  score: number;
  max_score: number;
  percentile?: number;
  status: 'excellent' | 'good' | 'average' | 'needs_improvement';
  color: string;
}

export interface CompetencyReport {
  student_id: string;
  assessment_date: string;
  total_score: number;
  percentile_rank: number;
  scores: CompetencyScore[];
  course_contribution: Record<string, number>;
  activity_contribution: Record<string, number>;
  recommendations?: string[];
}

// Alumni Types
export interface AlumniStatistics {
  department_id: string;
  graduation_year?: number;
  job_category: string;
  avg_gpa: number;
  avg_credits: number;
  common_certifications: string[];
  common_activities: string[];
  competency_profile: Record<string, number>;
  employment_rate: number;
  avg_salary?: number;
  sample_size: number;
}

export interface SuccessPattern {
  pattern_id: string;
  department_id: string;
  job_category: string;
  pattern_description: string;
  required_activities: string[];
  success_rate: number;
  sample_size: number;
}

export interface StudentComparison {
  student_id: string;
  student_data: {
    gpa: number;
    credits: number;
    certifications: number;
    activities: number;
    competency_scores: Record<string, number>;
  };
  alumni_average: {
    gpa: number;
    credits: number;
    certifications: number;
    activities: number;
    competency_scores: Record<string, number>;
  };
  gap_analysis: {
    gpa_gap: number;
    credits_gap: number;
    competency_gaps: Record<string, number>;
  };
  recommendations: string[];
}

// Integration Types
export interface WorknetJob {
  job_code: string;
  job_name: string;
  job_category: string;
  description?: string;
  required_skills: string[];
  required_certifications: string[];
  average_salary?: number;
  employment_trend: string;
  related_majors: string[];
}

// Dashboard Data Type (legacy)
export interface DashboardData {
  student: Student;
  courses: CourseRecord[];
  activities: Activity[];
  achievements: Achievement[];
  competencyReport: CompetencyReport;
  alumniComparison: StudentComparison;
  worknetJobs: WorknetJob[];
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// Re-export P1/P2 feature types
export * from './skill';
export * from './coaching';
export * from './risk';
export * from './opportunity';
export * from './sprint';
export * from './simulation';
export * from './badge';
export * from './advisor';
export * from './portfolio';
export * from './roadmap';

// Utility function to convert backend response to frontend format
export function convertEnrollmentToCourse(enrollment: EnrollmentWithGrade): CourseRecord {
  const semesterStr = enrollment.term_nm || (enrollment.academic_year && enrollment.semester ? `${enrollment.academic_year}-${enrollment.semester}` : '');
  return {
    id: 0, // Not used in new schema
    student_id: '',
    course_code: enrollment.course_cd,
    course_name: enrollment.course_nm,
    semester: semesterStr,
    credits: enrollment.credits,
    grade: enrollment.letter_grade || '',
    grade_point: enrollment.grade_point || 0,
    course_type: '',
  };
}

export function convertParticipationToActivity(participation: Participation): Activity {
  return {
    id: 0,
    student_id: participation.student_id,
    activity_name: participation.program?.program_nm || '',
    activity_type: participation.program?.program_type || '',
    status: 'completed',
    hours_completed: participation.hours_completed,
  };
}

// Convert backend ActivityResponse to frontend Activity format
export function convertActivityResponseToActivity(activityResp: ActivityResponse, idx: number): Activity {
  return {
    id: idx + 1,
    student_id: activityResp.student_id,
    activity_name: activityResp.title || '',
    activity_type: activityResp.activity_type || '',
    status: activityResp.status || 'completed',
    start_date: activityResp.start_date,
    end_date: activityResp.end_date,
    hours_completed: activityResp.hours,
  };
}
