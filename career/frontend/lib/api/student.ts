import { studentApi } from './client';
import type {
  StudentDetail,
  EnrollmentWithGrade,
  Participation,
  Achievement,
  DashboardSummary,
  CourseRecord,
  Activity,
  convertEnrollmentToCourse,
  convertParticipationToActivity,
} from '@/types';

export const studentService = {
  // Get student profile with detailed information
  getStudent: async (studentId: string): Promise<StudentDetail> => {
    const response = await studentApi.get(`/students/${studentId}`);
    return response.data;
  },

  // Get student dashboard (all data in one call)
  getDashboard: async (studentId: string): Promise<DashboardSummary> => {
    const response = await studentApi.get(`/students/${studentId}/dashboard`);
    return response.data;
  },

  // Get student enrollments with grades
  getEnrollments: async (studentId: string): Promise<EnrollmentWithGrade[]> => {
    const response = await studentApi.get(`/students/${studentId}/enrollments`);
    return response.data;
  },

  // Get student courses (alias for enrollments - legacy support)
  getCourses: async (studentId: string): Promise<CourseRecord[]> => {
    const response = await studentApi.get(`/students/${studentId}/courses`);
    const enrollments: EnrollmentWithGrade[] = response.data;
    // Convert to legacy format
    return enrollments.map((e, idx) => ({
      id: idx + 1,
      student_id: studentId,
      course_code: e.course_cd,
      course_name: e.course_nm,
      semester: `${e.academic_year}-${e.semester}`,
      credits: e.credits,
      grade: e.letter_grade || '',
      grade_point: e.grade_point || 0,
      course_type: '',
    }));
  },

  // Get student program participations (activities)
  getParticipations: async (studentId: string): Promise<Participation[]> => {
    const response = await studentApi.get(`/students/${studentId}/activities`);
    return response.data;
  },

  // Get student activities (legacy format)
  getActivities: async (studentId: string): Promise<Activity[]> => {
    const response = await studentApi.get(`/students/${studentId}/activities`);
    const participations: Participation[] = response.data;
    // Convert to legacy format
    return participations.map((p, idx) => ({
      id: idx + 1,
      student_id: p.student_id,
      activity_name: p.program?.program_nm || '',
      activity_type: p.program?.program_type || '',
      status: 'completed',
      hours_completed: p.hours_completed,
    }));
  },

  // Get student achievements
  getAchievements: async (studentId: string): Promise<Achievement[]> => {
    const response = await studentApi.get(`/students/${studentId}/achievements`);
    return response.data;
  },

  // Get department curriculum
  getCurriculum: async (departmentId: string) => {
    const response = await studentApi.get(`/curriculum/${departmentId}`);
    return response.data;
  },

  // List all students (with optional filters)
  listStudents: async (params?: {
    department_id?: string;
    grade?: number;
    skip?: number;
    limit?: number;
  }) => {
    const response = await studentApi.get('/students', { params });
    return response.data;
  },
};
