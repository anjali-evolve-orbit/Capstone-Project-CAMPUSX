"""
CAMPUSX — Discover People Behind the Work System
MySQL Database Setup & Seeding Script

Usage:
    python setup_db.py
"""

import sys
import os
from pathlib import Path
import mysql.connector
from mysql.connector import Error as MySQLError

# Ensure root directory is on Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, BASE_DIR


def execute_sql_file(cursor, file_path: Path):
    """Read an SQL script and execute each statement cleanly."""
    if not file_path.exists():
        print(f"Error: SQL file not found: {file_path}")
        return False

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by semicolon while ignoring comments
    statements = []
    current_stmt = []
    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("--") or trimmed.startswith("/*"):
            continue
        current_stmt.append(line)
        if trimmed.endswith(";"):
            statements.append("\n".join(current_stmt))
            current_stmt = []

    for stmt in statements:
        stmt_clean = stmt.strip()
        if stmt_clean:
            cursor.execute(stmt_clean)
    return True


def run_setup():
    print("=" * 65)
    print("CAMPUSX — Database Initialization & Seeding (MySQL Exclusive)")
    print("=" * 65)
    print(f"Connecting to MySQL server at {DB_HOST}:{DB_PORT} as user '{DB_USER}'...")

    try:
        # 1. Connect to MySQL server directly
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10,
            autocommit=True
        )
        cursor = conn.cursor()
        print("Connected to MySQL server.")

        # 2. Create database if it does not exist
        print(f"Ensuring database '{DB_NAME}' exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE `{DB_NAME}`;")
        print(f"Using database '{DB_NAME}'.")

        # 3. Apply schema.sql
        schema_file = BASE_DIR / "database" / "schema.sql"
        print(f"Applying schema from {schema_file.name}...")
        execute_sql_file(cursor, schema_file)
        print("Schema created successfully.")

        # 4. Apply seed.sql
        seed_file = BASE_DIR / "database" / "seed.sql"
        print(f"Applying seed data from {seed_file.name}...")
        execute_sql_file(cursor, seed_file)
        print("Seed data inserted successfully.")

        # 5. Verify record counts
        print("\n--- Database Verification Summary ---")
        tables = [
            ("campuses", "Campuses"),
            ("institutions", "Institutions"),
            ("departments", "Departments / Programs"),
            ("research_areas", "Research Areas"),
            ("researchers", "Researchers"),
            ("papers", "Academic Papers"),
            ("collaborations", "Collaborations (Graph Edges)"),
            ("communities", "Academic Communities"),
            ("users", "Users"),
            ("password_resets", "Password Reset Tokens")
        ]
        for tbl, label in tables:
            cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
            count = cursor.fetchone()[0]
            print(f" - {label:<32}: {count} records")

        cursor.close()
        conn.close()
        print("\nDatabase initialization complete! CAMPUSX is ready to run.")
        print("=" * 65)
        return True

    except MySQLError as err:
        print("\n" + "!" * 65)
        print("FAILED TO CONNECT TO MYSQL OR INITIALIZE DATABASE")
        print("!" * 65)
        print(f"Error Code: {err.errno}")
        print(f"Message   : {err.msg}")
        print("\nTroubleshooting:")
        print("1. Ensure MySQL service is running on your machine (e.g. MySQL80).")
        print("2. Check that DB_PASSWORD in your .env file matches your MySQL password.")
        print("   Edit .env: DB_PASSWORD=your_password")
        print("3. Re-run: python setup_db.py")
        print("!" * 65)
        return False


if __name__ == "__main__":
    success = run_setup()
    sys.exit(0 if success else 1)
