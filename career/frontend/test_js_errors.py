"""
Test all pages of IDINO Career app for JavaScript errors.
Login with user 2020010000/1234 and verify each page loads without console errors.
"""
from playwright.sync_api import sync_playwright
import time

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Collect console errors
        errors = []

        def handle_console(msg):
            if msg.type == 'error':
                errors.append({
                    'page': page.url,
                    'message': msg.text
                })

        page.on('console', handle_console)

        # Login
        print("Logging in...")
        page.goto('http://localhost:3000/login')
        page.wait_for_load_state('networkidle')

        page.fill('input[name="student_id"]', '2020010000')
        page.fill('input[name="password"]', '1234')
        page.click('button[type="submit"]')

        # Wait for redirect to home page
        page.wait_for_url('http://localhost:3000/', timeout=10000)
        page.wait_for_load_state('networkidle')
        time.sleep(2)

        print(f"Login successful. Current URL: {page.url}")

        # Pages to test
        pages_to_test = [
            ('/', 'Home'),
            ('/skills', 'Skills'),
            ('/coaching', 'Coaching'),
            ('/roadmap-planner', 'Roadmap Planner'),
            ('/portfolio', 'Portfolio'),
            ('/passport', 'Passport'),
            ('/risks', 'Risks'),
            ('/opportunities', 'Opportunities'),
            ('/simulation', 'Simulation'),
            ('/sprint', 'Sprint'),
        ]

        results = []

        for path, name in pages_to_test:
            url = f'http://localhost:3000{path}'
            print(f"\nTesting {name} ({url})...")

            # Clear errors for this page
            page_errors_before = len(errors)

            try:
                page.goto(url)
                page.wait_for_load_state('networkidle')
                time.sleep(2)  # Wait for any async operations

                page_errors = [e for e in errors[page_errors_before:]]

                if page_errors:
                    results.append({
                        'page': name,
                        'url': url,
                        'status': 'ERROR',
                        'errors': page_errors
                    })
                    print(f"  ❌ {len(page_errors)} error(s) found")
                    for err in page_errors:
                        print(f"     - {err['message'][:100]}")
                else:
                    results.append({
                        'page': name,
                        'url': url,
                        'status': 'OK',
                        'errors': []
                    })
                    print(f"  ✅ No errors")

            except Exception as e:
                results.append({
                    'page': name,
                    'url': url,
                    'status': 'FAILED',
                    'errors': [{'message': str(e)}]
                })
                print(f"  ❌ Page load failed: {e}")

        browser.close()

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        ok_count = len([r for r in results if r['status'] == 'OK'])
        error_count = len([r for r in results if r['status'] == 'ERROR'])
        failed_count = len([r for r in results if r['status'] == 'FAILED'])

        print(f"✅ OK: {ok_count}")
        print(f"❌ Errors: {error_count}")
        print(f"💥 Failed: {failed_count}")

        if error_count > 0 or failed_count > 0:
            print("\nPages with issues:")
            for r in results:
                if r['status'] != 'OK':
                    print(f"  - {r['page']}: {r['status']}")
                    for err in r['errors']:
                        print(f"    Error: {err['message'][:150]}")
            return 1
        else:
            print("\nAll pages loaded successfully without JS errors!")
            return 0

if __name__ == '__main__':
    exit(main())
