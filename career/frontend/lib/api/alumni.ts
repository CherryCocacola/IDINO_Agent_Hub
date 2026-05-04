import { alumniApi } from './client';
import type { AlumniStatistics, SuccessPattern, StudentComparison } from '@/types';

// Transform backend response to frontend expected structure
interface BackendComparisonResponse {
  student_id: string;
  department_cd: string;
  target_role_cd?: string;
  student_gpa?: number;
  student_competencies: Record<string, number>;
  alumni_avg_gpa_range?: string;
  alumni_competencies: Record<string, number>;
  competency_comparisons: Array<{
    competency_cd: string;
    competency_nm: string;
    student_score: number;
    alumni_avg_score: number;
    gap: number;
    status: string;
  }>;
  overall_readiness_score: number;
  improvement_areas: string[];
  // Student extras
  student_credits?: number;
  student_certifications?: number;
  student_activities?: number;
  // Alumni average extras
  alumni_avg_credits?: number;
  alumni_avg_certifications?: number;
  alumni_avg_activities?: number;
  best_matching_pattern?: {
    pattern_id: string;
    pattern_nm?: string;
    description?: string;
    correlation_score?: number;
    sample_size?: number;
  };
}

function parseGpaRange(range?: string): number {
  if (!range) return 3.5;
  // Parse "3.0-4.0" format and return midpoint
  const match = range.match(/(\d+\.?\d*)-(\d+\.?\d*)/);
  if (match) {
    return (parseFloat(match[1]) + parseFloat(match[2])) / 2;
  }
  return parseFloat(range) || 3.5;
}

function buildRecommendations(data: BackendComparisonResponse): string[] {
  // Use competency_comparisons for detailed, actionable recommendations
  const belowComps = data.competency_comparisons
    .filter(c => c.gap < -5)
    .sort((a, b) => a.gap - b.gap); // Worst gaps first

  if (belowComps.length === 0) {
    return ['현재 역량 수준이 동문 평균에 근접합니다'];
  }

  return belowComps.slice(0, 3).map(comp => {
    const absGap = Math.abs(comp.gap).toFixed(1);
    return `'${comp.competency_nm}' 역량이 졸업생 평균(${comp.alumni_avg_score.toFixed(1)}) 대비 ${absGap}점 부족합니다. 관련 교과목과 비교과 활동을 통해 보완하세요.`;
  });
}

function transformComparison(data: BackendComparisonResponse): StudentComparison {
  const studentGpa = data.student_gpa ?? 0;
  const alumniGpa = parseGpaRange(data.alumni_avg_gpa_range);

  // Build competency scores from comparison data
  const studentCompetencies: Record<string, number> = {};
  const alumniCompetencies: Record<string, number> = {};
  const competencyGaps: Record<string, number> = {};

  data.competency_comparisons.forEach(comp => {
    studentCompetencies[comp.competency_nm] = comp.student_score;
    alumniCompetencies[comp.competency_nm] = comp.alumni_avg_score;
    competencyGaps[comp.competency_nm] = comp.gap;
  });

  // Use backend data, fallback to defaults only when null
  const studentCredits = data.student_credits ?? 0;
  const studentCertifications = data.student_certifications ?? 0;
  const studentActivities = data.student_activities ?? 0;
  const alumniCredits = data.alumni_avg_credits ?? 130;
  const alumniCertifications = data.alumni_avg_certifications ?? 3;
  const alumniActivities = data.alumni_avg_activities ?? 7;

  return {
    student_id: data.student_id,
    student_data: {
      gpa: studentGpa,
      credits: studentCredits,
      certifications: studentCertifications,
      activities: studentActivities,
      competency_scores: studentCompetencies,
    },
    alumni_average: {
      gpa: alumniGpa,
      credits: alumniCredits,
      certifications: alumniCertifications,
      activities: alumniActivities,
      competency_scores: alumniCompetencies,
    },
    gap_analysis: {
      gpa_gap: studentGpa - alumniGpa,
      credits_gap: studentCredits - alumniCredits,
      competency_gaps: competencyGaps,
    },
    recommendations: buildRecommendations(data),
  };
}

export const alumniService = {
  // Get alumni benchmark for a department
  getBenchmark: async (departmentId: string): Promise<AlumniStatistics> => {
    const response = await alumniApi.get(`/alumni/benchmark/${departmentId}`);
    return response.data;
  },

  // Get success patterns for a department
  getPatterns: async (departmentId: string): Promise<SuccessPattern[]> => {
    const response = await alumniApi.get(`/alumni/patterns/${departmentId}`);
    return response.data;
  },

  // Compare student with alumni
  compareWithAlumni: async (studentId: string): Promise<StudentComparison> => {
    const response = await alumniApi.get<BackendComparisonResponse>(`/alumni/compare/${studentId}`);
    return transformComparison(response.data);
  },
};
