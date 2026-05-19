<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">{{ t('adminDocutilUsers.title') }}</h1>
        <p class="page-desc">{{ t('adminDocutilUsers.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <button
          class="btn btn-primary btn-sm"
          @click="refresh"
          :disabled="loading"
          :aria-label="t('adminDocutilUsers.refresh')"
        >
          <i class="bi bi-arrow-clockwise" aria-hidden="true"></i>
          {{ t('adminDocutilUsers.refresh') }}
        </button>
      </div>
    </div>

    <!-- 검색/필터 바 -->
    <div class="card aiuiux-card mb-3">
      <div class="card-body py-2 px-3">
        <form class="row g-2 align-items-center" @submit.prevent="onSearch">
          <div class="col-md-5">
            <div class="input-group input-group-sm">
              <span class="input-group-text">
                <i class="bi bi-search" aria-hidden="true"></i>
              </span>
              <input
                type="text"
                class="form-control"
                v-model="searchQuery"
                :placeholder="t('adminDocutilUsers.searchPlaceholder')"
                :aria-label="t('adminDocutilUsers.search')"
              />
            </div>
          </div>
          <div class="col-md-3">
            <select
              class="form-select form-select-sm"
              v-model="roleFilter"
              :aria-label="t('adminDocutilUsers.filterRole')"
            >
              <option value="">{{ t('adminDocutilUsers.allRoles') }}</option>
              <option value="admin">{{ t('adminDocutilUsers.roleAdmin') }}</option>
              <option value="member">{{ t('adminDocutilUsers.roleMember') }}</option>
            </select>
          </div>
          <div class="col-md-2">
            <select
              class="form-select form-select-sm"
              v-model="statusFilter"
              :aria-label="t('adminDocutilUsers.filterStatus')"
            >
              <option value="">{{ t('adminDocutilUsers.allStatuses') }}</option>
              <option value="active">{{ t('adminDocutilUsers.statusActive') }}</option>
              <option value="inactive">{{ t('adminDocutilUsers.statusInactive') }}</option>
              <option value="locked">{{ t('adminDocutilUsers.statusLocked') }}</option>
            </select>
          </div>
          <div class="col-md-2 d-flex gap-1">
            <button type="submit" class="btn btn-sm btn-primary flex-grow-1" :disabled="loading">
              {{ t('adminDocutilUsers.applyFilters') }}
            </button>
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary"
              @click="onClearFilters"
              :title="t('adminDocutilUsers.clearFilters')"
              :aria-label="t('adminDocutilUsers.clearFilters')"
            >
              <i class="bi bi-x-lg" aria-hidden="true"></i>
            </button>
          </div>
        </form>
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

    <!-- 사용자 목록 -->
    <div class="card aiuiux-card">
      <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
        <h6 class="mb-0">
          <i class="bi bi-people-fill me-1" aria-hidden="true"></i>
          {{ t('adminDocutilUsers.users') }}
          <span class="text-muted small ms-2" v-if="total > 0">({{ total }})</span>
        </h6>
      </div>
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border spinner-border-sm" role="status">
            <span class="visually-hidden">{{ t('common.loading') }}</span>
          </div>
        </div>
        <div v-else-if="items.length === 0" class="text-center text-muted py-5">
          <i class="bi bi-inbox fs-2 d-block mb-2" aria-hidden="true"></i>
          <p class="mb-0">{{ t('adminDocutilUsers.empty') }}</p>
        </div>
        <div v-else class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th scope="col">{{ t('adminDocutilUsers.colUsername') }}</th>
                <th scope="col">{{ t('adminDocutilUsers.colEmail') }}</th>
                <th scope="col" style="width: 100px;">{{ t('adminDocutilUsers.colRole') }}</th>
                <th scope="col" style="width: 120px;">{{ t('adminDocutilUsers.colStatus') }}</th>
                <th scope="col" style="width: 180px;">{{ t('adminDocutilUsers.colCreatedAt') }}</th>
                <th scope="col" style="width: 220px;" class="text-end">
                  {{ t('common.actions') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in items" :key="user.id">
                <td>
                  <div class="d-flex align-items-center">
                    <i class="bi bi-person-circle me-2 text-primary" aria-hidden="true"></i>
                    <div>
                      <div class="fw-medium">{{ user.username }}</div>
                      <code class="text-muted small">{{ user.id }}</code>
                    </div>
                  </div>
                </td>
                <td>
                  <span class="text-body">{{ user.email }}</span>
                </td>
                <td>
                  <span :class="['badge', roleBadgeClass(user.role)]">{{ user.role }}</span>
                </td>
                <td>
                  <span :class="['badge', statusBadgeClass(user.status)]">
                    {{ statusLabel(user.status) }}
                  </span>
                </td>
                <td>
                  <small class="text-muted">{{ formatDate(user.createdAt) }}</small>
                </td>
                <td class="text-end">
                  <button
                    class="btn btn-sm btn-link"
                    @click="openDetail(user.id)"
                    :aria-label="t('adminDocutilUsers.viewDetail')"
                  >
                    <i class="bi bi-eye" aria-hidden="true"></i>
                    {{ t('adminDocutilUsers.viewDetail') }}
                  </button>
                  <button
                    class="btn btn-sm btn-link"
                    @click="openEditModal(user)"
                    :aria-label="t('adminDocutilUsers.edit')"
                  >
                    <i class="bi bi-pencil" aria-hidden="true"></i>
                    {{ t('adminDocutilUsers.edit') }}
                  </button>
                  <button
                    class="btn btn-sm btn-link"
                    @click="confirmToggleStatus(user)"
                    :aria-label="
                      user.status === 'active'
                        ? t('adminDocutilUsers.deactivate')
                        : t('adminDocutilUsers.activate')
                    "
                  >
                    <i
                      :class="user.status === 'active' ? 'bi bi-pause-circle' : 'bi bi-play-circle'"
                      aria-hidden="true"
                    ></i>
                    {{
                      user.status === 'active'
                        ? t('adminDocutilUsers.deactivate')
                        : t('adminDocutilUsers.activate')
                    }}
                  </button>
                  <button
                    class="btn btn-sm btn-link text-danger"
                    @click="confirmDelete(user)"
                    :aria-label="t('adminDocutilUsers.delete')"
                  >
                    <i class="bi bi-trash" aria-hidden="true"></i>
                    {{ t('adminDocutilUsers.delete') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 페이지네이션 -->
      <div
        v-if="items.length > 0 && totalPages > 1"
        class="card-footer bg-transparent d-flex justify-content-between align-items-center"
      >
        <small class="text-muted">
          {{ t('adminDocutilUsers.pageInfo', { page: page, total: totalPages }) }}
        </small>
        <nav :aria-label="t('adminDocutilUsers.pagination')">
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: page <= 1 }">
              <button class="page-link" @click="goPage(page - 1)" :disabled="page <= 1">
                <i class="bi bi-chevron-left" aria-hidden="true"></i>
              </button>
            </li>
            <li class="page-item active">
              <span class="page-link">{{ page }}</span>
            </li>
            <li class="page-item" :class="{ disabled: page >= totalPages }">
              <button class="page-link" @click="goPage(page + 1)" :disabled="page >= totalPages">
                <i class="bi bi-chevron-right" aria-hidden="true"></i>
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 상세 모달 -->
    <div
      v-if="detailUser"
      class="modal-overlay d-flex align-items-center justify-content-center"
      role="dialog"
      :aria-label="t('adminDocutilUsers.modalTitle')"
      @click.self="detailUser = null"
    >
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">
            <i class="bi bi-person-vcard me-1" aria-hidden="true"></i>
            {{ t('adminDocutilUsers.modalTitle') }}
          </h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="detailUser = null"
          ></button>
        </div>
        <div class="card-body">
          <dl class="row mb-0 small">
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colId') }}</dt>
            <dd class="col-sm-8">
              <code>{{ detailUser.id }}</code>
            </dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colUsername') }}</dt>
            <dd class="col-sm-8">{{ detailUser.username }}</dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colEmail') }}</dt>
            <dd class="col-sm-8">{{ detailUser.email }}</dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colRole') }}</dt>
            <dd class="col-sm-8">
              <span :class="['badge', roleBadgeClass(detailUser.role)]">{{ detailUser.role }}</span>
            </dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colStatus') }}</dt>
            <dd class="col-sm-8">
              <span :class="['badge', statusBadgeClass(detailUser.status)]">
                {{ statusLabel(detailUser.status) }}
              </span>
            </dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colOrgId') }}</dt>
            <dd class="col-sm-8">
              <code>{{ detailUser.organizationId }}</code>
            </dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colDeptId') }}</dt>
            <dd class="col-sm-8">
              <code v-if="detailUser.departmentId">{{ detailUser.departmentId }}</code>
              <span v-else class="text-muted">-</span>
            </dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colLanguage') }}</dt>
            <dd class="col-sm-8">{{ detailUser.language || '-' }}</dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colLastLogin') }}</dt>
            <dd class="col-sm-8">{{ formatDate(detailUser.lastLoginAt) }}</dd>
            <dt class="col-sm-4">{{ t('adminDocutilUsers.colCreatedAt') }}</dt>
            <dd class="col-sm-8">{{ formatDate(detailUser.createdAt) }}</dd>
          </dl>
        </div>
        <div class="card-footer bg-transparent text-end">
          <button class="btn btn-sm btn-outline-secondary" @click="detailUser = null">
            {{ t('common.close') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 수정 모달 (트랙 #101 F7) -->
    <div
      v-if="editModal.open"
      class="modal-overlay d-flex align-items-center justify-content-center"
      role="dialog"
      :aria-label="t('adminDocutilUsers.modalEditTitle')"
      @click.self="closeEditModal"
    >
      <div class="modal-card card aiuiux-card">
        <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
          <h6 class="mb-0">
            <i class="bi bi-pencil-square me-1" aria-hidden="true"></i>
            {{ t('adminDocutilUsers.modalEditTitle') }}
            <code class="ms-2 small">{{ editModal.username }}</code>
          </h6>
          <button
            type="button"
            class="btn-close"
            :aria-label="t('common.close')"
            @click="closeEditModal"
          ></button>
        </div>
        <form @submit.prevent="submitEditModal">
          <div class="card-body">
            <p class="small text-muted mb-3">
              {{ t('adminDocutilUsers.editHint') }}
            </p>
            <div class="mb-3">
              <label for="edit-email" class="form-label small">
                {{ t('adminDocutilUsers.colEmail') }}
              </label>
              <input
                id="edit-email"
                type="email"
                class="form-control form-control-sm"
                v-model.trim="editModal.email"
                maxlength="255"
                :placeholder="t('adminDocutilUsers.emailPlaceholder')"
              />
            </div>
            <div class="row g-2 mb-3">
              <div class="col-sm-6">
                <label for="edit-role" class="form-label small">
                  {{ t('adminDocutilUsers.colRole') }}
                </label>
                <select
                  id="edit-role"
                  class="form-select form-select-sm"
                  v-model="editModal.role"
                >
                  <option value="member">{{ t('adminDocutilUsers.roleMember') }}</option>
                  <option value="admin">{{ t('adminDocutilUsers.roleAdmin') }}</option>
                  <option value="super_admin">{{ t('adminDocutilUsers.roleSuperAdmin') }}</option>
                  <option value="viewer">{{ t('adminDocutilUsers.roleViewer') }}</option>
                </select>
              </div>
              <div class="col-sm-6">
                <label for="edit-status" class="form-label small">
                  {{ t('adminDocutilUsers.colStatus') }}
                </label>
                <select
                  id="edit-status"
                  class="form-select form-select-sm"
                  v-model="editModal.status"
                >
                  <option value="active">{{ t('adminDocutilUsers.statusActive') }}</option>
                  <option value="inactive">{{ t('adminDocutilUsers.statusInactive') }}</option>
                  <option value="locked">{{ t('adminDocutilUsers.statusLocked') }}</option>
                </select>
              </div>
            </div>
            <div class="row g-2 mb-3">
              <div class="col-sm-7">
                <label for="edit-department" class="form-label small">
                  {{ t('adminDocutilUsers.colDeptId') }}
                </label>
                <select
                  id="edit-department"
                  class="form-select form-select-sm"
                  v-model="editModal.departmentId"
                  :disabled="loadingDepartments"
                >
                  <option value="">{{ t('adminDocutilUsers.departmentNone') }}</option>
                  <option
                    v-for="d in departmentOptions"
                    :key="d.id"
                    :value="d.id"
                  >
                    {{ '— '.repeat(d.depth) }}{{ d.name }}
                  </option>
                </select>
                <small v-if="loadingDepartments" class="form-text text-muted">
                  {{ t('common.loading') }}
                </small>
              </div>
              <div class="col-sm-5">
                <label for="edit-language" class="form-label small">
                  {{ t('adminDocutilUsers.colLanguage') }}
                </label>
                <select
                  id="edit-language"
                  class="form-select form-select-sm"
                  v-model="editModal.language"
                >
                  <option value="">{{ t('adminDocutilUsers.languageNone') }}</option>
                  <option value="ko">{{ t('adminDocutilUsers.languageKo') }}</option>
                  <option value="en">{{ t('adminDocutilUsers.languageEn') }}</option>
                  <option value="vi">{{ t('adminDocutilUsers.languageVi') }}</option>
                </select>
              </div>
            </div>
            <div v-if="editModal.error" class="alert alert-danger small mb-0">
              {{ editModal.error }}
            </div>
          </div>
          <div class="card-footer bg-transparent text-end">
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary me-2"
              @click="closeEditModal"
              :disabled="editModal.submitting"
            >
              {{ t('common.cancel') }}
            </button>
            <button
              type="submit"
              class="btn btn-sm btn-primary"
              :disabled="editModal.submitting"
            >
              <span v-if="editModal.submitting" class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>
              {{ t('adminDocutilUsers.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * AdminDocUtilUsers — DocUtil 사용자 운영자 관리 화면 (Phase 10.1a, 2026-05-10).
 *
 * 진입 경로: /admin/docutil-users (Admin / SuperAdmin 전용)
 *
 * 책임:
 *   1. 사용자 목록(페이지/검색/role/status 필터) 조회
 *   2. 상세 모달 표시 (read-only 전체 필드)
 *   3. 상태 토글(active ↔ inactive) — 한국어 confirm 후 PUT
 *   4. 삭제 — 한국어 confirm 후 DELETE (영구 삭제 경고 명시)
 *
 * 백엔드 BFF: /api/admin/docutil/users[/{id}[/status]]
 *   - 권한 게이트: [Authorize(Roles="Admin,SuperAdmin")]
 *   - 인증: services/api.ts axios 인터셉터 — JWT 자동 부착, 401 갱신
 *   - 캐시: 백엔드가 5분 TTL + version-key invalidate (mutation 후 자동 갱신)
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  listUsers,
  updateUserStatus,
  updateUser,
  deleteUser,
  listDepartments,
  type DocUtilUserSummary,
  type DocUtilUserDetail,
  type DocUtilUserStatus,
  type DocUtilUserUpdate,
  type DocUtilDepartment
} from '@/services/docutilService'

const { t } = useI18n()
const router = useRouter()

// ── 상태 ─────────────────────────────────────────────────────────────────
const items = ref<DocUtilUserSummary[]>([])
const total = ref<number>(0)
const page = ref<number>(1)
const size = ref<number>(20)
const loading = ref<boolean>(false)
const errorMessage = ref<string>('')

const searchQuery = ref<string>('')
const roleFilter = ref<string>('')
const statusFilter = ref<string>('')

const detailUser = ref<DocUtilUserDetail | null>(null)

// ── 트랙 #101 F7: 사용자 일반 정보 수정 모달 상태 ─────────────────────────
interface EditModalState {
  open: boolean
  userId: string
  username: string
  email: string
  role: string
  status: DocUtilUserStatus
  /** 빈 문자열은 "부서 없음"(백엔드 → DocUtil null 매핑). */
  departmentId: string
  /** 빈 문자열은 "변경하지 않음" 의도. */
  language: string
  /** 모달 오픈 시점 원본값 (변경 여부 비교용). */
  original: {
    email: string
    role: string
    status: DocUtilUserStatus
    departmentId: string
    language: string
  } | null
  error: string
  submitting: boolean
}

const editModal = ref<EditModalState>({
  open: false,
  userId: '',
  username: '',
  email: '',
  role: 'member',
  status: 'active',
  departmentId: '',
  language: '',
  original: null,
  error: '',
  submitting: false
})

// 부서 dropdown 옵션 — 모달 오픈 시 lazy load (path 사전순 + depth 들여쓰기).
const departmentOptions = ref<DocUtilDepartment[]>([])
const loadingDepartments = ref<boolean>(false)
let departmentsLoaded = false

async function ensureDepartmentsLoaded(): Promise<void> {
  if (departmentsLoaded) return
  loadingDepartments.value = true
  try {
    const list = await listDepartments()
    departmentOptions.value = [...list].sort((a, b) => a.path.localeCompare(b.path))
    departmentsLoaded = true
  } catch (err: unknown) {
    // 모달 오픈 흐름을 죽이지 않기 위해 부서 dropdown 만 비워두고 폼은 계속 사용 가능.
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loadingDepartments.value = false
  }
}

const totalPages = computed<number>(() => {
  if (size.value <= 0) return 1
  return Math.max(1, Math.ceil(total.value / size.value))
})

// ── 데이터 로드 ───────────────────────────────────────────────────────────
async function fetchPage(targetPage: number = page.value): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await listUsers(
      targetPage,
      size.value,
      searchQuery.value || undefined,
      roleFilter.value || undefined,
      statusFilter.value || undefined
    )
    items.value = data.items
    total.value = data.total
    page.value = data.page
    size.value = data.size
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function refresh(): void {
  fetchPage(page.value)
}

function onSearch(): void {
  fetchPage(1)
}

function onClearFilters(): void {
  searchQuery.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  fetchPage(1)
}

function goPage(target: number): void {
  if (target < 1 || target > totalPages.value) return
  fetchPage(target)
}

// ── 상세 모달 ─────────────────────────────────────────────────────────────
function openDetail(id: string): void {
  // 목록에서 이미 모든 필드를 가지고 있으므로 추가 조회 없이 표시.
  // 향후 트랙(10.1b) 에서 부서명 / 프로젝트 멤버십 등 합성 필드가 추가되면
  // GET /api/admin/docutil/users/{id} 호출로 전환 (getUser 함수 이미 준비됨).
  const found = items.value.find(u => u.id === id)
  if (found) {
    detailUser.value = { ...found }
  }
}

// ── 트랙 #101 F7: 수정 모달 ───────────────────────────────────────────────
function openEditModal(user: DocUtilUserSummary): void {
  const normalizedStatus: DocUtilUserStatus =
    user.status === 'inactive' || user.status === 'locked' ? user.status : 'active'
  const initialDept = user.departmentId ?? ''
  const initialLang = user.language ?? ''
  editModal.value = {
    open: true,
    userId: user.id,
    username: user.username,
    email: user.email ?? '',
    role: user.role || 'member',
    status: normalizedStatus,
    departmentId: initialDept,
    language: initialLang,
    original: {
      email: user.email ?? '',
      role: user.role || 'member',
      status: normalizedStatus,
      departmentId: initialDept,
      language: initialLang
    },
    error: '',
    submitting: false
  }
  // 부서 dropdown 옵션 lazy load (한 번만).
  void ensureDepartmentsLoaded()
}

function closeEditModal(): void {
  editModal.value.open = false
}

async function submitEditModal(): Promise<void> {
  const original = editModal.value.original
  if (!original) return

  // 변경된 필드만 payload 에 담는다 (백엔드는 최소 1 필드 요구).
  const payload: DocUtilUserUpdate = {}
  const trimmedEmail = editModal.value.email.trim()
  if (trimmedEmail !== original.email) payload.email = trimmedEmail
  if (editModal.value.role !== original.role) payload.role = editModal.value.role
  if (editModal.value.status !== original.status) payload.status = editModal.value.status
  if (editModal.value.departmentId !== original.departmentId) {
    // 빈 문자열 = 부서 해제 의도 (백엔드가 DocUtil null 로 매핑).
    payload.departmentId = editModal.value.departmentId
  }
  if (editModal.value.language !== original.language) {
    payload.language = editModal.value.language
  }

  if (Object.keys(payload).length === 0) {
    editModal.value.error = t('adminDocutilUsers.editNoChanges')
    return
  }

  editModal.value.submitting = true
  editModal.value.error = ''
  try {
    const updated = await updateUser(editModal.value.userId, payload)
    // 목록의 해당 행 즉시 반영 — 백엔드 캐시 invalidate 도 함께 발생.
    const idx = items.value.findIndex(u => u.id === editModal.value.userId)
    if (idx >= 0) {
      items.value[idx] = updated
    }
    editModal.value.open = false
  } catch (err: unknown) {
    editModal.value.error = extractErrorMessage(err)
  } finally {
    editModal.value.submitting = false
  }
}

// ── 상태 토글 ─────────────────────────────────────────────────────────────
async function confirmToggleStatus(user: DocUtilUserSummary): Promise<void> {
  const next: DocUtilUserStatus = user.status === 'active' ? 'inactive' : 'active'
  const message = t('adminDocutilUsers.toggleStatusConfirm', {
    username: user.username,
    next: statusLabel(next)
  })
  if (!window.confirm(message)) return

  loading.value = true
  errorMessage.value = ''
  try {
    const updated = await updateUserStatus(user.id, next)
    // 목록의 해당 행 즉시 반영 — 백엔드 캐시는 invalidate 되므로 다음 fetch 도 fresh.
    const idx = items.value.findIndex(u => u.id === user.id)
    if (idx >= 0) {
      items.value[idx] = updated
    }
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

// ── 삭제 ──────────────────────────────────────────────────────────────────
async function confirmDelete(user: DocUtilUserSummary): Promise<void> {
  const message = t('adminDocutilUsers.deleteConfirm', { username: user.username })
  if (!window.confirm(message)) return
  if (!window.confirm(t('adminDocutilUsers.deleteConfirmFinal'))) return

  loading.value = true
  errorMessage.value = ''
  try {
    await deleteUser(user.id)
    // 목록에서 제거 — 백엔드가 캐시 invalidate 하므로 다음 페이지 호출도 fresh.
    items.value = items.value.filter(u => u.id !== user.id)
    total.value = Math.max(0, total.value - 1)
    // 현재 페이지가 비고 이전 페이지가 있다면 한 페이지 앞으로.
    if (items.value.length === 0 && page.value > 1) {
      await fetchPage(page.value - 1)
    }
  } catch (err: unknown) {
    errorMessage.value = extractErrorMessage(err)
  } finally {
    loading.value = false
  }
}

// ── 표시 헬퍼 ─────────────────────────────────────────────────────────────
function roleBadgeClass(role: string): string {
  const lower = (role || '').toLowerCase()
  if (lower === 'admin' || lower === 'superadmin') {
    return 'bg-primary-subtle text-primary-emphasis'
  }
  return 'bg-secondary-subtle text-secondary-emphasis'
}

function statusBadgeClass(status: string): string {
  const lower = (status || '').toLowerCase()
  if (lower === 'active') return 'bg-success-subtle text-success-emphasis'
  if (lower === 'inactive') return 'bg-warning-subtle text-warning-emphasis'
  if (lower === 'locked') return 'bg-danger-subtle text-danger-emphasis'
  return 'bg-secondary-subtle text-secondary-emphasis'
}

function statusLabel(status: string): string {
  const lower = (status || '').toLowerCase()
  if (lower === 'active') return t('adminDocutilUsers.statusActive')
  if (lower === 'inactive') return t('adminDocutilUsers.statusInactive')
  if (lower === 'locked') return t('adminDocutilUsers.statusLocked')
  return status
}

function formatDate(value: string | null): string {
  if (!value) return '-'
  try {
    return new Date(value).toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return value
  }
}

function extractErrorMessage(err: unknown): string {
  // axios 에러: response.data.message — services/api.ts 인터셉터 패턴.
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const resp = (err as { response?: { data?: { message?: string } } }).response
    if (resp?.data?.message) return resp.data.message
  }
  if (err instanceof Error) return err.message
  return t('adminDocutilUsers.errorUnknown')
}

onMounted(() => {
  fetchPage(1)
})

// router 는 향후 트랙(10.1b/10.1c)에서 부서/프로젝트 페이지로 이동할 때 사용.
// 본 트랙에서는 모달만 사용하므로 push 호출 없음.
void router
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1050;
}

.modal-card {
  width: 90%;
  max-width: 640px;
  max-height: 86vh;
  overflow-y: auto;
}

dl.row dt {
  font-weight: 600;
  color: var(--bs-secondary-color);
}
</style>
