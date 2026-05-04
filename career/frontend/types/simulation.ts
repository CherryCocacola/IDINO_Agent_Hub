// Simulation Types - matches simulation-service (port 8013) schemas

export type ScenarioType =
  | 'career_path'        // 진로 경로 시뮬레이션
  | 'skill_development'  // 스킬 개발 시나리오
  | 'course_selection'   // 수강 신청 시나리오
  | 'opportunity'        // 기회 선택 시나리오
  | 'timeline';          // 타임라인 시뮬레이션

export interface ScenarioVariable {
  name: string;
  current_value: unknown;
  simulated_value: unknown;
  impact_description?: string;
}

export interface ScenarioCreate {
  student_id: string;
  scenario_type: ScenarioType;
  name: string;
  description?: string;
  variables: ScenarioVariable[];
  target_date?: string;
}

export interface SimulationResult {
  metric_name: string;
  current_value: number;
  simulated_value: number;
  change_percent: number;
  impact_level: 'positive' | 'negative' | 'neutral';
  explanation?: string;
}

export interface AIAnalysis {
  summary: string;
  strengths: string[];
  risks: string[];
  recommendations: string[];
  next_steps: string[];
  confidence_reason: string;
}

export interface ScenarioResponse {
  scenario_id: string;
  student_id: string;
  scenario_type: ScenarioType;
  name: string;
  description?: string;
  variables: ScenarioVariable[];
  results: SimulationResult[];
  overall_impact_score: number;
  recommendation?: string;
  ai_analysis?: AIAnalysis | null;
  created_at: string;
  is_saved: boolean;
}

export interface ComparisonRequest {
  student_id: string;
  scenario_ids: string[];  // 2-5 scenarios
}

export interface ComparisonResponse {
  comparison_id: string;
  student_id: string;
  scenarios: ScenarioResponse[];
  comparison_matrix: Record<string, Record<string, number>>;
  best_scenario_id: string;
  recommendation: string;
  created_at: string;
}

export interface CareerPathSimulation {
  student_id: string;
  target_role_cd: string;
  current_skills: Record<string, number>;
  planned_courses: string[];
  planned_opportunities: string[];
  timeline_months: number;
}

export interface SkillDevelopmentSimulation {
  student_id: string;
  target_skills: Record<string, number>;  // skill_cd -> target_level
  available_hours_per_week: number;
  learning_resources: string[];
}

// Frontend-specific types
export interface SimulationVariable {
  name: string;
  display_name: string;
  type: 'string' | 'number' | 'select';
  value: string | number;
  options?: string[];
  min?: number;
  max?: number;
}

// Alias for SimulationResult used in UI
export type SimulationResultResponse = ScenarioResponse;

// Scenario update request
export interface ScenarioUpdate {
  name?: string;
  description?: string;
  variables?: ScenarioVariable[];
  target_date?: string;
}

// API Response Types
export interface ScenarioTypeInfo {
  value: string;
  label: string;
  description: string;
}

export interface SuggestedScenario {
  scenario_type: ScenarioType;
  title: string;
  description: string;
  reason: string;
  variables: ScenarioVariable[];
}

// Helper
export const SCENARIO_TYPE_LABELS: Record<ScenarioType, string> = {
  career_path: '진로 경로',
  skill_development: '스킬 개발',
  course_selection: '수강 계획',
  opportunity: '기회 탐색',
  timeline: '타임라인',
};

export const SCENARIO_TYPE_DESCRIPTIONS: Record<ScenarioType, string> = {
  career_path: '목표 직무까지의 경로를 시뮬레이션합니다',
  skill_development: '스킬 개발 시나리오를 비교합니다',
  course_selection: '수강 신청 조합의 효과를 분석합니다',
  opportunity: '다양한 기회 선택의 영향을 예측합니다',
  timeline: '시간에 따른 성장을 시뮬레이션합니다',
};

export const IMPACT_LEVEL_COLORS: Record<string, string> = {
  positive: '#22c55e',  // green-500
  negative: '#ef4444',  // red-500
  neutral: '#6b7280',   // gray-500
};
