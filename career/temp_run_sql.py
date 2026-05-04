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
with open('database/16_seed_opportunities_extended.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    cur.execute(sql)
    print("SQL executed successfully!")
except Exception as e:
    print(f"Error: {e}")

# Check results
cur.execute("SET search_path TO idino_career, public;")
cur.execute("SELECT COUNT(*) FROM tb_opportunity")
print(f"Total opportunities: {cur.fetchone()[0]}")

cur.execute("""
    SELECT opportunity_type, COUNT(*)
    FROM tb_opportunity
    GROUP BY opportunity_type
    ORDER BY COUNT(*) DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

cur.close()
conn.close()
