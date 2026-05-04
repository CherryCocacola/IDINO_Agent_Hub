import { opportunityApi } from './client';
import type {
  OpportunityResponse,
  OpportunityListResponse,
  OpportunityCreate,
  OpportunityUpdate,
  OpportunitySearchRequest,
  RecommendationResponse,
  RecommendationRequest,
  ApplicationResponse,
  ApplicationCreate,
  ApplicationUpdate,
  OpportunityType,
} from '@/types';

export const opportunityService = {
  // ==================== Opportunities ====================

  // Get all opportunities with pagination
  getOpportunities: async (
    page = 1,
    pageSize = 20,
    isActive = true
  ): Promise<OpportunityListResponse> => {
    const response = await opportunityApi.get('/opportunities', {
      params: { page, page_size: pageSize, is_active: isActive },
    });
    return response.data;
  },

  // Get single opportunity
  getOpportunity: async (opportunityId: string): Promise<OpportunityResponse> => {
    const response = await opportunityApi.get(`/opportunities/${opportunityId}`);
    return response.data;
  },

  // Search opportunities
  searchOpportunities: async (
    params: OpportunitySearchRequest
  ): Promise<OpportunityListResponse> => {
    const response = await opportunityApi.post('/opportunities/search', params);
    return response.data;
  },

  // Get opportunities by type
  getOpportunitiesByType: async (
    type: OpportunityType,
    page = 1,
    pageSize = 20
  ): Promise<OpportunityListResponse> => {
    const response = await opportunityApi.get(`/opportunities/type/${type}`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  // Create opportunity (admin)
  createOpportunity: async (data: OpportunityCreate): Promise<OpportunityResponse> => {
    const response = await opportunityApi.post('/opportunities', data);
    return response.data;
  },

  // Update opportunity (admin)
  updateOpportunity: async (
    opportunityId: string,
    data: OpportunityUpdate
  ): Promise<OpportunityResponse> => {
    const response = await opportunityApi.patch(`/opportunities/${opportunityId}`, data);
    return response.data;
  },

  // Delete opportunity (admin)
  deleteOpportunity: async (opportunityId: string): Promise<void> => {
    await opportunityApi.delete(`/opportunities/${opportunityId}`);
  },

  // ==================== Recommendations ====================

  // Get personalized recommendations
  getRecommendations: async (
    studentId: string,
    params?: Partial<RecommendationRequest>
  ): Promise<RecommendationResponse> => {
    const response = await opportunityApi.post('/opportunities/recommend', {
      student_id: studentId,
      ...params,
    });
    return response.data;
  },

  // Get top opportunities for student
  getTopOpportunities: async (
    studentId: string,
    limit = 5
  ): Promise<RecommendationResponse> => {
    const response = await opportunityApi.get(
      `/opportunities/recommend/${studentId}?max_results=${limit}`
    );
    return response.data;
  },

  // ==================== Applications ====================

  // Get student's applications
  getStudentApplications: async (
    studentId: string,
    status?: string
  ): Promise<ApplicationResponse[]> => {
    const params = status ? { status } : {};
    const response = await opportunityApi.get(`/opportunities/applications/student/${studentId}`, {
      params,
    });
    return response.data;
  },

  // Get single application
  getApplication: async (applicationId: string): Promise<ApplicationResponse> => {
    const response = await opportunityApi.get(`/opportunities/applications/${applicationId}`);
    return response.data;
  },

  // Create application (express interest)
  createApplication: async (data: ApplicationCreate): Promise<ApplicationResponse> => {
    const response = await opportunityApi.post('/opportunities/applications', data);
    return response.data;
  },

  // Update application status
  updateApplication: async (
    applicationId: string,
    data: ApplicationUpdate
  ): Promise<ApplicationResponse> => {
    const response = await opportunityApi.patch(
      `/opportunities/applications/${applicationId}`,
      data
    );
    return response.data;
  },

  // Withdraw application
  withdrawApplication: async (applicationId: string): Promise<ApplicationResponse> => {
    const response = await opportunityApi.post(
      `/opportunities/applications/${applicationId}/withdraw`
    );
    return response.data;
  },

  // ==================== Utility ====================

  // Get opportunity types
  getOpportunityTypes: async (): Promise<Array<{ type: string; label: string }>> => {
    const response = await opportunityApi.get('/opportunities/types');
    return response.data;
  },

  // Get upcoming deadlines
  getUpcomingDeadlines: async (
    studentId: string,
    days = 30
  ): Promise<OpportunityResponse[]> => {
    const response = await opportunityApi.get(
      `/opportunities/deadlines/${studentId}?days=${days}`
    );
    return response.data;
  },
};
