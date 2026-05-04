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

# Tables that might need audit columns added
tables_to_fix = ['tb_department', 'tb_college', 'tb_university', 'tb_student']

# Columns to check/add
audit_columns = [
    ('ins_user_ip', 'VARCHAR(50)'),
    ('ins_system_gcd', 'VARCHAR(10)'),
    ('ins_menu_cd', 'VARCHAR(20)'),
    ('upd_user_ip', 'VARCHAR(50)'),
    ('upd_system_gcd', 'VARCHAR(10)'),
    ('upd_menu_cd', 'VARCHAR(20)'),
]

print("=" * 80)
print("Fixing schema - Adding missing audit columns")
print("=" * 80)

for table in tables_to_fix:
    print(f"\nProcessing {table}...")

    # Get existing columns
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = '{schema}' AND table_name = '{table}'
    """)
    existing_columns = set(row[0] for row in cur.fetchall())

    for col_name, col_type in audit_columns:
        if col_name not in existing_columns:
            try:
                cur.execute(f"""
                    ALTER TABLE {schema}.{table}
                    ADD COLUMN {col_name} {col_type}
                """)
                print(f"  [OK] Added {col_name} to {table}")
            except Exception as e:
                print(f"  [ERR] Failed to add {col_name}: {e}")
        else:
            print(f"  - {col_name} already exists")

print("\n" + "=" * 80)
print("Schema fix complete!")
print("=" * 80)

conn.close()
