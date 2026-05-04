"""Reconnaissance script to understand the app structure"""
from playwright.sync_api import sync_playwright
import os

os.makedirs('E:/workspace/idino_career/test_screenshots', exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Go to homepage
    print("Navigating to homepage...")
    page.goto('http://localhost:3000')
    page.wait_for_load_state('networkidle')
    page.screenshot(path='E:/workspace/idino_career/test_screenshots/01_homepage.png', full_page=True)
    print(f"Current URL: {page.url}")

    # Check if redirected to login
    if 'login' in page.url.lower():
        print("Redirected to login page")
        page.screenshot(path='E:/workspace/idino_career/test_screenshots/02_login_page.png', full_page=True)

        # Find form elements
        print("\nLooking for form elements...")
        inputs = page.locator('input').all()
        for i, inp in enumerate(inputs):
            print(f"  Input {i}: type={inp.get_attribute('type')}, name={inp.get_attribute('name')}, id={inp.get_attribute('id')}")

        buttons = page.locator('button').all()
        for i, btn in enumerate(buttons):
            print(f"  Button {i}: text='{btn.inner_text()}', type={btn.get_attribute('type')}")

    browser.close()
    print("\nReconnaissance complete. Screenshots saved.")
