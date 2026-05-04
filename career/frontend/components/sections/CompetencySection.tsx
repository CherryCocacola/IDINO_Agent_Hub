'use client';

import { BarChart3, TrendingUp, CheckCircle2 } from 'lucide-react';
import { CompetencyBar } from '@/components/ui/ProgressBar';
import type { CompetencyReport, CompetencyScore } from '@/types';

interface CompetencySectionProps {
  report: CompetencyReport | null;
  loading?: boolean;
}

// Default fallback data when API is not available
const defaultScores: CompetencyScore[] = [
  { competency_id: 'C1', competency_nm: '전문지식', score: 82, max_score: 100, percentile: 75, status: 'excellent', color: '#5b6dff' },
  { competency_id: 'C2', competency_nm: '문제해결', score: 68, max_score: 100, percentile: 55, status: 'good', color: '#00b7a8' },
  { competency_id: 'C3', competency_nm: '소통협업', score: 75, max_score: 100, percentile: 65, status: 'good', color: '#ff8a5c' },
  { competency_id: 'C4', competency_nm: '직업윤리', score: 88, max_score: 100, percentile: 85, status: 'excellent', color: '#f6c343' },
];

export default function CompetencySection({ report, loading }: CompetencySectionProps) {
  // Track if we're using real API data or fallback
  const isUsingRealData = report !== null && report.scores && report.scores.length > 0;

  // If no real data, hide the section entirely
  if (!loading && !isUsingRealData) {
    return null;
  }

  const scores = report?.scores || defaultScores;
  // totalScore is SUM (not average)
  const totalScore = report?.total_score || scores.reduce((sum, s) => sum + s.score, 0);
  const percentileRank = report?.percentile_rank || 70;

  if (loading) {
    return (
      <section id="competency" className="section">
        <h2 className="section-title">📈 역량 분석</h2>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-20 bg-gray-100 rounded-lg"></div>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section id="competency" className="section animate-fadeIn">
      <h2 className="section-title">
        <BarChart3 className="w-5 h-5 text-primary" />
        역량 분석
        {isUsingRealData && (
          <span className="ml-2 text-xs font-normal text-green-600 bg-green-50 px-2 py-1 rounded-full">
            실시간 데이터
          </span>
        )}
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Summary */}
        <div className="bg-gradient-to-br from-primary to-primary/80 text-white rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">역량 총점</h3>
          <div className="text-center mb-4">
            <span className="text-5xl font-bold">{totalScore >= 1000 ? totalScore.toLocaleString('ko-KR', { maximumFractionDigits: 0 }) : totalScore.toFixed(1)}</span>
            <span className="text-2xl opacity-80">점</span>
          </div>
          <div className="flex items-center justify-center gap-2 text-sm opacity-90">
            <TrendingUp className="w-4 h-4" />
            <span>상위 {100 - percentileRank}% (동일학과 기준)</span>
          </div>

          <div className="mt-6 pt-4 border-t border-white/20">
            <div className="flex justify-between text-sm mb-2">
              <span>우수 역량</span>
              <span className="font-medium">
                {scores.filter(s => s.status === 'excellent').map(s => s.competency_nm).join(', ') || '없음'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>보완 필요</span>
              <span className="font-medium">
                {scores.filter(s => s.status === 'needs_improvement').map(s => s.competency_nm).join(', ') || '없음'}
              </span>
            </div>
          </div>
        </div>

        {/* Right: Competency Bars */}
        <div className="lg:col-span-2 space-y-2">
          {scores.map((score, index) => (
            <CompetencyBar
              key={index}
              name={score.competency_nm}
              score={score.score}
              maxScore={score.max_score}
              status={score.status}
              percentile={score.percentile}
            />
          ))}
        </div>
      </div>

      {/* AI Recommendations */}
      {report?.recommendations && report.recommendations.length > 0 && (
        <div className="mt-6 p-4 bg-secondary/5 rounded-xl">
          <h3 className="font-semibold text-text mb-3 flex items-center gap-2">
            💡 AI 추천 액션
          </h3>
          <ul className="space-y-2">
            {report.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-text">
                <CheckCircle2 className="w-4 h-4 text-secondary mt-0.5 flex-shrink-0" />
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
