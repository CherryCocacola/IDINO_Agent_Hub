// Risk Types - matches risk-service (port 8010) schemas

export type RiskSeverity = 'low' | 'medium' | 'high' | 'critical';
export type RiskCategory = 'gpa' | 'credits' | 'attendance' | 'prerequisite' | 'graduation' | 'career' | 'skill_gap';
export type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed';

// Risk Alert
export interface RiskAlertBase {
  category: RiskCategory;
  severity: RiskSeverity;
  title: string;
  description: string;
  recommendation?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  due_date?: string;
}

export interface RiskAlertCreate extends RiskAlertBase {
  student_id: string;
}

export interface RiskAlertUpdate {
  status?: AlertStatus;
  acknowledged_at?: string;
  resolved_at?: string;
  resolution_note?: string;
}

export interface RiskAlertResponse extends RiskAlertBase {
  alert_id: string;
  student_id: string;
  status: AlertStatus;
  acknowledged_at?: string;
  resolved_at?: string;
  resolution_note?: string;
  created_at: string;
  updated_at?: string;
}

// Constraint Check
export interface ConstraintCheckResponse {
  check_id: string;
  student_id: string;
  constraint_type: string;
  constraint_name: string;
  is_satisfied: boolean;
  current_value?: string;
  required_value?: string;
  gap_description?: string;
  checked_at: string;
}

// Prerequisite Rule
export interface PrerequisiteRuleResponse {
  rule_id: string;
  course_cd: string;
  course_nm?: string;
  prerequisite_cd: string;
  prerequisite_nm?: string;
  rule_type: 'required' | 'recommended' | 'corequisite';
  min_grade?: string;
}

// Risk Recommendation
export interface RiskRecommendation {
  priority: number;
  category: RiskCategory;
  action: string;
  description: string;
  deadline?: string;
  resources: string[];
}

// Student Risk Profile
export interface StudentRiskProfile {
  student_id: string;
  student_name?: string;
  overall_risk_score: number; // 0-100, 0=safe, 100=very risky
  risk_level: RiskSeverity;

  // Category scores
  gpa_risk_score: number;
  credits_risk_score: number;
  prerequisite_risk_score: number;
  graduation_risk_score: number;
  career_risk_score: number;

  // Active alerts
  active_alerts: RiskAlertResponse[];
  total_active_alerts: number;
  critical_alerts: number;
  high_alerts: number;

  // Constraints
  unsatisfied_constraints: ConstraintCheckResponse[];

  // Recommendations
  recommendations: RiskRecommendation[];

  // Meta
  last_analyzed_at: string;
  next_review_date?: string;
}

// Risk Analysis
export interface RiskAnalysisRequest {
  student_id: string;
  categories?: RiskCategory[];
  include_recommendations?: boolean;
  force_refresh?: boolean;
}

export interface RiskAnalysisResponse {
  profile: StudentRiskProfile;
  analysis_summary: string;
  key_risks: string[];
  immediate_actions: string[];
  generated_at: string;
}

// Helper for severity colors
export const SEVERITY_COLORS: Record<RiskSeverity, string> = {
  low: '#22c55e',      // green-500
  medium: '#f59e0b',   // amber-500
  high: '#ef4444',     // red-500
  critical: '#dc2626', // red-600
};

export const SEVERITY_LABELS: Record<RiskSeverity, string> = {
  low: '낮음',
  medium: '보통',
  high: '높음',
  critical: '심각',
};

export const CATEGORY_LABELS: Record<RiskCategory, string> = {
  gpa: '학점',
  credits: '이수학점',
  attendance: '출석',
  prerequisite: '선수과목',
  graduation: '졸업요건',
  career: '진로',
  skill_gap: '스킬 갭',
};
