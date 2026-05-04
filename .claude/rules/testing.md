# IDINO Agent Hub — 통합 테스트 전략

## 현황

각 서브프로젝트의 테스트 성숙도가 다르다:

| 서브프로젝트 | 현재 상태 |
|---|---|
| `agenthub` | 정식 단위 테스트 인프라 미구축 (e2e 스크립트만) |
| `docutil` | `pytest` + 일부 e2e (`scripts/qa.bat` / `qa.sh`) |
| `career` | playwright e2e 일부 |
| `nexus` | `tests/{unit,integration,e2e}/` 구조 정립 |

**권장 방향**: 각자 도구 유지하되, **통합 테스트는 monorepo 루트에서 실행**.

## 테스트 계층 정의

### 1. Unit Test (서브프로젝트 내부)
- 각 서브프로젝트가 자체 도구 사용
  - agenthub: xUnit + Moq (도입 필요)
  - docutil: pytest + pytest-asyncio
  - career: pytest + 각 MS별
  - nexus: pytest + pytest-asyncio
- 외부 의존성 mock (DB, HTTP, Redis)

### 2. Integration Test (서브프로젝트 단위)
- 같은 서브프로젝트 내부의 다중 컴포넌트 테스트
- 진짜 DB(InMemory 또는 Testcontainers PostgreSQL) 사용

### 3. Cross-System Integration Test (monorepo 차원)
- **신규 도입 필요** — 통합의 핵심 검증
- 위치: `tests/integration/` (monorepo 루트)
- 시나리오:
  - DocUtil → AgentHub `/v1/chat/completions` 호출 → External LLM 응답
  - DocUtil → AgentHub → Nexus `/v1/chat` 응답 (Internal 라우팅)
  - career → AgentHub Agent → RAG (DocUtil) → 응답
  - AgentHub 운영자 KB 등록 → DocUtil에 collection 생성 확인
- 도구: pytest + httpx + docker-compose (테스트 스택)

### 4. E2E Test
- 사용자 시나리오 전체 (UI 포함)
- 도구: Playwright (Next.js) + Puppeteer (필요 시)
- 위치: 각 사용자 앱(`docutil/frontend/e2e/`, `career/frontend/e2e/`)

## 우선순위 테스트 대상 (통합 차원)

1. **AgentHub의 Nexus provider** (`AiProxyService.CallNexusAsync`)
   - mock Nexus 서버로 응답 검증
   - 실제 Nexus 인스턴스로 통합 시나리오
2. **AgentHub의 LLM 라우팅 결정 엔진** (`HybridRouter`)
   - PII 감지 → Internal 강제
   - 데이터 라벨별 분기
   - 비용 한도 초과 처리
3. **AgentHub `/v1/chat/completions` SSE 스트리밍** (현재 가짜 SSE → 진짜 SSE 변경 검증)
4. **DocUtil → AgentHub Agent API 클라이언트**
5. **career의 각 MS → AgentHub Agent API 클라이언트**
6. **DB 스키마 격리** — Cross-schema 조인 시도가 실패하는지
7. **API Key 인증 + 스코프 + Rate Limit**
8. **운영자 KB 등록 → DocUtil 동기화**

## 외부 의존성 Mock 전략

| 대상 | Mock 방법 |
|---|---|
| External LLM (OpenAI/Claude/...) | `Moq.Contrib.HttpClient` (.NET), `respx` (Python) |
| Nexus | mock FastAPI 서버 또는 stub 응답 fixture |
| DocUtil API | mock FastAPI 서버 |
| PostgreSQL | Testcontainers PostgreSQL 또는 SQLite InMemory (.NET) |
| Redis | `fakeredis.aioredis`, redis-mock (Node.js) |
| Qdrant | mock 클라이언트 또는 docker-compose |
| SignalR | `Moq IHubContext` |

## 테스트 환경

### 로컬 통합 테스트 스택 (`docker-compose.test.yml`)
```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: AGENT_HUB
      POSTGRES_USER: AGENT_HUB
      POSTGRES_PASSWORD: idino!@#$
  redis:
    image: redis:7
  qdrant:
    image: qdrant/qdrant
  nexus-mock:
    build: tests/mocks/nexus-mock
    ports: ["18000:8001"]
  docutil-mock:
    build: tests/mocks/docutil-mock
    ports: ["18100:8000"]
  agenthub:
    build: ./agenthub
    depends_on: [postgres, redis]
    environment:
      ConnectionStrings__DefaultConnection: "Host=postgres;..."
```

## 테스트 명명 규칙

```
test_{feature}_{scenario}_{expected_outcome}

예시:
test_aiproxy_nexus_routing_returns_nexus_response
test_hybrid_router_pii_detected_routes_to_internal
test_docutil_chat_via_agenthub_returns_streaming
test_career_coaching_agent_with_rag_includes_context
test_apikey_invalid_scope_returns_403
```

## CI 게이트 (도입 시)

```
1. lint:
   - agenthub: dotnet format --verify-no-changes
   - docutil/backend: ruff check .
   - docutil/frontend: eslint .
   - career: 동일
   - nexus: ruff check .
2. type-check:
   - agenthub/ClientApp: vue-tsc --noEmit
   - docutil/frontend: tsc --noEmit
   - career/frontend: tsc --noEmit
3. unit:
   - dotnet test
   - pytest (각 서브프로젝트)
4. integration (Cross-System):
   - docker-compose -f docker-compose.test.yml up
   - pytest tests/integration/
5. e2e:
   - playwright (선택, smoke만)
```

전 단계 통과해야 PR 머지 허용.

## 테스트 금지사항

- 실제 OpenAI/Claude API 호출 금지 (비용 + 결과 비결정성)
- 실제 운영 PostgreSQL 인스턴스 접근 금지 (테스트용 컨테이너만)
- 실제 Nexus 인스턴스 호출은 통합 테스트 중에서도 별도 환경 변수로 제어 (`INTEGRATION_TEST_REAL_NEXUS=true`)
- 테스트 간 실행 순서 의존 금지
- 프로젝트 wwwroot/uploads/data 디렉토리 오염 금지 — 임시 디렉토리 사용

## 수동 점검 체크리스트 (테스트 부재 영역)

자동화 도입 전까지 PR마다 수동 점검:

- [ ] 각 서브프로젝트 build 워닝 0건
- [ ] type-check 통과
- [ ] AgentHub Agent 새로 만들고 외부에서 호출 시 정상 응답
- [ ] PII가 포함된 입력 → Block/Mask 정책에 따라 동작
- [ ] Internal 라우팅 시 Nexus 호출, External 라우팅 시 OpenAI 호출 (로그 확인)
- [ ] DocUtil/career에서 AgentHub Agent 호출 → 응답 받음
- [ ] DB 마이그레이션 후 빈 환경에서 정상 동작
- [ ] 시크릿이 git에 커밋되지 않았는지 (git-secrets 또는 trufflehog)
