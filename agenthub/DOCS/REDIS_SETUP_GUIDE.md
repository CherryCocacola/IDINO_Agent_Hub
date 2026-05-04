# Redis 설치 및 설정 가이드

> **대상 환경**: Windows Server + IIS (AIAgentManagement 프로젝트)
> **작성일**: 2026-03-20

---

## 개요

Redis는 **선택 사항**입니다. 설치하지 않아도 앱은 정상 동작하며, 자동으로 In-Memory 캐시로 대체됩니다.
설치 시 아래 기능의 속도가 개선됩니다:

| 기능 | 효과 |
|------|------|
| RAG 검색 (쿼리 임베딩 캐싱) | 같은 질문 반복 시 OpenAI API 호출 생략 (1시간 캐시) |
| RAG 결과 캐싱 | DB + API 호출 전체 생략 (10분 캐시) |
| 할당량(Quota) 캐싱 | 사용량 조회 속도 향상 |

---

## 1. Redis 설치 (Windows)

### 방법 A: Memurai 설치 (권장 — Windows 서비스 자동 등록)

1. 아래 주소에서 Memurai 다운로드
   ```
   https://www.memurai.com/get-memurai
   ```
2. 설치 마법사 실행 (기본 설정으로 설치)
3. 설치 완료 시 Windows 서비스로 자동 등록됨

### 방법 B: Chocolatey로 설치

```powershell
# 관리자 PowerShell에서 실행
choco install redis-64
```

---

## 2. 서비스 설정

```powershell
# 서비스 자동 시작 설정 (서버 재부팅 후에도 유지)
Set-Service -Name "Memurai" -StartupType Automatic

# 서비스 시작
Start-Service -Name "Memurai"

# 상태 확인
Get-Service -Name "Memurai"
```

---

## 3. 동작 확인

```powershell
redis-cli ping
# 응답: PONG  ← 이게 나오면 정상
```

---

## 4. appsettings.json 설정

`appsettings.json`의 `ConnectionStrings`에 Redis 항목을 추가합니다.
*(현재 프로젝트에는 이미 설정되어 있음)*

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "...(기존 DB 연결 문자열)...",
    "Redis": "localhost:6379"
  }
}
```

> **운영 환경 (`appsettings.Production.json`)**: IIS 환경변수로 주입하는 경우
> ```powershell
> # iis-setting.ps1 또는 IIS 환경변수에 추가
> [System.Environment]::SetEnvironmentVariable("ConnectionStrings__Redis", "localhost:6379", "Machine")
> ```

---

## 5. 앱 재시작

```powershell
iisreset
```

재시작 후 로그에서 아래 메시지 확인:
```
Redis cache configured with connection: localhost:6379
```

아래 메시지가 보이면 Redis 연결 실패 → In-Memory 캐시로 자동 대체된 것:
```
Redis configuration failed, falling back to in-memory cache.
```

---

## 6. 동작 원리 (코드 참고)

`Program.cs:128` — Redis 연결 문자열이 있으면 Redis 캐시, 없으면 MemoryCache 자동 선택

```
Redis 연결 문자열 있음 → StackExchange.Redis 사용
Redis 연결 문자열 없음 → AddDistributedMemoryCache 사용 (인메모리)
Redis 연결 실패 시    → 자동으로 인메모리 폴백
```

`RagService.cs` — 캐시 키 구조:

| 캐시 키 | TTL | 내용 |
|---------|-----|------|
| `embedding:{쿼리해시}` | 1시간 | 쿼리 임베딩 벡터 |
| `rag:{agentId}:{userId}:{쿼리해시}` | 10분 | RAG 검색 결과 |
| `quota:user:{userId}:service:{serviceId}` | 30분 | 할당량 정보 |

---

## 7. 문제 해결

### redis-cli ping 이 응답 없음
```powershell
# 서비스 실행 여부 확인
Get-Service -Name "Memurai", "Redis*"

# 포트 사용 여부 확인
netstat -ano | findstr :6379
```

### 방화벽 설정 (외부 Redis 서버 사용 시)
```powershell
New-NetFirewallRule -DisplayName "Redis" -Direction Inbound -Protocol TCP -LocalPort 6379 -Action Allow
```

### 로그 확인 위치
- IIS 로그: `C:\inetpub\logs\LogFiles\`
- 앱 로그: IIS → 사이트 → 로깅 설정 경로

---

## 참고

- Memurai 공식: https://www.memurai.com
- Redis 공식 문서: https://redis.io/docs
