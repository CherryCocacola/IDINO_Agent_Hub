import psycopg
conn = psycopg.connect('host=localhost port=5432 dbname=postgres user=postgres password=2012')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'idino_career' AND table_name = 'tb_student'")
print("tb_student columns:", [r[0] for r in cur.fetchall()])
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'idino_career' AND table_name = 'tb_department'")
print("tb_department columns:", [r[0] for r in cur.fetchall()])
conn.close()
