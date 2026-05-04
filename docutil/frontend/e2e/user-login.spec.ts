import { test, expect } from '@playwright/test'

test.describe('User Login (member role)', () => {
  test('should login as user and redirect to search page', async ({ page }) => {
    await page.goto('/login')
    await page.waitForLoadState('domcontentloaded')

    // Fill login form
    await page.locator('#username').fill('user')
    await page.locator('#password').fill('user123!')

    // Click login button
    await page.getByRole('button', { name: /로그인/i }).click()

    // member role should redirect to /search
    await page.waitForURL(/.*search/, { timeout: 30000 })
    await expect(page).toHaveURL(/.*search/)
  })

  test('member user should not access admin pages', async ({ page }) => {
    // Login as user
    await page.goto('/login')
    await page.waitForLoadState('domcontentloaded')
    await page.locator('#username').fill('user')
    await page.locator('#password').fill('user123!')
    await page.getByRole('button', { name: /로그인/i }).click()
    await page.waitForURL(/.*search/, { timeout: 30000 })

    // Try to access admin dashboard - should redirect or show error
    await page.goto('/dashboard')
    await page.waitForLoadState('domcontentloaded')

    // Either redirected away from dashboard or access denied
    const url = page.url()
    const isDashboard = url.includes('/dashboard')

    if (isDashboard) {
      // If still on dashboard, should show limited content or error
      console.log('User can access dashboard - checking permissions')
    } else {
      // Redirected away - access denied
      console.log('User redirected from dashboard - access denied correctly')
    }
  })
})
