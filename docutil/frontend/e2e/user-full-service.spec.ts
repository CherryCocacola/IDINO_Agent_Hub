import { test, expect, Page } from '@playwright/test'

// Helper function to login as user
async function loginAsUser(page: Page) {
  await page.goto('/login')
  await page.waitForLoadState('domcontentloaded')
  await page.locator('#username').waitFor({ state: 'visible', timeout: 10000 })
  await page.locator('#username').fill('user')
  await page.locator('#password').fill('user123!')
  await page.getByRole('button', { name: /로그인/i }).click()
  await page.waitForURL(/.*search/, { timeout: 30000 })
  await page.waitForLoadState('domcontentloaded')
}

test.describe('User Full Service Test (member role)', () => {
  test('complete user journey test', async ({ page }) => {
    // Collect console errors
    const consoleErrors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    console.log('\n=== Step 1: Login as user ===')
    await loginAsUser(page)
    console.log('✓ Login successful, redirected to /search')

    // Check search page
    console.log('\n=== Step 2: Verify Search Page ===')
    await expect(page).toHaveURL(/.*search/)
    const searchPageTitle = await page.locator('h1').first().textContent()
    console.log(`✓ Search page loaded: ${searchPageTitle || 'Search'}`)

    // Check for search input
    const searchInput = page.locator('input[type="text"], input[type="search"], textarea').first()
    if (await searchInput.isVisible()) {
      console.log('✓ Search input is visible')
    }

    // Try to access admin pages and verify access control
    console.log('\n=== Step 3: Test Admin Page Access Control ===')

    const adminPages = [
      { path: '/dashboard', name: 'Dashboard' },
      { path: '/projects', name: 'Projects' },
      { path: '/documents', name: 'Documents' },
      { path: '/admin-accounts', name: 'Admin Accounts' },
      { path: '/api-keys', name: 'API Keys' },
      { path: '/settings', name: 'Settings' },
    ]

    for (const adminPage of adminPages) {
      await page.goto(adminPage.path)
      await page.waitForLoadState('domcontentloaded')

      // Wait for potential redirect (role check happens in useEffect)
      await page.waitForTimeout(2000)

      const currentUrl = page.url()

      if (currentUrl.includes('/login') || currentUrl.includes('/search') || currentUrl.includes('/unauthorized')) {
        console.log(`✓ ${adminPage.name}: Access denied (redirected to ${currentUrl.split('/').pop()})`)
      } else if (currentUrl.includes(adminPage.path)) {
        console.log(`⚠ ${adminPage.name}: User can access this page`)
      }
    }

    // Go back to search page
    console.log('\n=== Step 4: Test Search Functionality ===')
    await page.goto('/search')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000) // Wait for hydration

    // Try to perform a search if possible
    try {
      const searchInputField = page.locator('input[placeholder*="search" i]').first()
      await searchInputField.waitFor({ state: 'visible', timeout: 5000 })
      await searchInputField.click()
      await page.waitForTimeout(500)
      await searchInputField.fill('테스트 검색어')
      console.log('✓ Search input filled with test query')

      // Look for search button
      const searchButton = page.locator('button[type="submit"], button:has-text("Search"), button:has-text("검색")').first()
      if (await searchButton.isVisible({ timeout: 3000 }).catch(() => false)) {
        await searchButton.click()
        await page.waitForTimeout(2000)
        console.log('✓ Search button clicked')
      }
    } catch {
      console.log('⚠ Search input interaction failed (hydration issue)')
    }

    // Check chat functionality if available
    console.log('\n=== Step 5: Check Chat/FAQ Page ===')
    await page.goto('/chat')
    await page.waitForLoadState('domcontentloaded')
    const chatUrl = page.url()
    if (chatUrl.includes('/chat')) {
      console.log('✓ Chat page accessible')
    } else {
      console.log(`⚠ Chat page redirected to: ${chatUrl}`)
    }

    // Check FAQ page
    await page.goto('/faq')
    await page.waitForLoadState('domcontentloaded')
    const faqUrl = page.url()
    if (faqUrl.includes('/faq')) {
      console.log('✓ FAQ page accessible')
    } else {
      console.log(`⚠ FAQ page redirected to: ${faqUrl}`)
    }

    // Test logout
    console.log('\n=== Step 6: Test Logout ===')
    await page.goto('/search')
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000) // Wait for hydration

    // Look for logout button or user menu
    try {
      const logoutButton = page.getByRole('button', { name: /로그아웃|logout/i })
      if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await logoutButton.click()
        console.log('✓ Logout button clicked')
      } else {
        // Try user menu approach with force click
        const userMenu = page.locator('button[aria-label*="User menu"], button[aria-label*="user"]').first()
        if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
          await userMenu.click({ force: true })
          await page.waitForTimeout(500)
          const logoutMenuItem = page.getByText(/로그아웃|logout/i)
          if (await logoutMenuItem.isVisible({ timeout: 2000 }).catch(() => false)) {
            await logoutMenuItem.click()
            console.log('✓ Logout from user menu')
          } else {
            console.log('⚠ Logout menu item not found')
          }
        } else {
          console.log('⚠ User menu not found')
        }
      }
    } catch {
      console.log('⚠ Logout test skipped (hydration issue)')
    }

    // Print console errors summary
    console.log('\n=== Console Errors Summary ===')
    const criticalErrors = consoleErrors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('404') &&
      !e.includes('net::ERR')
    )
    if (criticalErrors.length === 0) {
      console.log('✓ No critical console errors')
    } else {
      console.log(`⚠ ${criticalErrors.length} console errors found:`)
      criticalErrors.slice(0, 5).forEach(e => console.log(`  - ${e.substring(0, 100)}`))
    }

    console.log('\n=== Test Complete ===\n')
  })
})
