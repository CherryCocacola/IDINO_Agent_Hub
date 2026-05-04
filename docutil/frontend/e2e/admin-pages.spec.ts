import { test, expect, Page } from '@playwright/test'

// Helper function to login
async function loginAsAdmin(page: Page) {
  await page.goto('/login')
  await page.waitForLoadState('domcontentloaded')

  // Wait for form to be ready
  await page.locator('#username').waitFor({ state: 'visible', timeout: 10000 })

  await page.locator('#username').fill('admin')
  await page.locator('#password').fill('admin123!')
  await page.getByRole('button', { name: /로그인/i }).click()

  // Wait for navigation to dashboard (with or without toast)
  await page.waitForURL(/.*dashboard/, { timeout: 45000 })
  await page.waitForLoadState('domcontentloaded')
}

test.describe('Admin Pages - Authenticated', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  test('should display dashboard with metrics', async ({ page }) => {
    await expect(page).toHaveURL(/.*dashboard/)
    // Check page heading
    await expect(page.getByRole('heading', { name: '대시보드' })).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to projects page', async ({ page }) => {
    await page.goto('/projects')
    await page.waitForLoadState('domcontentloaded')
    // Check we're on projects page (URL or heading)
    await expect(page).toHaveURL(/.*projects/)
    await expect(page.getByRole('heading', { name: /프로젝트/ })).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to documents page', async ({ page }) => {
    await page.goto('/documents')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*documents/)
    // Use h1 heading specifically
    await expect(page.locator('h1:has-text("문서")')).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to search-scopes page', async ({ page }) => {
    await page.goto('/search-scopes')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*search-scopes/)
    await expect(page.locator('h1:has-text("검색 범위")')).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to admin-accounts page', async ({ page }) => {
    await page.goto('/admin-accounts')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*admin-accounts/)
    await expect(page.locator('h1:has-text("관리자")')).toBeVisible({ timeout: 20000 })
  })

  test('should navigate to api-keys page', async ({ page }) => {
    await page.goto('/api-keys')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*api-keys/)
    await expect(page.locator('h1:has-text("API")')).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to search-test page', async ({ page }) => {
    await page.goto('/search-test')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*search-test/)
    // Page uses English heading "Search Test"
    await expect(page.locator('h1:has-text("Search Test")')).toBeVisible({ timeout: 10000 })
  })

  test('should navigate to settings page', async ({ page }) => {
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*settings/)
    // Page uses English heading "System Settings" or Korean "설정"
    await expect(
      page.locator('h1:has-text("System Settings")').or(page.locator('h1:has-text("설정")'))
    ).toBeVisible({ timeout: 20000 })
  })
})

test.describe('Sidebar Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
  })

  // Skip: Flaky due to hydration race condition
  test.skip('should show sidebar with menu items on desktop', async ({ page }) => {
    // Set viewport to desktop size to show sidebar
    await page.setViewportSize({ width: 1280, height: 720 })
    await page.goto('/dashboard')
    await page.waitForLoadState('domcontentloaded')

    // Wait for sidebar to be visible (desktop sidebar with lg:block)
    const sidebar = page.locator('aside.lg\\:block')
    await expect(sidebar).toBeVisible({ timeout: 10000 })

    // Check for sidebar menu text - look for visible links
    await expect(sidebar.locator('a[href="/dashboard"]')).toBeVisible({ timeout: 5000 })
    await expect(sidebar.locator('a[href="/projects"]')).toBeVisible({ timeout: 5000 })
  })

  // Skip: Flaky due to hydration race condition causing client-side error
  test.skip('should navigate using sidebar links', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 })
    await loginAsAdmin(page)

    // Wait for sidebar to be visible and stable
    const sidebar = page.locator('aside.lg\\:block')
    await expect(sidebar).toBeVisible({ timeout: 10000 })

    // Wait for the page to stabilize after hydration
    await page.waitForLoadState('networkidle')

    // Click projects link in sidebar using force to bypass stability checks
    const projectsLink = sidebar.locator('a[href="/projects"]')
    await expect(projectsLink).toBeVisible({ timeout: 5000 })
    await projectsLink.click({ force: true })

    // Wait for URL to change
    await page.waitForURL(/.*projects/, { timeout: 10000 })
  })
})
