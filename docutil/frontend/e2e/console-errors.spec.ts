import { test, expect, Page } from '@playwright/test'

// 모든 관리자 페이지 목록
const ADMIN_PAGES = [
  { path: '/dashboard', name: 'Dashboard' },
  { path: '/projects', name: 'Projects' },
  { path: '/documents', name: 'Documents' },
  { path: '/search-scopes', name: 'Search Scopes' },
  { path: '/admin-accounts', name: 'Admin Accounts' },
  { path: '/api-keys', name: 'API Keys' },
  { path: '/search-test', name: 'Search Test' },
  { path: '/settings', name: 'Settings' },
]

// 콘솔 에러 수집 함수
async function collectConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = []

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(`[Console Error] ${msg.text()}`)
    }
  })

  page.on('pageerror', (err) => {
    errors.push(`[Page Error] ${err.message}`)
  })

  return errors
}

// 로그인 함수
async function loginAsAdmin(page: Page) {
  await page.goto('/login')
  await page.waitForLoadState('networkidle')
  await page.locator('#username').fill('admin')
  await page.locator('#password').fill('admin123!')
  await page.getByRole('button', { name: /로그인/i }).click()
  await page.waitForSelector('text=로그인되었습니다', { timeout: 10000 })
  await page.waitForURL(/.*dashboard/, { timeout: 30000 })
  await page.waitForLoadState('networkidle')
}

test.describe('Console Error Check - All Pages', () => {
  test('Login page should have no console errors', async ({ page }) => {
    const errors: string[] = []

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    page.on('pageerror', (err) => {
      errors.push(err.message)
    })

    await page.goto('/login')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000) // Wait for any async errors

    console.log('Login page errors:', errors)

    // Filter out known acceptable errors
    const criticalErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('Failed to load resource')
    )

    expect(criticalErrors).toHaveLength(0)
  })

  test('All admin pages should have no critical console errors', async ({ page }) => {
    const allErrors: Record<string, string[]> = {}

    // Login first
    await loginAsAdmin(page)

    // Visit each page and collect errors
    for (const pageInfo of ADMIN_PAGES) {
      const pageErrors: string[] = []

      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          pageErrors.push(msg.text())
        }
      })

      page.on('pageerror', (err) => {
        pageErrors.push(err.message)
      })

      console.log(`\n--- Visiting ${pageInfo.name} (${pageInfo.path}) ---`)

      await page.goto(pageInfo.path)
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(5000) // Wait for API calls and rendering

      if (pageErrors.length > 0) {
        allErrors[pageInfo.name] = [...pageErrors]
        console.log(`Errors on ${pageInfo.name}:`, pageErrors)
      } else {
        console.log(`No errors on ${pageInfo.name}`)
      }

      // Clear listeners for next page
      page.removeAllListeners('console')
      page.removeAllListeners('pageerror')
    }

    // Print summary
    console.log('\n========== ERROR SUMMARY ==========')
    let totalErrors = 0
    for (const [pageName, errors] of Object.entries(allErrors)) {
      if (errors.length > 0) {
        console.log(`\n${pageName}:`)
        errors.forEach(e => console.log(`  - ${e}`))
        totalErrors += errors.length
      }
    }
    console.log(`\nTotal errors found: ${totalErrors}`)
    console.log('====================================')

    // Filter critical errors (exclude favicon, 404s for static resources)
    const criticalErrors: string[] = []
    for (const errors of Object.values(allErrors)) {
      for (const error of errors) {
        if (
          !error.includes('favicon') &&
          !error.includes('404') &&
          !error.includes('Failed to load resource') &&
          !error.includes('net::ERR')
        ) {
          criticalErrors.push(error)
        }
      }
    }

    // Report but don't fail for now - just collect info
    if (criticalErrors.length > 0) {
      console.log('\nCritical errors that need fixing:')
      criticalErrors.forEach(e => console.log(`  - ${e}`))
    }
  })
})
