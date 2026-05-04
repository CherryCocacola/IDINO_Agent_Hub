# AgentHub 아키텍처 원칙

## P1. 단일 진입점 (Single Entry Point per Concern)

각 횡단 관심사는 단 하나의 진입 지점만 가진다.

| 관심사 | 단일 진입점 | 직접 호출 금지 대상 |
|---|---|---|
| LLM 호출 | `IAiProxyService` | `HttpClient` 직접 호출, OpenAI/Anthropic SDK 직접 사용 |
| 설정 값 | `IConfiguration` / Options | 하드코딩된 URL/포트/키 |
| 인증 토큰 | `IJwtService` | `JwtSecurityTokenHandler` 직접 인스턴스화 |
| API Key 검증 | `IApiKeyAuthService` + `IApiKeyRateLimiter` | DB에서 ApiKey 직접 조회 |
| 활동 로그 | `ActivityLogChannel` (비동기 채널) | DB 직접 INSERT (미들웨어에서) |
| 캐시 | `CachingService` (singleton) | `IMemoryCache` 직접 주입 |
| 백그라운드 작업 | Hangfire `IRecurringJobManager` | `Task.Run`으로 영속 작업 실행 |
| 임베딩 | `IEmbeddingService` | OpenAI Embeddings API 직접 호출 |
| 파일 파싱 | `IFileParsingService` | OpenXml/PdfPig 직접 사용 (Service 레이어 외에서) |

## P2. 계층 구조 — 표준 모듈

신규 기능 추가 시 다음 6개 파일 셋만 만든다 (필요한 것만):

```
Controllers/{Resource}Controller.cs   # HTTP 진입, 경량
Services/I{Resource}Service.cs        # 인터페이스
Services/{Resource}Service.cs         # 비즈니스 로직
Models/{Entity}.cs                    # EF 엔티티 (필요 시)
DTOs/{Action}{Resource}Dto.cs         # 요청/응답 DTO
Migrations/...                        # `dotnet ef migrations add`로 자동 생성
```

다음 패턴은 거부한다:
- `*Helper.cs`, `*Manager.cs`, `*Handler.cs` (Controller가 아님에도 비즈니스 로직 보유)
- `*Repository.cs` — 이 프로젝트는 Repository 패턴을 쓰지 않는다. Service가 DbContext를 직접 사용
- Service 안의 정적 헬퍼 메서드 누적 → 별도 클래스가 필요하면 `Utils/` 또는 `Infrastructure/`로

## P3. 의존성 방향 (단방향)

```
Controllers / Hubs / Middleware
        ↓
     Services (I{Name}Service)
        ↓
   DbContext / HttpClient / Hangfire / Redis
```

- **Controller가 다른 Controller를 호출하지 않는다** — 공통 로직은 Service로
- **Service가 다른 Service를 호출하는 것은 허용**되지만, 순환 의존이 발생하면 호출자를 Controller 레벨에서 조립
- **Middleware는 Service를 통한 비즈니스 호출 금지** — 비동기 채널(예: `ActivityLogChannel`)에 메시지만 넣는다
- **Hub에서 무거운 작업은 Service로 위임**하고 즉시 반환 (SignalR 연결을 막지 않는다)

## P4. DI 수명 주기

| Lifetime | 사용 시점 | 예시 |
|---|---|---|
| Singleton | 상태를 메모리에 유지해야 하는 컴포넌트 | `IJwtService`, `CachingService`, `IApiKeyRateLimiter`, `IApiKeyPoolService`, `ActivityLogChannel` |
| Scoped | DbContext에 의존하는 모든 서비스 | 거의 모든 `I*Service` |
| Transient | 매번 새 인스턴스가 안전한 가벼운 헬퍼 | (현재 프로젝트에서 거의 사용 안 함) |

- **Singleton에서 Scoped 주입 금지** — `IServiceScopeFactory.CreateScope()`로 명시적으로 스코프 생성
- **`HttpContextAccessor`는 Singleton 안전** — Microsoft 권장

## P5. JSON 직렬화 규약

- **C# 내부**: PascalCase (`UserId`, `CreatedAt`)
- **API 외부 표면**: camelCase (`Program.cs`에서 `JsonNamingPolicy.CamelCase` 전역 적용)
- **`Dictionary<string, object>` 필드** (예: `ChartDto.Data`): `JsonElementRawConverter` + `DictionaryStringObjectJsonConverter` 적용 — 이를 우회하지 않는다
- **DB JSON 컬럼**: Models 레이어에서 `[Column(TypeName = "nvarchar(max)")]` + Service에서 `JsonSerializer.Serialize/Deserialize`로 명시 변환

## P6. 에러 처리

- **모든 예외는 `GlobalExceptionHandlerMiddleware`로 수렴** → `ErrorResponseDto`로 변환
- **컨트롤러에서 비즈니스 검증 실패** → `return BadRequest(new ErrorResponseDto(message, errorCode, details))`
- **모델 검증 실패**는 `Program.cs`의 `InvalidModelStateResponseFactory`가 자동으로 `ErrorResponseDto`로 변환 — Controller가 다시 처리하지 않는다
- **사용자향 메시지는 반드시 한국어**
- **`catch (Exception)` 단독 사용 금지** — 구체 예외 또는 `Exception ex`로 받아 로그에 타입 명시

## P7. Rate Limiting 정책 분리

`Program.cs`의 3개 정책을 컨트롤러에 명시적으로 부착한다:

| 정책 | 용도 | 키 |
|---|---|---|
| `ip-guest` | 게스트 공개 채팅 (분당 20) | RemoteIpAddress |
| `ip-openai` | OpenAI 호환 API `/v1/*` (분당 30) | RemoteIpAddress |
| `per-user` | 로그인 사용자 API (분당 60) | userId or IP |

추가로 LLM 프로바이더별 API Key 풀의 자체 Rate Limiter (`IApiKeyRateLimiter`)는 **외부 호출 시점**에 적용 — IP/사용자 레이어와 별개로 동작.

## P8. Hangfire 작업 등록

- `Program.cs`의 `recurringJobManager.AddOrUpdate()` 블록에서만 등록
- 작업 본체는 `BackgroundJobs/`에 두고 Scoped 서비스를 `IServiceProvider`에서 해석
- DB 연결이 없으면 Hangfire 자체를 등록하지 않음 (현재 try-catch 패턴 유지)

## P9. SignalR 메시지 흐름

- 채팅: 클라이언트 → REST API (`POST /api/chat/.../messages`) → Service에서 LLM 호출 → 결과를 `ChatHub.SendAsync()`로 푸시
- 알림: Service에서 `INotificationService.NotifyUserAsync()` → 내부에서 `NotificationHub` 사용
- **클라이언트가 Hub 메서드를 직접 호출하여 LLM을 트리거하지 않는다** — 항상 REST 경유

## P10. 마이그레이션 정책

- **새 스키마 변경**: `dotnet ef migrations add {DescriptiveName}` → `Migrations/`에 추가
- **루트의 `*.sql` 파일은 레거시 일회성 스크립트** — 새로 생성 금지, 참조용으로만 보존
- **시드 데이터**: `Data/DatabaseInitializer.SeedAsync()`에 코드로 추가 (멱등성 보장 — 존재 검사 후 INSERT)
