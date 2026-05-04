'use client';

import { useState, useEffect, useCallback } from 'react';
import { simulationService } from '@/lib/api/simulation';
import type {
  ScenarioResponse,
  SimulationResultResponse,
  ComparisonResponse,
  ScenarioCreate,
  ScenarioUpdate,
  ComparisonRequest,
} from '@/types';

interface SimulationState {
  scenarios: ScenarioResponse[];
  currentResult: SimulationResultResponse | null;
  comparison: ComparisonResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: SimulationState = {
  scenarios: [],
  currentResult: null,
  comparison: null,
  loading: true,
  error: null,
};

export function useSimulation(studentId: string | null) {
  const [state, setState] = useState<SimulationState>(initialState);

  // Fetch scenarios
  const fetchScenarios = useCallback(async () => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const scenarios = await simulationService.getStudentScenarios(studentId);
      setState(prev => ({
        ...prev,
        scenarios,
        loading: false,
      }));
    } catch (error) {
      console.error('Simulation fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '시뮬레이션 데이터를 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Create scenario
  const createScenario = useCallback(async (data: ScenarioCreate) => {
    const scenario = await simulationService.createScenario(data);
    setState(prev => ({
      ...prev,
      scenarios: [...prev.scenarios, scenario],
    }));
    return scenario;
  }, []);

  // Update scenario
  const updateScenario = useCallback(async (scenarioId: string, data: ScenarioUpdate) => {
    const updated = await simulationService.updateScenario(scenarioId, data);
    setState(prev => ({
      ...prev,
      scenarios: prev.scenarios.map(s => s.scenario_id === scenarioId ? updated : s),
    }));
    return updated;
  }, []);

  // Delete scenario
  const deleteScenario = useCallback(async (scenarioId: string) => {
    await simulationService.deleteScenario(scenarioId);
    setState(prev => ({
      ...prev,
      scenarios: prev.scenarios.filter(s => s.scenario_id !== scenarioId),
    }));
  }, []);

  // Run simulation
  const runSimulation = useCallback(async (scenarioId: string) => {
    const result = await simulationService.runSimulation(scenarioId);
    setState(prev => ({
      ...prev,
      currentResult: result,
      scenarios: prev.scenarios.map(s =>
        s.scenario_id === scenarioId ? result : s
      ),
    }));
    return result;
  }, []);

  // Compare scenarios
  const compareScenarios = useCallback(async (request: ComparisonRequest) => {
    const comparison = await simulationService.compareScenarios(request);
    setState(prev => ({
      ...prev,
      comparison,
    }));
    return comparison;
  }, []);

  // Clear comparison
  const clearComparison = useCallback(() => {
    setState(prev => ({ ...prev, comparison: null }));
  }, []);

  // Clear current result
  const clearResult = useCallback(() => {
    setState(prev => ({ ...prev, currentResult: null }));
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  return {
    ...state,
    refetch: fetchScenarios,
    createScenario,
    updateScenario,
    deleteScenario,
    runSimulation,
    compareScenarios,
    clearComparison,
    clearResult,
  };
}
