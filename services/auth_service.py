"""
CAMPUSX — Discover People Behind the Work System
Authentication Service: User Registration, Login, and Session Validation
"""

import hashlib
import logging
import re
import secrets
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional, Tuple
from database.connection import db
from services.ecosystem_service import EcosystemService

logger = logging.getLogger("campusx.auth")

VALID_EMAIL_REGEX = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class AuthService:

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Return True for standard email addresses including valid plus-address tags."""
        if not isinstance(email, str):
            return False
        email_clean = email.strip()
        return bool(email_clean) and bool(VALID_EMAIL_REGEX.fullmatch(email_clean))

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
        if not cls.is_valid_email(email_clean):
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

    # --- Secure Password Reset System ---

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a reset token using SHA-256 with project reset salt."""
        salt = "campusx_reset_salt_2026"
        return hashlib.sha256((salt + token.strip().upper()).encode("utf-8")).hexdigest()

    @staticmethod
    def is_email_configured() -> bool:
        """Check whether SMTP email delivery is configured in the environment."""
        from config import SMTP_HOST, SMTP_USER, SMTP_PORT
        return bool(SMTP_HOST and (SMTP_USER or SMTP_PORT == 1025))

    @classmethod
    def send_reset_email(cls, to_email: str, token: str) -> Tuple[bool, str]:
        """Send password reset email with single-use token via configured SMTP."""
        from config import (
            PROJECT_NAME, SMTP_HOST, SMTP_PORT, SMTP_USER,
            SMTP_PASSWORD, SMTP_FROM_EMAIL, SMTP_TLS
        )
        if not cls.is_email_configured():
            return False, "SMTP email delivery is not configured."

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{PROJECT_NAME}] Password Reset Request"
            msg["From"] = SMTP_FROM_EMAIL
            msg["To"] = to_email

            text_body = (
                f"Hello,\n\n"
                f"A password reset was requested for your {PROJECT_NAME} account ({to_email}).\n\n"
                f"Your single-use reset token is: {token}\n\n"
                f"This token is valid for 15 minutes. If you did not request this, you can safely ignore this email.\n\n"
                f"Best regards,\n"
                f"{PROJECT_NAME} Security Team"
            )
            html_body = f"""
            <html>
            <body style="font-family: Segoe UI, sans-serif; color: #0F172A; line-height: 1.5;">
                <div style="max-width: 500px; margin: 0 auto; padding: 24px; border: 1px solid #E2E8F0; border-radius: 8px;">
                    <h2 style="color: #0B1F33; margin-top: 0;">{PROJECT_NAME} Password Reset</h2>
                    <p>Hello,</p>
                    <p>A password reset was requested for your <strong>{PROJECT_NAME}</strong> account (<code>{to_email}</code>).</p>
                    <div style="background-color: #F6F8FC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 16px; margin: 20px 0; text-align: center;">
                        <div style="font-size: 13px; color: #64748B; margin-bottom: 6px;">YOUR PASSWORD RESET TOKEN</div>
                        <div style="font-size: 24px; font-weight: bold; letter-spacing: 3px; color: #1E4E8C;">{token}</div>
                    </div>
                    <p style="font-size: 13px; color: #64748B;">This token is valid for <strong>15 minutes</strong> and can only be used once. If you did not request this, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #E2E8F0; margin: 20px 0;">
                    <p style="font-size: 11px; color: #94A3B8;">CAMPUSX — Discover People Behind the Work System</p>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            if SMTP_TLS:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    if SMTP_USER and SMTP_PASSWORD:
                        server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                    if SMTP_USER and SMTP_PASSWORD:
                        server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)

            return True, "Email sent successfully."
        except Exception as e:
            logger.error("Failed to send reset email: %s", e)
            return False, f"SMTP Error: {str(e)}"

    @classmethod
    def request_password_reset(cls, email: str) -> Dict[str, Any]:
        """
        Initiate a secure password reset request.
        Generates a time-limited (15 min), single-use reset token and stores only its hash.
        Does not reveal whether an email address exists in the database.
        """
        from config import DEV_MODE

        email_clean = (email or "").strip().lower()
        if not email_clean or not cls.is_valid_email(email_clean):
            return {
                "success": False,
                "email_configured": cls.is_email_configured(),
                "email_sent": False,
                "message": "Please enter a valid email address.",
                "dev_token": None
            }

        # Look up user
        user_rows = db.execute_query("SELECT id, email FROM users WHERE email = %s LIMIT 1;", (email_clean,))
        user = user_rows[0] if user_rows else None

        generated_token = None
        if user:
            # Invalidate any existing unused tokens for this user
            db.execute_non_query(
                "UPDATE password_resets SET used_at = NOW() WHERE user_id = %s AND used_at IS NULL;",
                (user["id"],)
            )

            # Generate random 8-character uppercase token (e.g. 'A8F2B1C9')
            generated_token = secrets.token_hex(4).upper()
            token_hash = cls.hash_token(generated_token)

            # Store only hashed token, expires in 15 minutes
            db.execute_non_query(
                """
                INSERT INTO password_resets (user_id, token_hash, expires_at)
                VALUES (%s, %s, NOW() + INTERVAL 15 MINUTE);
                """,
                (user["id"], token_hash)
            )

        email_configured = cls.is_email_configured()

        if email_configured:
            # Send live email if user exists
            if user and generated_token:
                ok, err_msg = cls.send_reset_email(email_clean, generated_token)
            # Generic message to avoid email enumeration
            return {
                "success": True,
                "email_configured": True,
                "email_sent": True,
                "message": (
                    "If an account with this email exists, a password reset token has been sent to your email. "
                    "Please check your inbox and enter the reset token below."
                ),
                "dev_token": None
            }
        else:
            # Email delivery is not configured. Do not pretend that an email was sent!
            # Clearly report missing configuration.
            msg = (
                "Email delivery is not configured on this server. "
                "To enable automated reset emails, configure SMTP settings (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD) in .env."
            )
            return {
                "success": True,
                "email_configured": False,
                "email_sent": False,
                "message": msg,
                "dev_token": generated_token if (user and DEV_MODE) else None
            }

    @classmethod
    def reset_password(cls, token: str, new_password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Validate single-use reset token and update user password securely.
        """
        token_clean = (token or "").strip().upper()
        if not token_clean:
            return False, "Reset token is required."

        if not new_password or len(new_password) < 6:
            return False, "Password must be at least 6 characters long."

        if new_password != confirm_password:
            return False, "New password and confirm password do not match."

        token_hash = cls.hash_token(token_clean)

        # Query database for matching token
        query = """
            SELECT id, user_id, expires_at, used_at
            FROM password_resets
            WHERE token_hash = %s
            ORDER BY created_at DESC LIMIT 1;
        """
        rows = db.execute_query(query, (token_hash,))
        if not rows:
            return False, "Invalid or unrecognized reset token."

        reset_record = rows[0]
        if reset_record["used_at"] is not None:
            return False, "This reset token has already been used. Please request a new one."

        # Check expiration
        expires_at = reset_record["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at < datetime.now():
            return False, "This reset token has expired. Reset tokens are valid for 15 minutes. Please request a new one."

        user_id = reset_record["user_id"]

        # Hash new password with existing project salt
        new_password_hash = cls.hash_password(new_password)

        # Update user password in database
        db.execute_non_query(
            "UPDATE users SET password_hash = %s WHERE id = %s;",
            (new_password_hash, user_id)
        )

        # Mark all pending tokens for this user as used
        db.execute_non_query(
            "UPDATE password_resets SET used_at = NOW() WHERE user_id = %s AND used_at IS NULL;",
            (user_id,)
        )

        return True, "Password reset successful! You can now log in with your new password."
