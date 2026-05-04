import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 2,
  workers: 1,
  timeout: 60000,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3003',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    navigationTimeout: 30000,
    actionTimeout: 15000,
  },
  expect: {
    timeout: 15000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // 로컬 환경: 프론트엔드 dev 서버 자동 시작
  // Docker 환경에서는 이 섹션을 주석 처리하고 위의 baseURL만 사용
  webServer: {
    command: 'npm run dev -- -p 3003',
    url: 'http://localhost:3003',
    reuseExistingServer: true,
    timeout: 120000,
  },
})
