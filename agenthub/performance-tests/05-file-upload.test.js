/**
 * 시나리오 05 — 파일 업로드 성능 테스트
 * 대상: POST /api/files/upload
 * 목표: 1MB 파일 업로드 p(95) < 5000ms
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL, TEST_USER } from './config.js';

export const options = {
  thresholds: {
    'http_req_duration{name:파일업로드}': ['p(95)<5000'],
    'http_req_failed': ['rate<0.01'],
  },
  scenarios: {
    file_upload: {
      executor: 'constant-vus',
      vus: 3,        // 파일 업로드는 동시 3명 테스트
      duration: '1m',
    },
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: TEST_USER.email, password: TEST_USER.password }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  if (res.status !== 200) throw new Error(`로그인 실패: ${res.status}`);
  return { token: JSON.parse(res.body).accessToken };
}

export default function (data) {
  // 약 10KB 텍스트 파일 생성 (실제 파일 없이 인메모리 생성)
  const content = 'A'.repeat(10 * 1024);
  const formData = {
    file: http.file(content, 'test-document.txt', 'text/plain'),
  };

  const res = http.post(`${BASE_URL}/api/files/upload`, formData, {
    headers: { Authorization: `Bearer ${data.token}` },
    tags: { name: '파일업로드' },
  });

  check(res, {
    '[파일업로드] 상태코드 200': (r) => r.status === 200,
    '[파일업로드] 응답시간 < 5s': (r) => r.timings.duration < 5000,
    '[파일업로드] fileUrl 존재': (r) => {
      try { return JSON.parse(r.body).fileUrl !== undefined || JSON.parse(r.body).url !== undefined; }
      catch { return false; }
    },
  });

  sleep(2);
}
