import { test, expect, Page } from '@playwright/test'

/**
 * 서버(192.168.10.39) 대상 스모크 테스트
 * 각 단계마다 스크린샷을 저장하여 시각적으로 확인 가능
 */

const BASE_URL = 'http://192.168.10.39:8041'
const SCREENSHOT_DIR = 'e2e-screenshots'

test.describe.serial('Server Smoke Test', () => {
  let page: Page

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage()
  })

  test.afterAll(async () => {
    await page.close()
  })

  test('01. 로그인 페이지 접속', async () => {
    await page.goto(`${BASE_URL}/login`)
    await page.waitForLoadState('domcontentloaded')
    await page.locator('#username').waitFor({ state: 'visible', timeout: 15000 })
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-01-login-page.png`, fullPage: true })
    await expect(page.locator('#username')).toBeVisible()
  })

  test('02. 로그인 수행', async () => {
    await page.locator('#username').fill('admin')
    await page.locator('#password').fill('admin123!')
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-02-login-filled.png`, fullPage: true })
    await page.getByRole('button', { name: /로그인/i }).click()
    await expect(page.locator('text=로그인되었습니다')).toBeVisible({ timeout: 15000 })
    await page.waitForURL(/.*dashboard/, { timeout: 30000 })
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-03-dashboard.png`, fullPage: true })
  })

  test('03. 프로젝트 페이지', async () => {
    await page.goto(`${BASE_URL}/projects`)
    await page.waitForLoadState('networkidle', )
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-04-projects.png`, fullPage: true })
  })

  test('04. 문서 페이지', async () => {
    await page.goto(`${BASE_URL}/documents`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-05-documents.png`, fullPage: true })
  })

  test('05. 검색 페이지', async () => {
    await page.goto(`${BASE_URL}/search`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // 검색 입력
    const searchInput = page.locator('input[type="text"], input[placeholder*="검색"], textarea').first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('기술 스택')
      await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-06-search-query.png`, fullPage: true })

      // 검색 실행 (Enter 또는 버튼)
      await searchInput.press('Enter')
      await page.waitForTimeout(3000)
      await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-07-search-results.png`, fullPage: true })
    } else {
      await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-06-search-page.png`, fullPage: true })
    }
  })

  test('06. 챗봇 페이지', async () => {
    await page.goto(`${BASE_URL}/chat`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-08-chat-page.png`, fullPage: true })

    // 심층 검색 토글 확인
    const deepSearchBtn = page.locator('button:has-text("심층 검색")')
    if (await deepSearchBtn.isVisible()) {
      await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-09-deep-search-toggle.png`, fullPage: true })
    }
  })

  test('07. 보고서 페이지', async () => {
    await page.goto(`${BASE_URL}/reports`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-10-reports.png`, fullPage: true })
  })

  test('08. 템플릿 관리 (관리자)', async () => {
    await page.goto(`${BASE_URL}/templates`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-11-templates.png`, fullPage: true })
  })

  test('09. 에이전트 관리 (관리자)', async () => {
    await page.goto(`${BASE_URL}/agents`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-12-agents.png`, fullPage: true })
  })

  test('10. 사용자 관리 (관리자)', async () => {
    await page.goto(`${BASE_URL}/admin-accounts`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-13-admin-accounts.png`, fullPage: true })
  })

  test('11. 설정 페이지', async () => {
    await page.goto(`${BASE_URL}/settings`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)
    await page.screenshot({ path: `${SCREENSHOT_DIR}/smoke-14-settings.png`, fullPage: true })
  })
})
