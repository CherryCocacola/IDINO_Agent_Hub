'use client';

import { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, CheckCircle, Target, ChevronDown, ChevronUp } from 'lucide-react';
import { skillService } from '@/lib/api/skill';
import ProgressBar from '@/components/ui/ProgressBar';
import type { GapAnalysisResponse, SkillGapItem } from '@/types';

interface SkillGapSectionProps {
  studentId: string;
  selectedRole: string;
  onRoleChange: (role: string) => void;
}

interface Role {
  role_cd: string;
  role_nm: string;
  industry?: string;
}

// Gap priority color
const getPriorityColor = (importance: string): string => {
  switch (importance) {
    case 'critical': return 'bg-red-100 text-red-700 border-red-200';
    case 'important': return 'bg-amber-100 text-amber-700 border-amber-200';
    case 'nice_to_have': return 'bg-green-100 text-green-700 border-green-200';
    default: return 'bg-gray-100 text-gray-700 border-gray-200';
  }
};

// Gap bar color
const getGapBarColor = (gap: number): string => {
  if (gap >= 3) return 'bg-red-500';
  if (gap >= 2) return 'bg-amber-500';
  if (gap >= 1) return 'bg-yellow-500';
  return 'bg-green-500';
};

const importanceLabels: Record<string, string> = {
  critical: '필수',
  important: '중요',
  nice_to_have: '권장',
};

export default function SkillGapSection({
  studentId,
  selectedRole,
  onRoleChange,
}: SkillGapSectionProps) {
  const [gapData, setGapData] = useState<GapAnalysisResponse | null>(null);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);

  // Fetch roles
  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const data = await skillService.getRoles();
        setRoles(data);
        if (!selectedRole && data.length > 0) {
          onRoleChange(data[0].role_cd);
        }
      } catch (err) {
        console.error('Failed to fetch roles:', err);
      }
    };
    fetchRoles();
  }, []);

  // Fetch gap analysis
  useEffect(() => {
    const fetchGapAnalysis = async () => {
      if (!selectedRole) return;
      setIsLoading(true);
      setError(null);
      try {
        const data = await skillService.getGapAnalysis(studentId, selectedRole);
        setGapData(data);
      } catch (err) {
        setError('갭 분석을 불러오는데 실패했습니다.');
        console.error('Failed to fetch gap analysis:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchGapAnalysis();
  }, [studentId, selectedRole]);

  const toggleSkill = (skillCd: string) => {
    setExpandedSkill(expandedSkill === skillCd ? null : skillCd);
  };

  return (
    <div className="space-y-6">
      {/* Header with Role Selector */}
      <div className="bg-card rounded-xl p-6 border border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100">
              <TrendingUp className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold text-text">스킬 갭 분석</h3>
              <p className="text-xs text-muted">목표 역할 대비 현재 스킬 수준을 분석합니다</p>
            </div>
          </div>

          <select
            value={selectedRole}
            onChange={(e) => onRoleChange(e.target.value)}
            className="px-4 py-2 border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">목표 역할 선택</option>
            {roles.map((role) => (
              <option key={role.role_cd} value={role.role_cd}>
                {role.role_nm}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="bg-card rounded-xl p-12 border border-border">
          <div className="text-center">
            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-muted">갭 분석 중...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 rounded-xl p-6 border border-red-200 text-red-600">
          <p>{error}</p>
        </div>
      )}

      {/* Gap Analysis Results */}
      {gapData && !isLoading && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-card rounded-xl p-4 border border-border">
              <div className="flex items-center gap-2 text-muted text-sm mb-2">
                <Target className="w-4 h-4" />
                <span>목표 역할</span>
              </div>
              <p className="text-lg font-semibold text-text">{gapData.target_role_nm || selectedRole}</p>
            </div>

            <div className="bg-card rounded-xl p-4 border border-border">
              <div className="flex items-center gap-2 text-muted text-sm mb-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>준비도</span>
              </div>
              <p className="text-2xl font-bold text-green-600">{gapData.readiness_percentage}%</p>
            </div>

            <div className="bg-card rounded-xl p-4 border border-border">
              <div className="flex items-center gap-2 text-muted text-sm mb-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                <span>갭 점수</span>
              </div>
              <p className="text-2xl font-bold text-amber-600">{gapData.overall_gap_score}</p>
            </div>

            <div className="bg-card rounded-xl p-4 border border-border">
              <div className="flex items-center gap-2 text-muted text-sm mb-2">
                <TrendingUp className="w-4 h-4 text-blue-500" />
                <span>개선 필요 스킬</span>
              </div>
              <p className="text-2xl font-bold text-blue-600">
                {gapData.skill_gaps.filter(g => g.gap > 0).length}개
              </p>
            </div>
          </div>

          {/* Readiness Progress Bar */}
          <div className="bg-card rounded-xl p-6 border border-border">
            <h4 className="font-semibold text-text mb-4">전체 준비도</h4>
            <div className="space-y-2">
              <ProgressBar label="준비도" value={gapData.readiness_percentage} color="bg-primary" />
              <p className="text-sm text-muted">{gapData.summary}</p>
            </div>
          </div>

          {/* Strengths & Top Priority */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Strengths */}
            <div className="bg-card rounded-xl p-6 border border-border">
              <h4 className="font-semibold text-text mb-4 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                강점 스킬
              </h4>
              <div className="flex flex-wrap gap-2">
                {gapData.strengths.length > 0 ? (
                  gapData.strengths.map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))
                ) : (
                  <p className="text-muted text-sm">아직 분석된 강점 스킬이 없습니다</p>
                )}
              </div>
            </div>

            {/* Top Priority */}
            <div className="bg-card rounded-xl p-6 border border-border">
              <h4 className="font-semibold text-text mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                우선 개발 스킬
              </h4>
              <div className="flex flex-wrap gap-2">
                {gapData.top_priority_skills.length > 0 ? (
                  gapData.top_priority_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="px-3 py-1.5 bg-red-100 text-red-700 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))
                ) : (
                  <p className="text-muted text-sm">우선 개발이 필요한 스킬이 없습니다</p>
                )}
              </div>
            </div>
          </div>

          {/* Skill Gap Details */}
          <div className="bg-card rounded-xl p-6 border border-border">
            <h4 className="font-semibold text-text mb-4">스킬별 갭 상세</h4>

            <div className="space-y-3">
              {gapData.skill_gaps.map((skill) => (
                <div
                  key={skill.skill_cd}
                  className="border border-border rounded-lg overflow-hidden"
                >
                  {/* Skill Row */}
                  <div
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
                    onClick={() => toggleSkill(skill.skill_cd)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-muted">#{skill.priority_rank}</span>
                      <span className="font-medium text-text">{skill.skill_nm}</span>
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full border ${getPriorityColor(skill.importance)}`}
                      >
                        {importanceLabels[skill.importance] || skill.importance}
                      </span>
                    </div>

                    <div className="flex items-center gap-4">
                      {/* Level Indicator */}
                      <div className="text-sm">
                        <span className="text-muted">Lv.</span>
                        <span className="font-semibold text-text">{skill.current_level}</span>
                        <span className="text-muted mx-1">→</span>
                        <span className="font-semibold text-primary">{skill.required_level}</span>
                      </div>

                      {/* Gap Bar */}
                      <div className="w-32">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-muted">Gap</span>
                          <span className={skill.gap > 0 ? 'text-red-500' : 'text-green-500'}>
                            {skill.gap > 0 ? `+${skill.gap}` : '달성'}
                          </span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${getGapBarColor(skill.gap)} rounded-full transition-all`}
                            style={{ width: `${Math.min((skill.gap / 5) * 100, 100)}%` }}
                          />
                        </div>
                      </div>

                      {/* Expand Icon */}
                      {skill.recommended_actions && skill.recommended_actions.length > 0 && (
                        expandedSkill === skill.skill_cd ? (
                          <ChevronUp className="w-5 h-5 text-muted" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-muted" />
                        )
                      )}
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {expandedSkill === skill.skill_cd && skill.recommended_actions && (
                    <div className="px-4 pb-4 bg-gray-50 border-t border-border">
                      <p className="text-sm text-muted mb-2 pt-3">권장 학습 활동:</p>
                      <ul className="space-y-2">
                        {skill.recommended_actions.map((action, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="w-5 h-5 flex items-center justify-center bg-primary/10 text-primary rounded-full text-xs flex-shrink-0 mt-0.5">
                              {i + 1}
                            </span>
                            <span className="text-sm text-text">{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}

              {gapData.skill_gaps.length === 0 && (
                <div className="text-center py-8 text-muted">
                  갭 분석 결과가 없습니다. 목표 역할을 선택해주세요.
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!gapData && !isLoading && !error && (
        <div className="bg-card rounded-xl p-12 border border-border text-center">
          <Target className="w-12 h-12 text-muted mx-auto mb-3" />
          <p className="text-muted">목표 역할을 선택하면 갭 분석 결과를 확인할 수 있습니다.</p>
        </div>
      )}
    </div>
  );
}
