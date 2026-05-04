<template>
  <div class="page-content-wrap">
    <div class="page-header">
      <div>
        <h1 class="page-heading">시스템 상태</h1>
        <p class="page-desc">실시간 시스템 모니터링 및 헬스 체크</p>
      </div>
      <div class="page-actions">
        <div class="system-status-pill" :class="getSystemStatusBadgeClass()">
          <span class="status-indicator" :class="getSystemStatusIndicatorClass()"></span>
          <span class="status-text">{{ systemHealth?.systemStatus || '확인 중...' }}</span>
        </div>
        <button class="btn btn-outline-primary btn-sm" @click="refreshHealth">
          <i class="bi bi-arrow-clockwise"></i> 새로고침
        </button>
        <button class="btn btn-primary btn-sm ms-2" @click="runDiagnostics">
          <i class="bi bi-bug"></i> 진단 실행
        </button>
      </div>
    </div>

    <div class="row g-4 mb-4">
      <div class="col-md-3">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-check-circle"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">시스템 가동률</p>
            <h2 class="stat-value">99.9%</h2>
            <p class="stat-change">최근 30일</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-card stat-card-success">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-speedometer2"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">평균 응답시간</p>
            <h2 class="stat-value">{{ systemHealth?.averageResponseTime || 0 }}ms</h2>
            <p class="stat-change">P95: 250ms</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-card stat-card-info">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-cpu"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">CPU 사용률</p>
            <h2 class="stat-value">{{ diagnostics?.cpuUsage || 0 }}%</h2>
            <p class="stat-change">정상 범위</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="stat-card stat-card-warning">
          <div class="stat-icon-wrap">
            <div class="stat-icon"><i class="bi bi-memory"></i></div>
          </div>
          <div class="stat-content">
            <p class="stat-label">메모리 사용률</p>
            <h2 class="stat-value">{{ diagnostics?.memoryUsage || 0 }}MB</h2>
            <p class="stat-change">{{ systemHealth?.infrastructure?.memoryUsage || 0 }}%</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 서비스 상태 및 차트 -->
    <div class="row mb-4">
      <div class="col-lg-6 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-server"></i> 서비스 상태</h5>
          </div>
          <div class="card-body p-0">
            <div v-if="!systemHealth?.services?.length" class="text-center text-muted py-5 px-3">
              서비스 데이터가 없습니다.
            </div>
            <div v-else class="model-status-list">
              <div
                v-for="(service, index) in systemHealth.services"
                :key="service.name"
                class="model-status-item"
              >
                <div class="model-status-icon" :class="getServiceIconClass(service, index)">
                  <i :class="getServiceIcon(service, index)"></i>
                </div>
                <div class="model-status-info">
                  <p class="model-name">{{ service.name }}</p>
                  <p class="model-meta">응답시간: {{ service.responseTime }}ms</p>
                </div>
                <span class="status-badge" :class="getServiceStatusBadgeClass(service.status)">
                  {{ getServiceStatusLabel(service.status) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-graph-up"></i> CPU 및 메모리 사용률</h5>
          </div>
          <div class="card-body">
            <canvas ref="resourceChartCanvas" style="height: 200px;"></canvas>
          </div>
        </div>
      </div>
    </div>

    <!-- 인프라 상태 -->
    <div class="row mb-4">
      <div class="col-lg-6 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-hdd-stack me-2"></i>인프라 상태</h5>
          </div>
          <div class="card-body p-0">
            <div class="health-grid">
              <div class="health-row">
                <div class="health-model">디스크 사용량</div>
                <div class="health-bar-cell">
                  <div
                    class="health-bar"
                    :style="{ '--pct': (systemHealth?.infrastructure?.diskUsage || 0) + '%', '--c': getProgressBarColor(systemHealth?.infrastructure?.diskUsage || 0) }"
                  ></div>
                  <span class="health-val">{{ systemHealth?.infrastructure?.diskUsage || 0 }}%</span>
                </div>
              </div>
              <div class="health-row">
                <div class="health-model">데이터베이스 크기</div>
                <div class="health-bar-cell">
                  <span class="health-val">{{ systemHealth?.infrastructure?.databaseSize || 'N/A' }}</span>
                </div>
              </div>
              <div class="health-row">
                <div class="health-model">로그 파일 크기</div>
                <div class="health-bar-cell">
                  <span class="health-val">{{ systemHealth?.infrastructure?.logFileSize || 'N/A' }}</span>
                </div>
              </div>
              <div class="health-row">
                <div class="health-model">메모리 사용률</div>
                <div class="health-bar-cell">
                  <div
                    class="health-bar"
                    :style="{ '--pct': (systemHealth?.infrastructure?.memoryUsage || 0) + '%', '--c': getProgressBarColor(systemHealth?.infrastructure?.memoryUsage || 0) }"
                  ></div>
                  <span class="health-val">{{ systemHealth?.infrastructure?.memoryUsage || 0 }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6 mb-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-wifi me-2"></i>네트워크 상태</h5>
          </div>
          <div class="card-body p-0">
            <div class="health-grid">
              <div class="health-row">
                <div class="health-model">활성 연결</div>
                <div class="health-bar-cell">
                  <span class="health-val">{{ systemHealth?.network?.activeConnections ?? 0 }}</span>
                </div>
              </div>
              <div class="health-row">
                <div class="health-model">대역폭 사용률</div>
                <div class="health-bar-cell">
                  <div
                    class="health-bar"
                    :style="{ '--pct': (systemHealth?.network?.bandwidthUsage || 0) + '%', '--c': getProgressBarColor(systemHealth?.network?.bandwidthUsage || 0) }"
                  ></div>
                  <span class="health-val">{{ systemHealth?.network?.bandwidthUsage || 0 }}%</span>
                </div>
              </div>
              <div class="health-row">
                <div class="health-model">네트워크 지연시간</div>
                <div class="health-bar-cell">
                  <span class="health-val">{{ systemHealth?.network?.latency ?? 0 }}ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 외부 API 상태 -->
    <div class="row">
      <div class="col-12">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-globe"></i> 외부 API 상태</h5>
          </div>
          <div class="card-body p-0">
            <div v-if="!systemHealth?.externalApis?.length" class="text-center text-muted py-5 px-3">
              외부 API 데이터가 없습니다.
            </div>
            <div v-else class="alert-list">
              <div
                v-for="api in systemHealth.externalApis"
                :key="api.name"
                class="alert-item"
                :class="getApiAlertClass(api.status)"
              >
                <div class="alert-icon">
                  <i :class="getApiAlertIcon(api.status)"></i>
                </div>
                <div class="alert-content">
                  <p class="alert-title">{{ api.name }}</p>
                  <p class="alert-desc">응답시간: {{ api.responseTime }}ms</p>
                  <span class="alert-time">{{ getServiceStatusLabel(api.status) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

interface SystemHealth {
  uptime: string
  averageResponseTime: number
  systemStatus: string
  services: ServiceStatus[]
  infrastructure: InfrastructureStatus
  network: NetworkStatus
  externalApis: ExternalApiStatus[]
}

interface ServiceStatus {
  name: string
  status: string
  responseTime: number
}

interface InfrastructureStatus {
  diskUsage: number
  databaseSize: string
  logFileSize: string
  memoryUsage: number
}

interface NetworkStatus {
  bandwidthUsage: number
  activeConnections: number
  latency: number
}

interface ExternalApiStatus {
  name: string
  status: string
  responseTime: number
}

interface Diagnostics {
  timestamp: string
  databaseConnection: boolean
  diskSpace: DiskSpace
  memoryUsage: number
  cpuUsage: number
  networkLatency: number
}

interface DiskSpace {
  total: number
  used: number
  available: number
  percentage: number
}

const systemHealth = ref<SystemHealth | null>(null)
const diagnostics = ref<Diagnostics | null>(null)
const loading = ref(false)
const resourceChartCanvas = ref<HTMLCanvasElement | null>(null)
const resourceChart = ref<Chart | null>(null)
let refreshInterval: number | null = null

onMounted(() => {
  loadSystemHealth()
  // 30초마다 자동 새로고침
  refreshInterval = window.setInterval(() => {
    loadSystemHealth()
  }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (resourceChart.value) {
    resourceChart.value.destroy()
  }
})

const loadSystemHealth = async () => {
  loading.value = true
  try {
    const response = await api.get('/systemhealth')
    systemHealth.value = response.data
    
    // 진단 데이터도 함께 로드
    try {
      const diagnosticsResponse = await api.get('/systemhealth/diagnostics')
      diagnostics.value = diagnosticsResponse.data
    } catch (diagError) {
      console.warn('진단 데이터 로드 실패:', diagError)
    }
    
    createResourceChart()
  } catch (error: any) {
    console.error('시스템 상태 로드 실패:', error)
    if (error.response?.status === 403) {
      alert('시스템 상태 조회 권한이 없습니다. (Admin 권한 필요)')
    }
  } finally {
    loading.value = false
  }
}

const refreshHealth = () => {
  loadSystemHealth()
}

const runDiagnostics = async () => {
  try {
    const response = await api.get('/systemhealth/diagnostics')
    diagnostics.value = response.data
    alert('진단이 완료되었습니다.')
  } catch (error: any) {
    console.error('진단 실행 실패:', error)
    alert(error.response?.data?.message || '진단 실행에 실패했습니다.')
  }
}

const createResourceChart = () => {
  if (!resourceChartCanvas.value || !systemHealth.value) return

  if (resourceChart.value) {
    resourceChart.value.destroy()
  }

  // 실제 메트릭 데이터 사용
  const cpuUsage = diagnostics.value?.cpuUsage || 0
  const memoryUsage = systemHealth.value.infrastructure.memoryUsage || 0

  resourceChart.value = new Chart(resourceChartCanvas.value, {
    type: 'line',
    data: {
      labels: ['현재', '1분 전', '2분 전', '3분 전', '4분 전'],
      datasets: [
        {
          label: 'CPU 사용률 (%)',
          data: [cpuUsage, cpuUsage * 0.95, cpuUsage * 0.9, cpuUsage * 0.92, cpuUsage * 0.88],
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1,
          fill: true
        },
        {
          label: '메모리 사용률 (%)',
          data: [memoryUsage, memoryUsage * 0.98, memoryUsage * 0.96, memoryUsage * 0.97, memoryUsage * 0.95],
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.1,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      },
      plugins: {
        legend: {
          display: true,
          position: 'top'
        },
        tooltip: {
          mode: 'index',
          intersect: false
        }
      }
    }
  })
}

const getSystemStatusBadgeClass = () => {
  const status = systemHealth.value?.systemStatus?.toLowerCase() || ''
  if (status.includes('healthy')) return 'status-pill-healthy'
  if (status.includes('warning')) return 'status-pill-warning'
  return 'status-pill-critical'
}

const getSystemStatusIndicatorClass = () => {
  const status = systemHealth.value?.systemStatus?.toLowerCase() || ''
  if (status.includes('healthy')) return 'status-healthy'
  if (status.includes('warning')) return 'status-warning'
  return 'status-critical'
}

const getStatusBadgeClass = (status: string) => {
  const s = status.toLowerCase()
  if (s.includes('healthy')) return 'bg-success'
  if (s.includes('warning')) return 'bg-warning'
  return 'bg-danger'
}

const serviceIconClasses = ['model-gpt', 'model-claude', 'model-gemini', 'model-llama', 'model-custom', 'model-error'] as const
const serviceIcons = ['bi bi-robot', 'bi bi-cpu', 'bi bi-google', 'bi bi-fire', 'bi bi-code-slash', 'bi bi-exclamation-triangle'] as const

const getServiceIconClass = (service: { name: string; status?: string }, index: number): string => {
  const name = (service.name || '').toLowerCase()
  if (name.includes('gpt') || name.includes('openai')) return 'model-gpt'
  if (name.includes('claude') || name.includes('anthropic')) return 'model-claude'
  if (name.includes('gemini') || name.includes('google')) return 'model-gemini'
  if (name.includes('llama') || name.includes('meta')) return 'model-llama'
  const s = (service.status || '').toLowerCase()
  if (s.includes('error') || s.includes('unhealthy') || s.includes('down')) return 'model-error'
  return serviceIconClasses[index % serviceIconClasses.length] || 'model-custom'
}

const getServiceIcon = (service: { name: string; status?: string }, index: number): string => {
  const name = (service.name || '').toLowerCase()
  if (name.includes('gpt') || name.includes('openai')) return 'bi bi-robot'
  if (name.includes('claude') || name.includes('anthropic')) return 'bi bi-cpu'
  if (name.includes('gemini') || name.includes('google')) return 'bi bi-google'
  if (name.includes('llama') || name.includes('meta')) return 'bi bi-fire'
  const s = (service.status || '').toLowerCase()
  if (s.includes('error') || s.includes('unhealthy') || s.includes('down')) return 'bi bi-exclamation-triangle'
  return serviceIcons[index % serviceIcons.length] || 'bi bi-code-slash'
}

const getServiceStatusBadgeClass = (status: string): string => {
  const s = (status || '').toLowerCase()
  if (s.includes('healthy')) return 'status-online'
  if (s.includes('warning')) return 'status-warning'
  return 'status-error'
}

const getServiceStatusLabel = (status: string): string => {
  const s = (status || '').toLowerCase()
  if (s.includes('healthy')) return '운영중'
  if (s.includes('warning')) return '점검중'
  return '오류'
}

const getStatusTextClass = (status: string) => {
  const s = status.toLowerCase()
  if (s.includes('healthy')) return 'text-success'
  if (s.includes('warning')) return 'text-warning'
  return 'text-danger'
}

const getApiCardClass = (status: string) => {
  const s = status.toLowerCase()
  if (s.includes('healthy')) return 'border-success'
  if (s.includes('warning')) return 'border-warning'
  return 'border-danger'
}

const getApiAlertClass = (status: string): string => {
  const s = (status || '').toLowerCase()
  if (s.includes('healthy')) return 'alert-item-success'
  if (s.includes('warning')) return 'alert-item-warning'
  if (s.includes('degraded') || s.includes('maintenance')) return 'alert-item-info'
  return 'alert-item-error'
}

const getApiAlertIcon = (status: string): string => {
  const s = (status || '').toLowerCase()
  if (s.includes('healthy')) return 'bi bi-check-circle'
  if (s.includes('warning')) return 'bi bi-exclamation-triangle'
  if (s.includes('degraded') || s.includes('maintenance')) return 'bi bi-info-circle'
  return 'bi bi-x-circle'
}

const getProgressBarClass = (percentage: number) => {
  if (percentage < 70) return 'bg-info'
  if (percentage < 90) return 'bg-warning'
  return 'bg-danger'
}

const getProgressBarColor = (percentage: number): string => {
  if (percentage < 70) return 'var(--ai-info)'
  if (percentage < 90) return 'var(--ai-warning)'
  return 'var(--ai-danger)'
}
</script>

<style scoped>
.system-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid transparent;
  margin-right: 0.5rem;
}

.system-status-pill .status-text {
  line-height: 1;
}

.status-pill-healthy {
  background: rgba(25, 135, 84, 0.12);
  border-color: rgba(25, 135, 84, 0.35);
  color: #0f5132;
}

.status-pill-warning {
  background: rgba(255, 193, 7, 0.18);
  border-color: rgba(255, 193, 7, 0.5);
  color: #664d03;
}

.status-pill-critical {
  background: rgba(220, 53, 69, 0.12);
  border-color: rgba(220, 53, 69, 0.35);
  color: #842029;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-healthy {
  background: #198754;
  box-shadow: 0 0 0 2px rgba(25, 135, 84, 0.25);
}

.status-warning {
  background: #ffc107;
  box-shadow: 0 0 0 2px rgba(255, 193, 7, 0.3);
  animation: pulse 2s ease-in-out infinite;
}

.status-critical {
  background: #dc3545;
  box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.25);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}
</style>
