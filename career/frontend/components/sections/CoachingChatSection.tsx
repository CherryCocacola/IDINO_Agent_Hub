'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Bot, User, Lightbulb, ExternalLink, RefreshCw, Sparkles } from 'lucide-react';
import { coachingService } from '@/lib/api/coaching';
import type { ChatMessage, AICoachResponse, GoalResponse } from '@/types';

interface CoachingChatSectionProps {
  studentId: string;
}

const queryTypeLabels: Record<string, string> = {
  advice: '조언 요청',
  plan_suggest: '계획 제안',
  motivation: '동기부여',
  blockers: '장애물 해결',
  review: '진행 검토',
};

export default function CoachingChatSection({ studentId }: CoachingChatSectionProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedQueryType, setSelectedQueryType] = useState<string>('advice');
  const [selectedGoal, setSelectedGoal] = useState<string | undefined>();
  const [goals, setGoals] = useState<GoalResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isGoalsLoading, setIsGoalsLoading] = useState(true);

  // Fetch user's goals for context
  useEffect(() => {
    const fetchGoals = async () => {
      setIsGoalsLoading(true);
      try {
        const data = await coachingService.getStudentGoals(studentId);
        setGoals(data.filter((g) => g.status === 'active'));
      } catch (err) {
        console.error('Failed to fetch goals:', err);
      } finally {
        setIsGoalsLoading(false);
      }
    };
    fetchGoals();
  }, [studentId]);

  // Add initial welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        content: '안녕하세요! 저는 당신의 AI 코치입니다. 목표 달성, 학업 계획, 진로 고민 등 무엇이든 도와드릴 수 있어요. 무엇이 궁금하신가요?',
        timestamp: new Date().toISOString(),
        suggestions: [
          '이번 학기 목표를 어떻게 세워야 할까요?',
          '시간 관리 팁을 알려주세요',
          '동기부여가 필요해요',
        ],
      };
      setMessages([welcomeMessage]);
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = useCallback(async (messageContent?: string) => {
    const content = messageContent || inputValue.trim();
    if (!content || isLoading) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await coachingService.getAICoachResponse({
        student_id: studentId,
        goal_id: selectedGoal,
        query_type: selectedQueryType as 'advice' | 'plan_suggest' | 'motivation' | 'blockers' | 'review',
        context: content,
        include_history: true,
      });

      // Add AI response
      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        timestamp: response.generated_at,
        suggestions: response.follow_up_questions.slice(0, 3),
        resources: response.resources,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      console.error('Failed to get AI response:', err);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: '죄송합니다. 응답을 생성하는 중에 문제가 발생했습니다. 다시 시도해 주세요.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, studentId, selectedGoal, selectedQueryType, isLoading]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    handleSendMessage(suggestion);
  };

  const clearChat = () => {
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: '새로운 대화를 시작합니다. 무엇이 궁금하신가요?',
      timestamp: new Date().toISOString(),
      suggestions: [
        '이번 학기 목표를 어떻게 세워야 할까요?',
        '시간 관리 팁을 알려주세요',
        '동기부여가 필요해요',
      ],
    }]);
  };

  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 280px)', minHeight: '500px' }}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-gray-50">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-full bg-gradient-to-br from-primary to-secondary">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-text">AI 코치</h3>
            <p className="text-xs text-muted">언제든지 도움을 드릴 준비가 되어 있어요</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Query Type Selector */}
          <select
            value={selectedQueryType}
            onChange={(e) => setSelectedQueryType(e.target.value)}
            className="px-3 py-1.5 text-sm border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {Object.entries(queryTypeLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>

          {/* Goal Selector */}
          <select
            value={selectedGoal || ''}
            onChange={(e) => setSelectedGoal(e.target.value || undefined)}
            className="px-3 py-1.5 text-sm border border-border rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary max-w-[150px]"
            disabled={isGoalsLoading}
          >
            <option value="">목표 선택 (선택)</option>
            {goals.map((goal) => (
              <option key={goal.goal_id} value={goal.goal_id}>
                {goal.title.length > 15 ? goal.title.slice(0, 15) + '...' : goal.title}
              </option>
            ))}
          </select>

          <button
            onClick={clearChat}
            className="p-2 hover:bg-hover rounded-lg transition-colors"
            title="새 대화"
          >
            <RefreshCw className="w-4 h-4 text-muted" />
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'user'
                  ? 'bg-primary'
                  : 'bg-gradient-to-br from-primary to-secondary'
              }`}
            >
              {message.role === 'user' ? (
                <User className="w-4 h-4 text-white" />
              ) : (
                <Bot className="w-4 h-4 text-white" />
              )}
            </div>

            {/* Message Content */}
            <div
              className={`max-w-[70%] ${
                message.role === 'user'
                  ? 'bg-primary text-white rounded-2xl rounded-br-sm'
                  : 'bg-gray-100 text-text rounded-2xl rounded-bl-sm'
              } p-4`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>

              {/* Suggestions */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-center gap-1 text-xs text-muted mb-2">
                    <Lightbulb className="w-3 h-3" />
                    <span>추천 질문</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {message.suggestions.map((suggestion, i) => (
                      <button
                        key={i}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="px-3 py-1.5 text-xs bg-white hover:bg-gray-50 border border-gray-200 rounded-full text-text transition-colors"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Resources */}
              {message.resources && message.resources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="flex items-center gap-1 text-xs text-muted mb-2">
                    <ExternalLink className="w-3 h-3" />
                    <span>참고 자료</span>
                  </div>
                  <div className="space-y-1">
                    {message.resources.map((resource, i) => (
                      <a
                        key={i}
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-xs text-blue-600 hover:underline"
                      >
                        <ExternalLink className="w-3 h-3" />
                        {resource.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* Timestamp */}
              <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-white/70' : 'text-muted'}`}>
                {new Date(message.timestamp).toLocaleTimeString('ko-KR', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm p-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary animate-pulse" />
                <span className="text-muted">생각하는 중...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-gray-50">
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              rows={1}
              className="w-full px-4 py-3 border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
              style={{ maxHeight: '120px' }}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || isLoading}
            className="p-3 bg-primary text-white rounded-xl hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-muted mt-2">
          Enter로 전송, Shift+Enter로 줄바꿈
        </p>
      </div>
    </div>
  );
}
