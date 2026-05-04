'use client';

import { Users, TrendingUp, TrendingDown, Minus, Award, Lightbulb } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import type { StudentComparison, SuccessPattern } from '@/types';

interface AlumniSectionProps {
  comparison: StudentComparison | null;
  patterns: SuccessPattern[];
  loading?: boolean;
}


const defaultPatterns: SuccessPattern[] = [
  {
    pattern_id: 'P1',
    department_id: 'CS',
    job_category: '소프트웨어 개발자',
    pattern_description: '프로젝트 경험 3회 이상 + 인턴십 1회',
    required_activities: ['교내 프로젝트', '외부 공모전', '인턴십'],
    success_rate: 85,
    sample_size: 45,
  },
  {
    pattern_id: 'P2',
    department_id: 'CS',
    job_category: '데이터 분석가',
    pattern_description: '데이터 관련 자격증 2개 + 분석 프로젝트',
    required_activities: ['빅데이터 분석 자격증', '통계 관련 수업', '캡스톤'],
    success_rate: 78,
    sample_size: 32,
  },
];

export default function AlumniSection({ comparison, patterns, loading }: AlumniSectionProps) {
  const data = comparison;
  const patternData = patterns.length > 0 ? patterns : defaultPatterns;

  if (loading) {
    return (
      <section id="alumni" className="section">
        <h2 className="section-title">👥 졸업생 비교</h2>
        <div className="animate-pulse">
          <div className="h-64 bg-gray-100 rounded-lg"></div>
        </div>
      </section>
    );
  }

  if (!data) {
    return (
      <section id="alumni" className="section animate-fadeIn">
        <h2 className="section-title">
          <Users className="w-5 h-5 text-primary" />
          졸업생 비교
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-50 rounded-xl p-8 text-center text-muted">
            졸업생 비교 데이터를 불러올 수 없습니다.
          </div>
          {/* Still show success patterns even without comparison data */}
          <div className="space-y-4">
            <h3 className="font-semibold text-text flex items-center gap-2">
              <Award className="w-5 h-5 text-ethics" />
              취업 성공 패턴
            </h3>
            {patternData.map((pattern, index) => {
              const activities = pattern.required_activities || (pattern as any).key_activities || [];
              const category = pattern.job_category || (pattern as any).pattern_nm || '';
              const description = pattern.pattern_description || (pattern as any).description || '';
              const rate = typeof pattern.success_rate === 'number' && pattern.success_rate < 1
                ? Math.round(pattern.success_rate * 100) : pattern.success_rate;
              return (
                <div key={index} className="bg-gray-50 rounded-xl p-4">
                  <div className="flex items-start justify-between mb-2">
                    <span className="font-medium text-text">{category}</span>
                    <Badge variant="success">성공률 {rate}%</Badge>
                  </div>
                  <p className="text-sm text-muted mb-3">{description}</p>
                  <div className="flex flex-wrap gap-2">
                    {activities.map((activity: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-white rounded text-xs text-text border border-border">
                        {activity}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-muted mt-2">표본: {pattern.sample_size}명</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    );
  }

  const getTrendIcon = (gap: number) => {
    if (gap > 0) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (gap < 0) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getGapColor = (gap: number) => {
    if (gap > 0) return 'text-green-600';
    if (gap < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <section id="alumni" className="section animate-fadeIn">
      <h2 className="section-title">
        <Users className="w-5 h-5 text-primary" />
        졸업생 비교
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Comparison Table */}
        <div className="bg-gray-50 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="py-3 px-4 text-left font-semibold text-text">항목</th>
                <th className="py-3 px-4 text-center font-semibold text-text">나의 현황</th>
                <th className="py-3 px-4 text-center font-semibold text-text">졸업생 평균</th>
                <th className="py-3 px-4 text-center font-semibold text-text">차이</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-200">
                <td className="py-3 px-4 font-medium">평균학점</td>
                <td className="py-3 px-4 text-center">{(data.student_data?.gpa ?? 0).toFixed(2)}</td>
                <td className="py-3 px-4 text-center">{(data.alumni_average?.gpa ?? 0).toFixed(2)}</td>
                <td className={`py-3 px-4 text-center ${getGapColor(data.gap_analysis?.gpa_gap ?? 0)}`}>
                  <div className="flex items-center justify-center gap-1">
                    {getTrendIcon(data.gap_analysis?.gpa_gap ?? 0)}
                    {(data.gap_analysis?.gpa_gap ?? 0) > 0 ? '+' : ''}{(data.gap_analysis?.gpa_gap ?? 0).toFixed(2)}
                  </div>
                </td>
              </tr>
              <tr className="border-b border-gray-200">
                <td className="py-3 px-4 font-medium">이수학점</td>
                <td className="py-3 px-4 text-center">{data.student_data?.credits ?? 0}</td>
                <td className="py-3 px-4 text-center">{data.alumni_average?.credits ?? 0}</td>
                <td className={`py-3 px-4 text-center ${getGapColor(data.gap_analysis?.credits_gap ?? 0)}`}>
                  <div className="flex items-center justify-center gap-1">
                    {getTrendIcon(data.gap_analysis?.credits_gap ?? 0)}
                    {(data.gap_analysis?.credits_gap ?? 0) > 0 ? '+' : ''}{data.gap_analysis?.credits_gap ?? 0}
                  </div>
                </td>
              </tr>
              <tr className="border-b border-gray-200">
                <td className="py-3 px-4 font-medium">자격증</td>
                <td className="py-3 px-4 text-center">{data.student_data?.certifications ?? 0}개</td>
                <td className="py-3 px-4 text-center">{data.alumni_average?.certifications ?? 0}개</td>
                <td className={`py-3 px-4 text-center ${getGapColor((data.student_data?.certifications ?? 0) - (data.alumni_average?.certifications ?? 0))}`}>
                  <div className="flex items-center justify-center gap-1">
                    {getTrendIcon((data.student_data?.certifications ?? 0) - (data.alumni_average?.certifications ?? 0))}
                    {(data.student_data?.certifications ?? 0) - (data.alumni_average?.certifications ?? 0) > 0 ? '+' : ''}
                    {(data.student_data?.certifications ?? 0) - (data.alumni_average?.certifications ?? 0)}
                  </div>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium">비교과활동</td>
                <td className="py-3 px-4 text-center">{data.student_data?.activities ?? 0}건</td>
                <td className="py-3 px-4 text-center">{data.alumni_average?.activities ?? 0}건</td>
                <td className={`py-3 px-4 text-center ${getGapColor((data.student_data?.activities ?? 0) - (data.alumni_average?.activities ?? 0))}`}>
                  <div className="flex items-center justify-center gap-1">
                    {getTrendIcon((data.student_data?.activities ?? 0) - (data.alumni_average?.activities ?? 0))}
                    {(data.student_data?.activities ?? 0) - (data.alumni_average?.activities ?? 0) > 0 ? '+' : ''}
                    {(data.student_data?.activities ?? 0) - (data.alumni_average?.activities ?? 0)}
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Success Patterns */}
        <div className="space-y-4">
          <h3 className="font-semibold text-text flex items-center gap-2">
            <Award className="w-5 h-5 text-ethics" />
            취업 성공 패턴
          </h3>
          {patternData.map((pattern, index) => {
            const activities = pattern.required_activities || (pattern as any).key_activities || [];
            const category = pattern.job_category || (pattern as any).pattern_nm || '';
            const description = pattern.pattern_description || (pattern as any).description || '';
            const rate = typeof pattern.success_rate === 'number' && pattern.success_rate < 1
              ? Math.round(pattern.success_rate * 100) : pattern.success_rate;
            return (
              <div key={index} className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-start justify-between mb-2">
                  <span className="font-medium text-text">{category}</span>
                  <Badge variant="success">성공률 {rate}%</Badge>
                </div>
                <p className="text-sm text-muted mb-3">{description}</p>
                <div className="flex flex-wrap gap-2">
                  {activities.map((activity: string, i: number) => (
                    <span key={i} className="px-2 py-1 bg-white rounded text-xs text-text border border-border">
                      {activity}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-muted mt-2">
                  표본: {pattern.sample_size}명
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div className="mt-6 p-4 bg-accent/5 rounded-xl">
          <h3 className="font-semibold text-text mb-3 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-accent" />
            개선 권장사항
          </h3>
          <ul className="space-y-2">
            {data.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-text">
                <span className="text-accent">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
