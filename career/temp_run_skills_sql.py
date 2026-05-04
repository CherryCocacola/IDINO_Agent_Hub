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

# Read and execute SQL file
with open('database/17_seed_skills_extended.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    cur.execute(sql)
    print("SQL executed successfully!")
except Exception as e:
    print(f"Error: {e}")

# Check results
cur.execute("SET search_path TO idino_career, public;")

print("\n" + "=" * 60)
print("RESULTS AFTER SKILL INSERTION")
print("=" * 60)

cur.execute("SELECT COUNT(*) FROM tb_skill")
print(f"Total skills: {cur.fetchone()[0]}")

cur.execute("""
    SELECT category, COUNT(*)
    FROM tb_skill
    GROUP BY category
    ORDER BY category
""")
print("\nSkills by category:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("""
    SELECT COUNT(DISTINCT student_id)
    FROM tb_student_skill ss
    JOIN tb_student s ON ss.student_id = s.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
""")
print(f"\nStudents with skills (2023-2025): {cur.fetchone()[0]}")

cur.execute("""
    SELECT s.admission_year, COUNT(DISTINCT ss.student_id)
    FROM tb_student_skill ss
    JOIN tb_student s ON ss.student_id = s.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
    GROUP BY s.admission_year
    ORDER BY s.admission_year
""")
print("\nStudents with skills by admission year:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.execute("""
    SELECT COUNT(*)
    FROM tb_student s
    LEFT JOIN tb_student_skill ss ON s.student_id = ss.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
    AND ss.skill_cd IS NULL
""")
print(f"\nStudents still without skills (2023-2025): {cur.fetchone()[0]}")

cur.close()
conn.close()
