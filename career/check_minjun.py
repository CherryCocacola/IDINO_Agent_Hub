import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='postgres',
    user='postgres',
    password='2012'
)
cur = conn.cursor()

print("=" * 80)
print("Finding Kim Minjun in database")
print("=" * 80)

# Search for any student with name containing "민준" or "minjun"
cur.execute("""
    SELECT student_id, student_nm, student_nm_en, department_cd, current_grade
    FROM idino_career.tb_student
    WHERE student_nm LIKE '%민준%'
       OR student_nm_en ILIKE '%minjun%'
       OR student_id = 'STU001'
       OR student_id = '2021010001'
""")
results = cur.fetchall()

if results:
    print("Found matching students:")
    for r in results:
        print(f"  student_id: {r[0]}")
        print(f"  student_nm: {r[1]}")
        print(f"  student_nm_en: {r[2]}")
        print(f"  department_cd: {r[3]}")
        print(f"  current_grade: {r[4]}")
        print("-" * 40)
else:
    print("No student named '민준' or 'minjun' found!")

print("\n" + "=" * 80)
print("Check if mock data student_id 'STU001' exists")
print("=" * 80)

cur.execute("""
    SELECT student_id, student_nm FROM idino_career.tb_student
    WHERE student_id = 'STU001'
""")
stu001 = cur.fetchone()
if stu001:
    print(f"STU001 exists: {stu001}")
else:
    print("STU001 does NOT exist in database!")

print("\n" + "=" * 80)
print("Sample students (first 5)")
print("=" * 80)

cur.execute("""
    SELECT student_id, student_nm, student_nm_en
    FROM idino_career.tb_student
    ORDER BY student_id
    LIMIT 5
""")
for s in cur.fetchall():
    print(f"  {s[0]} | {s[1]} | {s[2]}")

conn.close()
