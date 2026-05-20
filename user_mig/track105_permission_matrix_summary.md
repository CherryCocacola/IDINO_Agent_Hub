# 트랙 #105 Phase B.4 — 5계정 × 410 endpoint 권한 매트릭스 결과

**검증일**: 2026-05-20
**대상**: 4계정 × (DocUtil 30 GET + AgentHub 72 GET) = 408 cell

(POST/PUT/PATCH/DELETE 및 path parameter 있는 endpoint 는 본 트랙 범위 외)

---

## 계정별 집계

| 계정 | DocUtil PASS | DocUtil FAIL | AgentHub PASS | AgentHub FAIL | 전체 PASS율 |
|---|---|---|---|---|---|
| SuperAdmin | 25 | 5 | 49 | 23 | 72.5% |
| UserLegacy | 26 | 4 | 58 | 14 | 82.4% |
| EmployeeHslee | 26 | 4 | 58 | 14 | 82.4% |
| EmployeeShbaek | 12 | 18 | 49 | 23 | 59.8% |

## FAIL endpoint 상세 (계정별)

### SuperAdmin — 28 FAIL

| system | method | path | roles/auth | expected | actual | 비고 |
|---|---|---|---|---|---|---|
| docutil | GET | /api/v1/evaluation/logs | super_admin,admin,org_admin | 200 | 500 | |
| docutil | GET | /api/v1/search-scopes/locations | super_admin,admin,org_admin,manager,member,editor,viewer,user | 200 | 422 | |
| docutil | GET | /api/v1 | admin,super_admin | 200 | 404 | |
| docutil | GET | /api/v1 | admin,super_admin | 200 | 404 | |
| docutil | GET | /api/v1/ | admin,super_admin | 200 | 404 | |
| agenthub | ListEvaluationLogs | /api/admin/docutil/evaluation/logs | Admin,SuperAdmin | 200 | 502 | |
| agenthub | GetEvaluationQuestions | /api/admin/docutil/evaluation/questions | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListEvaluationRuns | /api/admin/docutil/evaluation/runs | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetEvaluationTrend | /api/admin/docutil/evaluation/trend | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListFaqs | /api/admin/docutil/faq | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardMetrics | /api/admin/docutil/dashboard/metrics | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardResponseTimes | /api/admin/docutil/dashboard/response-times | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardSearchErrors | /api/admin/docutil/dashboard/search-errors | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardSearchUsage | /api/admin/docutil/dashboard/search-usage | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardUploadStatus | /api/admin/docutil/dashboard/upload-status | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListAuditLogs | /api/admin/docutil/audit-logs | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListProjects | /api/admin/docutil/projects | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetProjectTree | /api/admin/docutil/projects/tree | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListReports | /api/admin/docutil/reports | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListTemplates | /api/admin/docutil/reports/templates | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListSearchScopes | /api/admin/docutil/search-scopes | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListSearchScopeLocations | /api/admin/docutil/search-scopes/locations | Admin,SuperAdmin | 200 | 400 | |
| agenthub | ListUsers | /api/admin/docutil/users | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListDocuments | /api/admin/knowledge-base/documents | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListCollections | /api/admin/knowledge-base/collections | Admin,SuperAdmin | 200 | 500 | |
| agenthub | DownloadImage | /api/image-generation/download | authenticated | 200 | 400 | |
| agenthub | EstimateCost | /api/image-generation/estimate-cost | authenticated | 200 | 400 | |
| agenthub | GetPresentations | /api/presentations/list | authenticated | 200 | 500 | |

### UserLegacy — 18 FAIL

| system | method | path | roles/auth | expected | actual | 비고 |
|---|---|---|---|---|---|---|
| docutil | GET | /api/v1/search-scopes/locations | super_admin,admin,org_admin,manager,member,editor,viewer,user | 200 | 422 | |
| docutil | GET | /api/v1 | admin,super_admin | 403 | 404 | |
| docutil | GET | /api/v1 | admin,super_admin | 403 | 404 | |
| docutil | GET | /api/v1/ | admin,super_admin | 403 | 404 | |
| agenthub | GetUsageStats | /api/usage | Admin | 403 | 200 | |
| agenthub | GetTopUsers | /api/top-users | Admin | 403 | 200 | |
| agenthub | GetTeamStats | /api/team-stats | Admin | 403 | 200 | |
| agenthub | GetUsageHistorySummary | /api/usage-summary | Admin | 403 | 200 | |
| agenthub | GetUsageHistory | /api/usage-history | Admin | 403 | 200 | |
| agenthub | GetPoolStats | /api/pool-stats | Admin,SuperAdmin | 403 | 200 | |
| agenthub | GetBackups | /api/backups | Admin | 403 | 200 | |
| agenthub | GetBackupSettings | /api/settings | Admin | 403 | 200 | |
| agenthub | DownloadImage | /api/image-generation/download | authenticated | 200 | 400 | |
| agenthub | EstimateCost | /api/image-generation/estimate-cost | authenticated | 200 | 400 | |
| agenthub | GetStatistics | /api/statistics | Admin | 403 | 200 | |
| agenthub | GetPresentations | /api/presentations/list | authenticated | 200 | 500 | |
| agenthub | RunDiagnostics | /api/diagnostics | Admin | 403 | 200 | |
| agenthub | GetPiiProtectionSettings | /api/pii-protection | Admin | 403 | 200 | |

### EmployeeHslee — 18 FAIL

| system | method | path | roles/auth | expected | actual | 비고 |
|---|---|---|---|---|---|---|
| docutil | GET | /api/v1/search-scopes/locations | super_admin,admin,org_admin,manager,member,editor,viewer,user | 200 | 422 | |
| docutil | GET | /api/v1 | admin,super_admin | 403 | 404 | |
| docutil | GET | /api/v1 | admin,super_admin | 403 | 404 | |
| docutil | GET | /api/v1/ | admin,super_admin | 403 | 404 | |
| agenthub | GetUsageStats | /api/usage | Admin | 403 | 200 | |
| agenthub | GetTopUsers | /api/top-users | Admin | 403 | 200 | |
| agenthub | GetTeamStats | /api/team-stats | Admin | 403 | 200 | |
| agenthub | GetUsageHistorySummary | /api/usage-summary | Admin | 403 | 200 | |
| agenthub | GetUsageHistory | /api/usage-history | Admin | 403 | 200 | |
| agenthub | GetPoolStats | /api/pool-stats | Admin,SuperAdmin | 403 | 200 | |
| agenthub | GetBackups | /api/backups | Admin | 403 | 200 | |
| agenthub | GetBackupSettings | /api/settings | Admin | 403 | 200 | |
| agenthub | DownloadImage | /api/image-generation/download | authenticated | 200 | 400 | |
| agenthub | EstimateCost | /api/image-generation/estimate-cost | authenticated | 200 | 400 | |
| agenthub | GetStatistics | /api/statistics | Admin | 403 | 200 | |
| agenthub | GetPresentations | /api/presentations/list | authenticated | 200 | 500 | |
| agenthub | RunDiagnostics | /api/diagnostics | Admin | 403 | 200 | |
| agenthub | GetPiiProtectionSettings | /api/pii-protection | Admin | 403 | 200 | |

### EmployeeShbaek — 41 FAIL

| system | method | path | roles/auth | expected | actual | 비고 |
|---|---|---|---|---|---|---|
| docutil | GET | /api/v1/dashboard/metrics | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/dashboard/search-usage | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/dashboard/upload-status | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/dashboard/response-times | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/dashboard/search-errors | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/api-keys | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/audit-logs | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/audit-logs/export | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/evaluation/runs | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/evaluation/logs | super_admin,admin,org_admin | 403 | 500 | |
| docutil | GET | /api/v1/evaluation/trend | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/evaluation/config | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/evaluation/questions | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/reports/templates | super_admin,admin,org_admin | 403 | 200 | |
| docutil | GET | /api/v1/search-scopes/locations | super_admin,admin,org_admin,manager,member,editor,viewer,user | 200 | 422 | |
| docutil | GET | /api/v1 | admin,super_admin | 403 | 404 | |
| docutil | GET | /api/v1 | admin,super_admin | 403 | 404 | |
| docutil | GET | /api/v1/ | admin,super_admin | 403 | 404 | |
| agenthub | ListEvaluationLogs | /api/admin/docutil/evaluation/logs | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetEvaluationQuestions | /api/admin/docutil/evaluation/questions | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListEvaluationRuns | /api/admin/docutil/evaluation/runs | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetEvaluationTrend | /api/admin/docutil/evaluation/trend | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListFaqs | /api/admin/docutil/faq | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardMetrics | /api/admin/docutil/dashboard/metrics | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardResponseTimes | /api/admin/docutil/dashboard/response-times | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardSearchErrors | /api/admin/docutil/dashboard/search-errors | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardSearchUsage | /api/admin/docutil/dashboard/search-usage | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetDashboardUploadStatus | /api/admin/docutil/dashboard/upload-status | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListAuditLogs | /api/admin/docutil/audit-logs | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListProjects | /api/admin/docutil/projects | Admin,SuperAdmin | 200 | 500 | |
| agenthub | GetProjectTree | /api/admin/docutil/projects/tree | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListReports | /api/admin/docutil/reports | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListTemplates | /api/admin/docutil/reports/templates | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListSearchScopes | /api/admin/docutil/search-scopes | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListSearchScopeLocations | /api/admin/docutil/search-scopes/locations | Admin,SuperAdmin | 200 | 400 | |
| agenthub | ListUsers | /api/admin/docutil/users | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListDocuments | /api/admin/knowledge-base/documents | Admin,SuperAdmin | 200 | 500 | |
| agenthub | ListCollections | /api/admin/knowledge-base/collections | Admin,SuperAdmin | 200 | 500 | |
| agenthub | DownloadImage | /api/image-generation/download | authenticated | 200 | 400 | |
| agenthub | EstimateCost | /api/image-generation/estimate-cost | authenticated | 200 | 400 | |

_(추가 1 건 생략, raw JSON 참조)_

