from playwright.sync_api import sync_playwright
import os

def verify_data_display():
    """Verify that data is displayed correctly on key pages"""
    os.makedirs('E:/workspace/idino_career/screenshots', exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Login
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

            print("Login successful!")

            # Dashboard Overview
            print("\n1. Capturing Dashboard...")
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_dashboard.png', full_page=True)

            # Skills Page
            print("2. Capturing Skills page...")
            page.goto('http://localhost:3000/skills', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=15000)
            page.wait_for_timeout(2000)
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_skills.png', full_page=True)

            # Coaching Page
            print("3. Capturing Coaching page...")
            page.goto('http://localhost:3000/coaching', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=15000)
            page.wait_for_timeout(2000)
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_coaching.png', full_page=True)

            # Simulation Page
            print("4. Capturing Simulation page...")
            page.goto('http://localhost:3000/simulation', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=15000)
            page.wait_for_timeout(2000)
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_simulation.png', full_page=True)

            # Passport Page
            print("5. Capturing Passport page...")
            page.goto('http://localhost:3000/passport', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=15000)
            page.wait_for_timeout(2000)
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_passport.png', full_page=True)

            # Advisor Page
            print("6. Capturing Advisor page...")
            page.goto('http://localhost:3000/advisor', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=15000)
            page.wait_for_timeout(2000)
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_advisor.png', full_page=True)

            # Risks Page
            print("7. Capturing Risks page...")
            page.goto('http://localhost:3000/risks', timeout=15000)
            page.wait_for_load_state('networkidle', timeout=15000)
            page.wait_for_timeout(2000)
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_risks.png', full_page=True)

            print("\nAll screenshots captured!")
            print("Screenshots saved to: E:/workspace/idino_career/screenshots/")

        except Exception as e:
            print(f"Error: {str(e)}")
            page.screenshot(path='E:/workspace/idino_career/screenshots/verify_error.png', full_page=True)

        finally:
            browser.close()

if __name__ == "__main__":
    verify_data_display()
