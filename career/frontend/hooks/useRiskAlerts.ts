'use client';

import { useState, useEffect, useCallback } from 'react';
import { riskService } from '@/lib/api/risk';
import type {
  RiskAlertResponse,
  StudentRiskProfile,
  RiskCategory,
  AlertStatus,
  ConstraintCheckResponse,
} from '@/types';

interface RiskAlertsState {
  alerts: RiskAlertResponse[];
  profile: StudentRiskProfile | null;
  constraints: ConstraintCheckResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: RiskAlertsState = {
  alerts: [],
  profile: null,
  constraints: [],
  loading: true,
  error: null,
};

export function useRiskAlerts(
  studentId: string | null,
  filterStatus?: AlertStatus,
  filterCategory?: RiskCategory
) {
  const [state, setState] = useState<RiskAlertsState>(initialState);

  // Fetch alerts and profile
  const fetchData = useCallback(async () => {
    if (!studentId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [alerts, profile, constraints] = await Promise.all([
        riskService.getStudentAlerts(studentId, filterStatus, filterCategory),
        riskService.getRiskProfile(studentId),
        riskService.getConstraintChecks(studentId),
      ]);

      setState({
        alerts,
        profile,
        constraints,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Risk alerts fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '위험 알림을 불러오는데 실패했습니다.',
      }));
    }
  }, [studentId, filterStatus, filterCategory]);

  // Acknowledge alert
  const acknowledgeAlert = useCallback(async (alertId: string) => {
    const updated = await riskService.acknowledgeAlert(alertId);
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(a => a.alert_id === alertId ? updated : a),
    }));
    return updated;
  }, []);

  // Resolve alert
  const resolveAlert = useCallback(async (alertId: string, resolutionNote?: string) => {
    const updated = await riskService.resolveAlert(alertId, resolutionNote);
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(a => a.alert_id === alertId ? updated : a),
    }));
    return updated;
  }, []);

  // Dismiss alert
  const dismissAlert = useCallback(async (alertId: string) => {
    const updated = await riskService.dismissAlert(alertId);
    setState(prev => ({
      ...prev,
      alerts: prev.alerts.map(a => a.alert_id === alertId ? updated : a),
    }));
    return updated;
  }, []);

  // Refresh profile
  const refreshProfile = useCallback(async () => {
    if (!studentId) return null;
    const profile = await riskService.refreshRiskProfile(studentId);
    setState(prev => ({ ...prev, profile }));
    return profile;
  }, [studentId]);

  // Get risk summary
  const getRiskSummary = useCallback(async () => {
    if (!studentId) return null;
    return riskService.getRiskSummary(studentId);
  }, [studentId]);

  // Check prerequisites
  const checkPrerequisites = useCallback(async (courseCd: string) => {
    if (!studentId) return null;
    return riskService.checkPrerequisites(studentId, courseCd);
  }, [studentId]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    ...state,
    refetch: fetchData,
    acknowledgeAlert,
    resolveAlert,
    dismissAlert,
    refreshProfile,
    getRiskSummary,
    checkPrerequisites,
  };
}
