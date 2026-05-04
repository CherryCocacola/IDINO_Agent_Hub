import axios from 'axios';
import { apiLogger } from '../logger';

// Create a dedicated AI service client with shorter timeout
const AI_SERVICE_URL = process.env.NEXT_PUBLIC_AI_API_URL || 'http://localhost:8006';
const AI_TIMEOUT = 20000; // 20 seconds timeout for LLM API calls

const aiApiClient = axios.create({
  baseURL: AI_SERVICE_URL,
  timeout: AI_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Internal network support: resolve localhost to actual browser hostname
aiApiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined' && config.baseURL) {
    const hostname = window.location.hostname;
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      config.baseURL = config.baseURL.replace('//localhost:', `//${hostname}:`);
    }
  }
  return config;
});

// Add simple logging interceptor
aiApiClient.interceptors.response.use(
  response => response,
  error => {
    apiLogger.warn(`AI Service Error: ${error.message}`, { url: error.config?.url });
    throw error;
  }
);

export interface ActionRecommendation {
  id: number;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  deadline?: string;
  competency?: string;
  reasoning?: string;
  icon_type?: 'book' | 'users' | 'award' | 'briefcase' | 'code' | 'chart';
}

export interface ActionRecommendationResponse {
  student_id: string;
  recommendations: ActionRecommendation[];
  generated_at: string;
  model_used: string;
}

// Phase 2-2: Structured Output Response from JSON Schema
export interface StructuredRecommendationResponse {
  summary: string;
  strengths: string[];
  improvements: string[];
  recommendations: ActionRecommendation[];
  alumni_insights?: string[];
}

// Phase 2-3: RAG Evidence
export interface EvidenceItem {
  source_id: string;
  source_type: 'course' | 'program' | 'alumni' | 'pattern';
  title: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
}

// Tool Calling + RAG Full Response
export interface ToolsAndRAGResponse {
  result: StructuredRecommendationResponse;
  metadata: {
    total_duration_ms: number;
    model: string;
    tool_calls_count: number;
    evidence_count: number;
  };
  tool_results: Record<string, unknown>;
  evidence: EvidenceItem[];
}

// Request types
export interface RecommendationRequest {
  student_id: string;
  task: string;
  use_rag?: boolean;
  max_tool_calls?: number;
}

export interface CompetencyScore {
  name: string;
  score: number;
  status: string;
  gap?: number;
}

export interface CompetencyAnalysisRequest {
  student_id: string;
  competencies: CompetencyScore[];
  career_goal?: string;
}

export interface CompetencyAnalysisResponse {
  student_id: string;
  analysis: string;
  strengths: string[];
  weaknesses: string[];
  improvement_suggestions: string[];
  generated_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  student_id: string;
  message: string;
  history?: ChatMessage[];
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  student_id: string;
  response: string;
  suggestions: string[];
  generated_at: string;
}

export interface HeatStripData {
  name: string;
  monthly_scores: number[];
  color: string;
  trend: 'up' | 'down' | 'stable';
}

export interface HeatStripResponse {
  student_id: string;
  competencies: HeatStripData[];
  period: string;
  generated_at: string;
}

export interface SemesterGoal {
  label: string;
  completed: boolean;
  priority: 'high' | 'medium' | 'low';
}

export interface SemesterSprintResponse {
  student_id: string;
  semester: string;
  goals: SemesterGoal[];
  completion_rate: number;
  ai_suggestions: string[];
  generated_at: string;
}

export const aiService = {
  /**
   * AI 기반 액션 추천 조회
   */
  async getActionRecommendations(studentId: string): Promise<ActionRecommendationResponse> {
    const response = await aiApiClient.get<ActionRecommendationResponse>(
      `/ai/actions/${studentId}`
    );
    return response.data;
  },

  /**
   * 역량 분석 요청
   */
  async analyzeCompetencies(request: CompetencyAnalysisRequest): Promise<CompetencyAnalysisResponse> {
    const response = await aiApiClient.post<CompetencyAnalysisResponse>(
      `/ai/analyze`,
      request
    );
    return response.data;
  },

  /**
   * AI 챗봇 대화
   */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const response = await aiApiClient.post<ChatResponse>(
      `/ai/chat`,
      request
    );
    return response.data;
  },

  /**
   * 역량 변화 히트맵 데이터 조회
   */
  async getHeatStripData(studentId: string): Promise<HeatStripResponse> {
    const response = await aiApiClient.get<HeatStripResponse>(
      `/ai/heatstrip/${studentId}`
    );
    return response.data;
  },

  /**
   * 학기 스프린트 목표 조회
   */
  async getSemesterSprint(studentId: string): Promise<SemesterSprintResponse> {
    const response = await aiApiClient.get<SemesterSprintResponse>(
      `/ai/sprint/${studentId}`
    );
    return response.data;
  },

  /**
   * 서비스 상태 확인
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await aiApiClient.get(`/health`);
    return response.data;
  },

  /**
   * Phase 2-1: Tool Calling 기반 추천
   */
  async getRecommendationsWithTools(
    studentId: string,
    task: string = '맞춤형 취업 역량 개발 추천을 생성해주세요'
  ): Promise<ToolsAndRAGResponse> {
    const response = await aiApiClient.post<ToolsAndRAGResponse>(
      `/ai/recommendations/tools`,
      { student_id: studentId, task, use_rag: false }
    );
    return response.data;
  },

  /**
   * Phase 2-3: RAG + Tool Calling 통합 추천
   */
  async getRecommendationsWithRAG(
    studentId: string,
    task: string = '맞춤형 취업 역량 개발 추천을 생성해주세요'
  ): Promise<ToolsAndRAGResponse> {
    const response = await aiApiClient.post<ToolsAndRAGResponse>(
      `/ai/recommendations/rag`,
      { student_id: studentId, task, use_rag: true }
    );
    return response.data;
  },

  /**
   * 역량 점수 조회 (competency-service에서)
   */
  async getCompetencyScores(studentId: string): Promise<{
    scores: Array<{ name: string; value: number; color: string }>;
    totalScore: number;
  }> {
    // Colors for competencies
    const colors = ['#5b6dff', '#00b7a8', '#ff8a5c', '#f6c343', '#9b59b6', '#3498db'];

    try {
      const competencyHost = typeof window !== 'undefined'
        && window.location.hostname !== 'localhost'
        && window.location.hostname !== '127.0.0.1'
        ? window.location.hostname : 'localhost';
      const response = await axios.get(
        `http://${competencyHost}:8003/competency/${studentId}/scores`
      );

      // Transform backend response to expected format
      const competencies = Array.isArray(response.data) ? response.data : response.data?.value || [];

      if (competencies.length === 0) {
        throw new Error('No competency data');
      }

      // Calculate total as SUM (not average) - raw scores
      const totalScore = competencies.reduce((sum: number, c: { current_score?: number }) =>
        sum + (c.current_score || 0), 0);

      const scores = competencies.map((c: { competency_nm?: string; current_score?: number }, index: number) => ({
        name: c.competency_nm || `역량 ${index + 1}`,
        value: c.current_score || 0,
        color: colors[index % colors.length],
      }));

      return { scores, totalScore };
    } catch (error) {
      // No fallback - let caller handle the error
      throw error;
    }
  },
};
