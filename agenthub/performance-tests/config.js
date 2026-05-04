// =============================================================
// 성능 테스트 공통 설정
// =============================================================

export const BASE_URL = __ENV.BASE_URL || 'http://localhost:64005';

// 테스트 계정 (시험환경에서 미리 생성 필요)
export const TEST_ADMIN = {
  email: __ENV.ADMIN_EMAIL || 'admin@test.com',
  password: __ENV.ADMIN_PASSWORD || 'Test1234!',
};

export const TEST_USER = {
  email: __ENV.USER_EMAIL || 'user@test.com',
  password: __ENV.USER_PASSWORD || 'Test1234!',
};

// GS인증 합격 기준 (목표값)
export const THRESHOLDS = {
  // 응답 시간: 일반 API 2초 이내 (95th percentile)
  'http_req_duration': ['p(95)<2000'],
  // 오류율: 1% 미만
  'http_req_failed': ['rate<0.01'],
  // 초당 처리량 확인용 (최소 5 RPS 이상)
  'http_reqs': ['rate>5'],
};
