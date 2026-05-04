# 외부 시스템 연동을 위한 Agent API 개발 로드맵

> **최종 업데이트:** 2026-02-26
> **담당:** AI Agent Management 플랫폼
> **목적:** 외부 시스템에서 이 플랫폼의 Agent를 API 키로 직접 호출할 수 있도록 인프라 완성

---

## 현재 구현된 Agent API 엔드포인트

| Method | Endpoint | 설명 | 인증 | 상태 |
|--------|----------|------|------|------|
| `POST` | `/api/agents/{id}/chat` | 단일 메시지 전송 및 응답 | `X-API-Key` | ✅ 구현완료 |
| `POST` | `/api/agents/code/{code}/chat` | Agent 코드로 채팅 | `X-API-Key` | ✅ 구현완료 |
| `POST` | `/api/agents/{id}/chat/stream` | SSE 스트리밍 응답 | `X-API-Key` | ✅ 구현완료 (2026-02-26) |
| `GET`  | `/api/agents/{id}/info` | Agent 기본 정보 조회 | `X-API-Key` | ✅ 구현완료 (2026-02-26) |
| `GET`  | `/api/agents/{id}/usage` | API 키 사용량 통계 | `X-API-Key` | ✅ 구현완료 (2026-02-26) |

---

## 기본 사용법

### 인증 헤더

```http
X-API-Key: ak-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

또는

```http
Authorization: Bearer ak-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 기본 채팅 요청

```bash
curl -X POST https://your-domain.com/api/agents/1/chat \
  -H "X-API-Key: ak-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

### 응답 형식

```json
{
  "messageId": 123,
  "conversationId": 456,
  "content": "안녕하세요! 무엇을 도와드릴까요?",
  "model": "gpt-4o",
  "tokensUsed": 150,
  "cost": 0.003,
  "responseTime": 1234
}
```

---

## 구현 진행 상황

### ✅ 완료된 항목 (2026-02-26)

#### 1. IP 화이트리스트 (IP Whitelist) — 높음 우선순위

**구현 내용:**
- `ApiKey` 모델에 `AllowedIps` 컬럼 추가 (쉼표 구분 IP 목록)
- `ApiKeyAuthService`에서 인증 시 요청 IP와 화이트리스트 비교
- IP가 등록된 경우 일치하지 않으면 `403 Forbidden` 반환
- `ApiKeysController` 및 UI에서 IP 목록 설정 지원

**사용 예시:**
```
AllowedIps: "192.168.1.100,10.0.0.0/24,203.0.113.50"
```

**동작 방식:**
1. API 키 발급 시 허용 IP 목록 입력 (선택사항)
2. 목록이 비어있으면 모든 IP 허용
3. 목록이 있으면 목록에 있는 IP만 허용
4. 차단된 IP는 `403 Forbidden` + 로그 기록

---

#### 2. 권한 범위(Scope) 설정 — 높음 우선순위

**구현 내용:**
- `ApiKey` 모델에 `Scopes` 컬럼 추가 (쉼표 구분 스코프 목록)
- `ApiKeyAuthorizeAttribute`에 `RequiredScope` 파라미터 추가
- 각 엔드포인트별 스코프 검증

**지원 스코프:**

| 스코프 | 설명 | 엔드포인트 |
|--------|------|-----------|
| `chat` | 기본 채팅 | `POST /chat` |
| `stream` | 스트리밍 채팅 | `POST /chat/stream` |
| `info` | Agent 정보 조회 | `GET /info` |
| `usage` | 사용량 통계 조회 | `GET /usage` |

**스코프가 비어있거나 `*`이면 모든 권한 허용**

**사용 예시:**
```
Scopes: "chat,stream"
→ 채팅과 스트리밍만 허용, /info와 /usage는 403
```

---

#### 3. Rate Limiting — 높음 우선순위

**구현 내용:**
- `ApiKey` 모델에 `RateLimitPerMinute`, `RateLimitPerDay` 컬럼 추가
- `IApiKeyRateLimiter` 서비스 구현 (IMemoryCache 기반 슬라이딩 윈도우)
- 초과 시 `429 Too Many Requests` + `Retry-After` 헤더 반환
- DI 컨테이너에 `Singleton` 등록 (상태 유지)

**동작 방식:**
- 분당 초과 시: `429 Too Many Requests`, `Retry-After: 60`
- 일당 초과 시: `429 Too Many Requests`, `Retry-After: 86400`
- 제한 없음(null): 무제한 허용

**참고:** 분산 환경에서는 Redis 기반 구현으로 교체 필요

---

#### 4. SSE 스트리밍 지원 — 중간 우선순위

**구현 내용:**
- `POST /api/agents/{id}/chat/stream` 엔드포인트 추가
- `Content-Type: text/event-stream` 응답
- `[ApiKeyAuthorize(RequiredScope = "stream")]` 적용
- 토큰 단위 청크 전송, 연결 끊김 감지

**SSE 이벤트 형식:**
```
data: {"type":"chunk","content":"안녕"}

data: {"type":"chunk","content":"하세요"}

data: {"type":"done","totalTokens":150,"cost":0.003}

```

**클라이언트 사용 예시:**
```javascript
const eventSource = new EventSource(`/api/agents/1/chat/stream?message=안녕하세요`, {
  headers: { 'X-API-Key': 'ak-YOUR_KEY' }
});

eventSource.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === 'chunk') console.log(data.content);
  if (data.type === 'done') eventSource.close();
};
```

> **참고:** EventSource는 GET만 지원하므로 외부 시스템은 `fetch` + `ReadableStream` 사용 권장

---

#### 5. Agent 정보 조회 엔드포인트 — 중간 우선순위

**구현 내용:**
- `GET /api/agents/{id}/info` 엔드포인트 추가
- `[ApiKeyAuthorize(RequiredScope = "info")]` 적용
- 공개된 Agent 메타데이터 반환 (시스템 프롬프트 제외)

**응답 예시:**
```json
{
  "agentId": 1,
  "agentName": "고객지원 AI",
  "agentCode": "customer-support",
  "description": "고객 문의를 처리하는 AI 에이전트",
  "isPublic": true,
  "defaultModel": "gpt-4o",
  "enableRag": true,
  "capabilities": ["chat", "rag", "web_search"]
}
```

---

#### 6. API 사용량 통계 엔드포인트 — 중간 우선순위

**구현 내용:**
- `GET /api/agents/{id}/usage` 엔드포인트 추가
- 해당 API 키의 사용량 통계 반환
- `[ApiKeyAuthorize(RequiredScope = "usage")]` 적용

**응답 예시:**
```json
{
  "agentId": 1,
  "apiKeyId": 42,
  "totalRequests": 1523,
  "lastUsedAt": "2026-02-26T10:30:00Z",
  "todayRequests": 87,
  "rateLimitPerMinute": 30,
  "rateLimitPerDay": 1000,
  "remainingToday": 913,
  "expiresAt": null,
  "scopes": ["chat", "stream"]
}
```

---

### 📋 미구현 항목 (향후 개발 필요)

#### 7. 웹훅(Webhook) 이벤트 — 낮음 우선순위

**필요한 개발:**
- `ApiKeyWebhook` 테이블 추가 (URL, Secret, 이벤트 유형)
- 이벤트 발생 시 외부 URL로 HTTP POST 전송
- HMAC-SHA256 서명으로 위변조 방지
- 전송 실패 시 Hangfire 재시도 큐

**지원 이벤트:**
```
key.expiring     → 만료 7일 전
quota.exceeded   → Rate Limit 초과 시
key.blocked      → IP 차단 발생 시
usage.daily      → 일일 사용량 보고
```

**예시 웹훅 페이로드:**
```json
{
  "event": "key.expiring",
  "timestamp": "2026-02-26T10:00:00Z",
  "apiKeyId": 42,
  "agentId": 1,
  "data": { "expiresAt": "2026-03-05T00:00:00Z" },
  "signature": "sha256=abc123..."
}
```

---

#### 8. SDK 및 코드 예시 — 낮음 우선순위

**필요한 개발:**
- Python 클라이언트 라이브러리 (`pip install aiagent-sdk`)
- Node.js 클라이언트 라이브러리 (`npm install @aiagent/sdk`)
- Swagger/OpenAPI 명세 고도화 (현재 Swashbuckle 기본 구성)
- Postman Collection 자동 갱신 파이프라인

**Python 예시 (목표):**
```python
from aiagent import AgentClient

client = AgentClient(api_key="ak-YOUR_KEY")
response = client.agents(1).chat("안녕하세요")
print(response.content)

# 스트리밍
for chunk in client.agents(1).chat_stream("안녕하세요"):
    print(chunk.content, end="", flush=True)
```

---

#### 9. API 키 교체(Rotation) — 낮음 우선순위

**필요한 개발:**
- 신규 키 발급 후 구 키 유예기간 설정 (예: 24시간)
- 유예기간 중 두 키 모두 유효
- 유예기간 이후 구 키 자동 비활성화
- 교체 완료 웹훅/이메일 알림

**API 설계:**
```http
POST /api/agents/{agentId}/api-keys/{keyId}/rotate
{
  "gracePeriodHours": 24
}
→ 새 키 반환 + 구 키 유예기간 설정
```

---

## 보안 체크리스트

| 항목 | 상태 | 비고 |
|------|------|------|
| API 키 AES-256 암호화 저장 | ✅ | JWT SecretKey 기반 |
| HTTPS 강제 적용 | ✅ | `RequireHttpsForDomainMiddleware` |
| 만료일 검증 | ✅ | 인증 시 자동 검사 |
| 활성 상태 검증 | ✅ | `IsActive` 플래그 |
| IP 화이트리스트 | ✅ | 2026-02-26 구현 |
| 스코프 기반 권한 제어 | ✅ | 2026-02-26 구현 |
| Rate Limiting | ✅ | 2026-02-26 구현 (MemoryCache) |
| HMAC 서명 검증 | ❌ | 웹훅 구현 시 필요 |
| Redis 분산 Rate Limit | ❌ | 다중 서버 환경에서 필요 |
| CIDR 표기법 IP 검증 | ❌ | 현재 단순 IP 매칭만 지원 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-02-26 | IP 화이트리스트 구현 (ApiKey.AllowedIps) |
| 2026-02-26 | 스코프 기반 권한 제어 구현 (ApiKey.Scopes) |
| 2026-02-26 | Rate Limiting 구현 (MemoryCache 슬라이딩 윈도우) |
| 2026-02-26 | SSE 스트리밍 엔드포인트 추가 (POST /chat/stream) |
| 2026-02-26 | Agent 정보 조회 엔드포인트 추가 (GET /info) |
| 2026-02-26 | API 사용량 통계 엔드포인트 추가 (GET /usage) |
| 2026-02-26 | Postman Collection 작성 (DOCS/AIAgentManagement_AgentAPI.postman_collection.json) |
