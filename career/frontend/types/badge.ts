// Badge Types - matches badge-service (port 8012) schemas

export type BadgeCategory =
  | 'skill'          // 스킬 마스터리
  | 'achievement'    // 성취
  | 'course'         // 강의 수료
  | 'project'        // 프로젝트 완료
  | 'certification'  // 자격증
  | 'competition'    // 공모전
  | 'community';     // 커뮤니티 기여

export type BadgeLevel = 'bronze' | 'silver' | 'gold' | 'platinum';

// Badge
export interface BadgeBase {
  badge_cd: string;
  badge_nm: string;
  description?: string;
  category: BadgeCategory;
  level: BadgeLevel;
  icon_url?: string;
  criteria?: string;
  points: number;
  related_skill_cd?: string;
  is_active: boolean;
}

export interface BadgeCreate extends BadgeBase {}

export interface BadgeResponse extends BadgeBase {
  badge_id: string;
  created_at: string;
}

// Student Badge
export interface StudentBadgeResponse {
  student_badge_id: string;
  student_id: string;
  badge_id: string;
  badge: BadgeResponse;
  earned_at: string;
  issued_by?: string;
  evidence_url?: string;
  verification_hash?: string;
  is_public: boolean;
}

export interface BadgeAwardRequest {
  student_id: string;
  badge_cd: string;
  issued_by?: string;
  evidence_url?: string;
  is_public?: boolean;
}

// Skill Credential
export interface SkillCredential {
  skill_cd: string;
  skill_nm: string;
  level: number;
  verified: boolean;
  verification_source?: string;
  verified_at?: string;
  related_badges: string[];
  evidence: string[];
}

// Credential Response (for getStudentCredentials API)
export interface CredentialResponse {
  credential_id: string;
  student_id: string;
  credential_type: 'certification' | 'license' | 'award' | 'completion';
  credential_nm: string;
  issuing_org: string;
  issue_date: string;
  expiry_date?: string;
  credential_number?: string;
  verification_url?: string;
  verified: boolean;
  related_skill_cd?: string;
  created_at: string;
}

// Skill Passport
export interface SkillPassportResponse {
  passport_id: string;
  student_id: string;
  student_name?: string;
  issued_at: string;
  updated_at: string;

  // Summary
  total_skills: number;
  verified_skills: number;
  total_badges: number;
  total_points: number;

  // Credentials
  skills: SkillCredential[];
  badges: StudentBadgeResponse[];

  // Verification
  passport_hash?: string;
  is_valid: boolean;
  share_url?: string;
}

// Passport Share
export interface PassportShareRequest {
  student_id: string;
  include_skills?: boolean;
  include_badges?: boolean;
  expiry_days?: number;  // 1-365
  recipient_email?: string;
}

export interface PassportShareResponse {
  share_id: string;
  share_url: string;
  expires_at: string;
  access_count: number;
  created_at: string;
}

// Helper
export const BADGE_LEVEL_COLORS: Record<BadgeLevel, string> = {
  bronze: '#cd7f32',    // bronze
  silver: '#c0c0c0',    // silver
  gold: '#ffd700',      // gold
  platinum: '#e5e4e2',  // platinum
};

export const BADGE_LEVEL_LABELS: Record<BadgeLevel, string> = {
  bronze: '브론즈',
  silver: '실버',
  gold: '골드',
  platinum: '플래티넘',
};

export const BADGE_CATEGORY_LABELS: Record<BadgeCategory, string> = {
  skill: '스킬 마스터리',
  achievement: '성취',
  course: '강의 수료',
  project: '프로젝트',
  certification: '자격증',
  competition: '공모전',
  community: '커뮤니티',
};

export const BADGE_CATEGORY_ICONS: Record<BadgeCategory, string> = {
  skill: '⚡',
  achievement: '🏆',
  course: '📚',
  project: '💻',
  certification: '📜',
  competition: '🥇',
  community: '🤝',
};
