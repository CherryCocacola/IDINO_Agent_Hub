/**
 * 시나리오 02 — Agent 목록/조회 성능 테스트
 * 대상: GET /api/agents, GET /api/agents/{id}
 * 목표: p(95) < 2000ms, 오류율 < 1%
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL, TEST_USER, THRESHOLDS } from './config.js';

export const options = {
  thresholds: THRESHOLDS,
  scenarios: {
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m',  target: 10 },
        { duration: '30s', target: 0  },
      ],
      gracefulRampDown: '10s',
    },
  },
};

// 테스트 시작 시 1회 로그인하여 토큰 공유
export function setup() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: TEST_USER.email, password: TEST_USER.password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (res.status !== 200) {
    throw new Error(`setup 로그인 실패: ${res.status} ${res.body}`);
  }

  const body = JSON.parse(res.body);
  return { token: body.accessToken };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };

  // 1. Agent 목록 조회
  const listRes = http.get(`${BASE_URL}/api/agents`, { headers });

  check(listRes, {
    '[Agent목록] 상태코드 200': (r) => r.status === 200,
    '[Agent목록] 응답시간 < 2s': (r) => r.timings.duration < 2000,
    '[Agent목록] 배열 반환': (r) => {
      try { return Array.isArray(JSON.parse(r.body)); }
      catch { return false; }
    },
  });

  // 2. 개별 Agent 조회 (목록에서 첫 번째 항목)
  try {
    const agents = JSON.parse(listRes.body);
    if (agents.length > 0) {
      const agentId = agents[0].agentId;
      const detailRes = http.get(`${BASE_URL}/api/agents/${agentId}`, { headers });

      check(detailRes, {
        '[Agent상세] 상태코드 200': (r) => r.status === 200,
        '[Agent상세] 응답시간 < 1s': (r) => r.timings.duration < 1000,
      });
    }
  } catch (_) {}

  sleep(1);
}
