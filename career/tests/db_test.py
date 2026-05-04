# Simple DB connection test - using psycopg v3
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import psycopg

try:
    conn = psycopg.connect(
        host='localhost',
        port=5432,
        dbname='postgres',
        user='postgres',
        password='2012'
    )
    print("Connection OK")
    
    cur = conn.cursor()
    cur.execute("SET search_path TO idino_career")
    cur.execute("SELECT COUNT(*) FROM tb_student WHERE admission_year IN (2023, 2024, 2025)")
    count = cur.fetchone()[0]
    print(f"Total students: {count}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {type(e).__name__}: {str(e)[:100]}")
