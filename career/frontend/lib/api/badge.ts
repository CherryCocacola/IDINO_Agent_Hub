import { badgeApi } from './client';
import type {
  BadgeResponse,
  StudentBadgeResponse,
  BadgeAwardRequest,
  SkillPassportResponse,
  PassportShareRequest,
  PassportShareResponse,
  BadgeCategory,
  CredentialResponse,
} from '@/types';

export const badgeService = {
  // ==================== Badges ====================

  // Get all badges
  getAllBadges: async (category?: BadgeCategory): Promise<BadgeResponse[]> => {
    const params = category ? { category } : {};
    const response = await badgeApi.get('/badges', { params });
    return response.data;
  },

  // Get single badge
  getBadge: async (badgeId: string): Promise<BadgeResponse> => {
    const response = await badgeApi.get(`/badges/${badgeId}`);
    return response.data;
  },

  // Get badge by code
  getBadgeByCode: async (badgeCd: string): Promise<BadgeResponse> => {
    const response = await badgeApi.get(`/badges/code/${badgeCd}`);
    return response.data;
  },

  // ==================== Student Badges ====================

  // Get student's badges
  getStudentBadges: async (studentId: string): Promise<StudentBadgeResponse[]> => {
    const response = await badgeApi.get(`/badges/student/${studentId}`);
    return response.data;
  },

  // Get student's credentials (certifications, licenses, awards)
  getStudentCredentials: async (studentId: string): Promise<CredentialResponse[]> => {
    const response = await badgeApi.get(`/badges/student/${studentId}/credentials`);
    return response.data;
  },

  // Award badge to student
  awardBadge: async (data: BadgeAwardRequest): Promise<StudentBadgeResponse> => {
    const response = await badgeApi.post('/badges/award', data);
    return response.data;
  },

  // Revoke badge from student
  revokeBadge: async (studentBadgeId: string): Promise<void> => {
    await badgeApi.delete(`/badges/student-badges/${studentBadgeId}`);
  },

  // Toggle badge visibility
  toggleBadgeVisibility: async (
    studentBadgeId: string,
    isPublic: boolean
  ): Promise<StudentBadgeResponse> => {
    const response = await badgeApi.patch(`/badges/student-badges/${studentBadgeId}`, {
      is_public: isPublic,
    });
    return response.data;
  },

  // ==================== Skill Passport ====================

  // Get student's skill passport
  getPassport: async (studentId: string): Promise<SkillPassportResponse> => {
    const response = await badgeApi.get(`/passport/${studentId}`);
    return response.data;
  },

  // Generate/refresh passport
  generatePassport: async (studentId: string): Promise<SkillPassportResponse> => {
    const response = await badgeApi.post(`/passport/${studentId}/generate`);
    return response.data;
  },

  // Share passport
  sharePassport: async (data: PassportShareRequest): Promise<PassportShareResponse> => {
    const response = await badgeApi.post('/passport/share', data);
    return response.data;
  },

  // Get shared passport (public view)
  getSharedPassport: async (shareId: string): Promise<SkillPassportResponse> => {
    const response = await badgeApi.get(`/passport/shared/${shareId}`);
    return response.data;
  },

  // Revoke share link
  revokeShare: async (shareId: string): Promise<void> => {
    await badgeApi.delete(`/passport/share/${shareId}`);
  },

  // ==================== Utility ====================

  // Get badge categories
  getBadgeCategories: async (): Promise<Array<{ category: string; label: string }>> => {
    const response = await badgeApi.get('/badges/categories');
    return response.data;
  },

  // Get badge leaderboard
  getBadgeLeaderboard: async (
    limit = 10
  ): Promise<Array<{ student_id: string; student_name: string; badge_count: number; points: number }>> => {
    const response = await badgeApi.get(`/badges/leaderboard?limit=${limit}`);
    return response.data;
  },

  // Check badge eligibility
  checkBadgeEligibility: async (
    studentId: string,
    badgeCd: string
  ): Promise<{ is_eligible: boolean; missing_requirements: string[] }> => {
    const response = await badgeApi.get(`/badges/eligibility/${studentId}/${badgeCd}`);
    return response.data;
  },
};
