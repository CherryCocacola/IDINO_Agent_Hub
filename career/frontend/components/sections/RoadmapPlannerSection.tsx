'use client';

import { useState, useEffect, useCallback } from 'react';
import { roadmapService } from '@/lib/api/roadmap';
import type {
  FullRoadmapResponse,
  GradeRoadmapResponse,
  RoadmapItemResponse,
  RoadmapItemUpdate,
  RoadmapItemStatus,
  RoadmapItemType,
  RoadmapGenerateResponse,
} from '@/types';
import {
  ROADMAP_ITEM_TYPE_LABELS,
  ROADMAP_ITEM_TYPE_ICONS,
  ROADMAP_STATUS_LABELS,
  ROADMAP_STATUS_COLORS,
  GRADE_NAMES,
  SEMESTER_NAMES,
} from '@/types/roadmap';

interface RoadmapPlannerSectionProps {
  studentId: string;
}

const statusButtonColors: Record<RoadmapItemStatus, string> = {
  planned: 'bg-gray-100 text-gray-800 border-gray-300',
  in_progress: 'bg-blue-100 text-blue-800 border-blue-300',
  completed: 'bg-green-100 text-green-800 border-green-300',
  skipped: 'bg-yellow-100 text-yellow-800 border-yellow-300',
};

export default function RoadmapPlannerSection({ studentId }: RoadmapPlannerSectionProps) {
  const [fullRoadmap, setFullRoadmap] = useState<FullRoadmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedGrade, setSelectedGrade] = useState<number | 'all'>('all');
  const [selectedType, setSelectedType] = useState<RoadmapItemType | 'all'>('all');
  const [viewMode, setViewMode] = useState<'timeline' | 'list'>('timeline');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generateResult, setGenerateResult] = useState<RoadmapGenerateResponse | null>(null);
  const [applying, setApplying] = useState(false);
  const [addItemData, setAddItemData] = useState({
    grade_level: 1,
    semester: 1,
    item_type: 'course' as RoadmapItemType,
    title: '',
    description: '',
    priority: 2,
  });

  const fetchRoadmap = useCallback(async () => {
    setLoading(true);
    try {
      const data = await roadmapService.getFullRoadmap(studentId);
      setFullRoadmap(data);
    } catch (error) {
      console.error('Failed to fetch roadmap:', error);
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    fetchRoadmap();
  }, [fetchRoadmap]);

  const handleGenerateRoadmap = async () => {
    setGenerating(true);
    try {
      const result = await roadmapService.generateRoadmap({
        student_id: studentId,
      });
      setGenerateResult(result);
      setShowGenerateModal(true);
    } catch (error) {
      console.error('Failed to generate roadmap:', error);
      alert('AI 로드맵 생성에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setGenerating(false);
    }
  };

  const handleApplyGeneratedRoadmap = async () => {
    if (!generateResult) return;

    setApplying(true);
    try {
      // Apply the generated roadmap items to the database
      for (const gradeRoadmap of generateResult.roadmaps) {
        for (const semester of gradeRoadmap.semesters || []) {
          for (const item of semester.items || []) {
            // Only add AI recommended items that don't exist yet
            if (item.is_ai_recommended) {
              try {
                await roadmapService.addCustomItem(
                  studentId,
                  item.grade_level,
                  item.semester,
                  {
                    item_type: item.item_type,
                    title: item.title,
                    description: item.description,
                    priority: item.priority,
                    status: item.status,
                    is_ai_recommended: true,
                  }
                );
              } catch (err) {
                // Skip if item already exists
                console.warn('Item may already exist:', item.title);
              }
            }
          }
        }
      }

      await fetchRoadmap();
      setShowGenerateModal(false);
      setGenerateResult(null);
      alert('AI 로드맵이 적용되었습니다!');
    } catch (error) {
      console.error('Failed to apply roadmap:', error);
      alert('로드맵 적용에 실패했습니다.');
    } finally {
      setApplying(false);
    }
  };

  const handleUpdateItemStatus = async (itemId: string, status: RoadmapItemStatus) => {
    try {
      await roadmapService.updateItemStatus(itemId, status);
      await fetchRoadmap();
    } catch (error) {
      console.error('Failed to update item status:', error);
    }
  };

  const handleAddItem = async () => {
    if (!addItemData.title) return;

    try {
      await roadmapService.addCustomItem(
        studentId,
        addItemData.grade_level,
        addItemData.semester,
        {
          item_type: addItemData.item_type,
          title: addItemData.title,
          description: addItemData.description,
          priority: addItemData.priority,
          status: 'planned',
          is_ai_recommended: false,
        }
      );
      await fetchRoadmap();
      setShowAddModal(false);
      setAddItemData({
        grade_level: 1,
        semester: 1,
        item_type: 'course',
        title: '',
        description: '',
        priority: 2,
      });
    } catch (error) {
      console.error('Failed to add item:', error);
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    if (!confirm('이 항목을 삭제하시겠습니까?')) return;

    try {
      await roadmapService.removeItem(itemId);
      await fetchRoadmap();
    } catch (error) {
      console.error('Failed to remove item:', error);
    }
  };

  // Get all items across all grades/semesters for filtering
  const getAllItems = (): RoadmapItemResponse[] => {
    if (!fullRoadmap || !fullRoadmap.roadmaps) return [];
    return fullRoadmap.roadmaps.flatMap(grade =>
      (grade.semesters || []).flatMap(semester => semester.items || [])
    );
  };

  const filteredRoadmaps = (fullRoadmap?.roadmaps || []).filter(
    grade => selectedGrade === 'all' || grade.grade_level === selectedGrade
  );

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-12 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      {fullRoadmap && (
        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-lg shadow-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">로드맵 진행률</h2>
              <p className="text-sm opacity-75 mt-1">
                현재 {fullRoadmap.current_grade || 1}학년 {fullRoadmap.current_semester || 1}학기
              </p>
            </div>
            <div className="text-right">
              <div className="text-4xl font-bold">
                {Math.round(fullRoadmap.overall_completion || 0)}%
              </div>
              <div className="text-sm opacity-75">전체 완료율</div>
            </div>
          </div>

          <div className="mt-4">
            <div className="h-3 bg-white/20 rounded-full">
              <div
                className="h-full bg-white rounded-full transition-all"
                style={{ width: `${fullRoadmap.overall_completion || 0}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4 mt-6">
            {[1, 2, 3, 4].map(grade => {
              const gradeData = (fullRoadmap.roadmaps || []).find(r => r.grade_level === grade);
              return (
                <div key={grade} className="bg-white/10 rounded-lg p-3 text-center">
                  <div className="text-2xl font-bold">
                    {gradeData ? Math.round(gradeData.completion_rate) : 0}%
                  </div>
                  <div className="text-xs opacity-75">{GRADE_NAMES[grade]}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            {/* Grade Filter */}
            <select
              value={selectedGrade}
              onChange={e => setSelectedGrade(e.target.value === 'all' ? 'all' : Number(e.target.value))}
              className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">전체 학년</option>
              {[1, 2, 3, 4].map(grade => (
                <option key={grade} value={grade}>{GRADE_NAMES[grade]}</option>
              ))}
            </select>

            {/* View Mode Toggle */}
            <div className="flex border rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('timeline')}
                className={`px-4 py-2 text-sm ${
                  viewMode === 'timeline'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                타임라인
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-4 py-2 text-sm ${
                  viewMode === 'list'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                목록
              </button>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              + 항목 추가
            </button>
            <button
              onClick={handleGenerateRoadmap}
              disabled={generating}
              className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50 disabled:opacity-50"
            >
              {generating ? 'AI 생성 중...' : 'AI 로드맵 생성'}
            </button>
          </div>
        </div>
      </div>

      {/* Timeline View */}
      {viewMode === 'timeline' && (
        <div className="space-y-6">
          {filteredRoadmaps.map(gradeRoadmap => (
            <div key={gradeRoadmap.grade_level} className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{gradeRoadmap.grade_name}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">
                    완료율: {Math.round(gradeRoadmap.completion_rate)}%
                  </span>
                  {gradeRoadmap.career_path && (
                    <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                      {gradeRoadmap.career_path}
                    </span>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {(gradeRoadmap.semesters || []).map(semester => (
                  <div key={semester.semester} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium">{SEMESTER_NAMES[semester.semester]}</h4>
                      <span className="text-xs text-gray-500">
                        {(semester.items || []).length}개 항목
                      </span>
                    </div>

                    <div className="space-y-2">
                      {(semester.items || []).map(item => (
                        <div
                          key={item.item_id}
                          className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-50"
                        >
                          <span className="text-lg">{ROADMAP_ITEM_TYPE_ICONS[item.item_type]}</span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm truncate">{item.title}</span>
                              {item.is_ai_recommended && (
                                <span className="text-xs text-purple-600">✨AI</span>
                              )}
                            </div>
                            <span className="text-xs text-gray-500">
                              {ROADMAP_ITEM_TYPE_LABELS[item.item_type]}
                            </span>
                          </div>
                          <select
                            value={item.status}
                            onChange={e => handleUpdateItemStatus(item.item_id, e.target.value as RoadmapItemStatus)}
                            className={`text-xs px-2 py-1 rounded border ${statusButtonColors[item.status]}`}
                          >
                            {Object.entries(ROADMAP_STATUS_LABELS).map(([value, label]) => (
                              <option key={value} value={value}>{label}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => handleRemoveItem(item.item_id)}
                            className="text-red-500 hover:text-red-700 p-1"
                          >
                            ✕
                          </button>
                        </div>
                      ))}

                      {(!semester.items || semester.items.length === 0) && (
                        <div className="text-center py-4 text-gray-400 text-sm">
                          아직 항목이 없습니다
                        </div>
                      )}
                    </div>

                    {(semester.key_milestones || []).length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <div className="text-xs font-medium text-gray-500 mb-1">주요 마일스톤</div>
                        <div className="flex flex-wrap gap-1">
                          {(semester.key_milestones || []).map((milestone, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs"
                            >
                              {milestone}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-4 border-b">
            <div className="flex gap-2 overflow-x-auto">
              <button
                onClick={() => setSelectedType('all')}
                className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
                  selectedType === 'all'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                전체
              </button>
              {Object.entries(ROADMAP_ITEM_TYPE_LABELS).map(([type, label]) => (
                <button
                  key={type}
                  onClick={() => setSelectedType(type as RoadmapItemType)}
                  className={`px-4 py-2 rounded-full text-sm whitespace-nowrap ${
                    selectedType === type
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {ROADMAP_ITEM_TYPE_ICONS[type as RoadmapItemType]} {label}
                </button>
              ))}
            </div>
          </div>

          <div className="divide-y">
            {getAllItems()
              .filter(item => selectedType === 'all' || item.item_type === selectedType)
              .map(item => (
                <div key={item.item_id} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{ROADMAP_ITEM_TYPE_ICONS[item.item_type]}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium">{item.title}</h4>
                          {item.is_ai_recommended && (
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                              AI 추천
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-gray-500">
                            {GRADE_NAMES[item.grade_level]} {SEMESTER_NAMES[item.semester]}
                          </span>
                          <span className="text-xs text-gray-400">•</span>
                          <span className="text-xs text-gray-500">
                            {ROADMAP_ITEM_TYPE_LABELS[item.item_type]}
                          </span>
                        </div>
                        {item.description && (
                          <p className="text-sm text-gray-600 mt-2">{item.description}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <select
                        value={item.status}
                        onChange={e => handleUpdateItemStatus(item.item_id, e.target.value as RoadmapItemStatus)}
                        className={`text-sm px-3 py-1 rounded border ${statusButtonColors[item.status]}`}
                      >
                        {Object.entries(ROADMAP_STATUS_LABELS).map(([value, label]) => (
                          <option key={value} value={value}>{label}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => handleRemoveItem(item.item_id)}
                        className="text-red-500 hover:text-red-700 p-1"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Add Item Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">로드맵 항목 추가</h2>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">학년</label>
                    <select
                      value={addItemData.grade_level}
                      onChange={e => setAddItemData(prev => ({ ...prev, grade_level: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    >
                      {[1, 2, 3, 4].map(grade => (
                        <option key={grade} value={grade}>{GRADE_NAMES[grade]}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">학기</label>
                    <select
                      value={addItemData.semester}
                      onChange={e => setAddItemData(prev => ({ ...prev, semester: Number(e.target.value) }))}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    >
                      {[1, 2].map(semester => (
                        <option key={semester} value={semester}>{SEMESTER_NAMES[semester]}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">유형</label>
                  <select
                    value={addItemData.item_type}
                    onChange={e => setAddItemData(prev => ({ ...prev, item_type: e.target.value as RoadmapItemType }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    {Object.entries(ROADMAP_ITEM_TYPE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {ROADMAP_ITEM_TYPE_ICONS[value as RoadmapItemType]} {label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">제목</label>
                  <input
                    type="text"
                    value={addItemData.title}
                    onChange={e => setAddItemData(prev => ({ ...prev, title: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    placeholder="항목 제목"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">설명</label>
                  <textarea
                    value={addItemData.description}
                    onChange={e => setAddItemData(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    rows={3}
                    placeholder="항목 설명 (선택)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">우선순위</label>
                  <select
                    value={addItemData.priority}
                    onChange={e => setAddItemData(prev => ({ ...prev, priority: Number(e.target.value) }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value={1}>높음</option>
                    <option value={2}>중간</option>
                    <option value={3}>낮음</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  onClick={handleAddItem}
                  disabled={!addItemData.title}
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  추가
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Generate Result Modal */}
      {showGenerateModal && generateResult && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">🤖</span>
                  <h2 className="text-lg font-semibold">AI 로드맵 생성 결과</h2>
                </div>
                <button
                  onClick={() => {
                    setShowGenerateModal(false);
                    setGenerateResult(null);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[50vh]">
              {/* AI Summary */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                  <span>📝</span> AI 분석 요약
                </h3>
                <p className="text-gray-600 bg-gray-50 p-4 rounded-lg">
                  {generateResult.ai_summary}
                </p>
              </div>

              {/* Key Recommendations */}
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                  <span>💡</span> 핵심 추천사항
                </h3>
                <ul className="space-y-2">
                  {generateResult.key_recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-600">
                      <span className="text-indigo-500 mt-1">•</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Generated Items Preview */}
              <div>
                <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                  <span>✨</span> AI 추천 항목 미리보기
                </h3>
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {generateResult.roadmaps.flatMap(grade =>
                    (grade.semesters || []).flatMap(sem =>
                      (sem.items || [])
                        .filter(item => item.is_ai_recommended)
                        .map(item => (
                          <div
                            key={item.item_id}
                            className="flex items-center gap-2 p-2 bg-purple-50 rounded-lg text-sm"
                          >
                            <span>{ROADMAP_ITEM_TYPE_ICONS[item.item_type]}</span>
                            <span className="font-medium">{item.title}</span>
                            <span className="text-gray-400">•</span>
                            <span className="text-gray-500">
                              {GRADE_NAMES[item.grade_level]} {SEMESTER_NAMES[item.semester]}
                            </span>
                          </div>
                        ))
                    )
                  )}
                </div>
              </div>

              {/* Confidence Score */}
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">AI 신뢰도</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-full bg-green-500 rounded-full"
                        style={{ width: `${(generateResult.confidence_score || 0) * 100}%` }}
                      />
                    </div>
                    <span className="font-medium text-green-600">
                      {Math.round((generateResult.confidence_score || 0) * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 border-t bg-gray-50">
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowGenerateModal(false);
                    setGenerateResult(null);
                  }}
                  className="flex-1 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
                >
                  닫기
                </button>
                <button
                  onClick={handleApplyGeneratedRoadmap}
                  disabled={applying}
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {applying ? '적용 중...' : '로드맵에 적용하기'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
