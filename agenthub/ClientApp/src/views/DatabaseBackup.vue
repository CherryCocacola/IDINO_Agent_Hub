<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">데이터베이스 백업</h1>
        <p class="page-desc">자동 백업 설정 및 복구 관리</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-success btn-sm" @click="createBackup">
          <i class="bi bi-plus-circle"></i> 즉시 백업
        </button>
        <button class="btn btn-primary btn-sm ms-2" @click="showScheduleModal = true">
          <i class="bi bi-calendar"></i> 스케줄 설정
        </button>
      </div>
    </div>

    <div class="row g-4 mb-4">
      <div class="col-md-3">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-clock-history"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">마지막 백업</p>
            <h2 class="stat-value">{{ lastBackupTime }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-card stat-card-success">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-hdd"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">백업 파일</p>
            <h2 class="stat-value">{{ backups.length }}개</h2>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-card stat-card-info">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-archive"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">총 용량</p>
            <h2 class="stat-value">{{ formatSize(totalSize) }}</h2>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-card stat-card-warning">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-cloud-upload"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">저장 위치</p>
            <h2 class="stat-value">로컬</h2>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-8">
        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom d-flex justify-content-between align-items-center">
            <h5 class="mb-0">백업 목록</h5>
            <button class="btn btn-sm btn-outline-primary" @click="loadBackups">
              <i class="bi bi-arrow-clockwise"></i> 새로고침
            </button>
          </div>
          <div class="card-body">
            <div v-if="loading" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">로딩 중...</span>
              </div>
            </div>
            <div v-else-if="backups.length === 0" class="text-center py-4 text-muted">
              <i class="bi bi-hdd" style="font-size: 3rem;"></i>
              <p class="mt-3">백업 파일이 없습니다.</p>
            </div>
            <div v-else>
              <div class="table-responsive">
                <table class="table table-hover aiuiux-table">
                  <thead>
                    <tr>
                      <th>백업 이름</th>
                      <th>생성일시</th>
                      <th>크기</th>
                      <th>작업</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="backup in backups" :key="backup.name">
                      <td>{{ backup.name }}</td>
                      <td>{{ formatDate(backup.createdAt) }}</td>
                      <td>{{ formatSize(backup.size) }}</td>
                      <td>
                        <button 
                          class="btn btn-sm btn-outline-primary" 
                          @click="restoreBackup(backup)"
                          title="복원"
                        >
                          <i class="bi bi-arrow-counterclockwise"></i>
                        </button>
                        <button 
                          class="btn btn-sm btn-outline-danger ms-1" 
                          @click="deleteBackup(backup)"
                          title="삭제"
                        >
                          <i class="bi bi-trash"></i>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-4">
        <!-- 백업 설정 -->
        <div class="card aiuiux-card mb-4">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="mb-0"><i class="bi bi-gear"></i> 백업 설정</h5>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <div class="form-check form-switch">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  id="autoBackup"
                  v-model="backupSettings.autoBackupEnabled"
                  @change="updateSettings"
                >
                <label class="form-check-label" for="autoBackup">
                  자동 백업 활성화
                </label>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">백업 빈도</label>
              <select 
                class="form-select" 
                v-model="backupSettings.backupFrequency"
                @change="updateSettings"
              >
                <option value="Daily">매일</option>
                <option value="Weekly">매주</option>
                <option value="Monthly">매월</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">백업 시간</label>
              <input 
                type="time" 
                class="form-control" 
                v-model="backupSettings.backupTime"
                @change="updateSettings"
              >
            </div>
            <div class="mb-3">
              <label class="form-label">보관 기간 (일)</label>
              <input 
                type="number" 
                class="form-control" 
                v-model.number="backupSettings.retentionDays"
                @change="updateSettings"
                min="1"
              >
            </div>
            <div>
              <label class="form-label">백업 경로</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="backupSettings.backupPath"
                readonly
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 백업 생성 모달 -->
    <div class="modal fade" :class="{ show: showBackupModal, 'd-block': showBackupModal }" tabindex="-1" v-if="showBackupModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">백업 생성</h5>
            <button type="button" class="btn-close" @click="showBackupModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">백업 이름 (선택)</label>
              <input 
                type="text" 
                class="form-control" 
                v-model="backupName"
                placeholder="기본 이름 사용"
              >
            </div>
            <div class="alert alert-info">
              <i class="bi bi-info-circle"></i>
              백업 생성에는 시간이 소요될 수 있습니다.
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showBackupModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="confirmCreateBackup" :disabled="creating">
              <span v-if="creating" class="spinner-border spinner-border-sm me-2"></span>
              <i v-else class="bi bi-check-lg"></i>
              {{ creating ? '백업 중...' : '백업 생성' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showBackupModal }" v-if="showBackupModal" @click="showBackupModal = false"></div>

    <!-- 스케줄 설정 모달 -->
    <div class="modal fade" :class="{ show: showScheduleModal, 'd-block': showScheduleModal }" tabindex="-1" v-if="showScheduleModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">스케줄 설정</h5>
            <button type="button" class="btn-close" @click="showScheduleModal = false"></button>
          </div>
          <div class="modal-body">
            <p>스케줄 설정은 백업 설정 카드에서 관리할 수 있습니다.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showScheduleModal = false">닫기</button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showScheduleModal }" v-if="showScheduleModal" @click="showScheduleModal = false"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'

interface BackupInfo {
  name: string
  path: string
  size: number
  createdAt: string
  modifiedAt: string
}

interface BackupSettings {
  autoBackupEnabled: boolean
  backupFrequency: string
  backupTime: string
  retentionDays: number
  backupPath: string
}

const backups = ref<BackupInfo[]>([])
const loading = ref(false)
const creating = ref(false)
const showBackupModal = ref(false)
const showScheduleModal = ref(false)
const backupName = ref('')
const backupSettings = ref<BackupSettings>({
  autoBackupEnabled: false,
  backupFrequency: 'Daily',
  backupTime: '02:00',
  retentionDays: 30,
  backupPath: ''
})

const lastBackupTime = computed(() => {
  if (backups.value.length === 0) return '없음'
  const latest = backups.value[0]
  const date = new Date(latest.createdAt)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return '방금 전'
  if (hours < 24) return `${hours}시간 전`
  const days = Math.floor(hours / 24)
  return `${days}일 전`
})

const totalSize = computed(() => {
  return backups.value.reduce((sum, backup) => sum + backup.size, 0)
})

onMounted(() => {
  loadBackups()
  loadSettings()
})

const loadBackups = async () => {
  loading.value = true
  try {
    const response = await api.get('/databasebackup/backups')
    backups.value = response.data
  } catch (error: any) {
    console.error('백업 목록 로드 실패:', error)
    if (error.response?.status === 403) {
      alert('백업 조회 권한이 없습니다. (Admin 권한 필요)')
    }
  } finally {
    loading.value = false
  }
}

const loadSettings = async () => {
  try {
    const response = await api.get('/databasebackup/settings')
    backupSettings.value = response.data
  } catch (error: any) {
    console.error('설정 로드 실패:', error)
  }
}

const createBackup = () => {
  backupName.value = ''
  showBackupModal.value = true
}

const confirmCreateBackup = async () => {
  creating.value = true
  try {
    const response = await api.post('/databasebackup/backup', {
      backupName: backupName.value || undefined
    })
    
    showBackupModal.value = false
    alert(response.data.message || '백업이 성공적으로 생성되었습니다.')
    await loadBackups()
  } catch (error: any) {
    console.error('백업 생성 실패:', error)
    alert(error.response?.data?.message || '백업 생성에 실패했습니다.')
  } finally {
    creating.value = false
  }
}

const restoreBackup = async (backup: BackupInfo) => {
  if (!confirm(`"${backup.name}" 백업으로 복원하시겠습니까?\n주의: 현재 데이터가 모두 삭제됩니다.`)) {
    return
  }

  try {
    await api.post('/databasebackup/restore', {
      backupPath: backup.path
    })
    alert('백업이 성공적으로 복원되었습니다.')
  } catch (error: any) {
    console.error('백업 복원 실패:', error)
    alert(error.response?.data?.message || '백업 복원에 실패했습니다.')
  }
}

const deleteBackup = async (backup: BackupInfo) => {
  if (!confirm(`"${backup.name}" 백업을 삭제하시겠습니까?`)) {
    return
  }

  try {
    await api.delete(`/databasebackup/backups/${encodeURIComponent(backup.name)}`)
    alert('백업이 삭제되었습니다.')
    await loadBackups()
  } catch (error: any) {
    console.error('백업 삭제 실패:', error)
    alert(error.response?.data?.message || '백업 삭제에 실패했습니다.')
  }
}

const updateSettings = async () => {
  try {
    await api.put('/databasebackup/settings', backupSettings.value)
    // 성공 메시지는 표시하지 않음 (자동 저장)
  } catch (error: any) {
    console.error('설정 저장 실패:', error)
    alert(error.response?.data?.message || '설정 저장에 실패했습니다.')
  }
}

const formatDate = (date: string | Date) => {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}
</style>
