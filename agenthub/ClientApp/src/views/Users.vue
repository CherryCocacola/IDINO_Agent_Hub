<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">사용자 &amp; 권한 관리</h1>
        <p class="page-desc">시스템 사용자와 접근 권한을 관리합니다</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-outline-secondary btn-sm" @click="exportToCSV">
          <i class="bi bi-download me-1"></i>내보내기
        </button>
        <button class="btn btn-primary btn-sm" @click="showAddModal = true">
          <i class="bi bi-person-plus me-1"></i>사용자 추가
        </button>
      </div>
    </div>

    <!-- 통계 카드 -->
    <div class="row g-4 mb-4">
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-people"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">전체 사용자</p>
            <h2 class="stat-value">{{ stats.totalUsers }}</h2>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-success">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-person-check"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">활성 사용자</p>
            <h2 class="stat-value">{{ stats.activeUsers }}</h2>
            <p class="stat-change stat-up">{{ stats.activePercentage }}%</p>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-warning">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-clock-history"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">대기 중</p>
            <h2 class="stat-value">{{ stats.pendingUsers }}</h2>
            <p class="stat-change">{{ stats.pendingPercentage }}%</p>
          </div>
        </div>
      </div>
      <div class="col-xl-3 col-md-6">
        <div class="stat-card stat-card-danger">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-person-x"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">비활성</p>
            <h2 class="stat-value">{{ stats.inactiveUsers }}</h2>
            <p class="stat-change stat-down">{{ stats.inactivePercentage }}%</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 검색 및 필터 -->
    <div class="ag-filter-bar">
      <div class="ag-search-wrap">
        <i class="bi bi-search ag-search-icon"></i>
        <input 
          type="text" 
          class="ag-search-input" 
          v-model="searchText" 
          placeholder="사용자 검색... (이름, 이메일)"
          @input="loadUsers"
        >
        <button 
          type="button" 
          class="ag-search-clear" 
          v-show="searchText" 
          @click="searchText = ''; loadUsers()"
        >
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
      <div class="ag-filter-selects">
        <select class="ag-select" v-model="roleFilter" @change="loadUsers">
          <option value="">모든 역할</option>
          <option value="admin">Admin</option>
          <option value="developer">Developer</option>
          <option value="user">User</option>
        </select>
        <select class="ag-select" v-model="statusFilter" @change="loadUsers">
          <option value="">모든 상태</option>
          <option value="active">활성</option>
          <option value="pending">대기</option>
          <option value="inactive">비활성</option>
        </select>
      </div>
      <div class="ag-filter-right">
        <button class="btn btn-outline-secondary btn-sm" @click="resetFilters">
          <i class="bi bi-arrow-clockwise me-1"></i>초기화
        </button>
        <span class="ag-count-label">전체 <strong>{{ totalCount }}</strong>명</span>
      </div>
    </div>

    <!-- 사용자 테이블 -->
    <div class="card aiuiux-card">
      <div class="card-body p-0">
        <div class="table-responsive" v-if="loading">
          <div class="text-center p-4">
            <div class="spinner-border" role="status">
              <span class="visually-hidden">Loading...</span>
            </div>
          </div>
        </div>
        <div class="table-responsive" v-else>
          <table class="table table-hover aiuiux-table">
            <thead>
              <tr>
                <th>
                  <input 
                    type="checkbox" 
                    class="form-check-input" 
                    :checked="selectAll"
                    @change="toggleSelectAll"
                  >
                </th>
                <th>ID</th>
                <th>이름</th>
                <th>이메일</th>
                <th>역할</th>
                <th>상태</th>
                <th>마지막 로그인</th>
                <th>생성일</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="user in users" :key="user?.userId || Math.random()">
                <tr v-if="user != null">
                <td>
                  <input 
                    type="checkbox" 
                    class="form-check-input row-checkbox"
                    :value="user?.userId"
                    v-model="selectedUsers"
                  >
                </td>
                <td>{{ user?.userId || '-' }}</td>
                <td>
                  <div class="d-flex align-items-center">
                    <div class="avatar-circle me-2" :class="getAvatarClass(user)">
                      {{ getAvatarInitial(user?.fullName || '') }}
                    </div>
                    <strong>{{ user?.fullName || '-' }}</strong>
                  </div>
                </td>
                <td>{{ user?.email || '-' }}</td>
                <td>
                  <span 
                    v-for="role in (user?.roles || [])" 
                    :key="role" 
                    class="badge me-1"
                    :class="getRoleBadgeClass(role)"
                  >
                    {{ role }}
                  </span>
                  <span v-if="!user?.roles || user.roles.length === 0" class="text-muted">-</span>
                </td>
                <td>
                  <span class="status-indicator me-1" :class="getStatusClass(user?.status || '')"></span>
                  <span class="badge" :class="getStatusBadgeClass(user?.status || '')">
                    {{ getStatusText(user?.status || '') }}
                  </span>
                </td>
                <td>{{ formatDate(user?.lastLoginAt) }}</td>
                <td>{{ formatDate(user?.createdAt) }}</td>
                <td>
                  <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-outline-primary" @click="editUser(user)" title="수정">
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" @click="viewUser(user)" title="상세보기">
                      <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" @click="deleteUser(user)" title="삭제">
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
                </tr>
              </template>
              <tr v-if="users.length === 0">
                <td colspan="9" class="text-center text-muted py-4">
                  사용자가 없습니다.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div class="card-footer bg-transparent border-top d-flex flex-wrap align-items-center justify-content-between gap-3" v-if="users.length > 0">
        <div class="d-flex align-items-center gap-3">
          <span class="text-muted small">
            총 <strong class="text-body">{{ totalCount }}</strong>명 중 
            <strong class="text-body">{{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, totalCount) }}</strong> 표시
          </span>
          <select class="form-select form-select-sm" style="width:100px" v-model.number="pageSize" @change="onPageSizeChange">
            <option :value="10">10개씩</option>
            <option :value="20">20개씩</option>
            <option :value="50">50개씩</option>
            <option :value="100">100개씩</option>
          </select>
        </div>
        <nav v-if="totalPages > 1">
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">이전</a>
            </li>
            <li 
              v-for="page in visiblePages" 
              :key="page"
              class="page-item" 
              :class="{ active: page === currentPage }"
            >
              <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">다음</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 사용자 추가 모달 -->
    <div class="modal fade user-form-modal" :class="{ show: showAddModal }" :style="{ display: showAddModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered user-add-modal-dialog">
        <div class="modal-content user-modal-content">
          <div class="modal-header user-modal-header">
            <h5 class="modal-title">
              <i class="bi bi-person-plus-fill text-primary me-2" aria-hidden="true"></i>
              새 사용자 추가
            </h5>
            <button type="button" class="btn-close" @click="showAddModal = false" aria-label="닫기"></button>
          </div>
          <div class="modal-body user-modal-body">
            <form @submit.prevent="handleAddUser" class="user-modal-form">
              <div class="row">
                <div class="col-md-6 user-form-group">
                  <label class="user-form-label">이름 <span class="text-danger">*</span></label>
                  <input type="text" class="form-control user-form-control" v-model="newUser.fullName" required placeholder="이름을 입력하세요">
                </div>
                <div class="col-md-6 user-form-group">
                  <label class="user-form-label">이메일 <span class="text-danger">*</span></label>
                  <input type="email" class="form-control user-form-control" v-model="newUser.email" required placeholder="example@company.com">
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 user-form-group">
                  <label class="user-form-label">비밀번호 <span class="text-danger">*</span></label>
                  <input type="password" class="form-control user-form-control" v-model="newUser.password" required placeholder="8자 이상">
                </div>
                <div class="col-md-6 user-form-group">
                  <label class="user-form-label">비밀번호 확인 <span class="text-danger">*</span></label>
                  <input type="password" class="form-control user-form-control" v-model="newUser.passwordConfirm" required placeholder="비밀번호 재입력">
                </div>
              </div>
              <div class="row">
                <div class="col-md-6 user-form-group">
                  <label class="user-form-label">부서</label>
                  <input type="text" class="form-control user-form-control" v-model="newUser.department" placeholder="예: 개발팀">
                </div>
                <div class="col-md-6 user-form-group">
                  <label class="user-form-label">전화번호</label>
                  <input type="tel" class="form-control user-form-control" v-model="newUser.phoneNumber" placeholder="010-0000-0000">
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer user-modal-footer">
            <button type="button" class="btn btn-outline-secondary user-modal-btn" @click="showAddModal = false">취소</button>
            <button type="button" class="btn btn-primary user-modal-btn user-modal-btn-primary" @click="handleAddUser">
              <i class="bi bi-check-lg me-1" aria-hidden="true"></i>
              추가
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showAddModal }" v-if="showAddModal"></div>

    <!-- 사용자 수정 모달 -->
    <div class="modal fade" :class="{ show: showEditModal }" :style="{ display: showEditModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-pencil"></i> 사용자 정보 수정</h5>
            <button type="button" class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleUpdateUser">
              <div class="row">
                <div class="col-md-6 mb-3">
                  <label class="form-label">이름</label>
                  <input type="text" class="form-control" v-model="editingUser.fullName" v-if="editingUser">
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">이메일</label>
                  <input type="email" class="form-control" v-model="editingUser.email" readonly v-if="editingUser">
                </div>
              </div>
              <div class="row" v-if="editingUser">
                <div class="col-md-6 mb-3">
                  <label class="form-label">부서</label>
                  <input type="text" class="form-control" v-model="editingUser.department">
                </div>
                <div class="col-md-6 mb-3">
                  <label class="form-label">전화번호</label>
                  <input type="tel" class="form-control" v-model="editingUser.phoneNumber">
                </div>
              </div>
              <div class="mb-3" v-if="editingUser">
                <label class="form-label">상태</label>
                <select class="form-select" v-model="editingUser.status">
                  <option value="Active">활성</option>
                  <option value="Pending">대기</option>
                  <option value="Inactive">비활성</option>
                </select>
              </div>
              <div class="mb-3" v-if="editingUser">
                <label class="form-label">새 비밀번호 (변경 시에만 입력)</label>
                <input type="password" class="form-control" v-model="editingUserNewPassword">
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showEditModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleUpdateUser">
              <i class="bi bi-check-lg"></i> 저장
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showEditModal }" v-if="showEditModal"></div>

    <!-- 사용자 상세 모달 -->
    <div class="modal fade" :class="{ show: showDetailModal }" :style="{ display: showDetailModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-person-circle"></i> 사용자 상세 정보</h5>
            <button type="button" class="btn-close" @click="showDetailModal = false"></button>
          </div>
          <div class="modal-body" v-if="viewingUser">
            <div class="row mb-4">
              <div class="col-md-12 text-center">
                <div class="avatar-circle mx-auto mb-3" :class="getAvatarClass(viewingUser)" style="width: 100px; height: 100px; font-size: 3rem;">
                  {{ getAvatarInitial(viewingUser?.fullName || '') }}
                </div>
                <h4>{{ viewingUser?.fullName || '-' }}</h4>
                <span 
                  v-for="role in (viewingUser?.roles || [])" 
                  :key="role" 
                  class="badge me-1"
                  :class="getRoleBadgeClass(role)"
                >
                  {{ role }}
                </span>
                <span class="badge ms-1" :class="getStatusBadgeClass(viewingUser?.status || '')">
                  {{ getStatusText(viewingUser?.status || '') }}
                </span>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="text-muted small">이메일</label>
                <p class="mb-0"><strong>{{ viewingUser?.email || '-' }}</strong></p>
              </div>
              <div class="col-md-6 mb-3">
                <label class="text-muted small">전화번호</label>
                <p class="mb-0"><strong>{{ viewingUser?.phoneNumber || '-' }}</strong></p>
              </div>
              <div class="col-md-6 mb-3">
                <label class="text-muted small">부서</label>
                <p class="mb-0"><strong>{{ viewingUser?.department || '-' }}</strong></p>
              </div>
              <div class="col-md-6 mb-3">
                <label class="text-muted small">가입일</label>
                <p class="mb-0"><strong>{{ formatDate(viewingUser?.createdAt) }}</strong></p>
              </div>
              <div class="col-md-6 mb-3">
                <label class="text-muted small">마지막 로그인</label>
                <p class="mb-0"><strong>{{ formatDate(viewingUser?.lastLoginAt) || '-' }}</strong></p>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showDetailModal = false">닫기</button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showDetailModal }" v-if="showDetailModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import type { UserDto } from '@/types'

interface UserStats {
  totalUsers: number
  activeUsers: number
  pendingUsers: number
  inactiveUsers: number
  activePercentage: number
  pendingPercentage: number
  inactivePercentage: number
}

interface CreateUserData {
  fullName: string
  email: string
  password: string
  passwordConfirm: string
  department?: string
  phoneNumber?: string
}

const users = ref<UserDto[]>([])
const selectedUsers = ref<number[]>([])
const loading = ref(false)
const searchText = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)

const showAddModal = ref(false)
const showEditModal = ref(false)
const showDetailModal = ref(false)
const editingUser = ref<UserDto | null>(null)
const editingUserNewPassword = ref('')
const viewingUser = ref<UserDto | null>(null)

const newUser = ref<CreateUserData>({
  fullName: '',
  email: '',
  password: '',
  passwordConfirm: '',
  department: '',
  phoneNumber: ''
})

const stats = computed<UserStats>(() => {
  const total = users.value.length
  const active = users.value.filter(u => u && u.status === 'Active').length
  const pending = users.value.filter(u => u && u.status === 'Pending').length
  const inactive = users.value.filter(u => u && u.status === 'Inactive').length
  
  return {
    totalUsers: total,
    activeUsers: active,
    pendingUsers: pending,
    inactiveUsers: inactive,
    activePercentage: total > 0 ? Math.round((active / total) * 100) : 0,
    pendingPercentage: total > 0 ? Math.round((pending / total) * 100) : 0,
    inactivePercentage: total > 0 ? Math.round((inactive / total) * 100) : 0
  }
})

const selectAll = computed(() => {
  return users.value.length > 0 && selectedUsers.value.length === users.value.length
})

const totalPages = computed(() => {
  return Math.ceil(totalCount.value / pageSize.value)
})

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const loadUsers = async () => {
  try {
    loading.value = true
    const params: any = {}
    if (searchText.value) params.search = searchText.value
    if (roleFilter.value) params.role = roleFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    
    const response = await api.get<{ items?: UserDto[], totalCount?: number } | UserDto[]>('/users', { params })
    
    // 응답이 배열인 경우
    if (Array.isArray(response.data)) {
      users.value = response.data.filter((u: UserDto) => u != null && u.fullName != null) || []
      totalCount.value = users.value.length
    } 
    // 응답이 객체인 경우 (페이지네이션)
    else if (response.data && typeof response.data === 'object' && 'items' in response.data) {
      users.value = (response.data.items || []).filter((u: UserDto) => u != null && u.fullName != null)
      totalCount.value = response.data.totalCount || users.value.length
    } else {
      users.value = []
      totalCount.value = 0
    }
  } catch (error) {
    console.error('Error loading users:', error)
    users.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  searchText.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  loadUsers()
}

const toggleSelectAll = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.checked) {
    selectedUsers.value = users.value.filter(u => u != null).map(u => u.userId)
  } else {
    selectedUsers.value = []
  }
}

const changePage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadUsers()
  }
}

const onPageSizeChange = () => {
  currentPage.value = 1
  loadUsers()
}

const editUser = (user: UserDto | null) => {
  if (!user) return
  editingUser.value = { ...user }
  showEditModal.value = true
}

const viewUser = (user: UserDto | null) => {
  if (!user) return
  viewingUser.value = { ...user }
  showDetailModal.value = true
}

const deleteUser = async (user: UserDto | null) => {
  if (!user) return
  if (!confirm(`정말로 ${user?.fullName || '이 사용자'} 사용자를 삭제하시겠습니까?`)) {
    return
  }
  
  try {
    await api.delete(`/users/${user.userId}`)
    await loadUsers()
  } catch (error) {
    console.error('Error deleting user:', error)
    alert('사용자 삭제 중 오류가 발생했습니다.')
  }
}

const handleAddUser = async () => {
  if (newUser.value.password !== newUser.value.passwordConfirm) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }
  
  try {
    await api.post('/users', {
      fullName: newUser.value.fullName,
      email: newUser.value.email,
      password: newUser.value.password,
      department: newUser.value.department || undefined,
      phoneNumber: newUser.value.phoneNumber || undefined
    })
    
    showAddModal.value = false
    newUser.value = {
      fullName: '',
      email: '',
      password: '',
      passwordConfirm: '',
      department: '',
      phoneNumber: ''
    }
    await loadUsers()
  } catch (error: any) {
    console.error('Error adding user:', error)
    alert(error.response?.data?.message || '사용자 추가 중 오류가 발생했습니다.')
  }
}

const handleUpdateUser = async () => {
  if (!editingUser.value || !editingUser.value.userId) return
  
  try {
    const updateData: any = {
      fullName: editingUser.value.fullName || '',
      department: editingUser.value.department || undefined,
      phoneNumber: editingUser.value.phoneNumber || undefined,
      status: editingUser.value.status || 'Active'
    }
    
    // 비밀번호가 입력된 경우만 포함
    if (editingUserNewPassword.value) {
      updateData.password = editingUserNewPassword.value
    }
    
    await api.put(`/users/${editingUser.value.userId}`, updateData)
    
    showEditModal.value = false
    editingUser.value = null
    editingUserNewPassword.value = ''
    await loadUsers()
  } catch (error: any) {
    console.error('Error updating user:', error)
    alert(error.response?.data?.message || '사용자 수정 중 오류가 발생했습니다.')
  }
}

const exportToCSV = () => {
  const headers = ['ID', '이름', '이메일', '역할', '상태', '부서', '전화번호', '생성일']
  const rows = users.value.filter(user => user != null).map(user => [
    user?.userId || '-',
    user?.fullName || '-',
    user?.email || '-',
    user?.roles?.join(', ') || '-',
    user?.status || '-',
    user?.department || '',
    user?.phoneNumber || '',
    formatDate(user?.createdAt)
  ])
  
  const csv = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')
  
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `users_${new Date().toISOString().split('T')[0]}.csv`
  link.click()
}

const formatDate = (date: string | Date | undefined | null): string => {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('ko-KR')
}

const getAvatarInitial = (name: string | null | undefined): string => {
  if (!name) return '?'
  return name.charAt(0).toUpperCase()
}

const getAvatarClass = (user: UserDto | null | undefined): string => {
  if (!user || !user.userId) return 'avatar-pastel-0'
  const classes = ['avatar-pastel-1', 'avatar-pastel-2', 'avatar-pastel-3', 'avatar-pastel-4', 'avatar-pastel-5', 'avatar-pastel-6']
  const index = user.userId % classes.length
  return classes[index]
}

const getRoleBadgeClass = (role: string): string => {
  switch (role.toLowerCase()) {
    case 'admin':
      return 'bg-danger'
    case 'developer':
      return 'bg-info'
    default:
      return 'bg-secondary'
  }
}

const getStatusClass = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'active':
      return 'online'
    case 'pending':
      return 'pending'
    default:
      return 'offline'
  }
}

const getStatusBadgeClass = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'active':
      return 'badge-status-active'
    case 'pending':
      return 'badge-status-pending'
    default:
      return 'badge-status-inactive'
  }
}

const getStatusText = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'active':
      return '활성'
    case 'pending':
      return '대기'
    case 'inactive':
      return '비활성'
    default:
      return status
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.stat-icon-circle {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.avatar-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

/* 아바타 파스텔톤 */
.avatar-circle.avatar-pastel-0 { background: #E5E7EB; color: #374151; }
.avatar-circle.avatar-pastel-1 { background: #DDD6FE; color: #5B21B6; }
.avatar-circle.avatar-pastel-2 { background: #BFDBFE; color: #1D4ED8; }
.avatar-circle.avatar-pastel-3 { background: #A7F3D0; color: #047857; }
.avatar-circle.avatar-pastel-4 { background: #FDE68A; color: #B45309; }
.avatar-circle.avatar-pastel-5 { background: #FECACA; color: #B91C1C; }
.avatar-circle.avatar-pastel-6 { background: #E0E7FF; color: #4338CA; }

/* 상태 뱃지 파스텔톤 */
.badge.badge-status-active {
  background: #D1FAE5;
  color: #059669;
  border: none;
}
.badge.badge-status-pending {
  background: #FEF3C7;
  color: #D97706;
  border: none;
}
.badge.badge-status-inactive {
  background: #FEE2E2;
  color: #DC2626;
  border: none;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.online {
  background-color: #10b981;
}

.status-indicator.offline {
  background-color: #ef4444;
}

.status-indicator.pending {
  background-color: #f59e0b;
}

/* 사용자 추가/수정 모달 */
.user-form-modal .user-add-modal-dialog {
  max-width: 560px;
}

.user-modal-content {
  border: none;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.user-modal-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--ai-border, #e9ecef);
  background: var(--ai-bg-light, #f8f9fa);
}

.user-modal-header .modal-title {
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.user-modal-body {
  padding: 1.25rem 1.25rem;
}

.user-form-group {
  margin-bottom: 1rem;
}

.user-form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.35rem;
}

.user-form-control {
  border-radius: 8px;
  border-color: var(--ai-border, #dee2e6);
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
}

.user-form-control:focus {
  border-color: var(--ai-primary, #0d6efd);
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
}

.user-form-control::placeholder {
  color: #adb5bd;
}

.user-modal-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--ai-border, #e9ecef);
  background: #fff;
  gap: 0.5rem;
}

.user-modal-btn {
  border-radius: 8px;
  font-weight: 500;
  padding: 0.45rem 1rem;
}

.user-modal-btn-primary {
  min-width: 90px;
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}
</style>
