# AgentHub AI 코딩 협업 규칙

Claude Code 또는 다른 AI 코딩 도구가 이 프로젝트에서 작업할 때 따라야 하는 절차.

## 코드 작성 전

1. 수정할 파일을 반드시 먼저 `Read`로 읽는다 — 기존 패턴을 깨지 않기 위함
2. 관련 인터페이스(`I{Name}Service.cs`)를 먼저 확인 — 시그니처가 계약이다
3. `Program.cs`에서 해당 서비스가 어떤 Lifetime(`AddSingleton`/`AddScoped`)으로 등록되었는지 확인
4. EF 엔티티 변경이 필요한 경우 → 기존 마이그레이션이 있는지 확인하고 새 마이그레이션 추가
5. 3개 이상 파일을 수정해야 한다면 → 한글 계획서를 먼저 제시하고 사용자 확인 후 진행

## 코드 작성 중

1. **인터페이스 우선 변경** — `I{Name}Service.cs`에 메서드를 먼저 추가하고 구현체를 따라간다
2. **DTO는 외부 표면** — 새 필드는 항상 DTO에 추가하고 Entity → DTO 매핑 로직을 명시
3. **DI 등록 누락 금지** — 새 서비스 추가 시 반드시 `Program.cs`의 `builder.Services.Add{Lifetime}<...>()` 블록에 등록
4. **CancellationToken 전달** — 외부 I/O(`HttpClient`, `DbContext`)를 호출하는 모든 비동기 메서드는 `ct` 파라미터를 받아 끝까지 전파
5. **로그**: `ILogger<T>` 주입 — 한글/영문 무관, 단 PII나 시크릿은 마스킹
6. **사용자 응답 메시지는 한국어** — `ErrorResponseDto.Message`, RateLimit 응답, Validation 메시지
7. **EF Core 쿼리는 `AsNoTracking()` 기본** — 쓰기 작업이 아닌 조회는 명시적으로 적용
8. **Frontend**: 새 페이지는 `views/`에, 라우트는 `router/index.ts`에, API 호출은 `services/`에, 상태는 `stores/`에 — 한 컴포넌트에 모두 넣지 않는다

## 코드 작성 후

1. `dotnet build` 통과 확인 — 워닝도 가급적 제거
2. EF 모델 변경 시 → `dotnet ef migrations add {Name}` 실행하여 마이그레이션 생성
3. 프론트엔드 변경 시 → `cd ClientApp && npm run build:check` (vue-tsc로 타입 검사)
4. API 응답 스키마가 변경되면 → 프론트엔드의 해당 `services/`와 `types/` 동기화
5. 변경 요약을 한국어로 작성

## 커밋 메시지 형식

```
[모듈] 한글 설명

예시:
[chat] WebSocket 재연결 안정화 - 5초 백오프 적용
[agent] RAG 검색 결과 캐싱 도입 — Redis 30분 TTL
[auth] API Key 라운드로빈 풀 구현
[frontend/playground] 모델 선택 드롭다운 다국어화
```

## 변경 시 함께 점검할 항목

EF 엔티티 변경 → DTO, Service, DbContext, Migration  
새 LLM 프로바이더 추가 → `appsettings.json`, Named HttpClient(`Program.cs`), `IAiProxyService` 분기, `ApiServices` 시드  
새 Background Job → `BackgroundJobs/`에 클래스, `Program.cs`의 `AddScoped` + `AddOrUpdate` 등록  
새 SignalR 이벤트 → Hub 메서드 + Service 호출 + Frontend `services/signalr*.ts`  
새 권한이 필요한 컨트롤러 → `[Authorize(Roles = "Admin")]` 부착 + Frontend route guard 동기화

## 자주 사용하는 도구 / 위치

| 작업 | 위치 |
|---|---|
| LLM 호출 | `Services/AiProxyService.cs` |
| 채팅 흐름 | `Services/ChatService.cs` + `Hubs/ChatHub.cs` |
| API Key 인증 | `Attributes/`의 `[ApiKeyAuth]` + `Services/ApiKeyAuthService.cs` |
| 실시간 알림 | `Services/NotificationService.cs` → `Hubs/NotificationHub.cs` |
| 워크플로우 실행 | `Services/WorkflowEngine.cs` + `Services/WorkflowExecutionService.cs` |
| 도구 실행 | `Services/ToolExecutionService.cs` (C# / Script / API 분기) |
| 파일 파싱 | `Services/FileParsingService.cs` (PDF/Excel/Word/PPTX/HWP) |
| PPTX 생성 | `Services/PptxGenerationService.cs` + `Services/PresentationService.cs` |
| 시드 데이터 | `Data/DatabaseInitializer.cs` |

## 위험 작업 — 사용자 확인 필요

다음 작업은 **반드시 사용자 확인을 받은 후** 실행한다:

- `Migrations/` 폴더의 기존 마이그레이션 수정/삭제
- `appsettings.Production.json` 변경
- `Models/` 엔티티의 컬럼 삭제 (데이터 손실 위험)
- 루트의 레거시 `*.sql` 파일 실행
- `Tools/ResetAllUsersPassword.cs` 호출
- IIS 배포 (`web.config`, `iis-setting.ps1`)
- `dotnet ef database update` 프로덕션 DB 대상 실행
