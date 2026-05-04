'use client';

import { useState, useEffect, useCallback } from 'react';
import { portfolioService } from '@/lib/api/portfolio';
import type {
  PortfolioResponse,
  PortfolioListResponse,
  PortfolioCreate,
  PortfolioUpdate,
  PortfolioSummaryResponse,
  ArtifactType,
} from '@/types';

interface PortfolioState {
  items: PortfolioResponse[];
  totalCount: number;
  primaryItem: PortfolioResponse | null;
  summary: PortfolioSummaryResponse | null;
  loading: boolean;
  error: string | null;
}

const initialState: PortfolioState = {
  items: [],
  totalCount: 0,
  primaryItem: null,
  summary: null,
  loading: true,
  error: null,
};

export function usePortfolio(studentId: string | null) {
  const [state, setState] = useState<PortfolioState>(initialState);

  // Fetch portfolio items
  const fetchPortfolio = useCallback(async () => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [portfolioData, primaryItem, summary] = await Promise.all([
        portfolioService.getStudentPortfolio(studentId),
        portfolioService.getPrimaryItem(studentId),
        portfolioService.getPortfolioSummary(studentId),
      ]);

      setState({
        items: portfolioData.items,
        totalCount: portfolioData.total_count,
        primaryItem,
        summary,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Portfolio fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '포트폴리오를 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Create portfolio item
  const createItem = useCallback(async (data: PortfolioCreate) => {
    const item = await portfolioService.createPortfolioItem(data);
    setState(prev => ({
      ...prev,
      items: [...prev.items, item],
      totalCount: prev.totalCount + 1,
    }));
    return item;
  }, []);

  // Update portfolio item
  const updateItem = useCallback(async (portfolioId: string, data: PortfolioUpdate) => {
    const updated = await portfolioService.updatePortfolioItem(portfolioId, data);
    setState(prev => ({
      ...prev,
      items: prev.items.map(item => item.portfolio_id === portfolioId ? updated : item),
      primaryItem: prev.primaryItem?.portfolio_id === portfolioId ? updated : prev.primaryItem,
    }));
    return updated;
  }, []);

  // Delete portfolio item
  const deleteItem = useCallback(async (portfolioId: string) => {
    await portfolioService.deletePortfolioItem(portfolioId);
    setState(prev => ({
      ...prev,
      items: prev.items.filter(item => item.portfolio_id !== portfolioId),
      totalCount: prev.totalCount - 1,
      primaryItem: prev.primaryItem?.portfolio_id === portfolioId ? null : prev.primaryItem,
    }));
  }, []);

  // Set primary item
  const setPrimaryItem = useCallback(async (portfolioId: string) => {
    const updated = await portfolioService.setPrimaryItem(portfolioId);
    setState(prev => ({
      ...prev,
      items: prev.items.map(item => ({
        ...item,
        is_primary: item.portfolio_id === portfolioId,
      })),
      primaryItem: updated,
    }));
    return updated;
  }, []);

  // Get items by type
  const getByType = useCallback(async (type: ArtifactType) => {
    if (!studentId) return [];
    return portfolioService.getByType(studentId, type);
  }, [studentId]);

  // Search items
  const searchItems = useCallback(async (query: string) => {
    if (!studentId) return [];
    return portfolioService.searchPortfolio(studentId, query);
  }, [studentId]);

  // Validate URL
  const validateUrl = useCallback(async (url: string) => {
    return portfolioService.validateUrl(url);
  }, []);

  // Reorder items
  const reorderItems = useCallback(async (itemIds: string[]) => {
    if (!studentId) return [];
    const reordered = await portfolioService.reorderItems(studentId, itemIds);
    setState(prev => ({
      ...prev,
      items: reordered,
    }));
    return reordered;
  }, [studentId]);

  // Initial fetch
  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  return {
    ...state,
    refetch: fetchPortfolio,
    createItem,
    updateItem,
    deleteItem,
    setPrimaryItem,
    getByType,
    searchItems,
    validateUrl,
    reorderItems,
  };
}
