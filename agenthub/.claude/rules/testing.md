# AgentHub 테스트 전략

## 현재 상태

이 프로젝트는 정식 단위 테스트 인프라가 아직 구축되지 않은 상태다.
`test_e2e_server.py`, `test_scenario.py`, `performance-tests/`는 외부 시나리오 검증용 스크립트 — xUnit 단위 테스트와 별개.

신규 기능 추가 시 이 문서의 가이드를 따라 점진적으로 테스트 자산을 확보한다.

## 권장 구조

```
AIAgentManagement.Tests/                  # 새 테스트 프로젝트 (별도 .csproj)
├── Unit/
│   ├── Services/                         # Service 단위 — DbContext In-Memory, HttpClient mock
│   └── Utils/                            # 순수 함수 / 헬퍼
├── Integration/
│   ├── Controllers/                      # WebApplicationFactory + TestServer
│   └── Hangfire/                         # 작업 등록/실행 검증
└── E2E/
    └── (기존 test_e2e_server.py를 흡수하거나 Playwright로 마이그레이션)
```

도구: **xUnit** + **FluentAssertions** + **Moq** + **Microsoft.AspNetCore.Mvc.Testing** + **EFCore.InMemory**

## 우선순위가 높은 테스트 대상

1. **AiProxyService** — 프로바이더별 분기, 타임아웃, Rate Limit, API Key 풀 라운드로빈
2. **ApiKeyAuthService** + **ApiKeyRateLimiter** — 인증 거부 시나리오, 분/시/일 카운터 리셋
3. **ChatService** — RAG 활성화/비활성화, PII 차단 흐름, 토큰 집계
4. **WorkflowEngine** — 노드 그래프 실행 순서, 조건 분기, 실패 시 부분 롤백
5. **ToolExecutionService** + 3종 Executor — Roslyn 컴파일 에러, 스크립트 타임아웃, API 호출 실패
6. **PiiDetectionService** — 한국어 주민번호/카드번호 패턴, false positive 방지
7. **BannedWordService** — 캐시 무효화, 카테고리별 매칭
8. **GlobalExceptionHandlerMiddleware** — `ErrorResponseDto` 변환, 상태 코드 매핑
9. **JwtService** — 만료, 서명 검증, Refresh Token 회전
10. **DatabaseInitializer** — 시드의 멱등성

## 외부 의존성 Mock 전략

| 대상 | 권장 Mock | 이유 |
|---|---|---|
| `HttpClient` (LLM 호출) | `IHttpClientFactory` mock + `Moq.Contrib.HttpClient` 또는 `MockHttpMessageHandler` | 외부 API 호출 차단 |
| `AIAgentManagementDbContext` | `UseInMemoryDatabase()` 또는 `Sqlite(":memory:")` | 마이그레이션 검증 시 SQLite 권장 |
| `IDistributedCache` (Redis) | 인메모리 구현 직접 주입 | Redis 미설치 환경에서도 통과 |
| `IRecurringJobManager` (Hangfire) | `Moq` | 등록 호출만 검증 |
| `IHubContext<ChatHub>` | `Moq` — `Clients.User(...).SendAsync(...)` 호출 검증 | SignalR 연결 불필요 |
| 파일 시스템 | `tmp_path` 패턴 — `Path.GetTempPath()` 하위 임시 디렉토리 | 실제 wwwroot 오염 금지 |
| LibreOffice 변환 | 경로 존재 검사를 mock하여 우회 | CI에서 LibreOffice 미설치 |

## 테스트 명명 규칙

```
public class {ServiceName}Tests
{
    [Fact] public async Task {Method}_{Scenario}_{ExpectedOutcome}() { ... }
}

예시:
- AiProxyService_SendChat_OpenAiProvider_ReturnsCompletion
- ApiKeyRateLimiter_ExceedDaily_ReturnsRateLimitExceeded
- ChatService_PiiDetected_ReturnsBlockedResponse
- WorkflowEngine_ConditionalBranch_TrueBranch_Executes
```

## 통합 테스트 패턴

```csharp
public class AgentsControllerTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;
    public AgentsControllerTests(WebApplicationFactory<Program> factory) {
        _client = factory.WithWebHostBuilder(b => b.ConfigureServices(s => {
            // 외부 의존성 교체: Redis, HttpClient, ...
            s.AddDbContext<AIAgentManagementDbContext>(opt =>
                opt.UseInMemoryDatabase($"test-{Guid.NewGuid()}"));
        })).CreateClient();
    }

    [Fact]
    public async Task GetAgents_Authenticated_ReturnsList() {
        _client.DefaultRequestHeaders.Authorization =
            new AuthenticationHeaderValue("Bearer", TestTokens.AdminToken);

        var resp = await _client.GetAsync("/api/agents");

        resp.StatusCode.Should().Be(HttpStatusCode.OK);
    }
}
```

## 테스트 금지사항

- 테스트 간 실행 순서 의존 금지 — 각 테스트는 독립적
- 실제 OpenAI/Claude API 호출 금지 — 비용 + 결과 비결정성
- 실제 SQL Server 연결 금지 — InMemory 또는 Sqlite InMemory 사용
- 실제 Redis 연결 금지 — 위 표 참조
- `Thread.Sleep()` 금지 — `await Task.Delay(...)` + `CancellationToken` 사용
- 프로젝트 wwwroot/uploads 디렉토리에 파일 생성 금지 — `Path.GetTempPath()` 사용

## CI 게이트 (도입 시)

다음 순서로 실행:
1. `dotnet build --warnaserror`
2. `dotnet test --no-build --filter "Category=Unit"`
3. `dotnet test --no-build --filter "Category=Integration"`
4. `cd ClientApp && npm run build:check`

위 4단계 모두 통과해야 PR 머지 허용.

## 수동 점검 체크리스트 (테스트 부재 영역)

자동 테스트가 미비한 동안 다음을 PR마다 수동 점검:

- [ ] `dotnet build` 워닝 0건
- [ ] `npm run build:check` 통과
- [ ] 새 EF 마이그레이션 추가 시 → 빈 DB에 `database update` 실행 확인
- [ ] 새 LLM 프로바이더 추가 시 → Playground에서 1회 호출 + 사용량 기록 확인
- [ ] 새 컨트롤러 추가 시 → Swagger UI에서 인증 헤더 + 응답 스키마 확인
- [ ] PII / BannedWord 영향이 있는 변경 → 알려진 시나리오 수동 검증
- [ ] 프론트엔드 변경 → `agenthub.idino.co.kr` 로컬 빌드 후 라우팅/i18n 점검
