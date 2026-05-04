'use client';

import { useState, useEffect, useCallback } from 'react';
import { advisorService } from '@/lib/api/advisor';
import type {
  AdvisorDashboardResponse,
  StudentSummaryResponse,
  MeetingResponse,
  MeetingCreate,
  MeetingUpdate,
  NoteCreate,
} from '@/types';

interface AdvisorState {
  dashboard: AdvisorDashboardResponse | null;
  students: StudentSummaryResponse[];
  meetings: MeetingResponse[];
  loading: boolean;
  error: string | null;
}

const initialState: AdvisorState = {
  dashboard: null,
  students: [],
  meetings: [],
  loading: true,
  error: null,
};

export function useAdvisor(advisorId: string | null) {
  const [state, setState] = useState<AdvisorState>(initialState);

  // Fetch advisor data
  const fetchDashboard = useCallback(async () => {
    if (!advisorId) {
      setState(prev => ({ ...prev, loading: false }));
      return;
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const [dashboard, students, meetings] = await Promise.all([
        advisorService.getDashboard(advisorId),
        advisorService.getStudents(advisorId),
        advisorService.getMeetings(advisorId),
      ]);

      setState({
        dashboard,
        students,
        meetings,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Advisor fetch error:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: '지도교수 데이터를 불러오는데 실패했습니다.',
      }));
    }
  }, [advisorId]);

  // Get student details
  const getStudentDetails = useCallback(async (studentId: string) => {
    if (!advisorId) throw new Error('Advisor ID is required');
    return advisorService.getStudentDetail(advisorId, studentId);
  }, [advisorId]);

  // Get students by risk level
  const getStudentsByRisk = useCallback((riskLevel?: 'high' | 'medium' | 'low') => {
    if (!riskLevel) return state.students;
    return state.students.filter(s => s.risk_level === riskLevel);
  }, [state.students]);

  // Create meeting
  const createMeeting = useCallback(async (data: MeetingCreate) => {
    const meeting = await advisorService.createMeeting(data);
    setState(prev => ({
      ...prev,
      meetings: [meeting, ...prev.meetings],
    }));
    return meeting;
  }, []);

  // Update meeting
  const updateMeeting = useCallback(async (meetingId: string, data: MeetingUpdate) => {
    const updated = await advisorService.updateMeeting(meetingId, data);
    setState(prev => ({
      ...prev,
      meetings: prev.meetings.map(m => m.meeting_id === meetingId ? updated : m),
    }));
    return updated;
  }, []);

  // Complete meeting
  const completeMeeting = useCallback(async (meetingId: string, notes?: string) => {
    const updated = await advisorService.completeMeeting(meetingId, notes);
    setState(prev => ({
      ...prev,
      meetings: prev.meetings.map(m => m.meeting_id === meetingId ? updated : m),
    }));
    return updated;
  }, []);

  // Cancel meeting
  const cancelMeeting = useCallback(async (meetingId: string, reason?: string) => {
    const updated = await advisorService.cancelMeeting(meetingId, reason);
    setState(prev => ({
      ...prev,
      meetings: prev.meetings.map(m => m.meeting_id === meetingId ? updated : m),
    }));
    return updated;
  }, []);

  // Create note for student
  const createNote = useCallback(async (data: NoteCreate) => {
    return advisorService.createNote(data);
  }, []);

  // Get student notes
  const getStudentNotes = useCallback(async (studentId: string) => {
    if (!advisorId) throw new Error('Advisor ID is required');
    return advisorService.getStudentNotes(advisorId, studentId);
  }, [advisorId]);

  // Get upcoming meetings
  const getUpcomingMeetings = useCallback(() => {
    return state.meetings.filter(m => m.status === 'scheduled');
  }, [state.meetings]);

  // Get high risk students
  const getHighRiskStudents = useCallback(() => {
    return state.students.filter(s => s.risk_level === 'high');
  }, [state.students]);

  // Initial fetch
  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    ...state,
    refetch: fetchDashboard,
    getStudentDetails,
    getStudentsByRisk,
    createMeeting,
    updateMeeting,
    completeMeeting,
    cancelMeeting,
    createNote,
    getStudentNotes,
    getUpcomingMeetings,
    getHighRiskStudents,
  };
}
