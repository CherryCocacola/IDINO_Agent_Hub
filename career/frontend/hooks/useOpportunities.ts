'use client';

import { useState, useEffect, useCallback } from 'react';
import { opportunityService } from '@/lib/api/opportunity';
import type {
  OpportunityResponse,
  OpportunityListResponse,
  RecommendationResponse,
  ApplicationResponse,
  ApplicationCreate,
  ApplicationUpdate,
  OpportunityType,
  OpportunitySearchRequest,
} from '@/types';

interface OpportunitiesState {
  opportunities: OpportunityResponse[];
  recommendations: RecommendationResponse | null;
  applications: ApplicationResponse[];
  total: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
}

const initialState: OpportunitiesState = {
  opportunities: [],
  recommendations: null,
  applications: [],
  total: 0,
  page: 1,
  pageSize: 20,
  loading: true,
  error: null,
};

export function useOpportunities(studentId: string | null) {
  const [state, setState] = useState<OpportunitiesState>(initialState);

  // Fetch opportunities list
  const fetchOpportunities = useCallback(async (page = 1, pageSize = 20) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await opportunityService.getOpportunities(page, pageSize);
      setState(prev => ({
        ...prev,
        opportunities: data.opportunities,
        total: data.total_count,
        page: data.page,
        pageSize: data.page_size,
        loading: false,
      }));
    } catch (error) {
      console.error('Opportunities fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '기회 목록을 불러오는데 실패했습니다.',
      }));
    }
  }, []);

  // Fetch opportunities by type
  const fetchByType = useCallback(async (type: OpportunityType, page = 1, pageSize = 20) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await opportunityService.getOpportunitiesByType(type, page, pageSize);
      setState(prev => ({
        ...prev,
        opportunities: data.opportunities,
        total: data.total_count,
        page: data.page,
        pageSize: data.page_size,
        loading: false,
      }));
    } catch (error) {
      console.error('Opportunities by type fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '기회 목록을 불러오는데 실패했습니다.',
      }));
    }
  }, []);

  // Search opportunities
  const searchOpportunities = useCallback(async (params: OpportunitySearchRequest) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await opportunityService.searchOpportunities(params);
      setState(prev => ({
        ...prev,
        opportunities: data.opportunities,
        total: data.total_count,
        page: data.page,
        pageSize: data.page_size,
        loading: false,
      }));
    } catch (error) {
      console.error('Search error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '검색에 실패했습니다.',
      }));
    }
  }, []);

  // Fetch recommendations
  const fetchRecommendations = useCallback(async (maxResults = 20) => {
    if (!studentId) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const recommendations = await opportunityService.getRecommendations(studentId, {
        max_results: maxResults,
      });
      setState(prev => ({
        ...prev,
        recommendations,
        loading: false,
      }));
    } catch (error) {
      console.error('Recommendations fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '추천을 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Fetch student applications
  const fetchApplications = useCallback(async (status?: string) => {
    if (!studentId) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const applications = await opportunityService.getStudentApplications(studentId, status);
      setState(prev => ({
        ...prev,
        applications,
        loading: false,
      }));
    } catch (error) {
      console.error('Applications fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '지원 목록을 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Create application
  const createApplication = useCallback(async (data: ApplicationCreate) => {
    const application = await opportunityService.createApplication(data);
    setState(prev => ({
      ...prev,
      applications: [...prev.applications, application],
    }));
    return application;
  }, []);

  // Update application
  const updateApplication = useCallback(async (applicationId: string, data: ApplicationUpdate) => {
    const updated = await opportunityService.updateApplication(applicationId, data);
    setState(prev => ({
      ...prev,
      applications: prev.applications.map(a =>
        a.application_id === applicationId ? updated : a
      ),
    }));
    return updated;
  }, []);

  // Withdraw application
  const withdrawApplication = useCallback(async (applicationId: string) => {
    const withdrawn = await opportunityService.withdrawApplication(applicationId);
    setState(prev => ({
      ...prev,
      applications: prev.applications.map(a =>
        a.application_id === applicationId ? withdrawn : a
      ),
    }));
    return withdrawn;
  }, []);

  // Get upcoming deadlines
  const getUpcomingDeadlines = useCallback(async (days = 30) => {
    if (!studentId) return [];
    return opportunityService.getUpcomingDeadlines(studentId, days);
  }, [studentId]);

  // Initial fetch
  useEffect(() => {
    fetchOpportunities();
    if (studentId) {
      fetchApplications();
    }
  }, [fetchOpportunities, fetchApplications, studentId]);

  return {
    ...state,
    refetch: fetchOpportunities,
    fetchByType,
    searchOpportunities,
    fetchRecommendations,
    fetchApplications,
    createApplication,
    updateApplication,
    withdrawApplication,
    getUpcomingDeadlines,
  };
}
