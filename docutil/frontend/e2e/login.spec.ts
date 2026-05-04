import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.waitForLoadState('networkidle')
  })

  test('should display login form with Pedia design', async ({ page }) => {
    // Check for logo
    await expect(page.locator('text=DocUtil')).toBeVisible()

    // Check for form elements using input IDs
    await expect(page.locator('#username')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
    await expect(page.getByRole('button', { name: /로그인/i })).toBeVisible()

    // Check for remember me checkbox
    await expect(page.locator('#remember-me')).toBeVisible()

    // Check for copyright
    await expect(page.locator('text=Hancom')).toBeVisible()
  })

  test('should show error when submitting empty form', async ({ page }) => {
    await page.getByRole('button', { name: /로그인/i }).click()
    await expect(page.locator('text=아이디와 비밀번호를 입력해주세요')).toBeVisible()
  })

  test('should toggle password visibility', async ({ page }) => {
    const passwordInput = page.locator('#password')

    // Initially password should be hidden
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // Click toggle button using aria-label
    await page.locator('button[aria-label="비밀번호 보기"]').click()
    await expect(passwordInput).toHaveAttribute('type', 'text')

    // Click again to hide
    await page.locator('button[aria-label="비밀번호 숨기기"]').click()
    await expect(passwordInput).toHaveAttribute('type', 'password')
  })

  test('should show error on invalid credentials', async ({ page }) => {
    await page.locator('#username').fill('wronguser')
    await page.locator('#password').fill('wrongpassword')
    await page.getByRole('button', { name: /로그인/i }).click()

    // Wait for error message from real API
    await expect(
      page.locator('text=올바르지 않습니다').or(page.locator('text=Invalid')).or(page.locator('text=오류'))
    ).toBeVisible({ timeout: 15000 })
  })

  test('should login with valid credentials and redirect to dashboard', async ({ page }) => {
    // Real API login - no mocking
    await page.locator('#username').fill('admin')
    await page.locator('#password').fill('admin123!')

    // Click login button
    await page.getByRole('button', { name: /로그인/i }).click()

    // Wait for success toast and then navigation
    await expect(page.locator('text=로그인되었습니다')).toBeVisible({ timeout: 10000 })
    await page.waitForURL(/.*dashboard/, { timeout: 30000 })
  })

  test('should check remember me checkbox', async ({ page }) => {
    const checkbox = page.locator('#remember-me')
    await expect(checkbox).not.toBeChecked()
    await checkbox.check()
    await expect(checkbox).toBeChecked()
  })

  test('should have proper form styling', async ({ page }) => {
    // Check that the form card has white background
    const card = page.locator('.rounded-2xl.bg-white').first()
    await expect(card).toBeVisible()

    // Check that the login button has primary color (purple)
    const button = page.getByRole('button', { name: /로그인/i })
    await expect(button).toHaveClass(/bg-primary/)
  })
})
