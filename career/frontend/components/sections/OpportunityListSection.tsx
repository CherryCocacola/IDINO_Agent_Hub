'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  Star,
  Calendar,
  MapPin,
  ExternalLink,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Building,
  Trophy,
  Award,
  BookOpen,
  Clock,
  Check,
  X,
  Users,
} from 'lucide-react';
import { opportunityService } from '@/lib/api/opportunity';
import Badge from '@/components/ui/Badge';
import type {
  OpportunityResponse,
  ApplicationResponse,
  RecommendationResponse,
  OpportunityType,
  ApplicationCreate,
} from '@/types';

interface OpportunityListSectionProps {
  studentId: string;
  viewMode: 'all' | 'recommended' | 'applications';
}

const typeLabels: Record<OpportunityType, string> = {
  internship: '인턴십',
  competition: '공모전',
  research: '연구참여',
  extracurricular: '대외활동',
  scholarship: '장학금',
  certification: '자격증',
  mentoring: '멘토링',
  project: '프로젝트',
};

const typeIcons: Record<OpportunityType, React.ReactNode> = {
  internship: <Briefcase className="w-4 h-4" />,
  competition: <Trophy className="w-4 h-4" />,
  research: <BookOpen className="w-4 h-4" />,
  extracurricular: <Star className="w-4 h-4" />,
  scholarship: <BookOpen className="w-4 h-4" />,
  certification: <Award className="w-4 h-4" />,
  mentoring: <Users className="w-4 h-4" />,
  project: <Briefcase className="w-4 h-4" />,
};

const typeColors: Record<OpportunityType, string> = {
  internship: 'bg-blue-100 text-blue-700',
  competition: 'bg-purple-100 text-purple-700',
  research: 'bg-teal-100 text-teal-700',
  extracurricular: 'bg-pink-100 text-pink-700',
  scholarship: 'bg-amber-100 text-amber-700',
  certification: 'bg-green-100 text-green-700',
  mentoring: 'bg-indigo-100 text-indigo-700',
  project: 'bg-gray-100 text-gray-700',
};

const applicationStatusLabels: Record<string, { label: string; color: string }> = {
  interested: { label: '관심', color: 'bg-blue-100 text-blue-700' },
  applied: { label: '지원완료', color: 'bg-purple-100 text-purple-700' },
  in_progress: { label: '진행중', color: 'bg-amber-100 text-amber-700' },
  accepted: { label: '합격', color: 'bg-green-100 text-green-700' },
  rejected: { label: '불합격', color: 'bg-red-100 text-red-700' },
  withdrawn: { label: '철회', color: 'bg-gray-100 text-gray-700' },
};

export default function OpportunityListSection({
  studentId,
  viewMode,
}: OpportunityListSectionProps) {
  const [opportunities, setOpportunities] = useState<OpportunityResponse[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<OpportunityType | 'all'>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedOpportunity, setSelectedOpportunity] = useState<OpportunityResponse | null>(null);

  // Fetch data based on view mode
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (viewMode === 'recommended') {
        const data = await opportunityService.getRecommendations(studentId, {
          max_results: 20,
        });
        setRecommendations(data);
      } else if (viewMode === 'applications') {
        const data = await opportunityService.getStudentApplications(studentId);
        setApplications(data);
      } else {
        if (filterType !== 'all') {
          const data = await opportunityService.getOpportunitiesByType(filterType, page, 20);
          setOpportunities(data.opportunities);
          setTotalPages(Math.ceil(data.total_count / data.page_size));
        } else {
          const data = await opportunityService.getOpportunities(page, 20);
          setOpportunities(data.opportunities);
          setTotalPages(Math.ceil(data.total_count / data.page_size));
        }
      }
    } catch (err) {
      setError('데이터를 불러오는데 실패했습니다.');
      console.error('Failed to fetch data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [studentId, viewMode, filterType, page]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle apply/interest
  const handleApply = async (opportunity: OpportunityResponse) => {
    try {
      const application: ApplicationCreate = {
        student_id: studentId,
        opportunity_id: opportunity.opportunity_id,
        status: 'interested',
      };
      await opportunityService.createApplication(application);
      alert('관심 목록에 추가되었습니다!');
      if (viewMode === 'applications') {
        fetchData();
      }
    } catch (err) {
      console.error('Failed to apply:', err);
      alert('관심 등록에 실패했습니다.');
    }
  };

  // Handle withdraw
  const handleWithdraw = async (applicationId: string) => {
    if (!confirm('지원을 철회하시겠습니까?')) return;
    try {
      await opportunityService.withdrawApplication(applicationId);
      fetchData();
    } catch (err) {
      console.error('Failed to withdraw:', err);
      alert('철회에 실패했습니다.');
    }
  };

  // Filter opportunities by search
  const filteredOpportunities = opportunities.filter((opp) =>
    searchQuery
      ? opp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        opp.organization?.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  );

  // Days until deadline
  const getDaysUntilDeadline = (deadline?: string): string => {
    if (!deadline) return '';
    const days = Math.ceil(
      (new Date(deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
    );
    if (days < 0) return '마감';
    if (days === 0) return 'D-Day';
    if (days <= 7) return `D-${days}`;
    return `${days}일 남음`;
  };

  const renderOpportunityCard = (opportunity: OpportunityResponse, matchScore?: number, reason?: string) => (
    <div
      key={opportunity.opportunity_id}
      className="bg-card rounded-xl p-5 border border-border hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => setSelectedOpportunity(opportunity)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`p-2 rounded-lg ${typeColors[opportunity.opportunity_type]}`}>
            {typeIcons[opportunity.opportunity_type]}
          </span>
          <span className={`px-2 py-0.5 text-xs rounded-full ${typeColors[opportunity.opportunity_type]}`}>
            {typeLabels[opportunity.opportunity_type]}
          </span>
        </div>
        {matchScore !== undefined && (
          <div className="flex items-center gap-1 px-2 py-1 bg-primary/10 rounded-full">
            <Star className="w-3 h-3 text-primary fill-primary" />
            <span className="text-xs font-medium text-primary">{Math.round(matchScore)}%</span>
          </div>
        )}
      </div>

      <h4 className="font-semibold text-text mb-2 line-clamp-2">{opportunity.title}</h4>

      {opportunity.organization && (
        <div className="flex items-center gap-1 text-sm text-muted mb-2">
          <Building className="w-3.5 h-3.5" />
          <span>{opportunity.organization}</span>
        </div>
      )}

      <p className="text-sm text-muted mb-3 line-clamp-2">{opportunity.description}</p>

      {reason && (
        <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded-lg mb-3">
          💡 {reason}
        </p>
      )}

      <div className="flex items-center justify-between text-xs text-muted">
        <div className="flex items-center gap-3">
          {opportunity.location && (
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {opportunity.location}
            </span>
          )}
          {opportunity.application_deadline && (
            <span className={`flex items-center gap-1 ${getDaysUntilDeadline(opportunity.application_deadline) === '마감' ? 'text-gray-400' : getDaysUntilDeadline(opportunity.application_deadline).startsWith('D') ? 'text-red-500 font-medium' : ''}`}>
              <Calendar className="w-3 h-3" />
              {getDaysUntilDeadline(opportunity.application_deadline)}
            </span>
          )}
        </div>
        {opportunity.url && (
          <a
            href={opportunity.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex items-center gap-1 text-primary hover:underline"
          >
            <ExternalLink className="w-3 h-3" />
            상세
          </a>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Search & Filters (for 'all' view) */}
      {viewMode === 'all' && (
        <div className="bg-card rounded-xl p-4 border border-border">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="기회 검색..."
                className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted" />
              <select
                value={filterType}
                onChange={(e) => {
                  setFilterType(e.target.value as OpportunityType | 'all');
                  setPage(1);
                }}
                className="px-3 py-2 border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="all">모든 유형</option>
                {Object.entries(typeLabels).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="bg-card rounded-xl p-12 border border-border text-center">
          <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-muted">로딩 중...</p>
        </div>
      )}

      {/* Error */}
      {error && !isLoading && (
        <div className="bg-red-50 rounded-xl p-6 border border-red-200 text-center text-red-600">
          <p>{error}</p>
          <button
            onClick={fetchData}
            className="mt-2 px-4 py-1 text-sm bg-red-100 rounded-lg hover:bg-red-200"
          >
            다시 시도
          </button>
        </div>
      )}

      {/* Content based on view mode */}
      {!isLoading && !error && (
        <>
          {/* Recommended View */}
          {viewMode === 'recommended' && recommendations && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text">
                  맞춤 추천 기회 ({recommendations.recommendations.length}건)
                </h3>
                <p className="text-sm text-muted">
                  분석일: {new Date(recommendations.generated_at).toLocaleDateString('ko-KR')}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {recommendations.recommendations.map((rec) =>
                  renderOpportunityCard(rec.opportunity, rec.match_score.overall_score, rec.match_score.match_reasons?.[0])
                )}
              </div>
              {recommendations.recommendations.length === 0 && (
                <div className="text-center py-12 bg-card rounded-xl border border-border">
                  <Star className="w-12 h-12 text-muted mx-auto mb-3" />
                  <p className="text-muted">아직 추천된 기회가 없습니다.</p>
                </div>
              )}
            </div>
          )}

          {/* Applications View */}
          {viewMode === 'applications' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text">내 지원 현황 ({applications.length}건)</h3>
              </div>
              <div className="space-y-3">
                {applications.map((app) => (
                  <div
                    key={app.application_id}
                    className="bg-card rounded-xl p-4 border border-border"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-start gap-3">
                        <span className={`p-2 rounded-lg ${typeColors[(app.opportunity_type || 'project') as OpportunityType]}`}>
                          {typeIcons[(app.opportunity_type || 'project') as OpportunityType]}
                        </span>
                        <div>
                          <h4 className="font-medium text-text">
                            {app.opportunity_title || '제목 없음'}
                          </h4>
                          <p className="text-sm text-muted">
                            {app.organization || '조직 정보 없음'}
                          </p>
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted">
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(app.created_at).toLocaleDateString('ko-KR')} 지원
                            </span>
                            {app.applied_at && (
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                지원일: {new Date(app.applied_at).toLocaleDateString('ko-KR')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-3 py-1 text-sm rounded-full ${applicationStatusLabels[app.status]?.color || 'bg-gray-100 text-gray-700'}`}>
                          {applicationStatusLabels[app.status]?.label || app.status}
                        </span>
                        {['interested', 'applied'].includes(app.status) && (
                          <button
                            onClick={() => handleWithdraw(app.application_id)}
                            className="p-2 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-red-500"
                            title="철회"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {applications.length === 0 && (
                  <div className="text-center py-12 bg-card rounded-xl border border-border">
                    <Briefcase className="w-12 h-12 text-muted mx-auto mb-3" />
                    <p className="text-muted">아직 지원한 기회가 없습니다.</p>
                    <p className="text-sm text-muted mt-1">
                      추천 탭에서 관심 있는 기회를 찾아보세요!
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* All View */}
          {viewMode === 'all' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text">
                  전체 기회 ({filteredOpportunities.length}건)
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredOpportunities.map((opp) => renderOpportunityCard(opp))}
              </div>
              {filteredOpportunities.length === 0 && (
                <div className="text-center py-12 bg-card rounded-xl border border-border">
                  <Search className="w-12 h-12 text-muted mx-auto mb-3" />
                  <p className="text-muted">
                    {searchQuery ? '검색 결과가 없습니다.' : '등록된 기회가 없습니다.'}
                  </p>
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-6">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="p-2 rounded-lg border border-border hover:bg-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <span className="px-4 py-2 text-sm">
                    {page} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="p-2 rounded-lg border border-border hover:bg-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Detail Modal */}
      {selectedOpportunity && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className={`p-2 rounded-lg ${typeColors[selectedOpportunity.opportunity_type]}`}>
                    {typeIcons[selectedOpportunity.opportunity_type]}
                  </span>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${typeColors[selectedOpportunity.opportunity_type]}`}>
                    {typeLabels[selectedOpportunity.opportunity_type]}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedOpportunity(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <h2 className="text-xl font-bold text-text mb-3">{selectedOpportunity.title}</h2>

              {selectedOpportunity.organization && (
                <div className="flex items-center gap-2 text-muted mb-4">
                  <Building className="w-4 h-4" />
                  <span>{selectedOpportunity.organization}</span>
                </div>
              )}

              <div className="space-y-4 mb-6">
                <p className="text-text">{selectedOpportunity.description}</p>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  {selectedOpportunity.location && (
                    <div>
                      <p className="text-muted mb-1">위치</p>
                      <p className="font-medium">{selectedOpportunity.location}</p>
                    </div>
                  )}
                  {selectedOpportunity.application_deadline && (
                    <div>
                      <p className="text-muted mb-1">마감일</p>
                      <p className="font-medium">
                        {new Date(selectedOpportunity.application_deadline).toLocaleDateString('ko-KR')}
                      </p>
                    </div>
                  )}
                </div>

                {selectedOpportunity.required_skills && selectedOpportunity.required_skills.length > 0 && (
                  <div>
                    <p className="text-muted text-sm mb-2">필요 스킬</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedOpportunity.required_skills.map((skill, i) => (
                        <Badge key={i} variant="secondary">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                )}

              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    handleApply(selectedOpportunity);
                    setSelectedOpportunity(null);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
                >
                  <Star className="w-4 h-4" />
                  관심 등록
                </button>
                {selectedOpportunity.url && (
                  <a
                    href={selectedOpportunity.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 px-4 py-2.5 border border-border rounded-lg hover:bg-hover transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    상세 보기
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
