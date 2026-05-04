# AgentHub 금지 패턴

이 패턴들은 절대 허용되지 않는다.

## 1. LLM SDK 직접 호출

```csharp
// BAD — Service 안에서 OpenAI/Anthropic SDK를 직접 사용
using OpenAI_API;
var openai = new OpenAIAPI(apiKey);
var resp = await openai.Chat.CreateChatCompletionAsync(...);

// GOOD — IAiProxyService를 통해서만 호출
public class MyService(IAiProxyService aiProxy) {
    public async Task DoAsync() {
        var resp = await aiProxy.SendChatAsync(serviceType, model, messages, ct);
    }
}
```

이유: 프로바이더 전환, 키 풀 라운드로빈, 사용량 기록, PII 차단이 모두 `AiProxyService`에 집중되어 있다.

## 2. HttpClient 직접 인스턴스화

```csharp
// BAD — 연결 풀 누수 + 타임아웃 미설정
var client = new HttpClient();
await client.PostAsync(url, content);

// GOOD — Named HttpClient 풀 사용
public class MyService(IHttpClientFactory httpClientFactory) {
    public async Task DoAsync() {
        var client = httpClientFactory.CreateClient("openai"); // Program.cs에 등록된 이름
        await client.PostAsync(url, content);
    }
}
```

## 3. 하드코딩된 설정

```csharp
// BAD
const string OPENAI_URL = "https://api.openai.com/v1";
const int TIMEOUT_SEC = 60;

// GOOD
public class MyService(IConfiguration config) {
    private readonly string _baseUrl = config["AiApiSettings:OpenAI:BaseUrl"]!;
    private readonly int _timeout = config.GetValue<int>("AiApiSettings:DefaultTimeout", 120);
}
```

## 4. Frontend 하드코딩 API URL

```typescript
// BAD
fetch("http://localhost:5001/api/agents")

// GOOD — services/api.ts의 axios 인스턴스 사용
import api from "@/services/api"
const { data } = await api.get("/api/agents")
```

Vite proxy + `axios.defaults.baseURL`이 환경별 라우팅을 처리한다.

## 5. Repository 패턴 도입

```csharp
// BAD — 이 프로젝트는 Repository를 쓰지 않는다
public interface IUserRepository { Task<User?> GetByIdAsync(int id); }

// GOOD — Service가 DbContext를 직접 사용
public class UserService(AIAgentManagementDbContext db) {
    public Task<User?> GetByIdAsync(int id) => db.Users.FindAsync(id).AsTask();
}
```

이유: EF Core의 `DbSet<T>` + LINQ가 이미 Repository 역할. 한 겹 더 추가하면 abstraction tax만 늘어난다.

## 6. Middleware에서 DbContext 직접 사용

```csharp
// BAD — 미들웨어는 매 요청 핫패스 — DB I/O가 추가되면 전체 지연
public async Task InvokeAsync(HttpContext context, AIAgentManagementDbContext db) {
    db.ActivityLogs.Add(...);
    await db.SaveChangesAsync();
}

// GOOD — 비동기 채널로 분리
public async Task InvokeAsync(HttpContext context, ActivityLogChannel channel) {
    await channel.WriteAsync(activityLog); // ActivityLogWorker가 배치 처리
}
```

## 7. Singleton에서 Scoped 직접 주입

```csharp
// BAD — captive dependency, DbContext가 영구 살아있게 됨
public class CachingService {
    public CachingService(AIAgentManagementDbContext db) { ... }
}

// GOOD — IServiceScopeFactory로 필요할 때만 스코프 생성
public class CachingService(IServiceScopeFactory scopeFactory) {
    public async Task RefreshAsync() {
        using var scope = scopeFactory.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AIAgentManagementDbContext>();
    }
}
```

## 8. 사용자 메시지에 영문 사용

```csharp
// BAD
return BadRequest(new ErrorResponseDto("Invalid input", "VALIDATION_ERROR", null));

// GOOD
return BadRequest(new ErrorResponseDto("입력값이 올바르지 않습니다.", "VALIDATION_ERROR", null));
```

내부 로그(`logger.LogWarning(...)`)는 영문/한글 모두 허용. 사용자에게 노출되는 응답 본문/메시지만 한국어.

## 9. 새 SQL 마이그레이션 파일을 루트에 추가

```
# BAD — 루트의 *.sql은 레거시
AddNewFeatureTable.sql  # 추가 금지

# GOOD — EF Core 마이그레이션
dotnet ef migrations add AddNewFeatureTable
```

루트의 기존 `Add*.sql` / `Create*.sql` 파일은 EF 마이그레이션 도입 이전의 일회성 패치 — 보존만 하고 새로 만들지 않는다.

## 10. Bare catch / 예외 무시

```csharp
// BAD
try { ... } catch { }
try { ... } catch (Exception) { /* swallow */ }

// GOOD — 최소한 로그 + 사용자에게 의미 있는 응답
try {
    await _aiProxy.SendChatAsync(...);
} catch (HttpRequestException ex) {
    _logger.LogError(ex, "AI 프로바이더 호출 실패: {Provider}", provider);
    return StatusCode(502, new ErrorResponseDto("외부 AI 서비스에 연결할 수 없습니다.", "UPSTREAM_ERROR", null));
}
```

`Program.cs`의 DB 초기화 / Hangfire 등록 블록은 예외를 삼키는 것이 의도된 동작 — 기능 누락만으로 앱이 죽지 않게 함. 이 패턴을 비즈니스 코드로 확산시키지 않는다.

## 11. Vue 컴포넌트에서 axios 직접 사용

```typescript
// BAD
import axios from 'axios'
const { data } = await axios.get('/api/agents')

// GOOD
import api from '@/services/api'           // 인터셉터: JWT 자동 부착, 401 갱신
import { agentService } from '@/services/agentService' // 도메인별 래퍼
const agents = await agentService.list()
```

JWT 자동 부착, 401 시 토큰 갱신, 에러 통일 처리가 인터셉터에 있다.

## 12. PII 검사 우회

```csharp
// BAD — 사용자 입력을 그대로 LLM에 전송
var resp = await _aiProxy.SendChatAsync(serviceType, model, userMessages, ct);

// GOOD — PII 검출 + 금칙어 검사
var detected = await _piiService.DetectAndMaskAsync(userMessage, userId);
if (detected.HasBlockedPii) return BadRequest(...);
var sanitized = await _bannedWord.ScrubAsync(detected.Text);
```

모든 사용자 입력은 LLM 전송 전 `IPiiDetectionService` + `IBannedWordService` 통과.

## 13. SignalR Hub 메서드에서 DB/LLM 직접 호출

```csharp
// BAD — Hub 메서드가 길어지면 SignalR 연결이 막힘
public async Task SendMessage(string text) {
    var resp = await _aiProxy.SendChatAsync(...);  // 수 초 소요
    await Clients.Caller.SendAsync("ReceiveMessage", resp);
}

// GOOD — Hub는 라우팅만, 무거운 작업은 REST + 푸시
// Client → POST /api/chat/messages → ChatService → ChatHub.PushAsync(userId, response)
```

## 14. 프로덕션 비밀번호 / 시크릿 커밋

`appsettings.Production.json`의 실제 값, `.env`, 연결 문자열의 비밀번호는 **절대 git에 포함하지 않는다**.
- `.gitignore`에 추가 확인
- IIS 환경 변수 또는 Azure Key Vault 등 외부 비밀 저장소 사용
- `Program.cs`에서 비밀번호를 로깅할 때 마스킹 (`Replace("Password=...", "Password=***")` 패턴 유지)
