import psycopg2

# DB connection
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="2012"
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SET search_path TO idino_career, public;")

print("=" * 70)
print("1. CURRENT DEPARTMENTS")
print("=" * 70)
cur.execute("""
    SELECT d.department_cd, d.department_nm, c.college_nm
    FROM tb_department d
    LEFT JOIN tb_college c ON d.college_cd = c.college_cd
    ORDER BY c.college_nm, d.department_nm
""")
for row in cur.fetchall():
    college = row[2] if row[2] else 'N/A'
    print(f"  [{row[0]}] {row[1]} ({college})")

print("\n" + "=" * 70)
print("2. CURRENT SKILLS")
print("=" * 70)
cur.execute("SELECT skill_cd, skill_nm, category FROM tb_skill ORDER BY category, skill_cd")
for row in cur.fetchall():
    print(f"  [{row[2]}] {row[0]}: {row[1]}")

print("\n" + "=" * 70)
print("3. STUDENTS WITHOUT SKILLS (2023-2025)")
print("=" * 70)
cur.execute("""
    SELECT s.admission_year, COUNT(DISTINCT s.student_id) as cnt
    FROM tb_student s
    LEFT JOIN tb_student_skill ss ON s.student_id = ss.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
    AND ss.skill_cd IS NULL
    GROUP BY s.admission_year
    ORDER BY s.admission_year
""")
total_no_skills = 0
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} students without skills")
    total_no_skills += row[1]
print(f"  Total: {total_no_skills}")

print("\n" + "=" * 70)
print("4. STUDENTS BY DEPARTMENT (sample - 2023-2025 without skills)")
print("=" * 70)
cur.execute("""
    SELECT d.department_nm, COUNT(DISTINCT s.student_id) as cnt
    FROM tb_student s
    JOIN tb_department d ON s.department_cd = d.department_cd
    LEFT JOIN tb_student_skill ss ON s.student_id = ss.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
    AND ss.skill_cd IS NULL
    GROUP BY d.department_nm
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.close()
conn.close()
