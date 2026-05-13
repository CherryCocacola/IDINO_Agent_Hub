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
  // 트랙 #88 C2 (2026-05-13): 만료 임박 사전 갱신을 위한 만료 시각 (ISO 8601 UTC)
  // 백엔드 LoginResponseDto.cs 에 추가되는 필드와 1:1 매핑. 없으면 undefined.
  tokenExpiresAt?: string
  refreshTokenExpiresAt?: string
}

/**
 * 트랙 #88 C2 (2026-05-13): /api/auth/refresh 응답.
 * 백엔드가 회전(rotation)된 refreshToken 과 새 만료 시각을 함께 반환한다.
 */
export interface RefreshTokenResponseDto {
  token: string
  refreshToken: string
  tokenExpiresAt?: string
  refreshTokenExpiresAt?: string
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
  // 트랙 #91 (2026-05-13): KeyType 으로 외부 노출 키(External) 와 외부 LLM 풀 키(Provider) 격리.
  // 백엔드 ApiKey.KeyType 컬럼 (string, default "External") 과 1:1 매핑. 구버전 응답 호환을 위해 optional.
  keyType?: 'External' | 'Provider'
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

/**
 * 트랙 #91 (2026-05-13): 외부 LLM 키(KeyType='Provider') 등록 요청 DTO.
 *
 * 백엔드 CreateProviderApiKeyRequestDto.cs 와 정렬. 운영자(Admin/SuperAdmin)만 호출 가능.
 * apiKey 는 평문이며 클라이언트는 등록 응답 수신 직후 메모리에서 즉시 폐기한다.
 * (백엔드는 AES-GCM 으로 암호화 저장 + KeyHash SHA-256 으로 중복 검사)
 */
export interface CreateProviderApiKeyRequestDto {
  /** 운영자 별칭. 풀 통계/목록 표시용. (예: "Prod Gemini Primary") */
  keyName: string
  /** 프로바이더 코드. ApiKeyPoolService 의 NormalizeServiceCode 화이트리스트와 정렬. */
  serviceCode: string
  /** LLM 제공사 평문 키. 등록 후 즉시 메모리 폐기 권장. */
  apiKey: string
  /** 운영자 설명 (선택). */
  description?: string | null
  /** 만료 시각 (ISO 8601). 미설정 시 무기한. RefreshAsync 시 자동 제외. */
  expiresAt?: string | null
  /** 등록 직후 제공사별 ping 으로 즉시 유효성 검증 여부. 기본 true. */
  validateOnCreate: boolean
}

/**
 * 트랙 #91 (2026-05-13): API 키 즉시 유효성 검증 응답.
 *
 * 백엔드 TestApiKeyResponseDto.cs 와 정렬. Gemini/OpenAI/Claude/Perplexity/Mistral 등
 * 제공사별 가벼운 GET (ListModels 등) 결과를 표시한다.
 */
export interface TestApiKeyResponseDto {
  /** 200 응답 + 유효 키 여부. */
  success: boolean
  /** 사용자 표시 메시지 (한국어). 실패 시 원인 포함. */
  message: string
  /** 정규화된 프로바이더 이름. null 이면 키 자체를 식별 못함. */
  provider: string | null
  /** 라운드트립 시간 (ms). 운영자의 외부망 상태 판단에 사용. */
  latencyMs: number
}

/**
 * 트랙 #91 (2026-05-13): 풀 통계 — 프로바이더별 한 행.
 *
 * 백엔드 ProviderPoolStatDto.cs 와 정렬. DB/appsettings 출처 분리로
 * 운영자가 키 회전 후에도 어디서 가져온 키인지 즉시 파악할 수 있게 한다.
 */
export interface ProviderPoolStatDto {
  /** 정규화된 프로바이더 코드 (예: "gemini", "openai"). */
  serviceCode: string
  /** 풀에 살아있는 키 총개수. */
  totalCount: number
  /** appsettings.json 에서 로드된 키 수 (정적, 컨테이너 재시작 시점 고정). */
  fromAppsettings: number
  /** DB 에서 로드된 키 수 (운영자 GUI 등록). */
  fromDb: number
  /** 현재 Rate Limit 쿨다운 상태인 키 수 (호출 일시 정지). */
  coolingDownCount: number
}

/**
 * 트랙 #91 (2026-05-13): 풀 통계 응답 — `GET /api/apikeys/pool-stats`.
 *
 * 백엔드 PoolStatsResponseDto.cs 와 정렬. Admin/SuperAdmin 전용.
 */
export interface PoolStatsResponseDto {
  /** 프로바이더별 통계 행. 미등록 프로바이더는 미포함 — UI 에서 — 로 표시. */
  providers: ProviderPoolStatDto[]
  /** 마지막 RefreshAsync 완료 시각 (ISO 8601 UTC). 5분 RecurringJob 또는 즉시 트리거. */
  lastRefreshedAt: string
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
