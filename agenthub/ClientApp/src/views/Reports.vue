<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">
          리포트 생성
          <span class="badge bg-warning text-dark ms-2">준비 중</span>
        </h1>
        <p class="page-desc">자동 리포트 생성 및 예약 관리 — 정식 구현 대기 상태입니다.</p>
      </div>
      <div class="page-actions">
        <button class="btn btn-primary btn-sm" @click="showCreateModal = true">
          <i class="bi bi-plus-circle"></i> 새 리포트 생성
        </button>
      </div>
    </div>
    <!-- 트랙 #147 M1 (2026-06-01): 정식 구현 대기 안내. backend ReportsController /
         GeneratedReport 엔티티 미신설. 대체 메뉴 안내. -->
    <div class="alert alert-warning d-flex align-items-start gap-2 mb-4">
      <i class="bi bi-exclamation-triangle-fill flex-shrink-0 mt-1"></i>
      <div>
        <strong>본 화면은 정식 구현 대기 상태입니다.</strong>
        <div class="small mt-1">
          백엔드 ReportsController / Hangfire 백그라운드 작업 (사용량·비용 집계 → PDF/Excel 생성) 구현 예정.
          현재 운영 가능한 대체 메뉴:
          <ul class="mb-0 mt-1">
            <li><router-link to="/analytics">통계 (사용량 분석)</router-link></li>
            <li><router-link to="/usage-history">사용 기록</router-link></li>
            <li><router-link to="/admin/docutil-reports">DocUtil 보고서</router-link> — 문서 기반 보고서</li>
          </ul>
        </div>
      </div>
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

const generateReport = async () => {
  // 트랙 #147 M1 (2026-06-01): 정식 구현 대기 — 명시적 안내.
  alert(
    '[안내] 운영자 보고서 생성은 정식 구현 대기 상태입니다.\n\n' +
    '백엔드 ReportsController / ReportsService / GeneratedReport 엔티티 + ' +
    'Hangfire 백그라운드 작업 (사용량/비용 집계 → PDF/Excel) 구현 예정.\n\n' +
    '대체 안내:\n' +
    '• 사용량 분석: /analytics\n' +
    '• 사용 기록: /usage-history\n' +
    '• DocUtil 보고서: /admin/docutil-reports'
  )
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

const downloadReport = (report: GeneratedReport, format: string) => {
  // 트랙 #147 M1 (2026-06-01): /reports 화면은 운영자 보고서 정식 구현 대기 상태.
  // backend ReportsController / ReportsService / GeneratedReport 엔티티 모두 미신설.
  // 진짜 다운로드는 별도 트랙 (Hangfire 작업 + ApiUsages 집계 기반 PDF/Excel 생성)
  // 에서 구현 예정. 현재는 운영자에게 명확히 미구현 안내.
  alert(
    `[안내] 운영자 보고서 화면은 정식 구현 대기 상태입니다.\n` +
    `현재 [${report.name}] 의 ${format.toUpperCase()} 다운로드는 미구현입니다.\n\n` +
    `대체 안내:\n` +
    `• 사용량 분석: /analytics 메뉴\n` +
    `• 사용 기록: /usage-history 메뉴\n` +
    `• DocUtil 보고서: /admin/docutil-reports 메뉴`
  )
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
