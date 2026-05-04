'use client';

import { useState, useEffect, useCallback } from 'react';
import { badgeService } from '@/lib/api/badge';
import type {
  BadgeResponse,
  CredentialResponse,
  SkillPassportResponse,
  BadgeCategory,
  StudentBadgeResponse,
} from '@/types';

interface PassportSectionProps {
  studentId: string;
}

const categoryLabels: Record<BadgeCategory, string> = {
  skill: '스킬',
  achievement: '성취',
  course: '강의 수료',
  project: '프로젝트',
  certification: '자격증',
  competition: '공모전',
  community: '커뮤니티',
};

const categoryColors: Record<BadgeCategory, string> = {
  skill: 'bg-green-100 text-green-800 border-green-300',
  achievement: 'bg-red-100 text-red-800 border-red-300',
  course: 'bg-blue-100 text-blue-800 border-blue-300',
  project: 'bg-purple-100 text-purple-800 border-purple-300',
  certification: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  competition: 'bg-orange-100 text-orange-800 border-orange-300',
  community: 'bg-teal-100 text-teal-800 border-teal-300',
};

const levelColors: Record<string, string> = {
  bronze: 'from-amber-600 to-amber-400',
  silver: 'from-gray-400 to-gray-300',
  gold: 'from-yellow-500 to-yellow-300',
  platinum: 'from-cyan-400 to-cyan-200',
};

export default function PassportSection({ studentId }: PassportSectionProps) {
  const [passport, setPassport] = useState<SkillPassportResponse | null>(null);
  const [badges, setBadges] = useState<StudentBadgeResponse[]>([]);
  const [credentials, setCredentials] = useState<CredentialResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'badges' | 'credentials'>('overview');
  const [selectedCategory, setSelectedCategory] = useState<BadgeCategory | 'all'>('all');
  const [selectedBadge, setSelectedBadge] = useState<StudentBadgeResponse | null>(null);

  const fetchPassportData = useCallback(async () => {
    setLoading(true);
    try {
      const [passportResult, badgesResult, credentialsResult] = await Promise.allSettled([
        badgeService.getPassport(studentId),
        badgeService.getStudentBadges(studentId),
        badgeService.getStudentCredentials(studentId),
      ]);
      if (passportResult.status === 'fulfilled') setPassport(passportResult.value);
      if (badgesResult.status === 'fulfilled') setBadges(badgesResult.value);
      if (credentialsResult.status === 'fulfilled') setCredentials(credentialsResult.value);
    } catch (error) {
      console.error('Failed to fetch passport data:', error);
    } finally {
      setLoading(false);
    }
  }, [studentId]);

  useEffect(() => {
    fetchPassportData();
  }, [fetchPassportData]);

  const filteredBadges = badges.filter(
    badge => selectedCategory === 'all' || badge.badge.category === selectedCategory
  );

  const getBadgeLevelStyle = (level: string | undefined) => {
    if (!level) return 'from-gray-400 to-gray-300';
    return levelColors[level.toLowerCase()] || 'from-gray-400 to-gray-300';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Passport Card */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-lg shadow-lg p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-sm opacity-75">SKILL PASSPORT</div>
            <h2 className="text-2xl font-bold mt-1">{passport?.student_name || '학생'}</h2>
            <div className="text-sm opacity-75 mt-1">{passport?.student_id}</div>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold">{passport?.total_points || 0}</div>
            <div className="text-sm opacity-75">총 포인트</div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold">{passport?.total_badges || badges.length}</div>
            <div className="text-xs opacity-75">획득 배지</div>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold">{credentials.length}</div>
            <div className="text-xs opacity-75">자격증</div>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold">{passport?.verified_skills || 0}</div>
            <div className="text-xs opacity-75">검증 스킬</div>
          </div>
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold">{passport?.total_skills || 0}</div>
            <div className="text-xs opacity-75">총 스킬</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="border-b">
          <nav className="flex">
            {[
              { id: 'overview', label: '개요' },
              { id: 'badges', label: `배지 (${badges.length})` },
              { id: 'credentials', label: `자격증 (${credentials.length})` },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`px-6 py-3 font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'text-indigo-600 border-indigo-600'
                    : 'text-gray-500 border-transparent hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Category Summary */}
              <div>
                <h3 className="text-lg font-semibold mb-4">카테고리별 현황</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {Object.entries(categoryLabels).map(([category, label]) => {
                    const count = badges.filter(b => b.badge.category === category).length;
                    return (
                      <div
                        key={category}
                        className={`p-4 rounded-lg border ${categoryColors[category as BadgeCategory]}`}
                      >
                        <div className="text-2xl font-bold">{count}</div>
                        <div className="text-sm">{label}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Recent Badges */}
              <div>
                <h3 className="text-lg font-semibold mb-4">최근 획득 배지</h3>
                {badges.length > 0 ? (
                  <div className="flex gap-4 overflow-x-auto pb-2">
                    {badges.slice(0, 5).map(studentBadge => (
                      <div
                        key={studentBadge.student_badge_id}
                        onClick={() => setSelectedBadge(studentBadge)}
                        className="flex-shrink-0 w-24 text-center cursor-pointer hover:opacity-80 transition-opacity"
                      >
                        <div
                          className={`w-16 h-16 mx-auto rounded-full bg-gradient-to-br ${getBadgeLevelStyle(studentBadge.badge.level)} flex items-center justify-center text-white text-2xl shadow-lg`}
                        >
                          {studentBadge.badge.icon_url ? <img src={studentBadge.badge.icon_url} alt="" className="w-10 h-10" /> : '🏆'}
                        </div>
                        <div className="text-xs font-medium mt-2 truncate">{studentBadge.badge.badge_nm}</div>
                        <div className="text-xs text-gray-500">{studentBadge.badge.level}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">아직 획득한 배지가 없습니다.</p>
                )}
              </div>

              {/* Verified Skills */}
              {passport?.skills && passport.skills.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">검증된 스킬</h3>
                  <div className="flex flex-wrap gap-2">
                    {passport.skills.filter(skill => skill.verified).map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm"
                      >
                        ✓ {skill.skill_nm} (Lv.{skill.level})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Badges Tab */}
          {activeTab === 'badges' && (
            <div>
              {/* Category Filter */}
              <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
                <button
                  onClick={() => setSelectedCategory('all')}
                  className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                    selectedCategory === 'all'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  전체 ({badges.length})
                </button>
                {Object.entries(categoryLabels).map(([category, label]) => {
                  const count = badges.filter(b => b.badge.category === category).length;
                  return (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category as BadgeCategory)}
                      className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                        selectedCategory === category
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {label} ({count})
                    </button>
                  );
                })}
              </div>

              {/* Badges Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {filteredBadges.map(studentBadge => (
                  <div
                    key={studentBadge.student_badge_id}
                    onClick={() => setSelectedBadge(studentBadge)}
                    className="p-4 rounded-lg border hover:shadow-md transition-shadow cursor-pointer text-center"
                  >
                    <div
                      className={`w-16 h-16 mx-auto rounded-full bg-gradient-to-br ${getBadgeLevelStyle(studentBadge.badge.level)} flex items-center justify-center text-white text-2xl shadow-md`}
                    >
                      {studentBadge.badge.icon_url ? <img src={studentBadge.badge.icon_url} alt="" className="w-10 h-10" /> : '🏆'}
                    </div>
                    <h4 className="font-medium text-sm mt-3">{studentBadge.badge.badge_nm}</h4>
                    <div className="text-xs text-gray-500 mt-1">{studentBadge.badge.level}</div>
                    <div className={`inline-block px-2 py-0.5 rounded text-xs mt-2 ${categoryColors[studentBadge.badge.category]}`}>
                      {categoryLabels[studentBadge.badge.category]}
                    </div>
                  </div>
                ))}

                {filteredBadges.length === 0 && (
                  <div className="col-span-full text-center py-8 text-gray-500">
                    해당 카테고리의 배지가 없습니다.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Credentials Tab */}
          {activeTab === 'credentials' && (
            <div className="space-y-4">
              {credentials.length > 0 ? (
                credentials.map(credential => (
                  <div
                    key={credential.credential_id}
                    className="p-4 border rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium">{credential.credential_nm}</h4>
                        <p className="text-sm text-gray-500 mt-1">
                          {credential.issuing_org} • {credential.issue_date}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">{credential.credential_type}</p>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${
                            credential.verified
                              ? 'bg-green-100 text-green-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {credential.verified ? '검증됨' : '대기중'}
                        </span>
                        {credential.expiry_date && (
                          <span className="text-xs text-gray-500">
                            만료: {credential.expiry_date}
                          </span>
                        )}
                      </div>
                    </div>
                    {credential.credential_number && (
                      <div className="mt-2 text-xs text-gray-500">
                        자격번호: {credential.credential_number}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-gray-500">
                  등록된 자격증이 없습니다.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Badge Detail Modal */}
      {selectedBadge && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6 text-center">
              <div
                className={`w-24 h-24 mx-auto rounded-full bg-gradient-to-br ${getBadgeLevelStyle(selectedBadge.badge.level)} flex items-center justify-center text-white text-4xl shadow-lg`}
              >
                {selectedBadge.badge.icon_url ? <img src={selectedBadge.badge.icon_url} alt="" className="w-16 h-16" /> : '🏆'}
              </div>
              <h2 className="text-xl font-bold mt-4">{selectedBadge.badge.badge_nm}</h2>
              <div className="flex items-center justify-center gap-2 mt-2">
                <span className={`px-2 py-0.5 rounded text-xs ${categoryColors[selectedBadge.badge.category]}`}>
                  {categoryLabels[selectedBadge.badge.category]}
                </span>
                <span className="text-sm text-gray-500">{selectedBadge.badge.level}</span>
              </div>

              {selectedBadge.badge.description && (
                <p className="text-gray-600 mt-4">{selectedBadge.badge.description}</p>
              )}

              {selectedBadge.badge.criteria && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg text-left">
                  <div className="text-sm font-medium text-gray-700">획득 조건</div>
                  <div className="text-sm text-gray-600 mt-1">{selectedBadge.badge.criteria}</div>
                </div>
              )}

              <div className="mt-4 text-sm text-gray-500">
                획득일: {selectedBadge.earned_at || '정보 없음'}
              </div>

              <button
                onClick={() => setSelectedBadge(null)}
                className="mt-6 w-full py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
