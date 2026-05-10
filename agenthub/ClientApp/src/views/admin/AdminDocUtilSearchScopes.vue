<template>
  <div class="admin-docutil-search-scopes container-fluid py-4">
    <header class="mb-3">
      <h1 class="h3 mb-1">{{ t('adminDocutilSearchScopes.title') }}</h1>
      <p class="text-muted mb-0">{{ t('adminDocutilSearchScopes.subtitle') }}</p>
    </header>

    <!-- 탭 -->
    <ul class="nav nav-tabs mb-3" role="tablist">
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'scopes' }"
          @click="activeTab = 'scopes'"
        >
          <i class="bi bi-bullseye me-2"></i>{{ t('adminDocutilSearchScopes.tabScopes') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'locations' }"
          @click="onSwitchToLocations"
        >
          <i class="bi bi-geo-alt me-2"></i>{{ t('adminDocutilSearchScopes.tabLocations') }}
        </button>
      </li>
      <li class="nav-item" role="presentation">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'options' }"
          @click="onSwitchToOptions"
        >
          <i class="bi bi-list-check me-2"></i>{{ t('adminDocutilSearchScopes.tabOptions') }}
        </button>
      </li>
    </ul>

    <!-- 알림 -->
    <div v-if="successMessage" class="alert alert-success alert-dismissible" role="alert">
      {{ successMessage }}
      <button type="button" class="btn-close" @click="successMessage = ''"></button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible" role="alert">
      {{ errorMessage }}
      <button type="button" class="btn-close" @click="errorMessage = ''"></button>
    </div>

    <!-- Scopes 탭 -->
    <section v-if="activeTab === 'scopes'">
      <div class="d-flex align-items-center mb-3">
        <button
          type="button"
          class="btn btn-primary"
          @click="openCreateModal"
        >
          <i class="bi bi-plus-lg me-2"></i>{{ t('adminDocutilSearchScopes.create') }}
        </button>
        <button
          type="button"
          class="btn btn-outline-secondary ms-2"
          @click="loadScopes(true)"
          :disabled="loading"
        >
          <i class="bi bi-arrow-clockwise me-2"></i>{{ t('adminDocutilSearchScopes.refresh') }}
        </button>
        <span v-if="scopeList" class="text-muted ms-3">
          {{ t('adminDocutilSearchScopes.totalCount', { total: scopeList.total }) }}
        </span>
      </div>

      <div v-if="loading" class="text-center py-5 text-muted">
        <div class="spinner-border me-2"></div>{{ t('adminDocutilSearchScopes.loading') }}
      </div>
      <div v-else-if="!scopeList || scopeList.items.length === 0" class="text-center py-5 text-muted">
        {{ t('adminDocutilSearchScopes.empty') }}
      </div>
      <div v-else class="table-responsive">
        <table class="table table-hover align-middle">
          <thead>
            <tr>
              <th scope="col">{{ t('adminDocutilSearchScopes.colName') }}</th>
              <th scope="col">{{ t('adminDocutilSearchScopes.colDescription') }}</th>
              <th scope="col">{{ t('adminDocutilSearchScopes.colLocation') }}</th>
              <th scope="col">{{ t('adminDocutilSearchScopes.colFeatures') }}</th>
              <th scope="col">{{ t('adminDocutilSearchScopes.colCreatedAt') }}</th>
              <th scope="col" class="text-end">{{ t('adminDocutilSearchScopes.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in scopeList.items"
              :key="item.id"
            >
              <td>
                <button
                  type="button"
                  class="btn btn-link p-0 text-start fw-semibold"
                  @click="openDetail(item)"
                >
                  {{ item.name }}
                </button>
              </td>
              <td class="text-muted">
                {{ item.description || t('adminDocutilSearchScopes.noDescription') }}
              </td>
              <td>{{ item.locationPath || t('adminDocutilSearchScopes.noLocation') }}</td>
              <td>
                <span
                  v-if="item.chatbotEnabled"
                  class="badge bg-primary me-1"
                >{{ t('adminDocutilSearchScopes.featureChatbot') }}</span>
                <span
                  v-if="item.qaEnabled"
                  class="badge bg-success me-1"
                >{{ t('adminDocutilSearchScopes.featureQa') }}</span>
                <span
                  v-if="item.keywordSearchEnabled"
                  class="badge bg-info me-1"
                >{{ t('adminDocutilSearchScopes.featureKeyword') }}</span>
                <span
                  v-if="item.agentEnabled"
                  class="badge bg-warning text-dark me-1"
                >{{ t('adminDocutilSearchScopes.featureAgent') }}</span>
              </td>
              <td>{{ formatDate(item.createdAt) }}</td>
              <td class="text-end">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary me-1"
                  @click="openEditModal(item)"
                >
                  {{ t('adminDocutilSearchScopes.edit') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-info me-1"
                  @click="openEnvModal(item)"
                >
                  {{ t('adminDocutilSearchScopes.editEnvironment') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger"
                  @click="onDelete(item)"
                >
                  {{ t('adminDocutilSearchScopes.delete') }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- 페이지네이션 -->
        <nav class="d-flex justify-content-between align-items-center">
          <div class="d-flex align-items-center">
            <label class="me-2 small text-muted">{{ t('adminDocutilSearchScopes.pageSize') }}</label>
            <select v-model.number="size" class="form-select form-select-sm" style="width: auto" @change="onPageSizeChange">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <div class="d-flex align-items-center">
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary me-2"
              :disabled="page <= 1"
              @click="goToPage(page - 1)"
            >
              {{ t('adminDocutilSearchScopes.prevPage') }}
            </button>
            <span class="small text-muted">
              {{ t('adminDocutilSearchScopes.page') }} {{ page }} / {{ totalPages }}
            </span>
            <button
              type="button"
              class="btn btn-sm btn-outline-secondary ms-2"
              :disabled="page >= totalPages"
              @click="goToPage(page + 1)"
            >
              {{ t('adminDocutilSearchScopes.nextPage') }}
            </button>
          </div>
        </nav>
      </div>
    </section>

    <!-- Locations 탭 -->
    <section v-else-if="activeTab === 'locations'">
      <div class="card">
        <div class="card-header bg-light">
          <h2 class="h6 mb-0">{{ t('adminDocutilSearchScopes.locationsTitle') }}</h2>
          <p class="small text-muted mb-0">
            {{ t('adminDocutilSearchScopes.locationsSubtitle') }}
          </p>
        </div>
        <div class="card-body">
          <div class="btn-group mb-3" role="group">
            <button
              v-for="lt in (['project', 'board', 'folder'] as const)"
              :key="lt"
              type="button"
              class="btn btn-outline-primary"
              :class="{ active: locationType === lt }"
              @click="onChangeLocationType(lt)"
            >
              {{ t(`adminDocutilSearchScopes.locationType${capitalize(lt)}`) }}
            </button>
          </div>

          <div v-if="locationsLoading" class="text-center py-3 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilSearchScopes.loading') }}
          </div>
          <div v-else-if="locations.length === 0" class="text-muted">
            {{ t('adminDocutilSearchScopes.locationsEmpty') }}
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>{{ t('adminDocutilSearchScopes.colName') }}</th>
                  <th>ID</th>
                  <th>{{ t('adminDocutilSearchScopes.colLocation') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="loc in locations" :key="loc.id">
                  <td>{{ loc.name }}</td>
                  <td><code class="small">{{ loc.id }}</code></td>
                  <td class="text-muted">{{ loc.path || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- Options 탭 -->
    <section v-else-if="activeTab === 'options'">
      <div class="card">
        <div class="card-header bg-light">
          <h2 class="h6 mb-0">{{ t('adminDocutilSearchScopes.optionsTitle') }}</h2>
          <p class="small text-muted mb-0">
            {{ t('adminDocutilSearchScopes.optionsSubtitle') }}
          </p>
        </div>
        <div class="card-body">
          <div v-if="optionsLoading" class="text-center py-3 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilSearchScopes.loading') }}
          </div>
          <div v-else-if="scopeOptions.length === 0" class="text-muted">
            {{ t('adminDocutilSearchScopes.optionsEmpty') }}
          </div>
          <div v-else class="table-responsive">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>{{ t('adminDocutilSearchScopes.colName') }}</th>
                  <th>ID</th>
                  <th>{{ t('adminDocutilSearchScopes.colLocation') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="opt in scopeOptions" :key="opt.id">
                  <td>{{ opt.name }}</td>
                  <td><code class="small">{{ opt.id }}</code></td>
                  <td class="text-muted">{{ opt.locationPath || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- 생성/수정 모달 -->
    <div
      v-if="showFormModal"
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      style="background: rgba(0,0,0,0.5)"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ formMode === 'create'
                ? t('adminDocutilSearchScopes.modalCreateTitle')
                : t('adminDocutilSearchScopes.modalEditTitle') }}
            </h5>
            <button type="button" class="btn-close" @click="closeFormModal"></button>
          </div>
          <div class="modal-body">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label">{{ t('adminDocutilSearchScopes.fieldName') }} <span class="text-danger">*</span></label>
                <input
                  v-model="form.name"
                  type="text"
                  class="form-control"
                  :placeholder="t('adminDocutilSearchScopes.fieldNamePlaceholder')"
                  maxlength="255"
                />
              </div>
              <div class="col-md-6">
                <label class="form-label">{{ t('adminDocutilSearchScopes.fieldLocationType') }}</label>
                <select v-model="form.locationKind" class="form-select" @change="onFormLocationKindChange">
                  <option value="">{{ t('adminDocutilSearchScopes.locationTypeNone') }}</option>
                  <option value="project">{{ t('adminDocutilSearchScopes.locationTypeProject') }}</option>
                  <option value="board">{{ t('adminDocutilSearchScopes.locationTypeBoard') }}</option>
                  <option value="folder">{{ t('adminDocutilSearchScopes.locationTypeFolder') }}</option>
                </select>
              </div>
              <div v-if="form.locationKind" class="col-md-6">
                <label class="form-label">{{ t('adminDocutilSearchScopes.fieldLocationId') }}</label>
                <select v-model="form.locationId" class="form-select" :disabled="formLocationsLoading">
                  <option value="">{{ t('adminDocutilSearchScopes.locationIdNone') }}</option>
                  <option v-for="loc in formLocations" :key="loc.id" :value="loc.id">
                    {{ loc.name }} ({{ loc.id.slice(0, 8) }}...)
                  </option>
                </select>
              </div>
              <div class="col-12">
                <label class="form-label">{{ t('adminDocutilSearchScopes.fieldDescription') }}</label>
                <textarea
                  v-model="form.description"
                  class="form-control"
                  rows="2"
                  :placeholder="t('adminDocutilSearchScopes.fieldDescriptionPlaceholder')"
                  maxlength="2000"
                ></textarea>
              </div>

              <div class="col-12"><hr class="my-1" /></div>

              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="form.chatbotEnabled" class="form-check-input" type="checkbox" id="formChatbotEnabled" />
                  <label class="form-check-label" for="formChatbotEnabled">{{ t('adminDocutilSearchScopes.fieldChatbotEnabled') }}</label>
                </div>
              </div>
              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="form.qaEnabled" class="form-check-input" type="checkbox" id="formQaEnabled" />
                  <label class="form-check-label" for="formQaEnabled">{{ t('adminDocutilSearchScopes.fieldQaEnabled') }}</label>
                </div>
              </div>
              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="form.keywordSearchEnabled" class="form-check-input" type="checkbox" id="formKeywordSearchEnabled" />
                  <label class="form-check-label" for="formKeywordSearchEnabled">{{ t('adminDocutilSearchScopes.fieldKeywordSearchEnabled') }}</label>
                </div>
              </div>
              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="form.agentEnabled" class="form-check-input" type="checkbox" id="formAgentEnabled" />
                  <label class="form-check-label" for="formAgentEnabled">{{ t('adminDocutilSearchScopes.fieldAgentEnabled') }}</label>
                </div>
              </div>

              <div class="col-md-3">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldChunkSize') }}</label>
                <input v-model.number="form.chunkSize" type="number" class="form-control" min="64" max="8192" />
              </div>
              <div class="col-md-3">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldChunkOverlap') }}</label>
                <input v-model.number="form.chunkOverlap" type="number" class="form-control" min="0" max="1024" />
              </div>
              <div class="col-md-3">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldMaxResults') }}</label>
                <input v-model.number="form.maxResults" type="number" class="form-control" min="1" max="100" />
              </div>
              <div class="col-md-3">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldSimilarityThreshold') }}</label>
                <input v-model.number="form.similarityThreshold" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>

              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldTitleWeight') }}</label>
                <input v-model.number="form.titleWeight" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>
              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldKeywordWeight') }}</label>
                <input v-model.number="form.keywordWeight" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>
              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldContentWeight') }}</label>
                <input v-model.number="form.contentWeight" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>

              <div class="col-12 small text-muted">{{ t('adminDocutilSearchScopes.weightSumHint') }}</div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeFormModal">{{ t('adminDocutilSearchScopes.cancel') }}</button>
            <button type="button" class="btn btn-primary" :disabled="formSaving" @click="onSubmitForm">
              <span v-if="formSaving" class="spinner-border spinner-border-sm me-2"></span>
              {{ formSaving ? t('adminDocutilSearchScopes.saving') : t('adminDocutilSearchScopes.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 환경 설정 모달 -->
    <div
      v-if="showEnvModal"
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      style="background: rgba(0,0,0,0.5)"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ t('adminDocutilSearchScopes.modalEnvTitle') }} — {{ envForm.scopeName }}
            </h5>
            <button type="button" class="btn-close" @click="closeEnvModal"></button>
          </div>
          <div class="modal-body">
            <div class="row g-3">
              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="envForm.chatbotEnabled" class="form-check-input" type="checkbox" id="envChatbotEnabled" />
                  <label class="form-check-label" for="envChatbotEnabled">{{ t('adminDocutilSearchScopes.fieldChatbotEnabled') }}</label>
                </div>
              </div>
              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="envForm.qaEnabled" class="form-check-input" type="checkbox" id="envQaEnabled" />
                  <label class="form-check-label" for="envQaEnabled">{{ t('adminDocutilSearchScopes.fieldQaEnabled') }}</label>
                </div>
              </div>
              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="envForm.keywordSearchEnabled" class="form-check-input" type="checkbox" id="envKeywordEnabled" />
                  <label class="form-check-label" for="envKeywordEnabled">{{ t('adminDocutilSearchScopes.fieldKeywordSearchEnabled') }}</label>
                </div>
              </div>
              <div class="col-md-3">
                <div class="form-check form-switch">
                  <input v-model="envForm.agentEnabled" class="form-check-input" type="checkbox" id="envAgentEnabled" />
                  <label class="form-check-label" for="envAgentEnabled">{{ t('adminDocutilSearchScopes.fieldAgentEnabled') }}</label>
                </div>
              </div>

              <div class="col-md-6">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldChatbotFaqTemplate') }}</label>
                <textarea v-model="envForm.chatbotFaqTemplate" class="form-control" rows="2" maxlength="5000"></textarea>
              </div>
              <div class="col-md-6">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldQaPromptTemplate') }}</label>
                <textarea v-model="envForm.qaPromptTemplate" class="form-control" rows="2" maxlength="5000"></textarea>
              </div>

              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldQaLlmModel') }}</label>
                <input v-model="envForm.qaLlmModel" type="text" class="form-control" maxlength="255" />
              </div>
              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldChunkSize') }}</label>
                <input v-model.number="envForm.chunkSize" type="number" class="form-control" min="64" max="8192" />
              </div>
              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldChunkOverlap') }}</label>
                <input v-model.number="envForm.chunkOverlap" type="number" class="form-control" min="0" max="1024" />
              </div>

              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldTitleWeight') }}</label>
                <input v-model.number="envForm.titleWeight" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>
              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldKeywordWeight') }}</label>
                <input v-model.number="envForm.keywordWeight" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>
              <div class="col-md-4">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldContentWeight') }}</label>
                <input v-model.number="envForm.contentWeight" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>

              <div class="col-md-6">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldMaxResults') }}</label>
                <input v-model.number="envForm.maxResults" type="number" class="form-control" min="1" max="100" />
              </div>
              <div class="col-md-6">
                <label class="form-label small">{{ t('adminDocutilSearchScopes.fieldSimilarityThreshold') }}</label>
                <input v-model.number="envForm.similarityThreshold" type="number" class="form-control" min="0" max="1" step="0.05" />
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeEnvModal">{{ t('adminDocutilSearchScopes.cancel') }}</button>
            <button type="button" class="btn btn-primary" :disabled="envSaving" @click="onSubmitEnv">
              <span v-if="envSaving" class="spinner-border spinner-border-sm me-2"></span>
              {{ envSaving ? t('adminDocutilSearchScopes.saving') : t('adminDocutilSearchScopes.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 상세 모달 -->
    <div
      v-if="showDetailModal && detailItem"
      class="modal d-block"
      tabindex="-1"
      role="dialog"
      style="background: rgba(0,0,0,0.5)"
    >
      <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilSearchScopes.modalDetailTitle') }} — {{ detailItem.name }}</h5>
            <button type="button" class="btn-close" @click="showDetailModal = false"></button>
          </div>
          <div class="modal-body">
            <dl class="row mb-0">
              <dt class="col-sm-3">ID</dt>
              <dd class="col-sm-9"><code class="small">{{ detailItem.id }}</code></dd>

              <dt class="col-sm-3">{{ t('adminDocutilSearchScopes.fieldName') }}</dt>
              <dd class="col-sm-9">{{ detailItem.name }}</dd>

              <dt class="col-sm-3">{{ t('adminDocutilSearchScopes.fieldDescription') }}</dt>
              <dd class="col-sm-9">{{ detailItem.description || t('adminDocutilSearchScopes.noDescription') }}</dd>

              <dt class="col-sm-3">{{ t('adminDocutilSearchScopes.colLocation') }}</dt>
              <dd class="col-sm-9">{{ detailItem.locationPath || t('adminDocutilSearchScopes.noLocation') }}</dd>

              <dt class="col-sm-3">{{ t('adminDocutilSearchScopes.colFeatures') }}</dt>
              <dd class="col-sm-9">
                <span v-if="detailItem.chatbotEnabled" class="badge bg-primary me-1">{{ t('adminDocutilSearchScopes.featureChatbot') }}</span>
                <span v-if="detailItem.qaEnabled" class="badge bg-success me-1">{{ t('adminDocutilSearchScopes.featureQa') }}</span>
                <span v-if="detailItem.keywordSearchEnabled" class="badge bg-info me-1">{{ t('adminDocutilSearchScopes.featureKeyword') }}</span>
                <span v-if="detailItem.agentEnabled" class="badge bg-warning text-dark me-1">{{ t('adminDocutilSearchScopes.featureAgent') }}</span>
              </dd>

              <dt class="col-sm-3">Chunk</dt>
              <dd class="col-sm-9">size={{ detailItem.chunkSize }}, overlap={{ detailItem.chunkOverlap }}</dd>

              <dt class="col-sm-3">Weights</dt>
              <dd class="col-sm-9">
                title={{ detailItem.titleWeight }}, keyword={{ detailItem.keywordWeight }}, content={{ detailItem.contentWeight }}
              </dd>

              <dt class="col-sm-3">Threshold</dt>
              <dd class="col-sm-9">
                max={{ detailItem.maxResults }}, similarity={{ detailItem.similarityThreshold }}
              </dd>

              <dt class="col-sm-3">{{ t('adminDocutilSearchScopes.modalCreatedBy') }}</dt>
              <dd class="col-sm-9"><code class="small">{{ detailItem.createdBy }}</code></dd>

              <dt class="col-sm-3">{{ t('adminDocutilSearchScopes.modalCreatedAt') }}</dt>
              <dd class="col-sm-9">{{ formatDate(detailItem.createdAt) }}</dd>

              <dt class="col-sm-3">{{ t('adminDocutilSearchScopes.modalUpdatedAt') }}</dt>
              <dd class="col-sm-9">{{ formatDate(detailItem.updatedAt) }}</dd>

              <dt v-if="detailValidId" class="col-sm-3">{{ t('adminDocutilSearchScopes.validIdLabel') }}</dt>
              <dd v-if="detailValidId" class="col-sm-9"><pre class="small mb-0">{{ JSON.stringify(detailValidId, null, 2) }}</pre></dd>
            </dl>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-info" @click="onLoadValidId" :disabled="validIdLoading">
              <span v-if="validIdLoading" class="spinner-border spinner-border-sm me-2"></span>
              {{ t('adminDocutilSearchScopes.showValidId') }}
            </button>
            <button type="button" class="btn btn-secondary" @click="showDetailModal = false">{{ t('adminDocutilSearchScopes.cancel') }}</button>
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
  listSearchScopes,
  listSearchScopeOptions,
  listSearchScopeLocations,
  createSearchScope,
  updateSearchScope,
  deleteSearchScope,
  updateSearchScopeEnvironment,
  getSearchScopeValidId
} from '@/services/docutilService'
import type {
  DocUtilSearchScopeSummary,
  DocUtilSearchScopeList,
  DocUtilSearchScopeOption,
  DocUtilLocationOption,
  DocUtilCreateScopeRequest,
  DocUtilUpdateScopeRequest,
  DocUtilUpdateScopeEnvironmentRequest
} from '@/services/docutilService'

const { t } = useI18n()

// ── 상태 ──
type Tab = 'scopes' | 'locations' | 'options'
const activeTab = ref<Tab>('scopes')

const loading = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const scopeList = ref<DocUtilSearchScopeList | null>(null)
const page = ref(1)
const size = ref(20)
const totalPages = computed(() => {
  if (!scopeList.value || scopeList.value.total === 0) return 1
  return Math.max(1, Math.ceil(scopeList.value.total / scopeList.value.size))
})

// Locations / Options
const locationType = ref<'project' | 'board' | 'folder'>('project')
const locations = ref<DocUtilLocationOption[]>([])
const locationsLoading = ref(false)
const scopeOptions = ref<DocUtilSearchScopeOption[]>([])
const optionsLoading = ref(false)

// 폼 모달 상태
const showFormModal = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const formSaving = ref(false)
const formLocations = ref<DocUtilLocationOption[]>([])
const formLocationsLoading = ref(false)
const editingScopeId = ref<string | null>(null)

interface ScopeFormState {
  name: string
  description: string
  locationKind: '' | 'project' | 'board' | 'folder'
  locationId: string
  chatbotEnabled: boolean
  qaEnabled: boolean
  keywordSearchEnabled: boolean
  agentEnabled: boolean
  chunkSize: number
  chunkOverlap: number
  titleWeight: number
  keywordWeight: number
  contentWeight: number
  maxResults: number
  similarityThreshold: number
}

const form = ref<ScopeFormState>(buildEmptyForm())

function buildEmptyForm(): ScopeFormState {
  return {
    name: '',
    description: '',
    locationKind: '',
    locationId: '',
    chatbotEnabled: false,
    qaEnabled: false,
    keywordSearchEnabled: false,
    agentEnabled: false,
    chunkSize: 512,
    chunkOverlap: 64,
    titleWeight: 0.3,
    keywordWeight: 0.3,
    contentWeight: 0.4,
    maxResults: 10,
    similarityThreshold: 0.5
  }
}

// 환경 모달 상태
const showEnvModal = ref(false)
const envSaving = ref(false)
interface EnvFormState {
  scopeId: string
  scopeName: string
  chatbotEnabled: boolean
  chatbotFaqTemplate: string
  qaEnabled: boolean
  qaPromptTemplate: string
  qaLlmModel: string
  keywordSearchEnabled: boolean
  agentEnabled: boolean
  chunkSize: number
  chunkOverlap: number
  titleWeight: number
  keywordWeight: number
  contentWeight: number
  maxResults: number
  similarityThreshold: number
}
const envForm = ref<EnvFormState>(buildEmptyEnvForm())

function buildEmptyEnvForm(): EnvFormState {
  return {
    scopeId: '',
    scopeName: '',
    chatbotEnabled: false,
    chatbotFaqTemplate: '',
    qaEnabled: false,
    qaPromptTemplate: '',
    qaLlmModel: '',
    keywordSearchEnabled: false,
    agentEnabled: false,
    chunkSize: 512,
    chunkOverlap: 64,
    titleWeight: 0.3,
    keywordWeight: 0.3,
    contentWeight: 0.4,
    maxResults: 10,
    similarityThreshold: 0.5
  }
}

// 상세 모달
const showDetailModal = ref(false)
const detailItem = ref<DocUtilSearchScopeSummary | null>(null)
const detailValidId = ref<Record<string, unknown> | null>(null)
const validIdLoading = ref(false)

// ── 라이프사이클 ──
onMounted(() => {
  void loadScopes()
})

// ── 메서드 ──
function capitalize(s: string): string {
  if (!s) return s
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('ko-KR', { hour12: false })
  } catch {
    return iso
  }
}

function extractMessage(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const response = (err as { response?: { data?: { message?: string } } }).response
    if (response?.data?.message) return response.data.message
  }
  if (err instanceof Error) return err.message
  return t('adminDocutilSearchScopes.errorUnknown')
}

async function loadScopes(force = false): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    scopeList.value = await listSearchScopes(page.value, size.value)
    if (force) {
      successMessage.value = ''
    }
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    loading.value = false
  }
}

async function loadLocations(): Promise<void> {
  locationsLoading.value = true
  try {
    locations.value = await listSearchScopeLocations(locationType.value)
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    locationsLoading.value = false
  }
}

async function loadOptions(): Promise<void> {
  optionsLoading.value = true
  try {
    scopeOptions.value = await listSearchScopeOptions()
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    optionsLoading.value = false
  }
}

function onSwitchToLocations(): void {
  activeTab.value = 'locations'
  if (locations.value.length === 0) {
    void loadLocations()
  }
}

function onSwitchToOptions(): void {
  activeTab.value = 'options'
  if (scopeOptions.value.length === 0) {
    void loadOptions()
  }
}

function onChangeLocationType(t: 'project' | 'board' | 'folder'): void {
  locationType.value = t
  void loadLocations()
}

function goToPage(p: number): void {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  void loadScopes()
}

function onPageSizeChange(): void {
  page.value = 1
  void loadScopes()
}

// ── 모달 — 생성/수정 ──
function openCreateModal(): void {
  formMode.value = 'create'
  editingScopeId.value = null
  form.value = buildEmptyForm()
  formLocations.value = []
  showFormModal.value = true
}

function openEditModal(item: DocUtilSearchScopeSummary): void {
  formMode.value = 'edit'
  editingScopeId.value = item.id
  const kind: '' | 'project' | 'board' | 'folder' = item.projectId
    ? 'project'
    : item.boardId
      ? 'board'
      : item.folderId
        ? 'folder'
        : ''
  form.value = {
    name: item.name,
    description: item.description ?? '',
    locationKind: kind,
    locationId: item.projectId ?? item.boardId ?? item.folderId ?? '',
    chatbotEnabled: item.chatbotEnabled,
    qaEnabled: item.qaEnabled,
    keywordSearchEnabled: item.keywordSearchEnabled,
    agentEnabled: item.agentEnabled,
    chunkSize: item.chunkSize,
    chunkOverlap: item.chunkOverlap,
    titleWeight: item.titleWeight,
    keywordWeight: item.keywordWeight,
    contentWeight: item.contentWeight,
    maxResults: item.maxResults,
    similarityThreshold: item.similarityThreshold
  }
  if (kind) {
    void loadFormLocations(kind)
  } else {
    formLocations.value = []
  }
  showFormModal.value = true
}

function closeFormModal(): void {
  showFormModal.value = false
}

async function onFormLocationKindChange(): Promise<void> {
  form.value.locationId = ''
  if (!form.value.locationKind) {
    formLocations.value = []
    return
  }
  await loadFormLocations(form.value.locationKind)
}

async function loadFormLocations(kind: 'project' | 'board' | 'folder'): Promise<void> {
  formLocationsLoading.value = true
  try {
    formLocations.value = await listSearchScopeLocations(kind)
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    formLocationsLoading.value = false
  }
}

function validateForm(): string | null {
  const f = form.value
  if (!f.name.trim() || f.name.trim().length > 255) {
    return t('adminDocutilSearchScopes.validationName')
  }
  for (const w of [f.titleWeight, f.keywordWeight, f.contentWeight]) {
    if (w < 0 || w > 1) return t('adminDocutilSearchScopes.validationWeight')
  }
  if (f.similarityThreshold < 0 || f.similarityThreshold > 1) {
    return t('adminDocutilSearchScopes.validationSimilarity')
  }
  return null
}

function buildLocationPayload(): { projectId: string | null; boardId: string | null; folderId: string | null } {
  const f = form.value
  const id = f.locationId || null
  return {
    projectId: f.locationKind === 'project' ? id : null,
    boardId: f.locationKind === 'board' ? id : null,
    folderId: f.locationKind === 'folder' ? id : null
  }
}

async function onSubmitForm(): Promise<void> {
  const validationError = validateForm()
  if (validationError) {
    errorMessage.value = validationError
    return
  }
  formSaving.value = true
  errorMessage.value = ''
  try {
    const f = form.value
    const loc = buildLocationPayload()
    if (formMode.value === 'create') {
      const req: DocUtilCreateScopeRequest = {
        name: f.name.trim(),
        description: f.description.trim() || null,
        projectId: loc.projectId,
        boardId: loc.boardId,
        folderId: loc.folderId,
        chatbotEnabled: f.chatbotEnabled,
        qaEnabled: f.qaEnabled,
        keywordSearchEnabled: f.keywordSearchEnabled,
        agentEnabled: f.agentEnabled,
        chunkSize: f.chunkSize,
        chunkOverlap: f.chunkOverlap,
        titleWeight: f.titleWeight,
        keywordWeight: f.keywordWeight,
        contentWeight: f.contentWeight,
        maxResults: f.maxResults,
        similarityThreshold: f.similarityThreshold
      }
      await createSearchScope(req)
      successMessage.value = t('adminDocutilSearchScopes.createSuccess')
    } else if (editingScopeId.value) {
      const req: DocUtilUpdateScopeRequest = {
        name: f.name.trim(),
        description: f.description.trim() || null,
        projectId: loc.projectId,
        boardId: loc.boardId,
        folderId: loc.folderId,
        chatbotEnabled: f.chatbotEnabled,
        qaEnabled: f.qaEnabled,
        keywordSearchEnabled: f.keywordSearchEnabled,
        agentEnabled: f.agentEnabled,
        chunkSize: f.chunkSize,
        chunkOverlap: f.chunkOverlap,
        titleWeight: f.titleWeight,
        keywordWeight: f.keywordWeight,
        contentWeight: f.contentWeight,
        maxResults: f.maxResults,
        similarityThreshold: f.similarityThreshold
      }
      await updateSearchScope(editingScopeId.value, req)
      successMessage.value = t('adminDocutilSearchScopes.updateSuccess')
    }
    closeFormModal()
    await loadScopes()
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    formSaving.value = false
  }
}

// ── 모달 — 환경 설정 ──
function openEnvModal(item: DocUtilSearchScopeSummary): void {
  envForm.value = {
    scopeId: item.id,
    scopeName: item.name,
    chatbotEnabled: item.chatbotEnabled,
    chatbotFaqTemplate: item.chatbotFaqTemplate ?? '',
    qaEnabled: item.qaEnabled,
    qaPromptTemplate: item.qaPromptTemplate ?? '',
    qaLlmModel: item.qaLlmModel ?? '',
    keywordSearchEnabled: item.keywordSearchEnabled,
    agentEnabled: item.agentEnabled,
    chunkSize: item.chunkSize,
    chunkOverlap: item.chunkOverlap,
    titleWeight: item.titleWeight,
    keywordWeight: item.keywordWeight,
    contentWeight: item.contentWeight,
    maxResults: item.maxResults,
    similarityThreshold: item.similarityThreshold
  }
  showEnvModal.value = true
}

function closeEnvModal(): void {
  showEnvModal.value = false
  envForm.value = buildEmptyEnvForm()
}

async function onSubmitEnv(): Promise<void> {
  const e = envForm.value
  for (const w of [e.titleWeight, e.keywordWeight, e.contentWeight]) {
    if (w < 0 || w > 1) {
      errorMessage.value = t('adminDocutilSearchScopes.validationWeight')
      return
    }
  }
  if (e.similarityThreshold < 0 || e.similarityThreshold > 1) {
    errorMessage.value = t('adminDocutilSearchScopes.validationSimilarity')
    return
  }
  envSaving.value = true
  errorMessage.value = ''
  try {
    const req: DocUtilUpdateScopeEnvironmentRequest = {
      chatbotEnabled: e.chatbotEnabled,
      chatbotFaqTemplate: e.chatbotFaqTemplate || null,
      qaEnabled: e.qaEnabled,
      qaPromptTemplate: e.qaPromptTemplate || null,
      qaLlmModel: e.qaLlmModel || null,
      keywordSearchEnabled: e.keywordSearchEnabled,
      agentEnabled: e.agentEnabled,
      chunkSize: e.chunkSize,
      chunkOverlap: e.chunkOverlap,
      titleWeight: e.titleWeight,
      keywordWeight: e.keywordWeight,
      contentWeight: e.contentWeight,
      maxResults: e.maxResults,
      similarityThreshold: e.similarityThreshold
    }
    await updateSearchScopeEnvironment(e.scopeId, req)
    successMessage.value = t('adminDocutilSearchScopes.envUpdateSuccess')
    closeEnvModal()
    await loadScopes()
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    envSaving.value = false
  }
}

// ── 삭제 ──
async function onDelete(item: DocUtilSearchScopeSummary): Promise<void> {
  // eslint-disable-next-line no-alert
  if (!window.confirm(t('adminDocutilSearchScopes.deleteConfirm', { name: item.name }))) {
    return
  }
  errorMessage.value = ''
  try {
    await deleteSearchScope(item.id)
    successMessage.value = t('adminDocutilSearchScopes.deleteSuccess')
    await loadScopes()
  } catch (err) {
    errorMessage.value = extractMessage(err)
  }
}

// ── 상세 ──
function openDetail(item: DocUtilSearchScopeSummary): void {
  detailItem.value = item
  detailValidId.value = null
  showDetailModal.value = true
}

async function onLoadValidId(): Promise<void> {
  if (!detailItem.value) return
  validIdLoading.value = true
  try {
    detailValidId.value = await getSearchScopeValidId(detailItem.value.id)
  } catch (err) {
    errorMessage.value = extractMessage(err)
  } finally {
    validIdLoading.value = false
  }
}
</script>

<style scoped>
.admin-docutil-search-scopes {
  max-width: 1400px;
  margin: 0 auto;
}
.modal {
  overflow-y: auto;
}
</style>
