<template>
  <div class="admin-docutil-reports container-fluid py-4">
    <header class="mb-3 d-flex align-items-start justify-content-between flex-wrap gap-2">
      <div>
        <h1 class="h3 mb-1">{{ t('adminDocutilReports.title') }}</h1>
        <p class="text-muted mb-0">{{ t('adminDocutilReports.subtitle') }}</p>
      </div>
      <div class="d-flex gap-2">
        <button type="button" class="btn btn-outline-secondary" @click="onRefresh" :disabled="loading">
          <i class="bi bi-arrow-clockwise me-1"></i>{{ t('adminDocutilReports.refresh') }}
        </button>
        <button v-if="activeTab === 'reports'" type="button" class="btn btn-primary" @click="openGenerateDialog">
          <i class="bi bi-play-circle me-1"></i>{{ t('adminDocutilReports.newReport') }}
        </button>
        <button v-if="activeTab === 'templates'" type="button" class="btn btn-primary" @click="openTemplateCreateDialog">
          <i class="bi bi-plus-lg me-1"></i>{{ t('adminDocutilReports.newTemplate') }}
        </button>
      </div>
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
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'reports' }"
          @click="onSwitchToReports"
        >
          <i class="bi bi-file-earmark-text me-2"></i>{{ t('adminDocutilReports.tabReports') }}
        </button>
      </li>
      <li class="nav-item">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'templates' }"
          @click="onSwitchToTemplates"
        >
          <i class="bi bi-file-earmark-richtext me-2"></i>{{ t('adminDocutilReports.tabTemplates') }}
        </button>
      </li>
    </ul>

    <!-- 보고서 탭 -->
    <section v-if="activeTab === 'reports'">
      <!-- 필터 -->
      <div class="card mb-3">
        <div class="card-body">
          <div class="row g-2 align-items-end">
            <div class="col-md-4">
              <label class="form-label small">{{ t('adminDocutilReports.filterStatus') }}</label>
              <select v-model="reportStatusInput" class="form-select" @change="onChangeStatus">
                <option value="">{{ t('adminDocutilReports.statusAll') }}</option>
                <option value="pending">{{ t('adminDocutilReports.statusPending') }}</option>
                <option value="generating">{{ t('adminDocutilReports.statusGenerating') }}</option>
                <option value="completed">{{ t('adminDocutilReports.statusCompleted') }}</option>
                <option value="failed">{{ t('adminDocutilReports.statusFailed') }}</option>
              </select>
            </div>
            <div class="col-md-3">
              <label class="form-label small">{{ t('adminDocutilReports.pageSize') }}</label>
              <select v-model.number="reportSize" class="form-select" @change="onReportPageSizeChange">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- 보고서 표 -->
      <div class="card">
        <div class="card-body p-0">
          <div v-if="reportsLoading" class="text-center py-5 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilReports.loading') }}
          </div>
          <table v-else-if="reports.length > 0" class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>{{ t('adminDocutilReports.colTitle') }}</th>
                <th class="text-center">{{ t('adminDocutilReports.colStatus') }}</th>
                <th class="d-none d-md-table-cell">{{ t('adminDocutilReports.colOutputFormat') }}</th>
                <th class="d-none d-lg-table-cell">{{ t('adminDocutilReports.colCreatedAt') }}</th>
                <th class="d-none d-lg-table-cell">{{ t('adminDocutilReports.colCompletedAt') }}</th>
                <th class="text-end">{{ t('adminDocutilReports.colActions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in reports" :key="r.id">
                <td class="text-truncate" style="max-width: 480px">{{ r.title }}</td>
                <td class="text-center">
                  <span class="badge" :class="statusBadgeClass(r.status)">{{ r.status }}</span>
                </td>
                <td class="d-none d-md-table-cell">{{ r.outputFormat }}</td>
                <td class="d-none d-lg-table-cell text-muted small">{{ formatDate(r.createdAt) }}</td>
                <td class="d-none d-lg-table-cell text-muted small">{{ formatDate(r.completedAt) || '—' }}</td>
                <td class="text-end">
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary me-1"
                    @click="openReportDetail(r)"
                    :title="t('adminDocutilReports.viewDetail')"
                  >
                    <i class="bi bi-eye"></i>
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-primary me-1"
                    :disabled="!canDownload(r) || downloadingReportId === r.id"
                    @click="onDownloadReport(r)"
                    :title="t('adminDocutilReports.download')"
                  >
                    <span v-if="downloadingReportId === r.id" class="spinner-border spinner-border-sm"></span>
                    <i v-else class="bi bi-download"></i>
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-danger"
                    @click="onDeleteReport(r)"
                    :title="t('adminDocutilReports.delete')"
                  >
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="text-center py-5 text-muted">
            {{ t('adminDocutilReports.emptyReports') }}
          </div>
        </div>
      </div>

      <!-- 페이지네이션 -->
      <div class="d-flex justify-content-between align-items-center mt-3">
        <small class="text-muted">{{ t('adminDocutilReports.totalCount', { total: reportsTotal }) }}</small>
        <div class="d-flex align-items-center gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            :disabled="reportPage <= 1 || reportsLoading"
            @click="onChangeReportPage(reportPage - 1)"
          >
            <i class="bi bi-chevron-left"></i>{{ t('adminDocutilReports.prevPage') }}
          </button>
          <span class="small text-muted">
            {{ t('adminDocutilReports.page') }} {{ reportPage }} / {{ reportTotalPages }}
          </span>
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            :disabled="reportPage >= reportTotalPages || reportsLoading"
            @click="onChangeReportPage(reportPage + 1)"
          >
            {{ t('adminDocutilReports.nextPage') }}<i class="bi bi-chevron-right"></i>
          </button>
        </div>
      </div>
    </section>

    <!-- 템플릿 탭 -->
    <section v-if="activeTab === 'templates'">
      <div class="card mb-3">
        <div class="card-body">
          <div class="row g-2 align-items-end">
            <div class="col-md-3">
              <label class="form-label small">{{ t('adminDocutilReports.pageSize') }}</label>
              <select v-model.number="templateSize" class="form-select" @change="onTemplatePageSizeChange">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body p-0">
          <div v-if="templatesLoading" class="text-center py-5 text-muted">
            <div class="spinner-border spinner-border-sm me-2"></div>{{ t('adminDocutilReports.loading') }}
          </div>
          <table v-else-if="templates.length > 0" class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th>{{ t('adminDocutilReports.colName') }}</th>
                <th class="d-none d-md-table-cell">{{ t('adminDocutilReports.colDescription') }}</th>
                <th class="text-center">{{ t('adminDocutilReports.colFormat') }}</th>
                <th class="d-none d-lg-table-cell">{{ t('adminDocutilReports.colUpdatedAt') }}</th>
                <th class="text-end">{{ t('adminDocutilReports.colActions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tpl in templates" :key="tpl.id">
                <td>{{ tpl.name }}</td>
                <td class="d-none d-md-table-cell text-muted small text-truncate" style="max-width: 360px">
                  {{ tpl.description || '—' }}
                </td>
                <td class="text-center">
                  <span class="badge bg-light text-dark">{{ tpl.format }}</span>
                </td>
                <td class="d-none d-lg-table-cell text-muted small">{{ formatDate(tpl.updatedAt) }}</td>
                <td class="text-end">
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary me-1"
                    @click="openTemplateDetail(tpl)"
                    :title="t('adminDocutilReports.viewDetail')"
                  >
                    <i class="bi bi-eye"></i>
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-primary me-1"
                    @click="openTemplateEditDialog(tpl)"
                    :title="t('adminDocutilReports.edit')"
                  >
                    <i class="bi bi-pencil"></i>
                  </button>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-danger"
                    @click="onDeleteTemplate(tpl)"
                    :title="t('adminDocutilReports.delete')"
                  >
                    <i class="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-else class="text-center py-5 text-muted">
            {{ t('adminDocutilReports.emptyTemplates') }}
          </div>
        </div>
      </div>

      <div class="d-flex justify-content-between align-items-center mt-3">
        <small class="text-muted">{{ t('adminDocutilReports.totalCount', { total: templatesTotal }) }}</small>
        <div class="d-flex align-items-center gap-2">
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            :disabled="templatePage <= 1 || templatesLoading"
            @click="onChangeTemplatePage(templatePage - 1)"
          >
            <i class="bi bi-chevron-left"></i>{{ t('adminDocutilReports.prevPage') }}
          </button>
          <span class="small text-muted">
            {{ t('adminDocutilReports.page') }} {{ templatePage }} / {{ templateTotalPages }}
          </span>
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary"
            :disabled="templatePage >= templateTotalPages || templatesLoading"
            @click="onChangeTemplatePage(templatePage + 1)"
          >
            {{ t('adminDocutilReports.nextPage') }}<i class="bi bi-chevron-right"></i>
          </button>
        </div>
      </div>
    </section>

    <!-- 보고서 상세 모달 -->
    <div v-if="reportDetailModal.open" class="modal fade show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilReports.reportDetailTitle') }}</h5>
            <button type="button" class="btn-close" @click="reportDetailModal.open = false"></button>
          </div>
          <div class="modal-body" v-if="reportDetailModal.report">
            <dl class="row small">
              <dt class="col-sm-3">{{ t('adminDocutilReports.colTitle') }}</dt>
              <dd class="col-sm-9">{{ reportDetailModal.report.title }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaId') }}</dt>
              <dd class="col-sm-9 text-muted">{{ reportDetailModal.report.id }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaStatus') }}</dt>
              <dd class="col-sm-9">
                <span class="badge" :class="statusBadgeClass(reportDetailModal.report.status)">
                  {{ reportDetailModal.report.status }}
                </span>
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaOutputFormat') }}</dt>
              <dd class="col-sm-9">{{ reportDetailModal.report.outputFormat }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaTemplateId') }}</dt>
              <dd class="col-sm-9 text-muted">{{ reportDetailModal.report.templateId || '—' }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaOutputStoragePath') }}</dt>
              <dd class="col-sm-9 text-muted" style="word-break: break-all">
                {{ reportDetailModal.report.outputStoragePath || '—' }}
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaSourceDocumentIds') }}</dt>
              <dd class="col-sm-9 text-muted" style="word-break: break-all">
                {{ formatIdList(reportDetailModal.report.sourceDocumentIds) }}
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaSourceChatSessionId') }}</dt>
              <dd class="col-sm-9 text-muted">{{ reportDetailModal.report.sourceChatSessionId || '—' }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaGenerationParams') }}</dt>
              <dd class="col-sm-9 text-muted">
                <pre v-if="reportDetailModal.report.generationParams" class="mb-0">{{ JSON.stringify(reportDetailModal.report.generationParams, null, 2) }}</pre>
                <span v-else>—</span>
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaRenderingMode') }}</dt>
              <dd class="col-sm-9 text-muted">{{ reportDetailModal.report.renderingMode || '—' }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaErrorMessage') }}</dt>
              <dd class="col-sm-9 text-danger">{{ reportDetailModal.report.errorMessage || '—' }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaGeneratedBy') }}</dt>
              <dd class="col-sm-9 text-muted">{{ reportDetailModal.report.generatedBy }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaCreatedAt') }}</dt>
              <dd class="col-sm-9 text-muted">{{ formatDate(reportDetailModal.report.createdAt) }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaCompletedAt') }}</dt>
              <dd class="col-sm-9 text-muted">{{ formatDate(reportDetailModal.report.completedAt) || '—' }}</dd>
            </dl>
          </div>
          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-primary"
              :disabled="!reportDetailModal.report || !canDownload(reportDetailModal.report)"
              @click="reportDetailModal.report && onDownloadReport(reportDetailModal.report)"
            >
              <i class="bi bi-download me-1"></i>{{ t('adminDocutilReports.download') }}
            </button>
            <button type="button" class="btn btn-secondary" @click="reportDetailModal.open = false">
              {{ t('adminDocutilReports.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="reportDetailModal.open" class="modal-backdrop fade show"></div>

    <!-- 보고서 생성 모달 -->
    <div v-if="generateModal.open" class="modal fade show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilReports.generateTitle') }}</h5>
            <button type="button" class="btn-close" @click="generateModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">
                {{ t('adminDocutilReports.fieldReportTitle') }} <span class="text-danger">*</span>
              </label>
              <input
                v-model="generateForm.title"
                type="text"
                class="form-control"
                :placeholder="t('adminDocutilReports.fieldReportTitlePlaceholder')"
                maxlength="500"
              />
            </div>
            <div class="row g-2">
              <div class="col-md-6">
                <label class="form-label">{{ t('adminDocutilReports.fieldOutputFormat') }}</label>
                <select v-model="generateForm.outputFormat" class="form-select">
                  <option value="docx">docx</option>
                  <option value="pdf">pdf</option>
                  <option value="html">html</option>
                  <option value="hwp">hwp</option>
                  <option value="hwpx">hwpx</option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="form-label">{{ t('adminDocutilReports.fieldTemplate') }}</label>
                <select v-model="generateForm.templateId" class="form-select">
                  <option :value="''">—</option>
                  <option v-for="tpl in templates" :key="tpl.id" :value="tpl.id">
                    {{ tpl.name }} ({{ tpl.format }})
                  </option>
                </select>
                <small class="text-muted">{{ t('adminDocutilReports.fieldTemplateOptional') }}</small>
              </div>
            </div>
            <div class="mb-3 mt-3">
              <label class="form-label">{{ t('adminDocutilReports.fieldSourceDocumentIds') }}</label>
              <textarea
                v-model="generateForm.sourceDocumentIdsRaw"
                class="form-control"
                rows="2"
              ></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilReports.fieldSourceChatSessionId') }}</label>
              <input v-model="generateForm.sourceChatSessionId" type="text" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilReports.fieldGenerationParams') }}</label>
              <textarea
                v-model="generateForm.generationParamsRaw"
                class="form-control"
                rows="6"
                placeholder='{"key": "value"}'
              ></textarea>
              <small class="text-muted">{{ t('adminDocutilReports.fieldGenerationParamsHint') }}</small>
            </div>
            <div v-if="generateResponse" class="mt-3">
              <label class="form-label">{{ t('adminDocutilReports.generateResponseLabel') }}</label>
              <pre class="bg-light p-2 small mb-0" style="max-height: 200px; overflow: auto">{{ JSON.stringify(generateResponse, null, 2) }}</pre>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="generateModal.open = false">
              {{ t('adminDocutilReports.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="generating"
              @click="onGenerateReport"
            >
              <span v-if="generating" class="spinner-border spinner-border-sm me-2"></span>
              {{ generating ? t('adminDocutilReports.generating') : t('adminDocutilReports.generateButton') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="generateModal.open" class="modal-backdrop fade show"></div>

    <!-- 템플릿 생성/수정 모달 -->
    <div v-if="templateModal.open" class="modal fade show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ templateModal.mode === 'create' ? t('adminDocutilReports.templateCreateTitle') : t('adminDocutilReports.templateEditTitle') }}
            </h5>
            <button type="button" class="btn-close" @click="templateModal.open = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">
                {{ t('adminDocutilReports.fieldTemplateName') }} <span class="text-danger">*</span>
              </label>
              <input
                v-model="templateForm.name"
                type="text"
                class="form-control"
                :placeholder="t('adminDocutilReports.fieldTemplateNamePlaceholder')"
                maxlength="255"
              />
            </div>
            <div v-if="templateModal.mode === 'create'" class="mb-3">
              <label class="form-label">{{ t('adminDocutilReports.fieldTemplateFormat') }}</label>
              <select v-model="templateForm.format" class="form-select">
                <option value="docx">docx</option>
                <option value="pdf">pdf</option>
                <option value="html">html</option>
                <option value="hwp">hwp</option>
                <option value="hwpx">hwpx</option>
              </select>
            </div>
            <div class="mb-3">
              <label class="form-label">{{ t('adminDocutilReports.fieldTemplateDescription') }}</label>
              <textarea
                v-model="templateForm.description"
                class="form-control"
                rows="3"
                :placeholder="t('adminDocutilReports.fieldTemplateDescriptionPlaceholder')"
                maxlength="2000"
              ></textarea>
            </div>
            <div v-if="templateModal.mode === 'create'" class="mb-3">
              <label class="form-label">{{ t('adminDocutilReports.fieldTemplateFile') }}</label>
              <input
                ref="fileInputEl"
                type="file"
                class="form-control"
                @change="onFileChange"
              />
              <small class="text-muted d-block">{{ t('adminDocutilReports.fieldTemplateFileHint') }}</small>
              <div v-if="templateFile" class="mt-2 d-flex align-items-center gap-2">
                <span class="badge bg-light text-dark">
                  {{ t('adminDocutilReports.fieldTemplateFileSelected', { name: templateFile.name, size: formatFileSize(templateFile.size) }) }}
                </span>
                <button type="button" class="btn btn-sm btn-link" @click="clearFile">
                  {{ t('adminDocutilReports.removeFile') }}
                </button>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="templateModal.open = false">
              {{ t('adminDocutilReports.cancel') }}
            </button>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="templateSaving"
              @click="onSaveTemplate"
            >
              <span v-if="templateSaving" class="spinner-border spinner-border-sm me-2"></span>
              {{ templateSaving ? t('adminDocutilReports.saving') : t('adminDocutilReports.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="templateModal.open" class="modal-backdrop fade show"></div>

    <!-- 템플릿 상세 모달 -->
    <div v-if="templateDetailModal.open" class="modal fade show d-block" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ t('adminDocutilReports.templateDetailTitle') }}</h5>
            <button type="button" class="btn-close" @click="templateDetailModal.open = false"></button>
          </div>
          <div class="modal-body" v-if="templateDetailModal.template">
            <dl class="row small">
              <dt class="col-sm-3">{{ t('adminDocutilReports.colName') }}</dt>
              <dd class="col-sm-9">{{ templateDetailModal.template.name }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaId') }}</dt>
              <dd class="col-sm-9 text-muted">{{ templateDetailModal.template.id }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.colFormat') }}</dt>
              <dd class="col-sm-9">{{ templateDetailModal.template.format }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.colDescription') }}</dt>
              <dd class="col-sm-9">{{ templateDetailModal.template.description || '—' }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.metaOutputStoragePath') }}</dt>
              <dd class="col-sm-9 text-muted" style="word-break: break-all">
                {{ templateDetailModal.template.templateStoragePath || '—' }}
              </dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.colCreatedBy') }}</dt>
              <dd class="col-sm-9 text-muted">{{ templateDetailModal.template.createdBy }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.colCreatedAt') }}</dt>
              <dd class="col-sm-9 text-muted">{{ formatDate(templateDetailModal.template.createdAt) }}</dd>
              <dt class="col-sm-3">{{ t('adminDocutilReports.colUpdatedAt') }}</dt>
              <dd class="col-sm-9 text-muted">{{ formatDate(templateDetailModal.template.updatedAt) }}</dd>
            </dl>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="templateDetailModal.open = false">
              {{ t('adminDocutilReports.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="templateDetailModal.open" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import * as docutilService from '@/services/docutilService'
import type {
  DocUtilReport,
  DocUtilReportDetail,
  DocUtilReportTemplate,
  DocUtilReportTemplateDetail
} from '@/services/docutilService'

const { t } = useI18n()

// ── 공통 상태 ────────────────────────────────────────────────────────────
const activeTab = ref<'reports' | 'templates'>('reports')
const loading = computed(() => reportsLoading.value || templatesLoading.value)
const successMessage = ref('')
const errorMessage = ref('')

// ── 보고서 상태 ──────────────────────────────────────────────────────────
const reportsLoading = ref(false)
const reports = ref<DocUtilReport[]>([])
const reportsTotal = ref(0)
const reportPage = ref(1)
const reportSize = ref(20)
const reportStatusInput = ref('')
const reportTotalPages = computed(() => {
  if (reportsTotal.value <= 0) return 1
  return Math.max(1, Math.ceil(reportsTotal.value / reportSize.value))
})

const downloadingReportId = ref<string | null>(null)

const reportDetailModal = reactive<{ open: boolean; report: DocUtilReportDetail | null }>({
  open: false,
  report: null
})

const generateModal = reactive<{ open: boolean }>({ open: false })
const generateForm = reactive({
  title: '',
  templateId: '',
  outputFormat: 'docx',
  sourceDocumentIdsRaw: '',
  sourceChatSessionId: '',
  generationParamsRaw: ''
})
const generateResponse = ref<Record<string, unknown> | null>(null)
const generating = ref(false)

// ── 템플릿 상태 ──────────────────────────────────────────────────────────
const templatesLoading = ref(false)
const templates = ref<DocUtilReportTemplate[]>([])
const templatesTotal = ref(0)
const templatePage = ref(1)
const templateSize = ref(20)
const templateTotalPages = computed(() => {
  if (templatesTotal.value <= 0) return 1
  return Math.max(1, Math.ceil(templatesTotal.value / templateSize.value))
})

const templateModal = reactive<{ open: boolean; mode: 'create' | 'edit'; targetId: string | null }>({
  open: false,
  mode: 'create',
  targetId: null
})
const templateForm = reactive({
  name: '',
  format: 'docx',
  description: ''
})
const templateFile = ref<File | null>(null)
const fileInputEl = ref<HTMLInputElement | null>(null)
const templateSaving = ref(false)

const templateDetailModal = reactive<{ open: boolean; template: DocUtilReportTemplateDetail | null }>({
  open: false,
  template: null
})

// ── 마운트 ───────────────────────────────────────────────────────────────
onMounted(() => {
  loadReports()
  // 초기 템플릿 카탈로그 prefetch — 생성 모달의 드롭다운에 필요.
  loadTemplates(/*silent=*/true)
})

// ── 보고서 로드 ──────────────────────────────────────────────────────────
async function loadReports() {
  reportsLoading.value = true
  errorMessage.value = ''
  try {
    const list = await docutilService.listReports(
      reportPage.value,
      reportSize.value,
      reportStatusInput.value || undefined
    )
    reports.value = list.items
    reportsTotal.value = list.total
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.errorBoundary'))
    reports.value = []
    reportsTotal.value = 0
  } finally {
    reportsLoading.value = false
  }
}

async function loadTemplates(silent: boolean = false) {
  templatesLoading.value = true
  if (!silent) errorMessage.value = ''
  try {
    const list = await docutilService.listReportTemplates(templatePage.value, templateSize.value)
    templates.value = list.items
    templatesTotal.value = list.total
  } catch (e: unknown) {
    if (!silent) {
      errorMessage.value = extractError(e, t('adminDocutilReports.errorBoundary'))
    }
    templates.value = []
    templatesTotal.value = 0
  } finally {
    templatesLoading.value = false
  }
}

// ── 탭 전환 ──────────────────────────────────────────────────────────────
function onSwitchToReports() {
  activeTab.value = 'reports'
  loadReports()
}
function onSwitchToTemplates() {
  activeTab.value = 'templates'
  loadTemplates()
}

function onRefresh() {
  if (activeTab.value === 'reports') loadReports()
  else loadTemplates()
}

// ── 보고서 페이지/필터 ───────────────────────────────────────────────────
function onChangeStatus() {
  reportPage.value = 1
  loadReports()
}
function onReportPageSizeChange() {
  reportPage.value = 1
  loadReports()
}
function onChangeReportPage(next: number) {
  if (next < 1 || next > reportTotalPages.value) return
  reportPage.value = next
  loadReports()
}

// ── 보고서 상세/다운로드/삭제 ────────────────────────────────────────────
async function openReportDetail(r: DocUtilReport) {
  reportDetailModal.report = null
  reportDetailModal.open = true
  try {
    reportDetailModal.report = await docutilService.getReport(r.id)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.errorBoundary'))
    reportDetailModal.open = false
  }
}

function canDownload(r: { status: string }): boolean {
  // status 가 명확하지 않은 DocUtil 환경에서도 다운로드 시도 가능 — 실패 시 alert.
  // 일반적으로 'completed' / 'success' / 'done' 류만 가능.
  const s = (r.status || '').toLowerCase()
  return s === 'completed' || s === 'success' || s === 'done' || s === 'finished' || s === 'ready'
}

async function onDownloadReport(r: DocUtilReport | DocUtilReportDetail) {
  if (downloadingReportId.value === r.id) return
  downloadingReportId.value = r.id
  errorMessage.value = ''
  try {
    const { blob, fileName } = await docutilService.downloadReport(r.id)
    triggerBlobDownload(blob, fileName)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.downloadFailed'))
  } finally {
    downloadingReportId.value = null
  }
}

function triggerBlobDownload(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  // URL 은 즉시 revoke 시 일부 브라우저에서 다운로드 실패 — 짧은 지연 후 revoke.
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function onDeleteReport(r: DocUtilReport) {
  if (!window.confirm(t('adminDocutilReports.confirmDeleteReport'))) return
  errorMessage.value = ''
  try {
    await docutilService.deleteReport(r.id)
    successMessage.value = t('adminDocutilReports.deleteReportSuccess')
    await loadReports()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.errorUnknown'))
  }
}

// ── 보고서 생성 ──────────────────────────────────────────────────────────
function openGenerateDialog() {
  generateForm.title = ''
  generateForm.templateId = ''
  generateForm.outputFormat = 'docx'
  generateForm.sourceDocumentIdsRaw = ''
  generateForm.sourceChatSessionId = ''
  generateForm.generationParamsRaw = ''
  generateResponse.value = null
  generateModal.open = true
  // 템플릿 카탈로그 최신화(생성 모달의 드롭다운).
  loadTemplates(true)
}

async function onGenerateReport() {
  // 검증
  if (!generateForm.title.trim()) {
    errorMessage.value = t('adminDocutilReports.validationTitleRequired')
    return
  }
  if (generateForm.title.length > 500) {
    errorMessage.value = t('adminDocutilReports.validationTitleLength')
    return
  }

  // sourceDocumentIds 파싱(콤마/줄바꿈/공백 분리).
  const ids = generateForm.sourceDocumentIdsRaw
    .split(/[\s,]+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)

  // generationParams JSON 파싱.
  let parsedParams: Record<string, unknown> | undefined
  if (generateForm.generationParamsRaw.trim()) {
    try {
      const parsed = JSON.parse(generateForm.generationParamsRaw)
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        errorMessage.value = t('adminDocutilReports.validationGenerationParamsJson')
        return
      }
      parsedParams = parsed as Record<string, unknown>
    } catch {
      errorMessage.value = t('adminDocutilReports.validationGenerationParamsJson')
      return
    }
  }

  generating.value = true
  errorMessage.value = ''
  try {
    const resp = await docutilService.generateReport({
      title: generateForm.title.trim(),
      templateId: generateForm.templateId || null,
      outputFormat: generateForm.outputFormat,
      sourceDocumentIds: ids.length > 0 ? ids : null,
      sourceChatSessionId: generateForm.sourceChatSessionId.trim() || null,
      generationParams: parsedParams ?? null
    })
    generateResponse.value = resp
    successMessage.value = t('adminDocutilReports.generateSuccess')
    await loadReports()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.errorUnknown'))
  } finally {
    generating.value = false
  }
}

// ── 템플릿 페이지 ────────────────────────────────────────────────────────
function onTemplatePageSizeChange() {
  templatePage.value = 1
  loadTemplates()
}
function onChangeTemplatePage(next: number) {
  if (next < 1 || next > templateTotalPages.value) return
  templatePage.value = next
  loadTemplates()
}

// ── 템플릿 상세 ──────────────────────────────────────────────────────────
async function openTemplateDetail(tpl: DocUtilReportTemplate) {
  templateDetailModal.template = null
  templateDetailModal.open = true
  try {
    templateDetailModal.template = await docutilService.getReportTemplate(tpl.id)
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.errorBoundary'))
    templateDetailModal.open = false
  }
}

// ── 템플릿 생성/수정 ─────────────────────────────────────────────────────
function openTemplateCreateDialog() {
  templateModal.mode = 'create'
  templateModal.targetId = null
  templateForm.name = ''
  templateForm.format = 'docx'
  templateForm.description = ''
  templateFile.value = null
  if (fileInputEl.value) fileInputEl.value.value = ''
  templateModal.open = true
}

function openTemplateEditDialog(tpl: DocUtilReportTemplate) {
  templateModal.mode = 'edit'
  templateModal.targetId = tpl.id
  templateForm.name = tpl.name
  templateForm.format = tpl.format
  templateForm.description = tpl.description ?? ''
  templateFile.value = null
  templateModal.open = true
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    templateFile.value = input.files[0]
  }
}

function clearFile() {
  templateFile.value = null
  if (fileInputEl.value) fileInputEl.value.value = ''
}

async function onSaveTemplate() {
  // 검증
  if (!templateForm.name.trim()) {
    errorMessage.value = t('adminDocutilReports.validationTemplateNameRequired')
    return
  }
  if (templateForm.name.length > 255) {
    errorMessage.value = t('adminDocutilReports.validationTemplateNameLength')
    return
  }
  if (templateForm.description && templateForm.description.length > 2000) {
    errorMessage.value = t('adminDocutilReports.validationDescriptionLength')
    return
  }

  templateSaving.value = true
  errorMessage.value = ''
  try {
    if (templateModal.mode === 'create') {
      await docutilService.createReportTemplate(
        templateForm.name.trim(),
        templateForm.format,
        templateForm.description.trim() || undefined,
        templateFile.value ?? undefined
      )
      successMessage.value = t('adminDocutilReports.templateCreateSuccess')
    } else if (templateModal.targetId) {
      await docutilService.updateReportTemplate(templateModal.targetId, {
        name: templateForm.name.trim(),
        description: templateForm.description.trim() || null
      })
      successMessage.value = t('adminDocutilReports.templateUpdateSuccess')
    }
    templateModal.open = false
    await loadTemplates()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.errorUnknown'))
  } finally {
    templateSaving.value = false
  }
}

async function onDeleteTemplate(tpl: DocUtilReportTemplate) {
  if (!window.confirm(t('adminDocutilReports.confirmDeleteTemplate'))) return
  errorMessage.value = ''
  try {
    await docutilService.deleteReportTemplate(tpl.id)
    successMessage.value = t('adminDocutilReports.deleteTemplateSuccess')
    await loadTemplates()
  } catch (e: unknown) {
    errorMessage.value = extractError(e, t('adminDocutilReports.errorUnknown'))
  }
}

// ── 유틸 ─────────────────────────────────────────────────────────────────
function statusBadgeClass(status: string): string {
  const s = (status || '').toLowerCase()
  if (s === 'completed' || s === 'success' || s === 'done' || s === 'finished' || s === 'ready')
    return 'bg-success'
  if (s === 'generating' || s === 'in_progress' || s === 'pending' || s === 'queued')
    return 'bg-warning text-dark'
  if (s === 'failed' || s === 'error') return 'bg-danger'
  return 'bg-secondary'
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function formatIdList(ids: string[] | null | undefined): string {
  if (!ids || ids.length === 0) return '—'
  return ids.join(', ')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
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
.admin-docutil-reports .modal {
  background-color: rgba(0, 0, 0, 0.4);
}
</style>
