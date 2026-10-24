#!/usr/bin/env python3
"""One-time administrative recovery script for a CAMPUSX user account.

This script intentionally updates only the password_hash field for the selected
account identified by its registered email. It does not expose the password or
its hash in logs, and it verifies that exactly one row was updated.

Usage:
    python admin_recover_password.py

After running, log in with the new password using the existing email and password.
"""

import getpass
import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

sys.path.insert(0, str(ROOT_DIR))

from services.auth_service import AuthService


def main() -> int:
    print("CAMPUSX admin account recovery")
    print("This script updates only the password_hash for the selected user.")

    email = input("Registered email: ").strip().lower()
    if not AuthService.is_valid_email(email):
        print("Invalid email format.")
        return 1

    password = getpass.getpass("New password (hidden): ")
    confirm = getpass.getpass("Confirm new password (hidden): ")

    if not password or len(password) < 6:
        print("Password must be at least 6 characters long.")
        return 1
    if password != confirm:
        print("Passwords do not match.")
        return 1

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "3306"))
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "campusx_db")

    try:
        conn = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            autocommit=True,
            connect_timeout=5,
        )
    except mysql.connector.Error as exc:
        print(f"Database connection failed: {exc}")
        return 1

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, email, full_name, role FROM users WHERE email = %s LIMIT 1;",
            (email,),
        )
        user = cursor.fetchone()

        if not user:
            print("No matching user found for that email.")
            return 1

        hashed = AuthService.hash_password(password)
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s AND id = %s;",
            (hashed, email, user["id"]),
        )

        if cursor.rowcount != 1:
            print("Recovery failed: unexpected update count. No changes were applied.")
            return 1

        print(f"Password updated successfully for user id={user['id']} email={email}.")
        print("Only the password_hash field was changed for this one user.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
