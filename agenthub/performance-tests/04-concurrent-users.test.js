/**
 * 시나리오 04 — 동시 사용자 부하 테스트 (GS인증 핵심)
 * 목표: 10명 동시 접속 시 p(95) < 2000ms, 오류율 < 1%
 *
 * 시나리오 구성:
 *   - 10명의 가상 사용자가 동시에 일반적인 사용 패턴 반복
 *   - 로그인 → Agent 목록 → 채팅 목록 → 내 정보 조회
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';
import { BASE_URL, TEST_USER, TEST_ADMIN } from './config.js';

// 커스텀 메트릭
const loginDuration   = new Trend('login_duration',   true);
const agentsDuration  = new Trend('agents_duration',  true);
const chatsDuration   = new Trend('chats_duration',   true);
const errorRate       = new Rate('error_rate');
const totalRequests   = new Counter('total_requests');

export const options = {
  thresholds: {
    // GS인증 합격 기준
    'http_req_duration':     ['p(95)<2000', 'p(99)<5000'],
    'http_req_failed':       ['rate<0.01'],
    'login_duration':        ['p(95)<2000'],
    'agents_duration':       ['p(95)<2000'],
    'chats_duration':        ['p(95)<1000'],
    'error_rate':            ['rate<0.01'],
  },
  scenarios: {
    // GS인증 최소 기준: 10명 동시 접속
    concurrent_10: {
      executor: 'constant-vus',
      vus: 10,
      duration: '2m',
    },
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: TEST_USER.email, password: TEST_USER.password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (res.status !== 200) {
    throw new Error(`setup 로그인 실패: ${res.status} ${res.body}`);
  }
  return { token: JSON.parse(res.body).accessToken };
}

export default function (data) {
  const baseHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };
  let hasError = false;

  group('1. 로그인', () => {
    const res = http.post(
      `${BASE_URL}/api/auth/login`,
      JSON.stringify({ email: TEST_USER.email, password: TEST_USER.password }),
      { headers: { 'Content-Type': 'application/json' } }
    );
    totalRequests.add(1);
    loginDuration.add(res.timings.duration);

    const ok = check(res, {
      '[로그인] 200 OK': (r) => r.status === 200,
      '[로그인] < 2s': (r) => r.timings.duration < 2000,
    });
    if (!ok) hasError = true;
  });

  sleep(0.5);

  group('2. Agent 목록 조회', () => {
    const res = http.get(`${BASE_URL}/api/agents`, { headers: baseHeaders });
    totalRequests.add(1);
    agentsDuration.add(res.timings.duration);

    const ok = check(res, {
      '[Agent목록] 200 OK': (r) => r.status === 200,
      '[Agent목록] < 2s': (r) => r.timings.duration < 2000,
      '[Agent목록] 배열 반환': (r) => {
        try { return Array.isArray(JSON.parse(r.body)); }
        catch { return false; }
      },
    });
    if (!ok) hasError = true;
  });

  sleep(0.5);

  group('3. 채팅 목록 조회', () => {
    const res = http.get(`${BASE_URL}/api/chat/conversations`, { headers: baseHeaders });
    totalRequests.add(1);
    chatsDuration.add(res.timings.duration);

    const ok = check(res, {
      '[채팅목록] 200 OK': (r) => r.status === 200,
      '[채팅목록] < 1s': (r) => r.timings.duration < 1000,
    });
    if (!ok) hasError = true;
  });

  sleep(0.5);

  group('4. 내 정보 조회', () => {
    const res = http.get(`${BASE_URL}/api/auth/me`, { headers: baseHeaders });
    totalRequests.add(1);

    const ok = check(res, {
      '[내정보] 200 OK': (r) => r.status === 200,
      '[내정보] < 1s': (r) => r.timings.duration < 1000,
    });
    if (!ok) hasError = true;
  });

  errorRate.add(hasError ? 1 : 0);
  sleep(1);
}

export function handleSummary(data) {
  const p95 = data.metrics.http_req_duration?.values?.['p(95)'];
  const errRate = data.metrics.http_req_failed?.values?.rate;
  const pass = p95 < 2000 && errRate < 0.01;

  return {
    'performance-tests/results/concurrent-users-summary.txt': `
======================================================
  GS인증 성능 테스트 — 동시 사용자 부하 결과
  실행 일시: ${new Date().toLocaleString('ko-KR')}
======================================================

[합격 기준]
  - 응답 시간 p(95) < 2000ms
  - 오류율 < 1%

[측정 결과]
  - 동시 사용자 수: 10명
  - 총 요청 수: ${data.metrics.total_requests?.values?.count ?? '-'}
  - 응답 시간 p(50): ${data.metrics.http_req_duration?.values?.['p(50)']?.toFixed(1) ?? '-'} ms
  - 응답 시간 p(95): ${p95?.toFixed(1) ?? '-'} ms
  - 응답 시간 p(99): ${data.metrics.http_req_duration?.values?.['p(99)']?.toFixed(1) ?? '-'} ms
  - 최대 응답 시간: ${data.metrics.http_req_duration?.values?.max?.toFixed(1) ?? '-'} ms
  - 오류율: ${((errRate ?? 0) * 100).toFixed(2)} %
  - 처리량 (RPS): ${data.metrics.http_reqs?.values?.rate?.toFixed(1) ?? '-'} req/s

[API별 응답 시간 p(95)]
  - 로그인:      ${data.metrics.login_duration?.values?.['p(95)']?.toFixed(1) ?? '-'} ms
  - Agent 목록:  ${data.metrics.agents_duration?.values?.['p(95)']?.toFixed(1) ?? '-'} ms
  - 채팅 목록:   ${data.metrics.chats_duration?.values?.['p(95)']?.toFixed(1) ?? '-'} ms

[판정]
  ${pass ? '✅ PASS — GS인증 성능 기준 충족' : '❌ FAIL — 기준 미달, 최적화 필요'}
======================================================
`,
  };
}
