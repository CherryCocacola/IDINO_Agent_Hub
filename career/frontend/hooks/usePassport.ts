'use client';

import { useState, useEffect, useCallback } from 'react';
import { badgeService } from '@/lib/api/badge';
import type {
  StudentBadgeResponse,
  CredentialResponse,
  SkillPassportResponse,
  BadgeCategory,
} from '@/types';

interface PassportState {
  passport: SkillPassportResponse | null;
  badges: StudentBadgeResponse[];
  credentials: CredentialResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: PassportState = {
  passport: null,
  badges: [],
  credentials: [],
  loading: true,
  error: null,
};

export function usePassport(studentId: string | null) {
  const [state, setState] = useState<PassportState>(initialState);

  // Fetch passport data
  const fetchPassport = useCallback(async () => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [passport, badges, credentials] = await Promise.all([
        badgeService.getPassport(studentId),
        badgeService.getStudentBadges(studentId),
        badgeService.getStudentCredentials(studentId),
      ]);

      setState({
        passport,
        badges,
        credentials,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Passport fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '패스포트 데이터를 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId]);

  // Get badges by category
  const getBadgesByCategory = useCallback((category?: BadgeCategory) => {
    if (!category) return state.badges;
    return state.badges.filter(b => b.badge.category === category);
  }, [state.badges]);

  // Get badge details
  const getBadgeDetails = useCallback(async (badgeId: string) => {
    return badgeService.getBadge(badgeId);
  }, []);

  // Get category stats
  const getCategoryStats = useCallback(() => {
    const stats: Record<BadgeCategory, number> = {
      skill: 0,
      achievement: 0,
      course: 0,
      project: 0,
      certification: 0,
      competition: 0,
      community: 0,
    };

    state.badges.forEach(studentBadge => {
      const category = studentBadge.badge.category;
      if (stats[category] !== undefined) {
        stats[category]++;
      }
    });

    return stats;
  }, [state.badges]);

  // Get verified credentials count
  const getVerifiedCredentialsCount = useCallback(() => {
    return state.credentials.filter(c => c.verified).length;
  }, [state.credentials]);

  // Initial fetch
  useEffect(() => {
    fetchPassport();
  }, [fetchPassport]);

  return {
    ...state,
    refetch: fetchPassport,
    getBadgesByCategory,
    getBadgeDetails,
    getCategoryStats,
    getVerifiedCredentialsCount,
  };
}
