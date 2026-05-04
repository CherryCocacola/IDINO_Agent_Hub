import { skillApi } from './client';
import type {
  StudentSkillResponse,
  StudentSkillUpdate,
  SkillGraphResponse,
  GapAnalysisResponse,
  RoleRequirementResponse,
  SkillResponse,
} from '@/types';

export const skillService = {
  // Get student's skills
  getStudentSkills: async (studentId: string): Promise<StudentSkillResponse[]> => {
    const response = await skillApi.get(`/skills/student/${studentId}`);
    return response.data;
  },

  // Get single student skill
  getStudentSkill: async (studentId: string, skillCd: string): Promise<StudentSkillResponse> => {
    const response = await skillApi.get(`/skills/student/${studentId}/${skillCd}`);
    return response.data;
  },

  // Update student skill
  updateStudentSkill: async (
    studentId: string,
    skillCd: string,
    data: StudentSkillUpdate
  ): Promise<StudentSkillResponse> => {
    const response = await skillApi.patch(`/skills/student/${studentId}/${skillCd}`, data);
    return response.data;
  },

  // Get skill graph for visualization
  getSkillGraph: async (roleCd?: string): Promise<SkillGraphResponse> => {
    const url = roleCd ? `/skills/graph?role_cd=${roleCd}` : '/skills/graph';
    const response = await skillApi.get(url);
    return response.data;
  },

  // Get student skill graph (with student's current levels)
  getStudentSkillGraph: async (studentId: string, roleCd?: string): Promise<SkillGraphResponse> => {
    const url = roleCd
      ? `/skills/graph/student/${studentId}?role_cd=${roleCd}`
      : `/skills/graph/student/${studentId}`;
    const response = await skillApi.get(url);
    return response.data;
  },

  // Get gap analysis
  getGapAnalysis: async (studentId: string, roleCd: string): Promise<GapAnalysisResponse> => {
    const response = await skillApi.get(`/skills/gap-analysis/${studentId}/${roleCd}`);
    return response.data;
  },

  // Get role requirements
  getRoleRequirements: async (roleCd: string): Promise<RoleRequirementResponse> => {
    const response = await skillApi.get(`/skills/role/${roleCd}/requirements`);
    return response.data;
  },

  // Get all roles
  getRoles: async (): Promise<Array<{ role_cd: string; role_nm: string; industry?: string }>> => {
    const response = await skillApi.get('/skills/roles');
    return response.data;
  },

  // Get roles relevant to student's department
  getStudentRoles: async (studentId: string): Promise<Array<{ role_cd: string; role_nm: string; industry?: string }>> => {
    const response = await skillApi.get(`/skills/roles/student/${studentId}`);
    return response.data;
  },

  // Get skill by code
  getSkill: async (skillCd: string): Promise<SkillResponse> => {
    const response = await skillApi.get(`/skills/${skillCd}`);
    return response.data;
  },

  // Search skills
  searchSkills: async (query: string, category?: string): Promise<SkillResponse[]> => {
    const params = new URLSearchParams({ q: query });
    if (category) params.append('category', category);
    const response = await skillApi.get(`/skills/search?${params}`);
    return response.data;
  },

  // Get skill categories
  getCategories: async (): Promise<string[]> => {
    const response = await skillApi.get('/skills/categories');
    return response.data;
  },
};
