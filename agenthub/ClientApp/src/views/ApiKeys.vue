<template>
  <div class="page-content-wrap">

    <!-- ── 페이지 헤더 ── -->
    <div class="page-header">
      <div>
        <h1 class="page-heading">API 키 관리</h1>
        <p class="page-desc">외부 AI 서비스 API 키와 Agent API 키를 안전하게 관리하세요</p>
      </div>
      <div class="page-actions">
        <button v-if="activeTab === 'service'" class="btn btn-primary btn-sm" @click="showAddModal = true">
          <i class="bi bi-plus-circle me-1"></i>새 API 키 추가
        </button>
        <button v-else-if="activeTab === 'agent'" class="btn btn-primary btn-sm"
          @click="openAgentKeyModal" :disabled="!selectedAgentId">
          <i class="bi bi-plus-circle me-1"></i>Agent API 키 발급
        </button>
        <!-- 트랙 #91: 탭 3 운영자 전용 외부 LLM 키 등록 -->
        <button v-else-if="activeTab === 'provider-pool' && isAdmin" class="btn btn-primary btn-sm"
          @click="openProviderModal">
          <i class="bi bi-plus-circle me-1"></i>{{ t('apiKeys.provider.list.addButton') }}
        </button>
      </div>
    </div>

    <!-- ── 탭 ── -->
    <div class="ak-tabs" role="tablist">
      <button type="button" role="tab" class="ak-tab" :class="{ active: activeTab === 'service' }"
        :aria-selected="activeTab === 'service'" @click="activeTab = 'service'">
        <i class="bi bi-cloud-fill" aria-hidden="true"></i>
        <span>외부 서비스 API 키</span>
        <span class="ak-tab-badge" v-if="apiKeys.length">{{ apiKeys.length }}</span>
      </button>
      <button type="button" role="tab" class="ak-tab" :class="{ active: activeTab === 'agent' }"
        :aria-selected="activeTab === 'agent'" @click="switchToAgentTab">
        <i class="bi bi-robot" aria-hidden="true"></i>
        <span>Agent API 키</span>
        <span class="ak-tab-badge" v-if="agentApiKeys.length">{{ agentApiKeys.length }}</span>
      </button>
      <!-- 트랙 #91: 운영자(Admin/SuperAdmin) 전용 외부 LLM 키 풀 탭 -->
      <button v-if="isAdmin" type="button" role="tab" class="ak-tab"
        :class="{ active: activeTab === 'provider-pool' }"
        :aria-selected="activeTab === 'provider-pool'" @click="activeTab = 'provider-pool'">
        <i class="bi bi-shield-lock" aria-hidden="true"></i>
        <span>{{ t('apiKeys.tabs.providerPool') }}</span>
        <span class="ak-tab-badge" v-if="providerKeys.length">{{ providerKeys.length }}</span>
      </button>
    </div>

    <!-- ════════════════════════════════════════
         탭 1: 외부 서비스 API 키
    ════════════════════════════════════════ -->
    <div v-show="activeTab === 'service'" class="row g-4">

      <!-- 키 목록 -->
      <div class="col-lg-8">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
            <div>
              <h5 class="card-title mb-0">등록된 서비스 API 키</h5>
              <p class="card-subtitle mb-0 mt-1">외부 AI 서비스 접근에 사용되는 키 목록</p>
            </div>
            <span class="badge bg-primary-subtle text-primary fs-7">{{ apiKeys.length }}개</span>
          </div>
          <div class="card-body p-0">

            <!-- 로딩 -->
            <div v-if="loading" class="text-center py-5">
              <div class="spinner-border text-primary" role="status"><span class="visually-hidden">로딩 중...</span></div>
              <p class="mt-3 mb-0 text-muted small">API 키를 불러오는 중...</p>
            </div>

            <!-- 빈 상태 -->
            <div v-else-if="apiKeys.length === 0" class="ak-empty-state">
              <div class="ak-empty-icon"><i class="bi bi-key"></i></div>
              <p class="ak-empty-title">등록된 API 키가 없습니다</p>
              <p class="ak-empty-desc">외부 AI 서비스(OpenAI, Claude 등)의 API 키를 등록하세요</p>
              <button class="btn btn-primary btn-sm" @click="showAddModal = true">
                <i class="bi bi-plus-circle me-1"></i>첫 API 키 추가
              </button>
            </div>

            <!-- 키 목록 -->
            <div v-else class="ak-key-list">
              <div v-for="key in apiKeys" :key="key.apiKeyId" class="ak-key-row"
                :class="{ 'ak-key-row--inactive': !key.isActive, 'ak-key-row--expired': key.expiresAt && isExpired(key.expiresAt) }">

                <!-- 헤더 영역 -->
                <div class="ak-key-head">
                  <div class="ak-key-icon-wrap">
                    <i class="bi" :class="getServiceIcon(key.serviceCode)"></i>
                  </div>
                  <div class="ak-key-info">
                    <span class="ak-key-name">{{ key.keyName }}</span>
                    <span class="ak-key-service">{{ key.serviceName || key.serviceCode }}</span>
                  </div>
                  <div class="ak-key-badges ms-auto d-flex align-items-center gap-2">
                    <span v-if="key.expiresAt && isExpired(key.expiresAt)" class="badge bg-danger-subtle text-danger">만료됨</span>
                    <span v-else-if="key.expiresAt && isExpiringSoon(key.expiresAt)" class="badge bg-warning-subtle text-warning">만료 임박</span>
                    <span class="badge" :class="key.isActive ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'">
                      <i class="bi" :class="key.isActive ? 'bi-circle-fill' : 'bi-circle'"></i>
                      {{ key.isActive ? '활성' : '비활성' }}
                    </span>
                  </div>
                </div>

                <!-- 설명 -->
                <p v-if="key.description" class="ak-key-desc">{{ key.description }}</p>

                <!-- 키 값 표시 -->
                <div class="ak-key-value-row">
                  <div class="input-group input-group-sm">
                    <span class="input-group-text ak-key-prefix"><i class="bi bi-lock-fill"></i></span>
                    <input
                      :type="revealedKeys[key.apiKeyId] ? 'text' : 'password'"
                      class="form-control font-monospace ak-key-input"
                      :value="revealedKeys[key.apiKeyId] || key.maskedKey"
                      readonly
                      :id="'key-input-' + key.apiKeyId"
                    >
                    <button class="btn btn-outline-secondary" @click="toggleReveal(key.apiKeyId)" :title="revealedKeys[key.apiKeyId] ? '숨기기' : '보기'">
                      <i class="bi" :class="revealedKeys[key.apiKeyId] ? 'bi-eye-slash' : 'bi-eye'"></i>
                    </button>
                    <button class="btn btn-outline-primary" @click="copyToClipboard(key.apiKeyId, revealedKeys[key.apiKeyId] || key.maskedKey || '')" title="복사">
                      <i class="bi" :class="copiedKeyId === key.apiKeyId ? 'bi-check2' : 'bi-clipboard'"></i>
                    </button>
                  </div>
                </div>

                <!-- 메타 정보 -->
                <div class="ak-key-meta">
                  <span v-if="key.lastUsedAt">
                    <i class="bi bi-clock-history"></i> 마지막 사용 {{ formatDate(key.lastUsedAt) }}
                  </span>
                  <span v-if="key.usageCount">
                    <i class="bi bi-bar-chart-line"></i> {{ key.usageCount.toLocaleString() }}회 사용
                  </span>
                  <span>
                    <i class="bi bi-calendar-plus"></i> {{ formatDate(key.createdAt) }} 추가
                  </span>
                  <span v-if="key.expiresAt" :class="isExpired(key.expiresAt) ? 'text-danger' : isExpiringSoon(key.expiresAt) ? 'text-warning' : ''">
                    <i class="bi bi-calendar-x"></i> {{ formatDate(key.expiresAt) }} 만료
                  </span>
                </div>

                <!-- 액션 버튼 -->
                <div class="ak-key-actions">
                  <button class="btn btn-sm btn-outline-secondary" @click="editKey(key)" :disabled="!key.isActive">
                    <i class="bi bi-pencil me-1"></i>수정
                  </button>
                  <button class="btn btn-sm" :class="key.isActive ? 'btn-outline-warning' : 'btn-outline-success'" @click="toggleActive(key)">
                    <i class="bi" :class="key.isActive ? 'bi-pause-circle' : 'bi-play-circle'"></i>
                    {{ key.isActive ? '비활성화' : '활성화' }}
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteKey(key)">
                    <i class="bi bi-trash me-1"></i>삭제
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- 사이드바 -->
      <div class="col-lg-4 d-flex flex-column gap-4">

        <!-- 통계 카드 -->
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-bar-chart me-2 text-primary"></i>사용 현황</h5>
          </div>
          <div class="card-body">
            <div class="ak-stat-row">
              <span class="ak-stat-label">전체 API 키</span>
              <span class="ak-stat-value">{{ apiKeys.length }}</span>
            </div>
            <div class="progress ak-stat-bar mb-3" style="height:6px;" v-if="apiKeys.length">
              <div class="progress-bar bg-success" :style="{ width: (activeKeysCount / apiKeys.length * 100) + '%' }"></div>
              <div class="progress-bar bg-secondary" :style="{ width: (inactiveKeysCount / apiKeys.length * 100) + '%' }"></div>
            </div>
            <div class="ak-stat-row">
              <span class="ak-stat-label"><i class="bi bi-circle-fill text-success me-1" style="font-size:0.55rem;"></i>활성</span>
              <span class="ak-stat-value text-success">{{ activeKeysCount }}</span>
            </div>
            <div class="ak-stat-row">
              <span class="ak-stat-label"><i class="bi bi-circle-fill text-secondary me-1" style="font-size:0.55rem;"></i>비활성</span>
              <span class="ak-stat-value text-secondary">{{ inactiveKeysCount }}</span>
            </div>
            <div class="ak-stat-row" v-if="expiredKeysCount > 0">
              <span class="ak-stat-label"><i class="bi bi-circle-fill text-danger me-1" style="font-size:0.55rem;"></i>만료됨</span>
              <span class="ak-stat-value text-danger">{{ expiredKeysCount }}</span>
            </div>
          </div>
        </div>

        <!-- 보안 권장사항 -->
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-shield-check me-2 text-success"></i>보안 권장사항</h5>
          </div>
          <div class="card-body">
            <ul class="ak-security-list">
              <li><i class="bi bi-lock-fill text-success"></i>API 키는 AES-256으로 암호화 저장됩니다</li>
              <li><i class="bi bi-arrow-repeat text-primary"></i>노출된 키는 즉시 재발급하세요</li>
              <li><i class="bi bi-calendar-check text-warning"></i>만료일을 설정해 자동 갱신 주기를 관리하세요</li>
              <li><i class="bi bi-eye-slash text-secondary"></i>키는 조회 시에만 복호화되어 표시됩니다</li>
              <li><i class="bi bi-trash text-danger"></i>사용하지 않는 키는 즉시 삭제하세요</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════
         탭 2: Agent API 키
    ════════════════════════════════════════ -->
    <div v-show="activeTab === 'agent'" class="row g-4">

      <!-- 키 목록 -->
      <div class="col-lg-8">

        <!-- Agent 선택 바 -->
        <div class="ak-agent-select-bar mb-3">
          <label class="ak-agent-select-label">
            <i class="bi bi-robot text-primary"></i> Agent 선택
          </label>
          <select class="form-select form-select-sm ak-agent-select" v-model="selectedAgentId" @change="onAgentSelect">
            <option :value="null">-- Agent를 선택하세요 --</option>
            <option v-for="a in myAgents" :key="a.agentId" :value="a.agentId">{{ a.agentName }}</option>
          </select>
        </div>

        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
            <div>
              <h5 class="card-title mb-0">Agent API 키</h5>
              <p class="card-subtitle mb-0 mt-1">선택한 Agent를 외부에서 호출할 수 있는 키</p>
            </div>
            <span v-if="selectedAgentId" class="badge bg-primary-subtle text-primary fs-7">{{ agentApiKeys.length }}개</span>
          </div>
          <div class="card-body p-0">

            <!-- Agent 미선택 -->
            <div v-if="!selectedAgentId" class="ak-empty-state">
              <div class="ak-empty-icon"><i class="bi bi-robot"></i></div>
              <p class="ak-empty-title">Agent를 선택해주세요</p>
              <p class="ak-empty-desc">상단에서 Agent를 선택하면 해당 API 키를 관리할 수 있습니다</p>
            </div>

            <!-- 로딩 -->
            <div v-else-if="loadingAgentKeys" class="text-center py-5">
              <div class="spinner-border text-primary" role="status"></div>
              <p class="mt-3 mb-0 text-muted small">API 키 목록 조회 중...</p>
            </div>

            <!-- 빈 상태 -->
            <div v-else-if="agentApiKeys.length === 0" class="ak-empty-state">
              <div class="ak-empty-icon text-primary"><i class="bi bi-key"></i></div>
              <p class="ak-empty-title">발급된 API 키가 없습니다</p>
              <p class="ak-empty-desc">이 Agent에 대한 첫 번째 API 키를 발급하세요</p>
              <button class="btn btn-primary btn-sm" @click="openAgentKeyModal">
                <i class="bi bi-plus-circle me-1"></i>첫 API 키 발급
              </button>
            </div>

            <!-- Agent 키 목록 -->
            <div v-else class="ak-key-list">
              <div v-for="key in agentApiKeys" :key="key.apiKeyId" class="ak-key-row"
                :class="{ 'ak-key-row--inactive': !key.isActive, 'ak-key-row--expired': key.expiresAt && isExpired(key.expiresAt) }">
                <div class="ak-key-head">
                  <div class="ak-key-icon-wrap ak-key-icon-agent">
                    <i class="bi bi-key-fill"></i>
                  </div>
                  <div class="ak-key-info">
                    <span class="ak-key-name">{{ key.keyName || 'Agent API Key' }}</span>
                    <span class="ak-key-service font-monospace">{{ key.maskedKey || 'ak-xxxx...xxxx' }}</span>
                  </div>
                  <div class="ak-key-badges ms-auto d-flex align-items-center gap-2">
                    <span v-if="key.expiresAt && isExpired(key.expiresAt)" class="badge bg-danger-subtle text-danger">만료됨</span>
                    <span v-else-if="key.expiresAt && isExpiringSoon(key.expiresAt)" class="badge bg-warning-subtle text-warning">만료 임박</span>
                    <span class="badge" :class="key.isActive ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'">
                      <i class="bi" :class="key.isActive ? 'bi-circle-fill' : 'bi-circle'"></i>
                      {{ key.isActive ? '활성' : '비활성' }}
                    </span>
                  </div>
                </div>

                <p v-if="key.description" class="ak-key-desc">{{ key.description }}</p>

                <div class="ak-key-meta">
                  <span v-if="key.lastUsedAt"><i class="bi bi-clock-history"></i> 마지막 사용 {{ formatDate(key.lastUsedAt) }}</span>
                  <span v-if="key.usageCount"><i class="bi bi-bar-chart-line"></i> {{ key.usageCount.toLocaleString() }}회 호출</span>
                  <span><i class="bi bi-calendar-plus"></i> {{ formatDate(key.createdAt) }} 발급</span>
                  <span v-if="key.expiresAt" :class="isExpired(key.expiresAt) ? 'text-danger' : isExpiringSoon(key.expiresAt) ? 'text-warning' : ''">
                    <i class="bi bi-calendar-x"></i> {{ formatDate(key.expiresAt) }} 만료
                  </span>
                </div>

                <div class="ak-key-actions">
                  <button class="btn btn-sm btn-outline-primary" @click="copyAgentKey(key)" title="마스킹된 키 복사">
                    <i class="bi" :class="copiedKeyId === key.apiKeyId ? 'bi-check2' : 'bi-clipboard'"></i>
                    {{ copiedKeyId === key.apiKeyId ? '복사됨!' : '키 복사' }}
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteAgentApiKey(key)">
                    <i class="bi bi-trash me-1"></i>삭제
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 사이드바: API 사용 가이드 -->
      <div class="col-lg-4 d-flex flex-column gap-4">

        <!-- API 엔드포인트 안내 -->
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom">
            <h5 class="card-title mb-0"><i class="bi bi-code-slash me-2 text-primary"></i>API 사용 가이드</h5>
          </div>
          <div class="card-body">
            <p class="small text-muted mb-3">
              발급된 API 키를 헤더에 포함해 외부 시스템에서 이 Agent를 직접 호출할 수 있습니다.
            </p>

            <div class="ak-guide-section">
              <span class="ak-guide-label">Base URL</span>
              <div class="ak-code-block d-flex align-items-center gap-2">
                <code class="flex-1">{{ baseUrl }}/api/agents/{agentId}/chat</code>
                <button class="btn btn-link btn-sm p-0 text-muted" @click="copyText(baseUrl + '/api/agents/{agentId}/chat')" title="복사">
                  <i class="bi bi-clipboard"></i>
                </button>
              </div>
            </div>

            <div class="ak-guide-section">
              <span class="ak-guide-label">인증 헤더</span>
              <div class="ak-code-block">
                <code>X-API-Key: ak-xxxxxxxxxxxxxxxx</code>
                <br><code class="text-muted">또는</code>
                <br><code>Authorization: Bearer ak-xxxxxxxxxxxxxxxx</code>
              </div>
            </div>

            <div class="ak-guide-section">
              <span class="ak-guide-label">curl 예시</span>
              <div class="ak-code-block ak-code-multiline">
<pre>curl -X POST \
  {{ baseUrl }}/api/agents/{{'{agentId}'}}/chat \
  -H "X-API-Key: <span class="text-warning">YOUR_KEY</span>" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'</pre>
              </div>
            </div>

            <div class="ak-guide-section">
              <span class="ak-guide-label">응답 예시</span>
              <div class="ak-code-block ak-code-multiline">
<pre>{
  "message": "안녕하세요! 무엇을 ...",
  "conversationId": "xxx",
  "usage": { "tokens": 150 }
}</pre>
              </div>
            </div>
          </div>
        </div>

        <!-- 주의사항 -->
        <div class="card aiuiux-card border-warning-subtle">
          <div class="card-header bg-warning-subtle border-bottom border-warning-subtle">
            <h5 class="card-title mb-0 text-warning"><i class="bi bi-exclamation-triangle me-2"></i>키 관리 주의사항</h5>
          </div>
          <div class="card-body">
            <ul class="ak-security-list">
              <li><i class="bi bi-eye-slash text-warning"></i>키는 발급 직후 <strong>한 번만</strong> 전체 표시됩니다</li>
              <li><i class="bi bi-shield-lock text-primary"></i>키를 코드에 직접 하드코딩하지 마세요</li>
              <li><i class="bi bi-file-lock text-success"></i>환경 변수(.env)나 비밀 저장소를 사용하세요</li>
              <li><i class="bi bi-person-lock text-secondary"></i>키는 사용 목적별로 분리 발급하세요</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════
         탭 3 (트랙 #91): 외부 LLM 키 풀(운영자)
         - 운영자(Admin/SuperAdmin) 전용
         - 좌측: KeyType='Provider' 키 목록 + 액션 (테스트/삭제)
         - 우측: 풀 통계 카드 (DB/설정/냉각 출처 분리)
    ════════════════════════════════════════ -->
    <div v-show="activeTab === 'provider-pool' && isAdmin" class="row g-4">

      <!-- 좌측: 외부 LLM 키 목록 -->
      <div class="col-lg-8">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
            <div>
              <h5 class="card-title mb-0">{{ t('apiKeys.provider.list.title') }}</h5>
              <p class="card-subtitle mb-0 mt-1">{{ t('apiKeys.provider.list.subtitle') }}</p>
            </div>
            <span class="badge bg-primary-subtle text-primary fs-7">{{ providerKeys.length }}개</span>
          </div>
          <div class="card-body p-0">

            <!-- 빈 상태 -->
            <div v-if="providerKeys.length === 0" class="ak-empty-state">
              <div class="ak-empty-icon"><i class="bi bi-shield-lock"></i></div>
              <p class="ak-empty-title">{{ t('apiKeys.provider.list.empty') }}</p>
              <button class="btn btn-primary btn-sm" @click="openProviderModal">
                <i class="bi bi-plus-circle me-1"></i>{{ t('apiKeys.provider.list.addButton') }}
              </button>
            </div>

            <!-- 키 목록 -->
            <div v-else class="ak-key-list">
              <div v-for="key in providerKeys" :key="key.apiKeyId" class="ak-key-row"
                :class="{
                  'ak-key-row--inactive': !key.isActive,
                  'ak-key-row--expired': key.expiresAt && isExpired(key.expiresAt)
                }">

                <!-- 헤더 영역 -->
                <div class="ak-key-head">
                  <div class="ak-key-icon-wrap">
                    <i class="bi" :class="getServiceIcon(key.serviceCode)"></i>
                  </div>
                  <div class="ak-key-info">
                    <span class="ak-key-name">{{ key.keyName }}</span>
                    <span class="ak-key-service font-monospace">{{ key.maskedKey || 'sk-***...***' }}</span>
                  </div>
                  <div class="ak-key-badges ms-auto d-flex align-items-center gap-2">
                    <!-- 프로바이더 색상 배지 -->
                    <span class="badge" :class="getProviderBadgeClass(key.serviceCode)">{{ key.serviceCode }}</span>
                    <!-- 만료 상태 배지 -->
                    <span v-if="key.expiresAt && isExpired(key.expiresAt)" class="badge bg-danger-subtle text-danger">
                      {{ t('apiKeys.provider.list.expiredAlready') }}
                    </span>
                    <span v-else-if="key.expiresAt && isExpiringSoon(key.expiresAt)" class="badge bg-warning-subtle text-warning">
                      {{ t('apiKeys.provider.list.expiresIn', { days: daysUntilExpiry(key.expiresAt) ?? 0 }) }}
                    </span>
                    <!-- 활성 상태 -->
                    <span class="badge" :class="key.isActive ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary'">
                      <i class="bi" :class="key.isActive ? 'bi-circle-fill' : 'bi-circle'"></i>
                      {{ key.isActive ? '활성' : '비활성' }}
                    </span>
                  </div>
                </div>

                <!-- 설명 -->
                <p v-if="key.description" class="ak-key-desc">{{ key.description }}</p>

                <!-- 메타 정보 -->
                <div class="ak-key-meta">
                  <span v-if="key.lastUsedAt">
                    <i class="bi bi-clock-history"></i>
                    {{ t('apiKeys.provider.list.lastUsed', { time: formatDate(key.lastUsedAt) }) }}
                  </span>
                  <span v-else>
                    <i class="bi bi-clock-history"></i>
                    {{ t('apiKeys.provider.list.neverUsed') }}
                  </span>
                  <span>
                    <i class="bi bi-calendar-plus"></i>
                    {{ formatDate(key.createdAt) }} 등록
                  </span>
                  <span v-if="key.expiresAt"
                    :class="isExpired(key.expiresAt) ? 'text-danger' : (isExpiringSoon(key.expiresAt) ? 'text-warning' : '')">
                    <i class="bi bi-calendar-x"></i>
                    {{ formatDate(key.expiresAt) }} 만료
                  </span>
                </div>

                <!-- 액션 버튼 -->
                <div class="ak-key-actions">
                  <button class="btn btn-sm btn-outline-primary"
                    @click="testProviderKey(key)"
                    :disabled="testingKeys[key.apiKeyId] || !key.isActive">
                    <span v-if="testingKeys[key.apiKeyId]" class="spinner-border spinner-border-sm me-1"></span>
                    <i v-else class="bi bi-lightning-charge me-1"></i>
                    {{ t('apiKeys.provider.list.test') }}
                  </button>
                  <button class="btn btn-sm btn-outline-secondary" @click="editKey(key)" :disabled="!key.isActive">
                    <i class="bi bi-pencil me-1"></i>{{ t('apiKeys.provider.list.edit') }}
                  </button>
                  <button class="btn btn-sm btn-outline-danger" @click="deleteProviderKey(key)">
                    <i class="bi bi-trash me-1"></i>{{ t('apiKeys.provider.list.delete') }}
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- 우측: 풀 통계 카드 -->
      <div class="col-lg-4 d-flex flex-column gap-4">
        <div class="card aiuiux-card">
          <div class="card-header bg-transparent border-bottom d-flex align-items-center justify-content-between">
            <div>
              <h5 class="card-title mb-0">
                <i class="bi bi-bar-chart-line me-2 text-primary"></i>{{ t('apiKeys.provider.stats.title') }}
              </h5>
              <p class="card-subtitle mb-0 mt-1">{{ t('apiKeys.provider.stats.subtitle') }}</p>
            </div>
            <button class="btn btn-sm btn-outline-secondary" @click="loadPoolStats" :disabled="loadingPoolStats" :title="t('apiKeys.provider.stats.refresh')">
              <span v-if="loadingPoolStats" class="spinner-border spinner-border-sm"></span>
              <i v-else class="bi bi-arrow-clockwise"></i>
            </button>
          </div>
          <div class="card-body">
            <!-- 통계 행 — 백엔드에서 받은 프로바이더 목록 -->
            <div v-if="!poolStats || poolStats.providers.length === 0" class="text-center py-3">
              <i class="bi bi-info-circle text-muted"></i>
              <p class="small text-muted mb-0 mt-2">{{ t('apiKeys.provider.stats.noProviders') }}</p>
            </div>
            <template v-else>
              <div v-for="p in poolStats.providers" :key="p.serviceCode" class="ak-pool-row">
                <div class="ak-pool-head">
                  <span class="badge" :class="getProviderBadgeClass(p.serviceCode)">{{ p.serviceCode }}</span>
                  <span class="ak-pool-total ms-auto">
                    {{ t('apiKeys.provider.stats.totalLabel') }} <strong>{{ p.totalCount }}</strong>
                  </span>
                </div>
                <div class="ak-pool-detail">
                  <span :class="p.fromDb > 0 ? 'text-primary' : 'text-muted'">
                    {{ t('apiKeys.provider.stats.fromDb') }} {{ p.fromDb }}
                  </span>
                  <span class="ak-pool-sep">·</span>
                  <span :class="p.fromAppsettings > 0 ? 'text-info' : 'text-muted'">
                    {{ t('apiKeys.provider.stats.fromAppsettings') }} {{ p.fromAppsettings }}
                  </span>
                  <span class="ak-pool-sep">·</span>
                  <span :class="p.coolingDownCount > 0 ? 'text-warning' : 'text-muted'">
                    {{ t('apiKeys.provider.stats.coolingDown') }} {{ p.coolingDownCount }}
                  </span>
                </div>
              </div>
            </template>
            <!-- 마지막 갱신 시각 -->
            <div v-if="poolStats?.lastRefreshedAt" class="ak-pool-footer">
              <i class="bi bi-clock"></i>
              {{ t('apiKeys.provider.stats.lastRefreshedAt', { time: formatRefreshTime(poolStats.lastRefreshedAt) }) }}
            </div>
          </div>
        </div>

        <!-- 운영자 안내 -->
        <div class="card aiuiux-card border-info-subtle">
          <div class="card-header bg-info-subtle border-bottom border-info-subtle">
            <h5 class="card-title mb-0 text-info">
              <i class="bi bi-info-circle me-2"></i>운영자 안내
            </h5>
          </div>
          <div class="card-body">
            <ul class="ak-security-list">
              <li><i class="bi bi-arrow-repeat text-primary"></i>등록/삭제 시 풀에 즉시 반영됩니다</li>
              <li><i class="bi bi-shield-check text-success"></i>키는 AES-GCM 으로 암호화 저장됩니다</li>
              <li><i class="bi bi-lightning-charge text-warning"></i>[테스트] 버튼으로 제공사 ping 검증 가능</li>
              <li><i class="bi bi-stopwatch text-info"></i>Hangfire 5분 주기로 자동 동기화됩니다</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════════════════════════
         모달: 외부 LLM 키 등록 (탭 3 전용)
    ════════════════════════════════════════ -->
    <div class="modal fade" :class="{ show: showProviderModal, 'd-block': showProviderModal }" tabindex="-1" v-if="showProviderModal">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-shield-lock me-2 text-primary"></i>{{ t('apiKeys.provider.modal.title') }}
            </h5>
            <button type="button" class="btn-close" @click="closeProviderModal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitProviderKey">
              <div class="mb-3">
                <label class="form-label fw-medium">
                  {{ t('apiKeys.provider.modal.keyName') }} <span class="text-danger">*</span>
                </label>
                <input type="text" class="form-control" v-model="providerForm.keyName"
                  :placeholder="t('apiKeys.provider.modal.keyNamePlaceholder')"
                  required maxlength="100">
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">
                  {{ t('apiKeys.provider.modal.serviceCode') }} <span class="text-danger">*</span>
                </label>
                <select class="form-select" v-model="providerForm.serviceCode" required>
                  <option value="">{{ t('apiKeys.provider.modal.selectProvider') }}</option>
                  <option value="openai">OpenAI / ChatGPT</option>
                  <option value="claude">Anthropic Claude</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="gemini-image">Google Gemini Image</option>
                  <option value="imagen4">Google Imagen 4</option>
                  <option value="perplexity">Perplexity</option>
                  <option value="mistral">Mistral</option>
                  <option value="azureopenai">Azure OpenAI</option>
                  <option value="copilot">GitHub Copilot</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">
                  {{ t('apiKeys.provider.modal.apiKey') }} <span class="text-danger">*</span>
                </label>
                <input type="password" class="form-control font-monospace"
                  v-model="providerForm.apiKey"
                  required minlength="10" autocomplete="off" spellcheck="false"
                  placeholder="sk-... / AIza... / ...">
                <div class="form-text">
                  <i class="bi bi-lock me-1"></i>{{ t('apiKeys.provider.modal.apiKeyHint') }}
                </div>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">
                  {{ t('apiKeys.provider.modal.description') }}
                  <span class="text-muted fw-normal">({{ t('common.optional') }})</span>
                </label>
                <textarea class="form-control" rows="2" maxlength="500"
                  v-model="providerForm.description" placeholder="이 키의 용도를 설명하세요"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">
                  {{ t('apiKeys.provider.modal.expiresAt') }}
                  <span class="text-muted fw-normal">({{ t('common.optional') }})</span>
                </label>
                <input type="date" class="form-control" v-model="providerForm.expiresAt">
              </div>
              <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox"
                  v-model="providerForm.validateOnCreate" id="validateOnCreate">
                <label class="form-check-label" for="validateOnCreate">
                  <i class="bi bi-lightning-charge text-warning me-1"></i>
                  {{ t('apiKeys.provider.modal.validateOnCreate') }}
                </label>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="closeProviderModal">
              {{ $t('common.cancel') }}
            </button>
            <button type="button" class="btn btn-primary"
              :disabled="submittingProvider" @click="submitProviderKey">
              <span v-if="submittingProvider" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-check-lg me-1"></i>
              {{ t('apiKeys.provider.modal.submit') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showProviderModal }" v-if="showProviderModal" @click="closeProviderModal"></div>

    <!-- ════════════════════════════════════════
         모달: 서비스 API 키 추가
    ════════════════════════════════════════ -->
    <div class="modal fade" :class="{ show: showAddModal, 'd-block': showAddModal }" tabindex="-1" v-if="showAddModal">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-plus-circle me-2 text-primary"></i>새 API 키 추가</h5>
            <button type="button" class="btn-close" @click="showAddModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleAddKey">
              <div class="mb-3">
                <label class="form-label fw-medium">키 이름 (별칭) <span class="text-danger">*</span></label>
                <input type="text" class="form-control" v-model="newKey.keyName" placeholder="예: 프로덕션용 OpenAI" required>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">서비스 <span class="text-danger">*</span></label>
                <select class="form-select" v-model="newKey.serviceCode" required>
                  <option value="">선택하세요</option>
                  <option value="chatgpt">OpenAI (ChatGPT)</option>
                  <option value="claude">Anthropic (Claude)</option>
                  <option value="gemini">Google AI (Gemini)</option>
                  <option value="perplexity">Perplexity</option>
                  <option value="tavily">Tavily</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">API 키 <span class="text-danger">*</span></label>
                <input type="password" class="form-control font-monospace" v-model="newKey.apiKey" placeholder="sk-..." required autocomplete="off">
                <div class="form-text"><i class="bi bi-lock me-1"></i>키는 AES-256으로 암호화되어 안전하게 저장됩니다.</div>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">설명 <span class="text-muted fw-normal">(선택)</span></label>
                <textarea class="form-control" rows="2" v-model="newKey.description" placeholder="이 키의 용도를 설명하세요"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">만료일 <span class="text-muted fw-normal">(선택)</span></label>
                <input type="date" class="form-control" v-model="newKey.expiresAt">
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="showAddModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleAddKey">
              <i class="bi bi-check-lg me-1"></i>추가
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showAddModal }" v-if="showAddModal" @click="showAddModal = false"></div>

    <!-- ════════════════════════════════════════
         모달: 서비스 API 키 수정
    ════════════════════════════════════════ -->
    <div class="modal fade" :class="{ show: showEditModal, 'd-block': showEditModal }" tabindex="-1" v-if="showEditModal">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-pencil me-2 text-warning"></i>API 키 수정</h5>
            <button type="button" class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="handleUpdateKey">
              <div class="mb-3">
                <label class="form-label fw-medium">키 이름</label>
                <input type="text" class="form-control" v-model="editingKey.keyName" required>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">설명</label>
                <textarea class="form-control" rows="2" v-model="editingKey.description"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">만료일</label>
                <input type="date" class="form-control" v-model="editingKey.expiresAt">
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="showEditModal = false">취소</button>
            <button type="button" class="btn btn-primary" @click="handleUpdateKey">
              <i class="bi bi-check-lg me-1"></i>저장
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showEditModal }" v-if="showEditModal" @click="showEditModal = false"></div>

    <!-- ════════════════════════════════════════
         모달: Agent API 키 발급
    ════════════════════════════════════════ -->
    <div class="modal fade" :class="{ show: showAgentKeyModal, 'd-block': showAgentKeyModal }" tabindex="-1" v-if="showAgentKeyModal">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header">
            <h5 class="modal-title"><i class="bi bi-robot me-2 text-primary"></i>Agent API 키 발급</h5>
            <button type="button" class="btn-close" @click="closeAgentKeyModal"></button>
          </div>
          <div class="modal-body">
            <div v-if="!selectedAgentId" class="alert alert-warning d-flex align-items-center gap-2 mb-0">
              <i class="bi bi-exclamation-triangle"></i>
              <span>상단에서 Agent를 먼저 선택해주세요.</span>
            </div>
            <template v-else>
              <div class="mb-3">
                <label class="form-label fw-medium">선택된 Agent</label>
                <div class="p-3 rounded-3 border bg-primary-subtle">
                  <i class="bi bi-robot me-2 text-primary"></i>
                  <strong class="text-primary">{{ selectedAgentName }}</strong>
                </div>
                <div class="form-text">이 Agent를 외부에서 호출할 수 있는 키가 발급됩니다.</div>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">키 이름 <span class="text-muted fw-normal">(선택)</span></label>
                <input type="text" class="form-control" v-model="agentKeyForm.keyName" placeholder="예: 개발용, 프로덕션용">
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">설명 <span class="text-muted fw-normal">(선택)</span></label>
                <textarea class="form-control" rows="2" v-model="agentKeyForm.description" placeholder="용도를 간략히 설명하세요"></textarea>
              </div>
              <div class="mb-3">
                <label class="form-label fw-medium">만료일 <span class="text-muted fw-normal">(선택)</span></label>
                <input type="date" class="form-control" v-model="agentKeyForm.expiresAt">
              </div>

              <!-- 보안 확장 설정 (접기/펼치기) -->
              <div class="ak-advanced-toggle" @click="showAdvanced = !showAdvanced">
                <i class="bi" :class="showAdvanced ? 'bi-chevron-up' : 'bi-chevron-down'"></i>
                <span>고급 보안 설정</span>
                <span class="ak-advanced-badge" v-if="agentKeyForm.allowedIps || agentKeyForm.scopes || agentKeyForm.rateLimitPerMinute || agentKeyForm.rateLimitPerDay">
                  설정됨
                </span>
              </div>

              <div v-show="showAdvanced" class="ak-advanced-body">
                <div class="mb-3">
                  <label class="form-label fw-medium">
                    <i class="bi bi-shield-lock text-success me-1"></i>
                    허용 IP 목록 <span class="text-muted fw-normal">(선택)</span>
                  </label>
                  <input type="text" class="form-control" v-model="agentKeyForm.allowedIps"
                    placeholder="예: 192.168.1.100,10.0.0.1">
                  <div class="form-text">쉼표로 구분. 비워두면 모든 IP 허용.</div>
                </div>
                <div class="mb-3">
                  <label class="form-label fw-medium">
                    <i class="bi bi-toggles text-primary me-1"></i>
                    허용 스코프 <span class="text-muted fw-normal">(선택)</span>
                  </label>
                  <div class="d-flex flex-wrap gap-2 mt-1">
                    <div v-for="scope in availableScopes" :key="scope.value" class="form-check form-check-inline m-0">
                      <input class="form-check-input" type="checkbox" :id="'scope-' + scope.value"
                        :value="scope.value" v-model="agentKeyForm.selectedScopes">
                      <label class="form-check-label small" :for="'scope-' + scope.value">{{ scope.label }}</label>
                    </div>
                  </div>
                  <div class="form-text">선택하지 않으면 모든 스코프 허용 (*).</div>
                </div>
                <div class="row g-2">
                  <div class="col-6">
                    <label class="form-label fw-medium">
                      <i class="bi bi-speedometer2 text-warning me-1"></i>
                      분당 요청 제한
                    </label>
                    <input type="number" class="form-control" v-model.number="agentKeyForm.rateLimitPerMinute"
                      min="0" placeholder="무제한">
                    <div class="form-text">0 또는 빈값 = 무제한</div>
                  </div>
                  <div class="col-6">
                    <label class="form-label fw-medium">
                      <i class="bi bi-calendar-day text-info me-1"></i>
                      일당 요청 제한
                    </label>
                    <input type="number" class="form-control" v-model.number="agentKeyForm.rateLimitPerDay"
                      min="0" placeholder="무제한">
                    <div class="form-text">0 또는 빈값 = 무제한</div>
                  </div>
                </div>
              </div>

            </template>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="closeAgentKeyModal">취소</button>
            <button type="button" class="btn btn-primary" :disabled="!selectedAgentId || creatingAgentKey" @click="createAgentApiKey">
              <span v-if="creatingAgentKey" class="spinner-border spinner-border-sm me-1"></span>
              <i v-else class="bi bi-plus-circle me-1"></i>발급
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: showAgentKeyModal }" v-if="showAgentKeyModal" @click="closeAgentKeyModal"></div>

    <!-- ════════════════════════════════════════
         모달: Agent API 키 발급 완료 (한 번만 표시)
    ════════════════════════════════════════ -->
    <div class="modal fade" :class="{ show: !!createdAgentKey, 'd-block': !!createdAgentKey }" tabindex="-1" v-if="createdAgentKey">
      <div class="modal-dialog">
        <div class="modal-content aiuiux-modal">
          <div class="modal-header" style="background: linear-gradient(135deg, #198754, #20c997); color: #fff;">
            <h5 class="modal-title"><i class="bi bi-check-circle-fill me-2"></i>API 키 발급 완료!</h5>
            <button type="button" class="btn-close btn-close-white" @click="createdAgentKey = null"></button>
          </div>
          <div class="modal-body">
            <div class="alert alert-warning d-flex gap-2">
              <i class="bi bi-exclamation-triangle-fill flex-shrink-0 mt-1"></i>
              <div>{{ createdAgentKey.warning }}</div>
            </div>
            <div class="mb-3">
              <label class="form-label fw-medium">발급된 API 키</label>
              <div class="input-group">
                <input type="text" class="form-control font-monospace" :value="createdAgentKey.apiKey" readonly :id="'created-key-' + createdAgentKey.apiKeyId">
                <button class="btn btn-outline-primary" type="button" @click="copyCreatedKey">
                  <i class="bi" :class="createdKeyCopied ? 'bi-check2' : 'bi-clipboard'"></i>
                  {{ createdKeyCopied ? '복사됨!' : '복사' }}
                </button>
              </div>
              <div class="form-text">이 키는 지금만 확인할 수 있습니다. 반드시 안전한 곳에 저장하세요.</div>
            </div>
            <div class="ak-code-block">
              <span class="small text-muted">사용 예시</span>
              <code class="d-block mt-1 small">X-API-Key: {{ createdAgentKey.apiKey }}</code>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" @click="createdAgentKey = null; createdKeyCopied = false; loadAgentApiKeys()">
              <i class="bi bi-check-lg me-1"></i>확인
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade" :class="{ show: !!createdAgentKey }" v-if="createdAgentKey" @click="createdAgentKey = null; createdKeyCopied = false"></div>

    <!-- ── 토스트 알림 ── -->
    <div class="ak-toast" :class="['ak-toast--' + toastType, { 'ak-toast--show': showToast }]">
      <i class="bi" :class="toastType === 'success' ? 'bi-check-circle-fill' : toastType === 'error' ? 'bi-x-circle-fill' : 'bi-info-circle-fill'"></i>
      <span>{{ toastMessage }}</span>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/services/api'
import { apiKeyService } from '@/services/apiKeyService'
import { useAuthStore } from '@/stores/auth'
import type {
  ApiKeyDto,
  CreateApiKeyRequestDto,
  UpdateApiKeyRequestDto,
  CreateAgentApiKeyRequestDto,
  CreateAgentApiKeyResponseDto,
  AgentDto,
  CreateProviderApiKeyRequestDto,
  PoolStatsResponseDto,
  ProviderPoolStatDto
} from '@/types'

// 트랙 #91 (2026-05-13): i18n 사용 — 신규 탭 3 (외부 LLM 키 풀) 의 한국어/영어 라벨 동기화.
// 기존 탭 1/2 의 한국어 하드코딩은 회귀 위험을 피하기 위해 그대로 유지한다.
const { t, locale } = useI18n()

// 관리자 가드 (Dashboard.vue 의 isAdmin 패턴 동일).
const authStore = useAuthStore()
const isAdmin = computed<boolean>(() => {
  const roles = authStore.user?.roles ?? []
  return roles.includes('Admin') || roles.includes('SuperAdmin')
})

// ─── 상태 ──────────────────────────────────────────────
// 트랙 #91 (2026-05-13): 'provider-pool' 추가 — 운영자(Admin/SuperAdmin) 전용 외부 LLM 키 풀 탭.
const activeTab = ref<'service' | 'agent' | 'provider-pool'>('service')
const loading = ref(false)
const apiKeys = ref<ApiKeyDto[]>([])
const revealedKeys = ref<Record<number, string>>({})
const copiedKeyId = ref<number | null>(null)
const showAddModal = ref(false)
const showEditModal = ref(false)
const editingKey = ref<Partial<ApiKeyDto & { expiresAt?: string }>>({})

const newKey = ref<CreateApiKeyRequestDto & { expiresAt?: string }>({
  keyName: '', serviceCode: '', apiKey: '', description: '', expiresAt: undefined
})

const myAgents = ref<AgentDto[]>([])
const selectedAgentId = ref<number | null>(null)
const agentApiKeys = ref<ApiKeyDto[]>([])
const loadingAgentKeys = ref(false)
const showAgentKeyModal = ref(false)
const creatingAgentKey = ref(false)
const createdAgentKey = ref<CreateAgentApiKeyResponseDto | null>(null)
const createdKeyCopied = ref(false)
// Phase 3 vue-tsc 2.x 부채 정리 — null 사용을 undefined 로 좁혀서 DTO 와 정렬
// (CreateAgentApiKeyRequestDto 의 rateLimit* 가 number | undefined 이므로 null 이 거부됨)
const agentKeyForm = ref<CreateAgentApiKeyRequestDto & {
  expiresAt?: string
  allowedIps?: string
  selectedScopes: string[]
  rateLimitPerMinute?: number
  rateLimitPerDay?: number
}>({
  keyName: '', description: '', expiresAt: undefined,
  allowedIps: '', selectedScopes: [], rateLimitPerMinute: undefined, rateLimitPerDay: undefined
})

// 고급 보안 설정 패널 토글
const showAdvanced = ref(false)

// 지원 스코프 목록
const availableScopes = [
  { value: 'chat',   label: '채팅 (chat)' },
  { value: 'stream', label: '스트리밍 (stream)' },
  { value: 'info',   label: 'Agent 정보 (info)' },
  { value: 'usage',  label: '사용량 조회 (usage)' }
]

// Toast
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'info'>('success')
let toastTimer: ReturnType<typeof setTimeout> | null = null

// Base URL (현재 도메인 기반)
const baseUrl = computed(() => window.location.origin)

// ─── 계산 속성 ──────────────────────────────────────────
const activeKeysCount = computed(() => apiKeys.value.filter(k => k.isActive).length)
const inactiveKeysCount = computed(() => apiKeys.value.filter(k => !k.isActive).length)
const expiredKeysCount = computed(() => apiKeys.value.filter(k => k.expiresAt && isExpired(k.expiresAt)).length)

const selectedAgentName = computed(() => {
  if (!selectedAgentId.value) return ''
  return myAgents.value.find(a => a.agentId === selectedAgentId.value)?.agentName || ''
})

// ─── 트랙 #91 — 외부 LLM 키 풀 (탭 3) 상태 ────────────────────────────────
// KeyType='Provider' 키 목록 (좌측 카드)
const providerKeys = ref<ApiKeyDto[]>([])
// 풀 통계 응답 (우측 카드) — 백엔드 RefreshAsync 의 in-memory 스냅샷
const poolStats = ref<PoolStatsResponseDto | null>(null)
// 등록 모달 표시 여부
const showProviderModal = ref(false)
// 등록 폼 (reactive 로 두 way 바인딩)
const providerForm = reactive<CreateProviderApiKeyRequestDto>({
  keyName: '',
  serviceCode: '',
  apiKey: '',
  description: '',
  expiresAt: '',
  validateOnCreate: true
})
// 폼 제출 중 spinner 표시용
const submittingProvider = ref(false)
// 풀 통계 로딩 중 표시용
const loadingPoolStats = ref(false)
// 키별 [테스트] 버튼 진행 상태 (apiKeyId -> boolean)
const testingKeys = reactive<Record<number, boolean>>({})

// ─── 수명주기 ───────────────────────────────────────────
onMounted(() => {
  loadApiKeys()
  loadAgents()
})

// ─── 토스트 ─────────────────────────────────────────────
const toast = (message: string, type: 'success' | 'error' | 'info' = 'success', duration = 3000) => {
  if (toastTimer) clearTimeout(toastTimer)
  toastMessage.value = message
  toastType.value = type
  showToast.value = true
  toastTimer = setTimeout(() => { showToast.value = false }, duration)
}

// ─── 서비스 API 키 CRUD ─────────────────────────────────
const loadApiKeys = async () => {
  loading.value = true
  try {
    const response = await api.get('/apikeys')
    apiKeys.value = response.data
  } catch (error: any) {
    console.error('API 키 목록 로드 실패:', error)
    toast('API 키 목록을 불러오는데 실패했습니다.', 'error')
  } finally {
    loading.value = false
  }
}

const handleAddKey = async () => {
  try {
    const request: CreateApiKeyRequestDto = {
      keyName: newKey.value.keyName,
      serviceCode: newKey.value.serviceCode,
      apiKey: newKey.value.apiKey,
      description: newKey.value.description || undefined,
      expiresAt: newKey.value.expiresAt ? new Date(newKey.value.expiresAt) : undefined
    }
    await api.post('/apikeys', request)
    showAddModal.value = false
    newKey.value = { keyName: '', serviceCode: '', apiKey: '', description: '', expiresAt: undefined }
    await loadApiKeys()
    toast('API 키가 추가되었습니다.')
  } catch (error: any) {
    console.error('API 키 추가 실패:', error)
    toast(error.response?.data?.message || 'API 키 추가에 실패했습니다.', 'error')
  }
}

const editKey = (key: ApiKeyDto) => {
  editingKey.value = {
    ...key,
    expiresAt: key.expiresAt ? new Date(key.expiresAt).toISOString().split('T')[0] : undefined
  }
  showEditModal.value = true
}

const handleUpdateKey = async () => {
  if (!editingKey.value.apiKeyId) return
  try {
    const request: UpdateApiKeyRequestDto = {
      keyName: editingKey.value.keyName,
      description: editingKey.value.description,
      expiresAt: editingKey.value.expiresAt ? new Date(editingKey.value.expiresAt) : undefined
    }
    await api.put(`/apikeys/${editingKey.value.apiKeyId}`, request)
    showEditModal.value = false
    await loadApiKeys()
    toast('API 키가 수정되었습니다.')
  } catch (error: any) {
    console.error('API 키 수정 실패:', error)
    toast(error.response?.data?.message || 'API 키 수정에 실패했습니다.', 'error')
  }
}

const toggleActive = async (key: ApiKeyDto) => {
  try {
    await api.put(`/apikeys/${key.apiKeyId}`, { isActive: !key.isActive } as UpdateApiKeyRequestDto)
    await loadApiKeys()
    toast(key.isActive ? 'API 키가 비활성화되었습니다.' : 'API 키가 활성화되었습니다.', 'info')
  } catch (error: any) {
    toast(error.response?.data?.message || 'API 키 상태 변경에 실패했습니다.', 'error')
  }
}

const deleteKey = async (key: ApiKeyDto) => {
  if (!confirm(`"${key.keyName}" API 키를 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return
  try {
    await api.delete(`/apikeys/${key.apiKeyId}`)
    await loadApiKeys()
    toast('API 키가 삭제되었습니다.')
  } catch (error: any) {
    toast(error.response?.data?.message || 'API 키 삭제에 실패했습니다.', 'error')
  }
}

// ─── Agent API 키 ────────────────────────────────────────
const loadAgents = async () => {
  try {
    const res = await api.get<AgentDto[]>('/agents')
    myAgents.value = (res.data || []).filter((a: AgentDto) => a.isActive)
  } catch (e: any) {
    console.error('Agent 목록 로드 실패:', e)
    myAgents.value = []
  }
}

const switchToAgentTab = () => {
  activeTab.value = 'agent'
  loadAgents().then(() => loadAgentApiKeys())
}

const onAgentSelect = () => {
  agentApiKeys.value = []
  if (selectedAgentId.value) {
    loadAgentApiKeys()
  }
}

const loadAgentApiKeys = async () => {
  if (!selectedAgentId.value) { agentApiKeys.value = []; return }
  loadingAgentKeys.value = true
  try {
    const res = await api.get<ApiKeyDto[]>(`/agents/${selectedAgentId.value}/api-keys`)
    agentApiKeys.value = res.data ?? []
  } catch (e: any) {
    console.error('Agent API 키 목록 로드 실패:', e)
    agentApiKeys.value = []
  } finally {
    loadingAgentKeys.value = false
  }
}

const openAgentKeyModal = () => {
  if (!selectedAgentId.value) {
    toast('먼저 Agent를 선택해주세요.', 'info')
    return
  }
  // Phase 3 vue-tsc 2.x 부채 정리 — selectedScopes 빈 배열 default 추가 (TS2322 해소)
  agentKeyForm.value = {
    keyName: '', description: '', expiresAt: undefined,
    allowedIps: '', selectedScopes: [], rateLimitPerMinute: undefined, rateLimitPerDay: undefined
  }
  showAgentKeyModal.value = true
}

const closeAgentKeyModal = () => {
  showAgentKeyModal.value = false
  showAdvanced.value = false
  agentKeyForm.value = {
    keyName: '', description: '', expiresAt: undefined,
    allowedIps: '', selectedScopes: [], rateLimitPerMinute: undefined, rateLimitPerDay: undefined
  }
}

const createAgentApiKey = async () => {
  if (!selectedAgentId.value) return
  creatingAgentKey.value = true
  try {
    const scopesStr = agentKeyForm.value.selectedScopes?.length
      ? agentKeyForm.value.selectedScopes.join(',')
      : undefined

    const payload: CreateAgentApiKeyRequestDto = {
      keyName:           agentKeyForm.value.keyName || undefined,
      description:       agentKeyForm.value.description || undefined,
      expiresAt:         agentKeyForm.value.expiresAt ? new Date(agentKeyForm.value.expiresAt) : undefined,
      allowedIps:        agentKeyForm.value.allowedIps || undefined,
      scopes:            scopesStr,
      rateLimitPerMinute: agentKeyForm.value.rateLimitPerMinute || undefined,
      rateLimitPerDay:   agentKeyForm.value.rateLimitPerDay || undefined
    }
    const res = await api.post<CreateAgentApiKeyResponseDto>(`/agents/${selectedAgentId.value}/api-keys`, payload)
    createdAgentKey.value = res.data
    closeAgentKeyModal()
    await loadAgentApiKeys()
  } catch (e: any) {
    console.error('Agent API 키 발급 실패:', e)
    toast(e.response?.data?.message ?? 'Agent API 키 발급에 실패했습니다.', 'error')
  } finally {
    creatingAgentKey.value = false
  }
}

const deleteAgentApiKey = async (key: ApiKeyDto) => {
  if (!selectedAgentId.value) return
  if (!confirm(`"${key.keyName || '이 키'}" API 키를 삭제하시겠습니까?`)) return
  try {
    await api.delete(`/agents/${selectedAgentId.value}/api-keys/${key.apiKeyId}`)
    await loadAgentApiKeys()
    toast('API 키가 삭제되었습니다.')
  } catch (e: any) {
    toast(e.response?.data?.message ?? 'API 키 삭제에 실패했습니다.', 'error')
  }
}

// ─── 클립보드 ────────────────────────────────────────────
const copyCreatedKey = async () => {
  if (!createdAgentKey.value) return
  try {
    await navigator.clipboard.writeText(createdAgentKey.value.apiKey)
    createdKeyCopied.value = true
    setTimeout(() => { createdKeyCopied.value = false }, 2000)
  } catch {
    const el = document.getElementById(`created-key-${createdAgentKey.value.apiKeyId}`) as HTMLInputElement
    el?.select(); document.execCommand('copy')
  }
}

const copyAgentKey = async (key: ApiKeyDto) => {
  try {
    await navigator.clipboard.writeText(key.maskedKey || '')
    showCopiedFeedback(key.apiKeyId)
  } catch { /* ignore */ }
}

const copyToClipboard = async (apiKeyId: number, text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    showCopiedFeedback(apiKeyId)
  } catch {
    const input = document.getElementById(`key-input-${apiKeyId}`) as HTMLInputElement
    input?.select(); document.execCommand('copy')
    showCopiedFeedback(apiKeyId)
  }
}

const copyText = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    toast('클립보드에 복사되었습니다.', 'success', 1500)
  } catch { /* ignore */ }
}

const showCopiedFeedback = (keyId: number) => {
  copiedKeyId.value = keyId
  setTimeout(() => { copiedKeyId.value = null }, 2000)
}

// ─── API 키 표시/숨김 ────────────────────────────────────
const toggleReveal = async (apiKeyId: number) => {
  if (revealedKeys.value[apiKeyId]) {
    const updated = { ...revealedKeys.value }
    delete updated[apiKeyId]
    revealedKeys.value = updated
    return
  }
  try {
    const response = await api.post(`/apikeys/${apiKeyId}/reveal`)
    revealedKeys.value = { ...revealedKeys.value, [apiKeyId]: response.data.key }
  } catch (error: any) {
    toast(error.response?.data?.message || 'API 키를 조회하는데 실패했습니다.', 'error')
  }
}

// ─── 유틸 ────────────────────────────────────────────────
const getServiceIcon = (serviceCode: string) => {
  const icons: Record<string, string> = {
    chatgpt:    'bi-chat-square-text-fill text-info',
    claude:     'bi-robot text-primary',
    gemini:     'bi-stars text-success',
    perplexity: 'bi-search text-warning',
    tavily:     'bi-globe2 text-info'
  }
  return icons[serviceCode] || 'bi-key-fill text-secondary'
}

const formatDate = (date: string | Date | null | undefined) => {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' })
}

const isExpired = (expiresAt: string | Date | null | undefined) => {
  if (!expiresAt) return false
  return new Date(expiresAt) < new Date()
}

const isExpiringSoon = (expiresAt: string | Date | null | undefined) => {
  if (!expiresAt) return false
  const exp = new Date(expiresAt)
  const soon = new Date()
  soon.setDate(soon.getDate() + 7)
  return exp > new Date() && exp < soon
}

// ─── 트랙 #91 — 외부 LLM 키 풀 (탭 3) 핸들러 ─────────────────────────
/**
 * 만료까지 남은 일수. 만료된 키는 0 미만, 무기한 키는 null.
 * 운영자 콘솔에서 "만료 D-N" 표시에 사용.
 */
const daysUntilExpiry = (expiresAt: string | Date | null | undefined): number | null => {
  if (!expiresAt) return null
  const exp = new Date(expiresAt).getTime()
  const now = Date.now()
  return Math.ceil((exp - now) / (24 * 60 * 60 * 1000))
}

/**
 * 프로바이더 코드 → Bootstrap badge 색상 매핑.
 * 운영자가 한눈에 프로바이더를 구분할 수 있도록 색상으로 구분.
 */
const getProviderBadgeClass = (serviceCode: string): string => {
  const palette: Record<string, string> = {
    gemini: 'bg-success-subtle text-success',
    'gemini-image': 'bg-success-subtle text-success',
    imagen4: 'bg-success-subtle text-success',
    openai: 'bg-primary-subtle text-primary',
    chatgpt: 'bg-primary-subtle text-primary',
    claude: 'bg-warning-subtle text-warning',
    perplexity: 'bg-info-subtle text-info',
    mistral: 'bg-danger-subtle text-danger',
    azureopenai: 'bg-primary-subtle text-primary',
    copilot: 'bg-secondary-subtle text-secondary'
  }
  return palette[serviceCode] || 'bg-secondary-subtle text-secondary'
}

/**
 * lastRefreshedAt(ISO 8601 UTC) → "2026-05-13 19:34:21 UTC" 한국어 친화 표기.
 * 시간대를 명시해 운영자가 컨테이너 시계와 비교할 수 있게 함.
 */
const formatRefreshTime = (iso: string): string => {
  const d = new Date(iso)
  const y = d.getUTCFullYear()
  const m = String(d.getUTCMonth() + 1).padStart(2, '0')
  const day = String(d.getUTCDate()).padStart(2, '0')
  const h = String(d.getUTCHours()).padStart(2, '0')
  const min = String(d.getUTCMinutes()).padStart(2, '0')
  const s = String(d.getUTCSeconds()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}:${s} UTC`
}

/** 외부 LLM 키 목록 로드 — KeyType='Provider' 필터링은 도메인 래퍼가 담당. */
const loadProviderKeys = async () => {
  try {
    providerKeys.value = await apiKeyService.listProviderKeys()
  } catch (e: any) {
    console.error('외부 LLM 키 목록 로드 실패:', e)
    toast(e.response?.data?.message ?? 'API 키 목록을 불러오는데 실패했습니다.', 'error')
  }
}

/** 풀 통계 로드 — 백엔드 in-memory 스냅샷이므로 빠른 응답. */
const loadPoolStats = async () => {
  loadingPoolStats.value = true
  try {
    poolStats.value = await apiKeyService.getPoolStats()
  } catch (e: any) {
    console.error('풀 통계 로드 실패:', e)
    toast(e.response?.data?.message ?? '풀 통계를 불러오는데 실패했습니다.', 'error')
  } finally {
    loadingPoolStats.value = false
  }
}

/** 등록 모달 열기 — 폼 초기화. */
const openProviderModal = () => {
  providerForm.keyName = ''
  providerForm.serviceCode = ''
  providerForm.apiKey = ''
  providerForm.description = ''
  providerForm.expiresAt = ''
  providerForm.validateOnCreate = true
  showProviderModal.value = true
}

/** 등록 모달 닫기 — 평문 키를 메모리에서 즉시 폐기. */
const closeProviderModal = () => {
  // 평문 키 메모리 보존 시간 최소화 — 모달 닫는 즉시 폐기.
  providerForm.apiKey = ''
  showProviderModal.value = false
}

/**
 * 등록 폼 제출 핸들러.
 * - validateOnCreate=true 이면 백엔드가 등록 직후 ping → 실패 시 등록 거부.
 * - 등록 성공 → 풀 즉시 트리거 → 목록 + 통계 재로드.
 * - apiKey 평문은 응답 후 즉시 메모리 폐기.
 */
const submitProviderKey = async () => {
  // 클라이언트 사이드 가벼운 검증 (백엔드도 다시 검증함).
  if (!providerForm.keyName || !providerForm.serviceCode || !providerForm.apiKey) {
    toast('필수 항목을 모두 입력해주세요.', 'error')
    return
  }
  if (providerForm.apiKey.length < 10) {
    toast('API 키는 10자 이상이어야 합니다.', 'error')
    return
  }

  submittingProvider.value = true
  try {
    const payload: CreateProviderApiKeyRequestDto = {
      keyName: providerForm.keyName.trim(),
      serviceCode: providerForm.serviceCode,
      apiKey: providerForm.apiKey,
      description: providerForm.description || null,
      // 빈 문자열 -> null, "YYYY-MM-DD" -> ISO 8601 (시간은 UTC 자정으로 정규화)
      expiresAt: providerForm.expiresAt ? new Date(providerForm.expiresAt).toISOString() : null,
      validateOnCreate: providerForm.validateOnCreate
    }

    const created = await apiKeyService.createProviderKey(payload)
    // 등록 직후 평문 키 즉시 폐기 (보존 시간 최소화)
    providerForm.apiKey = ''
    toast(`${t('apiKeys.provider.toast.created')}: ${created.keyName}`, 'success')

    closeProviderModal()
    await Promise.all([loadProviderKeys(), loadPoolStats()])
  } catch (e: any) {
    const msg = e.response?.data?.message ?? t('apiKeys.provider.toast.createFailed')
    // 백엔드 ping 실패 메시지를 그대로 노출하기 위해 토스트 표시 시간을 늘림.
    toast(msg, 'error', 8000)
  } finally {
    submittingProvider.value = false
  }
}

/**
 * 키별 [테스트] 버튼 — 제공사별 ping.
 * 결과는 토스트로 표시. testingKeys 로 동시 호출 차단.
 */
const testProviderKey = async (key: ApiKeyDto) => {
  if (testingKeys[key.apiKeyId]) return
  testingKeys[key.apiKeyId] = true
  try {
    const r = await apiKeyService.testKey(key.apiKeyId)
    const label = r.success ? t('apiKeys.provider.toast.testPass') : t('apiKeys.provider.toast.testFail')
    toast(`${label}: ${r.message} (${r.latencyMs}ms)`,
          r.success ? 'success' : 'error', 5000)
  } catch (e: any) {
    toast(`${t('apiKeys.provider.toast.testNetworkError')}: ${e.response?.data?.message ?? e.message}`, 'error')
  } finally {
    testingKeys[key.apiKeyId] = false
  }
}

/**
 * 키 삭제 — 풀에서 즉시 제외됨 (백엔드 트리거).
 * 운영자 콘솔이므로 confirm 으로 명시적 확인.
 */
const deleteProviderKey = async (key: ApiKeyDto) => {
  if (!confirm(t('apiKeys.provider.confirmDelete', { name: key.keyName }))) return
  try {
    await apiKeyService.deleteKey(key.apiKeyId)
    toast(t('apiKeys.provider.toast.deleted'), 'success')
    await Promise.all([loadProviderKeys(), loadPoolStats()])
  } catch (e: any) {
    toast(e.response?.data?.message ?? t('apiKeys.provider.toast.deleteFailed'), 'error')
  }
}

/**
 * 풀 통계 우측 카드에서 단일 프로바이더 행 찾기 — undefined 면 미등록.
 */
const findProviderStat = (serviceCode: string): ProviderPoolStatDto | undefined => {
  return poolStats.value?.providers?.find(p => p.serviceCode === serviceCode)
}

// 탭 전환 감시 — provider-pool 탭 진입 시 데이터 로드 (운영자만).
// 일반 사용자는 isAdmin=false 이므로 탭 자체가 노출되지 않음 — 추가 가드는 백엔드 403.
watch(activeTab, async (tab) => {
  if (tab === 'provider-pool' && isAdmin.value) {
    await Promise.all([loadProviderKeys(), loadPoolStats()])
  }
})

// locale 변경 시 별도 리렌더 트리거 불필요 — vue-i18n 의 reactive translation 이 처리.
// 단, 향후 locale 별 다른 데이터가 필요해지면 여기서 reload 추가.
void locale
</script>

<style scoped>
/* ── 탭 ─────────────────────────────────────────────── */
.ak-tabs {
  display: inline-flex;
  background: var(--ai-bg-light, #f1f3f5);
  border: 1px solid var(--ai-border, #dee2e6);
  border-radius: 12px;
  padding: 4px;
  gap: 4px;
  margin-bottom: 1.25rem;
}

.ak-tab {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--ai-text-muted, #6c757d);
  background: transparent;
  border: none;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.18s ease;
  position: relative;
}
.ak-tab:hover { color: var(--ai-text, #212529); background: rgba(255,255,255,0.7); }
.ak-tab.active { background: #fff; color: var(--ai-primary, #0d6efd); box-shadow: 0 1px 4px rgba(0,0,0,0.1); }
.ak-tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  font-size: 0.7rem;
  font-weight: 700;
  border-radius: 99px;
  background: var(--ai-primary, #0d6efd);
  color: #fff;
}

/* ── 빈 상태 ─────────────────────────────────────────── */
.ak-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3.5rem 1.5rem;
  text-align: center;
}
.ak-empty-icon {
  width: 64px; height: 64px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 16px;
  background: var(--ai-bg-light, #f8f9fa);
  color: #adb5bd;
  font-size: 1.75rem;
  margin-bottom: 1rem;
}
.ak-empty-title { font-weight: 600; color: #495057; margin-bottom: 0.35rem; }
.ak-empty-desc { font-size: 0.875rem; color: #6c757d; margin-bottom: 1rem; }

/* ── API 키 목록 ─────────────────────────────────────── */
.ak-key-list { padding: 0.75rem; display: flex; flex-direction: column; gap: 0.5rem; }

.ak-key-row {
  border: 1px solid var(--ai-border, #e9ecef);
  border-radius: 12px;
  padding: 1rem 1.125rem;
  background: #fff;
  transition: box-shadow 0.18s ease, border-color 0.18s ease;
}
.ak-key-row:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.07); border-color: #ced4da; }
.ak-key-row--inactive { opacity: 0.65; background: var(--ai-bg-light, #f8f9fa); }
.ak-key-row--expired { border-color: #f5c6cb; background: #fff8f8; }

.ak-key-head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.65rem;
}
.ak-key-icon-wrap {
  width: 38px; height: 38px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 10px;
  background: var(--ai-bg-light, #f0f4ff);
  font-size: 1.15rem;
  flex-shrink: 0;
}
.ak-key-icon-agent { background: #e8f4ff; }
.ak-key-info { display: flex; flex-direction: column; min-width: 0; }
.ak-key-name { font-weight: 600; font-size: 0.9rem; color: #212529; line-height: 1.3; }
.ak-key-service { font-size: 0.78rem; color: #6c757d; margin-top: 1px; }

.ak-key-desc { font-size: 0.82rem; color: #6c757d; margin: 0 0 0.65rem; }

.ak-key-value-row { margin-bottom: 0.65rem; }
.ak-key-prefix { background: var(--ai-bg-light, #f8f9fa); padding: 0 0.65rem; }
.ak-key-input { font-size: 0.82rem; }

.ak-key-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.78rem;
  color: #6c757d;
  margin-bottom: 0.75rem;
}
.ak-key-meta i { margin-right: 0.25rem; }

.ak-key-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }

/* ── Agent 선택 바 ───────────────────────────────────── */
.ak-agent-select-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--ai-bg-light, #f8f9fa);
  border: 1px solid var(--ai-border, #e9ecef);
  border-radius: 10px;
  padding: 0.65rem 1rem;
}
.ak-agent-select-label { font-size: 0.875rem; font-weight: 500; white-space: nowrap; color: #495057; }
.ak-agent-select { flex: 1; max-width: 320px; }

/* ── 통계 ────────────────────────────────────────────── */
.ak-stat-row { display: flex; justify-content: space-between; align-items: center; padding: 0.35rem 0; font-size: 0.875rem; }
.ak-stat-label { color: #6c757d; }
.ak-stat-value { font-weight: 700; font-size: 1rem; }
.ak-stat-bar { border-radius: 99px; overflow: hidden; }

/* ── 트랙 #91: 외부 LLM 키 풀 통계 ───────────────────── */
.ak-pool-row {
  padding: 0.6rem 0;
  border-bottom: 1px dashed var(--ai-border, #e9ecef);
}
.ak-pool-row:last-child { border-bottom: none; }
.ak-pool-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}
.ak-pool-total { font-size: 0.85rem; color: #495057; }
.ak-pool-total strong { font-size: 1rem; color: #212529; }
.ak-pool-detail {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-family: var(--bs-font-monospace, monospace);
}
.ak-pool-sep { color: #adb5bd; }
.ak-pool-footer {
  margin-top: 0.65rem;
  padding-top: 0.55rem;
  border-top: 1px dashed var(--ai-border, #e9ecef);
  font-size: 0.75rem;
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

/* ── 보안/주의 목록 ──────────────────────────────────── */
.ak-security-list { list-style: none; padding: 0; margin: 0; }
.ak-security-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  font-size: 0.83rem;
  color: #495057;
  padding: 0.3rem 0;
  margin-bottom: 0.5rem;
}
.ak-security-list li i { flex-shrink: 0; margin-top: 0.1rem; }

/* ── API 가이드 ──────────────────────────────────────── */
.ak-guide-section { margin-bottom: 1rem; }
.ak-guide-label {
  display: inline-block;
  font-size: 0.73rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6c757d;
  margin-bottom: 0.4rem;
}
.ak-code-block {
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 0.6rem 0.85rem;
  font-size: 0.78rem;
  overflow-x: auto;
}
.ak-code-block code { color: #e2e8f0; background: none; padding: 0; font-size: inherit; }
.ak-code-multiline pre { margin: 0; color: #e2e8f0; font-size: 0.76rem; white-space: pre-wrap; word-break: break-all; }

/* ── 고급 보안 설정 토글 ─────────────────────────────── */
.ak-advanced-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 500;
  color: #495057;
  cursor: pointer;
  padding: 0.5rem 0;
  border-top: 1px dashed var(--ai-border, #dee2e6);
  margin-top: 0.5rem;
  user-select: none;
}
.ak-advanced-toggle:hover { color: var(--ai-primary, #0d6efd); }
.ak-advanced-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 99px;
  background: #e8f4ff;
  color: #0d6efd;
  margin-left: auto;
}
.ak-advanced-body {
  background: var(--ai-bg-light, #f8f9fa);
  border: 1px solid var(--ai-border, #e9ecef);
  border-radius: 10px;
  padding: 1rem;
  margin-top: 0.5rem;
}
/* ── 토스트 ─────────────────────────────────────────── */
.ak-toast {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.7rem 1.2rem;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #fff;
  background: #1e293b;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  opacity: 0;
  transform: translateY(12px);
  pointer-events: none;
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.ak-toast--show { opacity: 1; transform: translateY(0); pointer-events: auto; }
.ak-toast--success { background: #198754; }
.ak-toast--error   { background: #dc3545; }
.ak-toast--info    { background: #0d6efd; }

/* ── 모달 ────────────────────────────────────────────── */
.modal.show { display: block; }
.modal-backdrop.show { opacity: 0.45; }
.fs-7 { font-size: 0.8rem; }
</style>
