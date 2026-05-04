'use client';

import { useState, useEffect, useCallback } from 'react';
import { simulationService } from '@/lib/api/simulation';
import type {
  ScenarioResponse,
  SimulationResultResponse,
  ComparisonResponse,
  ScenarioCreate,
  ScenarioType,
  SimulationVariable,
  ScenarioVariable,
  ScenarioTypeInfo,
  SuggestedScenario,
} from '@/types';

interface SimulationSectionProps {
  studentId: string;
}

// Form state for creating scenarios (different from API ScenarioVariable)
interface FormScenarioCreate {
  student_id: string;
  scenario_type: ScenarioType;
  name: string;
  description?: string;
  formVariables: SimulationVariable[]; // For form rendering
}

const scenarioTypeLabels: Record<ScenarioType, string> = {
  course_selection: '📚 과목 선택',
  career_path: '🎯 진로 경로',
  skill_development: '💪 스킬 개발',
  opportunity: '🚀 기회 선택',
  timeline: '📅 타임라인',
};

const scenarioTypeDescriptions: Record<ScenarioType, string> = {
  course_selection: '수강 과목이 GPA와 역량에 미치는 영향 분석',
  career_path: '목표 직무 준비도 및 취업 가능성 예측',
  skill_development: '스킬 향상에 따른 경쟁력 변화 시뮬레이션',
  opportunity: '인턴십/공모전/자격증 취득 효과 분석',
  timeline: '목표 달성까지의 최적 경로 설계',
};

const scenarioTypeIcons: Record<ScenarioType, string> = {
  course_selection: '📚',
  career_path: '🎯',
  skill_development: '💪',
  opportunity: '🚀',
  timeline: '📅',
};

const defaultVariables: Record<ScenarioType, SimulationVariable[]> = {
  course_selection: [
    { name: 'course_cd', display_name: '과목 코드', type: 'string', value: '' },
    { name: 'expected_grade', display_name: '예상 학점', type: 'select', value: 'A', options: ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D+', 'D', 'F'] },
  ],
  career_path: [
    { name: 'target_role', display_name: '목표 직무', type: 'string', value: '' },
    { name: 'target_company_type', display_name: '목표 기업 유형', type: 'select', value: '대기업', options: ['대기업', '중견기업', '스타트업', '공기업', '외국계'] },
  ],
  skill_development: [
    { name: 'skill_cd', display_name: '스킬 코드', type: 'string', value: '' },
    { name: 'target_level', display_name: '목표 레벨', type: 'number', value: 4, min: 1, max: 5 },
  ],
  opportunity: [
    { name: 'opportunity_type', display_name: '기회 유형', type: 'select', value: '인턴십', options: ['인턴십', '공모전', '연구참여', '대외활동', '장학금'] },
    { name: 'expected_outcome', display_name: '예상 결과', type: 'select', value: '합격', options: ['합격', '수상', '완료', '참여'] },
  ],
  timeline: [
    { name: 'timeline_type', display_name: '타임라인 유형', type: 'select', value: '학기', options: ['학기', '연도', '전체'] },
    { name: 'prediction_range', display_name: '예측 범위', type: 'number', value: 2, min: 1, max: 8 },
  ],
};

export default function SimulationSection({ studentId }: SimulationSectionProps) {
  const [scenarios, setScenarios] = useState<ScenarioResponse[]>([]);
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SimulationResultResponse | null>(null);
  const [selectedScenarioDetail, setSelectedScenarioDetail] = useState<ScenarioResponse | null>(null);

  // New state for API-loaded scenario types and suggestions
  const [scenarioTypes, setScenarioTypes] = useState<ScenarioTypeInfo[]>([]);
  const [suggestedScenarios, setSuggestedScenarios] = useState<SuggestedScenario[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Convert form variables to API format
  const convertToApiVariables = (formVars: SimulationVariable[]): ScenarioVariable[] => {
    return formVars.map(v => ({
      name: v.name,
      current_value: v.value,
      simulated_value: v.value,
      impact_description: v.display_name,
    }));
  };

  // New scenario form state
  const [newScenario, setNewScenario] = useState<FormScenarioCreate>({
    student_id: studentId,
    scenario_type: 'course_selection',
    name: '',
    description: '',
    formVariables: defaultVariables.course_selection,
  });

  const fetchScenarios = useCallback(async () => {
    setLoading(true);
    try {
      const data = await simulationService.getStudentScenarios(studentId);
      setScenarios(data);
    } catch (error) {
      console.error('Failed to fetch scenarios:', error);
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  // Fetch scenario types from API
  const fetchScenarioTypes = useCallback(async () => {
    try {
      const types = await simulationService.getScenarioTypes();
      setScenarioTypes(types as unknown as ScenarioTypeInfo[]);
    } catch (error) {
      console.error('Failed to fetch scenario types:', error);
    }
  }, []);

  // Fetch suggested scenarios for the student
  const fetchSuggestedScenarios = useCallback(async () => {
    try {
      const suggestions = await simulationService.getSuggestedScenarios(studentId);
      setSuggestedScenarios(suggestions as unknown as SuggestedScenario[]);
    } catch (error) {
      console.error('Failed to fetch suggested scenarios:', error);
    }
  }, [studentId]);

  useEffect(() => {
    fetchScenarios();
    fetchScenarioTypes();
    fetchSuggestedScenarios();
  }, [fetchScenarios, fetchScenarioTypes, fetchSuggestedScenarios]);

  const handleTypeChange = (type: ScenarioType) => {
    setNewScenario(prev => ({
      ...prev,
      scenario_type: type,
      formVariables: defaultVariables[type],
    }));
  };

  const handleVariableChange = (index: number, value: string | number) => {
    setNewScenario(prev => {
      const formVariables = [...prev.formVariables];
      formVariables[index] = { ...formVariables[index], value };
      return { ...prev, formVariables };
    });
  };

  const handleCreateScenario = async () => {
    if (!newScenario.name || !newScenario.scenario_type) return;

    try {
      const scenarioCreate: ScenarioCreate = {
        student_id: newScenario.student_id,
        scenario_type: newScenario.scenario_type,
        name: newScenario.name,
        description: newScenario.description,
        variables: convertToApiVariables(newScenario.formVariables),
      };
      const created = await simulationService.createScenario(scenarioCreate);
      setScenarios(prev => [...prev, created]);
      setShowCreateModal(false);
      setNewScenario({
        student_id: studentId,
        scenario_type: 'course_selection',
        name: '',
        description: '',
        formVariables: defaultVariables.course_selection,
      });
    } catch (error) {
      console.error('Failed to create scenario:', error);
    }
  };

  const handleRunSimulation = async (scenarioId: string) => {
    setSimulating(true);
    try {
      const result = await simulationService.runSimulation(scenarioId);
      setSelectedResult(result);
      // Refresh scenarios to get updated status
      fetchScenarios();
    } catch (error) {
      console.error('Failed to run simulation:', error);
    } finally {
      setSimulating(false);
    }
  };

  const handleCompare = async () => {
    if (selectedScenarios.length < 2) return;

    try {
      const result = await simulationService.compareScenarios({
        student_id: studentId,
        scenario_ids: selectedScenarios,
      });
      setComparison(result);
    } catch (error) {
      console.error('Failed to compare scenarios:', error);
    }
  };

  const handleDeleteScenario = async (scenarioId: string) => {
    if (!confirm('이 시나리오를 삭제하시겠습니까?')) return;

    try {
      await simulationService.deleteScenario(scenarioId);
      setScenarios(prev => prev.filter(s => s.scenario_id !== scenarioId));
      setSelectedScenarios(prev => prev.filter(id => id !== scenarioId));
    } catch (error) {
      console.error('Failed to delete scenario:', error);
    }
  };

  const toggleScenarioSelection = (scenarioId: string) => {
    setSelectedScenarios(prev =>
      prev.includes(scenarioId)
        ? prev.filter(id => id !== scenarioId)
        : [...prev, scenarioId]
    );
  };

  const handleViewDetail = (scenario: ScenarioResponse) => {
    setSelectedScenarioDetail(scenario);
  };

  const getScenarioStatus = (scenario: ScenarioResponse): string => {
    // Derive status from results - if has results, it's completed
    if (scenario.results && scenario.results.length > 0) return 'completed';
    if (scenario.is_saved) return 'saved';
    return 'pending';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'running': return 'bg-blue-100 text-blue-800';
      case 'saved': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return '완료';
      case 'running': return '실행 중';
      case 'saved': return '저장됨';
      case 'failed': return '실패';
      default: return '대기';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Actions Bar */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              + 새 시나리오
            </button>
            {selectedScenarios.length >= 2 && (
              <button
                onClick={handleCompare}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                선택 비교 ({selectedScenarios.length}개)
              </button>
            )}
            <button
              onClick={() => setShowSuggestions(!showSuggestions)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                showSuggestions
                  ? 'bg-amber-100 border-amber-400 text-amber-800'
                  : 'border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              💡 추천 시나리오
            </button>
          </div>
          <span className="text-sm text-gray-500">
            총 {scenarios.length}개의 시나리오
          </span>
        </div>
      </div>

      {/* Suggested Scenarios Section - Enhanced Immersive Display */}
      {showSuggestions && suggestedScenarios.length > 0 && (
        <div className="bg-gradient-to-br from-amber-50 via-orange-50 to-yellow-50 rounded-2xl shadow-lg p-6 border border-amber-200 relative overflow-hidden">
          {/* Decorative Background */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-amber-200/30 to-orange-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-gradient-to-tr from-yellow-200/30 to-amber-200/30 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>

          <div className="relative">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-amber-900 text-lg flex items-center gap-2">
                <span className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center text-white text-xl shadow-md">
                  💡
                </span>
                AI 맞춤 추천 시나리오
              </h3>
              <div className="flex items-center gap-2">
                <span className="px-3 py-1 bg-amber-100 text-amber-700 text-xs rounded-full font-medium">
                  {suggestedScenarios.length}개 추천
                </span>
                <button
                  onClick={() => setShowSuggestions(false)}
                  className="text-amber-600 hover:text-amber-800 p-1"
                >
                  ✕
                </button>
              </div>
            </div>

            <p className="text-amber-800 text-sm mb-4 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              학생 프로필, 학습 현황, 취업시장 데이터를 기반으로 분석한 맞춤 시나리오입니다.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {suggestedScenarios.map((suggestion, idx) => (
                <div
                  key={idx}
                  className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-amber-100 hover:border-amber-400 hover:shadow-xl transition-all cursor-pointer group transform hover:-translate-y-1"
                  onClick={() => {
                    setNewScenario({
                      student_id: studentId,
                      scenario_type: suggestion.scenario_type,
                      name: suggestion.title,
                      description: suggestion.description,
                      formVariables: defaultVariables[suggestion.scenario_type],
                    });
                    setShowCreateModal(true);
                  }}
                >
                  {/* Type Badge */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-2xl">{scenarioTypeIcons[suggestion.scenario_type]}</span>
                    <span className="text-xs px-2 py-1 bg-gradient-to-r from-amber-100 to-orange-100 text-amber-800 rounded-full font-medium">
                      {scenarioTypeLabels[suggestion.scenario_type]}
                    </span>
                  </div>

                  {/* Title */}
                  <h4 className="font-semibold text-gray-900 mb-2 group-hover:text-amber-800 transition-colors">
                    {suggestion.title}
                  </h4>

                  {/* Description */}
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {suggestion.description}
                  </p>

                  {/* Reason */}
                  <div className="p-2 bg-amber-50 rounded-lg border border-amber-100">
                    <p className="text-xs text-amber-700">
                      <span className="font-semibold">추천 이유:</span> {suggestion.reason}
                    </p>
                  </div>

                  {/* CTA */}
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-gray-400">클릭하여 시작</span>
                    <span className="text-amber-600 group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Scenario Types Info */}
      {scenarioTypes.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h3 className="font-medium text-gray-800 mb-3">시뮬레이션 유형</h3>
          <div className="flex flex-wrap gap-2">
            {scenarioTypes.map((type, idx) => (
              <div
                key={idx}
                className="group relative px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-700 hover:bg-indigo-100 hover:text-indigo-700 transition-colors cursor-pointer"
                onClick={() => {
                  handleTypeChange(type.value as ScenarioType);
                  setShowCreateModal(true);
                }}
              >
                {type.label}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                  {type.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map(scenario => (
          <div
            key={scenario.scenario_id}
            className={`bg-white rounded-lg shadow-sm p-4 border-2 transition-colors ${
              selectedScenarios.includes(scenario.scenario_id)
                ? 'border-indigo-500'
                : 'border-transparent hover:border-gray-200'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedScenarios.includes(scenario.scenario_id)}
                  onChange={() => toggleScenarioSelection(scenario.scenario_id)}
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(getScenarioStatus(scenario))}`}>
                  {getStatusLabel(getScenarioStatus(scenario))}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {scenarioTypeLabels[scenario.scenario_type]}
              </span>
            </div>

            <h3 className="font-medium text-gray-900 mb-1">{scenario.name}</h3>
            {scenario.description && (
              <p className="text-sm text-gray-600 mb-3">{scenario.description}</p>
            )}

            {/* Variables Summary */}
            {scenario.variables && scenario.variables.length > 0 && (
              <div className="mb-3 p-2 bg-gray-50 rounded text-xs">
                {scenario.variables.slice(0, 3).map((v, i) => (
                  <div key={i} className="flex justify-between">
                    <span className="text-gray-500">{v.impact_description || v.name}:</span>
                    <span className="font-medium">{String(v.current_value)}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Result Summary (if completed) */}
            {scenario.results && scenario.results.length > 0 && (
              <div className="mb-3 p-2 bg-indigo-50 rounded text-xs">
                <div className="font-medium text-indigo-800 mb-1">결과 요약</div>
                {scenario.results.slice(0, 3).map((result, idx) => (
                  <div key={idx} className="flex justify-between text-indigo-700">
                    <span>{result.metric_name}:</span>
                    <span className="font-medium">
                      {result.simulated_value.toFixed(2)} ({result.change_percent > 0 ? '+' : ''}{result.change_percent.toFixed(1)}%)
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-2 mt-4">
              <button
                onClick={() => handleViewDetail(scenario)}
                className="flex-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
              >
                상세보기
              </button>
              <button
                onClick={() => handleRunSimulation(scenario.scenario_id)}
                disabled={simulating}
                className={`flex-1 px-3 py-1.5 rounded text-sm transition-all ${
                  simulating
                    ? 'bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500 bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite] text-white'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700'
                } disabled:cursor-not-allowed`}
              >
                {simulating ? (
                  <span className="flex items-center justify-center gap-1.5">
                    <span className="w-1.5 h-1.5 bg-white rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                    <span className="w-1.5 h-1.5 bg-white rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                    <span className="w-1.5 h-1.5 bg-white rounded-full animate-bounce"></span>
                    <span className="ml-1">분석 중</span>
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-1">
                    <span>▶</span>
                    시뮬레이션
                  </span>
                )}
              </button>
              <button
                onClick={() => handleDeleteScenario(scenario.scenario_id)}
                className="px-3 py-1.5 border border-red-300 text-red-600 rounded text-sm hover:bg-red-50"
              >
                삭제
              </button>
            </div>
          </div>
        ))}

        {scenarios.length === 0 && (
          <div className="col-span-full">
            {/* Immersive Empty State */}
            <div className="bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 rounded-2xl p-8 text-center border border-indigo-100">
              <div className="max-w-md mx-auto">
                {/* Animated Icon */}
                <div className="relative w-24 h-24 mx-auto mb-6">
                  <div className="absolute inset-0 bg-indigo-200 rounded-full animate-ping opacity-20"></div>
                  <div className="absolute inset-2 bg-indigo-100 rounded-full animate-pulse"></div>
                  <div className="relative w-24 h-24 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-4xl shadow-lg">
                    🔮
                  </div>
                </div>

                <h3 className="text-xl font-bold text-gray-800 mb-2">
                  미래를 시뮬레이션하세요
                </h3>
                <p className="text-gray-600 mb-6">
                  다양한 선택지를 시뮬레이션하고 최적의 진로를 설계하세요.
                  <br />
                  <span className="text-indigo-600 font-medium">AI가 당신의 선택이 미래에 미칠 영향을 분석합니다.</span>
                </p>

                {/* Quick Start Options */}
                <div className="grid grid-cols-2 gap-3 mb-6">
                  {Object.entries(scenarioTypeLabels).slice(0, 4).map(([type, label]) => (
                    <button
                      key={type}
                      onClick={() => {
                        handleTypeChange(type as ScenarioType);
                        setShowCreateModal(true);
                      }}
                      className="p-3 bg-white rounded-xl border border-gray-200 hover:border-indigo-300 hover:shadow-md transition-all text-left group"
                    >
                      <div className="text-2xl mb-1">{scenarioTypeIcons[type as ScenarioType]}</div>
                      <div className="font-medium text-gray-800 text-sm">{label.replace(/^[^\s]+\s/, '')}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{scenarioTypeDescriptions[type as ScenarioType]}</div>
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => setShowSuggestions(true)}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-full font-medium hover:shadow-lg transition-all hover:scale-105"
                >
                  <span>💡</span>
                  AI 추천 시나리오 보기
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">시나리오 비교 결과</h2>
            <button
              onClick={() => setComparison(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Best Scenario Highlight */}
          {comparison.best_scenario_id && (
            <div className="mb-4 p-3 bg-green-50 rounded-lg">
              <span className="text-green-800 font-medium">
                추천 시나리오: {comparison.scenarios.find(s => s.scenario_id === comparison.best_scenario_id)?.name || '알 수 없음'}
              </span>
            </div>
          )}

          {/* Comparison Matrix Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-3">지표</th>
                  {comparison.scenarios.map(s => (
                    <th
                      key={s.scenario_id}
                      className={`text-center py-2 px-3 ${s.scenario_id === comparison.best_scenario_id ? 'bg-green-50' : ''}`}
                    >
                      {s.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(comparison.comparison_matrix).map(([metricName, values]) => (
                  <tr key={metricName} className="border-b">
                    <td className="py-2 px-3 font-medium">{metricName}</td>
                    {comparison.scenarios.map(s => {
                      const value = values[s.scenario_id];
                      const allValues = Object.values(values);
                      const maxValue = Math.max(...allValues);
                      return (
                        <td
                          key={s.scenario_id}
                          className={`text-center py-2 px-3 ${
                            value === maxValue ? 'text-green-600 font-semibold' : ''
                          }`}
                        >
                          {value !== undefined ? value.toFixed(2) : '-'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Recommendation */}
          {comparison.recommendation && (
            <div className="mt-4 p-4 bg-indigo-50 rounded-lg">
              <h3 className="font-medium text-indigo-800 mb-2">AI 추천</h3>
              <p className="text-sm text-indigo-700">{comparison.recommendation}</p>
            </div>
          )}
        </div>
      )}

      {/* Simulation Result Modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">시뮬레이션 결과: {selectedResult.name}</h2>
                <button
                  onClick={() => setSelectedResult(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {/* Overall Score */}
              <div className="mb-6 p-4 bg-indigo-50 rounded-lg text-center">
                <div className="text-sm text-indigo-600 mb-1 flex items-center justify-center gap-1">
                  종합 영향 점수
                  <span className="group relative cursor-help">
                    <span className="text-indigo-400 text-xs">[?]</span>
                    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                      모든 지표의 변화량을 가중평균하여 0~100 사이로 산정합니다
                    </span>
                  </span>
                </div>
                <div className="text-3xl font-bold text-indigo-800">
                  {(selectedResult.overall_impact_score * 100).toFixed(0)}점
                </div>
              </div>

              {/* Results */}
              {selectedResult.results && selectedResult.results.length > 0 ? (
                <div className="mb-6">
                  <h3 className="font-medium mb-3">상세 결과</h3>
                  <p className="text-xs text-gray-500 mb-3">
                    각 지표는 학생의 현재 데이터와 졸업생 통계를 기반으로 시뮬레이션 변수 변경 시의 예상 변화를 계산합니다.
                  </p>
                  <div className="space-y-3">
                    {selectedResult.results.map((result, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium flex items-center gap-1">
                            {result.metric_name}
                            <span className="group relative cursor-help">
                              <span className="text-gray-400 text-xs">[?]</span>
                              <span className="absolute bottom-full left-0 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10 max-w-xs">
                                {result.explanation || '해당 지표의 현재값 대비 시뮬레이션 변수 적용 후 예상 변화량입니다'}
                              </span>
                            </span>
                          </span>
                          <span className={`text-sm font-medium ${
                            result.impact_level === 'positive' ? 'text-green-600' :
                            result.impact_level === 'negative' ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {result.change_percent > 0 ? '+' : ''}{result.change_percent.toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span>현재: {result.current_value.toFixed(2)}</span>
                          <span>→</span>
                          <span>예상: {result.simulated_value.toFixed(2)}</span>
                        </div>
                        {result.explanation && (
                          <p className="text-sm text-gray-500 mt-2">{result.explanation}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="text-center text-gray-500">
                    <div className="text-4xl mb-2">📊</div>
                    <h3 className="font-medium text-gray-700 mb-2">상세 결과 없음</h3>
                    <p className="text-sm">
                      이 시나리오는 상세 분석 결과가 없습니다.
                      <br />
                      새로운 시나리오를 생성하면 상세 결과를 확인할 수 있습니다.
                    </p>
                  </div>
                </div>
              )}

              {/* AI Analysis */}
              {selectedResult.ai_analysis ? (
                <div className="mb-6 space-y-3">
                  <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <h3 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
                      <span>💡</span>
                      AI 분석 및 추천
                    </h3>
                    <p className="text-sm text-yellow-700">{selectedResult.ai_analysis.summary}</p>
                  </div>

                  {selectedResult.ai_analysis.strengths?.length > 0 && (
                    <div className="p-3 bg-green-50 rounded-lg">
                      <h4 className="text-sm font-medium text-green-800 mb-1">강점</h4>
                      <ul className="text-xs text-green-700 space-y-1">
                        {selectedResult.ai_analysis.strengths.map((s, i) => (
                          <li key={i} className="flex items-start gap-1"><span className="mt-0.5">+</span> {s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedResult.ai_analysis.risks?.length > 0 && (
                    <div className="p-3 bg-red-50 rounded-lg">
                      <h4 className="text-sm font-medium text-red-800 mb-1">주의사항</h4>
                      <ul className="text-xs text-red-700 space-y-1">
                        {selectedResult.ai_analysis.risks.map((r, i) => (
                          <li key={i} className="flex items-start gap-1"><span className="mt-0.5">!</span> {r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedResult.ai_analysis.recommendations?.length > 0 && (
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <h4 className="text-sm font-medium text-blue-800 mb-1">실행 추천</h4>
                      <ul className="text-xs text-blue-700 space-y-1">
                        {selectedResult.ai_analysis.recommendations.map((r, i) => (
                          <li key={i} className="flex items-start gap-1"><span className="mt-0.5">{i+1}.</span> {r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedResult.ai_analysis.confidence_reason && (
                    <p className="text-xs text-gray-500 italic">
                      점수 산정 근거: {selectedResult.ai_analysis.confidence_reason}
                    </p>
                  )}
                </div>
              ) : selectedResult.recommendation ? (
                <div className="mb-6 p-4 bg-yellow-50 rounded-lg">
                  <h3 className="font-medium text-yellow-800 mb-2">AI 추천</h3>
                  <p className="text-sm text-yellow-700">{selectedResult.recommendation}</p>
                </div>
              ) : null}

              <button
                onClick={() => setSelectedResult(null)}
                className="mt-6 w-full py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Scenario Detail Modal */}
      {selectedScenarioDetail && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h2 className="text-lg font-semibold">{selectedScenarioDetail.name}</h2>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(getScenarioStatus(selectedScenarioDetail))}`}>
                    {getStatusLabel(getScenarioStatus(selectedScenarioDetail))}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedScenarioDetail(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              {/* Scenario Info */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">시나리오 유형:</span>
                    <span className="ml-2 font-medium">{scenarioTypeLabels[selectedScenarioDetail.scenario_type]}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">생성일:</span>
                    <span className="ml-2 font-medium">
                      {new Date(selectedScenarioDetail.created_at).toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                </div>
                {selectedScenarioDetail.description && (
                  <div className="mt-3 pt-3 border-t">
                    <span className="text-gray-500 text-sm">설명:</span>
                    <p className="mt-1 text-gray-700">{selectedScenarioDetail.description}</p>
                  </div>
                )}
              </div>

              {/* Scenario Variables / Input Parameters */}
              {selectedScenarioDetail.variables && selectedScenarioDetail.variables.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <span className="text-blue-600">📊</span>
                    시나리오 입력값
                  </h3>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="space-y-3">
                      {selectedScenarioDetail.variables.map((variable, idx) => (
                        <div key={idx} className="flex items-center justify-between p-2 bg-white rounded border border-blue-100">
                          <div>
                            <span className="font-medium text-gray-800">
                              {variable.impact_description || variable.name}
                            </span>
                            <span className="text-xs text-gray-400 ml-2">({variable.name})</span>
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <div className="text-xs text-gray-500">현재값</div>
                              <div className="font-medium text-gray-600">
                                {variable.current_value !== null ? String(variable.current_value) : '-'}
                              </div>
                            </div>
                            <span className="text-gray-400">→</span>
                            <div className="text-right">
                              <div className="text-xs text-gray-500">시뮬레이션값</div>
                              <div className="font-medium text-blue-600">
                                {variable.simulated_value !== null ? String(variable.simulated_value) : '-'}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Progress Indicator */}
              <div className="mb-6">
                <h3 className="font-medium mb-3 flex items-center gap-2">
                  <span className="text-purple-600">⚡</span>
                  시뮬레이션 진행 상태
                </h3>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="flex items-center gap-4">
                    {/* Step 1: Created */}
                    <div className="flex flex-col items-center">
                      <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center">
                        ✓
                      </div>
                      <span className="text-xs mt-1 text-gray-600">생성</span>
                    </div>
                    <div className="flex-1 h-1 bg-green-500 rounded"></div>

                    {/* Step 2: Variables Set */}
                    <div className="flex flex-col items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        selectedScenarioDetail.variables && selectedScenarioDetail.variables.length > 0
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-300 text-gray-500'
                      }`}>
                        {selectedScenarioDetail.variables && selectedScenarioDetail.variables.length > 0 ? '✓' : '2'}
                      </div>
                      <span className="text-xs mt-1 text-gray-600">변수설정</span>
                    </div>
                    <div className={`flex-1 h-1 rounded ${
                      selectedScenarioDetail.results && selectedScenarioDetail.results.length > 0
                        ? 'bg-green-500'
                        : 'bg-gray-300'
                    }`}></div>

                    {/* Step 3: Simulated */}
                    <div className="flex flex-col items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        selectedScenarioDetail.results && selectedScenarioDetail.results.length > 0
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-300 text-gray-500'
                      }`}>
                        {selectedScenarioDetail.results && selectedScenarioDetail.results.length > 0 ? '✓' : '3'}
                      </div>
                      <span className="text-xs mt-1 text-gray-600">시뮬레이션</span>
                    </div>
                    <div className={`flex-1 h-1 rounded ${
                      selectedScenarioDetail.recommendation ? 'bg-green-500' : 'bg-gray-300'
                    }`}></div>

                    {/* Step 4: Analyzed */}
                    <div className="flex flex-col items-center">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        selectedScenarioDetail.recommendation
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-300 text-gray-500'
                      }`}>
                        {selectedScenarioDetail.recommendation ? '✓' : '4'}
                      </div>
                      <span className="text-xs mt-1 text-gray-600">분석완료</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Simulation Results */}
              {selectedScenarioDetail.results && selectedScenarioDetail.results.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-medium mb-3 flex items-center gap-2">
                    <span className="text-green-600">📈</span>
                    시뮬레이션 결과
                  </h3>
                  <div className="space-y-3">
                    {selectedScenarioDetail.results.map((result, idx) => (
                      <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-800">{result.metric_name}</span>
                          <span className={`px-2 py-1 rounded text-sm font-medium ${
                            result.impact_level === 'positive' ? 'bg-green-100 text-green-700' :
                            result.impact_level === 'negative' ? 'bg-red-100 text-red-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {result.change_percent > 0 ? '+' : ''}{result.change_percent.toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm mb-2">
                          <div className="flex-1 bg-white rounded p-2 text-center border">
                            <div className="text-xs text-gray-500">현재</div>
                            <div className="font-medium">{result.current_value.toFixed(2)}</div>
                          </div>
                          <span className="text-xl text-gray-400">→</span>
                          <div className="flex-1 bg-indigo-50 rounded p-2 text-center border border-indigo-200">
                            <div className="text-xs text-indigo-600">예상</div>
                            <div className="font-medium text-indigo-700">{result.simulated_value.toFixed(2)}</div>
                          </div>
                        </div>
                        {result.explanation && (
                          <p className="text-sm text-gray-600 italic">&ldquo;{result.explanation}&rdquo;</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Overall Score */}
              {selectedScenarioDetail.overall_impact_score !== undefined && (
                <div className="mb-6 p-4 bg-indigo-50 rounded-lg text-center">
                  <div className="text-sm text-indigo-600 mb-1 flex items-center justify-center gap-1">
                    종합 영향 점수
                    <span className="group relative cursor-help">
                      <span className="text-indigo-400 text-xs">[?]</span>
                      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                        GPA/역량/취업률 등 개별 지표 변화를 가중평균하여 산정
                      </span>
                    </span>
                  </div>
                  <div className="text-3xl font-bold text-indigo-800">
                    {(selectedScenarioDetail.overall_impact_score * 100).toFixed(0)}점
                  </div>
                </div>
              )}

              {/* AI Analysis */}
              {selectedScenarioDetail.ai_analysis ? (
                <div className="mb-6 space-y-3">
                  <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <h3 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
                      <span>💡</span>
                      AI 분석 및 추천
                    </h3>
                    <p className="text-sm text-yellow-700">{selectedScenarioDetail.ai_analysis.summary}</p>
                  </div>

                  {selectedScenarioDetail.ai_analysis.strengths?.length > 0 && (
                    <div className="p-3 bg-green-50 rounded-lg">
                      <h4 className="text-sm font-medium text-green-800 mb-1">강점</h4>
                      <ul className="text-xs text-green-700 space-y-1">
                        {selectedScenarioDetail.ai_analysis.strengths.map((s, i) => (
                          <li key={i} className="flex items-start gap-1"><span className="mt-0.5">+</span> {s}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedScenarioDetail.ai_analysis.risks?.length > 0 && (
                    <div className="p-3 bg-red-50 rounded-lg">
                      <h4 className="text-sm font-medium text-red-800 mb-1">주의사항</h4>
                      <ul className="text-xs text-red-700 space-y-1">
                        {selectedScenarioDetail.ai_analysis.risks.map((r, i) => (
                          <li key={i} className="flex items-start gap-1"><span className="mt-0.5">!</span> {r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedScenarioDetail.ai_analysis.recommendations?.length > 0 && (
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <h4 className="text-sm font-medium text-blue-800 mb-1">실행 추천</h4>
                      <ul className="text-xs text-blue-700 space-y-1">
                        {selectedScenarioDetail.ai_analysis.recommendations.map((r, i) => (
                          <li key={i} className="flex items-start gap-1"><span className="mt-0.5">{i+1}.</span> {r}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedScenarioDetail.ai_analysis.confidence_reason && (
                    <p className="text-xs text-gray-500 italic">
                      점수 산정 근거: {selectedScenarioDetail.ai_analysis.confidence_reason}
                    </p>
                  )}
                </div>
              ) : selectedScenarioDetail.recommendation ? (
                <div className="mb-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <h3 className="font-medium text-yellow-800 mb-2 flex items-center gap-2">
                    <span>💡</span>
                    AI 분석 및 추천
                  </h3>
                  <p className="text-sm text-yellow-700">{selectedScenarioDetail.recommendation}</p>
                </div>
              ) : null}

              {/* Actions */}
              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setSelectedScenarioDetail(null)}
                  className="flex-1 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  닫기
                </button>
                <button
                  onClick={() => {
                    handleRunSimulation(selectedScenarioDetail.scenario_id);
                    setSelectedScenarioDetail(null);
                  }}
                  disabled={simulating}
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {simulating ? '실행 중...' : '다시 시뮬레이션'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Scenario Modal - Enhanced Immersive Design */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl">
            {/* Header with Gradient */}
            <div className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 p-6 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center text-2xl">
                    🔮
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">새 시뮬레이션 시나리오</h2>
                    <p className="text-indigo-200 text-sm">미래의 가능성을 탐색하세요</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-white/70 hover:text-white p-2 hover:bg-white/10 rounded-lg transition-colors"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Scenario Type Selection - Visual Cards */}
              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-3">
                  시뮬레이션 유형 선택
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {Object.entries(scenarioTypeLabels).map(([value, label]) => (
                    <button
                      key={value}
                      onClick={() => handleTypeChange(value as ScenarioType)}
                      className={`p-3 rounded-xl border-2 transition-all text-center ${
                        newScenario.scenario_type === value
                          ? 'border-indigo-500 bg-indigo-50 shadow-md'
                          : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="text-2xl mb-1">{scenarioTypeIcons[value as ScenarioType]}</div>
                      <div className="text-xs font-medium text-gray-700">{label.replace(/^[^\s]+\s/, '')}</div>
                    </button>
                  ))}
                </div>
                {/* Selected Type Description */}
                <div className="mt-3 p-3 bg-indigo-50 rounded-lg border border-indigo-100">
                  <div className="flex items-center gap-2 text-indigo-800">
                    <span className="text-lg">{scenarioTypeIcons[newScenario.scenario_type]}</span>
                    <span className="font-medium">{scenarioTypeLabels[newScenario.scenario_type]}</span>
                  </div>
                  <p className="text-sm text-indigo-600 mt-1">
                    {scenarioTypeDescriptions[newScenario.scenario_type]}
                  </p>
                </div>
              </div>

              {/* Scenario Name */}
              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2">
                  시나리오 이름 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newScenario.name || ''}
                  onChange={e => setNewScenario(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
                  placeholder="예: 보건직 공무원 준비 시뮬레이션"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-2">
                  설명 <span className="text-gray-400 font-normal">(선택)</span>
                </label>
                <textarea
                  value={newScenario.description || ''}
                  onChange={e => setNewScenario(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all resize-none"
                  rows={2}
                  placeholder="이 시나리오로 어떤 미래를 탐색하고 싶은지 설명해주세요"
                />
              </div>

              {/* Variables - Enhanced Display */}
              <div>
                <label className="block text-sm font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <span className="w-6 h-6 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600 text-sm">⚙️</span>
                  시뮬레이션 변수 설정
                </label>
                <div className="bg-gray-50 rounded-xl p-4 space-y-4">
                  {newScenario.formVariables.map((variable, idx) => (
                    <div key={idx} className="flex items-center gap-4 bg-white p-3 rounded-lg border border-gray-200">
                      <div className="flex-shrink-0 w-28">
                        <span className="text-sm font-medium text-gray-700">{variable.display_name}</span>
                      </div>
                      <div className="flex-1">
                        {variable.type === 'select' && variable.options ? (
                          <select
                            value={String(variable.value)}
                            onChange={e => handleVariableChange(idx, e.target.value)}
                            className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          >
                            {variable.options.map(opt => (
                              <option key={opt} value={opt}>{opt}</option>
                            ))}
                          </select>
                        ) : variable.type === 'number' ? (
                          <input
                            type="number"
                            value={Number(variable.value)}
                            onChange={e => handleVariableChange(idx, parseInt(e.target.value))}
                            min={variable.min}
                            max={variable.max}
                            className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          />
                        ) : (
                          <input
                            type="text"
                            value={String(variable.value)}
                            onChange={e => handleVariableChange(idx, e.target.value)}
                            className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            placeholder={`${variable.display_name} 입력`}
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Info Box */}
              <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                <div className="flex items-start gap-3">
                  <span className="text-xl">💡</span>
                  <div>
                    <p className="text-sm text-blue-800 font-medium">시뮬레이션 안내</p>
                    <p className="text-xs text-blue-600 mt-1">
                      시나리오를 생성하면 AI가 학생 프로필과 학습 데이터를 분석하여 미래 예측 결과를 제공합니다.
                      실제 취업시장 데이터와 졸업생 통계를 기반으로 현실적인 분석을 수행합니다.
                    </p>
                    <div className="mt-2 text-xs text-blue-500 space-y-0.5">
                      <p>- <strong>GPA 변화</strong>: 선택 과목의 예상 학점 반영</p>
                      <p>- <strong>역량 점수</strong>: 과목/활동의 역량 기여도 가중합산</p>
                      <p>- <strong>취업 준비도</strong>: 졸업생 취업 패턴 대비 준비 비율</p>
                      <p>- <strong>종합 점수</strong>: 개별 지표의 가중평균 (0~100)</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 font-medium transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleCreateScenario}
                  disabled={!newScenario.name}
                  className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-all shadow-lg hover:shadow-xl"
                >
                  <span className="flex items-center justify-center gap-2">
                    <span>🚀</span>
                    시뮬레이션 생성
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
