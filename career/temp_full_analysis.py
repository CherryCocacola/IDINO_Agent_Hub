import psycopg2
import pandas as pd

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
print("1. STUDENT DATA BY ADMISSION YEAR (2023-2025)")
print("=" * 70)
cur.execute("""
    SELECT admission_year, COUNT(*) as cnt
    FROM tb_student
    WHERE admission_year IN (2023, 2024, 2025)
    GROUP BY admission_year
    ORDER BY admission_year
""")
total_students = 0
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} students")
    total_students += row[1]
print(f"  Total (2023-2025): {total_students}")

print("\n" + "=" * 70)
print("2. EXCEL ACHIEVEMENT SCHEMA")
print("=" * 70)
df = pd.read_excel('user_mig/exports/idino_table_columns.xlsx')
table_col = df.columns[0]  # 테이블명
col_name = df.columns[2]   # 컬럼명
col_desc = df.columns[3]   # 컬럼설명
data_type = df.columns[4]  # 데이터타입
default_val = df.columns[5] # 기본값

achievement_df = df[df[table_col].astype(str) == 'tb_achievement']
print(f"Excel columns for tb_achievement ({len(achievement_df)} columns):")
for _, row in achievement_df.iterrows():
    desc = str(row[col_desc]) if pd.notna(row[col_desc]) else ''
    dtype = str(row[data_type]) if pd.notna(row[data_type]) else ''
    print(f"  {row[col_name]}: {dtype} - {desc}")

print("\n" + "=" * 70)
print("3. DB ACHIEVEMENT SCHEMA")
print("=" * 70)
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'idino_career' AND table_name = 'tb_achievement'
    ORDER BY ordinal_position
""")
db_cols = cur.fetchall()
print(f"DB columns for tb_achievement ({len(db_cols)} columns):")
for row in db_cols:
    print(f"  {row[0]}: {row[1]} ({row[2]})")

print("\n" + "=" * 70)
print("4. CURRENT SKILLS")
print("=" * 70)
cur.execute("SELECT skill_cd, skill_nm, category FROM tb_skill ORDER BY category, skill_cd")
skills = cur.fetchall()
print(f"Total skills: {len(skills)}")
for row in skills:
    print(f"  [{row[2]}] {row[0]}: {row[1]}")

print("\n" + "=" * 70)
print("5. STUDENT-SKILL LINKS (sample by admission year)")
print("=" * 70)
cur.execute("""
    SELECT s.admission_year, COUNT(DISTINCT ss.student_id) as students_with_skills
    FROM tb_student_skill ss
    JOIN tb_student s ON ss.student_id = s.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
    GROUP BY s.admission_year
    ORDER BY s.admission_year
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} students with skills")

print("\n" + "=" * 70)
print("6. PORTFOLIO BY DEPARTMENT (2023-2025)")
print("=" * 70)
cur.execute("""
    SELECT d.department_nm, COUNT(p.portfolio_id) as portfolio_count
    FROM tb_portfolio p
    JOIN tb_student s ON p.student_id = s.student_id
    JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE s.admission_year IN (2023, 2024, 2025)
    GROUP BY d.department_nm
    ORDER BY portfolio_count DESC
    LIMIT 15
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n" + "=" * 70)
print("7. STUDENTS WITHOUT PORTFOLIO (2023-2025)")
print("=" * 70)
cur.execute("""
    SELECT COUNT(DISTINCT s.student_id)
    FROM tb_student s
    LEFT JOIN tb_portfolio p ON s.student_id = p.student_id
    WHERE s.admission_year IN (2023, 2024, 2025)
    AND p.portfolio_id IS NULL
""")
print(f"  Students without portfolio: {cur.fetchone()[0]}")

cur.close()
conn.close()
