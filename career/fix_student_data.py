"""Fix student 2021010001 data"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='postgres',
    user='postgres',
    password='2012',
    options='-c search_path=idino_career'
)
conn.autocommit = True
cur = conn.cursor()

print("=" * 80)
print("Fixing student 2021010001")
print("=" * 80)

# Check current state
cur.execute("""
    SELECT student_id, student_nm, department_cd, current_grade
    FROM tb_student WHERE student_id = '2021010001'
""")
before = cur.fetchone()
print(f"Before: {before}")

# Update department_cd to DEPT01 (Computer Science)
cur.execute("""
    UPDATE tb_student
    SET department_cd = 'DEPT01'
    WHERE student_id = '2021010001'
""")
print(f"Updated {cur.rowcount} row(s)")

# Verify
cur.execute("""
    SELECT s.student_id, s.student_nm, s.department_cd, d.department_nm, s.current_grade
    FROM tb_student s
    LEFT JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE s.student_id = '2021010001'
""")
after = cur.fetchone()
print(f"After: {after}")

print("\n" + "=" * 80)
print("Fix complete!")
print("=" * 80)

conn.close()
