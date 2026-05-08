export interface UserDto {
  userId: number
  email: string
  fullName: string
  phoneNumber?: string
  department?: string
  bio?: string
  profileImageUrl?: string
  status: string
  roles: string[]
  lastLoginAt?: string
  createdAt: string
}

export interface LoginRequestDto {
  email: string
  password: string
}

export interface LoginResponseDto {
  token: string
  refreshToken: string
  user: UserDto
}

export interface AgentDto {
  agentId: number
  agentCode: string
  agentName: string
  description?: string
  serviceId: number
  serviceName: string
  systemPrompt?: string
  iconClass?: string
  colorCode?: string
  temperature?: number
  maxTokens?: number
  defaultModel?: string
  isPublic: boolean
  enableRag?: boolean
  piiProtectionEnabled?: boolean
  piiProtectionMode?: string | null // null이면 전역 설정 사용, "Block" 또는 "Mask"
  allowGuestChat?: boolean
  allowedEmbedDomains?: string
  welcomeMessage?: string
  placeholderText?: string
  chatTheme?: string
  // 후속 트랙 (2026-05-08): 백엔드 AgentDto 갭 보강 commit b3a2d85 의 6 신규 필드.
  // Phase 5.1 LLM 라우팅 + ADR-2 단일 권위 + Phase 6.5 호출 화이트리스트.
  // 모두 백엔드 직렬화 키 (camelCase) 와 일치. nullable 필드는 string | null 폴백.
  llmRouting?: string // "External" | "Internal" | "Hybrid", 백엔드 default "External"
  routingPolicyJson?: string | null // Hybrid 전용 결정 규칙 JSON, null 이면 기본 정책
  knowledgeBaseSource?: string // "AgentHub" | "DocUtil", Phase 6+ 는 "DocUtil" 권장
  knowledgeBaseRef?: string | null // DocUtil collection ID, null 이면 글로벌 corpus
  consumerSystems?: string | null // 호출 가능 End-User App ID JSON 배열 문자열
  sortOrder?: number // 같은 카테고리 내 정렬 순서, 큰 값이 위로
  createdBy: number
  createdByName: string
  isActive: boolean
  createdAt: string
  updatedAt: string
  // Marketplace specific fields (optional)
  downloadCount?: number
  rating?: number
  reviewCount?: number
}

export interface ConversationDto {
  conversationId: number
  userId: number
  agentId?: number
  agentName?: string
  serviceId: number
  serviceName: string
  title?: string
  model?: string
  temperature?: number
  maxTokens?: number
  messageCount: number
  totalTokens: number
  totalCost: number
  lastMessageAt?: string
  isArchived: boolean
  isPinned: boolean
  language?: string // 'ko', 'en', 'auto'
  // 후속 트랙 B-1 (2026-05-08): 백엔드 ChatConversation.cs / ConversationDto.cs 의
  // EnableRag / EnableWebSearch 와 정렬. 두 필드 모두 [Required] non-nullable bool 이므로 TS 도 boolean 으로 둔다.
  enableRag: boolean
  enableWebSearch: boolean
  createdAt: string
  updatedAt: string
}

export interface ChatMessageDto {
  messageId: number
  conversationId: number
  role: string
  content: string
  tokensUsed?: number
  model?: string
  finishReason?: string
  createdAt: string
}

export interface ApiServiceDto {
  serviceId: number
  serviceCode: string
  serviceName: string
  description?: string
  iconClass?: string
  colorCode?: string
  defaultModel?: string
  costPerRequest?: number
  isActive: boolean
  serviceType: 'Chat' | 'ImageGeneration' | 'VideoGeneration' | 'Both'
}

export interface ImageGenerationRequestDto {
  prompt: string
  model?: string
  size?: string
  quality?: string
  style?: string
  numberOfImages?: number
  serviceId: number
}

export interface ImageGenerationResponseDto {
  imageUrls: string[]
  prompt: string
  model: string
  createdAt: string
  cost: number
  responseTime: number
}

export interface QuotaDto {
  quotaId: number
  userId: number
  userEmail: string
  serviceId: number
  serviceName: string
  monthlyLimit: number
  dailyLimit: number
  costLimit: number
  currentUsage: number
  currentCost: number
  alertThreshold: number
  isAlertEnabled: boolean
  lastResetAt?: string
  createdAt: string
  updatedAt: string
}

export interface UsageStatsDto {
  serviceId: number
  serviceName: string
  date: string
  requestCount: number
  totalTokens: number
  totalCost: number
  averageResponseTime: number
}

export interface CostAnalysisDto {
  totalCost: number
  startDate: string
  endDate: string
  serviceCosts: ServiceCostDto[]
}

export interface ServiceCostDto {
  serviceId: number
  serviceName: string
  totalCost: number
  requestCount: number
  percentage: number
}

export interface DashboardStatsDto {
  totalUsers: number
  activeUsers: number
  todayApiCalls: number
  thisMonthCost: number
}

export interface ApiKeyDto {
  apiKeyId: number
  userId: number
  keyName: string
  serviceCode: string
  serviceName?: string
  agentId?: number
  description?: string
  expiresAt?: string | Date
  isActive: boolean
  lastUsedAt?: string | Date
  usageCount: number
  createdAt: string | Date
  updatedAt: string | Date
  maskedKey?: string
  // 보안 확장 필드
  allowedIps?: string
  scopes?: string
  rateLimitPerMinute?: number
  rateLimitPerDay?: number
}

export interface PiiProtectionSettings {
  enabled: boolean
  mode: string // "Block" or "Mask"
  detectionTypes: string[]
}

export interface PiiDetectionResult {
  hasPii: boolean
  detectedItems: PiiDetectionItem[]
  maskedMessage: string
}

export interface PiiDetectionItem {
  type: string // PhoneNumber, ResidentNumber, CreditCard, Email, AccountNumber, DriverLicense, PassportNumber, AlienRegistrationNumber
  originalValue: string
  maskedValue: string
  startIndex: number
  endIndex: number
}

export interface PiiDetectionLogDto {
  logId: number
  userId?: number
  userName?: string
  agentId?: number
  agentName?: string
  conversationId?: number
  detectionType: string
  detectionTypeName: string
  originalMessage: string
  actionTaken: string
  detectedAt: string | Date
  ipAddress?: string
}

export interface PiiDetectionStatisticsDto {
  totalDetections: number
  blockedCount: number
  maskedCount: number
  detectionTypeCounts: Record<string, number>
  dailyCounts: Record<string, number>
  agentCounts: Record<string, number>
  userCounts: Record<string, number>
}

export interface CreateApiKeyRequestDto {
  keyName: string
  serviceCode: string
  apiKey: string
  description?: string
  expiresAt?: Date
  allowedIps?: string
  scopes?: string
  rateLimitPerMinute?: number
  rateLimitPerDay?: number
}

export interface UpdateApiKeyRequestDto {
  keyName?: string
  description?: string
  isActive?: boolean
  expiresAt?: Date
  allowedIps?: string
  scopes?: string
  rateLimitPerMinute?: number
  rateLimitPerDay?: number
}

export interface CreateAgentApiKeyRequestDto {
  keyName?: string
  description?: string
  expiresAt?: Date
  allowedIps?: string
  scopes?: string
  rateLimitPerMinute?: number
  rateLimitPerDay?: number
}

export interface CreateAgentApiKeyResponseDto {
  apiKeyId: number
  apiKey: string
  keyName: string
  agentId: number
  expiresAt?: string | Date
  scopes?: string
  allowedIps?: string
  rateLimitPerMinute?: number
  rateLimitPerDay?: number
  warning: string
}

/** Agent 공개 정보 (API Key 인증) */
export interface AgentPublicInfoDto {
  agentId: number
  agentName: string
  agentCode?: string
  description?: string
  isPublic: boolean
  defaultModel?: string
  enableRag: boolean
  capabilities: string[]
}

/** API 사용량 통계 (API Key 인증) */
export interface AgentApiUsageDto {
  agentId: number
  apiKeyId: number
  keyName: string
  totalRequests: number
  lastUsedAt?: string | Date
  rateLimitPerMinute?: number
  rateLimitPerDay?: number
  scopes?: string
  expiresAt?: string | Date
}

export interface TeamStatsDto {
  totalMembers: number
  totalApiCalls: number
  totalCost: number
  sharedAgents: number
  userUsages: UserUsageDto[]
}

export interface UserUsageDto {
  userId: number
  email: string
  fullName: string
  requestCount: number
  totalCost: number
  totalTokens: number
}

export interface TeamDto {
  teamId: number
  teamName: string
  description?: string
  department?: string
  managerId?: number
  managerName?: string
  managerEmail?: string
  isActive: boolean
  memberCount: number
  createdAt: string
  updatedAt: string
  members: TeamMemberDto[]
}

export interface TeamMemberDto {
  teamMemberId: number
  teamId: number
  userId: number
  userName: string
  userEmail: string
  role?: string
  joinedAt: string
  isActive: boolean
}

export interface CreateTeamRequestDto {
  teamName: string
  description?: string
  department?: string
  managerId?: number
}

export interface UpdateTeamRequestDto {
  teamName?: string
  description?: string
  department?: string
  managerId?: number
  isActive?: boolean
}

export interface AddTeamMemberRequestDto {
  userId: number
  role?: string
}

export interface UserPreferenceDto {
  preferenceId: number
  userId: number
  preferenceKey: string
  preferenceValue?: string
  dataType: string
  category?: string
  description?: string
  createdAt: string
  updatedAt: string
}

export interface CreateUserPreferenceRequestDto {
  preferenceKey: string
  preferenceValue?: string
  dataType?: string
  category?: string
  description?: string
}

export interface UpdateUserPreferenceRequestDto {
  preferenceValue?: string
  dataType?: string
  category?: string
  description?: string
}

export interface ApiUsageDto {
  usageId: number
  userId: number
  userName?: string
  serviceId: number
  serviceName: string
  model?: string
  tokensUsed?: number
  requestCost: number
  requestTime: string
  responseTime?: number
  statusCode?: number
  errorMessage?: string
  prompt?: string
}

export interface FaqDto {
  faqId: number
  question: string
  answer: string
  category?: string
  sortOrder: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface TutorialDto {
  tutorialId: number
  title: string
  description?: string
  videoUrl?: string
  thumbnailUrl?: string
  duration?: string
  category?: string
  sortOrder: number
  isActive: boolean
  viewCount: number
  createdAt: string
  updatedAt: string
}

export interface ExamplePromptDto {
  examplePromptId: number
  title: string
  prompt: string
  description?: string
  serviceCode?: string
  model?: string
  category?: string
  iconClass?: string
  sortOrder: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface PresentationGenerationRequestDto {
  prompt?: string
  pasteContent?: string
  importUrl?: string
  sourceType?: 'topic' | 'paste' | 'import'
  slideCount?: number
  templateId?: number
  serviceId: number
  model?: string
  style?: string
  slideSize?: string
  fontHeading?: string
  fontBody?: string
  themeId?: string
  includeAiImages?: boolean
  imageServiceId?: number
  imageModel?: string
  userId?: number
}

/** PRESENTATIONS 테이블 목록 조회용 (슬라이드 본문 미포함) */
export interface PresentationListItemDto {
  presentationId: number
  userId: number
  title: string
  themeId?: string
  slideCount: number
  createdAt: string
  updatedAt: string
}

export interface PresentationDto {
  presentationId: number
  userId: number
  title: string
  slides: SlideDto[]
  /** 목록 조회 시 슬라이드 개수 (전체 slides 로드 없이 표시용) */
  slideCount?: number
  themeId?: string
  /** 슬라이드 비율: 4:3, 16:9, 16:10 */
  slideSize?: string
  fontHeading?: string
  fontBody?: string
  createdAt: string
  updatedAt: string
}

export interface SlideDto {
  slideId: string
  slideNumber: number
  title: string
  content: string
  layout: string
  images: string[]
  charts: ChartDto[]
  tables?: TableDto[]
  imageDescription?: string
  imageUrl?: string
  imagePrompt?: string
}

export interface TableDto {
  headerRow?: boolean
  rows: string[][]
}

export interface PresentationThemeConfig {
  themeId: string
  name: string
  primaryColor: string
  secondaryColor: string
  fontHeading: string
  fontBody: string
}

export interface PresentationTemplateDto {
  templateId: number
  templateName: string
  description?: string
  templateFilePath: string
  templateStructure?: TemplateStructureDto
  category: string
  isPublic: boolean
  createdBy?: number
  createdByName?: string
  createdAt: string
  updatedAt: string
}

export interface TemplateStructureDto {
  slideCount: number
  slides: TemplateSlideInfoDto[]
  colorScheme?: string
  fontScheme?: string
}

export interface TemplateSlideInfoDto {
  slideNumber: number
  layoutType: string
  placeholders: TemplatePlaceholderDto[]
}

export interface TemplatePlaceholderDto {
  type: string
  index: number
  defaultText?: string
}

export interface TemplateUploadRequestDto {
  templateName: string
  description?: string
  category?: string
  isPublic?: boolean
}

export interface ChartDto {
  chartId: string
  chartType: string
  title: string
  data: Record<string, any>
}

export interface ReorderSlidesRequestDto {
  slideIds: string[]
}

export interface VideoGenerationRequestDto {
  prompt: string
  models: string[]
  duration?: string
  resolution?: string
  frameRate?: number
  serviceId?: number
  conversationId?: number
  agentId?: number
}

export interface VideoGenerationResponseDto {
  videoUrls: string[]
  modelResults: ModelResult[]
  prompt: string
  createdAt: string
  totalCost: number
  totalResponseTime: number
  conversationId?: number
}

export interface BannedWordDto {
  bannedWordId: number
  word: string
  agentId?: number
  agentName?: string
  description?: string
  isActive: boolean
  createdBy: number
  createdByName?: string
  createdAt: string
  updatedAt: string
}

export interface CreateBannedWordRequestDto {
  word: string
  agentId?: number
  description?: string
}

export interface UpdateBannedWordRequestDto {
  word?: string
  agentId?: number
  description?: string
  isActive?: boolean
}

export interface ModelResult {
  model: string
  videoUrl?: string
  errorMessage?: string
  isSuccess: boolean
  cost: number
  responseTime: number
  serviceId: number
}
