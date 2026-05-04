"""Test student API directly"""
import asyncio
import sys
sys.path.insert(0, r'E:\workspace\idino_career\services\student-service')

from app.database import AsyncSessionLocal
from sqlalchemy import text

async def test_query():
    async with AsyncSessionLocal() as session:
        # Test simple query
        result = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'idino_career' AND table_name = 'tb_department' ORDER BY ordinal_position"))
        columns = [row[0] for row in result.fetchall()]
        print("TB_DEPARTMENT columns via SQLAlchemy:")
        for col in columns:
            print(f"  {col}")

        print("\n" + "=" * 60)
        print("Testing student query...")

        # Try to query student
        result = await session.execute(text("""
            SELECT s.student_id, s.student_nm, s.department_cd
            FROM idino_career.tb_student s
            WHERE s.student_id = '2021010001'
        """))
        student = result.fetchone()
        if student:
            print(f"Found student: {student[0]} - {student[1]} (dept: {student[2]})")
        else:
            print("Student not found!")

if __name__ == "__main__":
    asyncio.run(test_query())
