// Coaching Types - matches coaching-service (port 8009) schemas

export type GoalStatus = 'draft' | 'active' | 'paused' | 'completed' | 'abandoned';
export type GoalPriority = 'high' | 'medium' | 'low';
export type CheckinMood = 'great' | 'good' | 'neutral' | 'struggling' | 'blocked';

// Goal
export interface GoalBase {
  title: string;
  description?: string;
  goal_type: 'career' | 'skill' | 'academic' | 'personal';
  priority: GoalPriority;
  target_date?: string;
  target_role_cd?: string;
  related_skills?: string[];
  success_criteria?: string;
  motivation?: string;
}

export interface GoalCreate extends GoalBase {
  student_id: string;
}

export interface GoalUpdate {
  title?: string;
  description?: string;
  goal_type?: string;
  priority?: GoalPriority;
  status?: GoalStatus;
  target_date?: string;
  target_role_cd?: string;
  related_skills?: string[];
  success_criteria?: string;
  motivation?: string;
  progress_percentage?: number;
}

export interface GoalResponse extends GoalBase {
  goal_id: string;
  student_id: string;
  status: GoalStatus;
  progress_percentage: number;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  plan_items_count: number;
  completed_items_count: number;
  checkins_count: number;
  last_checkin_at?: string;
}

// Plan Item
export interface PlanItemBase {
  title: string;
  description?: string;
  order_index: number;
  due_date?: string;
  estimated_hours?: number;
  related_skill_cd?: string;
}

export interface PlanItemCreate extends PlanItemBase {
  goal_id: string;
}

export interface PlanItemUpdate {
  title?: string;
  description?: string;
  order_index?: number;
  due_date?: string;
  estimated_hours?: number;
  actual_hours?: number;
  is_completed?: boolean;
  completed_at?: string;
  notes?: string;
}

export interface PlanItemResponse extends PlanItemBase {
  plan_id: string;
  goal_id: string;
  is_completed: boolean;
  completed_at?: string;
  actual_hours?: number;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

// Check-in
export interface CheckinBase {
  mood: CheckinMood;
  progress_note?: string;
  blockers?: string;
  next_steps?: string;
  reflection?: string;
}

export interface CheckinCreate extends CheckinBase {
  goal_id: string;
}

export interface CheckinResponse extends CheckinBase {
  checkin_id: string;
  goal_id: string;
  goal_title?: string;
  ai_feedback?: string;
  ai_suggestions?: string[];
  created_at: string;
}

// Retrospective
export interface RetrospectiveBase {
  what_went_well?: string;
  what_could_improve?: string;
  lessons_learned?: string;
  next_goals?: string;
  satisfaction_rating: number; // 1-5
}

export interface RetrospectiveCreate extends RetrospectiveBase {
  goal_id: string;
}

export interface RetrospectiveResponse extends RetrospectiveBase {
  retrospective_id: string;
  goal_id: string;
  goal_title?: string;
  ai_analysis?: string;
  ai_recommendations?: string[];
  created_at: string;
}

// Coaching Session
export interface CoachingSessionResponse {
  goal: GoalResponse;
  plan_items: PlanItemResponse[];
  recent_checkins: CheckinResponse[];
  retrospective?: RetrospectiveResponse;
  ai_insights?: Record<string, unknown>;
}

// AI Coach
export interface AICoachRequest {
  student_id: string;
  goal_id?: string;
  query_type: 'advice' | 'plan_suggest' | 'motivation' | 'blockers' | 'review';
  context?: string;
  include_history?: boolean;
}

export interface AICoachResponse {
  message: string;
  suggestions: string[];
  recommended_actions: string[];
  resources: Array<{ title: string; url: string }>;
  follow_up_questions: string[];
  generated_at: string;
}

// Goal Progress Summary
export interface GoalProgressSummary {
  student_id: string;
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  average_progress: number;
  total_checkins: number;
  streak_days: number;
  goals: GoalResponse[];
  recent_activity: Array<Record<string, unknown>>;
}

// Chat message for UI
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  suggestions?: string[];
  resources?: Array<{ title: string; url: string }>;
}
