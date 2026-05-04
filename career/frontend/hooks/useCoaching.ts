'use client';

import { useState, useEffect, useCallback } from 'react';
import { coachingService } from '@/lib/api/coaching';
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
  AICoachRequest,
  AICoachResponse,
} from '@/types';

interface CoachingState {
  goals: GoalResponse[];
  progressSummary: GoalProgressSummary | null;
  recentCheckins: CheckinResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: CoachingState = {
  goals: [],
  progressSummary: null,
  recentCheckins: [],
  loading: true,
  error: null,
};

export function useCoaching(studentId: string | null) {
  const [state, setState] = useState<CoachingState>(initialState);

  // Fetch all goals and summary
  const fetchGoals = useCallback(async () => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [goals, progressSummary, recentCheckins] = await Promise.all([
        coachingService.getStudentGoals(studentId),
        coachingService.getGoalProgressSummary(studentId),
        coachingService.getStudentCheckins(studentId, 10),
      ]);

      setState({
        goals,
        progressSummary,
        recentCheckins,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Coaching fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '코칭 데이터를 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Create goal
  const createGoal = useCallback(async (data: GoalCreate) => {
    const newGoal = await coachingService.createGoal(data);
    setState(prev => ({
      ...prev,
      goals: [...prev.goals, newGoal],
    }));
    return newGoal;
  }, []);

  // Update goal
  const updateGoal = useCallback(async (goalId: string, data: GoalUpdate) => {
    const updated = await coachingService.updateGoal(goalId, data);
    setState(prev => ({
      ...prev,
      goals: prev.goals.map(g => g.goal_id === goalId ? updated : g),
    }));
    return updated;
  }, []);

  // Delete goal
  const deleteGoal = useCallback(async (goalId: string) => {
    await coachingService.deleteGoal(goalId);
    setState(prev => ({
      ...prev,
      goals: prev.goals.filter(g => g.goal_id !== goalId),
    }));
  }, []);

  // Get plan items for a goal
  const getPlanItems = useCallback(async (goalId: string): Promise<PlanItemResponse[]> => {
    return coachingService.getPlanItems(goalId);
  }, []);

  // Create plan item
  const createPlanItem = useCallback(async (data: PlanItemCreate) => {
    return coachingService.createPlanItem(data);
  }, []);

  // Update plan item
  const updatePlanItem = useCallback(async (planId: string, data: PlanItemUpdate) => {
    return coachingService.updatePlanItem(planId, data);
  }, []);

  // Delete plan item
  const deletePlanItem = useCallback(async (planId: string) => {
    return coachingService.deletePlanItem(planId);
  }, []);

  // Create checkin
  const createCheckin = useCallback(async (data: CheckinCreate) => {
    const checkin = await coachingService.createCheckin(data);
    setState(prev => ({
      ...prev,
      recentCheckins: [checkin, ...prev.recentCheckins].slice(0, 10),
    }));
    return checkin;
  }, []);

  // Get AI coach response
  const getAICoachResponse = useCallback(async (data: AICoachRequest): Promise<AICoachResponse> => {
    return coachingService.getAICoachResponse(data);
  }, []);

  // Get AI suggestions for goal
  const getAIPlanSuggestions = useCallback(async (goalId: string) => {
    return coachingService.getAIPlanSuggestions(goalId);
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  return {
    ...state,
    refetch: fetchGoals,
    createGoal,
    updateGoal,
    deleteGoal,
    getPlanItems,
    createPlanItem,
    updatePlanItem,
    deletePlanItem,
    createCheckin,
    getAICoachResponse,
    getAIPlanSuggestions,
  };
}
