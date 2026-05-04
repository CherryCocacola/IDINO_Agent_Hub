// Skill Types - matches skill-service (port 8007) schemas

export interface SkillBase {
  skill_cd: string;
  skill_nm: string;
  skill_nm_en?: string;
  category?: string;
  difficulty?: number; // 1-5
}

export interface SkillResponse extends SkillBase {
  synonyms?: string[];
}

export interface StudentSkillBase {
  skill_cd: string;
  current_level: number; // 1-5
  target_level: number; // 1-5
}

export interface StudentSkillResponse extends StudentSkillBase {
  student_skill_id: string;
  skill_nm?: string;
  evidence_count: number;
  last_verified_date?: string;
  verification_source?: string;
  trend: 'improving' | 'stable' | 'declining';
  gap: number; // target_level - current_level
}

export interface StudentSkillUpdate {
  current_level?: number;
  target_level?: number;
  verification_source?: string;
}

// Role-Skill Mapping
export interface RoleSkillMapResponse {
  role_cd: string;
  role_nm?: string;
  skill_cd: string;
  skill_nm?: string;
  required_level: number;
  importance: 'critical' | 'important' | 'nice_to_have';
  market_demand_score?: number;
  growth_trend: 'growing' | 'stable' | 'declining';
}

// Skill Graph
export interface SkillNode {
  id: string; // skill_cd
  name: string;
  category?: string;
  difficulty?: number;
  student_level?: number;
  required_level?: number;
  gap?: number;
  importance?: string;
}

export interface SkillEdge {
  source: string;
  target: string;
  relation_type: 'prerequisite' | 'complementary' | 'alternative' | 'builds_on';
  strength: number;
}

export interface SkillGraphResponse {
  nodes: SkillNode[];
  edges: SkillEdge[];
  role_cd?: string;
  role_nm?: string;
}

// Gap Analysis
export interface SkillGapItem {
  skill_cd: string;
  skill_nm: string;
  current_level: number;
  required_level: number;
  gap: number;
  importance: string;
  priority_rank: number;
  recommended_actions?: string[];
}

export interface GapAnalysisRequest {
  student_id: string;
  target_role_cd: string;
  include_recommendations?: boolean;
}

export interface GapAnalysisResponse {
  analysis_id?: string;
  student_id: string;
  target_role_cd: string;
  target_role_nm?: string;
  analysis_date: string;
  overall_gap_score: number; // 0-100, lower is better
  readiness_percentage: number; // 0-100, higher is better
  skill_gaps: SkillGapItem[];
  top_priority_skills: string[];
  strengths: string[];
  summary: string;
}

// Skill Relation
export interface SkillRelationResponse {
  skill_cd_from: string;
  skill_nm_from?: string;
  skill_cd_to: string;
  skill_nm_to?: string;
  relation_type: string;
  strength: number;
}

// Role Requirement
export interface RoleRequirementResponse {
  role_cd: string;
  role_nm: string;
  role_nm_en?: string;
  industry?: string;
  required_skills: RoleSkillMapResponse[];
  total_skills: number;
  critical_skills: number;
  average_required_level: number;
}
