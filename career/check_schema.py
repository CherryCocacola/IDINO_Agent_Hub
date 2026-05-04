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
print("TB_DEPARTMENT columns in database:")
print("=" * 80)

cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'idino_career'
    AND table_name = 'tb_department'
    ORDER BY ordinal_position
""")

for col in cur.fetchall():
    print(f"  {col[0]}: {col[1]}")

conn.close()
