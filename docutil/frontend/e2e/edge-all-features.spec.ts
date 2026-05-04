import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

/**
 * Edge 브라우저 전체 기능 테스트
 *
 * 실행: npx playwright test e2e/edge-all-features.spec.ts --headed
 *
 * 모든 페이지와 기능을 순서대로 테스트하며,
 * slowMo를 적용하여 사용자가 화면을 볼 수 있게 한다.
 */

test.use({
  channel: 'msedge',
  viewport: { width: 1440, height: 900 },
  launchOptions: { slowMo: 500 }, // 동작 간 0.5초 대기 (화면 확인용)
})

const SCREENSHOT_DIR = path.join(process.cwd(), 'e2e-screenshots')

function createTestFile(name: string, content: string): string {
  const tmpDir = path.join(process.cwd(), '.playwright-tmp')
  if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true })
  const filePath = path.join(tmpDir, name)
  fs.writeFileSync(filePath, content, 'utf-8')
  return filePath
}

async function shot(page: any, name: string) {
  if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${name}.png`), fullPage: true })
}

test('Edge 전체 기능 테스트', async ({ page }) => {
  test.setTimeout(600000) // 10분

  let testFiles: string[] = []

  try {
    // ================================================================
    // 1. 로그인
    // ================================================================
    console.log('\n[1] 로그인 페이지')
    await page.goto('/login')
    await page.waitForLoadState('domcontentloaded')
    await page.locator('#username').waitFor({ state: 'visible', timeout: 15000 })
    await page.waitForTimeout(1000)
    await shot(page, '01-login')

    await page.locator('#username').fill('admin')
    await page.locator('#password').fill('admin123!')
    await page.waitForTimeout(500)
    await page.getByRole('button', { name: /로그인/i }).click()
    await expect(page.locator('text=로그인되었습니다')).toBeVisible({ timeout: 15000 })
    await page.waitForURL(/.*dashboard/, { timeout: 30000 })
    await page.waitForTimeout(2000)
    await shot(page, '02-dashboard')
    console.log('  -> 로그인 성공, 대시보드 표시')

    // ================================================================
    // 2. 대시보드
    // ================================================================
    console.log('\n[2] 대시보드')
    await page.waitForTimeout(2000)
    // 메트릭 카드 확인
    const cards = page.locator('[class*="card"], [class*="Card"]')
    console.log(`  -> 카드 ${await cards.count()}개`)
    await shot(page, '03-dashboard-loaded')

    // ================================================================
    // 3. 프로젝트 관리
    // ================================================================
    console.log('\n[3] 프로젝트 관리')
    await page.goto('/projects')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '04-projects')

    // 프로젝트 생성
    const createProjectBtn = page.locator('button:has-text("프로젝트 생성"), button:has-text("Create")')
    if (await createProjectBtn.first().isVisible({ timeout: 5000 }).catch(() => false)) {
      await createProjectBtn.first().click()
      await page.waitForTimeout(1000)

      const dialog = page.locator('[role="dialog"]')
      if (await dialog.isVisible({ timeout: 3000 })) {
        const nameInput = dialog.locator('input').first()
        await nameInput.fill('E2E 테스트 프로젝트')
        await page.waitForTimeout(500)
        await shot(page, '05-project-create-dialog')

        const saveBtn = dialog.locator('button[type="submit"], button:has-text("생성"), button:has-text("Create"), button:has-text("저장")')
        if (await saveBtn.first().isVisible({ timeout: 2000 }).catch(() => false)) {
          await saveBtn.first().click()
          await page.waitForTimeout(2000)
        }
      }
    }
    await shot(page, '06-projects-after-create')
    console.log('  -> 프로젝트 목록 확인')

    // 보드 생성 시도
    const expandBtns = page.locator('button:has(svg[class*="chevron"]), td button').first()
    if (await expandBtns.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expandBtns.click()
      await page.waitForTimeout(1000)
    }
    await shot(page, '07-projects-expanded')

    // ================================================================
    // 4. 문서 관리 페이지
    // ================================================================
    console.log('\n[4] 문서 관리')
    await page.goto('/documents')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(3000)
    await shot(page, '08-documents-page')

    // 폴더 트리 확장
    const treeButtons = page.locator('button').filter({ has: page.locator('svg') })
    for (let i = 0; i < Math.min(await treeButtons.count(), 8); i++) {
      const btn = treeButtons.nth(i)
      const text = await btn.textContent().catch(() => '')
      if (text && !text.includes('업로드') && !text.includes('Search') && !text.includes('접기')) {
        await btn.click().catch(() => {})
        await page.waitForTimeout(300)
      }
    }
    await page.waitForTimeout(1000)
    await shot(page, '09-documents-tree')

    // 문서 업로드
    const testFile1 = createTestFile('test-doc-1.txt', [
      '# AI 문서 활용 시스템 소개',
      '',
      'DocUtil은 한컴에서 개발한 엔터프라이즈 문서 활용 솔루션입니다.',
      '문서를 업로드하면 AI가 자동으로 파싱하고 벡터화하여,',
      '자연어 검색과 질의응답을 제공합니다.',
      '',
      '## 핵심 기능',
      '- 하이브리드 검색 (의미 + 키워드)',
      '- Agentic RAG 기반 Q&A',
      '- WebSocket 실시간 채팅',
      '- 리포트 자동 생성',
    ].join('\n'))
    testFiles.push(testFile1)

    const testFile2 = createTestFile('test-doc-2.txt', [
      '# 기술 스택 문서',
      '',
      '## 백엔드',
      'FastAPI, SQLAlchemy 2.0, PostgreSQL 17, Celery, RabbitMQ',
      '',
      '## 프론트엔드',
      'Next.js 16, React 19, Tailwind CSS v4, Zustand 5',
      '',
      '## AI/ML',
      'GPT-4o, OpenAI Embedding, Qdrant Vector DB',
      '',
      '## 인프라',
      'Docker Compose, Nginx, Redis, MinIO',
    ].join('\n'))
    testFiles.push(testFile2)

    const fileInput = page.locator('input[type="file"]')
    if (await fileInput.count() > 0) {
      // 첫 번째 파일
      await fileInput.setInputFiles(testFile1)
      await page.waitForTimeout(3000)
      await shot(page, '10-document-upload-1')
      console.log('  -> 문서 1 업로드')

      // 두 번째 파일
      await fileInput.setInputFiles(testFile2)
      await page.waitForTimeout(3000)
      await shot(page, '11-document-upload-2')
      console.log('  -> 문서 2 업로드')
    }

    // 문서 테이블 확인
    await page.waitForTimeout(2000)
    await shot(page, '12-documents-list')

    // ================================================================
    // 5. 검색 범위 설정
    // ================================================================
    console.log('\n[5] 검색 범위 설정')
    await page.goto('/search-scopes')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '13-search-scopes')
    console.log('  -> 검색 범위 페이지 확인')

    // ================================================================
    // 6. 검색 테스트 (관리자)
    // ================================================================
    console.log('\n[6] 검색 테스트 (관리자)')
    await page.goto('/search-test')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '14-search-test-page')

    // 검색 범위 선택 후 검색
    const searchTestInput = page.locator('input[placeholder*="search" i], input[placeholder*="검색" i], textarea').first()
    if (await searchTestInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchTestInput.fill('DocUtil system features')
      await page.waitForTimeout(500)
      await shot(page, '15-search-test-query')

      // 검색 실행 버튼
      const searchBtn = page.locator('button:has-text("Search"), button:has-text("검색"), button[type="submit"]').first()
      if (await searchBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await searchBtn.click()
        await page.waitForTimeout(5000)
        await shot(page, '16-search-test-results')
        console.log('  -> 검색 테스트 실행')
      }
    }

    // ================================================================
    // 7. 관리자 계정 관리
    // ================================================================
    console.log('\n[7] 관리자 계정')
    await page.goto('/admin-accounts')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '17-admin-accounts')
    console.log('  -> 관리자 계정 페이지')

    // ================================================================
    // 8. API 키 관리
    // ================================================================
    console.log('\n[8] API 키 관리')
    await page.goto('/api-keys')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '18-api-keys')
    console.log('  -> API 키 페이지')

    // ================================================================
    // 9. 시스템 설정
    // ================================================================
    console.log('\n[9] 시스템 설정')
    await page.goto('/settings')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '19-settings-general')

    // 보안 탭 클릭
    const securityTab = page.locator('button:has-text("보안"), button:has-text("Security"), [role="tab"]:has-text("보안")')
    if (await securityTab.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await securityTab.first().click()
      await page.waitForTimeout(1000)
      await shot(page, '20-settings-security')
    }

    // 스토리지 탭 클릭
    const storageTab = page.locator('button:has-text("스토리지"), button:has-text("Storage"), [role="tab"]:has-text("스토리지")')
    if (await storageTab.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await storageTab.first().click()
      await page.waitForTimeout(1000)
      await shot(page, '21-settings-storage')
    }
    console.log('  -> 설정 3탭 확인')

    // ================================================================
    // 10. 퀵 가이드
    // ================================================================
    console.log('\n[10] 퀵 가이드')
    await page.goto('/quick-guide')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(1000)
    await shot(page, '22-quick-guide')
    console.log('  -> 퀵 가이드 페이지')

    // ================================================================
    // 11. 도움말 (FAQ)
    // ================================================================
    console.log('\n[11] 도움말')
    await page.goto('/help')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(1000)
    await shot(page, '23-help-faq')

    // FAQ 아코디언 열기
    const faqItem = page.locator('[data-state="closed"], button[class*="Accordion"]').first()
    if (await faqItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      await faqItem.click()
      await page.waitForTimeout(500)
      await shot(page, '24-help-faq-expanded')
    }
    console.log('  -> FAQ 페이지')

    // ================================================================
    // 12. 사용자 검색 (Document Search)
    // ================================================================
    console.log('\n[12] 문서 검색 (유저)')
    await page.goto('/search')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '25-user-search')

    const userSearchInput = page.locator('input[placeholder*="search" i]').first()
    await expect(userSearchInput).toBeVisible({ timeout: 10000 })

    // All 모드 검색
    await userSearchInput.click()
    await userSearchInput.fill('DocUtil main features')
    await page.waitForTimeout(500)
    await userSearchInput.press('Enter')
    await page.waitForTimeout(5000)
    await shot(page, '26-search-all-results')
    console.log('  -> All 모드 검색')

    // Q&A 모드
    const qaTab = page.locator('button:has-text("Q&A")').first()
    if (await qaTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await qaTab.click()
      await page.waitForTimeout(500)
      await userSearchInput.clear()
      await userSearchInput.fill('What is the tech stack?')
      await userSearchInput.press('Enter')
      await page.waitForTimeout(5000)
      await shot(page, '27-search-qa-results')
      console.log('  -> Q&A 모드 검색')
    }

    // Keyword 모드
    const kwTab = page.locator('button:has-text("Keyword")').first()
    if (await kwTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await kwTab.click()
      await page.waitForTimeout(500)
      await userSearchInput.clear()
      await userSearchInput.fill('FastAPI PostgreSQL')
      await userSearchInput.press('Enter')
      await page.waitForTimeout(3000)
      await shot(page, '28-search-keyword-results')
      console.log('  -> Keyword 모드 검색')
    }

    // ================================================================
    // 13. 채팅 (Chatbot)
    // ================================================================
    console.log('\n[13] AI 채팅')
    await page.goto('/chat')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(3000)
    await shot(page, '29-chat-page')

    // 채팅 API 확인
    const token = await page.evaluate(() => {
      try {
        const store = JSON.parse(localStorage.getItem('auth-storage') || '{}')
        return store?.state?.accessToken || ''
      } catch { return '' }
    })

    const chatApiOk = await page.request.get('/api/v1/chat/sessions', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.status() < 500).catch(() => false)

    if (chatApiOk) {
      // New Chat 클릭
      const newChatBtn = page.locator('button:has-text("New Chat")')
      if (await newChatBtn.first().isVisible({ timeout: 10000 }).catch(() => false)) {
        await newChatBtn.first().click()
        await page.waitForTimeout(1500)

        // 문서 선택 모달
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible({ timeout: 5000 }).catch(() => false)) {
          await shot(page, '30-chat-scope-modal')

          // Confirm Selection 클릭
          const confirmBtn = modal.locator('button:has-text("Confirm"), button:has-text("확인")')
          if (await confirmBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
            await confirmBtn.first().click()
            await page.waitForTimeout(3000)
          } else {
            await page.keyboard.press('Escape')
            await page.waitForTimeout(1000)
          }
        }

        await shot(page, '31-chat-session')

        // 메시지 입력
        const msgInput = page.locator('textarea[placeholder*="message" i], textarea[placeholder*="메시지"]')
        if (await msgInput.isVisible({ timeout: 10000 }).catch(() => false)) {
          // 첫 번째 메시지
          await msgInput.click()
          await msgInput.fill('What are the main features of this document system?')
          await shot(page, '32-chat-message-typed')

          // 전송
          const sendBtn = page.locator('button').filter({ has: page.locator('svg') }).last()
          await sendBtn.click()
          console.log('  -> 메시지 전송')

          // 응답 대기
          await page.waitForTimeout(10000)
          await shot(page, '33-chat-response')

          // 두 번째 메시지
          await msgInput.click()
          await msgInput.fill('Tell me about the tech stack in detail')
          await sendBtn.click()
          await page.waitForTimeout(10000)
          await shot(page, '34-chat-followup')
          console.log('  -> 후속 질문 전송')
        } else {
          console.log('  -> 메시지 입력란 미표시')
        }
      }
    } else {
      console.log('  -> 채팅 API 에러 (스킵)')
      await shot(page, '30-chat-api-error')
    }

    // ================================================================
    // 14. 리포트 페이지
    // ================================================================
    console.log('\n[14] 리포트')
    await page.goto('/reports')
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(2000)
    await shot(page, '35-reports')
    console.log('  -> 리포트 페이지')

    // ================================================================
    // 15. 사이드바 네비게이션 테스트
    // ================================================================
    console.log('\n[15] 사이드바 접기/펼치기')
    const collapseBtn = page.locator('button:has-text("접기"), button[aria-label*="collapse" i]').first()
    if (await collapseBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await collapseBtn.click()
      await page.waitForTimeout(1000)
      await shot(page, '36-sidebar-collapsed')
      console.log('  -> 사이드바 접기')

      // 다시 펼치기
      const expandBtn = page.locator('button[aria-label*="expand" i], button:has(svg[class*="chevron"])').first()
      if (await expandBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await expandBtn.click()
        await page.waitForTimeout(1000)
        await shot(page, '37-sidebar-expanded')
      }
    }

    // ================================================================
    // 16. 로그아웃
    // ================================================================
    console.log('\n[16] 로그아웃')
    // 헤더의 로그아웃 버튼 또는 유저 메뉴
    const logoutBtn = page.locator('button[aria-label*="logout" i], button:has-text("로그아웃")')
    if (await logoutBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
      await logoutBtn.first().click()
      await page.waitForTimeout(2000)
    } else {
      // 로그아웃 아이콘 버튼 (화살표)
      const exitBtn = page.locator('header button').last()
      if (await exitBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await exitBtn.click()
        await page.waitForTimeout(2000)
      }
    }
    await shot(page, '38-after-logout')
    console.log('  -> 로그아웃')

    // ================================================================
    console.log('\n==========================================')
    console.log('  전체 기능 테스트 완료!')
    console.log(`  스크린샷: ${SCREENSHOT_DIR}`)
    console.log('==========================================\n')

  } finally {
    // 테스트 파일 정리
    for (const f of testFiles) {
      if (fs.existsSync(f)) fs.unlinkSync(f)
    }
    const tmpDir = path.join(process.cwd(), '.playwright-tmp')
    if (fs.existsSync(tmpDir)) fs.rmSync(tmpDir, { recursive: true, force: true })
  }
})
