/**
 * docUtilStore — 운영자 KB(DocUtil BFF) Pinia 스토어.
 *
 * Vue View 가 직접 docutilService 를 호출하지 않고 본 스토어를 경유한다.
 * 이유: 페이지네이션 / 로딩 / 에러 상태 일관 관리 + 재진입 시 마지막 검색 보존.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import docutilService, {
  type DocumentSummary,
  type DocumentDetail,
  type SearchHit,
  type Chunk
} from '@/services/docutilService'

interface PaginationState {
  page: number
  size: number
  total: number
}

export const useDocUtilStore = defineStore('docUtil', () => {
  // ─── 상태 ─────────────────────────────────────────────────────────────────
  const documents = ref<DocumentSummary[]>([])
  const currentDocument = ref<DocumentDetail | null>(null)
  const currentChunks = ref<Chunk[]>([])
  const searchResults = ref<SearchHit[]>([])
  const lastSearchQuery = ref<string>('')

  const pagination = ref<PaginationState>({ page: 1, size: 20, total: 0 })
  const currentFolderId = ref<string | null>(null)

  const isLoading = ref<boolean>(false)
  const isUploading = ref<boolean>(false)
  const isSearching = ref<boolean>(false)
  const error = ref<string | null>(null)

  // ─── 헬퍼 ─────────────────────────────────────────────────────────────────
  function extractMessage(err: any, fallback: string): string {
    return err?.response?.data?.message || err?.message || fallback
  }

  function clearError(): void {
    error.value = null
  }

  // ─── 액션 ─────────────────────────────────────────────────────────────────

  /**
   * 문서 목록 로드. folderId / page / size 를 변경하면 새 페이지를 가져온다.
   * 호출 후 documents / pagination / currentFolderId 가 갱신된다.
   */
  async function fetchDocuments(folderId?: string, page: number = 1, size: number = 20): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const result = await docutilService.listDocuments(folderId, page, size)
      documents.value = result.items ?? []
      pagination.value = {
        page: result.page,
        size: result.size,
        total: result.total
      }
      currentFolderId.value = folderId ?? null
    } catch (err: any) {
      error.value = extractMessage(err, '문서 목록을 불러오지 못했습니다.')
      documents.value = []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 문서 업로드. 성공 시 현재 폴더 기준으로 목록을 새로고침한다.
   */
  async function uploadDocument(file: File, folderId?: string, visibility?: string): Promise<boolean> {
    isUploading.value = true
    error.value = null
    try {
      await docutilService.uploadDocument(file, folderId, visibility)
      await fetchDocuments(folderId ?? currentFolderId.value ?? undefined, 1, pagination.value.size)
      return true
    } catch (err: any) {
      error.value = extractMessage(err, '문서 업로드에 실패했습니다.')
      return false
    } finally {
      isUploading.value = false
    }
  }

  /**
   * 문서 삭제. 성공 시 현재 페이지 목록을 새로고침한다.
   */
  async function removeDocument(id: string): Promise<boolean> {
    isLoading.value = true
    error.value = null
    try {
      await docutilService.deleteDocument(id)
      if (currentDocument.value?.id === id) {
        currentDocument.value = null
        currentChunks.value = []
      }
      await fetchDocuments(currentFolderId.value ?? undefined, pagination.value.page, pagination.value.size)
      return true
    } catch (err: any) {
      error.value = extractMessage(err, '문서 삭제에 실패했습니다.')
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 문서 상세 + 청크 로드. 상세 페이지 진입 시 호출.
   * 404 응답은 currentDocument = null 로 셋업되며 error 는 설정되지 않는다.
   */
  async function loadDocumentDetail(id: string): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const detail = await docutilService.getDocument(id)
      currentDocument.value = detail
      if (detail) {
        try {
          currentChunks.value = await docutilService.getChunks(id)
        } catch (err: any) {
          // 청크 조회는 보조 정보 — 실패해도 상세 표시는 막지 않는다.
          currentChunks.value = []
          console.warn('[docUtilStore] 청크 조회 실패:', err)
        }
      } else {
        currentChunks.value = []
      }
    } catch (err: any) {
      error.value = extractMessage(err, '문서 상세를 불러오지 못했습니다.')
      currentDocument.value = null
      currentChunks.value = []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * KB 검색. 결과는 searchResults 에 저장되고 lastSearchQuery 가 갱신된다.
   */
  async function searchKnowledgeBase(
    query: string,
    collectionRef?: string,
    maxResults: number = 10
  ): Promise<void> {
    const trimmed = query.trim()
    if (!trimmed) {
      searchResults.value = []
      lastSearchQuery.value = ''
      return
    }

    isSearching.value = true
    error.value = null
    try {
      const result = await docutilService.search(trimmed, collectionRef, maxResults)
      searchResults.value = result.results ?? []
      lastSearchQuery.value = trimmed
    } catch (err: any) {
      error.value = extractMessage(err, '검색에 실패했습니다.')
      searchResults.value = []
    } finally {
      isSearching.value = false
    }
  }

  function clearSearch(): void {
    searchResults.value = []
    lastSearchQuery.value = ''
  }

  return {
    // 상태
    documents,
    currentDocument,
    currentChunks,
    searchResults,
    lastSearchQuery,
    pagination,
    currentFolderId,
    isLoading,
    isUploading,
    isSearching,
    error,
    // 액션
    fetchDocuments,
    uploadDocument,
    removeDocument,
    loadDocumentDetail,
    searchKnowledgeBase,
    clearSearch,
    clearError
  }
})
