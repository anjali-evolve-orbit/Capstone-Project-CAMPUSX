"""
CAMPUSX — Discover People Behind the Work System
MySQL Database Connection Manager (MySQL Exclusive)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import mysql.connector
from mysql.connector import Error as MySQLError, pooling

from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger("campusx.database")


class DatabaseConnectionError(Exception):
    """Raised when MySQL connection cannot be established or credentials fail."""
    pass


class MySQLDatabase:
    """Singleton MySQL Database Manager for CAMPUSX."""
    _instance: Optional["MySQLDatabase"] = None
    _pool: Optional[pooling.MySQLConnectionPool] = None

    def __new__(cls) -> "MySQLDatabase":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._init_pool()

    def _init_pool(self):
        """Initialize the MySQL connection pool."""
        try:
            self._pool = pooling.MySQLConnectionPool(
                pool_name="campusx_pool",
                pool_size=10,
                pool_reset_session=True,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=5,
                autocommit=True
            )
            logger.info("Connected to MySQL database '%s' at %s:%s", DB_NAME, DB_HOST, DB_PORT)
        except MySQLError as err:
            self._pool = None
            logger.warning("Could not initialize MySQL connection pool: %s", err)

    def get_connection(self):
        """
        Acquire a connection from the pool or establish a direct connection.
        Raises DatabaseConnectionError with troubleshooting guidance if unavailable.
        """
        if self._pool is not None:
            try:
                conn = self._pool.get_connection()
                if conn.is_connected():
                    return conn
            except MySQLError:
                pass

        # Try direct connection
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=5,
                autocommit=True
            )
            return conn
        except MySQLError as err:
            error_msg = (
                f"CAMPUSX Database Connection Error: Unable to connect to MySQL database '{DB_NAME}' "
                f"at {DB_HOST}:{DB_PORT} as user '{DB_USER}'.\n"
                f"MySQL Error Details: [{err.errno}] {err.msg}\n\n"
                f"Troubleshooting Steps:\n"
                f"1. Ensure your MySQL service (e.g., MySQL80) is running.\n"
                f"2. Check that your MySQL password in .env matches your MySQL root password:\n"
                f"   DB_PASSWORD=your_actual_password\n"
                f"3. Run the database setup script to create and seed the database:\n"
                f"   python setup_db.py\n"
            )
            logger.error(error_msg)
            raise DatabaseConnectionError(error_msg) from err

    def execute_query(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None,
        fetch_all: bool = True,
        dictionary: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return rows as dictionaries."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor(dictionary=dictionary)
            cursor.execute(query, params or ())
            result = cursor.fetchall() if fetch_all else cursor.fetchone()
            cursor.close()
            return result or []
        finally:
            conn.close()

    def execute_non_query(
        self,
        query: str,
        params: Optional[Union[Tuple, Dict]] = None
    ) -> int:
        """Execute an INSERT, UPDATE, or DELETE query and return the last row ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            last_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            return last_id
        finally:
            conn.close()

    def test_connection(self) -> Tuple[bool, str]:
        """Test connection status and return (is_connected, message)."""
        try:
            conn = self.get_connection()
            conn.close()
            return True, f"Successfully connected to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}"
        except DatabaseConnectionError as e:
            return False, str(e)


# Global instance for app-wide use
db = MySQLDatabase()
