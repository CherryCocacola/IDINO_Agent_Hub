"""Fix all schema mismatches"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='postgres',
    user='postgres',
    password='2012'
)
conn.autocommit = True
cur = conn.cursor()

schema = 'idino_career'

print("=" * 80)
print("Fixing schema mismatches")
print("=" * 80)

# Fix tb_enrollment column names
print("\n[1] tb_enrollment column renames:")
try:
    cur.execute(f"""
        ALTER TABLE {schema}.tb_enrollment
        RENAME COLUMN offering_id TO course_offering_id
    """)
    print("  [OK] offering_id -> course_offering_id")
except Exception as e:
    if "does not exist" in str(e):
        print("  [SKIP] offering_id doesn't exist (already renamed?)")
    else:
        print(f"  [ERR] {e}")

try:
    cur.execute(f"""
        ALTER TABLE {schema}.tb_enrollment
        RENAME COLUMN status TO status_cd
    """)
    print("  [OK] status -> status_cd")
except Exception as e:
    if "does not exist" in str(e):
        print("  [SKIP] status doesn't exist (already renamed?)")
    else:
        print(f"  [ERR] {e}")

# Check if tb_course_offering exists
print("\n[2] Checking related tables:")
cur.execute(f"""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = '{schema}' AND table_name LIKE 'tb_course%'
""")
course_tables = cur.fetchall()
print(f"  Course-related tables: {[t[0] for t in course_tables]}")

# Check tb_activity, tb_achievement
for table in ['tb_activity', 'tb_achievement']:
    cur.execute(f"""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = '{schema}' AND table_name = '{table}'
    """)
    exists = cur.fetchone()[0] > 0
    print(f"  {table}: {'exists' if exists else 'missing'}")

# Verify enrollment columns after fix
print("\n[3] tb_enrollment columns after fix:")
cur.execute(f"""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = '{schema}' AND table_name = 'tb_enrollment'
    ORDER BY ordinal_position
""")
for c in cur.fetchall():
    print(f"  {c[0]}")

print("\n" + "=" * 80)
print("Schema fix complete!")
print("=" * 80)

conn.close()
