"""Direct database query test"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='postgres',
    user='postgres',
    password='2012',
    options='-c search_path=idino_career'
)
cur = conn.cursor()

print("=" * 80)
print("Testing student query with department join")
print("=" * 80)

# Query student with department
cur.execute("""
    SELECT
        s.student_id,
        s.student_nm,
        s.department_cd,
        d.department_nm,
        s.current_grade
    FROM tb_student s
    LEFT JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE s.student_id = '2021010001'
""")

result = cur.fetchone()
if result:
    print(f"Student ID: {result[0]}")
    print(f"Name: {result[1]}")
    print(f"Department Code: {result[2]}")
    print(f"Department Name: {result[3]}")
    print(f"Grade: {result[4]}")
else:
    print("Student not found!")

print("\n" + "=" * 80)
print("Testing different student")
print("=" * 80)

# Query different student
cur.execute("""
    SELECT
        s.student_id,
        s.student_nm,
        s.department_cd,
        d.department_nm,
        s.current_grade
    FROM tb_student s
    LEFT JOIN tb_department d ON s.department_cd = d.department_cd
    WHERE s.student_id = '2020010000'
""")

result = cur.fetchone()
if result:
    print(f"Student ID: {result[0]}")
    print(f"Name: {result[1]}")
    print(f"Department Code: {result[2]}")
    print(f"Department Name: {result[3]}")
    print(f"Grade: {result[4]}")
else:
    print("Student not found!")

conn.close()
