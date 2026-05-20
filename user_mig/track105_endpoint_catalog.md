# 트랙 #105 Phase B.1 — endpoint 카탈로그 자동 추출 결과
**추출일**: 2026-05-20
**DocUtil 총 endpoint**: 135
**AgentHub 총 endpoint**: 275

---

## DocUtil endpoint (module 별)

| Module | endpoint 수 | require_role 미사용 | 'user' 포함 (member 기준) | 결함 후보 |
|---|---|---|---|---|
| admin | 5 | 0 | — |  |
| agents | 5 | 0 | ✓ |  |
| api_keys | 4 | 0 | — |  |
| audit | 2 | 0 | — |  |
| auth | 5 | 5 | — |  |
| chat | 6 | 6 | — |  |
| documents | 8 | 1 | ✓ |  |
| documents_v2 | 7 | 0 | — |  |
| evaluation | 7 | 0 | — |  |
| faq | 5 | 2 | — |  |
| organizations | 9 | 5 | — |  |
| projects | 20 | 0 | ✓ |  |
| reports | 10 | 0 | ✓ |  |
| search | 6 | 6 | — |  |
| search_scopes | 9 | 0 | ✓ |  |
| settings | 4 | 0 | — |  |
| templates | 15 | 0 | ✓ |  |
| users | 8 | 0 | — |  |

## AgentHub endpoint (controller 별)

| Controller | endpoint 수 | auth | Roles |
|---|---|---|---|
| ActivityLogController | 1 | authenticated | Admin |
| AdminDocUtilApiKeysController | 4 | authenticated | Admin,SuperAdmin |
| AdminDocUtilDepartmentsController | 9 | authenticated | Admin,SuperAdmin |
| AdminDocUtilDocAgentsController | 5 | authenticated | Admin,SuperAdmin |
| AdminDocUtilDocumentsV2Controller | 7 | authenticated | Admin,SuperAdmin |
| AdminDocUtilEvaluationController | 7 | authenticated | Admin,SuperAdmin |
| AdminDocUtilFaqController | 5 | authenticated | Admin,SuperAdmin |
| AdminDocUtilOperationsController | 7 | authenticated | Admin,SuperAdmin |
| AdminDocUtilProjectsController | 15 | authenticated | Admin,SuperAdmin |
| AdminDocUtilReportsController | 9 | authenticated | Admin,SuperAdmin |
| AdminDocUtilSearchScopesController | 9 | authenticated | Admin,SuperAdmin |
| AdminDocUtilTemplatesController | 15 | authenticated | Admin,SuperAdmin |
| AdminDocUtilUsersController | 5 | authenticated | Admin,SuperAdmin |
| AdminKnowledgeBaseController | 6 | authenticated | Admin,SuperAdmin |
| AdminMetricsController | 1 | authenticated | Admin,SuperAdmin |
| AgentsController | 18 | anonymous,authenticated | — |
| AnalyticsController | 10 | authenticated | Admin |
| ApiKeysController | 9 | authenticated | Admin,SuperAdmin |
| ApiServicesController | 4 | authenticated | — |
| AuthController | 7 | anonymous,authenticated | — |
| BannedWordsController | 4 | authenticated | Admin |
| ChatController | 10 | authenticated | — |
| DatabaseBackupController | 6 | authenticated | Admin |
| ExamplePromptsController | 5 | anonymous,authenticated | Admin |
| FaqsController | 5 | anonymous,authenticated | Admin |
| FilesController | 6 | authenticated | — |
| ImageGenerationController | 3 | authenticated | — |
| OpenAICompatController | 5 | none | — |
| PiiDetectionLogsController | 2 | authenticated | Admin |
| PresentationController | 14 | authenticated | — |
| PresentationTemplateController | 6 | authenticated | — |
| QuotaController | 5 | authenticated | Admin |
| SystemHealthController | 2 | authenticated | Admin |
| SystemSettingsController | 2 | authenticated | Admin |
| TeamsController | 8 | authenticated | Admin |
| ToolBuilderController | 3 | authenticated | — |
| ToolsController | 11 | authenticated | — |
| TutorialsController | 5 | anonymous,authenticated | Admin |
| UserPreferencesController | 5 | authenticated | — |
| UsersController | 6 | authenticated | Admin |
| WorkflowsController | 9 | authenticated | — |

## 'user' role 누락 잠재 결함 (DocUtil)

트랙 #104 fix 패턴 ('member' 가 있는 helper 에는 'user' 도 함께 포함되어야 함) 기준.
본 트랙 #105 Phase A 진단으로 projects/reports/search_scopes/templates 4 router fix 완료.

| Module | helper | roles | 'user' 포함? | 비고 |
|---|---|---|---|---|
| agents | _require_member | super_admin,admin,org_admin,editor,member,viewer,user | ✓ | ✓ fix 완료 |
| documents | _require_member | super_admin,admin,org_admin,manager,member,editor,viewer,user | ✓ | ✓ fix 완료 |
| documents_v2 | _require_reader | super_admin,admin,org_admin,editor,member,viewer,user | ✓ | ✓ fix 완료 |
| projects | _require_member | super_admin,admin,org_admin,manager,member,editor,viewer,user | ✓ | ✓ fix 완료 |
| reports | _require_member | super_admin,admin,org_admin,manager,member,editor,viewer,user | ✓ | ✓ fix 완료 |
| search_scopes | _require_member | super_admin,admin,org_admin,manager,member,editor,viewer,user | ✓ | ✓ fix 완료 |
| templates | _require_member | super_admin,admin,org_admin,manager,editor,member,viewer,user | ✓ | ✓ fix 완료 |

