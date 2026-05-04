// Roadmap Types - matches roadmap-service (port 8015) schemas

export type RoadmapItemType =
  | 'course'
  | 'activity'
  | 'certificate'
  | 'internship'
  | 'project';

export type RoadmapItemStatus =
  | 'planned'
  | 'in_progress'
  | 'completed'
  | 'skipped';

// Roadmap Item
export interface RoadmapItemResponse {
  item_id: string;
  item_type: RoadmapItemType;
  title: string;
  description?: string;
  grade_level: number;  // 1-4
  semester: number;     // 1-2
  status: RoadmapItemStatus;
  priority: number;     // 1-3
  competency_contributions?: Record<string, number>;
  skill_contributions?: Record<string, number>;
  prerequisites?: string[];
  deadline?: string;
  is_ai_recommended: boolean;
  recommendation_reason?: string;
}

// Semester Roadmap
export interface SemesterRoadmap {
  semester: number;  // 1-2
  items: RoadmapItemResponse[];
  total_credits: number;
  target_gpa?: number;
  key_milestones: string[];
}

// Grade Roadmap
export interface GradeRoadmapResponse {
  student_id: string;
  grade_level: number;  // 1-4
  grade_name: string;
  semesters: SemesterRoadmap[];
  competency_targets: Record<string, number>;
  skill_targets: Record<string, number>;
  career_path?: string;
  completion_rate: number;
}

// Full Roadmap
export interface FullRoadmapResponse {
  student_id: string;
  roadmaps: GradeRoadmapResponse[];
  overall_completion: number;
  current_grade: number;
  current_semester: number;
}

// Generate Request
export interface RoadmapGenerateRequest {
  student_id: string;
  target_role?: string;
  career_goal?: string;
  preferences?: Record<string, unknown>;
  constraints?: Record<string, unknown>;
}

// Generate Response
export interface RoadmapGenerateResponse {
  student_id: string;
  roadmaps: GradeRoadmapResponse[];
  ai_summary: string;
  key_recommendations: string[];
  alternative_paths: Array<Record<string, unknown>>;
  confidence_score: number;  // 0.0 - 1.0
}

// Item Update Request
export interface RoadmapItemUpdate {
  status?: RoadmapItemStatus;
  priority?: number;
  deadline?: string;
  notes?: string;
}

// Helper
export const ROADMAP_ITEM_TYPE_LABELS: Record<RoadmapItemType, string> = {
  course: '강의',
  activity: '활동',
  certificate: '자격증',
  internship: '인턴십',
  project: '프로젝트',
};

export const ROADMAP_ITEM_TYPE_ICONS: Record<RoadmapItemType, string> = {
  course: '📚',
  activity: '🎯',
  certificate: '📜',
  internship: '💼',
  project: '💻',
};

export const ROADMAP_STATUS_LABELS: Record<RoadmapItemStatus, string> = {
  planned: '계획됨',
  in_progress: '진행 중',
  completed: '완료',
  skipped: '건너뜀',
};

export const ROADMAP_STATUS_COLORS: Record<RoadmapItemStatus, string> = {
  planned: '#6b7280',     // gray-500
  in_progress: '#3b82f6', // blue-500
  completed: '#22c55e',   // green-500
  skipped: '#ef4444',     // red-500
};

export const GRADE_NAMES: Record<number, string> = {
  1: '1학년',
  2: '2학년',
  3: '3학년',
  4: '4학년',
};

export const SEMESTER_NAMES: Record<number, string> = {
  1: '1학기',
  2: '2학기',
};
