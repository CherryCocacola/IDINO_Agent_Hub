'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Zap, BookOpen, Users, Award, Briefcase, Loader2, Sparkles, Send, MessageSquare, AlertTriangle } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import { CompetencyHeatStrip } from '@/components/ui/HeatStrip';
import { ActionDetailModal, CompetencyDetailModal } from '@/components/ui/Modal';
import { aiService, type ActionRecommendation, type HeatStripData, type SemesterGoal } from '@/lib/api/ai';

interface ActionBoardSectionProps {
  studentId?: string;
  departmentCd?: string;
  departmentNm?: string;
}

// Icon mapping
const iconMap: Record<string, React.ReactNode> = {
  book: <BookOpen className="w-5 h-5" />,
  users: <Users className="w-5 h-5" />,
  award: <Award className="w-5 h-5" />,
  briefcase: <Briefcase className="w-5 h-5" />,
  default: <Zap className="w-5 h-5" />,
};

// Color mapping for competencies
const competencyColors: Record<string, string> = {
  '전문지식': 'bg-primary',
  '문제해결': 'bg-secondary',
  '소통협업': 'bg-accent',
  '직업윤리': 'bg-ethics',
};

export default function ActionBoardSection({ studentId, departmentCd, departmentNm }: ActionBoardSectionProps) {
  // Use studentId prop - no fallback to hardcoded value
  // Use department info for mock data selection
  const [actions, setActions] = useState<ActionRecommendation[]>([]);
  const [heatStripData, setHeatStripData] = useState<HeatStripData[]>([]);
  const [sprintGoals, setSprintGoals] = useState<SemesterGoal[]>([]);
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([]);
  const [completionRate, setCompletionRate] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUsingRealData, setIsUsingRealData] = useState(false);

  // State for action detail modal
  const [selectedAction, setSelectedAction] = useState<ActionRecommendation | null>(null);
  const [showActionModal, setShowActionModal] = useState(false);

  // State for competency detail modal
  const [selectedCompetency, setSelectedCompetency] = useState<{name: string; monthlyScores: number[]; color: string} | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<number | undefined>(undefined);
  const [showCompetencyModal, setShowCompetencyModal] = useState(false);

  // Handle action card click
  const handleActionClick = (action: ActionRecommendation) => {
    setSelectedAction(action);
    setShowActionModal(true);
  };

  // Handle heatstrip cell click
  const handleHeatStripClick = (competencyName: string, monthIndex: number) => {
    const competency = heatStripData.find(c => c.name === competencyName);
    if (competency) {
      setSelectedCompetency({
        name: competency.name,
        monthlyScores: competency.monthly_scores,
        color: competency.color,
      });
      setSelectedMonth(monthIndex);
      setShowCompetencyModal(true);
    }
  };

  // AI Chat state
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'ai'; content: string }>>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new message arrives
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Handle AI chat submit
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isChatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsChatLoading(true);

    try {
      // Build context from current data
      const context = {
        actions: actions.map(a => `${a.title}: ${a.description} (${a.reasoning})`).join('\n'),
        competencies: heatStripData.map(c => `${c.name}: 현재 ${c.monthly_scores[c.monthly_scores.length - 1]}점`).join(', '),
        goals: sprintGoals.map(g => `${g.label} (${g.completed ? '완료' : '미완료'})`).join(', '),
      };

      const response = await aiService.chat({
        student_id: studentId || '',
        message: userMessage,
        context,
      });
      setChatMessages(prev => [...prev, { role: 'ai', content: response.response }]);
    } catch (err) {
      console.error('AI Chat Error:', err);
      // Fallback response
      const fallbackResponse = generateFallbackResponse(userMessage, actions, heatStripData, sprintGoals);
      setChatMessages(prev => [...prev, { role: 'ai', content: fallbackResponse }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Generate fallback response when API is not available
  const generateFallbackResponse = (
    question: string,
    currentActions: ActionRecommendation[],
    currentHeatStrip: HeatStripData[],
    currentGoals: SemesterGoal[]
  ): string => {
    const q = question.toLowerCase();

    if (q.includes('왜') || q.includes('이유') || q.includes('근거')) {
      const action = currentActions[0];
      return `📊 분석 근거 설명:\n\n${action?.reasoning || '현재 데이터를 기반으로 분석 중입니다.'}\n\n현재 역량 현황:\n${currentHeatStrip.map(c => `• ${c.name}: ${c.monthly_scores[c.monthly_scores.length - 1]}점`).join('\n')}`;
    }

    if (q.includes('우선순위') || q.includes('먼저') || q.includes('중요')) {
      const highPriority = currentActions.filter(a => a.priority === 'high');
      return `🎯 우선순위 높은 액션:\n\n${highPriority.map((a, i) => `${i + 1}. ${a.title}\n   → ${a.reasoning}`).join('\n\n')}`;
    }

    if (q.includes('역량') || q.includes('점수') || q.includes('현재')) {
      return `📈 현재 역량 점수:\n\n${currentHeatStrip.map(c => {
        const current = c.monthly_scores[c.monthly_scores.length - 1];
        const initial = c.monthly_scores[0];
        const growth = current - initial;
        return `• ${c.name}: ${current}점 (${growth >= 0 ? '+' : ''}${growth}점 성장)`;
      }).join('\n')}\n\n💡 전문지식이 가장 높고, 문제해결 역량 강화가 필요합니다.`;
    }

    if (q.includes('목표') || q.includes('스프린트') || q.includes('할일')) {
      const pending = currentGoals.filter(g => !g.completed);
      const completed = currentGoals.filter(g => g.completed);
      return `📋 학기 스프린트 현황:\n\n✅ 완료 (${completed.length}개):\n${completed.map(g => `• ${g.label}`).join('\n')}\n\n⏳ 진행 예정 (${pending.length}개):\n${pending.map(g => `• ${g.label}${g.priority === 'high' ? ' ⚡' : ''}`).join('\n')}`;
    }

    return `🤖 AI 커리어 어드바이저입니다.\n\n현재 분석 결과를 바탕으로 답변드립니다:\n\n• 보유 자격증: 정보처리기사, SQLD\n• 현재 학점: 3.8/4.5\n• 추천 액션: ${currentActions[0]?.title}\n\n더 구체적인 질문을 해주시면 상세히 안내해 드리겠습니다.`;
  };

  // Ref to track fetched studentId to prevent duplicate fetches
  const fetchedStudentIdRef = useRef<string | null>(null);
  const isFetchingRef = useRef(false);

  useEffect(() => {
    const fetchAIData = async () => {
      // Guard: Don't fetch if no studentId - use department-specific mock data
      if (!studentId) {
        setLoading(false);
        const category = getDepartmentCategory(departmentCd, departmentNm);
        setActions(getMockActionsForCategory(category));
        setHeatStripData(mockHeatStripData);
        setSprintGoals(getMockSprintGoalsForCategory(category));
        setIsUsingRealData(false);
        return;
      }

      // Prevent duplicate fetch for same studentId
      if (fetchedStudentIdRef.current === studentId && !loading) {
        console.log('⏭️ Skipping duplicate fetch for studentId:', studentId);
        return;
      }

      // Prevent concurrent fetches
      if (isFetchingRef.current) {
        console.log('⏭️ Fetch already in progress, skipping');
        return;
      }

      isFetchingRef.current = true;
      setLoading(true);
      setError(null);

      try {
        // Fetch all AI data in parallel
        const [actionsRes, heatStripRes, sprintRes] = await Promise.allSettled([
          aiService.getActionRecommendations(studentId),
          aiService.getHeatStripData(studentId),
          aiService.getSemesterSprint(studentId),
        ]);

        let usingRealData = false;

        // Process actions - use mock if empty or failed
        const category = getDepartmentCategory(departmentCd, departmentNm);
        if (actionsRes.status === 'fulfilled' && actionsRes.value.recommendations?.length > 0) {
          setActions(actionsRes.value.recommendations);
          usingRealData = true;
          console.log('✅ AI Actions loaded from API');
        } else {
          console.warn('AI Actions API returned empty or failed, using mock data');
          setActions(getMockActionsForCategory(category));
        }

        // Process heatstrip - use mock if empty or failed
        if (heatStripRes.status === 'fulfilled' && heatStripRes.value.competencies?.length > 0) {
          setHeatStripData(heatStripRes.value.competencies);
          usingRealData = true;
          console.log('✅ HeatStrip data loaded from API');
        } else {
          console.warn('HeatStrip API returned empty or failed, using mock data');
          setHeatStripData(mockHeatStripData);
        }

        // Process sprint goals - use mock if empty or failed
        if (sprintRes.status === 'fulfilled' && sprintRes.value.goals?.length > 0) {
          setSprintGoals(sprintRes.value.goals);
          setAiSuggestions(sprintRes.value.ai_suggestions || []);
          setCompletionRate(sprintRes.value.completion_rate || 0);
          usingRealData = true;
          console.log('✅ Sprint goals loaded from API');
        } else {
          console.warn('Sprint API returned empty or failed, using mock data');
          setSprintGoals(getMockSprintGoalsForCategory(category));
          setAiSuggestions([]);
          setCompletionRate(0);
        }

        setIsUsingRealData(usingRealData);
        // Mark this studentId as fetched only on success
        fetchedStudentIdRef.current = studentId;
      } catch (err) {
        console.error('AI Service Error:', err);
        setError('AI 서비스 연결 중 오류가 발생했습니다. 기본 데이터를 표시합니다.');
        // Use fallback mock data based on department
        const category = getDepartmentCategory(departmentCd, departmentNm);
        setActions(getMockActionsForCategory(category));
        setHeatStripData(mockHeatStripData);
        setSprintGoals(getMockSprintGoalsForCategory(category));
        setIsUsingRealData(false);
      } finally {
        setLoading(false);
        isFetchingRef.current = false;
      }
    };

    fetchAIData();
  }, [studentId, departmentCd, departmentNm]);

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'high':
        return <Badge variant="error">긴급</Badge>;
      case 'medium':
        return <Badge variant="warning">권장</Badge>;
      default:
        return <Badge variant="muted">선택</Badge>;
    }
  };

  const getIcon = (iconType: string, competency: string) => {
    const icon = iconMap[iconType] || iconMap.default;
    const bgColor = competencyColors[competency] || 'bg-gray-500';
    return { icon, bgColor };
  };

  const completedCount = sprintGoals.filter(g => g.completed).length;
  const totalCount = sprintGoals.length;

  return (
    <section id="actions" className="section animate-fadeIn">
      <h2 className="section-title">
        <Zap className="w-5 h-5 text-primary" />
        AI 액션보드
        {loading && <Loader2 className="w-4 h-4 ml-2 animate-spin text-muted" />}
        {!loading && !error && isUsingRealData && <Sparkles className="w-4 h-4 ml-2 text-yellow-500" />}
        {!loading && isUsingRealData && (
          <span className="ml-2 text-xs font-normal text-green-600 bg-green-50 px-2 py-1 rounded-full">
            AI 실시간 분석
          </span>
        )}
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Warning when using mock data */}
      {!loading && !isUsingRealData && !error && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2 text-sm text-yellow-700">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>AI 서비스에서 데이터를 불러올 수 없어 샘플 데이터를 표시합니다. AI 서비스가 실행 중인지 확인해주세요.</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Action Cards */}
        <div>
          <h3 className="font-semibold text-text mb-4 flex items-center gap-2">
            📋 AI 추천 액션
            {!loading && actions.length > 0 && (
              <span className="text-xs text-muted font-normal">(GPT 생성)</span>
            )}
          </h3>
          <div className="space-y-3">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
                <span className="ml-2 text-muted">AI가 분석 중입니다...</span>
              </div>
            ) : (
              actions.map((action) => {
                const { icon, bgColor } = getIcon(action.icon_type || 'default', action.competency || '');
                return (
                  <div
                    key={action.id}
                    onClick={() => handleActionClick(action)}
                    className="p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer group"
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-white ${bgColor}`}>
                        {icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-text">{action.title}</span>
                          {getPriorityBadge(action.priority)}
                        </div>
                        <p className="text-sm text-muted mb-2">{action.description}</p>
                        <div className="flex items-center gap-3 text-xs text-muted">
                          <span>⏰ {action.deadline}</span>
                          <span>🎯 {action.competency}</span>
                        </div>
                        {/* AI Reasoning (shown on hover) */}
                        <div className="mt-2 text-xs text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
                          💡 {action.reasoning}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: HeatStrip Visualization */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <h3 className="font-semibold text-text">📊 역량 변화 히트맵</h3>
            <div className="group relative">
              <span className="w-5 h-5 rounded-full bg-gray-200 text-gray-600 text-xs flex items-center justify-center cursor-help">?</span>
              <div className="absolute left-0 top-6 w-72 p-3 bg-gray-800 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 shadow-lg">
                <p className="font-semibold mb-2">히트맵 읽는 법</p>
                <ul className="space-y-1 text-gray-300">
                  <li>• 가로축: 1월~12월 (시간 흐름)</li>
                  <li>• 세로축: 4대 핵심역량</li>
                  <li>• 색상 진하기: 역량 점수 (진할수록 높음)</li>
                  <li>• 클릭: 해당 월 상세 데이터 확인</li>
                </ul>
                <p className="mt-2 text-gray-400">수업 이수, 자격증 취득, 프로젝트 참여 등에 따라 점수가 변동됩니다.</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 rounded-xl p-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-primary" />
              </div>
            ) : (
              <CompetencyHeatStrip
                competencies={heatStripData.length > 0 ? heatStripData.map(c => ({
                  name: c.name,
                  monthlyScores: c.monthly_scores,
                  color: c.color,
                })) : mockHeatStripData.map(c => ({
                  name: c.name,
                  monthlyScores: c.monthly_scores,
                  color: c.color,
                }))}
                onCellClick={handleHeatStripClick}
              />
            )}
          </div>

          {/* Semester Sprint */}
          <div className="mt-6">
            <h3 className="font-semibold text-text mb-4">🏃 학기 스프린트</h3>
            <div className="bg-gradient-to-r from-primary/5 to-secondary/5 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-muted">이번 학기 목표</span>
                <Badge variant="primary">{completedCount}/{totalCount} 달성</Badge>
              </div>
              <div className="space-y-3">
                {loading ? (
                  <div className="flex items-center justify-center py-4">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                  </div>
                ) : (
                  sprintGoals.map((goal, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs
                        ${goal.completed ? 'bg-secondary text-white' : 'bg-gray-200 text-gray-500'}`}>
                        {goal.completed ? '✓' : index + 1}
                      </span>
                      <span className={`text-sm ${goal.completed ? 'text-muted line-through' : 'text-text'}`}>
                        {goal.label}
                      </span>
                      {goal.priority === 'high' && !goal.completed && (
                        <span className="text-xs text-red-500">⚡</span>
                      )}
                    </div>
                  ))
                )}
              </div>

              {/* AI Suggestions */}
              {aiSuggestions.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-xs text-muted mb-2">💡 AI 조언:</p>
                  {aiSuggestions.slice(0, 2).map((suggestion, index) => (
                    <p key={index} className="text-xs text-blue-600 mb-1">
                      • {suggestion}
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* AI Chat Section */}
      <div className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-100">
        <h3 className="font-semibold text-text mb-3 flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-primary" />
          AI 커리어 어드바이저에게 질문하기
        </h3>

        {/* Chat Messages */}
        {chatMessages.length > 0 && (
          <div className="mb-4 max-h-60 overflow-y-auto space-y-3 p-3 bg-white rounded-lg">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg text-sm whitespace-pre-line ${
                    msg.role === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-text'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isChatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 p-3 rounded-lg flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <span className="text-sm text-muted">AI가 분석 중...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        )}

        {/* Quick Questions */}
        {chatMessages.length === 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            <button
              onClick={() => setChatInput('왜 이 액션을 추천하나요?')}
              className="px-3 py-1.5 bg-white text-sm text-text border border-gray-200 rounded-lg hover:border-primary transition-colors"
            >
              💡 왜 이 액션을 추천하나요?
            </button>
            <button
              onClick={() => setChatInput('현재 역량 점수 분석해줘')}
              className="px-3 py-1.5 bg-white text-sm text-text border border-gray-200 rounded-lg hover:border-primary transition-colors"
            >
              📊 현재 역량 점수 분석
            </button>
            <button
              onClick={() => setChatInput('우선순위 높은 것부터 알려줘')}
              className="px-3 py-1.5 bg-white text-sm text-text border border-gray-200 rounded-lg hover:border-primary transition-colors"
            >
              🎯 우선순위 높은 것
            </button>
          </div>
        )}

        {/* Chat Input */}
        <form onSubmit={handleChatSubmit} className="flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="예: 왜 알고리즘 역량 강화를 추천하나요?"
            className="flex-1 px-4 py-2 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary text-sm"
            disabled={isChatLoading}
          />
          <button
            type="submit"
            disabled={isChatLoading || !chatInput.trim()}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">질문하기</span>
          </button>
        </form>
      </div>

      {/* Action Detail Modal */}
      <ActionDetailModal
        isOpen={showActionModal}
        onClose={() => setShowActionModal(false)}
        action={selectedAction}
      />

      {/* Competency Detail Modal */}
      <CompetencyDetailModal
        isOpen={showCompetencyModal}
        onClose={() => setShowCompetencyModal(false)}
        competency={selectedCompetency}
        selectedMonth={selectedMonth}
      />
    </section>
  );
}

// Department category detection helper
function getDepartmentCategory(departmentCd?: string, departmentNm?: string): string {
  const checkStrings = [
    departmentCd?.toUpperCase() || '',
    departmentNm || '',
  ].filter(Boolean);

  if (checkStrings.length === 0) return 'IT';

  const matchesAny = (keywords: string[]) =>
    keywords.some(keyword =>
      checkStrings.some(str => str.toUpperCase().includes(keyword.toUpperCase()))
    );

  if (matchesAny(['MED', 'MEDI', '의예', '의학', 'MD', '의과'])) return 'MEDICAL';
  if (matchesAny(['HEALTH', 'NURS', '보건', '간호', '치위생', '임상', '약학', '물리치료'])) return 'HEALTH';
  if (matchesAny(['CS', 'SE', 'IT', 'CSE', 'SWE', '컴퓨터', '소프트웨어', '정보'])) return 'IT';
  if (matchesAny(['EDU', 'TEACH', '교육', '사범'])) return 'EDUCATION';
  if (matchesAny(['ART', 'DESIGN', 'MUSIC', '예술', '디자인', '미술', '음악'])) return 'ARTS';
  if (matchesAny(['BUS', 'ECON', 'MGMT', '경영', '경제', '회계', '금융'])) return 'BUSINESS';
  if (matchesAny(['SOC', 'PSY', 'POL', '사회', '심리', '정치', '행정', '복지'])) return 'SOCIAL';
  if (matchesAny(['SCI', 'BIO', 'CHEM', '자연', '생명', '화학', '물리', '환경'])) return 'SCIENCE';
  if (matchesAny(['ENG', 'MECH', 'ELEC', '공학', '기계', '전기', '전자', '토목', '건축'])) return 'ENGINEERING';

  return 'IT';
}

// Category-based mock actions
const mockActionsByCategory: Record<string, ActionRecommendation[]> = {
  IT: [
    { id: 1, title: '알고리즘 역량 심화', description: 'LeetCode/백준 Medium 난이도 50문제 풀이', priority: 'high', deadline: '2주 이내', competency: '문제해결', reasoning: '현재 문제해결 역량(75점)이 목표 대비 15% 부족합니다.', icon_type: 'book' },
    { id: 2, title: '캡스톤 프로젝트 리드', description: '4인 팀 프로젝트에서 PM 역할 수행', priority: 'medium', deadline: '1개월', competency: '소통협업', reasoning: '팀 리딩 경험이 필요합니다.', icon_type: 'users' },
    { id: 3, title: 'AWS 자격증 취득', description: 'AWS Solutions Architect Associate 준비', priority: 'medium', deadline: '3개월', competency: '전문지식', reasoning: '클라우드 자격증 추가로 백엔드 개발자 경쟁력 강화 권장.', icon_type: 'award' },
    { id: 4, title: '인턴십 지원 준비', description: '이력서 및 포트폴리오 작성', priority: 'high', deadline: '1개월', competency: '직업윤리', reasoning: '하계 인턴십 지원 적기입니다.', icon_type: 'briefcase' },
  ],
  MEDICAL: [
    { id: 1, title: '임상실습 준비', description: '본과 임상실습 전 기초의학 복습', priority: 'high', deadline: '1개월', competency: '전문지식', reasoning: '임상실습에서 기초의학 지식 활용이 필수입니다.', icon_type: 'book' },
    { id: 2, title: '의료봉사 참여', description: '의료봉사단 활동으로 환자 상담 경험 쌓기', priority: 'medium', deadline: '2개월', competency: '소통협업', reasoning: '환자와의 소통 능력 향상이 필요합니다.', icon_type: 'users' },
    { id: 3, title: '의사국가고시 대비', description: '기출문제 분석 및 오답노트 작성', priority: 'high', deadline: '6개월', competency: '문제해결', reasoning: '국가고시 합격이 최우선 목표입니다.', icon_type: 'award' },
    { id: 4, title: '전공의 수련 계획', description: '희망 전공과 및 병원 리서치', priority: 'medium', deadline: '3개월', competency: '직업윤리', reasoning: '조기에 진로를 구체화하면 효율적인 준비가 가능합니다.', icon_type: 'briefcase' },
  ],
  HEALTH: [
    { id: 1, title: '전문자격증 취득', description: '해당 분야 국가자격증 준비 (간호사/물리치료사/임상병리사 등)', priority: 'high', deadline: '3개월', competency: '전문지식', reasoning: '자격증 취득이 취업의 필수 조건입니다.', icon_type: 'award' },
    { id: 2, title: '임상실습 심화', description: '병원 실습을 통한 실무 역량 강화', priority: 'high', deadline: '1개월', competency: '문제해결', reasoning: '현장 경험이 취업에 결정적 역할을 합니다.', icon_type: 'book' },
    { id: 3, title: '환자 커뮤니케이션', description: '환자 상담 시뮬레이션 연습', priority: 'medium', deadline: '2개월', competency: '소통협업', reasoning: '환자 응대 능력이 중요합니다.', icon_type: 'users' },
    { id: 4, title: '취업 병원 리서치', description: '희망 근무지 및 병원 정보 수집', priority: 'medium', deadline: '2개월', competency: '직업윤리', reasoning: '취업 목표를 구체화해야 합니다.', icon_type: 'briefcase' },
  ],
  EDUCATION: [
    { id: 1, title: '임용고시 대비', description: '임용시험 전 과목 기출분석 및 오답정리', priority: 'high', deadline: '6개월', competency: '전문지식', reasoning: '임용시험 합격이 최우선 목표입니다.', icon_type: 'book' },
    { id: 2, title: '교육실습 준비', description: '수업 시연 및 학급 운영 계획 작성', priority: 'high', deadline: '1개월', competency: '소통협업', reasoning: '교육실습 평가가 중요합니다.', icon_type: 'users' },
    { id: 3, title: '교육봉사 활동', description: '지역아동센터 학습 멘토링 참여', priority: 'medium', deadline: '2개월', competency: '직업윤리', reasoning: '봉사 경험이 면접에서 좋은 인상을 줍니다.', icon_type: 'award' },
    { id: 4, title: '수업 포트폴리오', description: '수업 지도안 및 교육자료 정리', priority: 'medium', deadline: '3개월', competency: '문제해결', reasoning: '체계적인 수업 준비 능력을 보여줄 수 있습니다.', icon_type: 'briefcase' },
  ],
  BUSINESS: [
    { id: 1, title: '회계/재무 자격증', description: 'CPA, CFA, 투자자산운용사 등 자격증 준비', priority: 'high', deadline: '6개월', competency: '전문지식', reasoning: '금융/회계 분야 자격증이 필수입니다.', icon_type: 'award' },
    { id: 2, title: '케이스 스터디', description: '컨설팅/투자은행 케이스 면접 준비', priority: 'high', deadline: '2개월', competency: '문제해결', reasoning: '논리적 분석 능력이 중요합니다.', icon_type: 'book' },
    { id: 3, title: '인턴십 지원', description: '대기업/금융권 인턴십 프로그램 지원', priority: 'high', deadline: '1개월', competency: '직업윤리', reasoning: '인턴십 경험이 정규직 전환에 유리합니다.', icon_type: 'briefcase' },
    { id: 4, title: '비즈니스 영어', description: 'OPIc IH 이상 / TOEIC Speaking Lv.7 준비', priority: 'medium', deadline: '3개월', competency: '소통협업', reasoning: '글로벌 기업 취업에 필수입니다.', icon_type: 'users' },
  ],
  DEFAULT: [
    { id: 1, title: '전공 심화 학습', description: '전공 핵심 과목 성적 향상', priority: 'high', deadline: '1학기', competency: '전문지식', reasoning: '전공 역량 강화가 필요합니다.', icon_type: 'book' },
    { id: 2, title: '관련 자격증 취득', description: '전공 관련 자격증 1개 이상 취득', priority: 'medium', deadline: '6개월', competency: '문제해결', reasoning: '자격증으로 전문성을 증명할 수 있습니다.', icon_type: 'award' },
    { id: 3, title: '현장 경험 쌓기', description: '인턴십, 현장실습 참여', priority: 'high', deadline: '2개월', competency: '직업윤리', reasoning: '실무 경험이 취업에 중요합니다.', icon_type: 'briefcase' },
    { id: 4, title: '팀 프로젝트 참여', description: '전공 관련 팀 프로젝트 수행', priority: 'medium', deadline: '1학기', competency: '소통협업', reasoning: '협업 능력을 기를 수 있습니다.', icon_type: 'users' },
  ],
};

// Category-based mock sprint goals
const mockSprintGoalsByCategory: Record<string, SemesterGoal[]> = {
  IT: [
    { label: '알고리즘 스터디 참여 (진행중)', completed: false, priority: 'high' },
    { label: '정보처리기사 취득 완료 ✓', completed: true, priority: 'high' },
    { label: 'SQLD 취득 완료 ✓', completed: true, priority: 'high' },
    { label: '캡스톤 팀 구성', completed: false, priority: 'medium' },
    { label: '인턴십 지원 준비', completed: false, priority: 'high' },
  ],
  MEDICAL: [
    { label: '기초의학 종합 복습', completed: false, priority: 'high' },
    { label: '임상실습 병원 배정', completed: true, priority: 'high' },
    { label: '의료봉사 참여 (진행중)', completed: false, priority: 'medium' },
    { label: '국가고시 스터디 가입', completed: true, priority: 'high' },
    { label: '전공의 희망과 결정', completed: false, priority: 'medium' },
  ],
  HEALTH: [
    { label: '국가자격증 시험 접수', completed: true, priority: 'high' },
    { label: '병원 임상실습 수료', completed: false, priority: 'high' },
    { label: '취업 희망 병원 리스트업', completed: false, priority: 'medium' },
    { label: '환자 상담 롤플레이 연습', completed: false, priority: 'medium' },
    { label: '이력서 및 자기소개서 작성', completed: false, priority: 'high' },
  ],
  EDUCATION: [
    { label: '임용고시 1차 대비 (진행중)', completed: false, priority: 'high' },
    { label: '교육실습 학교 배정', completed: true, priority: 'high' },
    { label: '수업 지도안 작성 연습', completed: false, priority: 'medium' },
    { label: '교육봉사 30시간 이수', completed: true, priority: 'medium' },
    { label: '면접 스터디 가입', completed: false, priority: 'high' },
  ],
  BUSINESS: [
    { label: 'CFA Level 1 준비 (진행중)', completed: false, priority: 'high' },
    { label: '인턴십 서류 제출', completed: true, priority: 'high' },
    { label: '케이스 스터디 연습', completed: false, priority: 'high' },
    { label: '영어 인터뷰 준비', completed: false, priority: 'medium' },
    { label: '네트워킹 이벤트 참석', completed: false, priority: 'medium' },
  ],
  DEFAULT: [
    { label: '전공 핵심 과목 이수', completed: true, priority: 'high' },
    { label: '관련 자격증 준비', completed: false, priority: 'high' },
    { label: '현장실습/인턴십 신청', completed: false, priority: 'high' },
    { label: '졸업 요건 확인', completed: true, priority: 'medium' },
    { label: '취업 포트폴리오 준비', completed: false, priority: 'medium' },
  ],
};

// Helper to get mock data by category
function getMockActionsForCategory(category: string): ActionRecommendation[] {
  return mockActionsByCategory[category] || mockActionsByCategory.DEFAULT;
}

function getMockSprintGoalsForCategory(category: string): SemesterGoal[] {
  return mockSprintGoalsByCategory[category] || mockSprintGoalsByCategory.DEFAULT;
}

// Default mock data for backward compatibility (IT focused)
const mockActions: ActionRecommendation[] = mockActionsByCategory.IT;

// 히트맵: 월별 역량 점수 변화 (1월~12월) - 공통 사용
const mockHeatStripData: HeatStripData[] = [
  { name: '전문지식', monthly_scores: [70, 72, 75, 78, 80, 82, 85, 85, 88, 88, 90, 92], color: '#5b6dff', trend: 'up' },
  { name: '문제해결', monthly_scores: [60, 62, 58, 65, 68, 70, 72, 73, 75, 75, 75, 75], color: '#00b7a8', trend: 'up' },
  { name: '소통협업', monthly_scores: [65, 68, 70, 72, 75, 78, 80, 80, 82, 82, 82, 82], color: '#ff8a5c', trend: 'stable' },
  { name: '직업윤리', monthly_scores: [75, 78, 80, 82, 85, 88, 88, 90, 90, 92, 92, 92], color: '#f6c343', trend: 'up' },
];

// Default sprint goals for backward compatibility (IT focused)
const mockSprintGoals: SemesterGoal[] = mockSprintGoalsByCategory.IT;
