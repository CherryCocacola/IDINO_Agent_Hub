from playwright.sync_api import sync_playwright
import os

def test_student(page, student_id, student_nm):
    """Test a single student's data display"""
    student_results = {
        'student_id': student_id,
        'student_nm': student_nm,
        'login': False,
        'dashboard': False,
        'skills': False,
        'simulation': False,
        'passport': False,
        'coaching': False,
        'errors': []
    }

    try:
        # Login
        page.goto('http://localhost:3000/login', timeout=15000)
        page.wait_for_load_state('networkidle', timeout=15000)

        username_input = page.locator('input[type="text"]').first
        password_input = page.locator('input[type="password"]').first
        username_input.fill(student_id)
        password_input.fill('1234')
        page.locator('button[type="submit"]').first.click()
        page.wait_for_load_state('networkidle', timeout=15000)
        page.wait_for_timeout(2000)

        if '/login' not in page.url:
            student_results['login'] = True
        else:
            student_results['errors'].append('Login failed')
            return student_results

        # Dashboard check
        content = page.content()
        if 'Dashboard' in content or page.url == 'http://localhost:3000/' or page.url == 'http://localhost:3000':
            student_results['dashboard'] = True

        # Skills page
        page.goto('http://localhost:3000/skills', timeout=10000)
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(1000)
        if '/login' not in page.url:
            student_results['skills'] = True

        # Simulation page
        page.goto('http://localhost:3000/simulation', timeout=10000)
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(1000)
        if '/login' not in page.url:
            student_results['simulation'] = True

        # Passport page
        page.goto('http://localhost:3000/passport', timeout=10000)
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(1000)
        if '/login' not in page.url:
            student_results['passport'] = True

        # Coaching page
        page.goto('http://localhost:3000/coaching', timeout=10000)
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(1000)
        if '/login' not in page.url:
            student_results['coaching'] = True

    except Exception as e:
        student_results['errors'].append(str(e)[:100])

    return student_results

def main():
    # Students with accounts and complete data
    students = [
        ('20001165', 'Lee**'),
        ('20001008', 'Kim**'),
        ('20001009', 'Kim**'),
        ('20001012', 'Kim**'),
        ('20001028', 'Noh**'),
        ('20001048', 'Seo**'),
        ('20001052', 'Son**'),
        ('20001082', 'Lee**'),
        ('20001091', 'Jang**'),
        ('20001117', 'Kong**'),
        ('20001120', 'Kwon**'),
        ('20001124', 'Kim**'),
        ('20001127', 'Kim**'),
        ('20001129', 'Kim**'),
        ('20001141', 'Nam**'),
        ('20001146', 'Park**'),
        ('20001150', 'Seo**'),
        ('20001151', 'Seo**'),
        ('20001156', 'Oh**'),
        ('20001157', 'Ok**'),
    ]

    os.makedirs('E:/workspace/idino_career/screenshots/students', exist_ok=True)

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, (student_id, student_nm) in enumerate(students):
            print(f"[{i+1}/{len(students)}] Testing student {student_id} ({student_nm})...")
            result = test_student(page, student_id, student_nm)
            results.append(result)

            # Take screenshot for first 5 students who login successfully
            if result['login'] and i < 5:
                try:
                    page.goto('http://localhost:3000', timeout=10000)
                    page.wait_for_load_state('networkidle', timeout=10000)
                    page.wait_for_timeout(2000)
                    page.screenshot(path=f'E:/workspace/idino_career/screenshots/students/{student_id}_dashboard.png', full_page=True)
                except:
                    pass

            # Status
            status = 'OK' if result['login'] else 'FAIL'
            pages_ok = sum([result['dashboard'], result['skills'], result['simulation'], result['passport'], result['coaching']])
            print(f"    Login: {status}, Pages: {pages_ok}/5")

        browser.close()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    login_ok = sum(1 for r in results if r['login'])
    print(f"Login Success: {login_ok}/{len(students)}")

    for page_type in ['dashboard', 'skills', 'simulation', 'passport', 'coaching']:
        ok_count = sum(1 for r in results if r[page_type])
        print(f"{page_type.capitalize()} Page: {ok_count}/{len(students)}")

    print("\nFailed Students:")
    for r in results:
        if not r['login']:
            print(f"  - {r['student_id']}: {r['errors']}")

    print("\nSuccessful Students:")
    for r in results:
        if r['login']:
            pages = sum([r['dashboard'], r['skills'], r['simulation'], r['passport'], r['coaching']])
            print(f"  - {r['student_id']} ({r['student_nm']}): {pages}/5 pages OK")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
