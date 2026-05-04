"""E2E Test Script for IDINO Career Application"""
from playwright.sync_api import sync_playwright
import os
import time
import json

# Test configuration
TEST_USERS = [
    '2020010000',
    '2020010020',
    '2020020025',
    '2020020045',
    '2020030050',
    '2020040075',
    '2020050000',
]

PASSWORD = '1234'
BASE_URL = 'http://localhost:3000'

# Menu pages to test
MENU_PAGES = [
    ('/', 'dashboard', 'Dashboard'),
    ('/skills', 'skills', 'Skills Management'),
    ('/coaching', 'coaching', 'AI Coaching'),
    ('/risks', 'risks', 'Risk Alerts'),
    ('/opportunities', 'opportunities', 'Opportunities'),
    ('/sprint', 'sprint', 'Sprint'),
    ('/simulation', 'simulation', 'Simulation'),
    ('/passport', 'passport', 'Skill Passport'),
    ('/portfolio', 'portfolio', 'Portfolio'),
    ('/roadmap-planner', 'roadmap', 'Roadmap Planner'),
]

def setup_dirs():
    os.makedirs('E:/workspace/idino_career/test_screenshots', exist_ok=True)
    os.makedirs('E:/workspace/idino_career/test_results', exist_ok=True)

def login(page, student_id, password):
    """Login to the application"""
    page.goto(f'{BASE_URL}/login')
    page.wait_for_load_state('networkidle')

    # Fill login form
    page.fill('#studentId', student_id)
    page.fill('#password', password)

    # Click login button
    page.click('button[type="submit"]')

    # Wait for redirect
    page.wait_for_load_state('networkidle')
    time.sleep(2)  # Extra wait for auth

    return page.url != f'{BASE_URL}/login'

def test_page(page, path, name, student_id, results):
    """Test a single page and record results"""
    result = {
        'path': path,
        'name': name,
        'student_id': student_id,
        'success': False,
        'has_data': False,
        'error': None,
    }

    try:
        print(f"    Testing {name} ({path})...")
        page.goto(f'{BASE_URL}{path}')
        page.wait_for_load_state('networkidle')
        time.sleep(1)

        # Take screenshot
        screenshot_name = f'{student_id}_{name.lower().replace(" ", "_")}.png'
        page.screenshot(
            path=f'E:/workspace/idino_career/test_screenshots/{screenshot_name}',
            full_page=True
        )

        # Check for error messages
        error_elements = page.locator('text=Error').count() + page.locator('text=오류').count()
        empty_elements = page.locator('text=데이터가 없습니다').count() + page.locator('text=No data').count()

        # Check for actual content - look for cards, lists, or data containers
        content_indicators = [
            'div[class*="card"]',
            'div[class*="Card"]',
            'table',
            'ul > li',
            '[data-testid]',
            '.bg-white',  # Common card background
        ]

        has_content = False
        for selector in content_indicators:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    has_content = True
                    break
            except:
                pass

        result['success'] = True
        result['has_data'] = has_content and error_elements == 0
        result['has_errors'] = error_elements > 0
        result['is_empty'] = empty_elements > 0

    except Exception as e:
        result['error'] = str(e)
        print(f"      ERROR: {e}")

    results.append(result)
    status = "OK" if result['success'] and result['has_data'] else "WARN" if result['success'] else "FAIL"
    print(f"      [{status}] {name}")
    return result

def run_tests():
    setup_dirs()
    all_results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for student_id in TEST_USERS:
            print(f"\n{'='*50}")
            print(f"Testing user: {student_id}")
            print('='*50)

            context = browser.new_context()
            page = context.new_page()

            user_results = []

            # Login
            print(f"  Logging in...")
            if not login(page, student_id, PASSWORD):
                print(f"  FAILED to login!")
                page.screenshot(path=f'E:/workspace/idino_career/test_screenshots/{student_id}_login_failed.png')
                context.close()
                all_results[student_id] = [{'error': 'Login failed'}]
                continue

            print(f"  Login successful!")

            # Test each page
            for path, slug, name in MENU_PAGES:
                test_page(page, path, name, student_id, user_results)

            all_results[student_id] = user_results
            context.close()

        browser.close()

    # Save results
    with open('E:/workspace/idino_career/test_results/e2e_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for student_id, results in all_results.items():
        success_count = sum(1 for r in results if r.get('success') and r.get('has_data'))
        total_count = len(results)
        print(f"\n{student_id}: {success_count}/{total_count} pages OK")

        for r in results:
            if not r.get('success') or not r.get('has_data'):
                status = "ERROR" if r.get('error') else "NO_DATA" if not r.get('has_data') else "FAIL"
                print(f"  - [{status}] {r.get('name', 'Unknown')}: {r.get('error', 'No data or errors on page')}")

    return all_results

if __name__ == '__main__':
    run_tests()
