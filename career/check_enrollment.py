"""Check enrollment table"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='postgres',
    user='postgres',
    password='2012'
)
cur = conn.cursor()

# Check if tb_enrollment exists
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'idino_career' AND table_name LIKE 'tb_enroll%'
""")
tables = cur.fetchall()
print("Enrollment-related tables:")
for t in tables:
    print(f"  {t[0]}")

if not tables:
    print("  No enrollment tables found!")

# Check tb_enrollment columns if exists
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'idino_career' AND table_name = 'tb_enrollment'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
if cols:
    print("\ntb_enrollment columns:")
    for c in cols:
        print(f"  {c[0]}")

conn.close()
