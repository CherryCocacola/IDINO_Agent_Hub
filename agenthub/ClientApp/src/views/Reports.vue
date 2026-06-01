<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">리포트 생성</h1>
        <p class="page-desc">사용량·비용 집계 Excel 보고서 — 운영자/사용자 본인 기준</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="showCreateModal = true">
          <i class="bi bi-plus-circle"></i> 새 리포트 생성
        </button>
      </div>
    </div>
    <div v-if="alertMessage" class="alert" :class="`alert-${alertType}`">
      {{ alertMessage }}
      <button type="button" class="btn-close float-end" @click="alertMessage = ''"></button>
    </div>

    <div class="row g-4 mb-4">
      <div 
        v-for="template in reportTemplates" 
        :key="template.id"
        class="col-md-3"
      >
        <div class="card aiuiux-card h-100 template-card" @click="selectTemplate(template)">
          <div class="card-body text-center">
            <i :class="template.icon" :style="{ fontSize: '3rem', color: template.color }"></i>
            <h5 class="mt-3">{{ template.name }}</h5>
            <p class="text-muted small">{{ template.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="card aiuiux-card mb-4">
      <div class="card-header bg-transparent border-bottom">
        <h5 class="card-title mb-0">예약 리포트</h5>
      </div>
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-hover aiuiux-table">
            <thead>
              <tr>
                <th>이름</th>
                <th>유형</th>
                <th>주기</th>
                <th>수신자</th>
                <th>다음 발송</th>
                <th>상태</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="report in scheduledReports" :key="report.id">
                <td>{{ report.name }}</td>
                <td>
                  <span class="badge" :class="getTypeBadgeClass(report.type)">
                    {{ report.type }}
                  </span>
                </td>
                <td>{{ report.schedule }}</td>
                <td>{{ report.recipients }}</td>
                <td>{{ formatDate(report.nextRun) }}</td>
                <td>
                  <span class="badge" :class="report.isActive ? 'bg-success' : 'bg-secondary'">
                    {{ report.isActive ? '활성' : '비활성' }}
                  </span>
                </td>
                <td>
                  <button class="btn btn-sm btn-outline-secondary" @click="editReport(report)">
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteReport(report)">
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 생성된 리포트 -->
    <div class="card">
      <div class="card-header bg-white">
        <h5 class="mb-0">생성된 리포트</h5>
      </div>
      <div class="card-body">
        <div class="list-group">
          <div 
            v-for="report in generatedReports" 
            :key="report.id"
            class="list-group-item list-group-item-action"
          >
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <h6 class="mb-1">{{ report.name }}</h6>
                <p class="mb-1 text-muted small">{{ formatDateTime(report.createdAt) }}</p>
              </div>
              <div>
                <button class="btn btn-sm btn-primary me-2" @click="downloadReport(report, 'pdf')">
                  <i class="bi bi-download"></i> PDF
                </button>
                <button class="btn btn-sm btn-success" @click="downloadReport(report, 'excel')">
                  <i class="bi bi-file-excel"></i> Excel
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 리포트 생성 모달 -->
    <div class="modal fade" :class="{ show: showCreateModal }" :style="{ display: showCreateModal ? 'block' : 'none' }" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">새 리포트 생성</h5>
            <button type="button" class="btn-close" @click="showCreateModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="generateReport">
              <div class="mb-3">
                <label class="form-label">리포트 이름 *</label>
                <input type="text" class="form-control" v-model="reportForm.name" required>
              </div>
              <div class="mb-3">
                <label class="form-label">템플릿</label>
                <select class="form-select" v-model="reportForm.template" required>
                  <option value="">선택하세요</option>
                  <option v-for="tpl in reportTemplates" :key="tpl.id" :value="tpl.id">
                    {{ tpl.name }}
                  </option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">기간</label>
                <div class="row">
                  <div class="col-md-6">
                    <input type="date" class="form-control" v-model="reportForm.startDate" required>
                  </div>
                  <div class="col-md-6">
                    <input type="date" class="form-control" v-model="reportForm.endDate" required>
                  </div>
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label">형식</label>
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" v-model="reportForm.formats.pdf" id="format-pdf">
                  <label class="form-check-label" for="format-pdf">PDF</label>
                </div>
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" v-model="reportForm.formats.excel" id="format-excel">
                  <label class="form-check-label" for="format-excel">Excel</label>
                </div>
              </div>
              <div class="mb-3">
                <div class="form-check">
                  <input class="form-check-input" type="checkbox" v-model="reportForm.isScheduled" id="is-scheduled">
                  <label class="form-check-label" for="is-scheduled">예약 생성</label>
                </div>
              </div>
              <div v-if="reportForm.isScheduled" class="mb-3">
                <label class="form-label">스케줄</label>
                <select class="form-select" v-model="reportForm.schedule">
                  <option value="daily">매일</option>
                  <option value="weekly">매주</option>
                  <option value="monthly">매월</option>
                </select>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="generateReport">
              <i class="bi bi-play-circle"></i> 생성
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showCreateModal }" v-if="showCreateModal"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'

interface ReportTemplate {
  id: string
  name: string
  description: string
  icon: string
  color: string
}

interface ScheduledReport {
  id: string
  name: string
  type: string
  schedule: string
  recipients: string
  nextRun: string
  isActive: boolean
}

interface GeneratedReport {
  id: string
  name: string
  createdAt: string
  filePath?: string
  // 트랙 #147 M1 — backend 응답 매핑
  status?: string
  downloadUrl?: string
  reportType?: string
  fileSizeBytes?: number | null
  errorMessage?: string | null
}

interface ReportForm {
  name: string
  template: string
  startDate: string
  endDate: string
  formats: {
    pdf: boolean
    excel: boolean
  }
  isScheduled: boolean
  schedule: string
}

const showCreateModal = ref(false)

const reportTemplates = ref<ReportTemplate[]>([
  {
    id: 'daily',
    name: '일일 요약',
    description: '당일 사용량 및 비용 요약',
    icon: 'bi bi-calendar-day',
    color: '#0d6efd'
  },
  {
    id: 'weekly',
    name: '주간 분석',
    description: '주간 트렌드 및 인사이트',
    icon: 'bi bi-calendar-week',
    color: '#198754'
  },
  {
    id: 'monthly',
    name: '월간 종합',
    description: '월별 성과 및 비용 분석',
    icon: 'bi bi-calendar-month',
    color: '#ffc107'
  },
  {
    id: 'custom',
    name: '사용자 정의',
    description: '원하는 항목 선택',
    icon: 'bi bi-gear',
    color: '#6c757d'
  }
])

const scheduledReports = ref<ScheduledReport[]>([])
const generatedReports = ref<GeneratedReport[]>([
  {
    id: '1',
    name: '월간 종합 리포트 - 2024년 12월',
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
  }
])

const reportForm = ref<ReportForm>({
  name: '',
  template: '',
  startDate: '',
  endDate: '',
  formats: {
    pdf: true,
    excel: false
  },
  isScheduled: false,
  schedule: 'daily'
})

const selectTemplate = (template: ReportTemplate) => {
  reportForm.value.template = template.id
  showCreateModal.value = true
}

const alertMessage = ref('')
const alertType = ref<'success' | 'danger'>('success')
function notify(type: 'success' | 'danger', msg: string) {
  alertType.value = type
  alertMessage.value = msg
  if (type === 'success') setTimeout(() => (alertMessage.value = ''), 3500)
}

const loadGeneratedReports = async () => {
  try {
    const res = await api.get<any[]>('/reports')
    generatedReports.value = (res.data || []).map(r => ({
      id: String(r.reportId),
      name: r.name,
      createdAt: r.createdAt,
      status: r.status,
      downloadUrl: r.downloadUrl,
      reportType: r.reportType,
      fileSizeBytes: r.fileSizeBytes,
      errorMessage: r.errorMessage
    }))
  } catch (e: any) {
    notify('danger', e.response?.data?.message || '보고서 목록을 불러오지 못했습니다.')
  }
}

const generateReport = async () => {
  if (!reportForm.value.name || !reportForm.value.template) {
    notify('danger', '필수 항목을 입력하세요.')
    return
  }
  try {
    const payload: any = {
      name: reportForm.value.name,
      reportType: reportForm.value.template,  // 'daily'/'weekly'/'monthly'/'custom'
      format: 'xlsx'
    }
    if (reportForm.value.template === 'custom') {
      payload.startDate = reportForm.value.startDate
      payload.endDate = reportForm.value.endDate
    }
    await api.post('/reports', payload)
    notify('success', '보고서가 생성되었습니다.')
    await loadGeneratedReports()
    showCreateModal.value = false
    reportForm.value = { name: '', template: '', startDate: '', endDate: '', formats: { pdf: false, excel: true }, isScheduled: false, schedule: 'daily' }
  } catch (e: any) {
    notify('danger', e.response?.data?.message || '보고서 생성에 실패했습니다.')
  }
  return
  // eslint-disable-next-line no-unreachable
  if (!reportForm.value.name || !reportForm.value.template) {
    alert('필수 항목을 입력하세요.')
    return
  }

  try {
    // 리포트 생성 API 호출
    const newReport: GeneratedReport = {
      id: Date.now().toString(),
      name: reportForm.value.name,
      createdAt: new Date().toISOString()
    }
    
    generatedReports.value.unshift(newReport)

    if (reportForm.value.isScheduled) {
      const scheduled: ScheduledReport = {
        id: Date.now().toString(),
        name: reportForm.value.name,
        type: reportTemplates.value.find(t => t.id === reportForm.value.template)?.name || '',
        schedule: reportForm.value.schedule,
        recipients: 'admin@example.com',
        nextRun: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        isActive: true
      }
      scheduledReports.value.push(scheduled)
    }

    showCreateModal.value = false
    reportForm.value = {
      name: '',
      template: '',
      startDate: '',
      endDate: '',
      formats: { pdf: true, excel: false },
      isScheduled: false,
      schedule: 'daily'
    }
    
    alert('리포트가 생성되었습니다.')
  } catch (error) {
    console.error('Error generating report:', error)
    alert('리포트 생성 중 오류가 발생했습니다.')
  }
}

const editReport = (report: ScheduledReport) => {
  // 리포트 편집 로직
  alert('리포트 편집 기능 (구현 필요)')
}

const deleteReport = (report: ScheduledReport) => {
  if (confirm('리포트를 삭제하시겠습니까?')) {
    scheduledReports.value = scheduledReports.value.filter(r => r.id !== report.id)
  }
}

const downloadReport = async (report: GeneratedReport, format: string) => {
  // 트랙 #147 M1 정식 구현 — backend /api/reports/{id}/download 호출 → Blob → 브라우저 다운로드
  if (format !== 'excel' && format !== 'xlsx') {
    notify('danger', '현재 Excel(xlsx) 형식만 지원됩니다. PDF 는 후속 트랙입니다.')
    return
  }
  try {
    const res = await api.get(`/reports/${report.id}/download`, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: res.headers['content-type'] || 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${report.name}.xlsx`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e: any) {
    notify('danger', e.response?.data?.message || '보고서 다운로드에 실패했습니다.')
  }
}

const deleteGeneratedReport = async (report: GeneratedReport) => {
  if (!confirm(`"${report.name}" 보고서를 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/reports/${report.id}`)
    notify('success', '보고서가 삭제되었습니다.')
    await loadGeneratedReports()
  } catch (e: any) {
    notify('danger', e.response?.data?.message || '보고서 삭제에 실패했습니다.')
  }
}

const getTypeBadgeClass = (type: string): string => {
  if (type.includes('일일')) return 'bg-primary'
  if (type.includes('주간')) return 'bg-success'
  if (type.includes('월간')) return 'bg-warning'
  return 'bg-secondary'
}

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('ko-KR')
}

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('ko-KR')
}

onMounted(() => {
  const today = new Date()
  const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1)
  const lastDay = new Date(today.getFullYear(), today.getMonth(), 0)

  reportForm.value.startDate = lastMonth.toISOString().split('T')[0]
  reportForm.value.endDate = lastDay.toISOString().split('T')[0]

  // 트랙 #147 M1 — 진입 시 백엔드 목록 로드.
  loadGeneratedReports()
})
</script>

<style scoped>
.template-card {
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.modal.show {
  display: block;
}

.modal-backdrop.show {
  opacity: 0.5;
}
</style>
