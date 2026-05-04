import { advisorApi } from './client';
import type {
  CohortDashboard,
  AdvisorAssignmentResponse,
  InterventionResponse,
  InterventionCreate,
  InterventionUpdate,
  AdvisorNoteResponse,
  AdvisorNoteCreate,
  CohortSnapshotResponse,
  InterventionType,
  InterventionStatus,
  MeetingCreate,
  MeetingUpdate,
  MeetingResponse,
} from '@/types';
import type { StudentSummary } from '@/types/advisor';

export const advisorService = {
  // ==================== Dashboard ====================

  // Get cohort dashboard
  getDashboard: async (advisorId: string): Promise<CohortDashboard> => {
    const response = await advisorApi.get(`/advisor/dashboard/${advisorId}`);
    return response.data;
  },

  // Get cohort analytics only
  getCohortAnalytics: async (advisorId: string): Promise<CohortDashboard['analytics']> => {
    const response = await advisorApi.get(`/advisor/analytics/${advisorId}`);
    return response.data;
  },

  // ==================== Students ====================

  // Get advisor's students
  getStudents: async (advisorId: string): Promise<StudentSummary[]> => {
    const response = await advisorApi.get(`/advisor/students/${advisorId}`);
    return response.data;
  },

  // Get students needing attention
  getStudentsNeedingAttention: async (advisorId: string): Promise<StudentSummary[]> => {
    const response = await advisorApi.get(`/advisor/students/${advisorId}/attention`);
    return response.data;
  },

  // Get student detail
  getStudentDetail: async (
    advisorId: string,
    studentId: string
  ): Promise<StudentSummary & { history: Array<Record<string, unknown>> }> => {
    const response = await advisorApi.get(`/advisor/${advisorId}/student/${studentId}`);
    return response.data;
  },

  // ==================== Assignments ====================

  // Get advisor assignments
  getAssignments: async (advisorId: string): Promise<AdvisorAssignmentResponse[]> => {
    const response = await advisorApi.get(`/advisor/assignments/${advisorId}`);
    return response.data;
  },

  // Assign student to advisor
  assignStudent: async (
    advisorId: string,
    studentId: string,
    isPrimary = true
  ): Promise<AdvisorAssignmentResponse> => {
    const response = await advisorApi.post('/advisor/assignments', {
      advisor_id: advisorId,
      student_id: studentId,
      is_primary: isPrimary,
    });
    return response.data;
  },

  // Remove assignment
  removeAssignment: async (assignmentId: string): Promise<void> => {
    await advisorApi.delete(`/advisor/assignments/${assignmentId}`);
  },

  // ==================== Interventions ====================

  // Get advisor's interventions
  getInterventions: async (
    advisorId: string,
    status?: InterventionStatus,
    type?: InterventionType
  ): Promise<InterventionResponse[]> => {
    const params: Record<string, string> = {};
    if (status) params.status = status;
    if (type) params.type = type;
    const response = await advisorApi.get(`/advisor/interventions/${advisorId}`, { params });
    return response.data;
  },

  // Get interventions for a student
  getStudentInterventions: async (
    advisorId: string,
    studentId: string
  ): Promise<InterventionResponse[]> => {
    const response = await advisorApi.get(
      `/advisor/${advisorId}/student/${studentId}/interventions`
    );
    return response.data;
  },

  // Get single intervention
  getIntervention: async (interventionId: string): Promise<InterventionResponse> => {
    const response = await advisorApi.get(`/advisor/interventions/detail/${interventionId}`);
    return response.data;
  },

  // Create intervention
  createIntervention: async (data: InterventionCreate): Promise<InterventionResponse> => {
    const response = await advisorApi.post('/advisor/interventions', data);
    return response.data;
  },

  // Update intervention
  updateIntervention: async (
    interventionId: string,
    data: InterventionUpdate
  ): Promise<InterventionResponse> => {
    const response = await advisorApi.patch(
      `/advisor/interventions/${interventionId}`,
      data
    );
    return response.data;
  },

  // Complete intervention
  completeIntervention: async (
    interventionId: string,
    outcome: string,
    followUpNeeded = false,
    nextAction?: string
  ): Promise<InterventionResponse> => {
    const response = await advisorApi.post(
      `/advisor/interventions/${interventionId}/complete`,
      {
        outcome,
        follow_up_needed: followUpNeeded,
        next_action: nextAction,
      }
    );
    return response.data;
  },

  // Cancel intervention
  cancelIntervention: async (interventionId: string): Promise<InterventionResponse> => {
    const response = await advisorApi.post(`/advisor/interventions/${interventionId}/cancel`);
    return response.data;
  },

  // ==================== Notes ====================

  // Get notes for a student
  getStudentNotes: async (
    advisorId: string,
    studentId: string
  ): Promise<AdvisorNoteResponse[]> => {
    const response = await advisorApi.get(`/advisor/${advisorId}/student/${studentId}/notes`);
    return response.data;
  },

  // Create note
  createNote: async (data: AdvisorNoteCreate): Promise<AdvisorNoteResponse> => {
    const response = await advisorApi.post('/advisor/notes', data);
    return response.data;
  },

  // Update note
  updateNote: async (
    noteId: string,
    content: string
  ): Promise<AdvisorNoteResponse> => {
    const response = await advisorApi.patch(`/advisor/notes/${noteId}`, { content });
    return response.data;
  },

  // Delete note
  deleteNote: async (noteId: string): Promise<void> => {
    await advisorApi.delete(`/advisor/notes/${noteId}`);
  },

  // ==================== Snapshots ====================

  // Get cohort snapshots
  getCohortSnapshots: async (
    advisorId: string,
    limit = 10
  ): Promise<CohortSnapshotResponse[]> => {
    const response = await advisorApi.get(`/advisor/snapshots/${advisorId}?limit=${limit}`);
    return response.data;
  },

  // Take cohort snapshot
  takeCohortSnapshot: async (advisorId: string): Promise<CohortSnapshotResponse> => {
    const response = await advisorApi.post(`/advisor/snapshots/${advisorId}`);
    return response.data;
  },

  // ==================== Meetings ====================

  // Get advisor's meetings
  getMeetings: async (advisorId: string): Promise<MeetingResponse[]> => {
    const response = await advisorApi.get(`/advisor/meetings/${advisorId}`);
    return response.data;
  },

  // Get single meeting
  getMeeting: async (meetingId: string): Promise<MeetingResponse> => {
    const response = await advisorApi.get(`/advisor/meetings/detail/${meetingId}`);
    return response.data;
  },

  // Create meeting
  createMeeting: async (data: MeetingCreate): Promise<MeetingResponse> => {
    const response = await advisorApi.post('/advisor/meetings', data);
    return response.data;
  },

  // Update meeting
  updateMeeting: async (meetingId: string, data: MeetingUpdate): Promise<MeetingResponse> => {
    const response = await advisorApi.patch(`/advisor/meetings/${meetingId}`, data);
    return response.data;
  },

  // Complete meeting
  completeMeeting: async (meetingId: string, notes?: string): Promise<MeetingResponse> => {
    const response = await advisorApi.patch(
      `/advisor/meetings/${meetingId}/complete`,
      { notes }
    );
    return response.data;
  },

  // Cancel meeting
  cancelMeeting: async (meetingId: string, reason?: string): Promise<MeetingResponse> => {
    const response = await advisorApi.post(`/advisor/meetings/${meetingId}/cancel`, { reason });
    return response.data;
  },
};
