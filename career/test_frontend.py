from playwright.sync_api import sync_playwright
import json

def test_idino_career():
    results = {
        "login_page_loaded": False,
        "login_successful": False,
        "dashboard_loaded": False,
        "student_data_displayed": False,
        "errors": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Step 1: Navigate to login page
            print("Step 1: Navigating to http://localhost:3000...")
            page.goto('http://localhost:3000', timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            # Take screenshot of initial page
            page.screenshot(path='E:/workspace/idino_career/screenshots/01_initial_page.png', full_page=True)
            print("Screenshot saved: 01_initial_page.png")

            # Check current URL - might redirect to login
            current_url = page.url
            print(f"Current URL: {current_url}")

            # Step 2: Check if on login page or need to redirect
            if '/login' in current_url or page.locator('input[type="text"], input[name="username"], input[id="username"]').count() > 0:
                results["login_page_loaded"] = True
                print("Login page detected!")
                page.screenshot(path='E:/workspace/idino_career/screenshots/02_login_page.png', full_page=True)

                # Find login form elements
                username_input = page.locator('input[type="text"], input[name="username"], input[id="username"], input[placeholder*="ID"]').first
                password_input = page.locator('input[type="password"]').first

                # Fill in credentials
                print("Filling in credentials: 20002268 / 1234")
                username_input.fill('20002268')
                password_input.fill('1234')

                page.screenshot(path='E:/workspace/idino_career/screenshots/03_credentials_filled.png', full_page=True)

                # Find and click login button
                login_button = page.locator('button[type="submit"], button:has-text("Login")').first
                print("Clicking login button...")
                login_button.click()

                # Wait for navigation/response
                page.wait_for_load_state('networkidle', timeout=30000)
                page.wait_for_timeout(3000)  # Extra wait for any redirects

            # Step 3: Check if login was successful (should be on dashboard now)
            current_url = page.url
            print(f"After login URL: {current_url}")
            page.screenshot(path='E:/workspace/idino_career/screenshots/04_after_login.png', full_page=True)

            # Check if redirected back to login (failed) or on dashboard
            if '/login' not in current_url:
                results["login_successful"] = True
                print("Login successful!")

                # Step 4: Check dashboard content
                page.wait_for_timeout(3000)  # Wait for data to load
                page.screenshot(path='E:/workspace/idino_career/screenshots/05_dashboard.png', full_page=True)

                # Look for dashboard elements
                page_content = page.content()

                # Check for student info elements
                if 'Dashboard' in page_content or 'overview' in current_url.lower():
                    results["dashboard_loaded"] = True
                    print("Dashboard loaded!")

                # Check for student data (name, ID, sections)
                if '20002268' in page_content or 'student' in page_content.lower():
                    results["student_data_displayed"] = True
                    print("Student data appears to be displayed!")

                # Try scrolling and taking more screenshots
                page.evaluate('window.scrollBy(0, 500)')
                page.wait_for_timeout(1000)
                page.screenshot(path='E:/workspace/idino_career/screenshots/06_dashboard_scroll.png', full_page=True)

            else:
                results["errors"].append("Login failed - still on login page")
                print("Login failed - still on login page")

                # Check for error messages
                error_msg = page.locator('.error, .alert, [class*="error"], [class*="alert"]').all_text_contents()
                if error_msg:
                    results["errors"].append(f"Error messages: {error_msg}")
                    print(f"Error messages found: {error_msg}")

        except Exception as e:
            error_msg = f"Test error: {str(e)}"
            results["errors"].append(error_msg)
            print(error_msg)
            page.screenshot(path='E:/workspace/idino_career/screenshots/error_screenshot.png', full_page=True)

        finally:
            browser.close()

    # Print summary
    print("\n" + "="*50)
    print("TEST RESULTS SUMMARY")
    print("="*50)
    print(f"Login Page Loaded: {'PASS' if results['login_page_loaded'] else 'FAIL'}")
    print(f"Login Successful: {'PASS' if results['login_successful'] else 'FAIL'}")
    print(f"Dashboard Loaded: {'PASS' if results['dashboard_loaded'] else 'FAIL'}")
    print(f"Student Data Displayed: {'PASS' if results['student_data_displayed'] else 'FAIL'}")
    if results["errors"]:
        print(f"Errors: {results['errors']}")
    print("="*50)

    return results

if __name__ == "__main__":
    import os
    os.makedirs('E:/workspace/idino_career/screenshots', exist_ok=True)
    test_idino_career()
