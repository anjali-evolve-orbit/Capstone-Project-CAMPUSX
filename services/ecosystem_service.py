"""
CAMPUSX — Discover People Behind the Work System
Ecosystem Service: Campus, Institution, and Department Hierarchy
"""

from typing import Any, Dict, List, Optional
from database.connection import db


class EcosystemService:

    @staticmethod
    def get_campuses() -> List[Dict[str, Any]]:
        query = "SELECT id, name, location, description FROM campuses ORDER BY id ASC;"
        return db.execute_query(query)

    @staticmethod
    def get_institutions(campus_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if campus_id:
            query = "SELECT id, campus_id, name, code, is_custom FROM institutions WHERE campus_id = %s ORDER BY is_custom ASC, id ASC;"
            return db.execute_query(query, (campus_id,))
        query = "SELECT id, campus_id, name, code, is_custom FROM institutions ORDER BY is_custom ASC, id ASC;"
        return db.execute_query(query)

    @staticmethod
    def get_departments(institution_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if institution_id:
            query = "SELECT id, institution_id, name, code, is_custom FROM departments WHERE institution_id = %s ORDER BY is_custom ASC, id ASC;"
            return db.execute_query(query, (institution_id,))
        query = "SELECT id, institution_id, name, code, is_custom FROM departments ORDER BY is_custom ASC, id ASC;"
        return db.execute_query(query)

    @staticmethod
    def ensure_custom_institution(campus_id: int, custom_name: str) -> int:
        """Store or retrieve custom institution entered by user."""
        name = custom_name.strip()
        rows = db.execute_query(
            "SELECT id FROM institutions WHERE name = %s AND campus_id = %s LIMIT 1;",
            (name, campus_id)
        )
        if rows:
            return rows[0]["id"]
        return db.execute_non_query(
            "INSERT INTO institutions (campus_id, name, code, is_custom) VALUES (%s, %s, 'CUSTOM', TRUE);",
            (campus_id, name)
        )

    @staticmethod
    def ensure_custom_department(institution_id: int, custom_name: str) -> int:
        """Store or retrieve custom department entered by user."""
        name = custom_name.strip()
        rows = db.execute_query(
            "SELECT id FROM departments WHERE name = %s AND institution_id = %s LIMIT 1;",
            (name, institution_id)
        )
        if rows:
            return rows[0]["id"]
        return db.execute_non_query(
            "INSERT INTO departments (institution_id, name, code, is_custom) VALUES (%s, %s, 'CUSTOM', TRUE);",
            (institution_id, name)
        )
