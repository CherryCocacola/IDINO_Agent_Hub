<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilSearchTest.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilSearchTest.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-outline-secondary btn-sm me-2"
          @click="showHistory = !showHistory"
          :aria-pressed="showHistory"
          :aria-label="t('adminDocutilSearchTest.toggleHistory')"
        >
          <i
            :class="['bi', showHistory ? 'bi-clock-fill' : 'bi-clock-history']"
            aria-hidden="true"
          ></i>
          {{
            showHistory
              ? t('adminDocutilSearchTest.hideHistory')
              : t('adminDocutilSearchTest.showHistory')
          }}
        </button>
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="refreshAll"
          :disabled="scopesLoading || searching"
          :aria-label="t('adminDocutilSearchTest.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminDocutilSearchTest.refresh') }}
        </button>
      </div>
    </div>

    <!-- 에러 알림 -->
    <div
      v-if="errorMessage"
      class="alert alert-danger d-flex justify-content-between align-items-center"
      role="alert"
    >
      <span>{{ errorMessage }}</span>
      <button
        type="button"
        class="btn-close"
        :aria-label="t('common.close')"
        @click="errorMessage = ''"
      ></button>
    </div>

    <div class="row g-3">
      <!-- 메인 영역 -->
      <div :class="showHistory ? 'col-lg-9' : 'col-12'">
        <!-- Scope + SearchType + Query -->
        <section class="card aiuiux-card mb-3">
          <div class="card-body">
            <!-- 검색 범위 -->
            <div class="mb-3">
              <label for="search-test-scope" class="form-label small fw-medium">
                {{ t('adminDocutilSearchTest.scope') }}
              </label>
              <div v-if="scopesLoading" class="d-flex align-items-center gap-2 small text-muted">
                <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
                {{ t('common.loading') }}
              </div>
              <select
                v-else
                id="search-test-scope"
                v-model="selectedScopeId"
                class="form-select form-select-sm"
                style="max-width: 480px;"
                :aria-label="t('adminDocutilSearchTest.scope')"
              >
                <option value="">{{ t('adminDocutilSearchTest.scopeNone') }}</option>
                <option
                  v-for="scope in scopes"
                  :key="scope.id"
                  :value="scope.id"
                >
                  {{ scope.name }}
                  <template v-if="scope.locationPath">— {{ scope.locationPath }}</template>
                </option>
              </select>
              <small v-if="!scopesLoading && scopes.length === 0" class="text-muted">
                {{ t('adminDocutilSearchTest.scopeEmpty') }}
              </small>
            </div>

            <!-- 검색 모드 탭 -->
            <ul
              class="nav nav-pills mb-3"
              role="tablist"
              :aria-label="t('adminDocutilSearchTest.searchTypeLabel')"
            >
              <li
                v-for="mode in searchModes"
                :key="mode.value"
                class="nav-item me-1"
                role="presentation"
              >
                <button
                  type="button"
                  class="nav-link btn-sm py-1 px-3"
                  :class="{ active: searchType === mode.value }"
                  role="tab"
                  :aria-selected="searchType === mode.value"
                  @click="searchType = mode.value"
                >
                  <i :class="['bi', mode.icon, 'me-1']" aria-hidden="true"></i>
                  {{ t(`adminDocutilSearchTest.modes.${mode.value}`) }}
                </button>
              </li>
            </ul>

            <!-- 질의 입력 -->
            <form class="d-flex gap-2" @submit.prevent="handleSearch">
              <input
                type="text"
                class="form-control form-control-sm"
                v-model="query"
                :placeholder="
                  isChatMode
                    ? t('adminDocutilSearchTest.queryPlaceholderChat')
                    : t('adminDocutilSearchTest.queryPlaceholderSearch')
                "
                :aria-label="t('adminDocutilSearchTest.query')"
                :disabled="searching"
              />
              <button
                type="submit"
                class="btn btn-primary btn-sm"
                :disabled="searching || !query.trim()"
              >
                <span
                  v-if="searching"
                  class="spinner-border spinner-border-sm me-1"
                  aria-hidden="true"
                ></span>
                <i v-else class="bi bi-search me-1" aria-hidden="true"></i>
                {{
                  searching
                    ? t('adminDocutilSearchTest.searching')
                    : t('adminDocutilSearchTest.searchButton')
                }}
              </button>
            </form>
          </div>
        </section>

        <!-- 결과 영역 -->
        <section class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h6 class="mb-0">
              <i class="bi bi-list-task me-1" aria-hidden="true"></i>
              {{ t('adminDocutilSearchTest.results') }}
              <span
                v-if="hasSearched && !searching && isChunkMode"
                class="text-muted small ms-2"
              >
                ({{ chunkResults.length }})
              </span>
            </h6>
          </div>
          <div class="card-body">
            <!-- 검색 중 -->
            <div v-if="searching" class="text-center py-5">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
              <p class="text-muted small mt-2 mb-0">
                {{ t('adminDocutilSearchTest.searching') }}
              </p>
            </div>

            <!-- 아직 검색 안 함 -->
            <div v-else-if="!hasSearched" class="text-center text-muted py-5">
              <i class="bi bi-search fs-2 d-block mb-2" aria-hidden="true"></i>
              <p class="mb-0">{{ t('adminDocutilSearchTest.emptyState') }}</p>
            </div>

            <!-- chunk 결과 (hybrid / keyword / admin-test) -->
            <div v-else-if="isChunkMode">
              <div v-if="chunkResults.length === 0" class="text-center text-muted py-5">
                <i class="bi bi-inbox fs-2 d-block mb-2" aria-hidden="true"></i>
                <p class="mb-0">{{ t('adminDocutilSearchTest.noResults') }}</p>
              </div>
              <ul v-else class="list-unstyled mb-0">
                <li
                  v-for="chunk in chunkResults"
                  :key="chunk.id"
                  class="border rounded p-3 mb-2"
                >
                  <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="d-flex align-items-center">
                      <i
                        class="bi bi-file-earmark-text me-2 text-secondary"
                        aria-hidden="true"
                      ></i>
                      <span class="fw-medium">{{ chunk.documentName || '-' }}</span>
                    </div>
                    <span class="badge bg-secondary-subtle text-secondary-emphasis">
                      {{ t('adminDocutilSearchTest.score') }}:
                      {{ formatScore(chunk.score) }}
                    </span>
                  </div>
                  <p class="small mb-2 text-body" style="white-space: pre-wrap;">
                    {{ chunk.content }}
                  </p>
                  <div
                    v-if="Array.isArray(chunk.highlights) && chunk.highlights.length > 0"
                    class="mt-2"
                  >
                    <small class="text-muted fw-medium d-block mb-1">
                      {{ t('adminDocutilSearchTest.highlights') }}
                    </small>
                    <!--
                      highlights 는 백엔드(DocUtil) 가 검색 매치 표시용 HTML 조각을 보내올 수 있다.
                      XSS 방지를 위해 본 화면은 항상 textContent 로 안전 렌더링한다.
                    -->
                    <div
                      v-for="(hl, idx) in chunk.highlights"
                      :key="idx"
                      class="rounded px-2 py-1 mb-1 highlight-chip"
                    >
                      {{ stripHtml(hl) }}
                    </div>
                  </div>
                </li>
              </ul>
            </div>

            <!-- chatbot / qa 결과 -->
            <div v-else-if="isChatMode && chatResult">
              <article class="border rounded p-3 mb-3">
                <h6 class="d-flex align-items-center mb-2">
                  <i class="bi bi-chat-square-text me-1 text-primary" aria-hidden="true"></i>
                  {{ t('adminDocutilSearchTest.answer') }}
                </h6>
                <p class="mb-0 small" style="white-space: pre-wrap;">{{ chatResult.answer }}</p>
                <div
                  v-if="searchType === 'qa' && chatResult.hallucinationScore !== undefined && chatResult.hallucinationScore !== null"
                  class="mt-3 pt-2 border-top"
                >
                  <small class="text-muted">
                    {{ t('adminDocutilSearchTest.hallucinationScore') }}:
                    <span
                      class="badge ms-1"
                      :class="hallucinationBadgeClass(chatResult.hallucinationScore)"
                    >
                      {{ formatScore(chatResult.hallucinationScore) }}
                    </span>
                  </small>
                </div>
              </article>

              <div v-if="chatResult.citations && chatResult.citations.length > 0">
                <h6 class="text-muted small fw-semibold mb-2">
                  {{ t('adminDocutilSearchTest.citations') }} ({{ chatResult.citations.length }})
                </h6>
                <div class="row g-2">
                  <div
                    v-for="(citation, idx) in chatResult.citations"
                    :key="idx"
                    class="col-md-6"
                  >
                    <article class="border rounded p-2 h-100">
                      <div class="d-flex align-items-center mb-1">
                        <i
                          class="bi bi-file-earmark me-1 text-secondary"
                          aria-hidden="true"
                        ></i>
                        <small class="fw-medium">{{ citation.documentName || '-' }}</small>
                        <span
                          v-if="citation.page"
                          class="badge bg-light text-muted ms-2 small"
                        >
                          p.{{ citation.page }}
                        </span>
                      </div>
                      <p class="small text-muted mb-0 citation-snippet">
                        {{ citation.content }}
                      </p>
                    </article>
                  </div>
                </div>
              </div>

              <div
                v-else-if="searchType === 'chatbot' || searchType === 'qa'"
                class="text-muted small mt-2"
              >
                <i class="bi bi-info-circle me-1" aria-hidden="true"></i>
                {{ t('adminDocutilSearchTest.noCitations') }}
              </div>
            </div>

            <!-- chat 모드인데 응답 없음 -->
            <div
              v-else-if="isChatMode && !chatResult"
              class="text-center text-muted py-5"
            >
              <i class="bi bi-emoji-frown fs-2 d-block mb-2" aria-hidden="true"></i>
              <p class="mb-0">{{ t('adminDocutilSearchTest.noAnswer') }}</p>
            </div>
          </div>
        </section>
      </div>

      <!-- History 사이드바 -->
      <aside v-if="showHistory" class="col-lg-3">
        <div class="card aiuiux-card h-100">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
              <i class="bi bi-clock-history me-1" aria-hidden="true"></i>
              {{ t('adminDocutilSearchTest.historyTitle') }}
            </h6>
            <button
              class="btn btn-link btn-sm p-0"
              @click="loadHistory"
              :disabled="historyLoading"
              :aria-label="t('adminDocutilSearchTest.refreshHistory')"
            >
              <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
            </button>
          </div>
          <div class="card-body p-2" style="max-height: 70vh; overflow-y: auto;">
            <div v-if="historyLoading" class="text-center py-4">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ t('common.loading') }}</span>
              </div>
            </div>
            <div v-else-if="history.length === 0" class="text-center text-muted py-4 small">
              {{ t('adminDocutilSearchTest.historyEmpty') }}
            </div>
            <ul v-else class="list-unstyled mb-0">
              <li
                v-for="entry in history"
                :key="entry.id"
                class="mb-1"
              >
                <button
                  type="button"
                  class="btn btn-link text-start w-100 p-2 history-item"
                  @click="loadFromHistory(entry)"
                >
                  <div class="text-truncate fw-medium small">{{ entry.query }}</div>
                  <div class="d-flex align-items-center gap-2 mt-1">
                    <span class="badge bg-secondary-subtle text-secondary-emphasis small">
                      {{ entry.searchType }}
                    </span>
                    <small class="text-muted">
                      <i class="bi bi-clock me-1" aria-hidden="true"></i>
                      {{ formatTimestamp(entry.timestamp) }}
                    </small>
                  </div>
                  <small class="text-muted d-block">
                    {{ t('adminDocutilSearchTest.historyResultCount', { count: entry.resultCount ?? 0 }) }}
                    <template v-if="entry.scopeName">— {{ entry.scopeName }}</template>
                  </small>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AdminDocUtilSearchTest — DocUtil 운영자 검색 품질 테스트 화면 (트랙 A1 Phase B, 2026-05-25).
 *
 * 진입 경로: /admin/docutil-search-test (Admin / SuperAdmin 전용)
 *
 * 책임:
 *   1. 검색 범위(scope) dropdown 표시
 *   2. 4 모드(hybrid / chatbot / qa / keyword) 검색 + 결과 표시
 *      - chunk 결과: document_name + content + score + highlights
 *      - chat 결과: answer + citations (+ qa 모드에서 hallucination_score)
 *   3. 검색 히스토리 사이드바 — 클릭 시 query/searchType 복원
 *
 * 보안:
 *   highlights 는 DocUtil 이 HTML 조각을 보낼 수 있어 v-html 금지. stripHtml() 으로
 *   태그를 제거한 텍스트만 표시(XSS 차단). 운영자 페이지지만 안전 기본값 채택.
 *
 * 추가 모드(admin-test):
 *   DocUtil 의 `/search/test` 와 동일한 admin bypass 모드 — UI 상은 hybrid 와 동일한
 *   chunk 결과를 표시. 백엔드 BFF 가 별도 endpoint 로 노출.
 */
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  listSearchTestScopes,
  searchTestHybrid,
  searchTestChatbot,
  searchTestQa,
  searchTestKeyword,
  searchTestAdminTest,
  listSearchTestHistory,
  type DocUtilSearchTestScopeOption,
  type DocUtilSearchTestChunkResult,
  type DocUtilSearchTestChatResult,
  type DocUtilSearchTestHistoryEntry
} from '@/services/docutilService'

const { t } = useI18n()

type SearchType = 'hybrid' | 'chatbot' | 'qa' | 'keyword' | 'admin-test'

interface SearchMode {
  value: SearchType
  icon: string
}

const searchModes: SearchMode[] = [
  { value: 'hybrid', icon: 'bi-shuffle' },
  { value: 'chatbot', icon: 'bi-chat-dots' },
  { value: 'qa', icon: 'bi-patch-question' },
  { value: 'keyword', icon: 'bi-type' },
  { value: 'admin-test', icon: 'bi-shield-check' }
]

// ── 상태 ────────────────────────────────────────────────────────────────────
const scopes = ref<DocUtilSearchTestScopeOption[]>([])
const selectedScopeId = ref<string>('')
const scopesLoading = ref<boolean>(false)

const searchType = ref<SearchType>('hybrid')
const query = ref<string>('')
const searching = ref<boolean>(false)
const hasSearched = ref<boolean>(false)

const chunkResults = ref<DocUtilSearchTestChunkResult[]>([])
const chatResult = ref<DocUtilSearchTestChatResult | null>(null)

const history = ref<DocUtilSearchTestHistoryEntry[]>([])
const historyLoading = ref<boolean>(false)
const showHistory = ref<boolean>(true)

const errorMessage = ref<string>('')

// ── 파생 ────────────────────────────────────────────────────────────────────
const isChunkMode = computed<boolean>(
  () =>
    searchType.value === 'hybrid' ||
    searchType.value === 'keyword' ||
    searchType.value === 'admin-test'
)

const isChatMode = computed<boolean>(
  () => searchType.value === 'chatbot' || searchType.value === 'qa'
)

// ── 데이터 로드 ─────────────────────────────────────────────────────────────
async function loadScopes(): Promise<void> {
  scopesLoading.value = true
  errorMessage.value = ''
  try {
    const data = await listSearchTestScopes()
    scopes.value = data
    if (data.length > 0 && !selectedScopeId.value) {
      selectedScopeId.value = data[0].id
    }
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    scopesLoading.value = false
  }
}

async function loadHistory(): Promise<void> {
  historyLoading.value = true
  try {
    const data = await listSearchTestHistory()
    history.value = data
  } catch (err: unknown) {
    // 히스토리 실패는 메인 흐름을 막지 않음.
    // eslint-disable-next-line no-console
    console.warn('[AdminDocUtilSearchTest] 히스토리 로드 실패:', err)
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

function refreshAll(): void {
  loadScopes()
  loadHistory()
}

// ── 검색 실행 ───────────────────────────────────────────────────────────────
async function handleSearch(): Promise<void> {
  const trimmedQuery = query.value.trim()
  if (!trimmedQuery) {
    errorMessage.value = t('adminDocutilSearchTest.queryRequired')
    return
  }
  // scope 선택은 선택사항 — 백엔드가 글로벌 검색을 허용할 수 있으므로 0-length 도 통과.

  searching.value = true
  hasSearched.value = true
  errorMessage.value = ''
  chunkResults.value = []
  chatResult.value = null

  const scopeId = selectedScopeId.value || null

  try {
    if (searchType.value === 'chatbot') {
      chatResult.value = await searchTestChatbot({
        searchScopeId: scopeId,
        query: trimmedQuery
      })
    } else if (searchType.value === 'qa') {
      chatResult.value = await searchTestQa({
        searchScopeId: scopeId,
        query: trimmedQuery
      })
    } else if (searchType.value === 'keyword') {
      chunkResults.value = await searchTestKeyword({
        searchScopeId: scopeId,
        query: trimmedQuery
      })
    } else if (searchType.value === 'admin-test') {
      chunkResults.value = await searchTestAdminTest({
        searchScopeId: scopeId,
        query: trimmedQuery
      })
    } else {
      // hybrid (기본)
      chunkResults.value = await searchTestHybrid({
        searchScopeId: scopeId,
        query: trimmedQuery
      })
    }
    // 검색 성공 후 히스토리 비동기 갱신.
    loadHistory()
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    searching.value = false
  }
}

function loadFromHistory(entry: DocUtilSearchTestHistoryEntry): void {
  query.value = entry.query
  if (
    entry.searchType === 'hybrid' ||
    entry.searchType === 'chatbot' ||
    entry.searchType === 'qa' ||
    entry.searchType === 'keyword' ||
    entry.searchType === 'admin-test'
  ) {
    searchType.value = entry.searchType
  }
}

// ── 표시 헬퍼 ───────────────────────────────────────────────────────────────
function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-'
  // 0~1 범위는 % 로, 그 외는 소수 3자리로 표시.
  if (value >= 0 && value <= 1) {
    return `${(value * 100).toFixed(1)}%`
  }
  return value.toFixed(3)
}

function hallucinationBadgeClass(score: number | null | undefined): string {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return 'bg-secondary-subtle text-secondary-emphasis'
  }
  // 환각 점수가 높을수록 위험(붉은색). 0.5 / 0.8 임계값 사용.
  if (score >= 0.8) return 'bg-danger-subtle text-danger-emphasis'
  if (score >= 0.5) return 'bg-warning-subtle text-warning-emphasis'
  return 'bg-success-subtle text-success-emphasis'
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString('ko-KR', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return value
  }
}

/**
 * highlights 의 HTML 태그를 안전하게 제거한다.
 * v-html 을 사용하지 않으므로 v-text/{{ }} 와 함께 호출되어야 XSS 가 차단된다.
 */
function stripHtml(html: string): string {
  if (!html) return ''
  // DOMParser 대신 정규식 + temp element 조합으로 일관 처리. 어떤 환경에서도 동작.
  const tmp = document.createElement('div')
  tmp.innerHTML = html
  return tmp.textContent || tmp.innerText || ''
}

function extractErrorMessage(err: unknown): string {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const resp = (err as { response?: { data?: { message?: string } } }).response
    if (resp?.data?.message) return resp.data.message
  }
  if (err instanceof Error) return err.message
  return t('adminDocutilSearchTest.errorUnknown')
}

onMounted(() => {
  loadScopes()
  loadHistory()
})
</script>

<style scoped>
.nav-pills .nav-link {
  color: var(--bs-secondary-color);
  background: transparent;
  border: 1px solid var(--bs-border-color);
}

.nav-pills .nav-link.active {
  color: #fff;
  background: var(--bs-primary);
  border-color: var(--bs-primary);
}

.highlight-chip {
  background: rgba(255, 235, 130, 0.4);
  font-size: 0.78rem;
}

.citation-snippet {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.history-item {
  text-decoration: none;
  color: var(--bs-body-color);
  border-radius: var(--radius-sm, 6px);
}

.history-item:hover {
  background-color: var(--bs-secondary-bg);
}
</style>
