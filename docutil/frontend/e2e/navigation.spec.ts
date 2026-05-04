import { test, expect } from '@playwright/test'

test.describe('Navigation - Unauthenticated', () => {
  test('should redirect /dashboard to login', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*login/, { timeout: 30000 })
  })

  test('should redirect /projects to login', async ({ page }) => {
    await page.goto('/projects')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*login/, { timeout: 30000 })
  })

  test('should redirect /documents to login', async ({ page }) => {
    await page.goto('/documents')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*login/, { timeout: 30000 })
  })

  test('should redirect /search-scopes to login', async ({ page }) => {
    await page.goto('/search-scopes')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*login/, { timeout: 30000 })
  })

  test('should redirect /api-keys to login', async ({ page }) => {
    await page.goto('/api-keys')
    await page.waitForLoadState('domcontentloaded')
    await expect(page).toHaveURL(/.*login/, { timeout: 30000 })
  })
})

test.describe('Navigation - Login Page Elements', () => {
  test('should show DocUtil logo on login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('text=DocUtil')).toBeVisible({ timeout: 5000 })
  })

  test('should show Korean labels on login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByText('아이디', { exact: true })).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('비밀번호', { exact: true })).toBeVisible({ timeout: 5000 })
    await expect(page.getByRole('button', { name: '로그인' })).toBeVisible({ timeout: 5000 })
  })

  test('should show Hancom copyright', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('text=Hancom')).toBeVisible({ timeout: 5000 })
  })
})
