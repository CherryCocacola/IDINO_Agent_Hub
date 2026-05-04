// Advisor Types - matches advisor-service (port 8014) schemas

export type InterventionType =
  | 'meeting'    // 상담
  | 'email'      // 이메일
  | 'referral'   // 의뢰/연계
  | 'resource'   // 자료 제공
  | 'followup';  // 후속 조치

export type InterventionStatus =
  | 'planned'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

// Advisor Assignment
export interface AdvisorAssignmentResponse {
  assignment_id: string;
  advisor_id: string;
  advisor_name?: string;
  student_id: string;
  student_name?: string;
  assigned_at: string;
  is_primary: boolean;
  notes?: string;
}

// Intervention
export interface InterventionCreate {
  advisor_id: string;
  student_id: string;
  intervention_type: InterventionType;
  title: string;
  description?: string;
  scheduled_at?: string;
  priority?: number;  // 1-5
}

export interface InterventionUpdate {
  status?: InterventionStatus;
  outcome?: string;
  completed_at?: string;
  follow_up_needed?: boolean;
  next_action?: string;
}

export interface InterventionResponse {
  intervention_id: string;
  advisor_id: string;
  student_id: string;
  student_name?: string;
  intervention_type: InterventionType;
  title: string;
  description?: string;
  status: InterventionStatus;
  scheduled_at?: string;
  completed_at?: string;
  outcome?: string;
  follow_up_needed: boolean;
  next_action?: string;
  priority: number;
  created_at: string;
}

// Cohort Snapshot
export interface CohortSnapshotResponse {
  snapshot_id: string;
  advisor_id: string;
  snapshot_date: string;
  total_students: number;
  at_risk_count: number;
  on_track_count: number;
  excelling_count: number;
  avg_gpa: number;
  avg_progress: number;
  key_metrics: Record<string, unknown>;
  created_at: string;
}

// Advisor Note
export interface AdvisorNoteCreate {
  advisor_id: string;
  student_id: string;
  note_type?: string;
  content: string;
  is_private?: boolean;
  tags?: string[];
}

export interface AdvisorNoteResponse {
  note_id: string;
  advisor_id: string;
  student_id: string;
  student_name?: string;
  note_type: string;
  content: string;
  is_private: boolean;
  tags?: string[];
  created_at: string;
  updated_at?: string;
}

// Student Summary
export interface StudentSummary {
  student_id: string;
  student_name: string;
  major?: string;
  grade: number;
  gpa: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  active_alerts: number;
  last_interaction?: string;
  progress_percentage: number;
  needs_attention: boolean;
}

// Cohort Analytics
export interface CohortAnalytics {
  total_students: number;
  by_risk_level: Record<string, number>;
  by_grade: Record<number, number>;
  avg_gpa: number;
  avg_progress: number;
  interventions_this_month: number;
  pending_followups: number;
}

// Cohort Dashboard
export interface CohortDashboard {
  advisor_id: string;
  advisor_name?: string;
  analytics: CohortAnalytics;
  students_needing_attention: StudentSummary[];
  recent_interventions: InterventionResponse[];
  upcoming_interventions: InterventionResponse[];
  recent_notes: AdvisorNoteResponse[];
  generated_at: string;
}

// Meeting Types
export type MeetingStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled';

export interface MeetingCreate {
  advisor_id: string;
  student_id: string;
  title: string;
  description?: string;
  scheduled_at: string;
  duration_minutes?: number;
  location?: string;
  meeting_type?: 'in_person' | 'video' | 'phone';
}

export interface MeetingUpdate {
  title?: string;
  description?: string;
  scheduled_at?: string;
  duration_minutes?: number;
  location?: string;
  meeting_type?: 'in_person' | 'video' | 'phone';
  status?: MeetingStatus;
  notes?: string;
}

export interface MeetingResponse {
  meeting_id: string;
  advisor_id: string;
  student_id: string;
  student_name?: string;
  title: string;
  description?: string;
  scheduled_at: string;
  duration_minutes: number;
  location?: string;
  meeting_type: 'in_person' | 'video' | 'phone';
  status: MeetingStatus;
  notes?: string;
  completed_at?: string;
  created_at: string;
}

// Type aliases for backward compatibility
export type AdvisorDashboardResponse = CohortDashboard;
export type StudentSummaryResponse = StudentSummary;
export type NoteCreate = AdvisorNoteCreate;
export type NoteResponse = AdvisorNoteResponse;

// Helper
export const INTERVENTION_TYPE_LABELS: Record<InterventionType, string> = {
  meeting: '상담',
  email: '이메일',
  referral: '의뢰/연계',
  resource: '자료 제공',
  followup: '후속 조치',
};

export const INTERVENTION_STATUS_LABELS: Record<InterventionStatus, string> = {
  planned: '예정',
  in_progress: '진행 중',
  completed: '완료',
  cancelled: '취소',
};

export const INTERVENTION_TYPE_ICONS: Record<InterventionType, string> = {
  meeting: '👥',
  email: '📧',
  referral: '🔗',
  resource: '📁',
  followup: '🔄',
};
