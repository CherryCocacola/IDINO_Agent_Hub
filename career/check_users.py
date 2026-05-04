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
print("TB_USER - 사용자-학생 연결 상태 확인")
print("=" * 80)

cur.execute("""
    SELECT user_id, login_id, student_id, user_type
    FROM idino_career.tb_user
    ORDER BY user_id
""")
rows = cur.fetchall()

print(f"{'user_id':<10} | {'login_id':<20} | {'student_id':<15} | {'user_type':<10}")
print("-" * 80)
for r in rows:
    student_id = r[2] if r[2] else 'NULL'
    print(f"{r[0]:<10} | {r[1]:<20} | {student_id:<15} | {r[3]:<10}")

print("\n" + "=" * 80)
print("TB_STUDENT - 학생 정보 샘플 (상위 10명)")
print("=" * 80)

cur.execute("""
    SELECT student_id, student_nm, department_cd, current_grade
    FROM idino_career.tb_student
    ORDER BY student_id
    LIMIT 10
""")
students = cur.fetchall()

print(f"{'student_id':<15} | {'student_nm':<15} | {'department_cd':<15} | {'grade':<5}")
print("-" * 60)
for s in students:
    print(f"{s[0]:<15} | {s[1]:<15} | {s[2]:<15} | {s[3]:<5}")

print("\n" + "=" * 80)
print("연결되지 않은 사용자 확인")
print("=" * 80)

cur.execute("""
    SELECT u.login_id, u.user_type
    FROM idino_career.tb_user u
    WHERE u.student_id IS NULL AND u.user_type = 'student'
""")
unlinked = cur.fetchall()

if unlinked:
    print("학생 타입인데 student_id가 없는 사용자:")
    for u in unlinked:
        print(f"  - {u[0]} ({u[1]})")
else:
    print("모든 학생 타입 사용자가 student_id에 연결되어 있습니다.")

conn.close()
