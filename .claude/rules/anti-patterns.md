# IDINO Agent Hub — 통합 금지 패턴

이 패턴들은 monorepo 어디에서도 절대 허용되지 않는다. 서브프로젝트별 자체 anti-patterns는 별도 유지.

## 1. End-User 앱이 LLM SDK를 직접 호출

```python
# BAD — docutil/career에서 OpenAI/Anthropic SDK 직접 사용
from openai import AsyncOpenAI
client = AsyncOpenAI()
resp = await client.chat.completions.create(...)

# GOOD — AgentHub Agent API 호출
import httpx
async with httpx.AsyncClient(base_url=AGENTHUB_URL) as client:
    resp = await client.post(
        "/v1/chat/completions",
        headers={"X-API-Key": API_KEY},
        json={"model": "agent-customer-support", "messages": [...]}
    )
```

이유: 라우팅(External/Internal), 사용량 추적, PII 차단, 캐싱이 모두 AgentHub에 집중되어 있어야 한다.

## 2. AgentHub가 Nexus를 OpenAI 호환 어댑터 없이 강제 변환

```csharp
// BAD — Nexus의 세션/멀티테넌시 강점을 잃는 변환
// (옵션 A 패턴, 우리는 옵션 B 채택)

// GOOD — Nexus의 네이티브 API를 그대로 호출
case "nexus":
    return await CallNexusAsync(request, ct);  // /v1/chat 호출
```

옵션 B 채택. AgentHub가 프로바이더별 네이티브 API를 호출하는 기존 패턴(Claude/Gemini도 그러함)과 일치.

## 3. Cross-Schema 조인 (DB 통합 후)

```sql
-- BAD — 다른 서브프로젝트 스키마 직접 조인
SELECT a.*, c.* FROM "AIAgentManagement"."Agents" a
JOIN "idino_career"."students" c ON c.agent_id = a."AgentId";

-- GOOD — API 호출로 데이터 합성
-- agenthub는 자기 스키마만, career는 자기 스키마만 접근
```

스키마 격리가 깨지면 통합의 모든 의미가 사라진다. 데이터가 필요하면 HTTP API.

## 4. 시크릿 평문 커밋

```yaml
# BAD — appsettings/yaml/env에 평문
postgresql:
  password: "idino@12"
```

```bash
# BAD — 코드 하드코딩
const string CONN = "Server=...;Password=idino@12;..."
```

```csharp
// BAD — 마스킹 가짜
connectionString.Replace("Password=idino@12", "Password=***")
```

`.env` / `appsettings.*.json`은 모두 `.gitignore` 대상. 마스킹은 운영 로그용일 뿐, 정답은 환경변수 또는 vault.

## 5. 운영자 화면을 End-User 앱에 잔존

```typescript
// BAD — docutil(사용자 화면)에 KB 관리/문서 업로드 UI가 그대로 남음
<Route path="/admin/knowledge-base" element={<AdminKBPage />} />

// GOOD — 운영자 기능은 AgentHub UI로 일원화, 링크만 제공
<a href={AGENTHUB_URL + "/admin/knowledge-base"}>관리자 콘솔</a>
```

운영자 = AgentHub. 사용자 앱에 운영자 페이지가 남아 있으면 권한/UX/보안 모두 깨진다.

## 6. 서브프로젝트 간 직접 import

```python
# BAD — docutil이 career의 코드 직접 import
from career.services.coaching import CoachingService
```

```csharp
// BAD — agenthub이 docutil 모듈 import 시도
// (사실상 불가능하지만 패턴으로 금지)
```

서브프로젝트는 다른 언어/런타임이고 통합 후에도 독립 배포되어야 한다. 통신은 HTTP/SSE/Channel만.

## 7. AgentHub 자체 KnowledgeBase에 신규 문서 추가

```csharp
// BAD — Phase 6 이후 AgentHub의 자체 KB에 문서 직접 INSERT
_dbContext.KnowledgeBaseDocuments.Add(new KnowledgeBaseDocument { ... });

// GOOD — DocUtil API 호출로 위임
await _docutilClient.UploadDocumentAsync(file, collectionId);
```

AgentHub의 자체 KB는 deprecate. 모든 RAG는 DocUtil로.

## 8. Hardcoded External LLM URL

```python
# BAD
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
resp = await httpx.post(OPENAI_URL, ...)
```

External LLM 호출은 AgentHub만의 권한. End-User 앱은 AgentHub URL만 알면 된다.

## 9. Nexus를 외부망에 노출

```yaml
# BAD — Nexus의 /v1/chat을 인터넷에 공개
nexus.example.com:443 -> 192.168.22.28:8001
```

Nexus는 LAN-only. AgentHub만 호출 가능. 에어갭 모드(`air_gap_mode: true`) 유지.

## 10. UTF-8/한국어 처리 비일관성

```python
# BAD — Latin-1 인코딩으로 한글 파일명 손상
filename.encode('latin-1')
```

```python
# GOOD — RFC 5987
from urllib.parse import quote
headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
```

DocUtil의 기존 규칙(`.claude/rules/anti-patterns.md`) 동일.

## 11. 마이그레이션 우회

```csharp
// BAD — EnsureCreatedAsync 사용 (drift 위험)
await context.Database.EnsureCreatedAsync();

// GOOD — Migration 적용
await context.Database.MigrateAsync();
```

AgentHub 통합 작업 시 baseline 마이그레이션을 작성하고 `MigrateAsync`로 전환한다.

## 12. SignalR Hub에 인증 부재 (AgentHub)

```csharp
// BAD — JoinUserNotifications(int userId) 클라이언트가 임의 ID 입력
public async Task JoinUserNotifications(int userId) {
    await Groups.AddToGroupAsync(ConnectionId, $"user_{userId}");
}

// GOOD — Context.UserIdentifier 사용
[Authorize]
public class NotificationHub : Hub {
    public async Task JoinUserNotifications() {
        var userId = Context.UserIdentifier;
        await Groups.AddToGroupAsync(ConnectionId, $"user_{userId}");
    }
}
```

TECHSPEC §16 C8 위험 항목.

## 13. AES 고정 IV / JWT 키 재사용 (AgentHub)

```csharp
// BAD — TECHSPEC §16 C1, C2
aes.IV = new byte[16];
aes.Key = SHA256(jwtSecretKey);

// GOOD — per-record random IV + 별도 암호화 키
aes.GenerateIV();
aes.Key = Convert.FromBase64String(_config["EncryptionKey"]);
```

PostgreSQL 마이그레이션 시 같이 정리할 항목.
