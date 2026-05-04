import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="postgres",
    user="postgres",
    password="2012"
)
cur = conn.cursor()
cur.execute("SET search_path TO idino_career, public;")

print("=" * 60)
print("tb_student_skill schema:")
print("=" * 60)
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'idino_career' AND table_name = 'tb_student_skill'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]})")

print("\n" + "=" * 60)
print("tb_skill schema:")
print("=" * 60)
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'idino_career' AND table_name = 'tb_skill'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]})")

cur.close()
conn.close()
