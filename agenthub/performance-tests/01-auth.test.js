/**
 * 시나리오 01 — 인증 API 성능 테스트
 * 대상: POST /api/auth/login, GET /api/auth/me
 * 목표: p(95) < 2000ms, 오류율 < 1%
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL, TEST_USER, THRESHOLDS } from './config.js';

export const options = {
  thresholds: THRESHOLDS,
  scenarios: {
    // 시나리오 A: 점진적 부하 증가 (Ramp-up)
    ramp_up: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '30s', target: 10 },  // 0→10명 증가
        { duration: '1m',  target: 10 },  // 10명 유지
        { duration: '30s', target: 0  },  // 감소
      ],
      gracefulRampDown: '10s',
    },
  },
};

export default function () {
  const headers = { 'Content-Type': 'application/json' };

  // 1. 로그인
  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: TEST_USER.email, password: TEST_USER.password }),
    { headers }
  );

  const loginOk = check(loginRes, {
    '[로그인] 상태코드 200': (r) => r.status === 200,
    '[로그인] 응답시간 < 2s': (r) => r.timings.duration < 2000,
    '[로그인] accessToken 존재': (r) => {
      try { return JSON.parse(r.body).accessToken !== undefined; }
      catch { return false; }
    },
  });

  if (!loginOk) {
    console.warn(`로그인 실패: status=${loginRes.status}, body=${loginRes.body}`);
    sleep(1);
    return;
  }

  const token = JSON.parse(loginRes.body).accessToken;
  const authHeaders = { ...headers, Authorization: `Bearer ${token}` };

  // 2. 내 정보 조회
  const meRes = http.get(`${BASE_URL}/api/auth/me`, { headers: authHeaders });

  check(meRes, {
    '[내정보] 상태코드 200': (r) => r.status === 200,
    '[내정보] 응답시간 < 1s': (r) => r.timings.duration < 1000,
    '[내정보] email 존재': (r) => {
      try { return JSON.parse(r.body).email !== undefined; }
      catch { return false; }
    },
  });

  sleep(1);
}
