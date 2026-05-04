import { portfolioApi } from './client';
import type {
  PortfolioResponse,
  PortfolioListResponse,
  PortfolioCreate,
  PortfolioUpdate,
  PortfolioSummaryResponse,
  PortfolioTypesResponse,
  ArtifactType,
} from '@/types';

export const portfolioService = {
  // ==================== Portfolio Items ====================

  // Get student's portfolio items
  getStudentPortfolio: async (studentId: string): Promise<PortfolioListResponse> => {
    const response = await portfolioApi.get(`/portfolio/student/${studentId}`);
    return response.data;
  },

  // Alias for backward compatibility
  getStudentPortfolios: async (studentId: string): Promise<PortfolioListResponse> => {
    const response = await portfolioApi.get(`/portfolio/student/${studentId}`);
    return response.data;
  },

  // Get single portfolio item
  getPortfolioItem: async (portfolioId: string): Promise<PortfolioResponse> => {
    const response = await portfolioApi.get(`/portfolio/${portfolioId}`);
    return response.data;
  },

  // Create portfolio item
  createPortfolioItem: async (data: PortfolioCreate): Promise<PortfolioResponse> => {
    const response = await portfolioApi.post('/portfolio', data);
    return response.data;
  },

  // Update portfolio item
  updatePortfolioItem: async (
    portfolioId: string,
    data: PortfolioUpdate
  ): Promise<PortfolioResponse> => {
    const response = await portfolioApi.put(`/portfolio/${portfolioId}`, data);
    return response.data;
  },

  // Delete portfolio item
  deletePortfolioItem: async (portfolioId: string): Promise<void> => {
    await portfolioApi.delete(`/portfolio/${portfolioId}`);
  },

  // ==================== Primary Item ====================

  // Set as primary portfolio item
  setPrimaryItem: async (portfolioId: string): Promise<PortfolioResponse> => {
    const response = await portfolioApi.post(`/portfolio/${portfolioId}/set-primary`);
    return response.data;
  },

  // Get primary portfolio item
  getPrimaryItem: async (studentId: string): Promise<PortfolioResponse | null> => {
    try {
      const response = await portfolioApi.get(`/portfolio/student/${studentId}/primary`);
      return response.data;
    } catch {
      return null;
    }
  },

  // ==================== Portfolio by Type ====================

  // Get portfolio items by type
  getByType: async (
    studentId: string,
    artifactType: ArtifactType
  ): Promise<PortfolioResponse[]> => {
    const response = await portfolioApi.get(
      `/portfolio/student/${studentId}/type/${artifactType}`
    );
    return response.data;
  },

  // ==================== Summary ====================

  // Get portfolio summary
  getPortfolioSummary: async (studentId: string): Promise<PortfolioSummaryResponse> => {
    const response = await portfolioApi.get(`/portfolio/student/${studentId}/summary`);
    return response.data;
  },

  // ==================== Utility ====================

  // Get available portfolio types
  getPortfolioTypes: async (): Promise<PortfolioTypesResponse> => {
    const response = await portfolioApi.get('/portfolio/types');
    return response.data;
  },

  // Validate URL
  validateUrl: async (
    url: string
  ): Promise<{ is_valid: boolean; artifact_type?: ArtifactType; title?: string }> => {
    const response = await portfolioApi.post('/portfolio/validate-url', { url });
    return response.data;
  },

  // Search portfolio items
  searchPortfolio: async (
    studentId: string,
    query: string
  ): Promise<PortfolioResponse[]> => {
    const response = await portfolioApi.get(
      `/portfolio/student/${studentId}/search?q=${encodeURIComponent(query)}`
    );
    return response.data;
  },

  // Get portfolio items by skill
  getBySkill: async (studentId: string, skillCd: string): Promise<PortfolioResponse[]> => {
    const response = await portfolioApi.get(
      `/portfolio/student/${studentId}/skill/${skillCd}`
    );
    return response.data;
  },

  // Bulk update portfolio items order
  reorderItems: async (
    studentId: string,
    itemIds: string[]
  ): Promise<PortfolioResponse[]> => {
    const response = await portfolioApi.post(`/portfolio/student/${studentId}/reorder`, {
      item_ids: itemIds,
    });
    return response.data;
  },
};
