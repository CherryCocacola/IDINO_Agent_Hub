"""
Database Migration Runner for IDINO Career System.

Usage:
    python run_migrations.py --setup     # Run initial schema setup only
    python run_migrations.py --migrate   # Run migrations only
    python run_migrations.py --all       # Run setup + migrations (default)
"""

import os
import sys
import argparse
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "2012"),
    )


def execute_sql_file(conn, filepath: Path, description: str):
    """Execute a SQL file."""
    print(f"\n{'='*60}")
    print(f"Executing: {description}")
    print(f"File: {filepath}")
    print("=" * 60)

    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            sql_content = f.read()

        with conn.cursor() as cursor:
            cursor.execute(sql_content)

        conn.commit()
        print(f"SUCCESS: {description} completed")
        return True

    except psycopg2.Error as e:
        conn.rollback()
        print(f"ERROR: {e}")
        return False


def run_setup(conn):
    """Run initial database setup."""
    setup_file = Path(__file__).parent.parent / "user_mig" / "run_database_setup.sql"
    return execute_sql_file(conn, setup_file, "Initial Database Setup")


def run_migrations(conn):
    """Run all migration files in order."""
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob("migration_*.sql"))

    if not migration_files:
        print("No migration files found.")
        return True

    success = True
    for migration_file in migration_files:
        result = execute_sql_file(
            conn,
            migration_file,
            f"Migration: {migration_file.name}"
        )
        if not result:
            success = False
            break

    return success


def verify_schema(conn):
    """Verify the schema was created correctly."""
    print("\n" + "=" * 60)
    print("Verifying Schema...")
    print("=" * 60)

    schema = os.getenv("DB_SCHEMA", "idino_career")

    with conn.cursor() as cursor:
        # Check tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
        """, (schema,))
        tables = cursor.fetchall()

        print(f"\nTables in schema '{schema}':")
        print("-" * 40)

        auth_tables = []
        career_tables = []
        other_tables = []

        for (table_name,) in tables:
            if table_name.startswith(("tb_user", "tb_auth", "tb_login")):
                auth_tables.append(table_name)
            elif "career" in table_name:
                career_tables.append(table_name)
            else:
                other_tables.append(table_name)

        print("\n[Authentication Tables]")
        for t in auth_tables:
            print(f"  - {t}")

        print("\n[Career Tables]")
        for t in career_tables:
            print(f"  - {t}")

        print(f"\n[Other Tables] ({len(other_tables)} tables)")
        for t in other_tables[:10]:
            print(f"  - {t}")
        if len(other_tables) > 10:
            print(f"  ... and {len(other_tables) - 10} more")

        # Check views
        cursor.execute("""
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = %s
            ORDER BY table_name
        """, (schema,))
        views = cursor.fetchall()

        if views:
            print("\n[Views]")
            for (view_name,) in views:
                print(f"  - {view_name}")

        print("\n" + "-" * 40)
        print(f"Total: {len(tables)} tables, {len(views)} views")

    return True


def main():
    parser = argparse.ArgumentParser(description="IDINO Career Database Migration Runner")
    parser.add_argument("--setup", action="store_true", help="Run initial schema setup only")
    parser.add_argument("--migrate", action="store_true", help="Run migrations only")
    parser.add_argument("--all", action="store_true", help="Run setup + migrations (default)")
    parser.add_argument("--verify", action="store_true", help="Verify schema only")

    args = parser.parse_args()

    # Default to --all if no flags specified
    if not any([args.setup, args.migrate, args.all, args.verify]):
        args.all = True

    print("\n" + "=" * 60)
    print("IDINO Career Database Migration Runner")
    print("=" * 60)
    print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"Port: {os.getenv('DB_PORT', '5432')}")
    print(f"Database: {os.getenv('DB_NAME', 'postgres')}")
    print(f"Schema: {os.getenv('DB_SCHEMA', 'idino_career')}")

    try:
        conn = get_db_connection()
        print("\nDatabase connection successful!")

        if args.verify:
            verify_schema(conn)
        elif args.setup:
            if run_setup(conn):
                verify_schema(conn)
        elif args.migrate:
            if run_migrations(conn):
                verify_schema(conn)
        else:  # --all
            if run_setup(conn):
                if run_migrations(conn):
                    verify_schema(conn)

        conn.close()
        print("\nDone!")
        return 0

    except psycopg2.OperationalError as e:
        print(f"\nERROR: Could not connect to database")
        print(f"Details: {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Connection settings in .env are correct")
        print("  3. Database 'postgres' exists")
        return 1

    except Exception as e:
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
