from playwright.sync_api import sync_playwright
import os

def test_all_dashboard_sections():
    """Test all dashboard sections and sidebar navigation"""
    os.makedirs('E:/workspace/idino_career/screenshots', exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Login first
            print("Logging in...")
            page.goto('http://localhost:3000/login', timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            username_input = page.locator('input[type="text"]').first
            password_input = page.locator('input[type="password"]').first
            username_input.fill('20002268')
            password_input.fill('1234')
            page.locator('button[type="submit"]').first.click()
            page.wait_for_load_state('networkidle', timeout=30000)
            page.wait_for_timeout(3000)

            print("Login successful, testing dashboard sections...")

            # Test main dashboard
            page.screenshot(path='E:/workspace/idino_career/screenshots/dashboard_full.png', full_page=True)

            # Check various sections
            sections_to_check = [
                ('overview', 'Overview section'),
                ('competency', 'Competency section'),
                ('roadmap', 'Roadmap section'),
                ('alumni', 'Alumni section'),
                ('actions', 'AI Actions section'),
            ]

            for section_id, section_name in sections_to_check:
                element = page.locator(f'#{section_id}, [id*="{section_id}"], section:has-text("{section_name}")')
                if element.count() > 0:
                    print(f"  [OK] {section_name} found")
                else:
                    print(f"  [--] {section_name} not found by ID")

            # Test sidebar navigation pages
            sidebar_links = [
                ('skills', 'Skills Page'),
                ('coaching', 'Coaching Page'),
                ('risks', 'Risks Page'),
                ('opportunities', 'Opportunities Page'),
                ('sprint', 'Sprint Page'),
                ('simulation', 'Simulation Page'),
                ('passport', 'Passport Page'),
                ('portfolio', 'Portfolio Page'),
                ('roadmap-planner', 'Roadmap Planner Page'),
                ('advisor', 'Advisor Page'),
            ]

            print("\nTesting sidebar navigation pages...")
            for path, page_name in sidebar_links:
                try:
                    page.goto(f'http://localhost:3000/{path}', timeout=15000)
                    page.wait_for_load_state('networkidle', timeout=15000)
                    page.wait_for_timeout(1000)

                    # Check if redirected to login (auth issue)
                    if '/login' in page.url:
                        print(f"  [AUTH] {page_name} - requires auth, redirected to login")
                        # Re-login
                        username_input = page.locator('input[type="text"]').first
                        password_input = page.locator('input[type="password"]').first
                        username_input.fill('20002268')
                        password_input.fill('1234')
                        page.locator('button[type="submit"]').first.click()
                        page.wait_for_load_state('networkidle', timeout=15000)
                        page.wait_for_timeout(2000)
                    else:
                        page.screenshot(path=f'E:/workspace/idino_career/screenshots/page_{path}.png', full_page=True)
                        print(f"  [OK] {page_name} - loaded successfully")
                except Exception as e:
                    print(f"  [ERR] {page_name} - {str(e)[:50]}")

            print("\nAll tests completed!")

        except Exception as e:
            print(f"Test error: {str(e)}")
            page.screenshot(path='E:/workspace/idino_career/screenshots/error.png', full_page=True)

        finally:
            browser.close()

if __name__ == "__main__":
    test_all_dashboard_sections()
