<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">팀 관리</h1>
        <p class="page-desc">팀을 생성하고 멤버를 관리하세요</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="showCreateTeamModal = true">
          <i class="bi bi-plus-lg me-1"></i>새 팀 생성
        </button>
      </div>
    </div>

    <!-- 팀 목록 -->
    <div class="row">
      <div class="col-12">
        <div class="card aiuiux-card">
          <div class="card-header bg-white d-flex justify-content-between align-items-center">
            <div>
              <h5 class="card-title mb-0">팀 목록</h5>
              <p class="card-subtitle mb-0">등록된 팀 검색·관리</p>
            </div>
            <div class="input-group" style="width: 300px;">
              <input 
                type="text" 
                class="form-control" 
                placeholder="팀 검색..." 
                v-model="searchQuery"
              >
              <button class="btn btn-outline-secondary" type="button">
                <i class="bi bi-search"></i>
              </button>
            </div>
          </div>
          <div class="card-body p-0">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">로딩 중...</span>
              </div>
            </div>
            <div v-else>
              <div class="table-responsive">
                <table class="table table-hover aiuiux-table">
                  <thead>
                    <tr>
                      <th>팀명</th>
                      <th>부서</th>
                      <th>매니저</th>
                      <th>멤버 수</th>
                      <th>상태</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="team in filteredTeams" :key="team.teamId">
                      <td>
                        <strong>{{ team.teamName }}</strong>
                        <br>
                        <small class="text-muted">{{ team.description || '설명 없음' }}</small>
                      </td>
                      <td>{{ team.department || '-' }}</td>
                      <td>
                        <span v-if="team.managerName">{{ team.managerName }}</span>
                        <span v-else class="text-muted">-</span>
                      </td>
                      <td>
                        <span class="team-badge team-badge-count">
                          <i class="bi bi-people" aria-hidden="true"></i>
                          {{ team.memberCount }}명
                        </span>
                      </td>
                      <td>
                        <span 
                          class="team-badge"
                          :class="team.isActive ? 'team-badge-active' : 'team-badge-inactive'"
                        >
                          <span class="team-badge-dot" :class="team.isActive ? 'active' : ''"></span>
                          {{ team.isActive ? '활성' : '비활성' }}
                        </span>
                      </td>
                      <td>
                        <div class="d-flex gap-2">
                          <button class="btn btn-sm btn-outline-primary" @click="editTeam(team)" title="수정">
                            <i class="bi bi-pencil"></i>
                          </button>
                          <button class="btn btn-sm btn-outline-secondary" @click="viewTeam(team)" title="상세보기">
                            <i class="bi bi-eye"></i>
                          </button>
                          <button class="btn btn-sm btn-outline-danger" @click="deleteTeam(team)" title="삭제">
                            <i class="bi bi-trash"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="filteredTeams.length === 0" class="text-center py-4 text-muted">
                  팀이 없습니다. 새 팀을 생성하세요.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 팀 상세 모달 -->
    <div class="modal fade" :class="{ show: showTeamDetailModal, 'd-block': showTeamDetailModal }" tabindex="-1" v-if="showTeamDetailModal && selectedTeam">
      <div class="modal-dialog modal-lg">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-people me-2"></i>{{ selectedTeam.teamName }} - 멤버 관리</h5>
            <button type="button" class="btn-close" @click="showTeamDetailModal = false"></button>
          </div>
          <div class="modal-body">
            <!-- 팀 정보 -->
            <div class="card aiuiux-card mb-4">
              <div class="card-body">
                <h6 class="card-subtitle mb-3 text-uppercase small fw-bold text-muted">팀 정보</h6>
                <div class="row g-3">
                  <div class="col-md-6">
                    <label class="text-muted small d-block mb-1">설명</label>
                    <p class="mb-0">{{ selectedTeam.description || '설명 없음' }}</p>
                  </div>
                  <div class="col-md-3">
                    <label class="text-muted small d-block mb-1">부서</label>
                    <p class="mb-0">{{ selectedTeam.department || '-' }}</p>
                  </div>
                  <div class="col-md-3">
                    <label class="text-muted small d-block mb-1">매니저</label>
                    <p class="mb-0">{{ selectedTeam.managerName || '-' }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 멤버 목록 -->
            <div>
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0"><i class="bi bi-person-lines me-2"></i>팀 멤버 <span class="ag-count-label ms-2">({{ selectedTeam.members.length }}명)</span></h6>
                <button class="btn btn-sm btn-primary" @click="showAddMemberModal = true">
                  <i class="bi bi-person-plus me-1"></i>멤버 추가
                </button>
              </div>
              <div class="table-responsive">
                <table class="table table-hover aiuiux-table mb-0">
                  <thead>
                    <tr>
                      <th>이름</th>
                      <th>이메일</th>
                      <th>팀 내 역할</th>
                      <th>가입일</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="member in selectedTeam.members" :key="member.teamMemberId">
                      <td>{{ member.userName }}</td>
                      <td>{{ member.userEmail }}</td>
                      <td>
                        <span class="perm-badge perm-badge-default">{{ member.role || 'Member' }}</span>
                      </td>
                      <td>{{ formatDate(member.joinedAt) }}</td>
                      <td>
                        <div class="d-flex gap-2">
                          <button class="btn btn-sm btn-outline-primary" @click="editMemberRole(member)" title="역할 수정">
                            <i class="bi bi-pencil"></i>
                          </button>
                          <button class="btn btn-sm btn-outline-danger" @click="removeMember(member)" title="제거">
                            <i class="bi bi-person-dash"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="selectedTeam.members.length === 0" class="text-center py-4 text-muted">
                  <i class="bi bi-person-x" style="font-size: 2rem; opacity: 0.5;"></i>
                  <p class="mt-2 mb-0">멤버가 없습니다.</p>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="showTeamDetailModal = false">닫기</button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showTeamDetailModal }" v-if="showTeamDetailModal" @click="showTeamDetailModal = false"></div>

    <!-- 팀 생성 모달 -->
    <div class="modal fade" :class="{ show: showCreateTeamModal, 'd-block': showCreateTeamModal }" tabindex="-1" v-if="showCreateTeamModal">
      <div class="modal-dialog modal-dialog-centered" style="max-width: 480px;">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-people-fill me-2"></i>새 팀 생성</h5>
            <button type="button" class="btn-close" @click="showCreateTeamModal = false; showManagerDropdown = false" aria-label="닫기"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleCreateTeam">
              <div class="mb-3">
                <label class="form-label">팀명 <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="teamForm.teamName" required placeholder="예: 개발팀">
              </div>
              <div class="mb-3">
                <label class="form-label">설명</label>
                <textarea class="form-control" rows="3" v-model="teamForm.description" placeholder="팀에 대한 설명을 입력하세요"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">부서</label>
                <input type="text" class="form-control" v-model="teamForm.department" placeholder="예: 개발본부">
              </div>
              <div class="mb-3">
                <label class="form-label">매니저 <small class="text-muted">(선택)</small></label>
                <div class="team-manager-dropdown-wrap">
                  <input
                    type="text"
                    class="form-control"
                    v-model="managerSearchQuery"
                    @input="showManagerDropdown = true"
                    @focus="handleManagerInputFocus"
                    @blur="handleManagerInputBlur"
                    :placeholder="getManagerPlaceholder(teamForm.managerId)"
                    autocomplete="off"
                  >
                  <div v-if="showManagerDropdown" class="team-manager-dropdown" @mousedown.prevent>
                    <button type="button" class="team-manager-dropdown-item" :class="{ active: teamForm.managerId === null }" @mousedown.prevent="selectManager(null)">
                      선택 안함
                    </button>
                    <button
                      v-for="user in filteredAvailableUsers"
                      :key="user.userId"
                      type="button"
                      class="team-manager-dropdown-item"
                      :class="{ active: teamForm.managerId === user.userId }"
                      @mousedown.prevent="selectManager(user.userId)"
                    >
                      {{ user.fullName }} <span class="text-muted">({{ user.email }})</span>
                    </button>
                    <div v-if="filteredAvailableUsers.length === 0 && managerSearchQuery" class="team-manager-dropdown-empty">
                      검색 결과가 없습니다
                    </div>
                  </div>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="showCreateTeamModal = false; showManagerDropdown = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleCreateTeam">
              <i class="bi bi-check-lg me-1"></i>생성
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showCreateTeamModal }" v-if="showCreateTeamModal" @click="showCreateTeamModal = false; showManagerDropdown = false"></div>

    <!-- 팀 수정 모달 -->
    <div class="modal fade" :class="{ show: showEditTeamModal, 'd-block': showEditTeamModal }" tabindex="-1" v-if="showEditTeamModal && editingTeam">
      <div class="modal-dialog modal-dialog-centered" style="max-width: 480px;">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-pencil-square me-2"></i>팀 수정</h5>
            <button type="button" class="btn-close" @click="showEditTeamModal = false; showEditManagerDropdown = false" aria-label="닫기"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleUpdateTeam">
              <div class="mb-3">
                <label class="form-label">팀명 <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="editTeamForm.teamName" required placeholder="예: 개발팀">
              </div>
              <div class="mb-3">
                <label class="form-label">설명</label>
                <textarea class="form-control" rows="3" v-model="editTeamForm.description" placeholder="팀에 대한 설명을 입력하세요"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label">부서</label>
                <input type="text" class="form-control" v-model="editTeamForm.department" placeholder="예: 개발본부">
              </div>
              <div class="mb-3">
                <label class="form-label">매니저 <small class="text-muted">(선택)</small></label>
                <div class="team-manager-dropdown-wrap">
                  <input
                    type="text"
                    class="form-control"
                    v-model="editManagerSearchQuery"
                    @input="showEditManagerDropdown = true"
                    @focus="handleEditManagerInputFocus"
                    @blur="handleEditManagerInputBlur"
                    :placeholder="getManagerPlaceholder(editTeamForm.managerId)"
                    autocomplete="off"
                  >
                  <div v-if="showEditManagerDropdown" class="team-manager-dropdown" @mousedown.prevent>
                    <button type="button" class="team-manager-dropdown-item" :class="{ active: editTeamForm.managerId === null }" @mousedown.prevent="selectEditManager(null)">
                      선택 안함
                    </button>
                    <button
                      v-for="user in filteredEditAvailableUsers"
                      :key="user.userId"
                      type="button"
                      class="team-manager-dropdown-item"
                      :class="{ active: editTeamForm.managerId === user.userId }"
                      @mousedown.prevent="selectEditManager(user.userId)"
                    >
                      {{ user.fullName }} <span class="text-muted">({{ user.email }})</span>
                    </button>
                    <div v-if="filteredEditAvailableUsers.length === 0 && editManagerSearchQuery" class="team-manager-dropdown-empty">
                      검색 결과가 없습니다
                    </div>
                  </div>
                </div>
              </div>
              <div class="mb-3">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox" v-model="editTeamForm.isActive" id="editTeamActive">
                  <label class="form-check-label" for="editTeamActive">활성 상태</label>
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="showEditTeamModal = false; showEditManagerDropdown = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleUpdateTeam">
              <i class="bi bi-check-lg me-1"></i>저장
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showEditTeamModal }" v-if="showEditTeamModal" @click="showEditTeamModal = false; showEditManagerDropdown = false"></div>

    <!-- 멤버 추가 모달 -->
    <div class="modal fade" :class="{ show: showAddMemberModal, 'd-block': showAddMemberModal }" tabindex="-1" v-if="showAddMemberModal && selectedTeam">
      <div class="modal-dialog modal-dialog-centered" style="max-width: 480px;">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-person-plus-fill me-2"></i>{{ selectedTeam.teamName }}에 멤버 추가</h5>
            <button type="button" class="btn-close" @click="showAddMemberModal = false; showMemberDropdown = false" aria-label="닫기"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleAddMember" novalidate>
              <div class="mb-3">
                <label class="form-label">사용자 <span class="text-danger">*</span></label>
                <div class="team-manager-dropdown-wrap">
                  <input
                    type="text"
                    class="form-control"
                    v-model="memberSearchQuery"
                    @input="showMemberDropdown = true"
                    @focus="handleMemberInputFocus"
                    @blur="handleMemberInputBlur"
                    placeholder="사용자 검색 또는 선택..."
                    autocomplete="off"
                  >
                  <div v-if="showMemberDropdown" class="team-manager-dropdown" @mousedown.prevent>
                    <button
                      v-for="user in filteredAvailableUsersForTeam"
                      :key="user.userId"
                      type="button"
                      class="team-manager-dropdown-item"
                      :class="{ active: memberForm.userId === user.userId }"
                      @mousedown.prevent="selectMember(user.userId)"
                    >
                      {{ user.fullName }} <span class="text-muted">({{ user.email }})</span>
                    </button>
                    <div v-if="filteredAvailableUsersForTeam.length === 0 && memberSearchQuery" class="team-manager-dropdown-empty">
                      검색 결과가 없습니다
                    </div>
                  </div>
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">팀 내 역할</label>
                <select class="form-select" v-model="memberForm.role">
                  <option value="">Member (기본)</option>
                  <option value="Leader">Leader</option>
                  <option value="Member">Member</option>
                  <option value="Contributor">Contributor</option>
                </select>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="showAddMemberModal = false; showMemberDropdown = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleAddMember">
              <i class="bi bi-person-plus me-1"></i>추가
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showAddMemberModal }" v-if="showAddMemberModal" @click="showAddMemberModal = false; showMemberDropdown = false"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import type { UserDto, TeamDto, TeamMemberDto } from '@/types'

const teams = ref<TeamDto[]>([])
const loading = ref(false)
const searchQuery = ref('')
const showCreateTeamModal = ref(false)
const showEditTeamModal = ref(false)
const showTeamDetailModal = ref(false)
const showAddMemberModal = ref(false)
const selectedTeam = ref<TeamDto | null>(null)
const editingTeam = ref<TeamDto | null>(null)
const availableUsers = ref<UserDto[]>([])
const managerSearchQuery = ref('')
const editManagerSearchQuery = ref('')
const memberSearchQuery = ref('')
const showManagerDropdown = ref(false)
const showEditManagerDropdown = ref(false)
const showMemberDropdown = ref(false)

const teamForm = ref({
  teamName: '',
  description: '',
  department: '',
  managerId: null as number | null
})

const editTeamForm = ref({
  teamName: '',
  description: '',
  department: '',
  managerId: null as number | null,
  isActive: true
})

const memberForm = ref({
  userId: null as number | null,
  role: ''
})

const filteredTeams = computed(() => {
  if (!searchQuery.value) return teams.value
  const query = searchQuery.value.toLowerCase()
  return teams.value.filter(t => 
    t.teamName.toLowerCase().includes(query) ||
    (t.description && t.description.toLowerCase().includes(query)) ||
    (t.department && t.department.toLowerCase().includes(query))
  )
})

const availableUsersForTeam = computed(() => {
  if (!selectedTeam.value) return availableUsers.value
  const memberUserIds = selectedTeam.value.members.map(m => m.userId)
  return availableUsers.value.filter(u => !memberUserIds.includes(u.userId))
})

const filteredAvailableUsersForTeam = computed(() => {
  let users = availableUsersForTeam.value
  if (memberSearchQuery.value) {
    const query = memberSearchQuery.value.toLowerCase()
    users = users.filter(u => 
      u.fullName.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query) ||
      (u.department && u.department.toLowerCase().includes(query))
    )
  }
  return users
})

const filteredAvailableUsers = computed(() => {
  let users = availableUsers.value
  if (managerSearchQuery.value) {
    const query = managerSearchQuery.value.toLowerCase()
    users = users.filter(u => 
      u.fullName.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query) ||
      (u.department && u.department.toLowerCase().includes(query))
    )
  }
  return users
})

const filteredEditAvailableUsers = computed(() => {
  let users = availableUsers.value
  if (editManagerSearchQuery.value) {
    const query = editManagerSearchQuery.value.toLowerCase()
    users = users.filter(u => 
      u.fullName.toLowerCase().includes(query) ||
      u.email.toLowerCase().includes(query) ||
      (u.department && u.department.toLowerCase().includes(query))
    )
  }
  return users
})


onMounted(() => {
  loadTeams()
  loadUsers()
})

const loadTeams = async () => {
  loading.value = true
  try {
    const response = await api.get<TeamDto[]>('/teams')
    teams.value = response.data || []
  } catch (error: any) {
    console.error('팀 목록 로드 실패:', error)
    if (error.response?.status === 403) {
      alert('팀 관리 권한이 없습니다. (Admin 권한 필요)')
    } else {
      alert('팀 목록을 불러오는데 실패했습니다.')
    }
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  try {
    const response = await api.get<UserDto[]>('/users')
    availableUsers.value = response.data || []
  } catch (error: any) {
    console.error('사용자 목록 로드 실패:', error)
  }
}

const viewTeam = async (team: TeamDto) => {
  try {
    const response = await api.get<TeamDto>(`/teams/${team.teamId}`)
    selectedTeam.value = response.data
    showTeamDetailModal.value = true
  } catch (error: any) {
    console.error('팀 상세 정보 로드 실패:', error)
    alert('팀 정보를 불러오는데 실패했습니다.')
  }
}

const editTeam = (team: TeamDto) => {
  editingTeam.value = team
  editTeamForm.value = {
    teamName: team.teamName,
    description: team.description || '',
    department: team.department || '',
    managerId: team.managerId || null,
    isActive: team.isActive
  }
  editManagerSearchQuery.value = ''
  showEditTeamModal.value = true
}

const handleCreateTeam = async () => {
  try {
    const response = await api.post<TeamDto>('/teams', teamForm.value)
    teams.value.push(response.data)
    showCreateTeamModal.value = false
    teamForm.value = {
      teamName: '',
      description: '',
      department: '',
      managerId: null
    }
    managerSearchQuery.value = ''
    showManagerDropdown.value = false
    alert('팀이 생성되었습니다.')
  } catch (error: any) {
    console.error('팀 생성 실패:', error)
    alert(error.response?.data?.message || '팀 생성에 실패했습니다.')
  }
}

const handleUpdateTeam = async () => {
  if (!editingTeam.value) return
  
  try {
    const response = await api.put<TeamDto>(`/teams/${editingTeam.value.teamId}`, editTeamForm.value)
    const index = teams.value.findIndex(t => t.teamId === editingTeam.value!.teamId)
    if (index !== -1) {
      teams.value[index] = response.data
    }
    showEditTeamModal.value = false
    editingTeam.value = null
    editManagerSearchQuery.value = ''
    showEditManagerDropdown.value = false
    alert('팀 정보가 업데이트되었습니다.')
  } catch (error: any) {
    console.error('팀 수정 실패:', error)
    alert(error.response?.data?.message || '팀 수정에 실패했습니다.')
  }
}

const deleteTeam = async (team: TeamDto) => {
  if (!confirm(`"${team.teamName}" 팀을 삭제하시겠습니까?`)) return
  
  try {
    await api.delete(`/teams/${team.teamId}`)
    teams.value = teams.value.filter(t => t.teamId !== team.teamId)
    alert('팀이 삭제되었습니다.')
  } catch (error: any) {
    console.error('팀 삭제 실패:', error)
    alert(error.response?.data?.message || '팀 삭제에 실패했습니다.')
  }
}

const handleAddMember = async () => {
  if (!selectedTeam.value || !memberForm.value.userId) return
  
  try {
    await api.post(`/teams/${selectedTeam.value.teamId}/members`, {
      userId: memberForm.value.userId,
      role: memberForm.value.role || null
    })
    
    // 팀 정보 다시 로드
    await viewTeam(selectedTeam.value)
    showAddMemberModal.value = false
    memberForm.value = {
      userId: null,
      role: ''
    }
    memberSearchQuery.value = ''
    showMemberDropdown.value = false
    alert('멤버가 추가되었습니다.')
  } catch (error: any) {
    console.error('멤버 추가 실패:', error)
    alert(error.response?.data?.message || '멤버 추가에 실패했습니다.')
  }
}

const removeMember = async (member: TeamMemberDto) => {
  if (!selectedTeam.value) return
  if (!confirm(`"${member.userName}"을(를) 팀에서 제거하시겠습니까?`)) return
  
  try {
    await api.delete(`/teams/${selectedTeam.value.teamId}/members/${member.userId}`)
    // 팀 정보 다시 로드
    await viewTeam(selectedTeam.value)
    alert('멤버가 제거되었습니다.')
  } catch (error: any) {
    console.error('멤버 제거 실패:', error)
    alert(error.response?.data?.message || '멤버 제거에 실패했습니다.')
  }
}

const editMemberRole = async (member: TeamMemberDto) => {
  if (!selectedTeam.value) return
  const newRole = prompt('팀 내 역할을 입력하세요:', member.role || 'Member')
  if (newRole === null) return
  
  try {
    await api.put(`/teams/${selectedTeam.value.teamId}/members/${member.userId}/role`, {
      role: newRole || null
    })
    // 팀 정보 다시 로드
    await viewTeam(selectedTeam.value)
    alert('멤버 역할이 업데이트되었습니다.')
  } catch (error: any) {
    console.error('멤버 역할 수정 실패:', error)
    alert(error.response?.data?.message || '멤버 역할 수정에 실패했습니다.')
  }
}

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('ko-KR')
}

const getManagerDisplayName = (managerId: number | null): string => {
  if (!managerId) return ''
  const user = availableUsers.value.find(u => u.userId === managerId)
  return user ? `${user.fullName} (${user.email})` : ''
}

const getManagerPlaceholder = (managerId: number | null): string => {
  if (managerId) {
    return getManagerDisplayName(managerId)
  }
  return '매니저 검색 또는 선택...'
}

const handleManagerInputFocus = () => {
  showManagerDropdown.value = true
  if (!managerSearchQuery.value && teamForm.value.managerId) {
    managerSearchQuery.value = ''
  }
}

const handleManagerInputBlur = () => {
  setTimeout(() => {
    showManagerDropdown.value = false
    if (!managerSearchQuery.value && teamForm.value.managerId) {
      // 선택된 매니저가 있으면 표시하지 않고 placeholder로만 표시
      managerSearchQuery.value = ''
    }
  }, 200)
}

const handleEditManagerInputFocus = () => {
  showEditManagerDropdown.value = true
  if (!editManagerSearchQuery.value && editTeamForm.value.managerId) {
    editManagerSearchQuery.value = ''
  }
}

const handleEditManagerInputBlur = () => {
  setTimeout(() => {
    showEditManagerDropdown.value = false
    if (!editManagerSearchQuery.value && editTeamForm.value.managerId) {
      // 선택된 매니저가 있으면 표시하지 않고 placeholder로만 표시
      editManagerSearchQuery.value = ''
    }
  }, 200)
}

const selectManager = (userId: number | null) => {
  teamForm.value.managerId = userId
  managerSearchQuery.value = ''
  showManagerDropdown.value = false
}

const selectEditManager = (userId: number | null) => {
  editTeamForm.value.managerId = userId
  editManagerSearchQuery.value = ''
  showEditManagerDropdown.value = false
}

const handleMemberInputFocus = () => {
  showMemberDropdown.value = true
  if (!memberSearchQuery.value && memberForm.value.userId) {
    memberSearchQuery.value = ''
  }
}

const handleMemberInputBlur = () => {
  setTimeout(() => {
    showMemberDropdown.value = false
    if (!memberSearchQuery.value && memberForm.value.userId) {
      memberSearchQuery.value = ''
    }
  }, 200)
}

const selectMember = (userId: number) => {
  memberForm.value.userId = userId
  const selectedUser = availableUsersForTeam.value.find(u => u.userId === userId)
  memberSearchQuery.value = selectedUser ? `${selectedUser.fullName} (${selectedUser.email})` : ''
  showMemberDropdown.value = false
}
</script>

<style scoped>
/* 팀 테이블 배지 */
.team-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 9999px;
  border: 1px solid transparent;
}

.team-badge-count {
  background: rgba(13, 110, 253, 0.1);
  border-color: rgba(13, 110, 253, 0.25);
  color: #0a58ca;
}

.team-badge-active {
  background: rgba(25, 135, 84, 0.12);
  border-color: rgba(25, 135, 84, 0.3);
  color: #0f5132;
}

.team-badge-inactive {
  background: rgba(108, 117, 125, 0.12);
  border-color: rgba(108, 117, 125, 0.25);
  color: #495057;
}

.team-badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.7;
}

.team-badge-dot.active {
  opacity: 1;
  box-shadow: 0 0 0 1px currentColor;
}

/* 매니저 선택 드롭다운 (팀 생성/수정 모달) */
.team-manager-dropdown-wrap {
  position: relative;
}

.team-manager-dropdown {
  position: absolute;
  left: 0;
  right: 0;
  top: 100%;
  margin-top: 6px;
  background: var(--ai-bg-card);
  border: 1.5px solid var(--ai-border);
  border-radius: var(--ai-radius-lg);
  box-shadow: var(--ai-shadow-lg);
  max-height: 260px;
  overflow-y: auto;
  z-index: 1050;
}

.team-manager-dropdown-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  text-align: left;
  border: none;
  background: transparent;
  color: var(--ai-text-primary);
  cursor: pointer;
  border-radius: var(--ai-radius);
  transition: background 0.15s;
}

.team-manager-dropdown-item:hover {
  background: var(--ai-bg-light);
}

.team-manager-dropdown-item.active {
  background: var(--ai-primary-light);
  color: var(--ai-primary);
  font-weight: 600;
}

.team-manager-dropdown-empty {
  padding: 12px;
  font-size: 12px;
  color: var(--ai-text-muted);
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}
</style>
