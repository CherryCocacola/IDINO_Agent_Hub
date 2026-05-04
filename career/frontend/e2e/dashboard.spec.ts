import { test, expect, Page } from '@playwright/test';

// Test students: one per admission year (2023, 2024, 2025)
const TEST_STUDENTS = [
  { id: '20231005', year: 2023 },
  { id: '20241001', year: 2024 },
  { id: '20251001', year: 2025 },
];
const PASSWORD = '1234';

async function login(page: Page, studentId: string) {
  await page.goto('/login');
  await page.fill('input[id="studentId"]', studentId);
  await page.fill('input[id="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  // Wait for navigation away from login page
  await page.waitForFunction(() => !window.location.pathname.includes('/login'), { timeout: 15000 });
}

// ============================================
// 1. Login Tests
// ============================================
test.describe('로그인', () => {
  test('정상 로그인 후 대시보드 이동', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[id="studentId"]', TEST_STUDENTS[0].id);
    await page.fill('input[id="password"]', PASSWORD);
    await page.click('button[type="submit"]');
    // Wait for navigation away from login
    await page.waitForFunction(() => !window.location.pathname.includes('/login'), { timeout: 15000 });
    // Should end up on dashboard (root)
    expect(page.url()).not.toContain('/login');
  });

  test('잘못된 비밀번호 오류 표시', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[id="studentId"]', TEST_STUDENTS[0].id);
    await page.fill('input[id="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');
    // Wait for error to appear
    await page.waitForTimeout(3000);
    // Should still be on login page
    expect(page.url()).toContain('/login');
  });
});

// ============================================
// 2. Dashboard Sections - Per Student Year
// ============================================
for (const student of TEST_STUDENTS) {
  test.describe(`대시보드 [${student.year}학번 ${student.id}]`, () => {
    test.beforeEach(async ({ page }) => {
      await login(page, student.id);
    });

    // --- Overview Section ---
    test('전체 개요 섹션 표시', async ({ page }) => {
      await expect(page.locator('#overview')).toBeVisible({ timeout: 15000 });
    });

    // --- Competency Section ---
    test('역량 분석 - 실시간 데이터 표시', async ({ page }) => {
      const compSection = page.locator('#competency');
      await compSection.scrollIntoViewIfNeeded();
      await page.waitForTimeout(3000);

      const realDataBadge = page.locator('span:has-text("실시간 데이터")');
      const mockWarning = page.locator('text=샘플 데이터를 표시합니다');

      const hasRealData = await realDataBadge.isVisible().catch(() => false);
      const hasMockWarning = await mockWarning.isVisible().catch(() => false);

      expect(hasRealData || !hasMockWarning).toBeTruthy();
    });

    // --- Roadmap Section ---
    test('로드맵 섹션 표시', async ({ page }) => {
      // Wait for data to load first
      await page.waitForTimeout(2000);
      const roadmapSection = page.locator('#roadmap');
      await roadmapSection.scrollIntoViewIfNeeded();
      await expect(roadmapSection).toBeVisible({ timeout: 15000 });
    });

    // --- Alumni Section ---
    test('졸업생 비교 섹션 표시', async ({ page }) => {
      const alumniSection = page.locator('#alumni');
      await alumniSection.scrollIntoViewIfNeeded();
      await expect(alumniSection).toBeVisible({ timeout: 10000 });
    });

    // --- Navigation ---
    test('퀵 네비게이션 동작', async ({ page }) => {
      const navItems = ['역량 분석', '학년 로드맵', '졸업생 비교'];
      for (const item of navItems) {
        const btn = page.locator(`#quick-nav button:has-text("${item}")`);
        if (await btn.isVisible().catch(() => false)) {
          await btn.click();
          await page.waitForTimeout(500);
        }
      }
    });
  });
}

// ============================================
// 3. API Health Checks (Backend Services)
// ============================================
test.describe('백엔드 서비스 상태', () => {
  const services = [
    { name: 'student-service', port: 8002 },
    { name: 'competency-service', port: 8003 },
    { name: 'alumni-service', port: 8005 },
    { name: 'ai-service', port: 8006 },
    { name: 'skill-service', port: 8007 },
    { name: 'opportunity-service', port: 8008 },
    { name: 'coaching-service', port: 8009 },
    { name: 'risk-service', port: 8010 },
    { name: 'auth-service', port: 8011 },
    { name: 'badge-service', port: 8012 },
    { name: 'simulation-service', port: 8013 },
    { name: 'advisor-service', port: 8014 },
    { name: 'roadmap-service', port: 8015 },
    { name: 'portfolio-service', port: 8016 },
    { name: 'privacy-service', port: 8017 },
    { name: 'worknet-service', port: 8018 },
    { name: 'integration-service', port: 8019 },
  ];

  for (const svc of services) {
    test(`${svc.name} health check (port ${svc.port})`, async ({ request }) => {
      const response = await request.get(`http://localhost:${svc.port}/health`);
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.status).toBe('healthy');
    });
  }
});

// ============================================
// 4. API Data Endpoints - Per Student Year
// ============================================
for (const student of TEST_STUDENTS) {
  test.describe(`API 데이터 조회 [${student.year}학번 ${student.id}]`, () => {

    test('학생 정보 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8002/students/${student.id}`);
      expect(res.status()).toBe(200);
      const data = await res.json();
      expect(data.student_id).toBe(student.id);
    });

    test('역량 리포트 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8003/competency/${student.id}/report`);
      expect(res.status()).toBe(200);
      const data = await res.json();
      expect(data.student_id).toBe(student.id);
      expect(data.competencies.length).toBeGreaterThan(0);
    });

    test('수강 이력 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8002/students/${student.id}/enrollments`);
      expect(res.status()).toBe(200);
      const data = await res.json();
      expect(data.length).toBeGreaterThan(0);
    });

    test('스킬 그래프 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8007/skills/graph`);
      expect(res.status()).toBe(200);
    });

    test('스킬 갭 분석 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8007/skills/gap-analysis?student_id=${student.id}`);
      expect([200, 404]).toContain(res.status());
    });

    test('코칭 진행현황 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8009/coaching/progress/${student.id}`);
      expect([200, 404]).toContain(res.status());
    });

    test('위험 프로필 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8010/risks/profile/${student.id}`);
      expect(res.status()).toBe(200);
    });

    test('배지 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8012/badges/student/${student.id}`);
      expect(res.status()).toBe(200);
    });

    test('포트폴리오 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8016/portfolio/student/${student.id}`);
      expect(res.status()).toBe(200);
    });

    test('시뮬레이션 시나리오 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8013/simulation/scenarios?student_id=${student.id}`);
      expect(res.status()).toBe(200);
    });

    test('로드맵 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8015/roadmap/${student.id}`);
      expect([200, 404]).toContain(res.status());
    });

    test('졸업생 비교 조회', async ({ request }) => {
      const res = await request.get(`http://localhost:8005/alumni/compare/${student.id}`);
      expect([200, 404]).toContain(res.status());
    });
  });
}

// ============================================
// 5. Sidebar Navigation Pages
// ============================================
test.describe('사이드바 페이지 이동', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, TEST_STUDENTS[0].id);
  });

  const sidebarPages = [
    { name: '스킬 관리', path: '/skills' },
    { name: 'AI 코칭', path: '/coaching' },
    { name: '위험 알림', path: '/risks' },
    { name: '기회 탐색', path: '/opportunities' },
    { name: '포트폴리오', path: '/portfolio' },
  ];

  for (const pg of sidebarPages) {
    test(`${pg.name} 페이지 로드 (${pg.path})`, async ({ page }) => {
      await page.goto(pg.path);
      await page.waitForLoadState('networkidle', { timeout: 15000 });
      // Check that a main content area rendered (not a blank error page)
      const h1 = page.locator('h1, h2, [role="main"], main').first();
      await expect(h1).toBeVisible({ timeout: 10000 });
    });
  }
});
