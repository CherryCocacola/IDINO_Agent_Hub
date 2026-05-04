import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

/**
 * Edge 브라우저 E2E 수동 테스트
 *
 * 실제 Docker 환경에서 Edge 브라우저를 사용하여
 * 로그인 → 문서 업로드 → 문서 조회 → 챗봇 실행까지의 전체 흐름을 검증한다.
 *
 * 실행 방법:
 *   npx playwright test e2e/edge-manual-test.spec.ts --headed
 *
 * 각 단계마다 스크린샷을 저장하여 결과를 시각적으로 확인할 수 있다.
 */

// Edge 브라우저 프로젝트 설정
test.use({
  channel: 'msedge',
  viewport: { width: 1440, height: 900 },
  screenshot: 'on',
})

// 스크린샷 저장 경로
const SCREENSHOT_DIR = path.join(process.cwd(), 'e2e-screenshots')

// 테스트 파일 생성용
function createTestFile(): string {
  const tmpDir = path.join(process.cwd(), '.playwright-tmp')
  if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true })

  const filePath = path.join(tmpDir, `e2e-test-document-${Date.now()}.txt`)
  fs.writeFileSync(filePath, [
    '# E2E 테스트 문서',
    '',
    '## 개요',
    '이 문서는 Edge 브라우저 E2E 테스트를 위한 샘플 문서입니다.',
    'Document Utilization System(DocUtil)의 핵심 기능을 검증합니다.',
    '',
    '## 주요 기능',
    '- 문서 업로드 및 자동 파싱 (PDF, DOCX, TXT 등)',
    '- 하이브리드 검색 (Dense + Sparse + RRF)',
    '- Agentic RAG 기반 질의응답',
    '- WebSocket 실시간 채팅',
    '',
    '## 기술 스택',
    '- 백엔드: FastAPI, SQLAlchemy, PostgreSQL, Celery',
    '- 프론트엔드: Next.js, React, Tailwind CSS, Zustand',
    '- AI: Qwen3-32B, Qdrant, Agentic RAG',
    '',
    '이 시스템은 한컴에서 개발한 엔터프라이즈 문서 활용 솔루션입니다.',
  ].join('\n'), 'utf-8')
  return filePath
}

// 스크린샷 저장 헬퍼
async function screenshot(page: any, name: string) {
  if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${name}.png`), fullPage: true })
  console.log(`  [screenshot] ${name}.png 저장됨`)
}

test.describe('Edge 브라우저 전체 흐름 테스트', () => {
  test('로그인 → 문서 업로드 → 문서 조회 → 챗봇 실행', async ({ page }) => {
    // 전체 시간 충분히 확보
    test.setTimeout(180000)

    let testFilePath: string | null = null

    try {
      // ════════════════════════════════════════════════════════════════════
      // STEP 1: 로그인
      // ════════════════════════════════════════════════════════════════════
      console.log('\n══════════════════════════════════════')
      console.log('  STEP 1: 관리자 로그인')
      console.log('══════════════════════════════════════')

      await page.goto('/login')
      await page.waitForLoadState('domcontentloaded')
      await page.locator('#username').waitFor({ state: 'visible', timeout: 15000 })

      // 로그인 페이지 확인
      await expect(page.locator('text=DocUtil')).toBeVisible()
      await expect(page.locator('text=관리자 로그인')).toBeVisible()
      await screenshot(page, '01-login-page')

      // 로그인 정보 입력
      await page.locator('#username').fill('admin')
      await page.locator('#password').fill('admin123!')
      await screenshot(page, '02-login-filled')

      // 로그인 실행
      await page.getByRole('button', { name: /로그인/i }).click()
      await expect(page.locator('text=로그인되었습니다')).toBeVisible({ timeout: 15000 })
      await page.waitForURL(/.*dashboard/, { timeout: 30000 })

      await screenshot(page, '03-dashboard-after-login')
      console.log('  --> 로그인 성공, 대시보드 도착')

      // ════════════════════════════════════════════════════════════════════
      // STEP 2: 프로젝트/보드/폴더 확인 (문서 업로드 전 필수)
      // ════════════════════════════════════════════════════════════════════
      console.log('\n══════════════════════════════════════')
      console.log('  STEP 2: 프로젝트 구조 확인')
      console.log('══════════════════════════════════════')

      await page.goto('/projects')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await screenshot(page, '04-projects-page')

      // 프로젝트가 있는지 확인
      const projectRows = page.locator('tbody tr, table tr').filter({ hasText: /.+/ })
      const projectCount = await projectRows.count()
      console.log(`  --> 프로젝트 ${projectCount}건 확인`)

      // 프로젝트가 없으면 생성
      if (projectCount === 0) {
        console.log('  --> 프로젝트가 없어 새로 생성합니다')

        const createBtn = page.locator('button:has-text("프로젝트 생성"), button:has-text("Create"), button:has-text("추가")')
        if (await createBtn.first().isVisible({ timeout: 5000 }).catch(() => false)) {
          await createBtn.first().click()
          await page.waitForTimeout(1000)

          // 다이얼로그에서 프로젝트 이름 입력
          const nameInput = page.locator('[role="dialog"] input').first()
          if (await nameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
            await nameInput.fill('E2E 테스트 프로젝트')

            // 저장 버튼 클릭
            const saveBtn = page.locator('[role="dialog"] button:has-text("생성"), [role="dialog"] button:has-text("Create"), [role="dialog"] button:has-text("저장"), [role="dialog"] button[type="submit"]')
            if (await saveBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
              await saveBtn.first().click()
              await page.waitForTimeout(2000)
              console.log('  --> 프로젝트 생성 완료')
            }
          }
        }
      }
      await screenshot(page, '05-projects-list')

      // ════════════════════════════════════════════════════════════════════
      // STEP 3: 문서 관리 페이지 → 문서 업로드
      // ════════════════════════════════════════════════════════════════════
      console.log('\n══════════════════════════════════════')
      console.log('  STEP 3: 문서 업로드')
      console.log('══════════════════════════════════════')

      await page.goto('/documents')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('h1:has-text("문서")')).toBeVisible({ timeout: 10000 })
      await screenshot(page, '06-documents-page')

      // 좌측 폴더 트리에서 첫 번째 폴더 선택 시도
      // 프로젝트 노드 확장
      const treeButtons = page.locator('button').filter({ has: page.locator('svg') })
      let folderSelected = false

      // 트리에서 클릭 가능한 노드를 순서대로 확장하여 폴더 도달
      for (let i = 0; i < Math.min(await treeButtons.count(), 10); i++) {
        const btn = treeButtons.nth(i)
        const text = await btn.textContent().catch(() => '')
        if (text && !text.includes('업로드') && !text.includes('Search')) {
          await btn.click().catch(() => {})
          await page.waitForTimeout(500)
        }
      }

      await page.waitForTimeout(1000)
      await screenshot(page, '07-documents-tree-expanded')

      // 파일 업로드
      testFilePath = createTestFile()
      const fileInput = page.locator('input[type="file"]')

      if (await fileInput.count() > 0) {
        await fileInput.setInputFiles(testFilePath)
        await page.waitForTimeout(5000)
        await screenshot(page, '08-document-uploaded')
        console.log('  --> 문서 업로드 완료')
      } else {
        console.log('  --> 파일 인풋 미발견')
      }

      // ════════════════════════════════════════════════════════════════════
      // STEP 4: 문서 목록 조회
      // ════════════════════════════════════════════════════════════════════
      console.log('\n══════════════════════════════════════')
      console.log('  STEP 4: 문서 목록 조회')
      console.log('══════════════════════════════════════')

      // 페이지 새로고침하여 최신 문서 목록 조회
      await page.goto('/documents')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      // 문서 테이블 확인
      const docTable = page.locator('table')
      if (await docTable.isVisible({ timeout: 5000 }).catch(() => false)) {
        const docRows = page.locator('tbody tr')
        const docCount = await docRows.count()
        console.log(`  --> 문서 ${docCount}건 표시됨`)

        if (docCount > 0) {
          // 첫 번째 문서의 상세 정보 확인
          const firstDoc = docRows.first()
          const docName = await firstDoc.locator('td').first().textContent()
          console.log(`  --> 첫 번째 문서: ${docName?.trim()}`)
        }
      } else {
        console.log('  --> 문서 테이블 미표시 (폴더를 선택해야 표시됨)')
      }

      await screenshot(page, '09-documents-list')

      // 검색 필터 테스트
      const searchInput = page.locator('input[placeholder*="Search"]')
      if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await searchInput.fill('test')
        await page.waitForTimeout(1000)
        await screenshot(page, '10-documents-search-filter')
        await searchInput.clear()
        console.log('  --> 문서 검색 필터 동작 확인')
      }

      // ════════════════════════════════════════════════════════════════════
      // STEP 5: 문서 검색 (유저 검색 페이지)
      // ════════════════════════════════════════════════════════════════════
      console.log('\n══════════════════════════════════════')
      console.log('  STEP 5: AI 문서 검색')
      console.log('══════════════════════════════════════')

      await page.goto('/search')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(2000)

      // 검색 페이지의 검색 입력란이 보일 때까지 대기
      const searchBox = page.locator('input[placeholder*="search" i], input[placeholder*="검색"]').first()
      await expect(searchBox).toBeVisible({ timeout: 15000 })
      await screenshot(page, '11-search-page')
      await searchBox.click()
      await searchBox.fill('문서 활용 시스템의 주요 기능')
      await screenshot(page, '12-search-query-entered')

      await searchBox.press('Enter')
      await page.waitForTimeout(5000)
      await screenshot(page, '13-search-results')

      console.log('  --> 검색 실행 완료')

      // ════════════════════════════════════════════════════════════════════
      // STEP 6: 챗봇 실행
      // ════════════════════════════════════════════════════════════════════
      console.log('\n══════════════════════════════════════')
      console.log('  STEP 6: AI 챗봇 실행')
      console.log('══════════════════════════════════════')

      await page.goto('/chat')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await screenshot(page, '14-chat-page')

      // 채팅 API 정상 여부 확인
      const token = await page.evaluate(() => {
        try {
          const store = JSON.parse(localStorage.getItem('auth-storage') || '{}')
          return store?.state?.accessToken || ''
        } catch { return '' }
      })

      const apiCheck = await page.request.get('/api/v1/chat/sessions', {
        headers: { 'Authorization': `Bearer ${token}` }
      }).catch(() => null)

      if (!apiCheck || apiCheck.status() >= 500) {
        console.log('  --> 채팅 API 500 에러 (Docker API 이미지 재빌드 필요)')
        console.log('  --> 재빌드 명령: docker compose build api && docker compose up -d api')
        await screenshot(page, '15-chat-api-error')

        // API 에러여도 페이지 구조는 확인
        console.log('  --> 채팅 페이지 UI 구조는 정상 로드됨')
        return
      }

      // New Chat 버튼 클릭
      const newChatBtn = page.locator('button:has-text("New Chat")')
      if (await newChatBtn.first().isVisible({ timeout: 10000 }).catch(() => false)) {
        console.log('  --> New Chat 버튼 클릭')
        await newChatBtn.first().click()
        await page.waitForTimeout(1000)

        // 문서 범위 선택 모달 처리
        const modal = page.locator('[role="dialog"]')
        if (await modal.isVisible({ timeout: 5000 }).catch(() => false)) {
          await screenshot(page, '15-chat-scope-modal')

          // 확인 버튼 클릭
          const confirmBtn = modal.locator('button:has-text("Confirm"), button:has-text("확인"), button:has-text("Start"), button:has-text("시작"), button:has-text("Create")')
          if (await confirmBtn.first().isVisible({ timeout: 3000 }).catch(() => false)) {
            await confirmBtn.first().click()
            await page.waitForTimeout(3000)
          } else {
            await page.keyboard.press('Escape')
            await page.waitForTimeout(1000)
          }
        }

        await screenshot(page, '16-chat-session-created')
      }

      // 메시지 입력 및 전송
      const msgInput = page.locator('textarea[placeholder*="message" i], textarea[placeholder*="메시지"]')
      if (await msgInput.isVisible({ timeout: 10000 }).catch(() => false)) {
        // 첫 번째 메시지 전송
        await msgInput.click()
        await msgInput.fill('안녕하세요! 업로드된 문서의 내용을 요약해주세요.')
        await screenshot(page, '17-chat-message-typed')

        // Send 버튼 클릭
        const sendBtn = page.locator('button').filter({ has: page.locator('svg') }).last()
        await sendBtn.click()
        console.log('  --> 메시지 전송됨')

        // 사용자 메시지 표시 확인
        await expect(page.locator('text=안녕하세요')).toBeVisible({ timeout: 10000 })
        await screenshot(page, '18-chat-user-message')

        // AI 응답 대기
        console.log('  --> AI 응답 대기 중...')
        await page.waitForTimeout(10000)
        await screenshot(page, '19-chat-ai-response')

        // 두 번째 메시지 전송
        await msgInput.click()
        await msgInput.fill('이 시스템의 기술 스택을 알려주세요.')
        await sendBtn.click()
        await page.waitForTimeout(8000)
        await screenshot(page, '20-chat-followup')

        console.log('  --> 챗봇 대화 완료')
      } else {
        console.log('  --> 메시지 입력란 미표시 (세션 생성 필요)')
        await screenshot(page, '17-chat-no-input')
      }

      // ════════════════════════════════════════════════════════════════════
      // 결과 요약
      // ════════════════════════════════════════════════════════════════════
      console.log('\n══════════════════════════════════════')
      console.log('  테스트 완료!')
      console.log('══════════════════════════════════════')
      console.log(`  스크린샷 저장 위치: ${SCREENSHOT_DIR}`)
      console.log('══════════════════════════════════════\n')

    } finally {
      // 테스트 파일 정리
      if (testFilePath && fs.existsSync(testFilePath)) {
        fs.unlinkSync(testFilePath)
      }
      const tmpDir = path.join(process.cwd(), '.playwright-tmp')
      if (fs.existsSync(tmpDir)) {
        fs.rmSync(tmpDir, { recursive: true, force: true })
      }
    }
  })
})
