"""
CAMPUSX — Discover People Behind the Work System
Authentication Service: User Registration, Login, and Session Validation
"""

import hashlib
import re
from typing import Any, Dict, Optional, Tuple
from database.connection import db
from services.ecosystem_service import EcosystemService


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with project salt."""
        salt = "campusx_salt_2026"
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    @classmethod
    def register(
        cls,
        full_name: str,
        email: str,
        password: str,
        role: str = "Student",
        campus_id: Optional[int] = None,
        institution_id: Optional[int] = None,
        department_id: Optional[int] = None,
        custom_institution: Optional[str] = None,
        custom_department: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate and register a new user in CAMPUSX."""
        # 1. Validations
        name_clean = full_name.strip()
        if not name_clean or len(name_clean) < 2:
            return False, "Full Name must be at least 2 characters.", None

        email_clean = email.strip().lower()
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email_clean):
            return False, "Please enter a valid email address.", None

        if len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        valid_roles = ["Student", "Researcher", "Faculty", "Other"]
        if role not in valid_roles:
            role = "Student"

        # Check existing email
        existing = db.execute_query("SELECT id FROM users WHERE email = %s LIMIT 1;", (email_clean,))
        if existing:
            return False, "An account with this email already exists. Please login.", None

        # Fallback default campus if not provided
        if not campus_id:
            campuses = EcosystemService.get_campuses()
            campus_id = campuses[0]["id"] if campuses else 1

        # Handle custom institution ("Other")
        final_inst_id = institution_id
        if custom_institution and custom_institution.strip():
            final_inst_id = EcosystemService.ensure_custom_institution(campus_id, custom_institution.strip())
        elif institution_id == 999:  # 'Other' selected without text
            return False, "Please enter your Institution name.", None

        # Handle custom department ("Other")
        final_dept_id = department_id
        if custom_department and custom_department.strip() and final_inst_id:
            final_dept_id = EcosystemService.ensure_custom_department(final_inst_id, custom_department.strip())
        elif department_id in [991, 992, 993, 999]:
            return False, "Please enter your Department / Program name.", None

        password_hash = cls.hash_password(password)

        user_id = db.execute_non_query(
            """
            INSERT INTO users (
                full_name, email, password_hash, role, campus_id,
                institution_id, department_id, custom_institution, custom_department
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                name_clean, email_clean, password_hash, role, campus_id,
                final_inst_id, final_dept_id, custom_institution or None, custom_department or None
            )
        )

        from services.research_service import ResearchService
        ResearchService.ensure_researcher_for_user(
            user_id=user_id,
            full_name=name_clean,
            institution_id=final_inst_id,
            department_id=final_dept_id,
            designation=role,
            email=email_clean,
            bio=f"{role} researcher at the campus actively exploring academic collaborations."
        )

        user_data = cls.get_user_by_id(user_id)
        return True, "Registration successful!", user_data

    @classmethod
    def login(cls, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticate user credentials."""
        email_clean = email.strip().lower()
        if not email_clean or not password:
            return False, "Email and password are required.", None

        hashed = cls.hash_password(password)

        query = """
            SELECT u.id, u.full_name, u.email, u.password_hash, u.role,
                   u.campus_id, u.institution_id, u.department_id,
                   u.custom_institution, u.custom_department,
                   i.name as institution_name, d.name as department_name, c.name as campus_name
            FROM users u
            LEFT JOIN institutions i ON u.institution_id = i.id
            LEFT JOIN departments d ON u.department_id = d.id
            LEFT JOIN campuses c ON u.campus_id = c.id
            WHERE u.email = %s LIMIT 1;
        """
        rows = db.execute_query(query, (email_clean,))
        if not rows:
            return False, "Invalid email or password.", None

        user = rows[0]
        # Check against both seeded demo hash and newly hashed password
        seed_hash = hashlib.sha256("CampusX@2026".encode("utf-8")).hexdigest()
        if user["password_hash"] != hashed and not (password == "CampusX@2026" and user["password_hash"] == seed_hash):
            return False, "Invalid email or password.", None

        from services.research_service import ResearchService
        ResearchService.ensure_researcher_for_user(
            user_id=user["id"],
            full_name=user.get("full_name"),
            institution_id=user.get("institution_id"),
            department_id=user.get("department_id"),
            designation=user.get("role") or "Student Researcher",
            email=user.get("email")
        )

        # Omit password hash in returned user object
        user.pop("password_hash", None)
        return True, "Login successful!", user

    @classmethod
    def get_user_by_id(cls, user_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.id, u.full_name, u.email, u.role,
                   u.campus_id, u.institution_id, u.department_id,
                   u.custom_institution, u.custom_department,
                   i.name as institution_name, d.name as department_name, c.name as campus_name
            FROM users u
            LEFT JOIN institutions i ON u.institution_id = i.id
            LEFT JOIN departments d ON u.department_id = d.id
            LEFT JOIN campuses c ON u.campus_id = c.id
            WHERE u.id = %s LIMIT 1;
        """
        rows = db.execute_query(query, (user_id,))
        return rows[0] if rows else None
