'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Plus,
  MoreVertical,
  Clock,
  Calendar,
  Tag,
  GripVertical,
  Pencil,
  Trash2,
  X,
  CheckCircle,
  Target,
  BookOpen,
  Activity,
  Code,
  LayoutGrid,
  RefreshCw,
} from 'lucide-react';
import ProgressBar from '@/components/ui/ProgressBar';
import { aiService, SemesterGoal } from '@/lib/api/ai';
import type {
  SprintItem,
  SprintStatus,
  SprintItemType,
  SprintPriority,
  KanbanColumn,
  SPRINT_STATUS_LABELS,
  SPRINT_ITEM_TYPE_LABELS,
  SPRINT_PRIORITY_LABELS,
  SPRINT_PRIORITY_COLORS,
} from '@/types';

interface SprintBoardSectionProps {
  studentId: string;
  semester: string;
  weekNumber: number;
}

const statusLabels: Record<SprintStatus, string> = {
  todo: '할 일',
  in_progress: '진행 중',
  done: '완료',
};

const itemTypeLabels: Record<SprintItemType, string> = {
  course: '강의',
  activity: '활동',
  goal: '목표',
  skill: '스킬',
  custom: '기타',
};

const itemTypeIcons: Record<SprintItemType, React.ReactNode> = {
  course: <BookOpen className="w-3.5 h-3.5" />,
  activity: <Activity className="w-3.5 h-3.5" />,
  goal: <Target className="w-3.5 h-3.5" />,
  skill: <Code className="w-3.5 h-3.5" />,
  custom: <LayoutGrid className="w-3.5 h-3.5" />,
};

const itemTypeColors: Record<SprintItemType, string> = {
  course: 'bg-blue-100 text-blue-700',
  activity: 'bg-purple-100 text-purple-700',
  goal: 'bg-green-100 text-green-700',
  skill: 'bg-amber-100 text-amber-700',
  custom: 'bg-gray-100 text-gray-700',
};

const priorityColors: Record<SprintPriority, { bg: string; text: string; bar: string }> = {
  high: { bg: 'bg-red-50', text: 'text-red-600', bar: 'bg-red-500' },
  medium: { bg: 'bg-amber-50', text: 'text-amber-600', bar: 'bg-amber-500' },
  low: { bg: 'bg-green-50', text: 'text-green-600', bar: 'bg-green-500' },
};

const priorityLabels: Record<SprintPriority, string> = {
  high: '높음',
  medium: '보통',
  low: '낮음',
};

const columnColors: Record<SprintStatus, string> = {
  todo: 'bg-gray-100',
  in_progress: 'bg-blue-50',
  done: 'bg-green-50',
};

// Local storage key
const getStorageKey = (studentId: string, semester: string, weekNumber: number) =>
  `sprint_${studentId}_${semester}_w${weekNumber}`;

// Key for tracking if initial data was loaded from API
const getInitializedKey = (studentId: string, semester: string) =>
  `sprint_initialized_${studentId}_${semester}`;

// Generate unique ID
const generateId = () => `item_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// Convert SemesterGoal from API to SprintItem format
const convertGoalToSprintItem = (goal: SemesterGoal, index: number): SprintItem => ({
  id: generateId(),
  title: goal.label,
  description: (goal as { description?: string }).description || undefined,
  item_type: 'goal' as SprintItemType,
  status: goal.completed ? 'done' : 'todo',
  priority: goal.priority,
  order_index: index,
  created_at: new Date().toISOString(),
});

export default function SprintBoardSection({
  studentId,
  semester,
  weekNumber,
}: SprintBoardSectionProps) {
  const [items, setItems] = useState<SprintItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingItem, setEditingItem] = useState<SprintItem | null>(null);
  const [addToColumn, setAddToColumn] = useState<SprintStatus>('todo');
  const [draggedItem, setDraggedItem] = useState<SprintItem | null>(null);
  const [actionMenuId, setActionMenuId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Load items from localStorage or API
  useEffect(() => {
    const loadItems = async () => {
      setIsLoading(true);
      setApiError(null);
      const key = getStorageKey(studentId, semester, weekNumber);
      const initializedKey = getInitializedKey(studentId, semester);
      const saved = localStorage.getItem(key);

      // If there's saved data, use it
      if (saved) {
        try {
          setItems(JSON.parse(saved));
          setIsLoading(false);
          return;
        } catch {
          // Continue to fetch from API if parsing fails
        }
      }

      // Check if this semester was already initialized (but all items were deleted)
      const wasInitialized = localStorage.getItem(initializedKey);
      if (wasInitialized && !saved) {
        // User intentionally cleared all items, don't re-fetch
        setItems([]);
        setIsLoading(false);
        return;
      }

      // No saved data - fetch from API
      try {
        console.log('📥 Fetching semester goals from API for:', studentId);
        const response = await aiService.getSemesterSprint(studentId);

        if (response.goals && response.goals.length > 0) {
          const sprintItems = response.goals.map((goal, index) =>
            convertGoalToSprintItem(goal, index)
          );

          // Save to localStorage
          localStorage.setItem(key, JSON.stringify(sprintItems));
          localStorage.setItem(initializedKey, 'true');
          setItems(sprintItems);
          console.log('✅ Loaded', sprintItems.length, 'goals from API');
        } else {
          // Mark as initialized even if no goals
          localStorage.setItem(initializedKey, 'true');
          setItems([]);
          console.log('⚠️ No goals found in API response');
        }
      } catch (error) {
        console.error('❌ Failed to fetch semester goals:', error);
        setApiError('학기 목표를 불러오는데 실패했습니다. 새로고침을 시도해주세요.');
        setItems([]);
      }

      setIsLoading(false);
    };

    loadItems();
  }, [studentId, semester, weekNumber]);

  // Function to refresh goals from API
  const handleRefreshFromAPI = async () => {
    setIsRefreshing(true);
    setApiError(null);

    try {
      const response = await aiService.getSemesterSprint(studentId);

      if (response.goals && response.goals.length > 0) {
        const sprintItems = response.goals.map((goal, index) =>
          convertGoalToSprintItem(goal, index)
        );

        // Save to localStorage
        const key = getStorageKey(studentId, semester, weekNumber);
        localStorage.setItem(key, JSON.stringify(sprintItems));
        setItems(sprintItems);
        console.log('✅ Refreshed', sprintItems.length, 'goals from API');
      } else {
        setApiError('불러올 목표가 없습니다.');
      }
    } catch (error) {
      console.error('❌ Failed to refresh goals:', error);
      setApiError('목표 새로고침에 실패했습니다.');
    }

    setIsRefreshing(false);
  };

  // Save items to localStorage
  const saveItems = useCallback((newItems: SprintItem[]) => {
    const key = getStorageKey(studentId, semester, weekNumber);
    localStorage.setItem(key, JSON.stringify(newItems));
    setItems(newItems);
  }, [studentId, semester, weekNumber]);

  // Group items by status for Kanban columns
  const columns: KanbanColumn[] = useMemo(() => {
    const grouped: Record<SprintStatus, SprintItem[]> = {
      todo: [],
      in_progress: [],
      done: [],
    };
    items
      .sort((a, b) => a.order_index - b.order_index)
      .forEach((item) => {
        if (grouped[item.status]) {
          grouped[item.status].push(item);
        }
      });
    return [
      { id: 'todo', title: statusLabels.todo, items: grouped.todo },
      { id: 'in_progress', title: statusLabels.in_progress, items: grouped.in_progress },
      { id: 'done', title: statusLabels.done, items: grouped.done },
    ];
  }, [items]);

  // Stats
  const stats = useMemo(() => {
    const total = items.length;
    const done = items.filter((i) => i.status === 'done').length;
    const inProgress = items.filter((i) => i.status === 'in_progress').length;
    const totalEstimated = items.reduce((sum, i) => sum + (i.estimated_hours || 0), 0);
    const totalActual = items.reduce((sum, i) => sum + (i.actual_hours || 0), 0);
    return {
      total,
      done,
      inProgress,
      completionRate: total ? Math.round((done / total) * 100) : 0,
      totalEstimated,
      totalActual,
    };
  }, [items]);

  // Add item
  const handleAddItem = (newItem: Omit<SprintItem, 'id' | 'order_index' | 'created_at'>) => {
    const item: SprintItem = {
      ...newItem,
      id: generateId(),
      order_index: items.filter((i) => i.status === newItem.status).length,
      created_at: new Date().toISOString(),
    };
    saveItems([...items, item]);
    setShowAddModal(false);
    setAddToColumn('todo');
  };

  // Update item
  const handleUpdateItem = (updatedItem: SprintItem) => {
    const newItems = items.map((i) => (i.id === updatedItem.id ? { ...updatedItem, updated_at: new Date().toISOString() } : i));
    saveItems(newItems);
    setEditingItem(null);
    setShowAddModal(false);
  };

  // Delete item
  const handleDeleteItem = (itemId: string) => {
    if (!confirm('이 항목을 삭제하시겠습니까?')) return;
    saveItems(items.filter((i) => i.id !== itemId));
    setActionMenuId(null);
  };

  // Drag and drop handlers
  const handleDragStart = (e: React.DragEvent, item: SprintItem) => {
    setDraggedItem(item);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetStatus: SprintStatus) => {
    e.preventDefault();
    if (!draggedItem) return;

    if (draggedItem.status !== targetStatus) {
      const updatedItems = items.map((item) =>
        item.id === draggedItem.id
          ? { ...item, status: targetStatus, updated_at: new Date().toISOString() }
          : item
      );
      saveItems(updatedItems);
    }
    setDraggedItem(null);
  };

  // Quick status change
  const handleQuickStatusChange = (itemId: string, newStatus: SprintStatus) => {
    const newItems = items.map((i) =>
      i.id === itemId ? { ...i, status: newStatus, updated_at: new Date().toISOString() } : i
    );
    saveItems(newItems);
  };

  return (
    <div className="space-y-6">
      {/* Week Stats */}
      <div className="bg-card rounded-xl p-6 border border-border">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-text">{semester} 학기 {weekNumber}주차</h3>
            <p className="text-sm text-muted">이번 주 할 일을 관리하세요</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefreshFromAPI}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-3 py-2 border border-border rounded-lg hover:bg-hover transition-colors disabled:opacity-50"
              title="학기 목표 새로고침"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">새로고침</span>
            </button>
            <button
              onClick={() => {
                setEditingItem(null);
                setAddToColumn('todo');
                setShowAddModal(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              <Plus className="w-4 h-4" />
              항목 추가
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-muted mb-1">전체 항목</p>
            <p className="text-2xl font-bold text-text">{stats.total}</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-3">
            <p className="text-xs text-muted mb-1">진행 중</p>
            <p className="text-2xl font-bold text-blue-600">{stats.inProgress}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-3">
            <p className="text-xs text-muted mb-1">완료</p>
            <p className="text-2xl font-bold text-green-600">{stats.done}</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-3">
            <p className="text-xs text-muted mb-1">완료율</p>
            <p className="text-2xl font-bold text-purple-600">{stats.completionRate}%</p>
          </div>
        </div>

        <div className="mt-4">
          <ProgressBar
            label="주간 진행률"
            value={stats.completionRate}
            maxValue={100}
            color="bg-primary"
            showPercentage={false}
            size="md"
          />
        </div>

        {/* API Error Message */}
        {apiError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
            <p className="text-sm text-red-600">{apiError}</p>
            <button
              onClick={() => setApiError(null)}
              className="text-red-600 hover:text-red-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Kanban Board */}
      {isLoading ? (
        <div className="bg-card rounded-xl p-12 border border-border text-center">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-muted">로딩 중...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {columns.map((column) => (
            <div
              key={column.id}
              className={`rounded-xl ${columnColors[column.id]} p-4 min-h-[400px]`}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, column.id)}
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-text">{column.title}</h4>
                  <span className="px-2 py-0.5 text-xs bg-white rounded-full text-muted">
                    {column.items.length}
                  </span>
                </div>
                <button
                  onClick={() => {
                    setEditingItem(null);
                    setAddToColumn(column.id);
                    setShowAddModal(true);
                  }}
                  className="p-1 hover:bg-white/50 rounded"
                >
                  <Plus className="w-4 h-4 text-muted" />
                </button>
              </div>

              <div className="space-y-3">
                {column.items.map((item) => (
                  <div
                    key={item.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, item)}
                    className={`bg-white rounded-lg p-3 border border-border shadow-sm cursor-move hover:shadow-md transition-shadow ${
                      draggedItem?.id === item.id ? 'opacity-50' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <GripVertical className="w-4 h-4 text-gray-300 flex-shrink-0" />
                        <span className={`px-1.5 py-0.5 text-xs rounded ${itemTypeColors[item.item_type]}`}>
                          {itemTypeIcons[item.item_type]}
                        </span>
                      </div>
                      <div className="relative">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setActionMenuId(actionMenuId === item.id ? null : item.id);
                          }}
                          className="p-1 hover:bg-gray-100 rounded"
                        >
                          <MoreVertical className="w-4 h-4 text-muted" />
                        </button>
                        {actionMenuId === item.id && (
                          <div className="absolute right-0 top-full mt-1 w-32 bg-white border border-border rounded-lg shadow-lg z-10">
                            <button
                              onClick={() => {
                                setEditingItem(item);
                                setShowAddModal(true);
                                setActionMenuId(null);
                              }}
                              className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                              수정
                            </button>
                            <button
                              onClick={() => handleDeleteItem(item.id)}
                              className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 text-red-600"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                              삭제
                            </button>
                          </div>
                        )}
                      </div>
                    </div>

                    <h5 className="font-medium text-text text-sm mb-2">{item.title}</h5>

                    {item.description && (
                      <p className="text-xs text-muted mb-2 line-clamp-2">{item.description}</p>
                    )}

                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <span className={`px-1.5 py-0.5 text-xs rounded ${priorityColors[item.priority].bg} ${priorityColors[item.priority].text}`}>
                        {priorityLabels[item.priority]}
                      </span>
                      {item.due_date && (
                        <span className="flex items-center gap-1 text-xs text-muted">
                          <Calendar className="w-3 h-3" />
                          {new Date(item.due_date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                        </span>
                      )}
                      {item.estimated_hours && (
                        <span className="flex items-center gap-1 text-xs text-muted">
                          <Clock className="w-3 h-3" />
                          {item.actual_hours !== undefined ? `${item.actual_hours}/${item.estimated_hours}h` : `${item.estimated_hours}h`}
                        </span>
                      )}
                    </div>

                    {item.tags && item.tags.length > 0 && (
                      <div className="flex items-center gap-1 flex-wrap">
                        {item.tags.slice(0, 3).map((tag, i) => (
                          <span key={i} className="px-1.5 py-0.5 text-xs bg-gray-100 rounded text-muted">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Quick status buttons */}
                    {column.id !== 'done' && (
                      <div className="flex gap-1 mt-2 pt-2 border-t border-gray-100">
                        {column.id === 'todo' && (
                          <button
                            onClick={() => handleQuickStatusChange(item.id, 'in_progress')}
                            className="flex-1 text-xs py-1 text-blue-600 hover:bg-blue-50 rounded"
                          >
                            시작
                          </button>
                        )}
                        <button
                          onClick={() => handleQuickStatusChange(item.id, 'done')}
                          className="flex-1 text-xs py-1 text-green-600 hover:bg-green-50 rounded flex items-center justify-center gap-1"
                        >
                          <CheckCircle className="w-3 h-3" />
                          완료
                        </button>
                      </div>
                    )}
                  </div>
                ))}

                {column.items.length === 0 && (
                  <div className="text-center py-8 text-muted text-sm">
                    <p>항목이 없습니다</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Click outside to close action menu */}
      {actionMenuId && (
        <div className="fixed inset-0 z-0" onClick={() => setActionMenuId(null)} />
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <SprintItemModal
          item={editingItem}
          defaultStatus={addToColumn}
          onClose={() => {
            setShowAddModal(false);
            setEditingItem(null);
          }}
          onSave={(item) => {
            if (editingItem) {
              handleUpdateItem({ ...editingItem, ...item });
            } else {
              handleAddItem(item);
            }
          }}
        />
      )}
    </div>
  );
}

// Sprint Item Modal
interface SprintItemModalProps {
  item?: SprintItem | null;
  defaultStatus: SprintStatus;
  onClose: () => void;
  onSave: (item: Omit<SprintItem, 'id' | 'order_index' | 'created_at'>) => void;
}

function SprintItemModal({ item, defaultStatus, onClose, onSave }: SprintItemModalProps) {
  const [formData, setFormData] = useState({
    title: item?.title || '',
    description: item?.description || '',
    item_type: item?.item_type || 'custom' as SprintItemType,
    status: item?.status || defaultStatus,
    priority: item?.priority || 'medium' as SprintPriority,
    due_date: item?.due_date?.split('T')[0] || '',
    estimated_hours: item?.estimated_hours || '',
    actual_hours: item?.actual_hours || '',
    tags: item?.tags?.join(', ') || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim()) {
      alert('제목을 입력해주세요.');
      return;
    }

    onSave({
      title: formData.title,
      description: formData.description || undefined,
      item_type: formData.item_type,
      status: formData.status,
      priority: formData.priority,
      due_date: formData.due_date || undefined,
      estimated_hours: formData.estimated_hours ? Number(formData.estimated_hours) : undefined,
      actual_hours: formData.actual_hours ? Number(formData.actual_hours) : undefined,
      tags: formData.tags ? formData.tags.split(',').map((t) => t.trim()).filter(Boolean) : undefined,
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <h3 className="font-semibold text-text">
            {item ? '항목 수정' : '새 항목 추가'}
          </h3>
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
              placeholder="항목 제목"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">설명</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary resize-none"
              placeholder="상세 설명 (선택)"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1">유형</label>
              <select
                value={formData.item_type}
                onChange={(e) => setFormData({ ...formData, item_type: e.target.value as SprintItemType })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {Object.entries(itemTypeLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">우선순위</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as SprintPriority })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {Object.entries(priorityLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1">상태</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as SprintStatus })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">마감일</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1">예상 시간 (h)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={formData.estimated_hours}
                onChange={(e) => setFormData({ ...formData, estimated_hours: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1">실제 시간 (h)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={formData.actual_hours}
                onChange={(e) => setFormData({ ...formData, actual_hours: e.target.value })}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="0"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text mb-1">태그</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="쉼표로 구분 (예: 중요, 과제)"
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
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              {item ? '수정' : '추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
