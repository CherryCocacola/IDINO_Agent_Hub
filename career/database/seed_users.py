"""
Seed script for test users in the auth system.

Usage:
    python seed_users.py
"""

import os
import sys
from pathlib import Path
from uuid import uuid4

import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "2012"),
    )


def seed_users(conn):
    """Seed test users into the database."""
    print("\n" + "=" * 60)
    print("Seeding Test Users")
    print("=" * 60)

    schema = os.getenv("DB_SCHEMA", "idino_career")

    # Test users to create
    # Note: student_id and professor_cd are set to None for now
    # They can be linked later when actual student/professor records exist
    test_users = [
        {
            "login_id": "admin",
            "password": "admin123",
            "user_type": "admin",
            "email": "admin@university.ac.kr",
            "student_id": None,
            "professor_cd": None,
        },
        {
            "login_id": "career_admin",
            "password": "admin123",
            "user_type": "career_admin",
            "email": "career@university.ac.kr",
            "student_id": None,
            "professor_cd": None,
        },
        {
            "login_id": "student_hong",
            "password": "student123",
            "user_type": "student",
            "email": "hong@student.ac.kr",
            "student_id": None,  # Will be linked when student record exists
            "professor_cd": None,
        },
        {
            "login_id": "student_lee",
            "password": "student123",
            "user_type": "student",
            "email": "lee@student.ac.kr",
            "student_id": None,  # Will be linked when student record exists
            "professor_cd": None,
        },
        {
            "login_id": "prof_kim",
            "password": "prof123",
            "user_type": "professor",
            "email": "prof@university.ac.kr",
            "student_id": None,
            "professor_cd": None,  # Will be linked when professor record exists
        },
    ]

    with conn.cursor() as cursor:
        # Set search path
        cursor.execute(f"SET search_path TO {schema}, public")

        for user_data in test_users:
            try:
                # Check if user already exists
                cursor.execute(
                    "SELECT user_id FROM tb_user WHERE login_id = %s",
                    (user_data["login_id"],)
                )
                existing = cursor.fetchone()

                if existing:
                    print(f"  - {user_data['login_id']}: Already exists (skipped)")
                    continue

                # Hash password
                password_hash = pwd_context.hash(user_data["password"])

                # Insert user
                user_id = uuid4()
                cursor.execute("""
                    INSERT INTO tb_user (
                        user_id, login_id, password_hash, user_type,
                        email, student_id, professor_cd, status,
                        mfa_enabled, ins_user_id, ins_dt
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, 'active',
                        FALSE, 'system', CURRENT_TIMESTAMP
                    )
                """, (
                    str(user_id),
                    user_data["login_id"],
                    password_hash,
                    user_data["user_type"],
                    user_data["email"],
                    user_data["student_id"],
                    user_data["professor_cd"],
                ))

                print(f"  - {user_data['login_id']}: Created ({user_data['user_type']})")

            except Exception as e:
                print(f"  - {user_data['login_id']}: Error - {e}")
                conn.rollback()
                continue

        conn.commit()

    print("\n" + "-" * 60)
    print("Test User Credentials:")
    print("-" * 60)
    print("| Login ID      | Password    | Type         |")
    print("|---------------|-------------|--------------|")
    print("| admin         | admin123    | admin        |")
    print("| career_admin  | admin123    | career_admin |")
    print("| student_hong  | student123  | student      |")
    print("| student_lee   | student123  | student      |")
    print("| prof_kim      | prof123     | professor    |")
    print("-" * 60)


def main():
    print("\n" + "=" * 60)
    print("IDINO Career - User Seed Script")
    print("=" * 60)
    print(f"Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"Database: {os.getenv('DB_NAME', 'postgres')}")
    print(f"Schema: {os.getenv('DB_SCHEMA', 'idino_career')}")

    try:
        conn = get_db_connection()
        print("\nDatabase connection successful!")

        seed_users(conn)

        conn.close()
        print("\nDone!")
        return 0

    except psycopg2.OperationalError as e:
        print(f"\nERROR: Could not connect to database")
        print(f"Details: {e}")
        return 1

    except Exception as e:
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
