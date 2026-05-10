<template>
  <div class="admin-docutil-evaluation container-fluid py-4">
    <header class="mb-3">
      <h1 class="h3 mb-1">{{ t('adminDocutilEvaluation.title') }}</h1>
      <p class="text-muted mb-0">{{ t('adminDocutilEvaluation.subtitle') }}</p>
    </header>

    <!-- 알림 -->
    <div v-if="successMessage" class="alert alert-success alert-dismissible" role="alert">
      {{ successMessage }}
      <button type="button" class="btn-close" @click="successMessage = ''"></button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible" role="alert">
      {{ errorMessage }}
      <button type="button" class="btn-close" @click="errorMessage = ''"></button>
    </div>

    <!-- 탭 -->
    <ul class="nav nav-tabs mb-3" role="tablist">
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'config' }"
          @click="activeTab = 'config'"
        >
          <i class="bi bi-sliders me-2"></i>{{ t('adminDocutilEvaluation.tabConfig') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'runs' }"
          @click="onSwitchToRuns"
        >
          <i class="bi bi-play-circle me-2"></i>{{ t('adminDocutilEvaluation.tabRuns') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'trend' }"
          @click="onSwitchToTrend"
        >
          <i class="bi bi-graph-up me-2"></i>{{ t('adminDocutilEvaluation.tabTrend') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'logs' }"
          @click="onSwitchToLogs"
        >
          <i class="bi bi-list-ul me-2"></i>{{ t('adminDocutilEvaluation.tabLogs') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'questions' }"
          @click="onSwitchToQuestions"
        >
          <i class="bi bi-chat-dots me-2"></i>{{ t('adminDocutilEvaluation.tabQuestions') }}
        </button>
      </li>
    </ul>

    <!-- Config 탭 -->
    <section v-if="activeTab === 'config'">
      <div class="card mb-4">
        <div class="card-header bg-light d-flex align-items-center">
          <h2 class="h6 mb-0">{{ t('adminDocutilEvaluation.configTitle') }}</h2>
          <p class="text-muted small mb-0 ms-3">{{ t('adminDocutilEvaluation.configSubtitle') }}</p>
        </div>
        <div class="card-body">
          <div v-if="configLoading" class="text-center py-3 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilEvaluation.loading') }}
          </div>
          <div v-else-if="config">
            <div class="row g-3">
              <div class="col-md-3">
                <label class="form-label">{{ t('adminDocutilEvaluation.weightContextRelevancy') }}</label>
                <input
                  v-model.number="configForm.contextRelevancyWeight"
                  type="number"
                  class="form-control"
                  min="0"
                  max="1"
                  step="0.05"
                  :disabled="!configEditing"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">{{ t('adminDocutilEvaluation.weightAnswerFaithfulness') }}</label>
                <input
                  v-model.number="configForm.answerFaithfulnessWeight"
                  type="number"
                  class="form-control"
                  min="0"
                  max="1"
                  step="0.05"
                  :disabled="!configEditing"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">{{ t('adminDocutilEvaluation.weightAnswerRelevancy') }}</label>
                <input
                  v-model.number="configForm.answerRelevancyWeight"
                  type="number"
                  class="form-control"
                  min="0"
                  max="1"
                  step="0.05"
                  :disabled="!configEditing"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">{{ t('adminDocutilEvaluation.weightHallucination') }}</label>
                <input
                  v-model.number="configForm.hallucinationWeight"
                  type="number"
                  class="form-control"
                  min="0"
                  max="1"
                  step="0.05"
                  :disabled="!configEditing"
                />
              </div>
              <div class="col-12">
                <span class="badge bg-secondary">
                  {{ t('adminDocutilEvaluation.weightSumLabel') }}: {{ weightSum.toFixed(2) }}
                </span>
              </div>
              <div class="col-12 d-flex">
                <button
                  v-if="!configEditing"
                  type="button"
                  class="btn btn-primary"
                  @click="configEditing = true"
                >
                  <i class="bi bi-pencil me-2"></i>{{ t('adminDocutilEvaluation.edit') }}
                </button>
                <template v-else>
                  <button
                    type="button"
                    class="btn btn-secondary me-2"
                    @click="onCancelConfigEdit"
                  >
                    {{ t('adminDocutilEvaluation.cancel') }}
                  </button>
                  <button
                    type="button"
                    class="btn btn-primary"
                    :disabled="configSaving"
                    @click="onSaveConfig"
                  >
                    <span v-if="configSaving" class="spinner-border spinner-border-sm me-2"></span>
                    {{ configSaving ? t('adminDocutilEvaluation.saving') : t('adminDocutilEvaluation.save') }}
                  </button>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 평가 실행 카드 -->
      <div class="card">
        <div class="card-header bg-light">
          <h2 class="h6 mb-0">{{ t('adminDocutilEvaluation.runTitle') }}</h2>
          <p class="text-muted small mb-0">{{ t('adminDocutilEvaluation.runSubtitle') }}</p>
        </div>
        <div class="card-body">
          <div class="form-check mb-3">
            <input v-model="useDefaultQuestions" class="form-check-input" type="checkbox" id="useDefaults" />
            <label class="form-check-label" for="useDefaults">
              {{ t('adminDocutilEvaluation.runUseDefaults') }}
            </label>
          </div>
          <div v-if="!useDefaultQuestions" class="mb-3">
            <label class="form-label small">{{ t('adminDocutilEvaluation.runCustomQuestions') }}</label>
            <textarea
              v-model="customQuestionsRaw"
              class="form-control"
              rows="5"
              :placeholder="t('adminDocutilEvaluation.runQuestionPlaceholder')"
            ></textarea>
          </div>
          <button
            type="button"
            class="btn btn-warning"
            :disabled="running"
            @click="onRunEvaluation"
          >
            <span v-if="running" class="spinner-border spinner-border-sm me-2"></span>
            <i v-else class="bi bi-play-fill me-1"></i>
            {{ running ? t('adminDocutilEvaluation.running') : t('adminDocutilEvaluation.runButton') }}
          </button>

          <div v-if="runResponse" class="mt-3">
            <label class="form-label small">{{ t('adminDocutilEvaluation.runResponseLabel') }}</label>
            <pre class="bg-light p-2 small mb-0">{{ JSON.stringify(runResponse, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </section>

    <!-- Runs 탭 -->
    <section v-else-if="activeTab === 'runs'">
      <div class="card">
        <div class="card-header bg-light d-flex align-items-center">
          <h2 class="h6 mb-0">{{ t('adminDocutilEvaluation.runsTitle') }}</h2>
          <div class="ms-auto d-flex align-items-center">
            <label class="me-2 small text-muted">{{ t('adminDocutilEvaluation.runsLimitLabel') }}</label>
            <select v-model.number="runsLimit" class="form-select form-select-sm" style="width: auto" @change="loadRuns">
              <option :value="10">10</option>
              <option :value="30">30</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
            <button type="button" class="btn btn-sm btn-outline-secondary ms-2" @click="loadRuns" :disabled="runsLoading">
              <i class="bi bi-arrow-clockwise me-1"></i>{{ t('adminDocutilEvaluation.runsRefresh') }}
            </button>
          </div>
        </div>
        <div class="card-body">
          <div v-if="runsLoading" class="text-center py-3 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilEvaluation.loading') }}
          </div>
          <div v-else-if="!runs || runs.items.length === 0" class="text-muted">
            {{ t('adminDocutilEvaluation.runsEmpty') }}
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm align-middle">
              <thead>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.runColRunId') }}</th>
                  <th>{{ t('adminDocutilEvaluation.runColRunType') }}</th>
                  <th>{{ t('adminDocutilEvaluation.runColCreatedAt') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColQuestionCount') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColCompositeAvg') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgContextRelevancy') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgAnswerFaithfulness') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgAnswerRelevancy') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgHallucinationScore') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColHallucinationCount') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="run in runs.items" :key="run.runId">
                  <td><code class="small">{{ run.runId.slice(0, 12) }}…</code></td>
                  <td><span class="badge bg-secondary">{{ run.runType }}</span></td>
                  <td>{{ formatDate(run.createdAt) }}</td>
                  <td class="text-end">{{ run.questionCount }}</td>
                  <td class="text-end">{{ run.avgCompositeScore.toFixed(3) }}</td>
                  <td class="text-end">{{ run.avgContextRelevancy.toFixed(3) }}</td>
                  <td class="text-end">{{ run.avgAnswerFaithfulness.toFixed(3) }}</td>
                  <td class="text-end">{{ run.avgAnswerRelevancy.toFixed(3) }}</td>
                  <td class="text-end">{{ run.avgHallucinationScore.toFixed(3) }}</td>
                  <td class="text-end">
                    <span :class="run.hallucinationCount > 0 ? 'badge bg-danger' : 'badge bg-success'">
                      {{ run.hallucinationCount }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- Trend 탭 -->
    <section v-else-if="activeTab === 'trend'">
      <div class="card">
        <div class="card-header bg-light d-flex align-items-center">
          <h2 class="h6 mb-0">{{ t('adminDocutilEvaluation.trendTitle') }}</h2>
          <div class="ms-auto d-flex align-items-center">
            <label class="me-2 small text-muted">{{ t('adminDocutilEvaluation.trendDaysLabel') }}</label>
            <select v-model.number="trendDays" class="form-select form-select-sm" style="width: auto" @change="loadTrend">
              <option :value="7">7</option>
              <option :value="14">14</option>
              <option :value="30">30</option>
              <option :value="90">90</option>
              <option :value="180">180</option>
              <option :value="365">365</option>
            </select>
          </div>
        </div>
        <div class="card-body">
          <p class="text-muted small">{{ t('adminDocutilEvaluation.trendSubtitle') }}</p>
          <div v-if="trendLoading" class="text-center py-3 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilEvaluation.loading') }}
          </div>
          <div v-else-if="!trend || trend.data.length === 0" class="text-muted">
            {{ t('adminDocutilEvaluation.trendEmpty') }}
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.trendColDate') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColCompositeAvg') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgContextRelevancy') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgAnswerFaithfulness') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgAnswerRelevancy') }}</th>
                  <th class="text-end">{{ t('adminDocutilEvaluation.runColAvgHallucinationScore') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="point in trend.data" :key="point.date">
                  <td>{{ point.date }}</td>
                  <td class="text-end">{{ point.avgCompositeScore.toFixed(3) }}</td>
                  <td class="text-end">{{ point.avgContextRelevancy.toFixed(3) }}</td>
                  <td class="text-end">{{ point.avgAnswerFaithfulness.toFixed(3) }}</td>
                  <td class="text-end">{{ point.avgAnswerRelevancy.toFixed(3) }}</td>
                  <td class="text-end">{{ point.avgHallucinationScore.toFixed(3) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- Logs 탭 -->
    <section v-else-if="activeTab === 'logs'">
      <div class="card mb-3">
        <div class="card-header bg-light">
          <h2 class="h6 mb-0">{{ t('adminDocutilEvaluation.filters') }}</h2>
        </div>
        <div class="card-body">
          <div class="row g-2">
            <div class="col-md-3">
              <label class="form-label small">{{ t('adminDocutilEvaluation.filterRunId') }}</label>
              <input v-model="logFilters.runId" type="text" class="form-control form-control-sm" :placeholder="t('adminDocutilEvaluation.filterRunIdPlaceholder')" />
            </div>
            <div class="col-md-2">
              <label class="form-label small">{{ t('adminDocutilEvaluation.filterRunType') }}</label>
              <input v-model="logFilters.runType" type="text" class="form-control form-control-sm" :placeholder="t('adminDocutilEvaluation.filterRunTypePlaceholder')" />
            </div>
            <div class="col-md-2">
              <label class="form-label small">{{ t('adminDocutilEvaluation.filterHasHallucination') }}</label>
              <select v-model="logFilters.hasHallucinationKey" class="form-select form-select-sm">
                <option value="any">{{ t('adminDocutilEvaluation.filterHallucinationAny') }}</option>
                <option value="yes">{{ t('adminDocutilEvaluation.filterHallucinationYes') }}</option>
                <option value="no">{{ t('adminDocutilEvaluation.filterHallucinationNo') }}</option>
              </select>
            </div>
            <div class="col-md-2">
              <label class="form-label small">{{ t('adminDocutilEvaluation.filterMinScore') }}</label>
              <input v-model.number="logFilters.minScore" type="number" min="0" max="1" step="0.05" class="form-control form-control-sm" />
            </div>
            <div class="col-md-2">
              <label class="form-label small">{{ t('adminDocutilEvaluation.filterMaxScore') }}</label>
              <input v-model.number="logFilters.maxScore" type="number" min="0" max="1" step="0.05" class="form-control form-control-sm" />
            </div>
            <div class="col-md-1 d-flex align-items-end">
              <button type="button" class="btn btn-sm btn-primary me-1" @click="onApplyLogFilters" :disabled="logsLoading">
                {{ t('adminDocutilEvaluation.applyFilters') }}
              </button>
            </div>
          </div>
          <div class="mt-2">
            <button type="button" class="btn btn-sm btn-outline-secondary" @click="onClearLogFilters">
              <i class="bi bi-x-lg me-1"></i>{{ t('adminDocutilEvaluation.clearFilters') }}
            </button>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header bg-light d-flex align-items-center">
          <h2 class="h6 mb-0">{{ t('adminDocutilEvaluation.logsTitle') }}</h2>
          <span v-if="logs" class="text-muted small ms-3">
            {{ t('adminDocutilEvaluation.totalCount', { total: logs.total }) }}
          </span>
        </div>
        <div class="card-body">
          <div v-if="logsLoading" class="text-center py-3 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilEvaluation.loading') }}
          </div>
          <div v-else-if="!logs || logs.items.length === 0" class="text-muted">
            {{ t('adminDocutilEvaluation.logsEmpty') }}
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm align-middle">
              <thead>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.logColCreatedAt') }}</th>
                  <th>{{ t('adminDocutilEvaluation.logColRunType') }}</th>
                  <th>{{ t('adminDocutilEvaluation.logColQuestion') }}</th>
                  <th>{{ t('adminDocutilEvaluation.logColCompositeScore') }}</th>
                  <th>{{ t('adminDocutilEvaluation.logColHasHallucination') }}</th>
                  <th class="text-end"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="log in logs.items" :key="log.id">
                  <td>{{ formatDate(log.createdAt) }}</td>
                  <td><span class="badge bg-secondary">{{ log.runType }}</span></td>
                  <td>{{ truncate(log.question, 60) }}</td>
                  <td>{{ log.compositeScore.toFixed(3) }}</td>
                  <td>
                    <span :class="log.hasHallucination ? 'badge bg-danger' : 'badge bg-success'">
                      {{ log.hasHallucination ? t('adminDocutilEvaluation.yes') : t('adminDocutilEvaluation.no') }}
                    </span>
                  </td>
                  <td class="text-end">
                    <button type="button" class="btn btn-sm btn-outline-primary" @click="openLogDetail(log)">
                      {{ t('adminDocutilEvaluation.openDetails') }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Logs 페이지네이션 -->
            <nav class="d-flex justify-content-between align-items-center">
              <div class="d-flex align-items-center">
                <label class="me-2 small text-muted">{{ t('adminDocutilEvaluation.pageSize') }}</label>
                <select v-model.number="logsSize" class="form-select form-select-sm" style="width: auto" @change="onLogsPageSizeChange">
                  <option :value="10">10</option>
                  <option :value="20">20</option>
                  <option :value="50">50</option>
                  <option :value="100">100</option>
                </select>
              </div>
              <div class="d-flex align-items-center">
                <button type="button" class="btn btn-sm btn-outline-secondary me-2" :disabled="logsPage <= 1" @click="goToLogsPage(logsPage - 1)">
                  {{ t('adminDocutilEvaluation.prevPage') }}
                </button>
                <span class="small text-muted">
                  {{ t('adminDocutilEvaluation.page') }} {{ logsPage }} / {{ totalLogPages }}
                </span>
                <button type="button" class="btn btn-sm btn-outline-secondary ms-2" :disabled="logsPage >= totalLogPages" @click="goToLogsPage(logsPage + 1)">
                  {{ t('adminDocutilEvaluation.nextPage') }}
                </button>
              </div>
            </nav>
          </div>
        </div>
      </div>
    </section>

    <!-- Questions 탭 -->
    <section v-else-if="activeTab === 'questions'">
      <div class="card">
        <div class="card-header bg-light">
          <h2 class="h6 mb-0">{{ t('adminDocutilEvaluation.questionsTitle') }}</h2>
          <p class="text-muted small mb-0">{{ t('adminDocutilEvaluation.questionsSubtitle') }}</p>
        </div>
        <div class="card-body">
          <div v-if="questionsLoading" class="text-center py-3 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilEvaluation.loading') }}
          </div>
          <div v-else-if="!questions || Object.keys(questions).length === 0" class="text-muted">
            {{ t('adminDocutilEvaluation.questionsEmpty') }}
          </div>
          <div v-else>
            <pre class="bg-light p-3 small mb-0">{{ JSON.stringify(questions, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </section>

    <!-- 평가 로그 상세 모달 -->
    <div
      v-if="logDetailItem"
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      style="background: rgba(0,0,0,0.5)"
    >
      <div class="modal-dialog modal-xl modal-dialog-scrollable" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilEvaluation.logDetailTitle') }}</h5>
            <button type="button" class="btn-close" @click="logDetailItem = null"></button>
          </div>
          <div class="modal-body">
            <dl class="row mb-3">
              <dt class="col-sm-2">Run ID</dt>
              <dd class="col-sm-10"><code class="small">{{ logDetailItem.runId }}</code></dd>

              <dt class="col-sm-2">{{ t('adminDocutilEvaluation.logColCreatedAt') }}</dt>
              <dd class="col-sm-10">{{ formatDate(logDetailItem.createdAt) }}</dd>

              <dt class="col-sm-2">{{ t('adminDocutilEvaluation.logColRunType') }}</dt>
              <dd class="col-sm-10"><span class="badge bg-secondary">{{ logDetailItem.runType }}</span></dd>
            </dl>

            <h6>{{ t('adminDocutilEvaluation.logDetailQuestion') }}</h6>
            <pre class="bg-light p-2 small">{{ logDetailItem.question }}</pre>

            <h6>{{ t('adminDocutilEvaluation.logDetailAnswer') }}</h6>
            <pre class="bg-light p-2 small">{{ logDetailItem.answer }}</pre>

            <h6>{{ t('adminDocutilEvaluation.logDetailScores') }}</h6>
            <table class="table table-sm">
              <tbody>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.weightContextRelevancy') }}</th>
                  <td>{{ logDetailItem.contextRelevancy.toFixed(3) }}</td>
                </tr>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.weightAnswerFaithfulness') }}</th>
                  <td>{{ logDetailItem.answerFaithfulness.toFixed(3) }}</td>
                </tr>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.weightAnswerRelevancy') }}</th>
                  <td>{{ logDetailItem.answerRelevancy.toFixed(3) }}</td>
                </tr>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.weightHallucination') }}</th>
                  <td>{{ logDetailItem.hallucinationScore.toFixed(3) }}</td>
                </tr>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.runColCompositeAvg') }}</th>
                  <td><strong>{{ logDetailItem.compositeScore.toFixed(3) }}</strong></td>
                </tr>
                <tr>
                  <th>{{ t('adminDocutilEvaluation.logColHasHallucination') }}</th>
                  <td>
                    <span :class="logDetailItem.hasHallucination ? 'badge bg-danger' : 'badge bg-success'">
                      {{ logDetailItem.hasHallucination ? t('adminDocutilEvaluation.yes') : t('adminDocutilEvaluation.no') }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>

            <details v-if="logDetailItem.contexts" class="mb-2">
              <summary><h6 class="d-inline">{{ t('adminDocutilEvaluation.logDetailContexts') }}</h6></summary>
              <pre class="bg-light p-2 small mt-2">{{ JSON.stringify(logDetailItem.contexts, null, 2) }}</pre>
            </details>
            <details v-if="logDetailItem.hallucinationEvidence" class="mb-2">
              <summary><h6 class="d-inline">{{ t('adminDocutilEvaluation.logDetailEvidence') }}</h6></summary>
              <pre class="bg-light p-2 small mt-2">{{ JSON.stringify(logDetailItem.hallucinationEvidence, null, 2) }}</pre>
            </details>
            <details v-if="logDetailItem.judgeDetails" class="mb-2">
              <summary><h6 class="d-inline">{{ t('adminDocutilEvaluation.logDetailJudgeDetails') }}</h6></summary>
              <pre class="bg-light p-2 small mt-2">{{ JSON.stringify(logDetailItem.judgeDetails, null, 2) }}</pre>
            </details>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="logDetailItem = null">{{ t('adminDocutilEvaluation.cancel') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  getEvaluationConfig,
  updateEvaluationConfig,
  listEvaluationLogs,
  getEvaluationQuestions,
  runEvaluation,
  listEvaluationRuns,
  getEvaluationTrend
} from '@/services/docutilService'
import type {
  DocUtilEvaluationConfig,
  DocUtilEvaluationLogList,
  DocUtilEvaluationLogEntry,
  DocUtilEvaluationRunList,
  DocUtilEvaluationTrend,
  DocUtilUpdateEvaluationConfigRequest,
  DocUtilRunEvaluationRequest,
  EvaluationLogFilters
} from '@/services/docutilService'

const { t } = useI18n()

type Tab = 'config' | 'runs' | 'trend' | 'logs' | 'questions'
const activeTab = ref<Tab>('config')

// 알림
const successMessage = ref('')
const errorMessage = ref('')

// Config
const configLoading = ref(false)
const configEditing = ref(false)
const configSaving = ref(false)
const config = ref<DocUtilEvaluationConfig | null>(null)
const configForm = ref<DocUtilUpdateEvaluationConfigRequest>({
  contextRelevancyWeight: 0.25,
  answerFaithfulnessWeight: 0.3,
  answerRelevancyWeight: 0.25,
  hallucinationWeight: 0.2
})
const weightSum = computed(() =>
  (configForm.value.contextRelevancyWeight || 0) +
  (configForm.value.answerFaithfulnessWeight || 0) +
  (configForm.value.answerRelevancyWeight || 0) +
  (configForm.value.hallucinationWeight || 0)
)

// 평가 실행
const useDefaultQuestions = ref(true)
const customQuestionsRaw = ref('')
const running = ref(false)
const runResponse = ref<Record<string, unknown> | null>(null)

// Runs
const runsLoading = ref(false)
const runsLimit = ref(30)
const runs = ref<DocUtilEvaluationRunList | null>(null)

// Trend
const trendLoading = ref(false)
const trendDays = ref(30)
const trend = ref<DocUtilEvaluationTrend | null>(null)

// Logs
const logsLoading = ref(false)
const logsPage = ref(1)
const logsSize = ref(20)
const logs = ref<DocUtilEvaluationLogList | null>(null)
interface LogFilterUiState {
  runId: string
  runType: string
  hasHallucinationKey: 'any' | 'yes' | 'no'
  minScore: number | null
  maxScore: number | null
}
const logFilters = ref<LogFilterUiState>({
  runId: '',
  runType: '',
  hasHallucinationKey: 'any',
  minScore: null,
  maxScore: null
})
const totalLogPages = computed(() => {
  if (!logs.value || logs.value.total === 0) return 1
  return Math.max(1, Math.ceil(logs.value.total / logs.value.size))
})
const logDetailItem = ref<DocUtilEvaluationLogEntry | null>(null)

// Questions
const questionsLoading = ref(false)
const questions = ref<Record<string, unknown> | null>(null)

// ── 라이프사이클 ──
onMounted(() => {
  void loadConfig()
})

// ── 공통 ──
function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('ko-KR', { hour12: false })
  } catch {
    return iso
  }
}

function truncate(s: string, n: number): string {
  if (!s) return ''
  return s.length > n ? `${s.slice(0, n)}...` : s
}

function extractMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response
    if (response?.data?.message) return response.data.message
  }
  if (err instanceof Error) return err.message
  return t('adminDocutilEvaluation.errorUnknown')
}

// ── Config ──
async function loadConfig(): Promise<void> {
  configLoading.value = true
  errorMessage.value = ''
  try {
    config.value = await getEvaluationConfig()
    configForm.value = {
      contextRelevancyWeight: config.value.contextRelevancyWeight,
      answerFaithfulnessWeight: config.value.answerFaithfulnessWeight,
      answerRelevancyWeight: config.value.answerRelevancyWeight,
      hallucinationWeight: config.value.hallucinationWeight
    }
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    configLoading.value = false
  }
}

function onCancelConfigEdit(): void {
  if (config.value) {
    configForm.value = {
      contextRelevancyWeight: config.value.contextRelevancyWeight,
      answerFaithfulnessWeight: config.value.answerFaithfulnessWeight,
      answerRelevancyWeight: config.value.answerRelevancyWeight,
      hallucinationWeight: config.value.hallucinationWeight
    }
  }
  configEditing.value = false
}

async function onSaveConfig(): Promise<void> {
  for (const w of [
    configForm.value.contextRelevancyWeight,
    configForm.value.answerFaithfulnessWeight,
    configForm.value.answerRelevancyWeight,
    configForm.value.hallucinationWeight
  ]) {
    if (w < 0 || w > 1) {
      errorMessage.value = t('adminDocutilEvaluation.validationWeight')
      return
    }
  }
  configSaving.value = true
  errorMessage.value = ''
  try {
    config.value = await updateEvaluationConfig(configForm.value)
    successMessage.value = t('adminDocutilEvaluation.configUpdateSuccess')
    configEditing.value = false
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    configSaving.value = false
  }
}

// ── Run ──
async function onRunEvaluation(): Promise<void> {
  let questions: string[] | null = null
  if (!useDefaultQuestions.value) {
    questions = customQuestionsRaw.value
      .split('\n')
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
    if (questions.length > 100) {
      errorMessage.value = t('adminDocutilEvaluation.validationQuestionCount')
      return
    }
    for (const q of questions) {
      if (q.length > 2000) {
        errorMessage.value = t('adminDocutilEvaluation.validationQuestionLength')
        return
      }
    }
  }
  running.value = true
  errorMessage.value = ''
  try {
    const req: DocUtilRunEvaluationRequest = { questions }
    runResponse.value = await runEvaluation(req)
    successMessage.value = t('adminDocutilEvaluation.runSuccess')
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    running.value = false
  }
}

// ── Runs ──
async function loadRuns(): Promise<void> {
  runsLoading.value = true
  errorMessage.value = ''
  try {
    runs.value = await listEvaluationRuns(runsLimit.value)
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    runsLoading.value = false
  }
}

function onSwitchToRuns(): void {
  activeTab.value = 'runs'
  if (!runs.value) {
    void loadRuns()
  }
}

// ── Trend ──
async function loadTrend(): Promise<void> {
  trendLoading.value = true
  errorMessage.value = ''
  try {
    trend.value = await getEvaluationTrend(trendDays.value)
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    trendLoading.value = false
  }
}

function onSwitchToTrend(): void {
  activeTab.value = 'trend'
  if (!trend.value) {
    void loadTrend()
  }
}

// ── Logs ──
async function loadLogs(): Promise<void> {
  logsLoading.value = true
  errorMessage.value = ''
  try {
    const filters: EvaluationLogFilters = {
      page: logsPage.value,
      size: logsSize.value
    }
    if (logFilters.value.runId.trim()) filters.runId = logFilters.value.runId.trim()
    if (logFilters.value.runType.trim()) filters.runType = logFilters.value.runType.trim()
    if (logFilters.value.hasHallucinationKey === 'yes') filters.hasHallucination = true
    else if (logFilters.value.hasHallucinationKey === 'no') filters.hasHallucination = false
    if (typeof logFilters.value.minScore === 'number') filters.minScore = logFilters.value.minScore
    if (typeof logFilters.value.maxScore === 'number') filters.maxScore = logFilters.value.maxScore

    if (typeof filters.minScore === 'number' && (filters.minScore < 0 || filters.minScore > 1)) {
      errorMessage.value = t('adminDocutilEvaluation.validationScoreRange')
      return
    }
    if (typeof filters.maxScore === 'number' && (filters.maxScore < 0 || filters.maxScore > 1)) {
      errorMessage.value = t('adminDocutilEvaluation.validationScoreRange')
      return
    }

    logs.value = await listEvaluationLogs(filters)
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    logsLoading.value = false
  }
}

function onSwitchToLogs(): void {
  activeTab.value = 'logs'
  if (!logs.value) {
    void loadLogs()
  }
}

function onApplyLogFilters(): void {
  logsPage.value = 1
  void loadLogs()
}

function onClearLogFilters(): void {
  logFilters.value = {
    runId: '',
    runType: '',
    hasHallucinationKey: 'any',
    minScore: null,
    maxScore: null
  }
  logsPage.value = 1
  void loadLogs()
}

function onLogsPageSizeChange(): void {
  logsPage.value = 1
  void loadLogs()
}

function goToLogsPage(p: number): void {
  if (p < 1 || p > totalLogPages.value) return
  logsPage.value = p
  void loadLogs()
}

function openLogDetail(log: DocUtilEvaluationLogEntry): void {
  logDetailItem.value = log
}

// ── Questions ──
async function loadQuestions(): Promise<void> {
  questionsLoading.value = true
  errorMessage.value = ''
  try {
    questions.value = await getEvaluationQuestions()
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    questionsLoading.value = false
  }
}

function onSwitchToQuestions(): void {
  activeTab.value = 'questions'
  if (!questions.value) {
    void loadQuestions()
  }
}
</script>

<style scoped>
.admin-docutil-evaluation {
  max-width: 1500px;
  margin: 0 auto;
}
.modal {
  overflow-y: auto;
}
</style>
