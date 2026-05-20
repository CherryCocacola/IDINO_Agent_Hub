# 트랙 #105 Phase B.5 — AgentHub BFF 500/502 진단 보고서

**검증일**: 2026-05-20
**대상**: 22 BFF endpoint

## endpoint 별 결과

| status | path | 핵심 에러 |
|---|---|---|
| 500 | `/api/admin/docutil/evaluation/logs` | [DocUtil HTTP circuit breaker] OPENED for 30s — status=500, exception= |
| 500 | `/api/admin/docutil/evaluation/questions` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/evaluation/runs` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/evaluation/trend` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 200 | `/api/admin/docutil/evaluation/config` |          at AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware.Invoke |
| 500 | `/api/admin/docutil/faq` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/dashboard/metrics` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/dashboard/response-times` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/dashboard/search-errors` |       Start processing HTTP request GET http://docutil-api:8000/api/v1/dashboard |
| 500 | `/api/admin/docutil/dashboard/search-usage` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/dashboard/upload-status` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/audit-logs` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/projects` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/projects/tree` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/reports` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/reports/templates` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/docutil/search-scopes` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 400 | `/api/admin/docutil/search-scopes/locations` |          at AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware.Invoke |
| 500 | `/api/admin/docutil/users` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 500 | `/api/admin/knowledge-base/documents` | fail: AIAgentManagement.Middleware.GlobalExceptionHandlerMiddleware[0] |
| 200 | `/api/admin/knowledge-base/collections` | — |
| 500 | `/api/presentations/list` | PostgresException |
