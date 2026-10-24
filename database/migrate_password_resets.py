"""
CAMPUSX — Non-destructive Database Migration: Password Resets Table
"""
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import db

def run_migration():
    print("Running migration for password_resets table...")
    sql = """
    CREATE TABLE IF NOT EXISTS `password_resets` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` INT NOT NULL,
        `token_hash` VARCHAR(255) NOT NULL,
        `expires_at` DATETIME NOT NULL,
        `used_at` DATETIME DEFAULT NULL,
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
        INDEX `idx_pwd_reset_token` (`token_hash`),
        INDEX `idx_pwd_reset_user` (`user_id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    db.execute_non_query(sql)
    rows = db.execute_query("SHOW TABLES LIKE 'password_resets';")
    if rows:
        print("Success: 'password_resets' table is ready in MySQL database.")
        return True
    else:
        print("Error: Could not verify 'password_resets' table.")
        return False

if __name__ == "__main__":
    run_migration()
