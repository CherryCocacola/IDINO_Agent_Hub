import { roadmapApi } from './client';
import type {
  GradeRoadmapResponse,
  RoadmapItemResponse,
  RoadmapItemUpdate,
  RoadmapGenerateRequest,
  RoadmapGenerateResponse,
  RoadmapItemType,
  RoadmapItemStatus,
  FullRoadmapResponse,
} from '@/types';

export const roadmapService = {
  // ==================== Full Roadmap ====================

  // Get student's full roadmap (all grades)
  getFullRoadmap: async (studentId: string): Promise<FullRoadmapResponse> => {
    const response = await roadmapApi.get(`/roadmap/student/${studentId}/full`);
    return response.data;
  },

  // Get roadmap for specific grade
  getGradeRoadmap: async (
    studentId: string,
    gradeLevel: number
  ): Promise<GradeRoadmapResponse> => {
    const response = await roadmapApi.get(`/roadmap/student/${studentId}/grade/${gradeLevel}`);
    return response.data;
  },

  // Get current semester roadmap
  getCurrentRoadmap: async (studentId: string): Promise<GradeRoadmapResponse> => {
    const response = await roadmapApi.get(`/roadmap/student/${studentId}/current`);
    return response.data;
  },

  // ==================== Roadmap Items ====================

  // Get single roadmap item
  getRoadmapItem: async (itemId: string): Promise<RoadmapItemResponse> => {
    const response = await roadmapApi.get(`/roadmap/items/${itemId}`);
    return response.data;
  },

  // Update roadmap item
  updateRoadmapItem: async (
    itemId: string,
    data: RoadmapItemUpdate
  ): Promise<RoadmapItemResponse> => {
    const response = await roadmapApi.patch(`/roadmap/items/${itemId}`, data);
    return response.data;
  },

  // Update item status
  updateItemStatus: async (
    itemId: string,
    status: RoadmapItemStatus
  ): Promise<RoadmapItemResponse> => {
    const response = await roadmapApi.patch(`/roadmap/items/${itemId}/status`, { status });
    return response.data;
  },

  // Add custom item to roadmap
  addCustomItem: async (
    studentId: string,
    gradeLevel: number,
    semester: number,
    item: Partial<RoadmapItemResponse>
  ): Promise<RoadmapItemResponse> => {
    const response = await roadmapApi.post('/roadmap/items', {
      student_id: studentId,
      grade_level: gradeLevel,
      semester,
      ...item,
    });
    return response.data;
  },

  // Remove item from roadmap
  removeItem: async (itemId: string): Promise<void> => {
    await roadmapApi.delete(`/roadmap/items/${itemId}`);
  },

  // ==================== Generation ====================

  // Generate AI roadmap
  generateRoadmap: async (data: RoadmapGenerateRequest): Promise<RoadmapGenerateResponse> => {
    const response = await roadmapApi.post('/roadmap/generate', data);
    return response.data;
  },

  // Apply generated roadmap
  applyGeneratedRoadmap: async (
    studentId: string,
    generationId: string
  ): Promise<FullRoadmapResponse> => {
    const response = await roadmapApi.post(`/roadmap/apply/${generationId}`, {
      student_id: studentId,
    });
    return response.data;
  },

  // Get roadmap suggestions
  getSuggestions: async (
    studentId: string,
    gradeLevel: number,
    semester: number
  ): Promise<RoadmapItemResponse[]> => {
    const response = await roadmapApi.get(
      `/roadmap/suggestions/${studentId}?grade=${gradeLevel}&semester=${semester}`
    );
    return response.data;
  },

  // ==================== Progress ====================

  // Get roadmap progress
  getRoadmapProgress: async (
    studentId: string
  ): Promise<{
    overall_completion: number;
    by_grade: Record<number, number>;
    by_type: Record<RoadmapItemType, number>;
    completed_items: number;
    total_items: number;
  }> => {
    const response = await roadmapApi.get(`/roadmap/progress/${studentId}`);
    return response.data;
  },

  // Get upcoming items
  getUpcomingItems: async (
    studentId: string,
    days = 30
  ): Promise<RoadmapItemResponse[]> => {
    const response = await roadmapApi.get(
      `/roadmap/upcoming/${studentId}?days=${days}`
    );
    return response.data;
  },

  // Get overdue items
  getOverdueItems: async (studentId: string): Promise<RoadmapItemResponse[]> => {
    const response = await roadmapApi.get(`/roadmap/overdue/${studentId}`);
    return response.data;
  },

  // ==================== Utility ====================

  // Get roadmap item types
  getItemTypes: async (): Promise<Array<{ type: RoadmapItemType; label: string }>> => {
    const response = await roadmapApi.get('/roadmap/item-types');
    return response.data;
  },

  // Clone roadmap from template
  cloneFromTemplate: async (
    studentId: string,
    templateId: string
  ): Promise<FullRoadmapResponse> => {
    const response = await roadmapApi.post('/roadmap/clone', {
      student_id: studentId,
      template_id: templateId,
    });
    return response.data;
  },

  // Reset roadmap to default
  resetRoadmap: async (studentId: string): Promise<FullRoadmapResponse> => {
    const response = await roadmapApi.post(`/roadmap/reset/${studentId}`);
    return response.data;
  },
};
