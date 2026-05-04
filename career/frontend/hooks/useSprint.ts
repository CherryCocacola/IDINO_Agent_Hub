'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import type {
  SprintItem,
  SprintStatus,
  SprintItemType,
  SprintPriority,
  SprintWeek,
  KanbanColumn,
} from '@/types';

// Local storage key generator
const getStorageKey = (studentId: string, semester: string, weekNumber: number) =>
  `sprint_${studentId}_${semester}_w${weekNumber}`;

// Generate unique ID
const generateId = () => `item_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

interface SprintState {
  items: SprintItem[];
  loading: boolean;
  error: string | null;
}

const initialState: SprintState = {
  items: [],
  loading: true,
  error: null,
};

export function useSprint(studentId: string | null, semester: string, weekNumber: number) {
  const [state, setState] = useState<SprintState>(initialState);

  // Load items from localStorage
  const loadItems = useCallback(() => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const key = getStorageKey(studentId, semester, weekNumber);
      const saved = localStorage.getItem(key);
      const items = saved ? JSON.parse(saved) : [];
      setState({ items, loading: false, error: null });
    } catch (error) {
      console.error('Failed to load sprint items:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '스프린트 데이터를 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId, semester, weekNumber]);

  // Save items to localStorage
  const saveItems = useCallback((newItems: SprintItem[]) => {
    if (!studentId) return;

    const key = getStorageKey(studentId, semester, weekNumber);
    localStorage.setItem(key, JSON.stringify(newItems));
    setState(prev => ({ ...prev, items: newItems }));
  }, [studentId, semester, weekNumber]);

  // Add item
  const addItem = useCallback((item: Omit<SprintItem, 'id' | 'order_index' | 'created_at'>) => {
    const newItem: SprintItem = {
      ...item,
      id: generateId(),
      order_index: state.items.filter(i => i.status === item.status).length,
      created_at: new Date().toISOString(),
    };
    saveItems([...state.items, newItem]);
    return newItem;
  }, [state.items, saveItems]);

  // Update item
  const updateItem = useCallback((itemId: string, updates: Partial<SprintItem>) => {
    const newItems = state.items.map(item =>
      item.id === itemId
        ? { ...item, ...updates, updated_at: new Date().toISOString() }
        : item
    );
    saveItems(newItems);
  }, [state.items, saveItems]);

  // Delete item
  const deleteItem = useCallback((itemId: string) => {
    const newItems = state.items.filter(item => item.id !== itemId);
    saveItems(newItems);
  }, [state.items, saveItems]);

  // Change item status
  const changeStatus = useCallback((itemId: string, newStatus: SprintStatus) => {
    updateItem(itemId, { status: newStatus });
  }, [updateItem]);

  // Move item (drag and drop)
  const moveItem = useCallback((itemId: string, targetStatus: SprintStatus, targetIndex?: number) => {
    const item = state.items.find(i => i.id === itemId);
    if (!item) return;

    let newItems = state.items.map(i =>
      i.id === itemId
        ? { ...i, status: targetStatus, updated_at: new Date().toISOString() }
        : i
    );

    // Reorder if target index specified
    if (targetIndex !== undefined) {
      const targetItems = newItems.filter(i => i.status === targetStatus && i.id !== itemId);
      targetItems.splice(targetIndex, 0, { ...item, status: targetStatus });
      targetItems.forEach((i, idx) => (i.order_index = idx));
      newItems = [
        ...newItems.filter(i => i.status !== targetStatus),
        ...targetItems,
      ];
    }

    saveItems(newItems);
  }, [state.items, saveItems]);

  // Reorder items within column
  const reorderItems = useCallback((status: SprintStatus, itemIds: string[]) => {
    const newItems = state.items.map(item => {
      if (item.status !== status) return item;
      const newIndex = itemIds.indexOf(item.id);
      return newIndex >= 0 ? { ...item, order_index: newIndex } : item;
    });
    saveItems(newItems);
  }, [state.items, saveItems]);

  // Group items by status (Kanban columns)
  const columns = useMemo((): KanbanColumn[] => {
    const grouped: Record<SprintStatus, SprintItem[]> = {
      todo: [],
      in_progress: [],
      done: [],
    };

    state.items
      .sort((a, b) => a.order_index - b.order_index)
      .forEach(item => {
        if (grouped[item.status]) {
          grouped[item.status].push(item);
        }
      });

    return [
      { id: 'todo', title: '할 일', items: grouped.todo },
      { id: 'in_progress', title: '진행 중', items: grouped.in_progress },
      { id: 'done', title: '완료', items: grouped.done },
    ];
  }, [state.items]);

  // Statistics
  const stats = useMemo(() => {
    const total = state.items.length;
    const done = state.items.filter(i => i.status === 'done').length;
    const inProgress = state.items.filter(i => i.status === 'in_progress').length;
    const todo = state.items.filter(i => i.status === 'todo').length;
    const totalEstimated = state.items.reduce((sum, i) => sum + (i.estimated_hours || 0), 0);
    const totalActual = state.items.reduce((sum, i) => sum + (i.actual_hours || 0), 0);

    return {
      total,
      done,
      inProgress,
      todo,
      completionRate: total ? Math.round((done / total) * 100) : 0,
      totalEstimated,
      totalActual,
      efficiency: totalEstimated ? Math.round((totalActual / totalEstimated) * 100) : 0,
    };
  }, [state.items]);

  // Get week summary
  const getWeekSummary = useCallback((): SprintWeek => {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);

    return {
      week_number: weekNumber,
      start_date: startOfWeek.toISOString(),
      end_date: endOfWeek.toISOString(),
      items: state.items,
      target_hours: stats.totalEstimated,
      actual_hours: stats.totalActual,
      completion_rate: stats.completionRate,
    };
  }, [state.items, weekNumber, stats]);

  // Filter items
  const filterItems = useCallback((
    filterType?: SprintItemType,
    filterPriority?: SprintPriority,
    filterStatus?: SprintStatus
  ) => {
    return state.items.filter(item => {
      if (filterType && item.item_type !== filterType) return false;
      if (filterPriority && item.priority !== filterPriority) return false;
      if (filterStatus && item.status !== filterStatus) return false;
      return true;
    });
  }, [state.items]);

  // Initial load
  useEffect(() => {
    loadItems();
  }, [loadItems]);

  return {
    ...state,
    columns,
    stats,
    refetch: loadItems,
    addItem,
    updateItem,
    deleteItem,
    changeStatus,
    moveItem,
    reorderItems,
    getWeekSummary,
    filterItems,
  };
}
