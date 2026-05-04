'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Target,
  Plus,
  MoreVertical,
  Calendar,
  CheckCircle,
  Clock,
  AlertCircle,
  Pencil,
  Trash2,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { coachingService } from '@/lib/api/coaching';
import ProgressBar from '@/components/ui/ProgressBar';
import type { GoalResponse, GoalCreate, GoalUpdate, GoalStatus, GoalPriority, PlanItemResponse } from '@/types';

interface GoalManagementSectionProps {
  studentId: string;
}

const statusColors: Record<GoalStatus, { bg: string; text: string; label: string }> = {
  draft: { bg: 'bg-gray-100', text: 'text-gray-600', label: '초안' },
  active: { bg: 'bg-blue-100', text: 'text-blue-600', label: '진행중' },
  paused: { bg: 'bg-yellow-100', text: 'text-yellow-600', label: '일시중지' },
  completed: { bg: 'bg-green-100', text: 'text-green-600', label: '완료' },
  abandoned: { bg: 'bg-red-100', text: 'text-red-600', label: '포기' },
};

const priorityColors: Record<GoalPriority, { bg: string; text: string; label: string }> = {
  high: { bg: 'bg-red-100', text: 'text-red-600', label: '높음' },
  medium: { bg: 'bg-amber-100', text: 'text-amber-600', label: '보통' },
  low: { bg: 'bg-green-100', text: 'text-green-600', label: '낮음' },
};

const goalTypeLabels: Record<string, string> = {
  career: '진로',
  skill: '스킬',
  academic: '학업',
  personal: '개인',
};

export default function GoalManagementSection({ studentId }: GoalManagementSectionProps) {
  const [goals, setGoals] = useState<GoalResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [expandedGoal, setExpandedGoal] = useState<string | null>(null);
  const [planItems, setPlanItems] = useState<Map<string, PlanItemResponse[]>>(new Map());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingGoal, setEditingGoal] = useState<GoalResponse | null>(null);
  const [actionMenuGoal, setActionMenuGoal] = useState<string | null>(null);

  // Fetch goals
  const fetchGoals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await coachingService.getStudentGoals(studentId);
      setGoals(data);
    } catch (err) {
      setError('목표를 불러오는데 실패했습니다.');
      console.error('Failed to fetch goals:', err);
    } finally {
      setIsLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  // Fetch plan items for expanded goal
  const fetchPlanItems = async (goalId: string) => {
    try {
      const items = await coachingService.getPlanItems(goalId);
      setPlanItems((prev) => new Map(prev).set(goalId, items));
    } catch (err) {
      console.error('Failed to fetch plan items:', err);
    }
  };

  const toggleGoalExpand = (goalId: string) => {
    if (expandedGoal === goalId) {
      setExpandedGoal(null);
    } else {
      setExpandedGoal(goalId);
      if (!planItems.has(goalId)) {
        fetchPlanItems(goalId);
      }
    }
  };

  const handleDeleteGoal = async (goalId: string) => {
    if (!confirm('이 목표를 삭제하시겠습니까?')) return;
    try {
      await coachingService.deleteGoal(goalId);
      setGoals((prev) => prev.filter((g) => g.goal_id !== goalId));
      setActionMenuGoal(null);
    } catch (err) {
      console.error('Failed to delete goal:', err);
      alert('목표 삭제에 실패했습니다.');
    }
  };

  const handleStatusChange = async (goalId: string, newStatus: GoalStatus) => {
    try {
      const updated = await coachingService.updateGoal(goalId, { status: newStatus });
      setGoals((prev) => prev.map((g) => (g.goal_id === goalId ? updated : g)));
    } catch (err) {
      console.error('Failed to update status:', err);
      alert('상태 변경에 실패했습니다.');
    }
  };

  // Filter goals
  const filteredGoals = goals.filter((g) => filterStatus === 'all' || g.status === filterStatus);

  // Stats
  const stats = {
    total: goals.length,
    active: goals.filter((g) => g.status === 'active').length,
    completed: goals.filter((g) => g.status === 'completed').length,
    avgProgress: goals.length
      ? Math.round(goals.reduce((sum, g) => sum + g.progress_percentage, 0) / goals.length)
      : 0,
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card rounded-xl p-4 border border-border">
          <p className="text-sm text-muted mb-1">전체 목표</p>
          <p className="text-2xl font-bold text-text">{stats.total}</p>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border">
          <p className="text-sm text-muted mb-1">진행중</p>
          <p className="text-2xl font-bold text-blue-600">{stats.active}</p>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border">
          <p className="text-sm text-muted mb-1">완료</p>
          <p className="text-2xl font-bold text-green-600">{stats.completed}</p>
        </div>
        <div className="bg-card rounded-xl p-4 border border-border">
          <p className="text-sm text-muted mb-1">평균 진행률</p>
          <p className="text-2xl font-bold text-primary">{stats.avgProgress}%</p>
        </div>
      </div>

      {/* Header */}
      <div className="bg-card rounded-xl p-6 border border-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100">
              <Target className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-text">내 목표</h3>
              <p className="text-xs text-muted">목표를 설정하고 진행 상황을 추적하세요</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Filter */}
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 text-sm border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">전체 상태</option>
              <option value="active">진행중</option>
              <option value="completed">완료</option>
              <option value="paused">일시중지</option>
              <option value="draft">초안</option>
            </select>

            {/* Add Button */}
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              <Plus className="w-4 h-4" />
              새 목표
            </button>
          </div>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-center py-12 text-red-500">
            <AlertCircle className="w-8 h-8 mx-auto mb-2" />
            <p>{error}</p>
            <button
              onClick={fetchGoals}
              className="mt-2 px-4 py-1 text-sm bg-red-100 rounded-lg hover:bg-red-200"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Goals List */}
        {!isLoading && !error && (
          <div className="space-y-3">
            {filteredGoals.map((goal) => (
              <div
                key={goal.goal_id}
                className="border border-border rounded-lg overflow-hidden"
              >
                {/* Goal Header */}
                <div className="flex items-center justify-between p-4 hover:bg-gray-50">
                  <div
                    className="flex items-center gap-3 flex-1 cursor-pointer"
                    onClick={() => toggleGoalExpand(goal.goal_id)}
                  >
                    {expandedGoal === goal.goal_id ? (
                      <ChevronUp className="w-5 h-5 text-muted" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-muted" />
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-text">{goal.title}</h4>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${statusColors[goal.status].bg} ${statusColors[goal.status].text}`}>
                          {statusColors[goal.status].label}
                        </span>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${priorityColors[goal.priority].bg} ${priorityColors[goal.priority].text}`}>
                          {priorityColors[goal.priority].label}
                        </span>
                        <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                          {goalTypeLabels[goal.goal_type] || goal.goal_type}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted">
                        {goal.target_date && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(goal.target_date).toLocaleDateString('ko-KR')}까지
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          {goal.completed_items_count}/{goal.plan_items_count} 완료
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          체크인 {goal.checkins_count}회
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Progress */}
                  <div className="w-32 mr-4">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-muted">진행률</span>
                      <span className="font-medium">{goal.progress_percentage}%</span>
                    </div>
                    <ProgressBar label="" value={goal.progress_percentage} color="primary" size="sm" showPercentage={false} />
                  </div>

                  {/* Actions Menu */}
                  <div className="relative">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActionMenuGoal(actionMenuGoal === goal.goal_id ? null : goal.goal_id);
                      }}
                      className="p-2 hover:bg-gray-100 rounded-lg"
                    >
                      <MoreVertical className="w-4 h-4 text-muted" />
                    </button>

                    {actionMenuGoal === goal.goal_id && (
                      <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-border rounded-lg shadow-lg z-10">
                        <button
                          onClick={() => {
                            setEditingGoal(goal);
                            setShowCreateModal(true);
                            setActionMenuGoal(null);
                          }}
                          className="w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50 text-left"
                        >
                          <Pencil className="w-4 h-4" />
                          수정
                        </button>
                        {goal.status !== 'completed' && (
                          <button
                            onClick={() => {
                              handleStatusChange(goal.goal_id, 'completed');
                              setActionMenuGoal(null);
                            }}
                            className="w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50 text-left text-green-600"
                          >
                            <CheckCircle className="w-4 h-4" />
                            완료로 표시
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteGoal(goal.goal_id)}
                          className="w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-gray-50 text-left text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                          삭제
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Expanded Content */}
                {expandedGoal === goal.goal_id && (
                  <div className="px-4 pb-4 bg-gray-50 border-t border-border">
                    {goal.description && (
                      <div className="pt-4">
                        <p className="text-sm text-muted mb-1">설명</p>
                        <p className="text-sm text-text">{goal.description}</p>
                      </div>
                    )}

                    {goal.success_criteria && (
                      <div className="pt-3">
                        <p className="text-sm text-muted mb-1">성공 기준</p>
                        <p className="text-sm text-text">{goal.success_criteria}</p>
                      </div>
                    )}

                    {/* Plan Items */}
                    <div className="pt-4">
                      <p className="text-sm text-muted mb-2">계획 항목</p>
                      {planItems.get(goal.goal_id) ? (
                        <div className="space-y-2">
                          {planItems.get(goal.goal_id)!.length > 0 ? (
                            planItems.get(goal.goal_id)!.map((item) => (
                              <div
                                key={item.plan_id}
                                className={`flex items-center gap-3 p-2 rounded-lg ${
                                  item.is_completed ? 'bg-green-50' : 'bg-white'
                                }`}
                              >
                                <div
                                  className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                                    item.is_completed
                                      ? 'bg-green-500 border-green-500'
                                      : 'border-gray-300'
                                  }`}
                                >
                                  {item.is_completed && (
                                    <CheckCircle className="w-3 h-3 text-white" />
                                  )}
                                </div>
                                <span
                                  className={`flex-1 text-sm ${
                                    item.is_completed ? 'line-through text-muted' : 'text-text'
                                  }`}
                                >
                                  {item.title}
                                </span>
                                {item.due_date && (
                                  <span className="text-xs text-muted">
                                    {new Date(item.due_date).toLocaleDateString('ko-KR')}
                                  </span>
                                )}
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-muted">계획 항목이 없습니다</p>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-2">
                          <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {filteredGoals.length === 0 && (
              <div className="text-center py-12">
                <Target className="w-12 h-12 text-muted mx-auto mb-3" />
                <p className="text-muted">
                  {filterStatus === 'all'
                    ? '아직 목표가 없습니다. 새 목표를 추가해보세요!'
                    : '해당 상태의 목표가 없습니다.'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <GoalModal
          studentId={studentId}
          goal={editingGoal}
          onClose={() => {
            setShowCreateModal(false);
            setEditingGoal(null);
          }}
          onSave={() => {
            fetchGoals();
            setShowCreateModal(false);
            setEditingGoal(null);
          }}
        />
      )}

      {/* Click outside to close action menu */}
      {actionMenuGoal && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setActionMenuGoal(null)}
        />
      )}
    </div>
  );
}

// Goal Modal Component
interface GoalModalProps {
  studentId: string;
  goal?: GoalResponse | null;
  onClose: () => void;
  onSave: () => void;
}

function GoalModal({ studentId, goal, onClose, onSave }: GoalModalProps) {
  const [formData, setFormData] = useState<Partial<GoalCreate>>({
    student_id: studentId,
    title: goal?.title || '',
    description: goal?.description || '',
    goal_type: goal?.goal_type || 'career',
    priority: goal?.priority || 'medium',
    target_date: goal?.target_date?.split('T')[0] || '',
    success_criteria: goal?.success_criteria || '',
    motivation: goal?.motivation || '',
  });
  const [isSaving, setIsSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title?.trim()) {
      alert('목표 제목을 입력해주세요.');
      return;
    }

    setIsSaving(true);
    try {
      if (goal) {
        await coachingService.updateGoal(goal.goal_id, formData as GoalUpdate);
      } else {
        await coachingService.createGoal(formData as GoalCreate);
      }
      onSave();
    } catch (err) {
      console.error('Failed to save goal:', err);
      alert('저장에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h3 className="font-semibold text-text">{goal ? '목표 수정' : '새 목표 추가'}</h3>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-text mb-1">제목 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="목표 제목을 입력하세요"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">설명</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              placeholder="목표에 대한 설명을 입력하세요"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1">유형</label>
              <select
                value={formData.goal_type}
                onChange={(e) => setFormData({ ...formData, goal_type: e.target.value as 'career' | 'skill' | 'academic' | 'personal' })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="career">진로</option>
                <option value="skill">스킬</option>
                <option value="academic">학업</option>
                <option value="personal">개인</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">우선순위</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as GoalPriority })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="high">높음</option>
                <option value="medium">보통</option>
                <option value="low">낮음</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">목표 날짜</label>
            <input
              type="date"
              value={formData.target_date}
              onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">성공 기준</label>
            <textarea
              value={formData.success_criteria}
              onChange={(e) => setFormData({ ...formData, success_criteria: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              placeholder="어떻게 되면 성공인지 구체적으로 작성하세요"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">동기</label>
            <textarea
              value={formData.motivation}
              onChange={(e) => setFormData({ ...formData, motivation: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              placeholder="이 목표를 달성하고 싶은 이유는?"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-gray-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isSaving ? '저장 중...' : goal ? '수정' : '추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
