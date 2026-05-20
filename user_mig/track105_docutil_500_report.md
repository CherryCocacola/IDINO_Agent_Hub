# 트랙 #105 Phase B.5 — DocUtil upstream 500 진단 보고서

**검증일**: 2026-05-20
**대상**: 18 DocUtil endpoint (AgentHub BFF 가 호출하는 path)

## endpoint 별 결과

| status | path | 핵심 에러 |
|---|---|---|
| 500 | `/api/v1/evaluation/logs` | ValidationError |
| 200 | `/api/v1/evaluation/questions` | ValidationError |
| 200 | `/api/v1/evaluation/runs` | ValidationError |
| 200 | `/api/v1/evaluation/trend` | ValidationError |
| 200 | `/api/v1/evaluation/config` | ValidationError |
| 200 | `/api/v1/faq` | ValidationError |
| 200 | `/api/v1/dashboard/metrics` | ValidationError |
| 200 | `/api/v1/dashboard/response-times` |     For further information visit https://errors.pydantic.dev/2.13/v/dict_type |
| 200 | `/api/v1/dashboard/search-errors` |     For further information visit https://errors.pydantic.dev/2.13/v/dict_type |
| 200 | `/api/v1/dashboard/search-usage` |     For further information visit https://errors.pydantic.dev/2.13/v/dict_type |
| 200 | `/api/v1/dashboard/upload-status` | INFO:     192.168.10.39:33702 - "GET /api/v1/dashboard/search-errors HTTP/1.1" 200 OK |
| 200 | `/api/v1/audit-logs` | INFO:     192.168.10.39:33702 - "GET /api/v1/dashboard/search-errors HTTP/1.1" 200 OK |
| 200 | `/api/v1/projects` | INFO:     192.168.10.39:33702 - "GET /api/v1/dashboard/search-errors HTTP/1.1" 200 OK |
| 200 | `/api/v1/projects/tree` | INFO:     192.168.10.39:33702 - "GET /api/v1/dashboard/search-errors HTTP/1.1" 200 OK |
| 200 | `/api/v1/reports` | INFO:     192.168.10.39:33702 - "GET /api/v1/dashboard/search-errors HTTP/1.1" 200 OK |
| 200 | `/api/v1/reports/templates` | INFO:     192.168.10.39:33702 - "GET /api/v1/dashboard/search-errors HTTP/1.1" 200 OK |
| 200 | `/api/v1/search-scopes` | INFO:     192.168.10.39:33702 - "GET /api/v1/dashboard/search-errors HTTP/1.1" 200 OK |
| 422 | `/api/v1/users` | — |
