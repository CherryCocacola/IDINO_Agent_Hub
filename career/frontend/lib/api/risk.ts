import { riskApi } from './client';
import type {
  RiskAlertResponse,
  RiskAlertUpdate,
  StudentRiskProfile,
  RiskAnalysisResponse,
  RiskAnalysisRequest,
  ConstraintCheckResponse,
  PrerequisiteRuleResponse,
  RiskCategory,
} from '@/types';

export const riskService = {
  // ==================== Alerts ====================

  // Get all alerts for a student
  getStudentAlerts: async (
    studentId: string,
    status?: string,
    category?: RiskCategory
  ): Promise<RiskAlertResponse[]> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    const queryString = params.toString();
    const url = queryString
      ? `/risks/alerts/${studentId}?${queryString}`
      : `/risks/alerts/${studentId}`;
    const response = await riskApi.get(url);
    return response.data;
  },

  // Get single alert
  getAlert: async (alertId: string): Promise<RiskAlertResponse> => {
    const response = await riskApi.get(`/risks/alerts/detail/${alertId}`);
    return response.data;
  },

  // Acknowledge alert
  acknowledgeAlert: async (alertId: string): Promise<RiskAlertResponse> => {
    const response = await riskApi.post(`/risks/alerts/${alertId}/acknowledge`);
    return response.data;
  },

  // Resolve alert
  resolveAlert: async (
    alertId: string,
    resolutionNote?: string
  ): Promise<RiskAlertResponse> => {
    const response = await riskApi.post(`/risks/alerts/${alertId}/resolve`, {
      resolution_note: resolutionNote,
    });
    return response.data;
  },

  // Dismiss alert
  dismissAlert: async (alertId: string): Promise<RiskAlertResponse> => {
    const response = await riskApi.post(`/risks/alerts/${alertId}/dismiss`);
    return response.data;
  },

  // Update alert
  updateAlert: async (
    alertId: string,
    data: RiskAlertUpdate
  ): Promise<RiskAlertResponse> => {
    const response = await riskApi.patch(`/risks/alerts/${alertId}`, data);
    return response.data;
  },

  // ==================== Risk Profile ====================

  // Get student risk profile
  getRiskProfile: async (studentId: string): Promise<StudentRiskProfile> => {
    const response = await riskApi.get(`/risks/profile/${studentId}`);
    return response.data;
  },

  // Refresh risk profile (force recalculation)
  refreshRiskProfile: async (studentId: string): Promise<StudentRiskProfile> => {
    const response = await riskApi.post(`/risks/profile/${studentId}/refresh`);
    return response.data;
  },

  // ==================== Risk Analysis ====================

  // Run full risk analysis
  runRiskAnalysis: async (data: RiskAnalysisRequest): Promise<RiskAnalysisResponse> => {
    const response = await riskApi.post('/risks/analyze', data);
    return response.data;
  },

  // Get risk score breakdown
  getRiskScoreBreakdown: async (
    studentId: string
  ): Promise<Record<RiskCategory, number>> => {
    const response = await riskApi.get(`/risks/profile/${studentId}/breakdown`);
    return response.data;
  },

  // ==================== Constraints ====================

  // Get constraint checks for a student
  getConstraintChecks: async (studentId: string): Promise<ConstraintCheckResponse[]> => {
    const response = await riskApi.get(`/risks/constraints/${studentId}`);
    return response.data;
  },

  // Check specific constraint
  checkConstraint: async (
    studentId: string,
    constraintType: string
  ): Promise<ConstraintCheckResponse> => {
    const response = await riskApi.post(`/risks/constraints/${studentId}/check`, {
      constraint_type: constraintType,
    });
    return response.data;
  },

  // ==================== Prerequisites ====================

  // Get prerequisite rules for a course
  getPrerequisiteRules: async (courseCd: string): Promise<PrerequisiteRuleResponse[]> => {
    const response = await riskApi.get(`/risks/prerequisites/${courseCd}`);
    return response.data;
  },

  // Check if student meets prerequisites for a course
  checkPrerequisites: async (
    studentId: string,
    courseCd: string
  ): Promise<{ is_satisfied: boolean; missing: PrerequisiteRuleResponse[] }> => {
    const response = await riskApi.get(
      `/risks/prerequisites/${courseCd}/check/${studentId}`
    );
    return response.data;
  },

  // ==================== Summary ====================

  // Get risk summary for dashboard
  getRiskSummary: async (
    studentId: string
  ): Promise<{
    risk_level: string;
    score: number;
    active_alerts: number;
    critical_alerts: number;
    top_risks: string[];
  }> => {
    const response = await riskApi.get(`/risks/summary/${studentId}`);
    return response.data;
  },
};
