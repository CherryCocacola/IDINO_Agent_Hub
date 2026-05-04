'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  RefreshCw,
  Filter,
  Bell,
  BellOff,
  TrendingUp,
  BookOpen,
  UserX,
  Award,
  Briefcase,
  Code,
} from 'lucide-react';
import { riskService } from '@/lib/api/risk';
import type {
  RiskAlertResponse,
  StudentRiskProfile,
  RiskCategory,
  RiskSeverity,
  AlertStatus,
  SEVERITY_COLORS,
  SEVERITY_LABELS,
  CATEGORY_LABELS,
} from '@/types';

interface RiskAlertsSectionProps {
  studentId: string;
}

const severityColors: Record<RiskSeverity, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
};

const severityLabels: Record<RiskSeverity, string> = {
  low: '낮음',
  medium: '보통',
  high: '높음',
  critical: '심각',
};

const categoryLabels: Record<RiskCategory, string> = {
  gpa: 'GPA 위험도',
  credits: '학점이수 위험도',
  attendance: '출석 위험도',
  prerequisite: '선수과목 위험도',
  graduation: '졸업요건 위험도',
  career: '진로준비 위험도',
  skill_gap: '스킬갭 위험도',
};

const categoryIcons: Record<RiskCategory, React.ReactNode> = {
  gpa: <TrendingUp className="w-4 h-4" />,
  credits: <BookOpen className="w-4 h-4" />,
  attendance: <UserX className="w-4 h-4" />,
  prerequisite: <BookOpen className="w-4 h-4" />,
  graduation: <Award className="w-4 h-4" />,
  career: <Briefcase className="w-4 h-4" />,
  skill_gap: <Code className="w-4 h-4" />,
};

const statusLabels: Record<AlertStatus, string> = {
  active: '활성',
  acknowledged: '확인됨',
  resolved: '해결됨',
  dismissed: '무시됨',
};

export default function RiskAlertsSection({ studentId }: RiskAlertsSectionProps) {
  const [alerts, setAlerts] = useState<RiskAlertResponse[]>([]);
  const [profile, setProfile] = useState<StudentRiskProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterCategory, setFilterCategory] = useState<RiskCategory | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<AlertStatus | 'all'>('active');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch alerts and profile
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [alertsData, profileData] = await Promise.all([
        riskService.getStudentAlerts(
          studentId,
          filterStatus !== 'all' ? filterStatus : undefined,
          filterCategory !== 'all' ? filterCategory : undefined
        ),
        riskService.getRiskProfile(studentId).catch(() => null),
      ]);
      setAlerts(alertsData);
      if (profileData) setProfile(profileData);
    } catch (err) {
      setError('위험 알림을 불러오는데 실패했습니다.');
      console.error('Failed to fetch risk data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [studentId, filterCategory, filterStatus]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const newProfile = await riskService.refreshRiskProfile(studentId);
      setProfile(newProfile);
      await fetchData();
    } catch (err) {
      console.error('Failed to refresh:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      const updated = await riskService.acknowledgeAlert(alertId);
      setAlerts((prev) => prev.map((a) => (a.alert_id === alertId ? updated : a)));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolve = async (alertId: string) => {
    const note = prompt('해결 메모를 입력하세요 (선택):');
    try {
      const updated = await riskService.resolveAlert(alertId, note || undefined);
      setAlerts((prev) => prev.map((a) => (a.alert_id === alertId ? updated : a)));
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleDismiss = async (alertId: string) => {
    if (!confirm('이 알림을 무시하시겠습니까?')) return;
    try {
      const updated = await riskService.dismissAlert(alertId);
      setAlerts((prev) => prev.map((a) => (a.alert_id === alertId ? updated : a)));
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  // Risk level indicator color
  const getRiskLevelColor = (score: number): string => {
    if (score >= 70) return 'text-red-600';
    if (score >= 50) return 'text-orange-500';
    if (score >= 30) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <div className="space-y-6">
      {/* Risk Profile Summary */}
      {profile && (
        <div className="bg-card rounded-xl p-6 border border-border">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-text">위험 프로필</h3>
                <p className="text-xs text-muted">
                  마지막 분석: {new Date(profile.last_analyzed_at).toLocaleString('ko-KR')}
                </p>
              </div>
            </div>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2 px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-hover disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              새로 분석
            </button>
          </div>

          {/* Overall Score */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-sm text-muted mb-1">종합 위험 점수</p>
              <p className={`text-3xl font-bold ${getRiskLevelColor(profile.overall_risk_score)}`}>
                {profile.overall_risk_score}
              </p>
              <p className={`text-sm ${severityColors[profile.risk_level].text}`}>
                {severityLabels[profile.risk_level]}
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-sm text-muted mb-1">활성 알림</p>
              <p className="text-3xl font-bold text-text">{profile.total_active_alerts}</p>
              <p className="text-sm text-muted">총 알림</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-sm text-muted mb-1">심각 알림</p>
              <p className="text-3xl font-bold text-red-600">{profile.critical_alerts}</p>
              <p className="text-sm text-muted">심각</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <p className="text-sm text-muted mb-1">높음 알림</p>
              <p className="text-3xl font-bold text-orange-500">{profile.high_alerts}</p>
              <p className="text-sm text-muted">높음</p>
            </div>
          </div>

          {/* Category Risk Scores */}
          <div className="mb-2">
            <p className="text-xs text-muted">* 위험도 점수: 0(안전) ~ 100(위험). 실제 학점/이수학점이 아닌, 분석된 위험 수준입니다.</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {[
              { key: 'gpa', score: profile.gpa_risk_score },
              { key: 'credits', score: profile.credits_risk_score },
              { key: 'prerequisite', score: profile.prerequisite_risk_score },
              { key: 'graduation', score: profile.graduation_risk_score },
              { key: 'career', score: profile.career_risk_score },
            ].map(({ key, score }) => (
              <div key={key} className="bg-white border border-border rounded-lg p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`${getRiskLevelColor(score)}`}>
                    {categoryIcons[key as RiskCategory]}
                  </span>
                  <span className="text-xs text-muted">{categoryLabels[key as RiskCategory]}</span>
                </div>
                <p className={`text-lg font-bold ${getRiskLevelColor(score)}`}>{score}<span className="text-xs font-normal text-muted">/100</span></p>
                <div className="h-1.5 bg-gray-200 rounded-full mt-1 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      score >= 70
                        ? 'bg-red-500'
                        : score >= 50
                        ? 'bg-orange-500'
                        : score >= 30
                        ? 'bg-yellow-500'
                        : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(score, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Top Recommendations */}
          {profile.recommendations.length > 0 && (
            <div className="mt-6">
              <h4 className="font-medium text-text mb-3">권장 조치</h4>
              <div className="space-y-2">
                {profile.recommendations.slice(0, 3).map((rec, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200"
                  >
                    <span className="w-6 h-6 flex items-center justify-center bg-blue-500 text-white text-sm rounded-full flex-shrink-0">
                      {rec.priority}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-blue-800">{rec.action}</p>
                      <p className="text-xs text-blue-600 mt-1">{rec.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="bg-card rounded-xl p-4 border border-border">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-muted" />
            <span className="text-sm text-muted">필터:</span>
          </div>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value as RiskCategory | 'all')}
            className="px-3 py-1.5 text-sm border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">모든 카테고리</option>
            {Object.entries(categoryLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as AlertStatus | 'all')}
            className="px-3 py-1.5 text-sm border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="all">모든 상태</option>
            {Object.entries(statusLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-card rounded-xl p-6 border border-border">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-text">알림 목록</h3>
          <span className="text-sm text-muted">{alerts.length}개 알림</span>
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {/* Error */}
        {error && !isLoading && (
          <div className="text-center py-12 text-red-500">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
            <p>{error}</p>
            <button
              onClick={fetchData}
              className="mt-2 px-4 py-1 text-sm bg-red-100 rounded-lg hover:bg-red-200"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* Alerts */}
        {!isLoading && !error && (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.alert_id}
                className={`p-4 rounded-lg border ${severityColors[alert.severity].bg} ${severityColors[alert.severity].border}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${severityColors[alert.severity].bg} ${severityColors[alert.severity].text}`}>
                      {categoryIcons[alert.category]}
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium text-text">{alert.title}</h4>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${severityColors[alert.severity].bg} ${severityColors[alert.severity].text} border ${severityColors[alert.severity].border}`}>
                          {severityLabels[alert.severity]}
                        </span>
                        <span className="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">
                          {categoryLabels[alert.category]}
                        </span>
                        {alert.status !== 'active' && (
                          <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-600">
                            {statusLabels[alert.status]}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted">{alert.description}</p>
                      {alert.recommendation && (
                        <p className="text-sm text-text mt-2 p-2 bg-white/50 rounded-lg">
                          💡 {alert.recommendation}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-muted">
                        <span>생성: {new Date(alert.created_at).toLocaleDateString('ko-KR')}</span>
                        {alert.due_date && (
                          <span className="text-red-500">
                            기한: {new Date(alert.due_date).toLocaleDateString('ko-KR')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  {alert.status === 'active' && (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleAcknowledge(alert.alert_id)}
                        className="p-2 hover:bg-white/50 rounded-lg transition-colors"
                        title="확인"
                      >
                        <Eye className="w-4 h-4 text-blue-500" />
                      </button>
                      <button
                        onClick={() => handleResolve(alert.alert_id)}
                        className="p-2 hover:bg-white/50 rounded-lg transition-colors"
                        title="해결"
                      >
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      </button>
                      <button
                        onClick={() => handleDismiss(alert.alert_id)}
                        className="p-2 hover:bg-white/50 rounded-lg transition-colors"
                        title="무시"
                      >
                        <BellOff className="w-4 h-4 text-gray-400" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {alerts.length === 0 && (
              <div className="text-center py-12">
                <Bell className="w-12 h-12 text-muted mx-auto mb-3" />
                <p className="text-muted">
                  {filterCategory !== 'all' || filterStatus !== 'all'
                    ? '해당 조건의 알림이 없습니다.'
                    : '활성 알림이 없습니다. 잘 하고 있어요!'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
