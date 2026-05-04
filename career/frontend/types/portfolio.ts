// Portfolio Types - matches portfolio-service (port 8016) schemas

export type ArtifactType =
  | 'github'
  | 'notion'
  | 'blog'
  | 'website'
  | 'project'
  | 'paper'
  | 'video'
  | 'document'
  | 'other';

// Portfolio
export interface PortfolioBase {
  artifact_type: ArtifactType;
  title: string;
  url: string;
  description?: string;
  is_primary: boolean;
  tags?: string[];
  skills?: string[];
}

export interface PortfolioCreate extends PortfolioBase {
  student_id: string;
}

export interface PortfolioUpdate {
  artifact_type?: ArtifactType;
  title?: string;
  url?: string;
  description?: string;
  is_primary?: boolean;
  tags?: string[];
  skills?: string[];
}

export interface PortfolioResponse extends PortfolioBase {
  portfolio_id: string;
  student_id: string;
  created_at: string;
  updated_at?: string;
}

export interface PortfolioListResponse {
  student_id: string;
  total_count: number;
  items: PortfolioResponse[];
  primary_item?: PortfolioResponse;
}

export interface PortfolioSummaryResponse {
  student_id: string;
  total_items: number;
  by_type: Record<string, number>;
  has_primary: boolean;
  primary_url?: string;
  top_skills: string[];
  last_updated?: string;
}

export interface PortfolioTypeInfo {
  type: ArtifactType;
  display_name: string;
  description: string;
  icon: string;
}

export interface PortfolioTypesResponse {
  types: PortfolioTypeInfo[];
}

// Helper
export const ARTIFACT_TYPE_LABELS: Record<ArtifactType, string> = {
  github: 'GitHub',
  notion: 'Notion',
  blog: '블로그',
  website: '웹사이트',
  project: '프로젝트',
  paper: '논문',
  video: '영상',
  document: '문서',
  other: '기타',
};

export const ARTIFACT_TYPE_ICONS: Record<ArtifactType, string> = {
  github: '🐙',
  notion: '📝',
  blog: '✍️',
  website: '🌐',
  project: '💻',
  paper: '📄',
  video: '🎬',
  document: '📋',
  other: '📁',
};

export const ARTIFACT_TYPE_COLORS: Record<ArtifactType, string> = {
  github: '#24292e',
  notion: '#000000',
  blog: '#ff6b6b',
  website: '#4dabf7',
  project: '#69db7c',
  paper: '#ffd43b',
  video: '#ff8787',
  document: '#748ffc',
  other: '#868e96',
};
