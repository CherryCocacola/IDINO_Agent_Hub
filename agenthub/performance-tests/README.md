# AIAgentManagement — 성능 테스트 가이드

> GS인증 성능효율성 (ISO/IEC 25023) 요구사항 대응
> 도구: [k6](https://k6.io/) (오픈소스 부하 테스트)

---

## 📋 테스트 시나리오 구성

| 파일 | 시나리오 | 동시 사용자 | 목표 |
|---|---|---|---|
| `01-auth.test.js` | 로그인/내정보 | 10명 | p(95) < 2000ms |
| `02-agents.test.js` | Agent 목록/상세 | 10명 | p(95) < 2000ms |
| `03-chat.test.js` | 채팅 목록/생성 | 10명 | p(95) < 2000ms |
| `04-concurrent-users.test.js` | **종합 부하 (GS핵심)** | 10명 동시 | p(95) < 2000ms, 오류율 < 1% |
| `05-file-upload.test.js` | 파일 업로드 | 3명 | p(95) < 5000ms |

---

## ✅ GS인증 합격 기준

| 지표 | 기준 | 비고 |
|---|---|---|
| 응답 시간 p(95) | **< 2,000ms** | 일반 API (AI 응답 제외) |
| 응답 시간 p(95) | < 5,000ms | 파일 업로드 |
| 오류율 | **< 1%** | HTTP 4xx/5xx 비율 |
| 동시 사용자 | **10명 이상** | GS인증 최소 기준 |
| 처리량 | > 5 RPS | 초당 요청 처리 수 |

> AI API 호출(채팅 전송)은 외부 서비스 의존이므로 성능 평가 제외 가능 — 심사관과 사전 협의 필요

---

## 🚀 설치 및 실행

### 1. k6 설치

```powershell
# Windows — winget
winget install k6 --source winget

# 또는 Chocolatey
choco install k6

# 설치 확인
k6 version
```

### 2. 시험환경 준비

```powershell
# 테스트 계정 미리 생성 (DB에 직접 또는 회원가입으로)
# - admin@test.com / Test1234! (Admin 역할)
# - user@test.com  / Test1234! (일반 사용자)
```

### 3. 단일 시나리오 실행

```powershell
# 기본 실행 (localhost)
k6 run performance-tests/01-auth.test.js

# 시험 서버 지정
k6 run -e BASE_URL=https://agenthub.idino.co.kr performance-tests/01-auth.test.js

# 계정 커스텀
k6 run `
  -e BASE_URL=https://agenthub.idino.co.kr `
  -e USER_EMAIL=user@test.com `
  -e USER_PASSWORD=Test1234! `
  performance-tests/01-auth.test.js
```

### 4. GS인증 핵심 — 동시 사용자 종합 테스트

```powershell
# 결과 파일 저장 폴더 생성
New-Item -ItemType Directory -Force -Path performance-tests/results

# 종합 부하 테스트 실행 (결과 자동 저장)
k6 run `
  -e BASE_URL=https://agenthub.idino.co.kr `
  --out json=performance-tests/results/concurrent-users-raw.json `
  performance-tests/04-concurrent-users.test.js
```

### 5. 전체 시나리오 순차 실행

```powershell
$BASE = "https://agenthub.idino.co.kr"
$RESULTS = "performance-tests/results"
New-Item -ItemType Directory -Force -Path $RESULTS

foreach ($test in @("01-auth","02-agents","03-chat","04-concurrent-users","05-file-upload")) {
    Write-Host "Running $test ..." -ForegroundColor Cyan
    k6 run `
      -e BASE_URL=$BASE `
      --out json="$RESULTS/$test-raw.json" `
      "performance-tests/$test.test.js"
}
Write-Host "완료! 결과 파일: $RESULTS" -ForegroundColor Green
```

---

## 📊 결과 해석

### 실행 후 화면 예시

```
✓ [로그인] 상태코드 200
✓ [로그인] 응답시간 < 2s
✓ [Agent목록] 200 OK

http_req_duration............: avg=234ms  min=89ms   med=201ms  max=1.2s   p(90)=450ms p(95)=680ms
http_req_failed..............: 0.00%  ✓ 0   ✗ 0
```

### 판정 기준

| 결과 | 의미 |
|---|---|
| `✓ threshold` | 합격 기준 충족 |
| `✗ threshold` | 기준 미달 — 최적화 필요 |

### 기준 미달 시 조치

| 증상 | 원인 | 조치 |
|---|---|---|
| 로그인 > 2s | JWT 서명 오버헤드 | SecretKey 길이 최소화, 알고리즘 확인 |
| Agent목록 > 2s | 풀 스캔 쿼리 | DB 인덱스 확인 (IX_Agents_UserId) |
| 채팅목록 > 1s | N+1 쿼리 | Include() / AsNoTracking() 확인 |
| 오류율 > 1% | Rate Limiting | Limit 값 상향 또는 IP 예외 처리 |

---

## 📁 결과 파일 저장 위치

```
performance-tests/
├── results/
│   ├── concurrent-users-summary.txt   ← GS인증 제출용 요약 리포트
│   ├── concurrent-users-raw.json      ← 원시 데이터
│   └── ...
```

`concurrent-users-summary.txt` 파일이 GS인증 제출용 **성능 테스트 결과 리포트**입니다.

---

## ⚠️ 주의사항

1. **실제 AI API 호출 포함 테스트 금지** — API 비용 과다 발생
2. **프로덕션 서버 직접 테스트 주의** — 시험환경 서버 별도 구성 권장
3. **테스트 계정 실제 데이터와 혼용 금지** — 테스트 후 데이터 정리 필요
4. **Rate Limiting 임시 완화** — 테스트 시 IP 화이트리스트 또는 Limit 상향 필요
