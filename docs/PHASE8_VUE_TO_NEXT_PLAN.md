# Phase 8 — AgentHub Vue → Next.js 점진 이행 계획

> **트랙 #149 P4 (2026-06-01)** — CLAUDE.md 의 Phase 8 "보류" 상태를 정식 계획 문서로 승격.
> 본 문서는 **실행 결정 문서가 아니라 의사결정 토대**다. 실제 진입 시 사용자 승인 필요.

---

## 0. 요약

AgentHub 의 Vue 3 + Vite 5 SPA (37+ root views + 19 admin views) 를 Next.js
16 으로 점진 이행한다. 일시 정지/롤백 가능한 **strangler-fig 패턴** 으로 진행
하되, **운영 가동률 100% 유지 + 회귀 결함 0** 이 절대 조건.

- 예상 영업일: **15~20일** (가장 보수적 ─ DocUtil 프런트엔드와의 디자인 토큰 정합 포함)
- 위험 레벨: **중상** (라우팅/i18n/SignalR/Vue Flow/Bootstrap 5 → Next.js 의존성 전환)
- 사용자 가시 변화: 점진 진행 시 동시 가동, 페이지별 표면 동일

## 1. 현황 진단

### 1.1 AgentHub 프런트엔드 카탈로그

| 항목 | 수량 |
|---|---|
| `views/*.vue` (root) | 37 |
| `views/admin/*.vue` | 19 |
| `views/agent/*.vue` | (Agent 빌더/마켓플레이스/채팅) |
| `components/` | 다수 (재사용 UI) |
| `stores/` (Pinia) | 다수 |
| `services/*.ts` (axios) | 다수 |
| `composables/` | 다수 |
| `i18n/locales/` | ko/en/vi 3 locale |
| 라우트 정의 | `router/index.ts` 단일 파일 |

### 1.2 핵심 의존성

| 라이브러리 | 용도 | Next.js 대응 |
|---|---|---|
| `vue@3` + `vite@5` | SPA 런타임/빌드 | `next@16` + React 19 — 전면 교체 |
| `vue-router` | 클라이언트 라우팅 | Next.js App Router (file-based) |
| `pinia` | 상태 관리 | Zustand 또는 React Query (선호: Zustand + RQ 조합) |
| `vue-i18n` | 다국어 | `next-intl` 또는 `react-i18next` |
| `@microsoft/signalr` | 실시간 (chat/notification) | **동일 라이브러리 유지** (브라우저 SDK 변동 없음) |
| `Vue Flow` | 워크플로우 비주얼 에디터 | React Flow (`@xyflow/react`) — API 유사 |
| `Bootstrap 5.3` + `data-bs-theme` | UI 프레임워크 + 다크모드 | **유지 또는 대체** — Bootstrap React-bootstrap or shadcn/ui 결정 필요 |
| `Chart.js` + `vue-chartjs` | 분석 대시보드 | `react-chartjs-2` |
| `marked` + `DOMPurify` + `prismjs` | 마크다운/코드 렌더링 | **동일 (vanilla)** |

### 1.3 백엔드 정합 (변경 없음)

- ASP.NET Core 8.0 — `Program.cs` 의 SPA 서빙 설정만 조정
- `wwwroot/` 빌드 산출물 경로는 동일 패턴 유지 가능
- API 표면(`/api/*`, `/v1/*`, `/hubs/*`)은 영향 없음

## 2. 전환 전략 — Strangler-Fig (점진)

### 2.1 옵션 비교

| 옵션 | 설명 | 장점 | 단점 | 선호 |
|---|---|---|---|---|
| **A. 전면 재작성 + cut-over** | 별도 폴더에 Next.js 풀버전 작성 → 한 번에 교체 | 깔끔, 의존성 충돌 없음 | 위험 크고 회귀 검증 광범위 | × |
| **B. Strangler-Fig 점진** | Next.js 를 reverse-proxy 로 두고 페이지별 교체 | 위험 분산, 롤백 즉시 가능 | 듀얼 가동 운영 부담 | ✓ |
| **C. Astro 같은 hybrid** | 정적 페이지부터 점진 | 일부 페이지만 빠른 빌드 | AgentHub 의 동적 UI 비율 높아 부적합 | × |

**선택: B (Strangler-Fig)**.

### 2.2 Strangler 패턴 적용

```
[ASP.NET Core 8] (변동 없음)
     ↓
 /api/*      → 백엔드 API (그대로)
 /hubs/*     → SignalR (그대로)
 /v1/*       → OpenAI 호환 (그대로)
 /(spa)/*    → SPA 라우팅
   ├─ Phase 8.A: 운영 SPA = Vue 빌드 산출물 (현행)
   ├─ Phase 8.B: 일부 라우트만 Next.js 산출물 (혼합)
   └─ Phase 8.C: 전체 라우트가 Next.js (전환 완료)
```

라우팅 분기는 ASP.NET Core 의 `MapFallbackToFile` 위에 **path-prefix 분기**
미들웨어를 신설:

```
if (path starts with "/(next-pages)") → wwwroot/next/index.html
else                                    → wwwroot/index.html (기존 Vue)
```

페이지 교체 시 분기 패턴에 path 만 추가 → 즉시 적용 / 회귀 시 path 제거 →
이전 Vue 라우트 즉시 복귀.

## 3. 단계별 진행 (Phase 8.A ~ 8.E)

### Phase 8.A — 준비 + 기반 인프라 (3일)

1. `agenthub/NextApp/` 디렉토리 신설 (`ClientApp/` 와 병존)
2. `next@16` + React 19 + TypeScript 셋업
3. 디자인 토큰 통합: Bootstrap 5.3 데이터 일관성 — DocUtil 프런트엔드(Next.js
   16)의 토큰 정의 재사용
4. axios → fetch 또는 axios 유지 결정 (선호: axios — 인터셉터 자산 활용)
5. JWT/sessionStorage SSO 패턴 (현행 Vue 와 동일 키 사용)
6. 라우트 분기 미들웨어 ASP.NET 추가 (`/next/*` prefix)

### Phase 8.B — 정적/단순 페이지 우선 이행 (5일)

저복잡도 페이지부터 이행 — 풀스택 검증의 risk 최소화:

| 우선순위 | 페이지 | 이유 |
|---|---|---|
| 1 | `/login`, `/forgot-password`, `/reset-password` | 폼만 — Pinia/axios 의존 적음 |
| 2 | `/privacy-policy`, `/help`, `/landing-page` | 정적 컨텐츠 |
| 3 | `/dashboard` (read-only) | API 호출 패턴 검증 |
| 4 | `/settings` | i18n + 테마 전환 검증 (트랙 #149 P1 영향 영역) |

각 페이지 이행 → Playwright 회귀 → admin_console_smoke + i18n_locale_matrix
+ user_scenario_e2e 3 매트릭스 모두 PASS 확인 후 다음 페이지.

### Phase 8.C — Admin 콘솔 (5일)

19개 `admin/*.vue` 를 일괄 이행. 트랙 #149 P1 의 다크모드/i18n/smoke
자산을 회귀 게이트로 활용.

- `/admin/docutil-*` 13개 — DocUtil 흡수 Vue 화면
- `/admin/faqs`, `/admin/tutorials` — 트랙 #136 신설
- 나머지 4개

### Phase 8.D — Agent 빌더/마켓플레이스/채팅 (4일)

가장 복잡한 영역. Vue Flow → React Flow 전환 + SignalR 클라이언트 재배선.

- `/agents/builder` — Vue Flow 워크플로우 에디터
- `/agents/marketplace` — Agent 카탈로그
- `/agents/select` — 공유 모달 + QR
- `/agents/chat` — 실시간 채팅 (SignalR + SSE)

### Phase 8.E — Vue 잔존 제거 + cleanup (3일)

- `ClientApp/` 디렉토리 archive (즉시 삭제 금지 — 4주 보존)
- Bootstrap 5.3 의존 정리 (필요 시 React-bootstrap 으로 일원화)
- ASP.NET 라우트 분기 미들웨어 제거 (단일 Next.js 산출물 서빙)
- `Program.cs` SPA 설정 단순화

## 4. 위험 분석 / 완화

| 위험 | 영향 | 완화 방안 |
|---|---|---|
| **Vue Flow → React Flow API 차이** | 워크플로우 에디터 UX 변동 | Phase 8.D 진입 전 React Flow PoC 1주 — 데모용 워크플로우 작성 후 사용자 데모 |
| **Bootstrap 5 → React 컴포넌트 라이브러리 전환 시 디자인 drift** | UI 일관성 손상 | 디자인 토큰 (CSS 변수 + data-bs-theme) **그대로 유지** — Bootstrap CSS 만 활용, React-bootstrap 미도입 옵션 검토 |
| **vue-i18n → next-intl 메시지 키 호환성** | 누락 메시지 → 영문 폴백 | locale JSON 파일 키 동일 유지 + next-intl 의 fallbackLocale=ko 설정 |
| **Pinia store 패턴 → React 상태 패턴 차이** | 컴포넌트 트리 재구조화 | Zustand 도입 (Pinia 와 가장 유사한 API) |
| **SignalR 재연결/이벤트 누수** | 채팅 누락 | useEffect cleanup 강제 + Phase 8.D 의 e2e 검증에 SSE/SignalR 누수 케이스 추가 |
| **세션 격리 (sessionStorage)** | 다중 탭 회귀 | 트랙 #149 의 SSO Option A 패턴 유지 — Next.js 클라이언트도 동일 키 |
| **CI 빌드 시간 증가** | 배포 지연 | Next.js 빌드는 docker build cache 활용 + IIS 배포 변경 없음 |
| **점진 진행 중 Vue/Next.js 동시 가동 → 의존성 충돌** | 빌드 충돌 | `ClientApp/` 와 `NextApp/` 별도 디렉토리 + 별도 `package.json` 격리 |
| **운영 중 SPA 라우트 prefix 충돌** | 페이지 404 | 라우트 분기 미들웨어 단위 테스트 + 운영 진입 전 5분 dry-run |
| **테스트 더블 (axios mock 등) 재작성** | 회귀 테스트 시간 증가 | tools/integration/ 자산은 backend API 호출 기반이므로 영향 없음 |

## 5. 진행 조건 / 진입 결정 (Open Questions)

진입 결정 전 사용자 컨펌 필요:

1. **Q1. UI 프레임워크**: Bootstrap 5 CSS 그대로 유지 vs React-bootstrap 도입 vs shadcn/ui 전환 — 어느 쪽인가?
2. **Q2. 상태 관리**: Zustand vs Redux Toolkit vs React Query 단독 — Pinia 와 유사도 우선인가, 미래 React 생태계 정합 우선인가?
3. **Q3. i18n**: next-intl vs react-i18next — Next.js App Router 와의 통합 패턴 차이.
4. **Q4. PoC 1주 선행 권장**: Phase 8.A 진입 전 Vue Flow → React Flow 의 워크플로우 에디터 PoC + 사용자 데모. 결정 후 정식 시작.
5. **Q5. 듀얼 가동 기간**: Phase 8.B 시작 ~ Phase 8.E 종료 까지 약 12 영업일 듀얼 가동. 이 기간 동안 발견되는 결함은 Vue/Next 양쪽 모두 fix 해야 함 (이중 부담). 수용 가능한가?
6. **Q6. 진입 시점**: 다른 통합 작업 (트랙 A1 DocUtil 운영자 흡수 잔존 작업 등) 완료 후 진입할지, 또는 병렬 진행할지.

## 6. 검증 게이트 (각 Phase 종료 시)

다음 4개 매트릭스를 모두 PASS 해야 다음 Phase 진입:

1. **관리자 콘솔 smoke** — `tools/integration/admin_console_smoke.py` (18 페이지)
2. **사용자 시나리오 e2e** — `tools/integration/user_scenario_e2e.py` (9 단계)
3. **i18n 3 locale 매트릭스** — `tools/integration/i18n_locale_matrix.py` (3 × 5 = 15 셀)
4. **다크모드 회귀** — Phase 8.A 진입 시 신설 (light/dark 토글 + 페이지 이동 유지)

각 매트릭스는 Vue/Next.js 양쪽 산출물에 대해 동시 실행. 양쪽 모두 PASS
시에만 다음 페이지 이행.

## 7. 산출물 (Phase 8 완료 시)

- `agenthub/NextApp/` — Next.js 16 + React 19 + TypeScript 풀스택
- `agenthub/wwwroot/` — Next.js export 산출물
- `agenthub/ClientApp/` — archive 또는 삭제 (운영 보존 4주)
- `docs/PHASE8_VUE_TO_NEXT_PLAN.md` — 본 문서 (실 진행 시 진행 로그 추가)
- `docs/PHASE8_MIGRATION_LOG.md` — 페이지별 이행 일자/결함/회귀 결과

## 8. 비-Phase8 잔존 작업 (참고)

본 Phase 진입 전후로 처리할 비-목표 작업:

- 트랙 A1 — DocUtil 운영자 콘솔 흡수 (Plan witty-spinning-snail.md, Phase
  C/D/E/F 잔존). 우선 완료 권장.
- 운영 OpenAI 키 갱신 (트랙 #149 P2 검증에서 확인된 401)
- Nexus:SharedSecret 운영 설정 (Phase 5 완료, 운영 키 적용 대기)
- DocUtil docker-compose 운영 build 전환 (트랙 #144 완료, image 운영 적용 대기)

---

**다음 진행**: 본 문서 사용자 검토 → Q1~Q6 답변 → PoC 1주 (선택) → Phase 8.A 진입.
