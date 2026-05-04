"""
Quick Sample Test - Tests 30 random students (10 per year)
Use this to validate before running full test
Uses psycopg v3 for Windows compatibility
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import psycopg
from playwright.async_api import async_playwright
from datetime import datetime
import random

# Configuration
DB_DSN = "host=localhost port=5432 dbname=postgres user=postgres password=2012"
BASE_URL = "http://localhost:3000"
PASSWORD = "1234"
SAMPLE_SIZE = 10  # Students per year

def get_sample_students():
    """Fetch sample students from each admission year"""
    conn = psycopg.connect(DB_DSN)
    cursor = conn.cursor()
    
    students = []
    for year in [2023, 2024, 2025]:
        query = f"""
            SELECT s.student_id, s.student_nm, s.admission_year, u.user_id, u.login_id, d.department_nm
            FROM idino_career.tb_student s
            JOIN idino_career.tb_user u ON s.student_id = u.student_id
            JOIN idino_career.tb_department d ON s.department_cd = d.department_cd
            WHERE s.admission_year = {year}
            ORDER BY RANDOM()
            LIMIT {SAMPLE_SIZE}
        """
        cursor.execute(query)
        for row in cursor.fetchall():
            students.append({
                "student_id": row[0],
                "student_nm": row[1],
                "admission_year": row[2],
                "user_id": row[3],
                "login_id": row[4],
                "department_nm": row[5]
            })
    
    cursor.close()
    conn.close()
    return students

async def test_student(page, student):
    """Test single student"""
    login_id = student["login_id"]
    year = student["admission_year"]
    dept = student["department_nm"]
    
    try:
        # Navigate to login
        await page.goto(f"{BASE_URL}/login", timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=10000)
        
        # Fill login form
        await page.fill('input[name="username"], input[type="text"]', login_id)
        await page.fill('input[name="password"], input[type="password"]', PASSWORD)
        
        # Click login
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)
        
        current_url = page.url
        if "/login" not in current_url or "/dashboard" in current_url:
            await page.wait_for_load_state("networkidle", timeout=10000)
            content = await page.content()
            
            has_name = student["student_nm"] in content
            has_competency = "역량" in content or "competency" in content.lower()
            
            result = "OK" if (has_name or has_competency) else "NO_DATA"
        else:
            result = "LOGIN_FAIL"
            
    except Exception as e:
        result = f"ERROR: {str(e)[:50]}"
    
    # Logout for next test
    try:
        await page.goto(f"{BASE_URL}/logout", timeout=5000)
    except:
        pass
    
    return {
        "login_id": login_id,
        "year": year,
        "dept": dept[:20] if dept else "N/A",
        "result": result
    }

async def main():
    print("="*70)
    print("SAMPLE STUDENT E2E TEST (30 students - 10 per year)")
    print("="*70)
    
    students = get_sample_students()
    print(f"Selected {len(students)} random students for testing\n")
    
    results = {"OK": 0, "NO_DATA": 0, "LOGIN_FAIL": 0, "ERROR": 0}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for i, student in enumerate(students, 1):
            result = await test_student(page, student)
            
            # Categorize result
            if result["result"] == "OK":
                results["OK"] += 1
                status = "OK"
            elif result["result"] == "NO_DATA":
                results["NO_DATA"] += 1
                status = "NO_DATA"
            elif result["result"] == "LOGIN_FAIL":
                results["LOGIN_FAIL"] += 1
                status = "FAIL"
            else:
                results["ERROR"] += 1
                status = "ERR"
            
            print(f"[{i:2d}/30] {status:7} | {result['year']} | {result['login_id']:12} | {result['dept']:20} | {result['result'][:30]}")
        
        await browser.close()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"OK (Login + Data visible): {results['OK']}")
    print(f"NO_DATA (Login OK, no data): {results['NO_DATA']}")
    print(f"LOGIN_FAIL: {results['LOGIN_FAIL']}")
    print(f"ERROR: {results['ERROR']}")
    print(f"\nSuccess Rate: {results['OK']/30*100:.1f}%")
    print("="*70)
    
    if results["OK"] >= 25:
        print("\nSample test PASSED - Ready for full test")
    else:
        print("\nSample test needs review before full test")

if __name__ == "__main__":
    asyncio.run(main())
