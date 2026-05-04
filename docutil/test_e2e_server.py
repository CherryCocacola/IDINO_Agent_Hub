"""
서버(192.168.10.39) E2E 테스트 - Edge 브라우저 (headed 모드)
로그인 → 대시보드 → 문서 → 검색 → 챗봇 순서로 진행
"""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "http://192.168.10.39:8041"
SCREENSHOT_DIR = "D:/workspace/document_utilization/e2e_server_test"

import os
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="msedge",
            headless=False,
            slow_mo=800,
        )
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="ko-KR",
        )
        page = await context.new_page()

        try:
            # ===== 1. 로그인 페이지 =====
            print("[1/7] 로그인 페이지 접속...")
            await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/01_login_page.png")

            # ===== 2. 로그인 =====
            print("[2/7] admin 로그인...")
            username_input = page.locator('input[name="username"], input[type="text"]').first
            password_input = page.locator('input[name="password"], input[type="password"]').first
            await username_input.fill("admin")
            await password_input.fill("admin123!")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/02_login_filled.png")

            login_btn = page.locator('button[type="submit"]').first
            await login_btn.click()
            await page.wait_for_timeout(4000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/03_dashboard.png")
            print("  → 대시보드 진입 완료")

            # ===== 3. 문서 페이지 =====
            print("[3/7] 문서 페이지...")
            try:
                await page.locator('a[href*="documents"]').first.click(timeout=5000)
            except:
                await page.goto(f"{BASE_URL}/documents", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/04_documents.png")
            print("  → 문서 목록 확인")

            # ===== 4. 검색 페이지 =====
            print("[4/7] 검색 테스트...")
            # 사용자 사이드바의 "문서 검색" 클릭
            try:
                await page.locator('text=문서 검색').first.click(timeout=5000)
            except:
                await page.goto(f"{BASE_URL}/search", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(2000)

            # 검색어 입력
            search_input = page.locator('input[type="text"], input[type="search"]').first
            await search_input.fill("교육 사업 제안서")
            await page.wait_for_timeout(500)

            # 검색 실행
            try:
                await page.locator('button:has-text("검색")').first.click(timeout=3000)
            except:
                await search_input.press("Enter")
            await page.wait_for_timeout(5000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/05_search_results.png")
            print("  → 검색 결과 확인")

            # ===== 5. 챗봇 - 새 세션 생성 =====
            print("[5/7] 챗봇 - 새 채팅 세션 생성...")
            try:
                await page.locator('text=챗봇').first.click(timeout=5000)
            except:
                await page.goto(f"{BASE_URL}/chat", wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/06_chat_page.png")

            # "+ 새 채팅" 버튼 클릭
            new_chat = page.locator('button:has-text("새 채팅")').first
            await new_chat.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/07_chat_session_created.png")
            print("  → 새 채팅 세션 생성")

            # ===== 6. 챗봇 - 메시지 전송 =====
            print("[6/7] 챗봇 - 메시지 전송...")
            # textarea 또는 input 찾기
            chat_input = None
            for selector in ['textarea', 'input[placeholder]', 'div[contenteditable="true"]']:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=3000):
                        chat_input = el
                        break
                except:
                    continue

            if chat_input:
                await chat_input.fill("업로드된 문서 중 교육 관련 내용을 요약해줘")
                await page.wait_for_timeout(1000)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/08_chat_input.png")

                # 전송 버튼 클릭
                try:
                    send_btn = page.locator('button:has-text("전송")').first
                    await send_btn.click(timeout=3000)
                except:
                    try:
                        # 아이콘 전송 버튼 (SVG)
                        send_btn = page.locator('button[type="submit"]').first
                        await send_btn.click(timeout=3000)
                    except:
                        await chat_input.press("Enter")

                # AI 응답 대기
                print("  → AI 응답 대기 중 (최대 30초)...")
                await page.wait_for_timeout(20000)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/09_chat_response.png")
                print("  → 챗봇 응답 확인")
            else:
                print("  → 채팅 입력란을 찾지 못함")
                await page.screenshot(path=f"{SCREENSHOT_DIR}/08_chat_no_input.png")

            # ===== 7. 최종 =====
            print("[7/7] 테스트 완료!")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/10_final.png")

            print("\n화면을 확인하세요. 30초 후 브라우저가 닫힙니다...")
            await page.wait_for_timeout(30000)

        except Exception as e:
            print(f"에러: {e}")
            await page.screenshot(path=f"{SCREENSHOT_DIR}/error.png")
            await page.wait_for_timeout(10000)
        finally:
            await browser.close()

asyncio.run(run())
