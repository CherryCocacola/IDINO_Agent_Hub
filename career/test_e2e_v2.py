"""E2E Test Script for IDINO Career Application - V2"""
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
    time.sleep(1)

    # Fill login form
    page.fill('#studentId', student_id)
    page.fill('#password', password)

    # Click login button
    page.click('button[type="submit"]')

    # Wait for redirect - check for dashboard content
    try:
        page.wait_for_load_state('networkidle')
        time.sleep(3)  # Extra wait for auth and data loading

        # Check if we're on the dashboard by looking for dashboard elements
        current_url = page.url
        # Check if there's a sidebar or dashboard content
        has_sidebar = page.locator('aside').count() > 0
        has_dashboard_content = page.locator('text=대시보드').count() > 0 or page.locator('text=Dashboard').count() > 0

        return has_sidebar or has_dashboard_content or '/login' not in current_url
    except:
        return False

def test_page(page, path, name, student_id, results):
    """Test a single page and record results"""
    result = {
        'path': path,
        'name': name,
        'student_id': student_id,
        'success': False,
        'has_data': False,
        'error': None,
        'console_errors': [],
    }

    try:
        print(f"    Testing {name} ({path})...")

        # Navigate to page
        page.goto(f'{BASE_URL}{path}')
        page.wait_for_load_state('networkidle')
        time.sleep(2)  # Wait for data loading

        # Take screenshot
        screenshot_name = f'{student_id}_{name.lower().replace(" ", "_")}.png'
        page.screenshot(
            path=f'E:/workspace/idino_career/test_screenshots/{screenshot_name}',
            full_page=True
        )

        # Check page content
        page_content = page.content()

        # Check for error indicators
        has_error = 'Error' in page_content or 'error' in page_content.lower()
        has_loading = 'Loading' in page_content or '로딩' in page_content

        # Check for data - different indicators per page
        data_indicators = {
            '/': ['핵심역량', '이수학점', '역량 분석', '전체 개요'],
            '/skills': ['스킬', 'skill', '레벨', 'level', '현재', '목표'],
            '/coaching': ['코칭', '목표', 'goal', '세션'],
            '/risks': ['위험', '알림', 'alert', 'risk'],
            '/opportunities': ['기회', '인턴', '채용', 'opportunity'],
            '/sprint': ['스프린트', '목표', '진행', 'sprint'],
            '/simulation': ['시뮬레이션', '시나리오', 'scenario', 'what-if'],
            '/passport': ['패스포트', '뱃지', '스킬', 'passport', 'badge'],
            '/portfolio': ['포트폴리오', '프로젝트', 'portfolio', 'project'],
            '/roadmap-planner': ['로드맵', '계획', '마일스톤', 'roadmap'],
        }

        indicators = data_indicators.get(path, ['데이터', 'data'])
        has_content = any(ind.lower() in page_content.lower() for ind in indicators)

        result['success'] = True
        result['has_data'] = has_content
        result['has_loading'] = has_loading
        result['has_error'] = has_error

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

    total_tests = 0
    total_success = 0

    for student_id, results in all_results.items():
        success_count = sum(1 for r in results if r.get('success') and r.get('has_data'))
        total_count = len(results)
        total_tests += total_count
        total_success += success_count
        print(f"\n{student_id}: {success_count}/{total_count} pages OK")

        for r in results:
            if not r.get('success') or not r.get('has_data'):
                status = "ERROR" if r.get('error') else "NO_DATA" if not r.get('has_data') else "FAIL"
                print(f"  - [{status}] {r.get('name', 'Unknown')}: {r.get('error', 'Check screenshot')}")

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_success}/{total_tests} tests passed")
    print(f"{'='*60}")

    return all_results

if __name__ == '__main__':
    run_tests()
