// Opportunity Types - matches opportunity-service (port 8008) schemas

export type OpportunityType =
  | 'internship'       // 인턴십
  | 'competition'      // 공모전
  | 'research'         // 연구참여
  | 'extracurricular'  // 대외활동
  | 'scholarship'      // 장학금
  | 'certification'    // 자격증
  | 'mentoring'        // 멘토링
  | 'project';         // 프로젝트

export type ApplicationStatus =
  | 'interested'  // 관심등록
  | 'preparing'   // 준비중
  | 'applied'     // 지원완료
  | 'reviewing'   // 심사중
  | 'accepted'    // 합격
  | 'rejected'    // 불합격
  | 'withdrawn';  // 철회

// Opportunity
export interface OpportunityBase {
  opportunity_type: OpportunityType;
  title: string;
  description?: string;
  organization?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  application_deadline?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  min_gpa?: number;
  eligible_majors?: string[];
  eligible_years?: number[];
  benefits?: string;
  url?: string;
  is_active: boolean;
}

export interface OpportunityCreate extends OpportunityBase {}

export interface OpportunityUpdate {
  opportunity_type?: OpportunityType;
  title?: string;
  description?: string;
  organization?: string;
  location?: string;
  start_date?: string;
  end_date?: string;
  application_deadline?: string;
  required_skills?: string[];
  preferred_skills?: string[];
  min_gpa?: number;
  eligible_majors?: string[];
  eligible_years?: number[];
  benefits?: string;
  url?: string;
  is_active?: boolean;
}

export interface OpportunityResponse extends OpportunityBase {
  opportunity_id: string;
  created_at: string;
  updated_at?: string;
}

export interface OpportunityListResponse {
  opportunities: OpportunityResponse[];
  total_count: number;
  page: number;
  page_size: number;
}

// Recommendation
export interface OpportunityMatchScore {
  opportunity_id: string;
  skill_match_score: number;     // 0-100
  eligibility_score: number;     // 0-100
  preference_score: number;      // 0-100
  overall_score: number;         // 0-100
  match_reasons: string[];
  gap_skills: string[];
}

export interface OpportunityRecommendationResponse {
  opportunity: OpportunityResponse;
  match_score: OpportunityMatchScore;
  recommended_actions: string[];
}

export interface RecommendationRequest {
  student_id: string;
  opportunity_types?: OpportunityType[];
  min_score?: number;    // default 50
  max_results?: number;  // default 10
  include_expired?: boolean;
}

export interface RecommendationResponse {
  student_id: string;
  recommendations: OpportunityRecommendationResponse[];
  generated_at: string;
  filters_applied: Record<string, unknown>;
}

// Application
export interface ApplicationCreate {
  student_id: string;
  opportunity_id: string;
  status?: ApplicationStatus;
  notes?: string;
}

export interface ApplicationUpdate {
  status?: ApplicationStatus;
  notes?: string;
  applied_at?: string;
  result_at?: string;
}

export interface ApplicationResponse {
  application_id: string;
  student_id: string;
  opportunity_id: string;
  opportunity_title?: string;
  opportunity_type?: OpportunityType;
  organization?: string;
  status: ApplicationStatus;
  notes?: string;
  applied_at?: string;
  result_at?: string;
  created_at: string;
  updated_at?: string;
}

// Search
export interface OpportunitySearchRequest {
  query?: string;
  opportunity_types?: OpportunityType[];
  skills?: string[];
  location?: string;
  min_deadline_days?: number;
  is_active?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: 'deadline' | 'created' | 'title';
  sort_order?: 'asc' | 'desc';
}

// Helper
export const OPPORTUNITY_TYPE_LABELS: Record<OpportunityType, string> = {
  internship: '인턴십',
  competition: '공모전',
  research: '연구참여',
  extracurricular: '대외활동',
  scholarship: '장학금',
  certification: '자격증',
  mentoring: '멘토링',
  project: '프로젝트',
};

export const OPPORTUNITY_TYPE_ICONS: Record<OpportunityType, string> = {
  internship: '💼',
  competition: '🏆',
  research: '🔬',
  extracurricular: '🎯',
  scholarship: '🎓',
  certification: '📜',
  mentoring: '👥',
  project: '💻',
};

export const APPLICATION_STATUS_LABELS: Record<ApplicationStatus, string> = {
  interested: '관심등록',
  preparing: '준비중',
  applied: '지원완료',
  reviewing: '심사중',
  accepted: '합격',
  rejected: '불합격',
  withdrawn: '철회',
};
