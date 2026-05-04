'use client';

import { useState, useEffect, useCallback } from 'react';
import { roadmapService } from '@/lib/api/roadmap';
import type {
  FullRoadmapResponse,
  GradeRoadmapResponse,
  RoadmapItemResponse,
  RoadmapItemUpdate,
  RoadmapItemStatus,
  RoadmapGenerateRequest,
} from '@/types';

interface RoadmapState {
  fullRoadmap: FullRoadmapResponse | null;
  currentSemester: GradeRoadmapResponse | null;
  upcomingItems: RoadmapItemResponse[];
  overdueItems: RoadmapItemResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: RoadmapState = {
  fullRoadmap: null,
  currentSemester: null,
  upcomingItems: [],
  overdueItems: [],
  loading: true,
  error: null,
};

export function useRoadmap(studentId: string | null) {
  const [state, setState] = useState<RoadmapState>(initialState);

  // Fetch roadmap data
  const fetchRoadmap = useCallback(async () => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [fullRoadmap, currentSemester, upcomingItems, overdueItems] = await Promise.all([
        roadmapService.getFullRoadmap(studentId),
        roadmapService.getCurrentRoadmap(studentId),
        roadmapService.getUpcomingItems(studentId),
        roadmapService.getOverdueItems(studentId),
      ]);

      setState({
        fullRoadmap,
        currentSemester,
        upcomingItems,
        overdueItems,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Roadmap fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '로드맵 데이터를 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Update roadmap item
  const updateItem = useCallback(async (itemId: string, data: RoadmapItemUpdate) => {
    const updated = await roadmapService.updateRoadmapItem(itemId, data);
    fetchRoadmap();
    return updated;
  }, [fetchRoadmap]);

  // Update item status
  const updateItemStatus = useCallback(async (itemId: string, status: RoadmapItemStatus) => {
    const updated = await roadmapService.updateItemStatus(itemId, status);
    fetchRoadmap();
    return updated;
  }, [fetchRoadmap]);

  // Add custom item
  const addCustomItem = useCallback(async (
    grade: number,
    semester: number,
    item: Partial<RoadmapItemResponse>
  ) => {
    if (!studentId) throw new Error('Student ID is required');
    const created = await roadmapService.addCustomItem(studentId, grade, semester, item);
    fetchRoadmap();
    return created;
  }, [studentId, fetchRoadmap]);

  // Remove item
  const removeItem = useCallback(async (itemId: string) => {
    await roadmapService.removeItem(itemId);
    fetchRoadmap();
  }, [fetchRoadmap]);

  // Generate AI roadmap
  const generateRoadmap = useCallback(async (data: RoadmapGenerateRequest) => {
    return roadmapService.generateRoadmap(data);
  }, []);

  // Apply generated roadmap
  const applyGeneratedRoadmap = useCallback(async (generationId: string) => {
    if (!studentId) throw new Error('Student ID is required');
    const applied = await roadmapService.applyGeneratedRoadmap(studentId, generationId);
    setState(prev => ({
      ...prev,
      fullRoadmap: applied,
    }));
    fetchRoadmap();
    return applied;
  }, [studentId, fetchRoadmap]);

  // Get suggestions for semester
  const getSuggestions = useCallback(async (grade: number, semester: number) => {
    if (!studentId) return [];
    return roadmapService.getSuggestions(studentId, grade, semester);
  }, [studentId]);

  // Get progress
  const getProgress = useCallback(async () => {
    if (!studentId) return null;
    return roadmapService.getRoadmapProgress(studentId);
  }, [studentId]);

  // Reset roadmap
  const resetRoadmap = useCallback(async () => {
    if (!studentId) throw new Error('Student ID is required');
    const reset = await roadmapService.resetRoadmap(studentId);
    setState(prev => ({
      ...prev,
      fullRoadmap: reset,
    }));
    fetchRoadmap();
    return reset;
  }, [studentId, fetchRoadmap]);

  // Get grade roadmap
  const getGradeRoadmap = useCallback(async (grade: number) => {
    if (!studentId) return null;
    return roadmapService.getGradeRoadmap(studentId, grade);
  }, [studentId]);

  // Get items by status (computed from all roadmaps)
  const getItemsByStatus = useCallback((status: RoadmapItemStatus) => {
    if (!state.fullRoadmap) return [];
    const allItems: RoadmapItemResponse[] = [];
    state.fullRoadmap.roadmaps.forEach(gradeRoadmap => {
      gradeRoadmap.semesters.forEach(semester => {
        allItems.push(...semester.items.filter(item => item.status === status));
      });
    });
    return allItems;
  }, [state.fullRoadmap]);

  // Get progress statistics
  const getProgressStats = useCallback(() => {
    if (!state.fullRoadmap) return { total: 0, completed: 0, in_progress: 0, planned: 0, skipped: 0, percentage: 0 };

    let total = 0;
    let completed = 0;
    let in_progress = 0;
    let planned = 0;
    let skipped = 0;

    state.fullRoadmap.roadmaps.forEach(gradeRoadmap => {
      gradeRoadmap.semesters.forEach(semester => {
        semester.items.forEach(item => {
          total++;
          if (item.status === 'completed') completed++;
          else if (item.status === 'in_progress') in_progress++;
          else if (item.status === 'planned') planned++;
          else if (item.status === 'skipped') skipped++;
        });
      });
    });

    return {
      total,
      completed,
      in_progress,
      planned,
      skipped,
      percentage: total > 0 ? Math.round((completed / total) * 100) : 0,
    };
  }, [state.fullRoadmap]);

  // Initial fetch
  useEffect(() => {
    fetchRoadmap();
  }, [fetchRoadmap]);

  return {
    ...state,
    refetch: fetchRoadmap,
    updateItem,
    updateItemStatus,
    addCustomItem,
    removeItem,
    generateRoadmap,
    applyGeneratedRoadmap,
    getSuggestions,
    getProgress,
    resetRoadmap,
    getGradeRoadmap,
    getItemsByStatus,
    getProgressStats,
  };
}
