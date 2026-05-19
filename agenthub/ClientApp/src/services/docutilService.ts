/**
 * docutilService — 운영자 KB(DocUtil BFF) API 클라이언트.
 *
 * 진입점: AgentHub `/api/admin/knowledge-base/*` (Phase 6.3 신설 컨트롤러)
 *
 * 호출 흐름:
 *   Vue View (AdminKnowledgeBase.vue 등)
 *     -> docUtilStore (Pinia)
 *     -> docutilService (본 파일)
 *     -> services/api.ts (axios 인터셉터: JWT 자동 부착, 401 갱신)
 *     -> AgentHub `[Authorize(Roles="Admin,SuperAdmin")] /api/admin/knowledge-base`
 *     -> IDocUtilClient (Phase 6.1)
 *     -> DocUtil FastAPI `/api/v1/*`
 *
 * 통합 비전: 운영자 KB 관리는 AgentHub UI 단일 진입점(R2). 본 서비스는 외부 LLM/
 * DocUtil API 를 직접 호출하지 않으며, 항상 AgentHub BFF 만을 경유한다.
 */

import api from '@/services/api'

// ─── 백엔드 응답 DTO 매핑 (camelCase, Program.cs JsonNamingPolicy.CamelCase 적용) ───

/** 문서 목록 한 행 */
export interface DocumentSummary {
  id: string
  name: string
  status: string
  createdAt: string | null
}

/** 문서 목록 응답 */
export interface DocumentList {
  items: DocumentSummary[]
  total: number
  page: number
  size: number
}

/** 문서 상세 */
export interface DocumentDetail {
  id: string
  name: string
  status: string
  createdAt: string | null
  uploaderName: string | null
  visibilityTargets: unknown
}

/** 업로드 응답 */
export interface UploadResult {
  id: string
  name: string
  status: string
  jobId: string | null
}

/** 청크 한 건 */
export interface Chunk {
  chunkId: string
  content: string
  chunkIndex: number
  metadata: unknown
}

/** 검색 결과 단일 hit */
export interface SearchHit {
  id: string
  content: string
  score: number
  metadata: unknown
}

/** 검색 응답 */
export interface SearchResult {
  results: SearchHit[]
  totalTime: number
  metadata: unknown
}

/**
 * DocUtil 컬렉션(projects) 카탈로그 한 행.
 *
 * 후속 트랙(2026-05-08): AgentBuilder.vue 의 KnowledgeBaseRef dropdown UX 용.
 * BFF 단순화 원칙으로 id/name/description 3 필드만 표면화 — DocUtil 의 organization_id /
 * created_by / created_at / updated_at / allow_original_download 등 내부 메타는 비노출.
 */
export interface DocUtilCollection {
  /** DocUtil project UUID — Agent.KnowledgeBaseRef 에 그대로 저장됨. */
  id: string
  /** 사용자 표기명 — dropdown option 라벨로 사용. */
  name: string
  /** 선택 설명 — dropdown option 의 hover hint(:title) 로 사용. 없을 수 있음. */
  description: string | null
}

// ─── API 호출 ────────────────────────────────────────────────────────────────

const BASE = '/admin/knowledge-base'

/**
 * 문서 목록 조회.
 * @param folderId DocUtil collection / folder 식별자(선택). 미지정 시 글로벌.
 * @param page    1-based 페이지 번호.
 * @param size    페이지 크기(1~200).
 */
export async function listDocuments(
  folderId?: string,
  page: number = 1,
  size: number = 20
): Promise<DocumentList> {
  const params: Record<string, string | number> = { page, size }
  if (folderId) params.folderId = folderId
  const { data } = await api.get<DocumentList>(`${BASE}/documents`, { params })
  return data
}

/**
 * 문서 업로드.
 * @param file       업로더가 선택한 File 객체.
 * @param folderId   대상 collection(선택).
 * @param visibility 가시성 정책(예: "internal" | "public", DocUtil 측 정의).
 */
export async function uploadDocument(
  file: File,
  folderId?: string,
  visibility?: string
): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('file', file)
  if (folderId) formData.append('folderId', folderId)
  if (visibility) formData.append('visibility', visibility)

  const { data } = await api.post<UploadResult>(`${BASE}/documents/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return data
}

/**
 * 문서 상세 조회. 404 응답은 null 로 정규화한다(Vue View 에서 빈 상태 분기 단순화).
 */
export async function getDocument(id: string): Promise<DocumentDetail | null> {
  try {
    const { data } = await api.get<DocumentDetail>(`${BASE}/documents/${encodeURIComponent(id)}`)
    return data
  } catch (err: any) {
    if (err?.response?.status === 404) {
      return null
    }
    throw err
  }
}

/** 문서 삭제. 백엔드 204 NoContent — 반환 값 없음. */
export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`${BASE}/documents/${encodeURIComponent(id)}`)
}

/** 문서 청크 목록 조회. */
export async function getChunks(id: string): Promise<Chunk[]> {
  const { data } = await api.get<Chunk[]>(`${BASE}/documents/${encodeURIComponent(id)}/chunks`)
  return data
}

/**
 * KB 검색(하이브리드).
 * @param query         사용자 질의 원문.
 * @param collectionRef 검색 범위 collection(선택).
 * @param maxResults    상위 결과 개수(1~50, 기본 10).
 */
export async function search(
  query: string,
  collectionRef?: string,
  maxResults: number = 10
): Promise<SearchResult> {
  const { data } = await api.post<SearchResult>(`${BASE}/search`, {
    query,
    collectionRef: collectionRef ?? null,
    maxResults
  })
  return data
}

/**
 * DocUtil 컬렉션(projects) 카탈로그 조회 — 후속 트랙 KB collection dropdown UX(2026-05-08).
 *
 * AgentBuilder.vue 가 KnowledgeBaseSource = "DocUtil" 일 때 호출하여 dropdown 옵션을 채움.
 * 운영자는 ID(UUID) 를 수동 입력하지 않고 사람이 읽을 수 있는 collection name 을 선택할 수 있음.
 *
 * @param page 1-based 페이지 번호(기본 1).
 * @param size 페이지 크기(기본 50, 최대 200 — DocUtil 측 한도).
 * @returns BFF 단순화된 collection 배열(id/name/description). 404/5xx 는 axios 인터셉터를 거쳐 throw.
 */
export async function listCollections(
  page: number = 1,
  size: number = 50
): Promise<DocUtilCollection[]> {
  const { data } = await api.get<DocUtilCollection[]>(`${BASE}/collections`, {
    params: { page, size }
  })
  return data
}

// ─── Phase 10.1a (2026-05-10): DocUtil 사용자 운영자 BFF ────────────────────
//
// 진입점: AgentHub `/api/admin/docutil/users[/{id}[/status]]` (Phase 10.1a 신설 컨트롤러)
//
// 인증/권한:
//   - 컨트롤러 레벨 [Authorize(Roles="Admin,SuperAdmin")] — Bearer 미부착/비-Admin → 401/403
//   - DocUtil 측 운영자 토큰은 IDocUtilTokenProvider 4단계 폴백으로 자동 부착(BFF 내부)
//
// 데이터 소스: DocUtil OpenAPI(2026-05-10 캡처) UserResponse / UserListResponse 매핑.
//   GET /api/v1/users → AgentHub /api/admin/docutil/users
//   GET /api/v1/users/{id} → AgentHub /api/admin/docutil/users/{id}
//   PUT /api/v1/users/{id}/status → AgentHub /api/admin/docutil/users/{id}/status
//   DELETE /api/v1/users/{id} → AgentHub /api/admin/docutil/users/{id}

/** DocUtil 사용자 한 행 — 목록/상세 공통(camelCase 직렬화). */
export interface DocUtilUserSummary {
  /** DocUtil user UUID. */
  id: string
  /** 사용자 표기명(한글 이름 또는 ID 형식). */
  username: string
  /** 사용자 이메일. */
  email: string
  /** 사용자 역할(예: "admin", "member"). */
  role: string
  /** 사용자 상태(예: "active", "inactive", "locked"). */
  status: string
  /** 소속 organization UUID. */
  organizationId: string
  /** 소속 부서 UUID(선택). 향후 10.1b 트랙에서 부서명 조인 예정. */
  departmentId: string | null
  /** 선호 언어 코드(선택). */
  language: string | null
  /** 최근 로그인 시각(선택, ISO 8601). */
  lastLoginAt: string | null
  /** 생성 시각(ISO 8601). */
  createdAt: string
}

/** DocUtil 사용자 상세(현재 트랙은 Summary 와 동일 셋). */
export type DocUtilUserDetail = DocUtilUserSummary

/** 사용자 목록 응답. */
export interface DocUtilUserList {
  items: DocUtilUserSummary[]
  total: number
  page: number
  size: number
}

/** 상태 변경 시 허용되는 값 — 백엔드 화이트리스트와 일치. */
export type DocUtilUserStatus = 'active' | 'inactive' | 'locked'

const USERS_BASE = '/admin/docutil'

/**
 * DocUtil 사용자 목록 조회 — 페이지/검색/필터.
 * @param page   1-based 페이지 번호(기본 1).
 * @param size   페이지 크기(1~100, 기본 20).
 * @param search username/email LIKE 검색(선택).
 * @param role   role 필터(선택, 예: "admin", "member").
 * @param status status 필터(선택, 예: "active", "inactive", "locked").
 */
export async function listUsers(
  page: number = 1,
  size: number = 20,
  search?: string,
  role?: string,
  status?: string
): Promise<DocUtilUserList> {
  const params: Record<string, string | number> = { page, size }
  if (search) params.search = search
  if (role) params.role = role
  if (status) params.status = status
  const { data } = await api.get<DocUtilUserList>(`${USERS_BASE}/users`, { params })
  return data
}

/**
 * DocUtil 사용자 상세 조회. 404 응답은 null 로 정규화한다.
 */
export async function getUser(id: string): Promise<DocUtilUserDetail | null> {
  try {
    const { data } = await api.get<DocUtilUserDetail>(
      `${USERS_BASE}/users/${encodeURIComponent(id)}`
    )
    return data
  } catch (err: unknown) {
    if (typeof err === 'object' && err !== null && 'response' in err) {
      const resp = (err as { response?: { status?: number } }).response
      if (resp?.status === 404) {
        return null
      }
    }
    throw err
  }
}

/**
 * DocUtil 사용자 상태 변경(active ↔ inactive ↔ locked).
 * 백엔드가 화이트리스트 검증 + 캐시 일괄 무효화(version-key bump) 수행.
 */
export async function updateUserStatus(
  id: string,
  status: DocUtilUserStatus
): Promise<DocUtilUserDetail> {
  const { data } = await api.put<DocUtilUserDetail>(
    `${USERS_BASE}/users/${encodeURIComponent(id)}/status`,
    { status }
  )
  return data
}

/**
 * DocUtil 사용자 일반 정보 수정 — partial PUT (트랙 #101 F7).
 *
 * 백엔드 진입점: AgentHub `PUT /api/admin/docutil/users/{id}` (UpdateDocUtilUserRequest).
 * 모든 필드 nullable — 최소 한 필드는 지정되어야 하며(컨트롤러 검증), departmentId 가
 * 빈 문자열("")이면 부서 해제 의도로 해석된다(백엔드 → DocUtil null 매핑).
 *
 * 성공/실패 모두 백엔드가 사용자 캐시(version-key bump)를 일괄 무효화한다.
 */
export interface DocUtilUserUpdate {
  /** 변경할 이메일. undefined 면 변경하지 않음. */
  email?: string
  /** 변경할 역할(예: "admin", "member"). */
  role?: string
  /** 변경할 부서 UUID. 빈 문자열("")은 부서 해제 의도. null 미지원 — 빈 문자열로 전달. */
  departmentId?: string
  /** 변경할 선호 언어 코드(예: "ko", "en", "vi"). */
  language?: string
  /** 변경할 상태(active/inactive/locked). */
  status?: DocUtilUserStatus
}

export async function updateUser(
  id: string,
  request: DocUtilUserUpdate
): Promise<DocUtilUserDetail> {
  const { data } = await api.put<DocUtilUserDetail>(
    `${USERS_BASE}/users/${encodeURIComponent(id)}`,
    request
  )
  return data
}

/**
 * DocUtil 사용자 삭제. 백엔드 204 NoContent — 반환값 없음.
 * 성공 시 백엔드가 캐시 일괄 무효화.
 */
export async function deleteUser(id: string): Promise<void> {
  await api.delete(`${USERS_BASE}/users/${encodeURIComponent(id)}`)
}

// ─── Phase 10.1b (2026-05-10): DocUtil 조직/부서/할당량 운영자 BFF ──────────
//
// 진입점: AgentHub `/api/admin/docutil/{organization,departments,...}` (Phase 10.1b 신설 컨트롤러)
//
// 인증/권한:
//   - 컨트롤러 레벨 [Authorize(Roles="Admin,SuperAdmin")] — Bearer 미부착/비-Admin → 401/403
//   - DocUtil 측 운영자 토큰은 IDocUtilTokenProvider 4단계 폴백으로 자동 부착(BFF 내부)
//   - org_id 자동 추출(GetOrganizationIdAsync) — 클라이언트 무관여
//
// 데이터 소스: DocUtil OpenAPI(2026-05-10 캡처) — OrganizationResponse / DepartmentResponse /
//   OrganizationQuotasCurrentResponse / QuotaStatusResponse 매핑.

/** DocUtil 조직 응답. */
export interface DocUtilOrganization {
  id: string
  name: string
  slug: string
  description: string | null
  /** 조직 free-form 설정(향후 확장 대비 pass-through). */
  settings: unknown
  /** 생성 시각(ISO 8601, DocUtil 측은 ins_dt 를 created_at 으로 alias). */
  createdAt: string
}

/** DocUtil 조직 수정 요청(partial). */
export interface UpdateOrganizationRequest {
  name?: string | null
  description?: string | null
  settings?: unknown
}

/** DocUtil 부서 응답 — path/depth 가 트리 위치를 표현(materialized path). */
export interface DocUtilDepartment {
  id: string
  organizationId: string
  parentId: string | null
  name: string
  /** 트리 깊이(루트 = 0). */
  depth: number
  /** materialized path (예: /uuid1/uuid2/). */
  path: string
  createdAt: string
}

/** DocUtil 부서 생성 요청. */
export interface CreateDepartmentRequest {
  name: string
  parentId?: string | null
}

/** DocUtil 부서 수정 요청(partial). */
export interface UpdateDepartmentRequest {
  name?: string | null
  parentId?: string | null
}

/** DocUtil 부서 멤버 한 행(free-form 응답에서 4 필드만 안정적으로 노출). */
export interface DocUtilDepartmentMember {
  id: string
  username: string
  email: string
  role: string
}

/** DocUtil 단일 할당량 항목. */
export interface DocUtilOrganizationQuotaStatus {
  /** 쿼터 유형(예: "dalle_monthly", "unsplash_monthly"). */
  quotaType: string
  monthlyLimit: number
  usedCount: number
  remaining: number
  /** 대상 연-월(YYYY-MM). */
  yearMonth: string
}

/** DocUtil 조직 월 할당량 현황 — quotas 가 List 로 평탄화됨(BFF 변환). */
export interface DocUtilOrganizationQuotaCurrent {
  organizationId: string
  yearMonth: string
  quotas: DocUtilOrganizationQuotaStatus[]
}

/** DocUtil 할당량 한도 수정 요청. */
export interface UpdateQuotaRequest {
  monthlyLimit: number
}

const DEPTS_BASE = '/admin/docutil'

/** 조직 정보 조회. */
export async function getOrganization(): Promise<DocUtilOrganization> {
  const { data } = await api.get<DocUtilOrganization>(`${DEPTS_BASE}/organization`)
  return data
}

/** 조직 정보 수정(partial — 적어도 한 필드 지정). */
export async function updateOrganization(
  request: UpdateOrganizationRequest
): Promise<DocUtilOrganization> {
  const { data } = await api.put<DocUtilOrganization>(
    `${DEPTS_BASE}/organization`,
    request
  )
  return data
}

/** 부서 목록 조회(평탄 List, path 기반 트리 표현). */
export async function listDepartments(): Promise<DocUtilDepartment[]> {
  const { data } = await api.get<DocUtilDepartment[]>(`${DEPTS_BASE}/departments`)
  return data
}

/** 부서 생성. */
export async function createDepartment(
  request: CreateDepartmentRequest
): Promise<DocUtilDepartment> {
  const { data } = await api.post<DocUtilDepartment>(
    `${DEPTS_BASE}/departments`,
    request
  )
  return data
}

/** 부서 수정(partial — 적어도 한 필드 지정). */
export async function updateDepartment(
  deptId: string,
  request: UpdateDepartmentRequest
): Promise<DocUtilDepartment> {
  const { data } = await api.put<DocUtilDepartment>(
    `${DEPTS_BASE}/departments/${encodeURIComponent(deptId)}`,
    request
  )
  return data
}

/** 부서 삭제. 백엔드 204 NoContent — 반환값 없음. */
export async function deleteDepartment(deptId: string): Promise<void> {
  await api.delete(`${DEPTS_BASE}/departments/${encodeURIComponent(deptId)}`)
}

/** 부서 멤버 조회. */
export async function getDepartmentMembers(deptId: string): Promise<DocUtilDepartmentMember[]> {
  const { data } = await api.get<DocUtilDepartmentMember[]>(
    `${DEPTS_BASE}/departments/${encodeURIComponent(deptId)}/members`
  )
  return data
}

/** 조직 월 할당량 현황 조회. */
export async function getOrganizationQuota(): Promise<DocUtilOrganizationQuotaCurrent> {
  const { data } = await api.get<DocUtilOrganizationQuotaCurrent>(
    `${DEPTS_BASE}/organization/quota`
  )
  return data
}

/** 조직 월 할당량 한도 수정. */
export async function updateOrganizationQuota(
  quotaType: string,
  request: UpdateQuotaRequest
): Promise<DocUtilOrganizationQuotaStatus> {
  const { data } = await api.put<DocUtilOrganizationQuotaStatus>(
    `${DEPTS_BASE}/organization/quota/${encodeURIComponent(quotaType)}`,
    request
  )
  return data
}

// ─── Phase 10.1c (2026-05-10): DocUtil 프로젝트 / 보드 운영자 BFF ───────────
//
// 진입점: AgentHub `/api/admin/docutil/projects[/{id}[/...]]` (Phase 10.1c 신설 컨트롤러)
//
// 인증/권한: 컨트롤러 [Authorize(Roles="Admin,SuperAdmin")] — 401/403 자동 매핑.
// 기존 listCollections (294e8a6, AgentBuilder dropdown) 시그니처/동작 보존.
// 통합 namespace `docutil-collections` 효과로 본 화면의 mutation 시 AgentBuilder dropdown 도 즉시 갱신.
//
// 데이터 소스: DocUtil OpenAPI(2026-05-10 캡처) — ProjectResponse / ProjectListResponse /
//   BoardResponse / BoardListResponse 매핑. members/departments/tree 는 free-form schema.

/** DocUtil 프로젝트 응답(8 필드 — 운영자 콘솔 풍부 표면). */
export interface DocUtilProject {
  /** 프로젝트 UUID. */
  id: string
  name: string
  description: string | null
  /** 원본 파일 다운로드 허용 여부(기본 true). */
  allowOriginalDownload: boolean
  /** 소속 조직 UUID. */
  organizationId: string
  /** 생성자 UUID. */
  createdBy: string
  /** 생성 시각(ISO 8601, DocUtil ins_dt → created_at alias). */
  createdAt: string
  /** 수정 시각(ISO 8601, DocUtil upd_dt → updated_at alias). */
  updatedAt: string
}

/** 프로젝트 목록 응답. */
export interface DocUtilProjectList {
  items: DocUtilProject[]
  total: number
  page: number
  size: number
}

/** 프로젝트 트리 노드 — DocUtil `/api/v1/projects/tree` 응답(평면 + boards sub-array). */
export interface DocUtilProjectTreeNode {
  id: string
  name: string
  /** 프로젝트의 보드 목록(현재 트랙: 트리는 프로젝트 → 보드 2단계 평면). */
  boards: DocUtilBoard[]
}

/** 프로젝트 멤버 한 행(free-form 응답에서 4 필드 안정 노출). */
export interface DocUtilProjectMember {
  id: string
  username: string
  email: string
  role: string
}

/** 프로젝트 참여 부서 한 행(free-form 응답에서 4 필드 안정 노출). */
export interface DocUtilProjectDepartment {
  id: string
  name: string
  /** materialized path. */
  path: string
  /** 트리 깊이(루트 = 0). */
  depth: number
}

/** 프로젝트 생성 요청 — DocUtil ProjectCreate 매핑. */
export interface CreateProjectRequest {
  name: string
  description?: string | null
  /** DocUtil 기본값 true. */
  allowOriginalDownload?: boolean | null
}

/** 프로젝트 수정 요청 — DocUtil ProjectUpdate(partial). allow_original_download 미존재. */
export interface UpdateProjectRequest {
  name?: string | null
  description?: string | null
}

/** DocUtil 보드 응답(7 필드 — folder_id 미존재). */
export interface DocUtilBoard {
  id: string
  /** 상위 프로젝트 UUID. */
  projectId: string
  name: string
  description: string | null
  createdBy: string
  createdAt: string
  updatedAt: string
}

/** 보드 목록 응답(페이지네이션). */
export interface DocUtilBoardList {
  items: DocUtilBoard[]
  total: number
  page: number
  size: number
}

/** 보드 생성 요청 — DocUtil BoardCreate(folder_id 미존재). */
export interface CreateBoardRequest {
  name: string
  description?: string | null
}

/** 보드 수정 요청 — DocUtil BoardUpdate(partial). */
export interface UpdateBoardRequest {
  name?: string | null
  description?: string | null
}

const PROJECTS_BASE = '/admin/docutil'

/**
 * 프로젝트 목록 조회(페이징 + 검색).
 * @param page   1-based 페이지 번호(기본 1).
 * @param size   페이지 크기(1~200, 기본 20).
 * @param search name/description LIKE 검색(선택).
 */
export async function listProjects(
  page: number = 1,
  size: number = 20,
  search?: string
): Promise<DocUtilProjectList> {
  const params: Record<string, string | number> = { page, size }
  if (search) params.search = search
  const { data } = await api.get<DocUtilProjectList>(`${PROJECTS_BASE}/projects`, { params })
  return data
}

/** 프로젝트 트리 조회. */
export async function getProjectTree(): Promise<DocUtilProjectTreeNode[]> {
  const { data } = await api.get<DocUtilProjectTreeNode[]>(`${PROJECTS_BASE}/projects/tree`)
  return data
}

/** 프로젝트 상세 조회. 404 응답은 null 로 정규화. */
export async function getProject(id: string): Promise<DocUtilProject | null> {
  try {
    const { data } = await api.get<DocUtilProject>(
      `${PROJECTS_BASE}/projects/${encodeURIComponent(id)}`
    )
    return data
  } catch (err: unknown) {
    if (typeof err === 'object' && err !== null && 'response' in err) {
      const resp = (err as { response?: { status?: number } }).response
      if (resp?.status === 404) return null
    }
    throw err
  }
}

/** 프로젝트 신규 생성. */
export async function createProject(request: CreateProjectRequest): Promise<DocUtilProject> {
  const { data } = await api.post<DocUtilProject>(`${PROJECTS_BASE}/projects`, request)
  return data
}

/** 프로젝트 수정(partial — 적어도 한 필드 지정). */
export async function updateProject(
  id: string,
  request: UpdateProjectRequest
): Promise<DocUtilProject> {
  const { data } = await api.put<DocUtilProject>(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(id)}`,
    request
  )
  return data
}

/** 프로젝트 삭제. 백엔드 204 NoContent — 반환값 없음. */
export async function deleteProject(id: string): Promise<void> {
  await api.delete(`${PROJECTS_BASE}/projects/${encodeURIComponent(id)}`)
}

/** 프로젝트 멤버 조회. */
export async function getProjectMembers(id: string): Promise<DocUtilProjectMember[]> {
  const { data } = await api.get<DocUtilProjectMember[]>(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(id)}/members`
  )
  return data
}

/**
 * 프로젝트 멤버 추가 요청(트랙 #101 F8).
 *
 * 백엔드 진입점: AgentHub `POST /api/admin/docutil/projects/{projectId}/members`.
 * role 화이트리스트 — "member" 또는 "manager" (백엔드 사전 검증). 누락 시 백엔드가
 * "member" 로 기본 적용한다.
 *
 * 실패 모드:
 *   - 409 Conflict — 이미 동일 사용자가 멤버
 *   - 404 Not Found — 프로젝트 또는 사용자 미존재
 *   - 400 Bad Request — role 화이트리스트 위반
 */
export interface DocUtilProjectMemberAdd {
  /** 추가할 사용자 UUID. */
  userId: string
  /** 역할 — 백엔드 화이트리스트는 "member" / "manager". 미지정 시 "member" 기본. */
  role?: 'member' | 'manager'
}

export async function addProjectMember(
  projectId: string,
  request: DocUtilProjectMemberAdd
): Promise<DocUtilProjectMember> {
  const { data } = await api.post<DocUtilProjectMember>(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(projectId)}/members`,
    request
  )
  return data
}

/**
 * 프로젝트 멤버 제거(트랙 #101 F8).
 *
 * 백엔드 진입점: AgentHub `DELETE /api/admin/docutil/projects/{projectId}/members/{userId}`.
 * 백엔드 204 NoContent — 반환값 없음. 성공/실패 모두 캐시 일괄 무효화.
 */
export async function removeProjectMember(
  projectId: string,
  userId: string
): Promise<void> {
  await api.delete(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(projectId)}/members/${encodeURIComponent(userId)}`
  )
}

/** 프로젝트 참여 부서 조회. */
export async function getProjectDepartments(id: string): Promise<DocUtilProjectDepartment[]> {
  const { data } = await api.get<DocUtilProjectDepartment[]>(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(id)}/departments`
  )
  return data
}

/** 프로젝트의 보드 목록 조회. */
export async function listProjectBoards(
  projectId: string,
  page: number = 1,
  size: number = 50
): Promise<DocUtilBoardList> {
  const { data } = await api.get<DocUtilBoardList>(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(projectId)}/boards`,
    { params: { page, size } }
  )
  return data
}

/** 보드 신규 생성. */
export async function createProjectBoard(
  projectId: string,
  request: CreateBoardRequest
): Promise<DocUtilBoard> {
  const { data } = await api.post<DocUtilBoard>(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(projectId)}/boards`,
    request
  )
  return data
}

/** 보드 상세 조회. 404 응답은 null 로 정규화. */
export async function getProjectBoard(
  projectId: string,
  boardId: string
): Promise<DocUtilBoard | null> {
  try {
    const { data } = await api.get<DocUtilBoard>(
      `${PROJECTS_BASE}/projects/${encodeURIComponent(projectId)}/boards/${encodeURIComponent(boardId)}`
    )
    return data
  } catch (err: unknown) {
    if (typeof err === 'object' && err !== null && 'response' in err) {
      const resp = (err as { response?: { status?: number } }).response
      if (resp?.status === 404) return null
    }
    throw err
  }
}

/** 보드 수정(partial). */
export async function updateProjectBoard(
  projectId: string,
  boardId: string,
  request: UpdateBoardRequest
): Promise<DocUtilBoard> {
  const { data } = await api.put<DocUtilBoard>(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(projectId)}/boards/${encodeURIComponent(boardId)}`,
    request
  )
  return data
}

/** 보드 삭제. 백엔드 204 NoContent. */
export async function deleteProjectBoard(projectId: string, boardId: string): Promise<void> {
  await api.delete(
    `${PROJECTS_BASE}/projects/${encodeURIComponent(projectId)}/boards/${encodeURIComponent(boardId)}`
  )
}

// ════════════════════════════════════════════════════════════════════════════
// Phase 10.2a (2026-05-10) — DocUtil Dashboard + Audit BFF 운영자 콘솔
//
// 진입점: AgentHub `/api/admin/docutil/{dashboard,audit-logs}/*`
//   (AdminDocUtilOperationsController, [Authorize(Roles="Admin,SuperAdmin")])
//
// 백엔드 record 와 1:1 매핑(camelCase 직렬화 자동 변환). 추정 금지 — DocUtil
// OpenAPI(2026-05-10 캡처) schema 그대로.
// ════════════════════════════════════════════════════════════════════════════

const OPS_BASE = '/admin/docutil'

/** 대시보드 KPI 메트릭 (DashboardMetrics → camelCase). */
export interface DocUtilDashboardMetrics {
  totalUsers: number
  activeUsers: number
  totalDocuments: number
  totalSearches: number
  /** 자유 형식 카운터(예: chat / qa / keyword). DocUtil additionalProperties=true. */
  featureUsage: Record<string, number>
}

/** 시간별 평균 응답시간 시계열 — timestamps/values 동일 길이 평행 배열. */
export interface DocUtilResponseTimes {
  timestamps: string[]
  values: number[]
}

/** 일별 검색 오류 카운트 — dates/errorCounts 동일 길이 평행 배열. */
export interface DocUtilSearchErrors {
  dates: string[]
  errorCounts: number[]
}

/** 검색 사용량 통계. */
export interface DocUtilSearchUsage {
  totalRequests: number
  totalResponses: number
  totalFailures: number
  /** 집계 기간 라벨(예: "7d"). */
  period: string
}

/** 문서 업로드 상태 분포. */
export interface DocUtilUploadStatus {
  completed: number
  processing: number
  waiting: number
  error: number
}

/** 감사 로그 한 행. user_agent 등 schema 미존재 필드는 추가하지 않음. */
export interface DocUtilAuditLogEntry {
  id: string
  organizationId: string
  /** 시스템 액션 등에서 null 가능. */
  userId: string | null
  /** 예: "auth.login", "user.update". */
  action: string
  /** 예: "auth", "user". */
  resourceType: string
  resourceId: string | null
  /** 자유 형식 dict (DocUtil 측 additionalProperties=true). */
  details: Record<string, unknown> | null
  ipAddress: string | null
  /** ISO-8601 UTC. */
  createdAt: string
}

/** 감사 로그 페이지 응답. */
export interface DocUtilAuditLogList {
  items: DocUtilAuditLogEntry[]
  total: number
  page: number
  size: number
}

/** 감사 로그 목록 필터 — 모든 필드 선택. */
export interface AuditLogFilters {
  page?: number
  size?: number
  action?: string
  resourceType?: string
  userId?: string
  /** ISO-8601 UTC. */
  startDate?: string
  /** ISO-8601 UTC. */
  endDate?: string
}

/** 대시보드 KPI 메트릭 조회. */
export async function getDashboardMetrics(): Promise<DocUtilDashboardMetrics> {
  const { data } = await api.get<DocUtilDashboardMetrics>(`${OPS_BASE}/dashboard/metrics`)
  return data
}

/** 시간별 응답시간 시계열 조회. period 미지정 시 DocUtil 기본(빈 배열일 가능성). */
export async function getDashboardResponseTimes(
  period?: string
): Promise<DocUtilResponseTimes> {
  const params: Record<string, string> = {}
  if (period && period.trim()) params.period = period.trim()
  const { data } = await api.get<DocUtilResponseTimes>(`${OPS_BASE}/dashboard/response-times`, {
    params
  })
  return data
}

/** 일별 검색 오류 카운트 조회. */
export async function getDashboardSearchErrors(
  period?: string
): Promise<DocUtilSearchErrors> {
  const params: Record<string, string> = {}
  if (period && period.trim()) params.period = period.trim()
  const { data } = await api.get<DocUtilSearchErrors>(`${OPS_BASE}/dashboard/search-errors`, {
    params
  })
  return data
}

/** 검색 사용량 통계 조회. */
export async function getDashboardSearchUsage(
  period?: string
): Promise<DocUtilSearchUsage> {
  const params: Record<string, string> = {}
  if (period && period.trim()) params.period = period.trim()
  const { data } = await api.get<DocUtilSearchUsage>(`${OPS_BASE}/dashboard/search-usage`, {
    params
  })
  return data
}

/** 문서 업로드 상태 분포 조회. */
export async function getDashboardUploadStatus(): Promise<DocUtilUploadStatus> {
  const { data } = await api.get<DocUtilUploadStatus>(`${OPS_BASE}/dashboard/upload-status`)
  return data
}

/** 감사 로그 목록(페이징 + 필터) 조회. */
export async function listAuditLogs(
  filters: AuditLogFilters = {}
): Promise<DocUtilAuditLogList> {
  const params: Record<string, string | number> = {}
  params.page = filters.page ?? 1
  params.size = filters.size ?? 50
  if (filters.action && filters.action.trim()) params.action = filters.action.trim()
  if (filters.resourceType && filters.resourceType.trim())
    params.resourceType = filters.resourceType.trim()
  if (filters.userId && filters.userId.trim()) params.userId = filters.userId.trim()
  if (filters.startDate && filters.startDate.trim()) params.startDate = filters.startDate.trim()
  if (filters.endDate && filters.endDate.trim()) params.endDate = filters.endDate.trim()
  const { data } = await api.get<DocUtilAuditLogList>(`${OPS_BASE}/audit-logs`, { params })
  return data
}

/**
 * 감사 로그 CSV 내보내기(Blob 다운로드).
 * 호출자는 반환된 Blob 을 file-saver / a[download] 등으로 저장한다.
 *
 * 응답 헤더(Content-Disposition) 의 한국어 파일명도 함께 추출하여 반환.
 */
export async function exportAuditLogs(
  filters: Omit<AuditLogFilters, 'page' | 'size'> = {}
): Promise<{ blob: Blob; fileName: string; contentType: string }> {
  const params: Record<string, string> = {}
  if (filters.action && filters.action.trim()) params.action = filters.action.trim()
  if (filters.resourceType && filters.resourceType.trim())
    params.resourceType = filters.resourceType.trim()
  if (filters.userId && filters.userId.trim()) params.userId = filters.userId.trim()
  if (filters.startDate && filters.startDate.trim()) params.startDate = filters.startDate.trim()
  if (filters.endDate && filters.endDate.trim()) params.endDate = filters.endDate.trim()

  const response = await api.get(`${OPS_BASE}/audit-logs/export`, {
    params,
    responseType: 'blob'
  })

  const contentType =
    (response.headers?.['content-type'] as string | undefined) ?? 'text/csv; charset=utf-8'
  const fileName = parseFileNameFromDisposition(
    response.headers?.['content-disposition'] as string | undefined
  )

  return { blob: response.data as Blob, fileName, contentType }
}

/**
 * Content-Disposition 헤더에서 filename 추출.
 * RFC 5987(`filename*=UTF-8''...`) 우선, 없으면 ASCII fallback.
 */
function parseFileNameFromDisposition(disposition: string | undefined): string {
  if (!disposition) return 'audit_logs.csv'

  // filename*=UTF-8''<encoded> 우선
  const star = /filename\*=(?:UTF-8|utf-8)''([^;]+)/i.exec(disposition)
  if (star) {
    try {
      return decodeURIComponent(star[1].trim().replace(/^"|"$/g, ''))
    } catch {
      // fallthrough
    }
  }

  // filename="..." fallback
  const ascii = /filename="?([^";]+)"?/i.exec(disposition)
  if (ascii) return ascii[1].trim()

  return 'audit_logs.csv'
}

// ─── Phase 10.2b — DocUtil Search Scopes + Evaluation BFF ───────────────────
//
// AgentHub `/api/admin/docutil/search-scopes` + `/api/admin/docutil/evaluation` 진입점.
// 모두 axios `services/api.ts` 인스턴스 사용 — JWT 자동 부착 + 401 갱신.
// 백엔드 record DTO 와 1:1 정렬 (camelCase JSON, Program.cs JsonNamingPolicy).
//
// 추정 금지 — DocUtil OpenAPI 캡처(2026-05-10) + 백엔드 IDocUtilClient.cs 시그니처 일치.

const SEARCH_SCOPES_BASE = '/admin/docutil/search-scopes'
const EVALUATION_BASE = '/admin/docutil/evaluation'

// ─── Search Scopes 인터페이스 ────────────────────────────────────────────────

/** 검색 범위 한 행(목록 표시용 요약 — Detail 과 동일 24 필드 셋). */
export interface DocUtilSearchScopeSummary {
  id: string
  name: string
  description: string | null
  organizationId: string
  createdBy: string
  projectId: string | null
  boardId: string | null
  folderId: string | null
  locationPath: string | null
  chatbotEnabled: boolean
  chatbotFaqTemplate: string | null
  qaEnabled: boolean
  qaPromptTemplate: string | null
  qaLlmModel: string | null
  keywordSearchEnabled: boolean
  agentEnabled: boolean
  chunkSize: number
  chunkOverlap: number
  titleWeight: number
  keywordWeight: number
  contentWeight: number
  maxResults: number
  similarityThreshold: number
  createdAt: string
  updatedAt: string
}

/** 검색 범위 상세 — Summary 와 동일 셋. */
export type DocUtilSearchScopeDetail = DocUtilSearchScopeSummary

/** 검색 범위 목록 응답. */
export interface DocUtilSearchScopeList {
  items: DocUtilSearchScopeSummary[]
  total: number
  page: number
  size: number
}

/** 검색 범위 옵션(드롭다운용). */
export interface DocUtilSearchScopeOption {
  id: string
  name: string
  locationPath: string | null
}

/** 위치 옵션(프로젝트/보드/폴더). */
export interface DocUtilLocationOption {
  id: string
  name: string
  type: string
  path: string | null
}

/** 검색 범위 생성 요청. */
export interface DocUtilCreateScopeRequest {
  name: string
  description?: string | null
  projectId?: string | null
  boardId?: string | null
  folderId?: string | null
  chatbotEnabled?: boolean | null
  qaEnabled?: boolean | null
  keywordSearchEnabled?: boolean | null
  agentEnabled?: boolean | null
  chunkSize?: number | null
  chunkOverlap?: number | null
  titleWeight?: number | null
  keywordWeight?: number | null
  contentWeight?: number | null
  maxResults?: number | null
  similarityThreshold?: number | null
}

/** 검색 범위 수정 요청 (partial update). */
export type DocUtilUpdateScopeRequest = Partial<Omit<DocUtilCreateScopeRequest, 'name'>> & {
  name?: string | null
}

/** 검색 범위 환경 설정 요청 (모든 필드 nullable, default 적용). */
export interface DocUtilUpdateScopeEnvironmentRequest {
  chatbotEnabled?: boolean | null
  chatbotFaqTemplate?: string | null
  qaEnabled?: boolean | null
  qaPromptTemplate?: string | null
  qaLlmModel?: string | null
  keywordSearchEnabled?: boolean | null
  agentEnabled?: boolean | null
  chunkSize?: number | null
  chunkOverlap?: number | null
  titleWeight?: number | null
  keywordWeight?: number | null
  contentWeight?: number | null
  maxResults?: number | null
  similarityThreshold?: number | null
}

// ─── Evaluation 인터페이스 ───────────────────────────────────────────────────

/** 평가 가중치 설정. */
export interface DocUtilEvaluationConfig {
  id: string
  organizationId: string
  contextRelevancyWeight: number
  answerFaithfulnessWeight: number
  answerRelevancyWeight: number
  hallucinationWeight: number
}

/** 평가 가중치 수정 요청. */
export interface DocUtilUpdateEvaluationConfigRequest {
  contextRelevancyWeight: number
  answerFaithfulnessWeight: number
  answerRelevancyWeight: number
  hallucinationWeight: number
}

/** 평가 로그 한 항목. */
export interface DocUtilEvaluationLogEntry {
  id: string
  organizationId: string
  runId: string
  question: string
  answer: string
  contexts: Record<string, unknown> | null
  contextRelevancy: number
  answerFaithfulness: number
  answerRelevancy: number
  hallucinationScore: number
  hasHallucination: boolean
  hallucinationEvidence: Record<string, unknown> | null
  compositeScore: number
  judgeDetails: Record<string, unknown> | null
  runType: string
  questionIndex: number
  createdAt: string
}

/** 평가 로그 목록 응답. */
export interface DocUtilEvaluationLogList {
  items: DocUtilEvaluationLogEntry[]
  total: number
  page: number
  size: number
}

/** 평가 실행 요청 (questions 미지정 시 default 셋 사용). */
export interface DocUtilRunEvaluationRequest {
  questions?: string[] | null
}

/** 평가 실행 요약. */
export interface DocUtilEvaluationRunSummary {
  runId: string
  runType: string
  createdAt: string
  questionCount: number
  avgContextRelevancy: number
  avgAnswerFaithfulness: number
  avgAnswerRelevancy: number
  avgHallucinationScore: number
  avgCompositeScore: number
  hallucinationCount: number
}

/** 평가 실행 목록 응답 (page/size 없음 — items + total 만). */
export interface DocUtilEvaluationRunList {
  items: DocUtilEvaluationRunSummary[]
  total: number
}

/** 평가 트렌드 데이터 포인트. */
export interface DocUtilEvaluationTrendDataPoint {
  date: string
  avgContextRelevancy: number
  avgAnswerFaithfulness: number
  avgAnswerRelevancy: number
  avgHallucinationScore: number
  avgCompositeScore: number
}

/** 평가 트렌드 응답. */
export interface DocUtilEvaluationTrend {
  data: DocUtilEvaluationTrendDataPoint[]
}

/** 평가 로그 필터 (UI 폼 통합용). */
export interface EvaluationLogFilters {
  page?: number
  size?: number
  runId?: string
  runType?: string
  hasHallucination?: boolean
  minScore?: number
  maxScore?: number
}

// ─── Search Scopes API 호출 ─────────────────────────────────────────────────

/** 검색 범위 목록 조회. */
export async function listSearchScopes(
  page: number = 1,
  size: number = 20
): Promise<DocUtilSearchScopeList> {
  const { data } = await api.get<DocUtilSearchScopeList>(`${SEARCH_SCOPES_BASE}`, {
    params: { page, size }
  })
  return data
}

/** 검색 범위 옵션 목록(드롭다운) 조회. */
export async function listSearchScopeOptions(): Promise<DocUtilSearchScopeOption[]> {
  const { data } = await api.get<DocUtilSearchScopeOption[]>(`${SEARCH_SCOPES_BASE}/options`)
  return data
}

/**
 * 위치 카탈로그 조회.
 * @param locationType "project" | "board" | "folder" 중 하나(필수).
 */
export async function listSearchScopeLocations(
  locationType: 'project' | 'board' | 'folder'
): Promise<DocUtilLocationOption[]> {
  const { data } = await api.get<DocUtilLocationOption[]>(`${SEARCH_SCOPES_BASE}/locations`, {
    params: { locationType }
  })
  return data
}

/** 검색 범위 상세 조회. */
export async function getSearchScope(scopeId: string): Promise<DocUtilSearchScopeDetail> {
  const { data } = await api.get<DocUtilSearchScopeDetail>(
    `${SEARCH_SCOPES_BASE}/${encodeURIComponent(scopeId)}`
  )
  return data
}

/** 검색 범위 생성. */
export async function createSearchScope(
  request: DocUtilCreateScopeRequest
): Promise<DocUtilSearchScopeDetail> {
  const { data } = await api.post<DocUtilSearchScopeDetail>(`${SEARCH_SCOPES_BASE}`, request)
  return data
}

/** 검색 범위 수정. */
export async function updateSearchScope(
  scopeId: string,
  request: DocUtilUpdateScopeRequest
): Promise<DocUtilSearchScopeDetail> {
  const { data } = await api.put<DocUtilSearchScopeDetail>(
    `${SEARCH_SCOPES_BASE}/${encodeURIComponent(scopeId)}`,
    request
  )
  return data
}

/** 검색 범위 삭제. */
export async function deleteSearchScope(scopeId: string): Promise<void> {
  await api.delete<void>(`${SEARCH_SCOPES_BASE}/${encodeURIComponent(scopeId)}`)
}

/** 검색 범위 환경 설정 변경. */
export async function updateSearchScopeEnvironment(
  scopeId: string,
  request: DocUtilUpdateScopeEnvironmentRequest
): Promise<DocUtilSearchScopeDetail> {
  const { data } = await api.put<DocUtilSearchScopeDetail>(
    `${SEARCH_SCOPES_BASE}/${encodeURIComponent(scopeId)}/environment`,
    request
  )
  return data
}

/** 검색 범위 valid-id 조회 (free-form dict 응답). */
export async function getSearchScopeValidId(
  scopeId: string
): Promise<Record<string, unknown>> {
  const { data } = await api.get<Record<string, unknown>>(
    `${SEARCH_SCOPES_BASE}/${encodeURIComponent(scopeId)}/valid-id`
  )
  return data
}

// ─── Evaluation API 호출 ────────────────────────────────────────────────────

/** 평가 가중치 설정 조회. */
export async function getEvaluationConfig(): Promise<DocUtilEvaluationConfig> {
  const { data } = await api.get<DocUtilEvaluationConfig>(`${EVALUATION_BASE}/config`)
  return data
}

/** 평가 가중치 설정 수정. */
export async function updateEvaluationConfig(
  request: DocUtilUpdateEvaluationConfigRequest
): Promise<DocUtilEvaluationConfig> {
  const { data } = await api.put<DocUtilEvaluationConfig>(`${EVALUATION_BASE}/config`, request)
  return data
}

/** 평가 로그 목록 조회. */
export async function listEvaluationLogs(
  filters: EvaluationLogFilters = {}
): Promise<DocUtilEvaluationLogList> {
  const params: Record<string, string | number | boolean> = {}
  params.page = filters.page ?? 1
  params.size = filters.size ?? 20
  if (filters.runId && filters.runId.trim()) params.runId = filters.runId.trim()
  if (filters.runType && filters.runType.trim()) params.runType = filters.runType.trim()
  if (typeof filters.hasHallucination === 'boolean')
    params.hasHallucination = filters.hasHallucination
  if (typeof filters.minScore === 'number') params.minScore = filters.minScore
  if (typeof filters.maxScore === 'number') params.maxScore = filters.maxScore
  const { data } = await api.get<DocUtilEvaluationLogList>(`${EVALUATION_BASE}/logs`, {
    params
  })
  return data
}

/** 기본 평가 질문 목록 조회 (free-form dict). */
export async function getEvaluationQuestions(): Promise<Record<string, unknown>> {
  const { data } = await api.get<Record<string, unknown>>(`${EVALUATION_BASE}/questions`)
  return data
}

/**
 * 수동 평가 실행 트리거.
 *
 * 주의: 실제 LLM 호출(judge LLM) 트리거 — 비용/시간 영향 가능.
 * questions 가 null/빈 배열이면 DocUtil 의 default 질문 셋 사용.
 */
export async function runEvaluation(
  request: DocUtilRunEvaluationRequest = {}
): Promise<Record<string, unknown>> {
  const { data } = await api.post<Record<string, unknown>>(`${EVALUATION_BASE}/run`, request)
  return data
}

/** 최근 평가 실행 목록 조회. */
export async function listEvaluationRuns(limit: number = 30): Promise<DocUtilEvaluationRunList> {
  const { data } = await api.get<DocUtilEvaluationRunList>(`${EVALUATION_BASE}/runs`, {
    params: { limit }
  })
  return data
}

/** 평가 점수 추이 조회 (최근 N일). */
export async function getEvaluationTrend(days: number = 30): Promise<DocUtilEvaluationTrend> {
  const { data } = await api.get<DocUtilEvaluationTrend>(`${EVALUATION_BASE}/trend`, {
    params: { days }
  })
  return data
}

// ─── Phase 10.2c — DocUtil FAQ + Reports + Templates BFF ────────────────────
//
// AgentHub `/api/admin/docutil/faq` + `/api/admin/docutil/reports` 진입점.
// 모두 axios `services/api.ts` 인스턴스 사용 — JWT 자동 부착 + 401 갱신.
// 백엔드 record DTO 와 1:1 정렬 (camelCase JSON, Program.cs JsonNamingPolicy).
//
// 추정 금지 — DocUtil OpenAPI 캡처(2026-05-11) + 백엔드 IDocUtilClient.cs 시그니처 일치.

const FAQ_BASE = '/admin/docutil/faq'
const REPORTS_BASE = '/admin/docutil/reports'

// ─── FAQ 인터페이스 ──────────────────────────────────────────────────────────

/** FAQ 한 행(목록 표시용 — DocUtilFaq record 매핑). */
export interface DocUtilFaq {
  id: string
  searchScopeId: string | null
  organizationId: string
  question: string
  answer: string
  category: string | null
  displayOrder: number
  isActive: boolean
  createdAt: string
  updatedAt: string
}

/** FAQ 상세 — Faq 요약과 동일 셋. */
export type DocUtilFaqDetail = DocUtilFaq

/** FAQ 목록 응답. */
export interface DocUtilFaqList {
  items: DocUtilFaq[]
  total: number
  page: number
  size: number
}

/** FAQ 생성 요청. */
export interface CreateFaqRequest {
  question: string
  answer: string
  category?: string | null
  displayOrder?: number | null
  searchScopeId?: string | null
}

/** FAQ 수정 요청(모두 nullable, partial). */
export interface UpdateFaqRequest {
  question?: string | null
  answer?: string | null
  category?: string | null
  displayOrder?: number | null
  isActive?: boolean | null
}

// ─── Reports 인터페이스 ──────────────────────────────────────────────────────

/** 보고서 한 행 — DocUtilReport record 매핑(15 필드). */
export interface DocUtilReport {
  id: string
  templateId: string | null
  organizationId: string
  title: string
  status: string
  outputFormat: string
  outputStoragePath: string | null
  sourceDocumentIds: string[] | null
  sourceChatSessionId: string | null
  generationParams: Record<string, unknown> | null
  renderingMode: string | null
  jinja2Context: Record<string, unknown> | null
  errorMessage: string | null
  generatedBy: string
  createdAt: string
  completedAt: string | null
}

/** 보고서 상세. */
export type DocUtilReportDetail = DocUtilReport

/** 보고서 목록 응답. */
export interface DocUtilReportList {
  items: DocUtilReport[]
  total: number
  page: number
  size: number
}

/** 보고서 생성 요청. */
export interface GenerateReportRequest {
  title: string
  templateId?: string | null
  outputFormat?: string | null
  sourceDocumentIds?: string[] | null
  sourceChatSessionId?: string | null
  generationParams?: Record<string, unknown> | null
}

// ─── Report Templates 인터페이스 ────────────────────────────────────────────

/** 보고서 템플릿 한 행. */
export interface DocUtilReportTemplate {
  id: string
  organizationId: string
  name: string
  description: string | null
  format: string
  templateStoragePath: string | null
  schema: Record<string, unknown> | null
  createdBy: string
  createdAt: string
  updatedAt: string
}

/** 보고서 템플릿 상세. */
export type DocUtilReportTemplateDetail = DocUtilReportTemplate

/** 보고서 템플릿 목록 응답. */
export interface DocUtilReportTemplateList {
  items: DocUtilReportTemplate[]
  total: number
  page: number
  size: number
}

/** 보고서 템플릿 수정 요청(name?/description? partial). */
export interface UpdateReportTemplateRequest {
  name?: string | null
  description?: string | null
}

// ─── FAQ 함수 (5) ────────────────────────────────────────────────────────────

/** FAQ 목록 조회. */
export async function listFaqs(
  page: number = 1,
  size: number = 20,
  filters: { scopeId?: string; category?: string; q?: string } = {}
): Promise<DocUtilFaqList> {
  const params: Record<string, string | number> = { page, size }
  if (filters.scopeId && filters.scopeId.trim()) params.scopeId = filters.scopeId.trim()
  if (filters.category && filters.category.trim()) params.category = filters.category.trim()
  if (filters.q && filters.q.trim()) params.q = filters.q.trim()
  const { data } = await api.get<DocUtilFaqList>(`${FAQ_BASE}`, { params })
  return data
}

/** FAQ 상세 조회. 404 는 axios 가 throw — 호출자가 try/catch. */
export async function getFaq(faqId: string): Promise<DocUtilFaqDetail> {
  const { data } = await api.get<DocUtilFaqDetail>(`${FAQ_BASE}/${faqId}`)
  return data
}

/** FAQ 생성. */
export async function createFaq(request: CreateFaqRequest): Promise<DocUtilFaqDetail> {
  const { data } = await api.post<DocUtilFaqDetail>(`${FAQ_BASE}`, request)
  return data
}

/** FAQ 수정. */
export async function updateFaq(
  faqId: string,
  request: UpdateFaqRequest
): Promise<DocUtilFaqDetail> {
  const { data } = await api.put<DocUtilFaqDetail>(`${FAQ_BASE}/${faqId}`, request)
  return data
}

/** FAQ 삭제. */
export async function deleteFaq(faqId: string): Promise<void> {
  await api.delete(`${FAQ_BASE}/${faqId}`)
}

// ─── Reports 함수 (5) ────────────────────────────────────────────────────────

/** 보고서 목록 조회. */
export async function listReports(
  page: number = 1,
  size: number = 20,
  status?: string
): Promise<DocUtilReportList> {
  const params: Record<string, string | number> = { page, size }
  if (status && status.trim()) params.status = status.trim()
  const { data } = await api.get<DocUtilReportList>(`${REPORTS_BASE}`, { params })
  return data
}

/** 보고서 상세 조회. */
export async function getReport(reportId: string): Promise<DocUtilReportDetail> {
  const { data } = await api.get<DocUtilReportDetail>(`${REPORTS_BASE}/${reportId}`)
  return data
}

/** 보고서 생성(비동기 job 가능성 — 응답은 free-form dict). */
export async function generateReport(
  request: GenerateReportRequest
): Promise<Record<string, unknown>> {
  const { data } = await api.post<Record<string, unknown>>(
    `${REPORTS_BASE}/generate`,
    request
  )
  return data
}

/** 보고서 삭제. */
export async function deleteReport(reportId: string): Promise<void> {
  await api.delete(`${REPORTS_BASE}/${reportId}`)
}

/**
 * 보고서 다운로드(Blob).
 * 응답 헤더(Content-Disposition) 의 한국어 파일명도 함께 추출하여 반환.
 */
export async function downloadReport(
  reportId: string
): Promise<{ blob: Blob; fileName: string; contentType: string }> {
  const response = await api.get(`${REPORTS_BASE}/${reportId}/download`, {
    responseType: 'blob'
  })
  const contentType =
    (response.headers?.['content-type'] as string | undefined) ?? 'application/octet-stream'
  const fileName = parseReportFileName(
    response.headers?.['content-disposition'] as string | undefined,
    reportId
  )
  return { blob: response.data as Blob, fileName, contentType }
}

/**
 * Content-Disposition 헤더에서 filename 추출.
 * RFC 5987(`filename*=UTF-8''...`) 우선, 없으면 ASCII fallback.
 */
function parseReportFileName(disposition: string | undefined, reportId: string): string {
  const fallback = `report-${reportId}`
  if (!disposition) return fallback

  const star = /filename\*=(?:UTF-8|utf-8)''([^;]+)/i.exec(disposition)
  if (star) {
    try {
      return decodeURIComponent(star[1].trim().replace(/^"|"$/g, ''))
    } catch {
      // fallthrough
    }
  }

  const ascii = /filename="?([^";]+)"?/i.exec(disposition)
  if (ascii) return ascii[1].trim()

  return fallback
}

// ─── Report Templates 함수 (5) ───────────────────────────────────────────────

/** 보고서 템플릿 목록 조회. */
export async function listReportTemplates(
  page: number = 1,
  size: number = 20
): Promise<DocUtilReportTemplateList> {
  const { data } = await api.get<DocUtilReportTemplateList>(`${REPORTS_BASE}/templates`, {
    params: { page, size }
  })
  return data
}

/** 보고서 템플릿 상세 조회. */
export async function getReportTemplate(templateId: string): Promise<DocUtilReportTemplateDetail> {
  const { data } = await api.get<DocUtilReportTemplateDetail>(
    `${REPORTS_BASE}/templates/${templateId}`
  )
  return data
}

/**
 * 보고서 템플릿 생성 — multipart/form-data.
 * file 은 선택(없으면 이름/설명/format 만 등록).
 */
export async function createReportTemplate(
  name: string,
  format: string,
  description?: string,
  file?: File
): Promise<DocUtilReportTemplateDetail> {
  const form = new FormData()
  form.append('name', name)
  form.append('format', format)
  if (description) form.append('description', description)
  if (file) form.append('file', file, file.name)

  const { data } = await api.post<DocUtilReportTemplateDetail>(
    `${REPORTS_BASE}/templates`,
    form,
    {
      headers: { 'Content-Type': 'multipart/form-data' }
    }
  )
  return data
}

/** 보고서 템플릿 수정(name?/description? partial). */
export async function updateReportTemplate(
  templateId: string,
  request: UpdateReportTemplateRequest
): Promise<DocUtilReportTemplateDetail> {
  const { data } = await api.put<DocUtilReportTemplateDetail>(
    `${REPORTS_BASE}/templates/${templateId}`,
    request
  )
  return data
}

/** 보고서 템플릿 삭제. */
export async function deleteReportTemplate(templateId: string): Promise<void> {
  await api.delete(`${REPORTS_BASE}/templates/${templateId}`)
}

// ─── Phase 10.2d — DocUtil 문서 템플릿(Document Templates) BFF ──────────────
//
// AgentHub `/api/admin/docutil/templates/*` 진입점. DocUtil 의 Jinja2 기반 문서
// 생성용 템플릿(보고서 출력 템플릿과 무관 — 별도 도메인).
//
// 백엔드 record DTO(IDocUtilClient.cs 의 DocUtilDocumentTemplate*) 와 1:1.
// snake_case 키 ↔ camelCase 매핑은 Program.cs JsonNamingPolicy.CamelCase 가 처리.

const DOC_TEMPLATES_BASE = '/admin/docutil/templates'

// ─── 인터페이스 ──────────────────────────────────────────────────────────

/** 문서 템플릿 한 행(목록 표시용 — DocUtilDocumentTemplate record 매핑, 17 필드). */
export interface DocUtilDocumentTemplate {
  id: string
  organizationId: string
  name: string
  description: string | null
  templateType: string
  tone: string
  outputFormat: string
  schema: Record<string, unknown> | null
  samplePrompt: string | null
  isActive: boolean
  createdBy: string
  createdAt: string
  updatedAt: string
  templateStoragePath: string | null
  jinja2Variables: Record<string, unknown> | null
  renderingMode: string
  imageGenerationConfig: Record<string, unknown> | null
}

/** 문서 템플릿 상세 — 요약과 동일 셋. */
export type DocUtilDocumentTemplateDetail = DocUtilDocumentTemplate

/** 문서 템플릿 목록 응답. */
export interface DocUtilDocumentTemplateList {
  items: DocUtilDocumentTemplate[]
  total: number
  page: number
  size: number
}

/** 문서 템플릿 생성 요청(JSON, 메타데이터만). */
export interface CreateDocumentTemplateRequest {
  name: string
  templateType: string
  outputFormat: string
  description?: string | null
  tone?: string
  schema?: Record<string, unknown> | null
  samplePrompt?: string | null
  renderingMode?: string
  imageGenerationConfig?: Record<string, unknown> | null
}

/** 문서 템플릿 수정 요청(모두 nullable, partial). */
export interface UpdateDocumentTemplateRequest {
  name?: string | null
  description?: string | null
  templateType?: string | null
  tone?: string | null
  outputFormat?: string | null
  schema?: Record<string, unknown> | null
  samplePrompt?: string | null
  isActive?: boolean | null
  renderingMode?: string | null
  imageGenerationConfig?: Record<string, unknown> | null
}

/** 템플릿 변수 한 행(6 필드). */
export interface DocUtilDocumentTemplateVariable {
  name: string
  varType: string
  label: string | null
  description: string | null
  required: boolean
  category: string
}

/** 변수 메타 일괄 수정 요청. */
export interface UpdateDocumentTemplateVariablesRequest {
  variables: DocUtilDocumentTemplateVariable[]
}

/** 파일 업로드 응답. */
export interface DocUtilDocumentTemplateUpload {
  id: string
  name: string
  outputFormat: string
  renderingMode: string
  templateStoragePath: string | null
  variables: DocUtilDocumentTemplateVariable[]
}

/** AI 자동채움 요청. */
export interface AutoFillDocumentTemplateRequest {
  sourceDocumentIds: string[]
  aiPrompt?: string | null
}

/** AI 자동채움 응답. */
export interface DocUtilDocumentTemplateAutoFill {
  context: Record<string, unknown>
}

/** 변수 매핑 한 행. */
export interface DocUtilDocumentTemplateMapping {
  locationType: 'table_cell' | 'paragraph'
  variableName: string
  tableIndex?: number | null
  row?: number | null
  col?: number | null
  paragraphIndex?: number | null
  varType?: string
  label?: string | null
  category?: string
  fieldType?: 'short' | 'long'
}

/** 변수 매핑 적용 요청. */
export interface ApplyDocumentTemplateMappingRequest {
  mappings: DocUtilDocumentTemplateMapping[]
}

/** Convert 요청 — AI 분석 결과 wrapper. */
export interface ConvertDocumentTemplateRequest {
  aiAnalysis: Record<string, unknown>
}

/** 미리보기 다운로드 응답(Blob + 파일명). */
export interface DocumentTemplatePreview {
  blob: Blob
  fileName: string
  contentType: string
}

// ─── 함수 (15) ───────────────────────────────────────────────────────────

/** 문서 템플릿 목록 조회(페이징 + 유형 필터). */
export async function listDocumentTemplates(
  page: number = 1,
  size: number = 20,
  filters: { templateType?: string } = {}
): Promise<DocUtilDocumentTemplateList> {
  const params: Record<string, string | number> = { page, size }
  if (filters.templateType) params.templateType = filters.templateType
  const { data } = await api.get<DocUtilDocumentTemplateList>(DOC_TEMPLATES_BASE, { params })
  return data
}

/** 문서 템플릿 상세 조회. */
export async function getDocumentTemplate(
  templateId: string
): Promise<DocUtilDocumentTemplateDetail> {
  const { data } = await api.get<DocUtilDocumentTemplateDetail>(
    `${DOC_TEMPLATES_BASE}/${templateId}`
  )
  return data
}

/** 문서 템플릿 생성(JSON, 메타데이터만 — 파일 업로드는 별도). */
export async function createDocumentTemplate(
  request: CreateDocumentTemplateRequest
): Promise<DocUtilDocumentTemplateDetail> {
  const { data } = await api.post<DocUtilDocumentTemplateDetail>(
    DOC_TEMPLATES_BASE,
    request
  )
  return data
}

/** 문서 템플릿 수정(partial). */
export async function updateDocumentTemplate(
  templateId: string,
  request: UpdateDocumentTemplateRequest
): Promise<DocUtilDocumentTemplateDetail> {
  const { data } = await api.put<DocUtilDocumentTemplateDetail>(
    `${DOC_TEMPLATES_BASE}/${templateId}`,
    request
  )
  return data
}

/** 문서 템플릿 삭제. */
export async function deleteDocumentTemplate(templateId: string): Promise<void> {
  await api.delete(`${DOC_TEMPLATES_BASE}/${templateId}`)
}

/** 일반 Jinja2 템플릿 파일 업로드 — multipart/form-data. */
export async function uploadDocumentTemplate(
  templateType: string,
  outputFormat: string,
  file: File,
  options: { tone?: string; name?: string; description?: string } = {}
): Promise<DocUtilDocumentTemplateUpload> {
  const form = new FormData()
  form.append('templateType', templateType)
  form.append('outputFormat', outputFormat)
  if (options.tone) form.append('tone', options.tone)
  if (options.name) form.append('name', options.name)
  if (options.description) form.append('description', options.description)
  form.append('file', file, file.name)

  const { data } = await api.post<DocUtilDocumentTemplateUpload>(
    `${DOC_TEMPLATES_BASE}/upload`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return data
}

/** 빈 양식 업로드(AI 자동 Jinja2 변환) — multipart/form-data. */
export async function uploadBlankFormTemplate(
  templateType: string,
  outputFormat: string,
  file: File,
  options: { tone?: string; name?: string; description?: string } = {}
): Promise<DocUtilDocumentTemplateUpload> {
  const form = new FormData()
  form.append('templateType', templateType)
  form.append('outputFormat', outputFormat)
  if (options.tone) form.append('tone', options.tone)
  if (options.name) form.append('name', options.name)
  if (options.description) form.append('description', options.description)
  form.append('file', file, file.name)

  const { data } = await api.post<DocUtilDocumentTemplateUpload>(
    `${DOC_TEMPLATES_BASE}/upload-blank`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return data
}

/** 스마트 업로드(파일 자동 분석 후 처리 분기) — multipart/form-data. */
export async function uploadSmartTemplate(
  file: File,
  options: { templateType?: string; tone?: string; name?: string; description?: string } = {}
): Promise<DocUtilDocumentTemplateUpload> {
  const form = new FormData()
  if (options.templateType) form.append('templateType', options.templateType)
  if (options.tone) form.append('tone', options.tone)
  if (options.name) form.append('name', options.name)
  if (options.description) form.append('description', options.description)
  form.append('file', file, file.name)

  const { data } = await api.post<DocUtilDocumentTemplateUpload>(
    `${DOC_TEMPLATES_BASE}/upload-smart`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  )
  return data
}

/** 일반 문서 → Jinja2 변환(AI 분석 결과 적용). */
export async function convertDocumentTemplate(
  templateId: string,
  request: ConvertDocumentTemplateRequest
): Promise<DocUtilDocumentTemplateDetail> {
  const { data } = await api.post<DocUtilDocumentTemplateDetail>(
    `${DOC_TEMPLATES_BASE}/${templateId}/convert`,
    request
  )
  return data
}

/** AI 자동채움 — 소스 문서로부터 변수값 자동 생성. */
export async function autoFillDocumentTemplate(
  templateId: string,
  request: AutoFillDocumentTemplateRequest
): Promise<DocUtilDocumentTemplateAutoFill> {
  const { data } = await api.post<DocUtilDocumentTemplateAutoFill>(
    `${DOC_TEMPLATES_BASE}/${templateId}/auto-fill`,
    request
  )
  return data
}

/** 변수 메타 조회. */
export async function getDocumentTemplateVariables(
  templateId: string
): Promise<DocUtilDocumentTemplateVariable[]> {
  const { data } = await api.get<DocUtilDocumentTemplateVariable[]>(
    `${DOC_TEMPLATES_BASE}/${templateId}/variables`
  )
  return data
}

/** 변수 메타 일괄 수정. */
export async function updateDocumentTemplateVariables(
  templateId: string,
  request: UpdateDocumentTemplateVariablesRequest
): Promise<DocUtilDocumentTemplateDetail> {
  const { data } = await api.put<DocUtilDocumentTemplateDetail>(
    `${DOC_TEMPLATES_BASE}/${templateId}/variables`,
    request
  )
  return data
}

/** 에디터용 문서 구조 조회(paragraphs/tables/existing_variables). */
export async function getDocumentTemplateStructure(
  templateId: string
): Promise<Record<string, unknown>> {
  const { data } = await api.get<Record<string, unknown>>(
    `${DOC_TEMPLATES_BASE}/${templateId}/structure`
  )
  return data
}

/** 변수 매핑 적용. */
export async function applyDocumentTemplateMapping(
  templateId: string,
  request: ApplyDocumentTemplateMappingRequest
): Promise<DocUtilDocumentTemplateDetail> {
  const { data } = await api.post<DocUtilDocumentTemplateDetail>(
    `${DOC_TEMPLATES_BASE}/${templateId}/apply-mapping`,
    request
  )
  return data
}

/**
 * 템플릿 파일 미리보기 다운로드 — binary Blob 반환.
 * 호출자는 Blob 을 URL.createObjectURL 로 열거나 a[download] 로 저장.
 */
export async function previewDocumentTemplate(
  templateId: string
): Promise<DocumentTemplatePreview> {
  const response = await api.get(
    `${DOC_TEMPLATES_BASE}/${templateId}/preview`,
    { responseType: 'blob' }
  )
  const disposition = (response.headers['content-disposition'] as string | undefined) ?? ''
  const fileName = parseDocumentTemplateFileName(disposition, templateId)
  const contentType = (response.headers['content-type'] as string | undefined)
    ?? 'application/octet-stream'
  return { blob: response.data as Blob, fileName, contentType }
}

/**
 * Content-Disposition 헤더에서 filename 추출 (RFC 5987 우선).
 * Report download 의 parseReportFileName 과 동일 로직 — 별도 함수로 중복 회피하지 않음(도메인 격리).
 */
function parseDocumentTemplateFileName(disposition: string | undefined, templateId: string): string {
  const fallback = `template-${templateId}`
  if (!disposition) return fallback

  const star = /filename\*=(?:UTF-8|utf-8)''([^;]+)/i.exec(disposition)
  if (star) {
    try {
      return decodeURIComponent(star[1].trim().replace(/^"|"$/g, ''))
    } catch {
      // fallthrough
    }
  }

  const ascii = /filename="?([^";]+)"?/i.exec(disposition)
  if (ascii) return ascii[1].trim()

  return fallback
}

// ════════════════════════════════════════════════════════════════════════════
// Phase 10.2e (2026-05-11) — DocUtil API Keys + Agents + Documents V2
//
// 백엔드 record DTO(IDocUtilClient.cs) 와 1:1.
// snake_case 키 ↔ camelCase 매핑은 Program.cs JsonNamingPolicy.CamelCase 가 처리.
// ════════════════════════════════════════════════════════════════════════════

const API_KEYS_BASE = '/admin/docutil/api-keys'
const DOC_AGENTS_BASE = '/admin/docutil/agents'
const DOCUMENTS_V2_BASE = '/admin/docutil/documents-v2'

// ─── API Keys 인터페이스 ─────────────────────────────────────────────────

/** LLM API Key 한 행(마스킹). */
export interface DocUtilApiKey {
  id: string
  organizationId: string
  llmName: string
  apiKeyPrefix: string
  isVerified: boolean
  registeredBy: string | null
  createdAt: string
  updatedAt: string
}

/** LLM API Key 상세 — 목록과 동일 셋. */
export type DocUtilApiKeyDetail = DocUtilApiKey

/** LLM API Key 목록 응답. */
export interface DocUtilApiKeyList {
  items: DocUtilApiKey[]
  total: number
  page: number
  size: number
}

/** LLM API Key 등록 요청. */
export interface CreateApiKeyRequest {
  llmName: string
  apiKey: string
}

/** LLM API Key 검증 결과. */
export interface DocUtilApiKeyVerifyResult {
  isValid: boolean
  message: string
}

// ─── DocUtil Agents 인터페이스 (AgentHub Agent 와 별개) ─────────────────────

/** DocUtil 자체 에이전트 한 행. */
export interface DocUtilDocAgent {
  id: string
  organizationId: string
  name: string
  description: string | null
  agentType: string
  systemPrompt: string
  llmProvider: string | null
  llmModel: string
  temperature: number
  maxTokens: number
  isActive: boolean
  createdBy: string
  createdAt: string
  updatedAt: string
}

export type DocUtilDocAgentDetail = DocUtilDocAgent

export interface DocUtilDocAgentList {
  items: DocUtilDocAgent[]
  total: number
  page: number
  size: number
}

export interface CreateDocAgentRequest {
  name: string
  agentType: string
  systemPrompt: string
  description?: string | null
  llmProvider?: string | null
  llmModel?: string
  temperature?: number
  maxTokens?: number
}

export interface UpdateDocAgentRequest {
  name?: string | null
  description?: string | null
  agentType?: string | null
  systemPrompt?: string | null
  llmProvider?: string | null
  llmModel?: string | null
  temperature?: number | null
  maxTokens?: number | null
  isActive?: boolean | null
}

// ─── Documents V2 인터페이스 ────────────────────────────────────────────

export type DocumentV2Type =
  | 'slide_report'
  | 'docx_report'
  | 'proposal'
  | 'minutes'
  | 'one_pager'
  | 'weekly_status'
  | 'freeform_doc'

export type DocumentV2Mode = 'free_generation' | 'template_fill'

export type DocumentV2PatchType = 'page' | 'component' | 'tokens'

export type DocumentV2ExportFormat = 'pptx' | 'docx' | 'hwpx' | 'pdf' | 'html'

export type DocumentV2ExportStatusValue =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'

export interface DocUtilDocumentV2 {
  id: string
  organizationId: string
  generatedByUserId: string | null
  agentId: string | null
  templateId: string | null
  documentType: string
  mode: string
  title: string
  status: string
  errorMessage: string | null
  llmProvider: string | null
  llmModel: string | null
  promptTokens: number | null
  completionTokens: number | null
  createdAt: string
  completedAt: string | null
  documentSchema: Record<string, unknown> | null
}

export type DocUtilDocumentV2Detail = DocUtilDocumentV2

export interface DocUtilDocumentV2List {
  items: DocUtilDocumentV2[]
  total: number
  limit: number
  offset: number
}

export interface GenerateDocumentV2Request {
  prompt: string
  documentType: DocumentV2Type
  mode?: DocumentV2Mode
  sourceDocumentIds?: string[] | null
  agentId?: string | null
  designTokens?: Record<string, unknown> | null
}

export interface PatchDocumentV2Request {
  patchType: DocumentV2PatchType
  data: Record<string, unknown>
  pageId?: string | null
  componentId?: string | null
  expectedVersion?: number | null
}

export interface RequestDocumentV2ExportRequest {
  format: DocumentV2ExportFormat
}

export interface DocumentV2ExportJobAck {
  jobId: string
}

export interface DocumentV2ExportStatus {
  status: DocumentV2ExportStatusValue
  progress: number
  downloadUrl: string | null
  error: string | null
}

export interface DocumentV2Download {
  blob: Blob
  fileName: string
  contentType: string
}

// ─── API Keys 함수 (4) ───────────────────────────────────────────────────

/** LLM API Key 목록 조회(페이징). 응답 prefix 는 마스킹된 prefix. */
export async function listApiKeys(
  page: number = 1,
  size: number = 20
): Promise<DocUtilApiKeyList> {
  const { data } = await api.get<DocUtilApiKeyList>(API_KEYS_BASE, {
    params: { page, size }
  })
  return data
}

/**
 * LLM API Key 등록 — 평문 키는 요청 시 한 번만 전송된다.
 * DocUtil 측이 AES 암호화 후 폐기하며, 응답에는 마스킹 prefix 만 포함된다.
 */
export async function createApiKey(
  request: CreateApiKeyRequest
): Promise<DocUtilApiKeyDetail> {
  const { data } = await api.post<DocUtilApiKeyDetail>(API_KEYS_BASE, request)
  return data
}

/** LLM API Key 회수(삭제). */
export async function deleteApiKey(keyId: string): Promise<void> {
  await api.delete(`${API_KEYS_BASE}/${keyId}`)
}

/**
 * LLM API Key 검증 — DocUtil 이 프로바이더에 1회 호출 후 is_valid + message 반환.
 * 외부 LLM 응답 지연으로 수십 초 소요 가능 — 로딩 처리 권장.
 */
export async function verifyApiKey(
  keyId: string
): Promise<DocUtilApiKeyVerifyResult> {
  const { data } = await api.post<DocUtilApiKeyVerifyResult>(
    `${API_KEYS_BASE}/${keyId}/verify`
  )
  return data
}

// ─── DocUtil Agents 함수 (5) ──────────────────────────────────────────────

/** DocUtil 에이전트 목록(페이징 + agent_type 필터). */
export async function listDocAgents(
  page: number = 1,
  size: number = 20,
  filters: { agentType?: string } = {}
): Promise<DocUtilDocAgentList> {
  const params: Record<string, string | number> = { page, size }
  if (filters.agentType) params.agentType = filters.agentType
  const { data } = await api.get<DocUtilDocAgentList>(DOC_AGENTS_BASE, { params })
  return data
}

/** DocUtil 에이전트 상세. */
export async function getDocAgent(
  agentId: string
): Promise<DocUtilDocAgentDetail> {
  const { data } = await api.get<DocUtilDocAgentDetail>(
    `${DOC_AGENTS_BASE}/${agentId}`
  )
  return data
}

/** DocUtil 에이전트 생성. */
export async function createDocAgent(
  request: CreateDocAgentRequest
): Promise<DocUtilDocAgentDetail> {
  const { data } = await api.post<DocUtilDocAgentDetail>(
    DOC_AGENTS_BASE,
    request
  )
  return data
}

/** DocUtil 에이전트 부분 수정(보낸 필드만 갱신). */
export async function updateDocAgent(
  agentId: string,
  request: UpdateDocAgentRequest
): Promise<DocUtilDocAgentDetail> {
  const { data } = await api.put<DocUtilDocAgentDetail>(
    `${DOC_AGENTS_BASE}/${agentId}`,
    request
  )
  return data
}

/** DocUtil 에이전트 삭제. */
export async function deleteDocAgent(agentId: string): Promise<void> {
  await api.delete(`${DOC_AGENTS_BASE}/${agentId}`)
}

// ─── Documents V2 함수 (7) ──────────────────────────────────────────────

/** 문서 V2 목록(limit/offset + 필터). */
export async function listDocumentsV2(
  limit: number = 20,
  offset: number = 0,
  filters: { documentType?: string; mode?: string } = {}
): Promise<DocUtilDocumentV2List> {
  const params: Record<string, string | number> = { limit, offset }
  if (filters.documentType) params.documentType = filters.documentType
  if (filters.mode) params.mode = filters.mode
  const { data } = await api.get<DocUtilDocumentV2List>(DOCUMENTS_V2_BASE, {
    params
  })
  return data
}

/** 문서 V2 단건. */
export async function getDocumentV2(
  documentId: string
): Promise<DocUtilDocumentV2Detail> {
  const { data } = await api.get<DocUtilDocumentV2Detail>(
    `${DOCUMENTS_V2_BASE}/${documentId}`
  )
  return data
}

/**
 * 문서 V2 자유 생성(Mode A) — 202 Accepted.
 * 생성 직후 status 는 generating 일 수 있어 단건 조회 폴링이 필요할 수 있다.
 */
export async function generateDocumentV2(
  request: GenerateDocumentV2Request
): Promise<DocUtilDocumentV2Detail> {
  const { data } = await api.post<DocUtilDocumentV2Detail>(
    DOCUMENTS_V2_BASE,
    request
  )
  return data
}

/** 문서 V2 부분 패치(page / component / tokens). expectedVersion 으로 낙관적 락. */
export async function patchDocumentV2(
  documentId: string,
  request: PatchDocumentV2Request
): Promise<DocUtilDocumentV2Detail> {
  const { data } = await api.patch<DocUtilDocumentV2Detail>(
    `${DOCUMENTS_V2_BASE}/${documentId}`,
    request
  )
  return data
}

/** 문서 V2 비동기 export 요청 — 202 + job_id. */
export async function requestDocumentV2Export(
  documentId: string,
  request: RequestDocumentV2ExportRequest
): Promise<DocumentV2ExportJobAck> {
  const { data } = await api.post<DocumentV2ExportJobAck>(
    `${DOCUMENTS_V2_BASE}/${documentId}/export`,
    request
  )
  return data
}

/** Export 작업 상태 폴링. */
export async function getDocumentV2ExportStatus(
  jobId: string
): Promise<DocumentV2ExportStatus> {
  const { data } = await api.get<DocumentV2ExportStatus>(
    `${DOCUMENTS_V2_BASE}/exports/${jobId}`
  )
  return data
}

/** Export 결과 다운로드(백엔드 프록시). Blob + 파일명/Content-Type 반환. */
export async function downloadDocumentV2Export(
  jobId: string
): Promise<DocumentV2Download> {
  const response = await api.get(
    `${DOCUMENTS_V2_BASE}/exports/${jobId}/download`,
    { responseType: 'blob' }
  )
  const disposition = (response.headers['content-disposition'] as string | undefined) ?? ''
  const fileName = parseDocumentV2FileName(disposition, jobId)
  const contentType =
    (response.headers['content-type'] as string | undefined) ?? 'application/octet-stream'
  return {
    blob: response.data as Blob,
    fileName,
    contentType
  }
}

/**
 * Documents V2 export 응답의 Content-Disposition 헤더에서 파일명 추출 (RFC 5987 우선).
 * previewDocumentTemplate 의 parseDocumentTemplateFileName 과 동일 로직 — 도메인 격리 위해 별도 함수.
 */
function parseDocumentV2FileName(disposition: string | undefined, jobId: string): string {
  const fallback = `document-${jobId}`
  if (!disposition) return fallback

  const star = /filename\*=(?:UTF-8|utf-8)''([^;]+)/i.exec(disposition)
  if (star) {
    try {
      return decodeURIComponent(star[1].trim().replace(/^"|"$/g, ''))
    } catch {
      // fallthrough
    }
  }

  const ascii = /filename="?([^";]+)"?/i.exec(disposition)
  if (ascii) return ascii[1].trim()

  return fallback
}

export default {
  listDocuments,
  uploadDocument,
  getDocument,
  deleteDocument,
  getChunks,
  search,
  listCollections,
  listUsers,
  getUser,
  updateUserStatus,
  updateUser,
  deleteUser,
  // Phase 10.1b — 조직/부서/할당량
  getOrganization,
  updateOrganization,
  listDepartments,
  createDepartment,
  updateDepartment,
  deleteDepartment,
  getDepartmentMembers,
  getOrganizationQuota,
  updateOrganizationQuota,
  // Phase 10.1c — 프로젝트/보드
  listProjects,
  getProjectTree,
  getProject,
  createProject,
  updateProject,
  deleteProject,
  getProjectMembers,
  addProjectMember,
  removeProjectMember,
  getProjectDepartments,
  listProjectBoards,
  createProjectBoard,
  getProjectBoard,
  updateProjectBoard,
  deleteProjectBoard,
  // Phase 10.2a — 대시보드/감사 로그
  getDashboardMetrics,
  getDashboardResponseTimes,
  getDashboardSearchErrors,
  getDashboardSearchUsage,
  getDashboardUploadStatus,
  listAuditLogs,
  exportAuditLogs,
  // Phase 10.2b — Search Scopes + Evaluation
  listSearchScopes,
  listSearchScopeOptions,
  listSearchScopeLocations,
  getSearchScope,
  createSearchScope,
  updateSearchScope,
  deleteSearchScope,
  updateSearchScopeEnvironment,
  getSearchScopeValidId,
  getEvaluationConfig,
  updateEvaluationConfig,
  listEvaluationLogs,
  getEvaluationQuestions,
  runEvaluation,
  listEvaluationRuns,
  getEvaluationTrend,
  // Phase 10.2c — FAQ + Reports + Templates
  listFaqs,
  getFaq,
  createFaq,
  updateFaq,
  deleteFaq,
  listReports,
  getReport,
  generateReport,
  deleteReport,
  downloadReport,
  listReportTemplates,
  getReportTemplate,
  createReportTemplate,
  updateReportTemplate,
  deleteReportTemplate,
  // Phase 10.2d — Document Templates
  listDocumentTemplates,
  getDocumentTemplate,
  createDocumentTemplate,
  updateDocumentTemplate,
  deleteDocumentTemplate,
  uploadDocumentTemplate,
  uploadBlankFormTemplate,
  uploadSmartTemplate,
  convertDocumentTemplate,
  autoFillDocumentTemplate,
  getDocumentTemplateVariables,
  updateDocumentTemplateVariables,
  getDocumentTemplateStructure,
  applyDocumentTemplateMapping,
  previewDocumentTemplate,
  // Phase 10.2e — API Keys + Doc Agents + Documents V2
  listApiKeys,
  createApiKey,
  deleteApiKey,
  verifyApiKey,
  listDocAgents,
  getDocAgent,
  createDocAgent,
  updateDocAgent,
  deleteDocAgent,
  listDocumentsV2,
  getDocumentV2,
  generateDocumentV2,
  patchDocumentV2,
  requestDocumentV2Export,
  getDocumentV2ExportStatus,
  downloadDocumentV2Export
}
