import { coachingApi } from './client';
import type {
  GoalResponse,
  GoalCreate,
  GoalUpdate,
  GoalProgressSummary,
  PlanItemResponse,
  PlanItemCreate,
  PlanItemUpdate,
  CheckinResponse,
  CheckinCreate,
  RetrospectiveResponse,
  RetrospectiveCreate,
  CoachingSessionResponse,
  AICoachRequest,
  AICoachResponse,
} from '@/types';

export const coachingService = {
  // ==================== Goals ====================

  // Get all goals for a student
  getStudentGoals: async (studentId: string): Promise<GoalResponse[]> => {
    const response = await coachingApi.get(`/coaching/goals/student/${studentId}`);
    return response.data;
  },

  // Get goal progress summary
  getGoalProgressSummary: async (studentId: string): Promise<GoalProgressSummary> => {
    const response = await coachingApi.get(`/coaching/goals/student/${studentId}/summary`);
    return response.data;
  },

  // Get single goal
  getGoal: async (goalId: string): Promise<GoalResponse> => {
    const response = await coachingApi.get(`/coaching/goals/${goalId}`);
    return response.data;
  },

  // Create goal
  createGoal: async (data: GoalCreate): Promise<GoalResponse> => {
    const response = await coachingApi.post('/coaching/goals', data);
    return response.data;
  },

  // Update goal
  updateGoal: async (goalId: string, data: GoalUpdate): Promise<GoalResponse> => {
    const response = await coachingApi.patch(`/coaching/goals/${goalId}`, data);
    return response.data;
  },

  // Delete goal
  deleteGoal: async (goalId: string): Promise<void> => {
    await coachingApi.delete(`/coaching/goals/${goalId}`);
  },

  // ==================== Plan Items ====================

  // Get plan items for a goal
  getPlanItems: async (goalId: string): Promise<PlanItemResponse[]> => {
    const response = await coachingApi.get(`/coaching/goals/${goalId}/plan-items`);
    return response.data;
  },

  // Create plan item
  createPlanItem: async (data: PlanItemCreate): Promise<PlanItemResponse> => {
    const response = await coachingApi.post('/coaching/plan-items', data);
    return response.data;
  },

  // Update plan item
  updatePlanItem: async (planId: string, data: PlanItemUpdate): Promise<PlanItemResponse> => {
    const response = await coachingApi.patch(`/coaching/plan-items/${planId}`, data);
    return response.data;
  },

  // Delete plan item
  deletePlanItem: async (planId: string): Promise<void> => {
    await coachingApi.delete(`/coaching/plan-items/${planId}`);
  },

  // ==================== Check-ins ====================

  // Get check-ins for a goal
  getCheckins: async (goalId: string): Promise<CheckinResponse[]> => {
    const response = await coachingApi.get(`/coaching/goals/${goalId}/checkins`);
    return response.data;
  },

  // Create check-in
  createCheckin: async (data: CheckinCreate): Promise<CheckinResponse> => {
    const response = await coachingApi.post('/coaching/checkins', data);
    return response.data;
  },

  // Get student's recent check-ins
  getStudentCheckins: async (studentId: string, limit?: number): Promise<CheckinResponse[]> => {
    const url = limit
      ? `/coaching/checkins/student/${studentId}?limit=${limit}`
      : `/coaching/checkins/student/${studentId}`;
    const response = await coachingApi.get(url);
    return response.data;
  },

  // ==================== Retrospectives ====================

  // Get retrospective for a goal
  getRetrospective: async (goalId: string): Promise<RetrospectiveResponse | null> => {
    try {
      const response = await coachingApi.get(`/coaching/goals/${goalId}/retrospective`);
      return response.data;
    } catch {
      return null;
    }
  },

  // Create retrospective
  createRetrospective: async (data: RetrospectiveCreate): Promise<RetrospectiveResponse> => {
    const response = await coachingApi.post('/coaching/retrospectives', data);
    return response.data;
  },

  // ==================== Coaching Session ====================

  // Get full coaching session for a goal
  getCoachingSession: async (goalId: string): Promise<CoachingSessionResponse> => {
    const response = await coachingApi.get(`/coaching/session/${goalId}`);
    return response.data;
  },

  // ==================== AI Coach ====================

  // Get AI coach response
  getAICoachResponse: async (data: AICoachRequest): Promise<AICoachResponse> => {
    const response = await coachingApi.post('/coaching/ai-coach', data);
    return response.data;
  },

  // Get AI suggestions for goal planning
  getAIPlanSuggestions: async (goalId: string): Promise<{ suggestions: string[] }> => {
    const response = await coachingApi.get(`/coaching/goals/${goalId}/ai-suggestions`);
    return response.data;
  },
};
