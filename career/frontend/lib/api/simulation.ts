import { simulationApi } from './client';
import type {
  ScenarioResponse,
  ScenarioCreate,
  ScenarioUpdate,
  ComparisonRequest,
  ComparisonResponse,
  CareerPathSimulation,
  SkillDevelopmentSimulation,
  ScenarioType,
} from '@/types';

export const simulationService = {
  // ==================== Scenarios ====================

  // Get student's scenarios
  getStudentScenarios: async (
    studentId: string,
    scenarioType?: ScenarioType
  ): Promise<ScenarioResponse[]> => {
    const params = scenarioType ? { scenario_type: scenarioType } : {};
    const response = await simulationApi.get(`/simulation/scenarios/student/${studentId}`, {
      params,
    });
    return response.data;
  },

  // Get single scenario
  getScenario: async (scenarioId: string): Promise<ScenarioResponse> => {
    const response = await simulationApi.get(`/simulation/scenarios/${scenarioId}`);
    return response.data;
  },

  // Create new scenario (run simulation)
  createScenario: async (data: ScenarioCreate): Promise<ScenarioResponse> => {
    const response = await simulationApi.post('/simulation/scenarios', data);
    return response.data;
  },

  // Save scenario (mark as saved for future reference)
  saveScenario: async (scenarioId: string): Promise<ScenarioResponse> => {
    const response = await simulationApi.post(`/simulation/scenarios/${scenarioId}/save`);
    return response.data;
  },

  // Delete scenario
  deleteScenario: async (scenarioId: string): Promise<void> => {
    await simulationApi.delete(`/simulation/scenarios/${scenarioId}`);
  },

  // Update scenario
  updateScenario: async (scenarioId: string, data: ScenarioUpdate): Promise<ScenarioResponse> => {
    const response = await simulationApi.put(`/simulation/scenarios/${scenarioId}`, data);
    return response.data;
  },

  // Run simulation (get scenario with results)
  runSimulation: async (scenarioId: string): Promise<ScenarioResponse> => {
    // Get the scenario details which includes computed results
    const response = await simulationApi.get(`/simulation/scenarios/${scenarioId}`);
    return response.data;
  },

  // ==================== Comparison ====================

  // Compare multiple scenarios
  compareScenarios: async (data: ComparisonRequest): Promise<ComparisonResponse> => {
    const response = await simulationApi.post('/simulation/compare', data);
    return response.data;
  },

  // Get comparison result
  getComparison: async (comparisonId: string): Promise<ComparisonResponse> => {
    const response = await simulationApi.get(`/simulation/compare/${comparisonId}`);
    return response.data;
  },

  // ==================== Specialized Simulations ====================

  // Run career path simulation
  runCareerPathSimulation: async (
    data: CareerPathSimulation
  ): Promise<ScenarioResponse> => {
    const response = await simulationApi.post('/simulation/career-path', data);
    return response.data;
  },

  // Run skill development simulation
  runSkillDevelopmentSimulation: async (
    data: SkillDevelopmentSimulation
  ): Promise<ScenarioResponse> => {
    const response = await simulationApi.post('/simulation/skill-development', data);
    return response.data;
  },

  // Course selection simulation
  runCourseSelectionSimulation: async (
    studentId: string,
    courseCodes: string[]
  ): Promise<ScenarioResponse> => {
    const response = await simulationApi.post('/simulation/course-selection', {
      student_id: studentId,
      course_codes: courseCodes,
    });
    return response.data;
  },

  // Timeline simulation
  runTimelineSimulation: async (
    studentId: string,
    targetDate: string,
    milestones: string[]
  ): Promise<ScenarioResponse> => {
    const response = await simulationApi.post('/simulation/timeline', {
      student_id: studentId,
      target_date: targetDate,
      milestones,
    });
    return response.data;
  },

  // ==================== Utility ====================

  // Get scenario types
  getScenarioTypes: async (): Promise<Array<{ type: string; label: string; description: string }>> => {
    const response = await simulationApi.get('/simulation/types');
    return response.data;
  },

  // Get suggested scenarios based on student profile
  getSuggestedScenarios: async (
    studentId: string
  ): Promise<Array<{ type: ScenarioType; reason: string }>> => {
    const response = await simulationApi.get(`/simulation/suggestions/${studentId}`);
    return response.data;
  },
};
