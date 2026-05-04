// Sprint Types - for semester sprint board UI

export type SprintStatus = 'todo' | 'in_progress' | 'done';
export type SprintItemType = 'course' | 'activity' | 'goal' | 'skill' | 'custom';
export type SprintPriority = 'high' | 'medium' | 'low';

export interface SprintItem {
  id: string;
  title: string;
  description?: string;
  item_type: SprintItemType;
  status: SprintStatus;
  priority: SprintPriority;
  due_date?: string;
  estimated_hours?: number;
  actual_hours?: number;
  related_goal_id?: string;
  related_skill_cd?: string;
  tags?: string[];
  order_index: number;
  created_at: string;
  updated_at?: string;
}

export interface SprintWeek {
  week_number: number;
  start_date: string;
  end_date: string;
  items: SprintItem[];
  target_hours: number;
  actual_hours: number;
  completion_rate: number;
}

export interface SemesterSprint {
  sprint_id: string;
  student_id: string;
  semester: string; // e.g., "2024-1"
  start_date: string;
  end_date: string;
  weeks: SprintWeek[];
  total_items: number;
  completed_items: number;
  completion_rate: number;
  goals_linked: number;
}

export interface SprintCreateRequest {
  student_id: string;
  semester: string;
  target_hours_per_week?: number;
  auto_import_goals?: boolean;
  auto_import_courses?: boolean;
}

export interface SprintItemCreate {
  title: string;
  description?: string;
  item_type: SprintItemType;
  priority?: SprintPriority;
  due_date?: string;
  estimated_hours?: number;
  related_goal_id?: string;
  related_skill_cd?: string;
  tags?: string[];
  week_number: number;
}

export interface SprintItemUpdate {
  title?: string;
  description?: string;
  status?: SprintStatus;
  priority?: SprintPriority;
  due_date?: string;
  estimated_hours?: number;
  actual_hours?: number;
  tags?: string[];
  order_index?: number;
  week_number?: number;
}

// Kanban Board Types
export interface KanbanColumn {
  id: SprintStatus;
  title: string;
  items: SprintItem[];
}

export interface KanbanBoard {
  columns: KanbanColumn[];
  week_number: number;
  semester: string;
}

// Helper
export const SPRINT_STATUS_LABELS: Record<SprintStatus, string> = {
  todo: '할 일',
  in_progress: '진행 중',
  done: '완료',
};

export const SPRINT_ITEM_TYPE_LABELS: Record<SprintItemType, string> = {
  course: '강의',
  activity: '활동',
  goal: '목표',
  skill: '스킬',
  custom: '기타',
};

export const SPRINT_PRIORITY_LABELS: Record<SprintPriority, string> = {
  high: '높음',
  medium: '보통',
  low: '낮음',
};

export const SPRINT_PRIORITY_COLORS: Record<SprintPriority, string> = {
  high: '#ef4444',    // red-500
  medium: '#f59e0b',  // amber-500
  low: '#22c55e',     // green-500
};
