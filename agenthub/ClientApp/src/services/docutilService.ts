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
 * DocUtil 사용자 삭제. 백엔드 204 NoContent — 반환값 없음.
 * 성공 시 백엔드가 캐시 일괄 무효화.
 */
export async function deleteUser(id: string): Promise<void> {
  await api.delete(`${USERS_BASE}/users/${encodeURIComponent(id)}`)
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
  deleteUser
}
