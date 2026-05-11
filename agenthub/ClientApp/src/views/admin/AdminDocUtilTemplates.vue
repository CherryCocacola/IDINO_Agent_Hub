<template>
  <div class="admin-docutil-doctemplates container-fluid py-4">
    <!-- 헤더 -->
    <header class="mb-3 d-flex align-items-start justify-content-between flex-wrap gap-2">
      <div>
        <h1 class="h3 mb-1">{{ t('adminDocutilTemplates.title') }}</h1>
        <p class="text-muted mb-0">{{ t('adminDocutilTemplates.subtitle') }}</p>
      </div>
      <div class="d-flex gap-2 flex-wrap">
        <button type="button" class="btn btn-outline-secondary" @click="loadList()" :disabled="loading">
          <i class="bi bi-arrow-clockwise me-1"></i>{{ t('adminDocutilTemplates.refresh') }}
        </button>
        <button type="button" class="btn btn-primary" @click="openCreateDialog">
          <i class="bi bi-plus-lg me-1"></i>{{ t('adminDocutilTemplates.newTemplate') }}
        </button>
        <button type="button" class="btn btn-outline-primary" @click="openUploadDialog('standard')">
          <i class="bi bi-upload me-1"></i>{{ t('adminDocutilTemplates.uploadStandard') }}
        </button>
        <button type="button" class="btn btn-outline-primary" @click="openUploadDialog('blank')">
          <i class="bi bi-file-earmark-plus me-1"></i>{{ t('adminDocutilTemplates.uploadBlank') }}
        </button>
        <button type="button" class="btn btn-outline-primary" @click="openUploadDialog('smart')">
          <i class="bi bi-stars me-1"></i>{{ t('adminDocutilTemplates.uploadSmart') }}
        </button>
      </div>
    </header>

    <!-- 알림 -->
    <div v-if="successMessage" class="alert alert-success alert-dismissible" role="alert">
      {{ successMessage }}
      <button type="button" class="btn-close" @click="successMessage = ''" aria-label="close"></button>
    </div>
    <div v-if="errorMessage" class="alert alert-danger alert-dismissible" role="alert">
      {{ errorMessage }}
      <button type="button" class="btn-close" @click="errorMessage = ''" aria-label="close"></button>
    </div>

    <!-- 필터 -->
    <div class="card mb-3">
      <div class="card-body">
        <div class="row g-2 align-items-end">
          <div class="col-md-5">
            <label class="form-label small">{{ t('adminDocutilTemplates.filterTemplateType') }}</label>
            <input
              v-model="templateTypeInput"
              type="text"
              class="form-control"
              :placeholder="t('adminDocutilTemplates.filterTemplateTypePlaceholder')"
              @keyup.enter="onApplyFilters"
            />
          </div>
          <div class="col-md-2">
            <label class="form-label small">{{ t('adminDocutilTemplates.pageSize') }}</label>
            <select v-model.number="size" class="form-select" @change="onPageSizeChange">
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
              <option :value="100">100</option>
            </select>
          </div>
          <div class="col-md-5 d-flex gap-2">
            <button type="button" class="btn btn-secondary flex-fill" @click="onClearFilters">
              {{ t('adminDocutilTemplates.clearFilters') }}
            </button>
            <button type="button" class="btn btn-primary flex-fill" @click="onApplyFilters">
              {{ t('adminDocutilTemplates.applyFilters') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 표 -->
    <div class="card">
      <div class="card-body p-0">
        <div v-if="loading" class="text-center py-5 text-muted">
          <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilTemplates.loading') }}
        </div>
        <table v-else-if="items.length > 0" class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th>{{ t('adminDocutilTemplates.colName') }}</th>
              <th class="d-none d-md-table-cell">{{ t('adminDocutilTemplates.colTemplateType') }}</th>
              <th class="d-none d-md-table-cell">{{ t('adminDocutilTemplates.colOutputFormat') }}</th>
              <th class="d-none d-md-table-cell">{{ t('adminDocutilTemplates.colRenderingMode') }}</th>
              <th class="d-none d-md-table-cell text-center">{{ t('adminDocutilTemplates.colIsActive') }}</th>
              <th class="d-none d-lg-table-cell">{{ t('adminDocutilTemplates.colUpdatedAt') }}</th>
              <th class="text-end">{{ t('adminDocutilTemplates.colActions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tpl in items" :key="tpl.id">
              <td class="text-truncate" style="max-width: 320px">
                <strong>{{ tpl.name }}</strong>
                <small v-if="tpl.description" class="d-block text-muted text-truncate">{{ tpl.description }}</small>
              </td>
              <td class="d-none d-md-table-cell">
                <span class="badge bg-light text-dark">{{ tpl.templateType }}</span>
              </td>
              <td class="d-none d-md-table-cell">
                <span class="badge bg-info text-dark">{{ tpl.outputFormat }}</span>
              </td>
              <td class="d-none d-md-table-cell">
                <span class="badge bg-secondary">{{ tpl.renderingMode }}</span>
              </td>
              <td class="d-none d-md-table-cell text-center">
                <span class="badge" :class="tpl.isActive ? 'bg-success' : 'bg-secondary'">
                  {{ tpl.isActive ? t('adminDocutilTemplates.active') : t('adminDocutilTemplates.inactive') }}
                </span>
              </td>
              <td class="d-none d-lg-table-cell text-muted small">{{ formatDate(tpl.updatedAt) }}</td>
              <td class="text-end">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary me-1"
                  @click="openDetail(tpl)"
                  :title="t('adminDocutilTemplates.viewDetail')"
                >
                  <i class="bi bi-eye"></i>
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-primary me-1"
                  @click="onPreview(tpl)"
                  :title="t('adminDocutilTemplates.preview')"
                  :disabled="!tpl.templateStoragePath"
                >
                  <i class="bi bi-download"></i>
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-danger"
                  @click="onDelete(tpl)"
                  :title="t('adminDocutilTemplates.delete')"
                >
                  <i class="bi bi-trash"></i>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-5 text-muted">
          {{ t('adminDocutilTemplates.emptyList') }}
        </div>
      </div>
    </div>

    <!-- 페이지네이션 -->
    <div class="d-flex justify-content-between align-items-center mt-3">
      <small class="text-muted">{{ t('adminDocutilTemplates.totalCount', { total }) }}</small>
      <div class="d-flex align-items-center gap-2">
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary"
          :disabled="page <= 1 || loading"
          @click="onChangePage(page - 1)"
        >
          <i class="bi bi-chevron-left"></i>{{ t('adminDocutilTemplates.prevPage') }}
        </button>
        <span class="small text-muted">{{ t('adminDocutilTemplates.page') }} {{ page }} / {{ totalPages }}</span>
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary"
          :disabled="page >= totalPages || loading"
          @click="onChangePage(page + 1)"
        >
          {{ t('adminDocutilTemplates.nextPage') }}<i class="bi bi-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- 상세 모달 (탭 구조) -->
    <div v-if="detailModal.open" class="modal fade show d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-xl modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ t('adminDocutilTemplates.detailTitle') }}
              <small v-if="detailModal.template" class="text-muted ms-2">{{ detailModal.template.name }}</small>
            </h5>
            <button type="button" class="btn-close" @click="closeDetail"></button>
          </div>
          <div class="modal-body">
            <ul class="nav nav-tabs mb-3" role="tablist">
              <li class="nav-item">
                <button type="button" class="nav-link" :class="{ active: detailTab === 'info' }" @click="detailTab = 'info'">
                  {{ t('adminDocutilTemplates.tabInfo') }}
                </button>
              </li>
              <li class="nav-item">
                <button type="button" class="nav-link" :class="{ active: detailTab === 'variables' }" @click="onSwitchTab('variables')">
                  {{ t('adminDocutilTemplates.tabVariables') }}
                </button>
              </li>
              <li class="nav-item">
                <button type="button" class="nav-link" :class="{ active: detailTab === 'structure' }" @click="onSwitchTab('structure')">
                  {{ t('adminDocutilTemplates.tabStructure') }}
                </button>
              </li>
              <li class="nav-item">
                <button type="button" class="nav-link" :class="{ active: detailTab === 'autoFill' }" @click="detailTab = 'autoFill'">
                  {{ t('adminDocutilTemplates.tabAutoFill') }}
                </button>
              </li>
              <li class="nav-item">
                <button type="button" class="nav-link" :class="{ active: detailTab === 'convert' }" @click="detailTab = 'convert'">
                  {{ t('adminDocutilTemplates.tabConvert') }}
                </button>
              </li>
              <li class="nav-item">
                <button type="button" class="nav-link" :class="{ active: detailTab === 'mapping' }" @click="detailTab = 'mapping'">
                  {{ t('adminDocutilTemplates.tabMapping') }}
                </button>
              </li>
            </ul>

            <!-- 정보 + 편집 -->
            <div v-if="detailTab === 'info' && detailModal.template">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label small">{{ t('adminDocutilTemplates.fieldName') }}</label>
                  <input v-model="editForm.name" type="text" class="form-control" maxlength="255" />
                </div>
                <div class="col-md-6">
                  <label class="form-label small">{{ t('adminDocutilTemplates.fieldTemplateType') }}</label>
                  <input v-model="editForm.templateType" type="text" class="form-control" maxlength="100" />
                </div>
                <div class="col-md-12">
                  <label class="form-label small">{{ t('adminDocutilTemplates.fieldDescription') }}</label>
                  <textarea v-model="editForm.description" class="form-control" rows="2" maxlength="2000"></textarea>
                </div>
                <div class="col-md-4">
                  <label class="form-label small">{{ t('adminDocutilTemplates.fieldOutputFormat') }}</label>
                  <input v-model="editForm.outputFormat" type="text" class="form-control" maxlength="20" />
                </div>
                <div class="col-md-4">
                  <label class="form-label small">{{ t('adminDocutilTemplates.fieldTone') }}</label>
                  <input v-model="editForm.tone" type="text" class="form-control" maxlength="20" />
                </div>
                <div class="col-md-4">
                  <label class="form-label small">{{ t('adminDocutilTemplates.fieldRenderingMode') }}</label>
                  <input v-model="editForm.renderingMode" type="text" class="form-control" maxlength="20" />
                </div>
                <div class="col-md-12">
                  <label class="form-label small">{{ t('adminDocutilTemplates.fieldSamplePrompt') }}</label>
                  <textarea v-model="editForm.samplePrompt" class="form-control" rows="2" maxlength="5000"></textarea>
                </div>
                <div class="col-md-12">
                  <div class="form-check">
                    <input v-model="editForm.isActive" class="form-check-input" type="checkbox" id="tplIsActive" />
                    <label class="form-check-label" for="tplIsActive">
                      {{ t('adminDocutilTemplates.fieldIsActive') }}
                    </label>
                  </div>
                </div>
                <div class="col-md-12">
                  <hr />
                  <dl class="row mb-0">
                    <dt class="col-sm-3">{{ t('adminDocutilTemplates.metaId') }}</dt>
                    <dd class="col-sm-9 text-muted small">{{ detailModal.template.id }}</dd>
                    <dt class="col-sm-3">{{ t('adminDocutilTemplates.metaOrganizationId') }}</dt>
                    <dd class="col-sm-9 text-muted small">{{ detailModal.template.organizationId }}</dd>
                    <dt class="col-sm-3">{{ t('adminDocutilTemplates.metaStoragePath') }}</dt>
                    <dd class="col-sm-9 text-muted small text-break">{{ detailModal.template.templateStoragePath || '—' }}</dd>
                    <dt class="col-sm-3">{{ t('adminDocutilTemplates.metaCreatedAt') }}</dt>
                    <dd class="col-sm-9 text-muted small">{{ formatDate(detailModal.template.createdAt) }}</dd>
                    <dt class="col-sm-3">{{ t('adminDocutilTemplates.metaUpdatedAt') }}</dt>
                    <dd class="col-sm-9 text-muted small">{{ formatDate(detailModal.template.updatedAt) }}</dd>
                  </dl>
                </div>
              </div>
            </div>

            <!-- 변수 메타 편집 -->
            <div v-if="detailTab === 'variables'">
              <div v-if="variablesLoading" class="text-center py-3 text-muted">
                <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilTemplates.loading') }}
              </div>
              <template v-else>
                <p class="text-muted small mb-3">{{ t('adminDocutilTemplates.variablesHint') }}</p>
                <div v-if="variableList.length === 0" class="text-muted">
                  {{ t('adminDocutilTemplates.variablesEmpty') }}
                </div>
                <table v-else class="table table-sm align-middle">
                  <thead>
                    <tr>
                      <th>{{ t('adminDocutilTemplates.varName') }}</th>
                      <th>{{ t('adminDocutilTemplates.varType') }}</th>
                      <th>{{ t('adminDocutilTemplates.varLabel') }}</th>
                      <th>{{ t('adminDocutilTemplates.varCategory') }}</th>
                      <th class="text-center">{{ t('adminDocutilTemplates.varRequired') }}</th>
                      <th class="text-end"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(v, i) in variableList" :key="v.name + i">
                      <td><input v-model="v.name" type="text" class="form-control form-control-sm" /></td>
                      <td>
                        <select v-model="v.varType" class="form-select form-select-sm">
                          <option value="string">string</option>
                          <option value="array">array</option>
                          <option value="boolean">boolean</option>
                          <option value="image">image</option>
                          <option value="date">date</option>
                        </select>
                      </td>
                      <td><input v-model="v.label" type="text" class="form-control form-control-sm" /></td>
                      <td>
                        <select v-model="v.category" class="form-select form-select-sm">
                          <option value="user_input">user_input</option>
                          <option value="session_auto">session_auto</option>
                          <option value="ai_generated">ai_generated</option>
                        </select>
                      </td>
                      <td class="text-center"><input v-model="v.required" type="checkbox" class="form-check-input" /></td>
                      <td class="text-end">
                        <button type="button" class="btn btn-sm btn-outline-danger" @click="onRemoveVariable(i)">
                          <i class="bi bi-trash"></i>
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <button type="button" class="btn btn-sm btn-outline-primary mt-2" @click="onAddVariable">
                  <i class="bi bi-plus-lg me-1"></i>{{ t('adminDocutilTemplates.addVariable') }}
                </button>
                <button
                  type="button"
                  class="btn btn-sm btn-primary mt-2 ms-2"
                  :disabled="saving"
                  @click="onSaveVariables"
                >
                  <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
                  {{ t('adminDocutilTemplates.saveVariables') }}
                </button>
              </template>
            </div>

            <!-- 구조 -->
            <div v-if="detailTab === 'structure'">
              <div v-if="structureLoading" class="text-center py-3 text-muted">
                <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilTemplates.loading') }}
              </div>
              <template v-else>
                <p class="text-muted small mb-3">{{ t('adminDocutilTemplates.structureHint') }}</p>
                <pre class="bg-light p-3 small" style="max-height: 480px; overflow:auto">{{ structureJson }}</pre>
              </template>
            </div>

            <!-- AI 자동채움 -->
            <div v-if="detailTab === 'autoFill'">
              <p class="text-muted small mb-3">{{ t('adminDocutilTemplates.autoFillHint') }}</p>
              <div class="mb-3">
                <label class="form-label">{{ t('adminDocutilTemplates.autoFillSourceIds') }}</label>
                <textarea
                  v-model="autoFillForm.sourceIdsRaw"
                  class="form-control"
                  rows="3"
                  :placeholder="t('adminDocutilTemplates.autoFillSourceIdsPlaceholder')"
                ></textarea>
                <small class="text-muted">{{ t('adminDocutilTemplates.autoFillSourceIdsHelp') }}</small>
              </div>
              <div class="mb-3">
                <label class="form-label">{{ t('adminDocutilTemplates.autoFillPrompt') }}</label>
                <textarea
                  v-model="autoFillForm.aiPrompt"
                  class="form-control"
                  rows="2"
                  maxlength="5000"
                ></textarea>
              </div>
              <button
                type="button"
                class="btn btn-primary"
                :disabled="autoFillLoading"
                @click="onAutoFill"
              >
                <span v-if="autoFillLoading" class="spinner-border spinner-border-sm me-2"></span>
                {{ t('adminDocutilTemplates.runAutoFill') }}
              </button>
              <hr />
              <p class="small">{{ t('adminDocutilTemplates.autoFillResult') }}</p>
              <pre class="bg-light p-3 small" style="max-height: 320px; overflow:auto">{{ autoFillResultJson }}</pre>
            </div>

            <!-- 변환 (Convert) -->
            <div v-if="detailTab === 'convert'">
              <p class="text-muted small mb-3">{{ t('adminDocutilTemplates.convertHint') }}</p>
              <div class="mb-3">
                <label class="form-label">{{ t('adminDocutilTemplates.convertAnalysis') }}</label>
                <textarea
                  v-model="convertForm.aiAnalysisRaw"
                  class="form-control font-monospace small"
                  rows="10"
                  :placeholder="convertPlaceholder"
                ></textarea>
                <small class="text-muted">{{ t('adminDocutilTemplates.convertAnalysisHelp') }}</small>
              </div>
              <button
                type="button"
                class="btn btn-primary"
                :disabled="convertLoading"
                @click="onConvert"
              >
                <span v-if="convertLoading" class="spinner-border spinner-border-sm me-2"></span>
                {{ t('adminDocutilTemplates.runConvert') }}
              </button>
            </div>

            <!-- 변수 매핑 적용 -->
            <div v-if="detailTab === 'mapping'">
              <p class="text-muted small mb-3">{{ t('adminDocutilTemplates.mappingHint') }}</p>
              <div class="mb-3">
                <label class="form-label">{{ t('adminDocutilTemplates.mappingJson') }}</label>
                <textarea
                  v-model="mappingForm.mappingsRaw"
                  class="form-control font-monospace small"
                  rows="12"
                  :placeholder="mappingPlaceholder"
                ></textarea>
                <small class="text-muted">{{ t('adminDocutilTemplates.mappingJsonHelp') }}</small>
              </div>
              <button
                type="button"
                class="btn btn-primary"
                :disabled="mappingLoading"
                @click="onApplyMapping"
              >
                <span v-if="mappingLoading" class="spinner-border spinner-border-sm me-2"></span>
                {{ t('adminDocutilTemplates.runApplyMapping') }}
              </button>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeDetail">
              {{ t('adminDocutilTemplates.cancel') }}
            </button>
            <button
              v-if="detailTab === 'info'"
              type="button"
              class="btn btn-primary"
              :disabled="saving"
              @click="onSaveInfo"
            >
              <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
              {{ saving ? t('adminDocutilTemplates.saving') : t('adminDocutilTemplates.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="detailModal.open" class="modal-backdrop fade show"></div>

    <!-- 생성 모달 (JSON, 메타데이터만) -->
    <div v-if="createModal.open" class="modal fade show d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilTemplates.createTitle') }}</h5>
            <button type="button" class="btn-close" @click="createModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label">
                  {{ t('adminDocutilTemplates.fieldName') }} <span class="text-danger">*</span>
                </label>
                <input v-model="createForm.name" type="text" class="form-control" maxlength="255" />
              </div>
              <div class="col-md-6">
                <label class="form-label">
                  {{ t('adminDocutilTemplates.fieldTemplateType') }} <span class="text-danger">*</span>
                </label>
                <input v-model="createForm.templateType" type="text" class="form-control" maxlength="100" />
              </div>
              <div class="col-md-12">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldDescription') }}</label>
                <textarea v-model="createForm.description" class="form-control" rows="2" maxlength="2000"></textarea>
              </div>
              <div class="col-md-4">
                <label class="form-label">
                  {{ t('adminDocutilTemplates.fieldOutputFormat') }} <span class="text-danger">*</span>
                </label>
                <input v-model="createForm.outputFormat" type="text" class="form-control" maxlength="20" />
              </div>
              <div class="col-md-4">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldTone') }}</label>
                <input v-model="createForm.tone" type="text" class="form-control" maxlength="20" />
              </div>
              <div class="col-md-4">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldRenderingMode') }}</label>
                <input v-model="createForm.renderingMode" type="text" class="form-control" maxlength="20" />
              </div>
              <div class="col-md-12">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldSamplePrompt') }}</label>
                <textarea v-model="createForm.samplePrompt" class="form-control" rows="2" maxlength="5000"></textarea>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="createModal.open = false">
              {{ t('adminDocutilTemplates.cancel') }}
            </button>
            <button type="button" class="btn btn-primary" :disabled="creating" @click="onCreate">
              <span v-if="creating" class="spinner-border spinner-border-sm me-2"></span>
              {{ creating ? t('adminDocutilTemplates.saving') : t('adminDocutilTemplates.create') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="createModal.open" class="modal-backdrop fade show"></div>

    <!-- 업로드 모달 (3종 — 일반/빈양식/스마트) -->
    <div v-if="uploadModal.open" class="modal fade show d-block" tabindex="-1" role="dialog">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ uploadModalTitle }}</h5>
            <button type="button" class="btn-close" @click="uploadModal.open = false"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted small">{{ uploadModalHint }}</p>
            <div class="row g-3">
              <div v-if="uploadModal.mode !== 'smart'" class="col-md-6">
                <label class="form-label">
                  {{ t('adminDocutilTemplates.fieldTemplateType') }} <span class="text-danger">*</span>
                </label>
                <input v-model="uploadForm.templateType" type="text" class="form-control" maxlength="100" />
              </div>
              <div v-else class="col-md-6">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldTemplateTypeOptional') }}</label>
                <input v-model="uploadForm.templateType" type="text" class="form-control" maxlength="100" />
              </div>
              <div v-if="uploadModal.mode !== 'smart'" class="col-md-6">
                <label class="form-label">
                  {{ t('adminDocutilTemplates.fieldOutputFormat') }} <span class="text-danger">*</span>
                </label>
                <input v-model="uploadForm.outputFormat" type="text" class="form-control" maxlength="20" />
              </div>
              <div class="col-md-6">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldName') }}</label>
                <input v-model="uploadForm.name" type="text" class="form-control" maxlength="255" />
              </div>
              <div class="col-md-12">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldDescription') }}</label>
                <textarea v-model="uploadForm.description" class="form-control" rows="2" maxlength="2000"></textarea>
              </div>
              <div class="col-md-6">
                <label class="form-label">{{ t('adminDocutilTemplates.fieldTone') }}</label>
                <input v-model="uploadForm.tone" type="text" class="form-control" maxlength="20" />
              </div>
              <div class="col-md-12">
                <label class="form-label">
                  {{ t('adminDocutilTemplates.fieldFile') }} <span class="text-danger">*</span>
                </label>
                <input ref="uploadFileInput" type="file" class="form-control" @change="onUploadFileChange" />
                <small class="text-muted">{{ t('adminDocutilTemplates.fieldFileHelp') }}</small>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="uploadModal.open = false">
              {{ t('adminDocutilTemplates.cancel') }}
            </button>
            <button type="button" class="btn btn-primary" :disabled="uploading" @click="onUpload">
              <span v-if="uploading" class="spinner-border spinner-border-sm me-2"></span>
              {{ uploading ? t('adminDocutilTemplates.uploading') : t('adminDocutilTemplates.upload') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="uploadModal.open" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import * as docutilService from '@/services/docutilService'
import type {
  DocUtilDocumentTemplate,
  DocUtilDocumentTemplateDetail,
  DocUtilDocumentTemplateVariable
} from '@/services/docutilService'

const { t } = useI18n()

// ── 목록 상태 ────────────────────────────────────────────────────────────
const loading = ref(false)
const items = ref<DocUtilDocumentTemplate[]>([])
const total = ref(0)
const page = ref(1)
const size = ref(20)

// 필터(입력 vs 적용된 값 분리)
const templateTypeInput = ref('')
const appliedTemplateType = ref('')

// 알림
const successMessage = ref('')
const errorMessage = ref('')

// ── 상세 모달 ────────────────────────────────────────────────────────────
const detailModal = reactive<{ open: boolean; template: DocUtilDocumentTemplateDetail | null }>({
  open: false,
  template: null
})
type DetailTab = 'info' | 'variables' | 'structure' | 'autoFill' | 'convert' | 'mapping'
const detailTab = ref<DetailTab>('info')

// 정보 편집 폼
const editForm = reactive({
  name: '',
  description: '',
  templateType: '',
  tone: '',
  outputFormat: '',
  samplePrompt: '',
  renderingMode: 'jinja2',
  isActive: true
})
const saving = ref(false)

// 변수 메타 편집 상태
const variablesLoading = ref(false)
const variableList = ref<DocUtilDocumentTemplateVariable[]>([])

// 구조 조회 상태
const structureLoading = ref(false)
const structureJson = ref('')

// AI 자동채움
const autoFillLoading = ref(false)
const autoFillForm = reactive({
  sourceIdsRaw: '',
  aiPrompt: ''
})
const autoFillResultJson = ref('')

// 변환(Convert)
const convertLoading = ref(false)
const convertForm = reactive({
  aiAnalysisRaw: ''
})
const convertPlaceholder = `{\n  "replacements": [\n    { "original": "홍길동", "variable": "author_name" },\n    { "original": "2026년 1분기", "variable": "period" }\n  ]\n}`

// 변수 매핑 적용
const mappingLoading = ref(false)
const mappingForm = reactive({
  mappingsRaw: ''
})
const mappingPlaceholder = `[\n  {\n    "locationType": "table_cell",\n    "tableIndex": 0,\n    "row": 2,\n    "col": 1,\n    "variableName": "place",\n    "varType": "string",\n    "label": "장 소",\n    "category": "user_input",\n    "fieldType": "short"\n  },\n  {\n    "locationType": "paragraph",\n    "paragraphIndex": 0,\n    "variableName": "title",\n    "varType": "string",\n    "label": "문서 제목",\n    "category": "user_input",\n    "fieldType": "short"\n  }\n]`

// ── 생성 모달 ────────────────────────────────────────────────────────────
const createModal = reactive<{ open: boolean }>({ open: false })
const createForm = reactive({
  name: '',
  description: '',
  templateType: '',
  outputFormat: 'docx',
  tone: 'formal',
  samplePrompt: '',
  renderingMode: 'jinja2'
})
const creating = ref(false)

// ── 업로드 모달 ──────────────────────────────────────────────────────────
type UploadMode = 'standard' | 'blank' | 'smart'
const uploadModal = reactive<{ open: boolean; mode: UploadMode }>({ open: false, mode: 'standard' })
const uploadForm = reactive({
  templateType: '',
  outputFormat: 'docx',
  tone: 'formal',
  name: '',
  description: ''
})
const uploadFileInput = ref<HTMLInputElement | null>(null)
const uploadFile = ref<File | null>(null)
const uploading = ref(false)

const uploadModalTitle = computed(() => {
  if (uploadModal.mode === 'blank') return t('adminDocutilTemplates.uploadBlankTitle')
  if (uploadModal.mode === 'smart') return t('adminDocutilTemplates.uploadSmartTitle')
  return t('adminDocutilTemplates.uploadStandardTitle')
})
const uploadModalHint = computed(() => {
  if (uploadModal.mode === 'blank') return t('adminDocutilTemplates.uploadBlankHint')
  if (uploadModal.mode === 'smart') return t('adminDocutilTemplates.uploadSmartHint')
  return t('adminDocutilTemplates.uploadStandardHint')
})

// ── 파생 값 ──────────────────────────────────────────────────────────────
const totalPages = computed(() => {
  if (total.value <= 0) return 1
  return Math.max(1, Math.ceil(total.value / size.value))
})

// ══════════════════════════════════════════════════════════════════════
// 로드 / 필터 / 페이지네이션
// ══════════════════════════════════════════════════════════════════════
async function loadList() {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await docutilService.listDocumentTemplates(page.value, size.value, {
      templateType: appliedTemplateType.value || undefined
    })
    items.value = result.items
    total.value = result.total
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorBoundary'))
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadList()
})

function onApplyFilters() {
  appliedTemplateType.value = templateTypeInput.value.trim()
  page.value = 1
  loadList()
}

function onClearFilters() {
  templateTypeInput.value = ''
  appliedTemplateType.value = ''
  page.value = 1
  loadList()
}

function onPageSizeChange() {
  page.value = 1
  loadList()
}

function onChangePage(next: number) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  loadList()
}

// ══════════════════════════════════════════════════════════════════════
// 상세 + 편집
// ══════════════════════════════════════════════════════════════════════
async function openDetail(tpl: DocUtilDocumentTemplate) {
  detailModal.template = null
  detailModal.open = true
  detailTab.value = 'info'
  resetTabState()
  try {
    const detail = await docutilService.getDocumentTemplate(tpl.id)
    detailModal.template = detail
    // 편집 폼 초기화
    editForm.name = detail.name
    editForm.description = detail.description ?? ''
    editForm.templateType = detail.templateType
    editForm.tone = detail.tone
    editForm.outputFormat = detail.outputFormat
    editForm.samplePrompt = detail.samplePrompt ?? ''
    editForm.renderingMode = detail.renderingMode
    editForm.isActive = detail.isActive
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorBoundary'))
    detailModal.open = false
  }
}

function closeDetail() {
  detailModal.open = false
  detailModal.template = null
  resetTabState()
}

function resetTabState() {
  variableList.value = []
  structureJson.value = ''
  autoFillForm.sourceIdsRaw = ''
  autoFillForm.aiPrompt = ''
  autoFillResultJson.value = ''
  convertForm.aiAnalysisRaw = ''
  mappingForm.mappingsRaw = ''
}

async function onSwitchTab(tab: DetailTab) {
  detailTab.value = tab
  if (!detailModal.template) return
  if (tab === 'variables' && variableList.value.length === 0) {
    await loadVariables()
  } else if (tab === 'structure' && !structureJson.value) {
    await loadStructure()
  }
}

async function loadVariables() {
  if (!detailModal.template) return
  variablesLoading.value = true
  errorMessage.value = ''
  try {
    const list = await docutilService.getDocumentTemplateVariables(detailModal.template.id)
    // copy to make editable (reactivity)
    variableList.value = list.map((v) => ({ ...v }))
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorBoundary'))
    variableList.value = []
  } finally {
    variablesLoading.value = false
  }
}

async function loadStructure() {
  if (!detailModal.template) return
  structureLoading.value = true
  errorMessage.value = ''
  try {
    const data = await docutilService.getDocumentTemplateStructure(detailModal.template.id)
    structureJson.value = JSON.stringify(data, null, 2)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorBoundary'))
    structureJson.value = ''
  } finally {
    structureLoading.value = false
  }
}

async function onSaveInfo() {
  if (!detailModal.template) return
  if (!editForm.name.trim()) {
    errorMessage.value = t('adminDocutilTemplates.validationNameRequired')
    return
  }
  if (editForm.name.length > 255) {
    errorMessage.value = t('adminDocutilTemplates.validationNameLength')
    return
  }
  if (editForm.description && editForm.description.length > 2000) {
    errorMessage.value = t('adminDocutilTemplates.validationDescriptionLength')
    return
  }
  if (editForm.samplePrompt && editForm.samplePrompt.length > 5000) {
    errorMessage.value = t('adminDocutilTemplates.validationSamplePromptLength')
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    const updated = await docutilService.updateDocumentTemplate(detailModal.template.id, {
      name: editForm.name.trim(),
      description: editForm.description.trim() || null,
      templateType: editForm.templateType.trim() || null,
      tone: editForm.tone.trim() || null,
      outputFormat: editForm.outputFormat.trim() || null,
      samplePrompt: editForm.samplePrompt.trim() || null,
      renderingMode: editForm.renderingMode.trim() || null,
      isActive: editForm.isActive
    })
    detailModal.template = updated
    successMessage.value = t('adminDocutilTemplates.updateSuccess')
    await loadList()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  } finally {
    saving.value = false
  }
}

function onAddVariable() {
  variableList.value.push({
    name: '',
    varType: 'string',
    label: null,
    description: null,
    required: true,
    category: 'user_input'
  })
}

function onRemoveVariable(index: number) {
  variableList.value.splice(index, 1)
}

async function onSaveVariables() {
  if (!detailModal.template) return
  for (const v of variableList.value) {
    if (!v.name || !v.name.trim()) {
      errorMessage.value = t('adminDocutilTemplates.validationVariableName')
      return
    }
  }
  saving.value = true
  errorMessage.value = ''
  try {
    const updated = await docutilService.updateDocumentTemplateVariables(detailModal.template.id, {
      variables: variableList.value
    })
    detailModal.template = updated
    successMessage.value = t('adminDocutilTemplates.variablesSaved')
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  } finally {
    saving.value = false
  }
}

async function onAutoFill() {
  if (!detailModal.template) return
  const ids = autoFillForm.sourceIdsRaw
    .split(/[\s,;\n]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
  if (ids.length === 0) {
    errorMessage.value = t('adminDocutilTemplates.validationAutoFillIds')
    return
  }
  if (ids.length > 50) {
    errorMessage.value = t('adminDocutilTemplates.validationAutoFillIdsMax')
    return
  }
  autoFillLoading.value = true
  errorMessage.value = ''
  try {
    const result = await docutilService.autoFillDocumentTemplate(detailModal.template.id, {
      sourceDocumentIds: ids,
      aiPrompt: autoFillForm.aiPrompt.trim() || null
    })
    autoFillResultJson.value = JSON.stringify(result.context, null, 2)
    successMessage.value = t('adminDocutilTemplates.autoFillSuccess')
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  } finally {
    autoFillLoading.value = false
  }
}

async function onConvert() {
  if (!detailModal.template) return
  let parsed: Record<string, unknown>
  try {
    parsed = JSON.parse(convertForm.aiAnalysisRaw || '{}') as Record<string, unknown>
    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      throw new Error('ai_analysis must be an object')
    }
  } catch {
    errorMessage.value = t('adminDocutilTemplates.validationConvertJson')
    return
  }
  convertLoading.value = true
  errorMessage.value = ''
  try {
    const updated = await docutilService.convertDocumentTemplate(detailModal.template.id, {
      aiAnalysis: parsed
    })
    detailModal.template = updated
    successMessage.value = t('adminDocutilTemplates.convertSuccess')
    await loadList()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  } finally {
    convertLoading.value = false
  }
}

async function onApplyMapping() {
  if (!detailModal.template) return
  let parsed: unknown
  try {
    parsed = JSON.parse(mappingForm.mappingsRaw || '[]')
    if (!Array.isArray(parsed)) {
      throw new Error('mappings must be an array')
    }
    if (parsed.length === 0) {
      throw new Error('mappings is empty')
    }
  } catch {
    errorMessage.value = t('adminDocutilTemplates.validationMappingJson')
    return
  }
  mappingLoading.value = true
  errorMessage.value = ''
  try {
    const updated = await docutilService.applyDocumentTemplateMapping(detailModal.template.id, {
      mappings: parsed as docutilService.DocUtilDocumentTemplateMapping[]
    })
    detailModal.template = updated
    successMessage.value = t('adminDocutilTemplates.mappingSuccess')
    await loadList()
    // 매핑 적용 후 변수 목록도 새로고침 필요할 수 있음 — 다음 탭 진입 시 fresh load 위해 캐시 비움
    variableList.value = []
    structureJson.value = ''
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  } finally {
    mappingLoading.value = false
  }
}

// ══════════════════════════════════════════════════════════════════════
// 생성 (JSON 메타데이터만)
// ══════════════════════════════════════════════════════════════════════
function openCreateDialog() {
  createForm.name = ''
  createForm.description = ''
  createForm.templateType = ''
  createForm.outputFormat = 'docx'
  createForm.tone = 'formal'
  createForm.samplePrompt = ''
  createForm.renderingMode = 'jinja2'
  createModal.open = true
}

async function onCreate() {
  if (!createForm.name.trim()) {
    errorMessage.value = t('adminDocutilTemplates.validationNameRequired')
    return
  }
  if (!createForm.templateType.trim()) {
    errorMessage.value = t('adminDocutilTemplates.validationTemplateTypeRequired')
    return
  }
  if (!createForm.outputFormat.trim()) {
    errorMessage.value = t('adminDocutilTemplates.validationOutputFormatRequired')
    return
  }
  creating.value = true
  errorMessage.value = ''
  try {
    await docutilService.createDocumentTemplate({
      name: createForm.name.trim(),
      description: createForm.description.trim() || null,
      templateType: createForm.templateType.trim(),
      outputFormat: createForm.outputFormat.trim(),
      tone: createForm.tone.trim() || 'formal',
      samplePrompt: createForm.samplePrompt.trim() || null,
      renderingMode: createForm.renderingMode.trim() || 'jinja2'
    })
    successMessage.value = t('adminDocutilTemplates.createSuccess')
    createModal.open = false
    await loadList()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  } finally {
    creating.value = false
  }
}

// ══════════════════════════════════════════════════════════════════════
// 업로드 (3종)
// ══════════════════════════════════════════════════════════════════════
function openUploadDialog(mode: UploadMode) {
  uploadModal.mode = mode
  uploadModal.open = true
  uploadForm.templateType = ''
  uploadForm.outputFormat = 'docx'
  uploadForm.tone = 'formal'
  uploadForm.name = ''
  uploadForm.description = ''
  uploadFile.value = null
  if (uploadFileInput.value) uploadFileInput.value.value = ''
}

function onUploadFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  uploadFile.value = input.files && input.files.length > 0 ? input.files[0] : null
}

async function onUpload() {
  if (!uploadFile.value) {
    errorMessage.value = t('adminDocutilTemplates.validationFileRequired')
    return
  }
  if (uploadModal.mode !== 'smart') {
    if (!uploadForm.templateType.trim()) {
      errorMessage.value = t('adminDocutilTemplates.validationTemplateTypeRequired')
      return
    }
    if (!uploadForm.outputFormat.trim()) {
      errorMessage.value = t('adminDocutilTemplates.validationOutputFormatRequired')
      return
    }
  }
  uploading.value = true
  errorMessage.value = ''
  try {
    const opts = {
      tone: uploadForm.tone.trim() || 'formal',
      name: uploadForm.name.trim() || undefined,
      description: uploadForm.description.trim() || undefined
    }
    if (uploadModal.mode === 'standard') {
      await docutilService.uploadDocumentTemplate(
        uploadForm.templateType.trim(),
        uploadForm.outputFormat.trim(),
        uploadFile.value,
        opts
      )
    } else if (uploadModal.mode === 'blank') {
      await docutilService.uploadBlankFormTemplate(
        uploadForm.templateType.trim(),
        uploadForm.outputFormat.trim(),
        uploadFile.value,
        opts
      )
    } else {
      await docutilService.uploadSmartTemplate(uploadFile.value, {
        templateType: uploadForm.templateType.trim() || undefined,
        ...opts
      })
    }
    successMessage.value = t('adminDocutilTemplates.uploadSuccess')
    uploadModal.open = false
    await loadList()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  } finally {
    uploading.value = false
  }
}

// ══════════════════════════════════════════════════════════════════════
// 미리보기 / 삭제
// ══════════════════════════════════════════════════════════════════════
async function onPreview(tpl: DocUtilDocumentTemplate) {
  if (!tpl.templateStoragePath) {
    errorMessage.value = t('adminDocutilTemplates.previewUnavailable')
    return
  }
  errorMessage.value = ''
  try {
    const result = await docutilService.previewDocumentTemplate(tpl.id)
    const url = window.URL.createObjectURL(result.blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.fileName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  }
}

async function onDelete(tpl: DocUtilDocumentTemplate) {
  if (!window.confirm(t('adminDocutilTemplates.confirmDelete', { name: tpl.name }))) return
  errorMessage.value = ''
  try {
    await docutilService.deleteDocumentTemplate(tpl.id)
    successMessage.value = t('adminDocutilTemplates.deleteSuccess')
    await loadList()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilTemplates.errorUnknown'))
  }
}

// ══════════════════════════════════════════════════════════════════════
// 유틸
// ══════════════════════════════════════════════════════════════════════
function formatDate(iso: string): string {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}

function extractError(e: unknown, fallback: string): string {
  if (typeof e === 'object' && e !== null) {
    const anyE = e as { response?: { data?: { message?: string } }; message?: string }
    if (anyE.response?.data?.message) return anyE.response.data.message
    if (anyE.message) return anyE.message
  }
  return fallback
}
</script>

<style scoped>
.admin-docutil-doctemplates .modal {
  background-color: rgba(0, 0, 0, 0.4);
}
</style>
