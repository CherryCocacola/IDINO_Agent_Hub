#!/usr/bin/env python
"""Initialize IDINO Career database with all seed data."""

import psycopg2
from pathlib import Path

DB_DIR = Path(__file__).parent

def get_connection():
    return psycopg2.connect(
        host='localhost',
        port='5432',
        dbname='postgres',
        user='postgres',
        password='2012'
    )

def run_sql_file(cur, filepath, step_name):
    """Execute SQL file, stripping comments to avoid encoding issues."""
    print(f'[{step_name}] Processing {filepath.name}...')
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        # Remove comments to avoid encoding issues
        lines = []
        for line in content.split('\n'):
            # Remove line comments
            if '--' in line:
                idx = line.find('--')
                line = line[:idx]
            lines.append(line)

        sql = '\n'.join(lines)

        # Split into statements
        statements = sql.split(';')
        executed = 0
        errors = 0

        for stmt in statements:
            stmt = stmt.strip()
            # Skip empty statements and psql commands
            if not stmt or stmt.startswith('\\'):
                continue
            try:
                cur.execute(stmt)
                executed += 1
            except psycopg2.Error as e:
                errors += 1
                # Print first few errors for debugging
                if errors <= 5:
                    error_msg = str(e).split('\n')[0][:100]
                    print(f'  Error {errors}: {error_msg}')

        print(f'[{step_name}] Executed {executed} statements ({errors} errors)')
        return True
    except Exception as e:
        print(f'[{step_name}] Error: {e}')
        return False

def main():
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()

    print('=' * 60)
    print('IDINO Career Database Initialization')
    print('=' * 60)

    # Reset schema
    print('\n[Setup] Resetting schema...')
    cur.execute('DROP SCHEMA IF EXISTS idino_career CASCADE')
    cur.execute('CREATE SCHEMA idino_career')
    cur.execute('SET search_path TO idino_career, public')
    cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public')
    cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto" SCHEMA public')
    print('[Setup] Schema reset complete.')

    # SQL files to run in order
    files = [
        '01_schema_create.sql',
        '02_techspec_tables.sql',
        '03_seed_data.sql',
        '04_seed_students.sql',
        '05_seed_enrollments.sql',
        '10_p1_p2_extensions.sql',
        '06_seed_p1_skills.sql',
        '07_seed_p1_coaching.sql',
        '08_seed_p1_opportunities.sql',
        '09_seed_p1_risk.sql',
        '10_seed_p2_badges.sql',
        '11_seed_p2_simulation.sql',
        '12_seed_p2_advisor.sql',
    ]

    print(f'\n[Run] Executing {len(files)} SQL files...')
    for i, filename in enumerate(files, 1):
        filepath = DB_DIR / filename
        if filepath.exists():
            run_sql_file(cur, filepath, f'{i:02d}/{len(files)}')
        else:
            print(f'[{i:02d}/{len(files)}] File not found: {filename}')

    # Verification
    print('\n' + '=' * 60)
    print('Verification:')
    print('=' * 60)

    tables_to_check = [
        ('tb_university', 'Universities'),
        ('tb_department', 'Departments'),
        ('tb_student', 'Students'),
        ('tb_course', 'Courses'),
        ('tb_professor', 'Professors'),
        ('tb_skill', 'Skills'),
        ('tb_competency', 'Competencies'),
        ('tb_student_skill', 'Student Skills'),
        ('tb_coaching_goal', 'Coaching Goals'),
        ('tb_opportunity', 'Opportunities'),
        ('tb_risk_alert', 'Risk Alerts'),
        ('tb_badge', 'Badges'),
        ('tb_advisor', 'Advisors'),
    ]

    for table, label in tables_to_check:
        try:
            cur.execute(f'SELECT COUNT(*) FROM idino_career.{table}')
            count = cur.fetchone()[0]
            print(f'  {label:20s}: {count:5d} rows')
        except Exception as e:
            print(f'  {label:20s}: table not found')

    conn.close()
    print('\n' + '=' * 60)
    print('Database initialization complete!')
    print('=' * 60)

if __name__ == '__main__':
    main()
