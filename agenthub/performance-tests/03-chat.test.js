/**
 * 시나리오 03 — 채팅 목록/메시지 성능 테스트
 * 대상: GET /api/chat/conversations, POST /api/chat/conversations,
 *       GET /api/chat/conversations/{id}/messages
 * 목표: p(95) < 2000ms, 오류율 < 1%
 * ※ AI 응답(POST send) 은 외부 API 의존 → 별도 타임아웃 기준 적용
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL, TEST_USER, THRESHOLDS } from './config.js';

export const options = {
  thresholds: {
    ...THRESHOLDS,
    // 채팅 목록/메시지 조회는 1초 이내
    'http_req_duration{name:채팅목록}': ['p(95)<1000'],
    'http_req_duration{name:메시지목록}': ['p(95)<1000'],
  },
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

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: TEST_USER.email, password: TEST_USER.password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  if (res.status !== 200) {
    throw new Error(`setup 로그인 실패: ${res.status}`);
  }

  const body = JSON.parse(res.body);
  return { token: body.accessToken };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };

  // 1. 대화 목록 조회
  const listRes = http.get(`${BASE_URL}/api/chat/conversations`, {
    headers,
    tags: { name: '채팅목록' },
  });

  check(listRes, {
    '[채팅목록] 상태코드 200': (r) => r.status === 200,
    '[채팅목록] 응답시간 < 1s': (r) => r.timings.duration < 1000,
  });

  // 2. 새 대화 생성
  const createRes = http.post(
    `${BASE_URL}/api/chat/conversations`,
    JSON.stringify({ title: `성능테스트_${Date.now()}` }),
    { headers }
  );

  check(createRes, {
    '[대화생성] 상태코드 200 또는 201': (r) => r.status === 200 || r.status === 201,
    '[대화생성] 응답시간 < 2s': (r) => r.timings.duration < 2000,
  });

  // 3. 대화 메시지 목록 조회
  try {
    const convId = JSON.parse(createRes.body).conversationId
                ?? JSON.parse(createRes.body).id;

    if (convId) {
      const msgRes = http.get(
        `${BASE_URL}/api/chat/conversations/${convId}/messages`,
        { headers, tags: { name: '메시지목록' } }
      );

      check(msgRes, {
        '[메시지목록] 상태코드 200': (r) => r.status === 200,
        '[메시지목록] 응답시간 < 1s': (r) => r.timings.duration < 1000,
      });
    }
  } catch (_) {}

  sleep(1);
}
