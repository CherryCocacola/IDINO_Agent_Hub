import { test, expect } from '@playwright/test'

test.describe('Dashboard Page - Basic', () => {
  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard')
    // Should redirect to login page
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 })
  })

  test('should display DocUtil on login redirect', async ({ page }) => {
    await page.goto('/dashboard')
    // After redirect, should see login page with DocUtil
    await expect(page.locator('text=DocUtil')).toBeVisible({ timeout: 10000 })
  })
})
