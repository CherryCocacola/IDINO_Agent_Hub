import { integrationApi } from './client';
import type { WorknetJob } from '@/types';

export const integrationService = {
  // Get worknet jobs (optionally filtered by department)
  getJobs: async (departmentNm?: string): Promise<WorknetJob[]> => {
    const params = departmentNm ? { department: departmentNm } : {};
    const response = await integrationApi.get('/integration/worknet/jobs', { params });
    return response.data;
  },

  // Get specific job by code
  getJob: async (jobCode: string): Promise<WorknetJob> => {
    const response = await integrationApi.get(`/integration/worknet/jobs/${jobCode}`);
    return response.data;
  },

  // Search jobs
  searchJobs: async (query: string): Promise<WorknetJob[]> => {
    const response = await integrationApi.get('/integration/worknet/search', {
      params: { query },
    });
    return response.data;
  },

  // Get HRD alumni data
  getHRDAlumni: async (params?: { department_id?: string; graduation_year?: number; limit?: number }) => {
    const response = await integrationApi.get('/integration/hrd/alumni', { params });
    return response.data;
  },

  // Get university student data
  getUniversityStudent: async (studentId: string) => {
    const response = await integrationApi.get(`/integration/university/student/${studentId}`);
    return response.data;
  },
};
