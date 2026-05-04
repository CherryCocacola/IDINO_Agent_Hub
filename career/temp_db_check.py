import psycopg2
import os

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

# Set schema
cur.execute("SET search_path TO idino_career, public;")

print("=" * 60)
print("1. tb_student counts by admission_year")
print("=" * 60)
cur.execute("""
    SELECT admission_year, COUNT(*)
    FROM tb_student
    GROUP BY admission_year
    ORDER BY admission_year DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} students")

print("\n" + "=" * 60)
print("2. tb_opportunity count and sample")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM tb_opportunity")
print(f"  Total: {cur.fetchone()[0]} records")
cur.execute("SELECT opportunity_type, title, organization FROM tb_opportunity LIMIT 5")
for row in cur.fetchall():
    print(f"  [{row[0]}] {row[1]} - {row[2]}")

print("\n" + "=" * 60)
print("3. tb_skill count")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM tb_skill")
print(f"  Total: {cur.fetchone()[0]} skills")

print("\n" + "=" * 60)
print("4. tb_student_skill count")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM tb_student_skill")
print(f"  Total: {cur.fetchone()[0]} student-skill links")

print("\n" + "=" * 60)
print("5. tb_portfolio count")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM tb_portfolio")
print(f"  Total: {cur.fetchone()[0]} portfolio items")

print("\n" + "=" * 60)
print("6. tb_achievement schema")
print("=" * 60)
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'idino_career' AND table_name = 'tb_achievement'
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]})")

print("\n" + "=" * 60)
print("7. tb_achievement count")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM tb_achievement")
print(f"  Total: {cur.fetchone()[0]} records")

print("\n" + "=" * 60)
print("8. Excel tb_achievement columns")
print("=" * 60)
import pandas as pd
df = pd.read_excel('user_mig/exports/idino_table_columns.xlsx')
table_col = df.columns[0]
col_col = df.columns[2]  # Column name
type_col = df.columns[4]  # Data type
achievement_df = df[df[table_col].astype(str).str.contains('tb_achievement', case=False, na=False)]
for _, row in achievement_df.iterrows():
    print(f"  {row[col_col]}: {row[type_col]}")

cur.close()
conn.close()
