"""
Automated E2E Test for All Students (2023, 2024, 2025)
Tests login and dashboard functionality for 7,436 students
Uses psycopg v3 for Windows compatibility
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Force unbuffered output
class UnbufferedOutput:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def writelines(self, datas):
        self.stream.writelines(datas)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

sys.stdout = UnbufferedOutput(sys.stdout)

import psycopg
from playwright.async_api import async_playwright
from datetime import datetime
import json
import os

# Configuration
DB_DSN = "host=localhost port=5432 dbname=postgres user=postgres password=2012"
BASE_URL = "http://localhost:3000"
PASSWORD = "1234"
CONCURRENT_TESTS = 5  # Number of parallel browser instances
BATCH_SIZE = 100  # Students per batch for progress logging

class StudentTester:
    def __init__(self):
        self.results = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "errors": [],
            "by_year": {2023: {"success": 0, "failed": 0}, 2024: {"success": 0, "failed": 0}, 2025: {"success": 0, "failed": 0}}
        }
        self.start_time = None
        
    def get_all_students(self):
        """Fetch all students from database"""
        conn = psycopg.connect(DB_DSN)
        cursor = conn.cursor()
        
        query = """
            SELECT s.student_id, s.student_nm, s.admission_year, u.user_id, u.login_id
            FROM idino_career.tb_student s
            JOIN idino_career.tb_user u ON s.student_id = u.student_id
            WHERE s.admission_year IN (2023, 2024, 2025)
            ORDER BY s.admission_year, s.student_id
        """
        cursor.execute(query)
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [
            {
                "student_id": row[0],
                "student_nm": row[1],
                "admission_year": row[2],
                "user_id": row[3],
                "login_id": row[4]
            }
            for row in students
        ]
    
    async def test_student(self, browser, student, semaphore):
        """Test single student login and dashboard"""
        async with semaphore:
            context = await browser.new_context()
            page = await context.new_page()
            
            student_id = student["student_id"]
            login_id = student["login_id"]
            year = student["admission_year"]
            
            try:
                # Navigate to login
                await page.goto(f"{BASE_URL}/login", timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                # Fill login form
                await page.fill('input[name="username"], input[type="text"]', login_id)
                await page.fill('input[name="password"], input[type="password"]', PASSWORD)
                
                # Click login button
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(2000)
                
                # Check for successful login (dashboard or redirect)
                current_url = page.url
                
                if "/dashboard" in current_url or "/student" in current_url or current_url != f"{BASE_URL}/login":
                    # Verify dashboard content
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    
                    # Check for student name or competency data
                    content = await page.content()
                    
                    if student["student_nm"] in content or "역량" in content or "competency" in content.lower():
                        self.results["success"] += 1
                        self.results["by_year"][year]["success"] += 1
                        return True
                    else:
                        # Dashboard loaded but no data
                        self.results["failed"] += 1
                        self.results["by_year"][year]["failed"] += 1
                        self.results["errors"].append({
                            "student_id": student_id,
                            "login_id": login_id,
                            "year": year,
                            "error": "Dashboard loaded but no student data visible"
                        })
                        return False
                else:
                    # Login failed
                    self.results["failed"] += 1
                    self.results["by_year"][year]["failed"] += 1
                    self.results["errors"].append({
                        "student_id": student_id,
                        "login_id": login_id,
                        "year": year,
                        "error": "Login failed - stayed on login page"
                    })
                    return False
                    
            except Exception as e:
                self.results["failed"] += 1
                self.results["by_year"][year]["failed"] += 1
                self.results["errors"].append({
                    "student_id": student_id,
                    "login_id": login_id,
                    "year": year,
                    "error": str(e)[:200]
                })
                return False
            finally:
                await context.close()
    
    async def run_tests(self, students, max_concurrent=5):
        """Run tests for all students with concurrency control"""
        self.start_time = datetime.now()
        self.results["total"] = len(students)
        
        print(f"\n{'='*60}")
        print(f"Starting E2E Tests for {len(students)} Students")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Concurrent Tests: {max_concurrent}")
        print(f"{'='*60}\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            semaphore = asyncio.Semaphore(max_concurrent)
            
            # Process in batches for progress reporting
            for batch_start in range(0, len(students), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(students))
                batch = students[batch_start:batch_end]
                
                tasks = [self.test_student(browser, student, semaphore) for student in batch]
                await asyncio.gather(*tasks)
                
                # Progress report
                progress = (batch_end / len(students)) * 100
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = batch_end / elapsed if elapsed > 0 else 0
                eta = (len(students) - batch_end) / rate if rate > 0 else 0
                
                print(f"Progress: {batch_end}/{len(students)} ({progress:.1f}%) | "
                      f"Success: {self.results['success']} | Failed: {self.results['failed']} | "
                      f"Rate: {rate:.1f}/s | ETA: {eta/60:.1f}min")
            
            await browser.close()
        
        self.print_final_report()
        self.save_results()
    
    def print_final_report(self):
        """Print final test report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print("FINAL TEST REPORT")
        print(f"{'='*60}")
        print(f"Total Students Tested: {self.results['total']}")
        print(f"Successful: {self.results['success']} ({self.results['success']/self.results['total']*100:.2f}%)")
        print(f"Failed: {self.results['failed']} ({self.results['failed']/self.results['total']*100:.2f}%)")
        print(f"\nBy Admission Year:")
        for year in [2023, 2024, 2025]:
            yr = self.results["by_year"][year]
            total_yr = yr["success"] + yr["failed"]
            if total_yr > 0:
                print(f"  {year}: {yr['success']}/{total_yr} success ({yr['success']/total_yr*100:.2f}%)")
        print(f"\nDuration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"Rate: {self.results['total']/duration:.2f} students/second")
        
        if self.results["errors"]:
            print(f"\nFirst 10 Errors:")
            for err in self.results["errors"][:10]:
                print(f"  - {err['login_id']} ({err['year']}): {err['error'][:50]}...")
        print(f"{'='*60}\n")
    
    def save_results(self):
        """Save results to JSON file"""
        report_path = os.path.join(os.path.dirname(__file__), 
                                   f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": self.results["total"],
                    "success": self.results["success"],
                    "failed": self.results["failed"],
                    "success_rate": f"{self.results['success']/self.results['total']*100:.2f}%",
                    "by_year": self.results["by_year"],
                    "timestamp": datetime.now().isoformat()
                },
                "errors": self.results["errors"]
            }, f, ensure_ascii=False, indent=2)
        
        print(f"Results saved to: {report_path}")


async def main():
    tester = StudentTester()
    
    print("Fetching students from database...")
    students = tester.get_all_students()
    print(f"Found {len(students)} students to test")
    
    # Distribution by year
    by_year = {}
    for s in students:
        year = s["admission_year"]
        by_year[year] = by_year.get(year, 0) + 1
    print(f"Distribution: {by_year}")
    
    # Run tests
    await tester.run_tests(students, max_concurrent=CONCURRENT_TESTS)


if __name__ == "__main__":
    asyncio.run(main())
