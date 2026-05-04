import { competencyApi } from './client';
import type { CompetencyReport, CompetencyDefinition, CompetencyScore } from '@/types';

// Backend response types
interface BackendCompetencyScore {
  student_competency_id: string;
  student_id: string;
  competency_cd: string;
  competency_nm: string;
  competency_nm_en?: string;
  definition?: string;
  current_score: number;
  target_score: number;
  gap_score: number;
  status: string;
  trend?: string;
  percentile?: number;
}

interface BackendCompetencyReport {
  student_id: string;
  report_date: string;
  overall_score: number;
  percentile_rank?: number;
  competencies: BackendCompetencyScore[];
  improvement_suggestions: string[];
}

// Color mapping for competency visualization
const COMPETENCY_COLORS: Record<string, string> = {
  '창의역량': '#5b6dff',
  '융복합역량': '#00b7a8',
  '소통역량': '#ff8a5c',
  '협력역량': '#f6c343',
  '도전역량': '#9b59b6',
  // Default color for unknown competencies
  default: '#6b7280',
};

// Convert backend status to frontend status
function mapStatus(status: string): 'excellent' | 'good' | 'average' | 'needs_improvement' {
  switch (status.toLowerCase()) {
    case 'excellent':
      return 'excellent';
    case 'good':
      return 'good';
    case 'average':
      return 'average';
    case 'improve':
    case 'focus':
    case 'needs_improvement':
      return 'needs_improvement';
    default:
      return 'average';
  }
}

// Transform backend response to frontend format
function transformReportResponse(backend: BackendCompetencyReport): CompetencyReport {
  const scores: CompetencyScore[] = backend.competencies.map(comp => {
    return {
      competency_id: comp.competency_cd,
      competency_nm: comp.competency_nm,
      score: comp.current_score,
      max_score: 100, // Not used for clamping; kept for interface compatibility
      percentile: comp.percentile ?? 50,
      status: mapStatus(comp.status),
      color: COMPETENCY_COLORS[comp.competency_nm] || COMPETENCY_COLORS.default,
    };
  });

  // overall_score is SUM from backend
  return {
    student_id: backend.student_id,
    assessment_date: backend.report_date,
    total_score: backend.overall_score,
    percentile_rank: backend.percentile_rank ?? 50,
    scores,
    course_contribution: {},
    activity_contribution: {},
    recommendations: backend.improvement_suggestions,
  };
}

export const competencyService = {
  // Get competency report for a student (transforms backend response to frontend format)
  getReport: async (studentId: string): Promise<CompetencyReport> => {
    const response = await competencyApi.get<BackendCompetencyReport>(`/competency/${studentId}/report`);
    return transformReportResponse(response.data);
  },

  // Get competency history
  getHistory: async (studentId: string) => {
    const response = await competencyApi.get(`/competency/${studentId}/history`);
    return response.data;
  },

  // Get competency definitions
  getDefinitions: async (departmentId?: string): Promise<CompetencyDefinition[]> => {
    const url = departmentId
      ? `/competency/definitions/${departmentId}`
      : '/competency/definitions';
    const response = await competencyApi.get(url);
    return response.data;
  },
};
