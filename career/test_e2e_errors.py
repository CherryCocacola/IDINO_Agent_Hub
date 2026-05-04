"""E2E Test Script - Check for JavaScript/Console Errors"""
from playwright.sync_api import sync_playwright
import os
import time
import json

TEST_USERS = ['2020010000']
PASSWORD = '1234'
BASE_URL = 'http://localhost:3000'

MENU_PAGES = [
    ('/', 'dashboard', 'Dashboard'),
    ('/skills', 'skills', 'Skills'),
    ('/coaching', 'coaching', 'Coaching'),
    ('/risks', 'risks', 'Risks'),
    ('/opportunities', 'opportunities', 'Opportunities'),
    ('/sprint', 'sprint', 'Sprint'),
    ('/simulation', 'simulation', 'Simulation'),
    ('/passport', 'passport', 'Passport'),
    ('/portfolio', 'portfolio', 'Portfolio'),
    ('/roadmap-planner', 'roadmap', 'Roadmap'),
]

def run_error_check():
    os.makedirs('E:/workspace/idino_career/test_screenshots', exist_ok=True)

    all_errors = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for student_id in TEST_USERS:
            print(f"\n{'='*60}")
            print(f"Checking errors for user: {student_id}")
            print('='*60)

            context = browser.new_context()
            page = context.new_page()

            # Collect console messages
            console_errors = []
            page_errors = []

            page.on('console', lambda msg: console_errors.append({
                'type': msg.type,
                'text': msg.text,
                'location': str(msg.location) if msg.location else None
            }) if msg.type in ['error', 'warning'] else None)

            page.on('pageerror', lambda err: page_errors.append(str(err)))

            # Login
            print("  Logging in...")
            page.goto(f'{BASE_URL}/login')
            page.wait_for_load_state('networkidle')
            time.sleep(1)

            page.fill('#studentId', student_id)
            page.fill('#password', PASSWORD)
            page.click('button[type="submit"]')
            page.wait_for_load_state('networkidle')
            time.sleep(3)

            user_errors = {'console': [], 'page': []}

            # Test each page
            for path, slug, name in MENU_PAGES:
                print(f"\n  Testing {name} ({path})...")
                console_errors.clear()
                page_errors.clear()

                try:
                    page.goto(f'{BASE_URL}{path}', timeout=30000)
                    page.wait_for_load_state('networkidle', timeout=30000)
                    time.sleep(2)

                    # Take screenshot
                    page.screenshot(path=f'E:/workspace/idino_career/test_screenshots/{student_id}_{slug}_check.png', full_page=True)

                    if console_errors:
                        print(f"    Console errors/warnings: {len(console_errors)}")
                        for err in console_errors[:5]:  # Show first 5
                            print(f"      [{err['type']}] {err['text'][:100]}")
                        user_errors['console'].append({
                            'page': path,
                            'errors': console_errors.copy()
                        })
                    else:
                        print(f"    No console errors")

                    if page_errors:
                        print(f"    Page errors: {len(page_errors)}")
                        for err in page_errors[:3]:
                            print(f"      {err[:100]}")
                        user_errors['page'].append({
                            'page': path,
                            'errors': page_errors.copy()
                        })
                    else:
                        print(f"    No page errors")

                except Exception as e:
                    print(f"    EXCEPTION: {e}")
                    user_errors['page'].append({
                        'page': path,
                        'errors': [str(e)]
                    })

            all_errors[student_id] = user_errors
            context.close()

        browser.close()

    # Summary
    print("\n" + "="*60)
    print("ERROR SUMMARY")
    print("="*60)

    for student_id, errors in all_errors.items():
        console_count = sum(len(e['errors']) for e in errors['console'])
        page_count = sum(len(e['errors']) for e in errors['page'])
        print(f"\n{student_id}:")
        print(f"  Console errors/warnings: {console_count}")
        print(f"  Page errors: {page_count}")

        if errors['console']:
            print("  Pages with console issues:")
            for item in errors['console']:
                print(f"    - {item['page']}: {len(item['errors'])} issues")

    return all_errors

if __name__ == '__main__':
    run_error_check()
