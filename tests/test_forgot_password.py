"""
CAMPUSX — Automated Tests for Forgot Password & Secure Token Reset System
"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import db
from services.auth_service import AuthService
from api.main import (
    forgot_password_endpoint,
    reset_password_endpoint,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from fastapi import HTTPException
import customtkinter as ctk
from ui.login import LoginView
from ui.forgot_password import ForgotPasswordView


class TestForgotPassword(unittest.TestCase):
    """Comprehensive test suite for secure password reset flow."""

    @classmethod
    def setUpClass(cls):
        # Create a dedicated test user for password reset tests
        cls.test_email = "pwd_reset_test_user@campusx.edu"
        cls.original_password = "InitialPassword@2026"
        cls.new_password = "UpdatedPassword@2026"

        # Clean any preexisting test user and researcher
        db.execute_non_query("DELETE FROM researchers WHERE email = %s;", (cls.test_email,))
        db.execute_non_query("DELETE FROM users WHERE email = %s;", (cls.test_email,))

        # Register test user
        ok, msg, user = AuthService.register(
            full_name="Password Reset Tester",
            email=cls.test_email,
            password=cls.original_password,
            role="Student"
        )
        assert ok, f"Failed to register test user: {msg}"
        cls.test_user_id = user["id"]

    @classmethod
    def tearDownClass(cls):
        # Clean up test user, researcher, and associated reset tokens
        db.execute_non_query("DELETE FROM password_resets WHERE user_id = %s;", (cls.test_user_id,))
        db.execute_non_query("DELETE FROM researchers WHERE user_id = %s OR email = %s;", (cls.test_user_id, cls.test_email))
        db.execute_non_query("DELETE FROM users WHERE id = %s;", (cls.test_user_id,))

    def setUp(self):
        # Clear tokens for test user before each test
        db.execute_non_query("DELETE FROM password_resets WHERE user_id = %s;", (self.test_user_id,))

    def test_1_request_token_valid_user(self):
        """Requesting reset token generates a secure hashed token in database."""
        res = AuthService.request_password_reset(self.test_email)
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["dev_token"])
        token = res["dev_token"]

        # Verify token is NOT stored in plain text in database
        plain_in_db = db.execute_query(
            "SELECT id FROM password_resets WHERE token_hash = %s;",
            (token,)
        )
        self.assertEqual(len(plain_in_db), 0, "Plain text token must NEVER be stored in database!")

        # Verify hashed token IS stored in database
        hashed = AuthService.hash_token(token)
        token_rows = db.execute_query(
            "SELECT id, user_id, expires_at, used_at FROM password_resets WHERE token_hash = %s;",
            (hashed,)
        )
        self.assertEqual(len(token_rows), 1)
        self.assertEqual(token_rows[0]["user_id"], self.test_user_id)
        self.assertIsNone(token_rows[0]["used_at"])

    def test_2_request_token_unknown_email(self):
        """Unknown email returns generic response without revealing user non-existence."""
        res = AuthService.request_password_reset("nonexistent_scholar_9999@campusx.edu")
        self.assertTrue(res["success"])
        self.assertIsNone(res["dev_token"])

    def test_3_invalid_token_rejected(self):
        """Invalid or unrecognized token must be rejected."""
        ok, msg = AuthService.reset_password("FAKE1234", self.new_password, self.new_password)
        self.assertFalse(ok)
        self.assertIn("Invalid or unrecognized", msg)

    def test_4_password_mismatch_rejected(self):
        """Mismatched passwords must be rejected without modifying user record."""
        res = AuthService.request_password_reset(self.test_email)
        token = res["dev_token"]

        ok, msg = AuthService.reset_password(token, self.new_password, "MismatchPass@123")
        self.assertFalse(ok)
        self.assertIn("do not match", msg)

        # Confirm old password still works
        login_ok, _, _ = AuthService.login(self.test_email, self.original_password)
        self.assertTrue(login_ok, "Old password should still be active after failed mismatch reset.")

    def test_5_short_password_rejected(self):
        """Passwords shorter than 6 characters must be rejected."""
        res = AuthService.request_password_reset(self.test_email)
        token = res["dev_token"]

        ok, msg = AuthService.reset_password(token, "123", "123")
        self.assertFalse(ok)
        self.assertIn("at least 6 characters", msg)

    def test_6_expired_token_rejected(self):
        """Expired tokens must be rejected."""
        token = "EXPIRED8"
        token_hash = AuthService.hash_token(token)
        db.execute_non_query(
            """
            INSERT INTO password_resets (user_id, token_hash, expires_at)
            VALUES (%s, %s, NOW() - INTERVAL 5 MINUTE);
            """,
            (self.test_user_id, token_hash)
        )

        ok, msg = AuthService.reset_password(token, self.new_password, self.new_password)
        self.assertFalse(ok)
        self.assertIn("expired", msg.lower())

    def test_7_successful_reset_and_login_flow(self):
        """Complete successful password reset and verify new password can authenticate."""
        # 1. Request token
        res = AuthService.request_password_reset(self.test_email)
        token = res["dev_token"]
        self.assertIsNotNone(token)

        # 2. Reset password
        ok, msg = AuthService.reset_password(token, self.new_password, self.new_password)
        self.assertTrue(ok)
        self.assertIn("successful", msg.lower())

        # 3. Old password must now fail
        old_login_ok, old_msg, _ = AuthService.login(self.test_email, self.original_password)
        self.assertFalse(old_login_ok, "Old password must no longer authenticate after reset!")

        # 4. New password must authenticate successfully
        new_login_ok, new_msg, user = AuthService.login(self.test_email, self.new_password)
        self.assertTrue(new_login_ok)
        self.assertEqual(user["email"], self.test_email)

        # 5. Token replay must fail (single-use validation)
        replay_ok, replay_msg = AuthService.reset_password(token, "AnotherPass@999", "AnotherPass@999")
        self.assertFalse(replay_ok)
        self.assertIn("already been used", replay_msg)

    def test_8_fastapi_endpoints(self):
        """Test FastAPI endpoint handlers directly."""
        # 1. Forgot password endpoint
        req1 = ForgotPasswordRequest(email=self.test_email)
        res1 = forgot_password_endpoint(req1)
        self.assertTrue(res1["success"])
        token = res1.get("dev_token")
        self.assertIsNotNone(token)

        # 2. Reset password endpoint with invalid token
        req2 = ResetPasswordRequest(
            token="BADTOKEN",
            new_password="EndpointPass@2026",
            confirm_password="EndpointPass@2026"
        )
        with self.assertRaises(HTTPException) as ctx:
            reset_password_endpoint(req2)
        self.assertEqual(ctx.exception.status_code, 400)

        # 3. Reset password endpoint with valid token
        req3 = ResetPasswordRequest(
            token=token,
            new_password="EndpointPass@2026",
            confirm_password="EndpointPass@2026"
        )
        res3 = reset_password_endpoint(req3)
        self.assertTrue(res3["success"])

        # 4. Authenticate using new password
        ok, _, user = AuthService.login(self.test_email, "EndpointPass@2026")
        self.assertTrue(ok)
        self.assertEqual(user["email"], self.test_email)

    def test_9_valid_plus_sign_email_accepted(self):
        """Valid emails with a plus tag should be accepted by registration and login."""
        email = "plus.sign+campusx@campusx.edu"
        db.execute_non_query("DELETE FROM users WHERE email = %s;", (email,))

        ok, msg, user = AuthService.register(
            full_name="Plus Sign User",
            email=email,
            password="PlusTag@123",
            role="Student"
        )
        self.assertTrue(ok, msg)
        self.assertEqual(user["email"], email)

        login_ok, login_msg, login_user = AuthService.login(email, "PlusTag@123")
        self.assertTrue(login_ok, login_msg)
        self.assertEqual(login_user["email"], email)

        db.execute_non_query("DELETE FROM users WHERE email = %s;", (email,))

    def test_10_ui_components(self):
        """Verify UI widgets for LoginView forgot password link and ForgotPasswordView."""
        root = ctk.CTk()

        # 1. LoginView has Forgot Password option
        forgot_clicked = []
        lv = LoginView(
            root,
            on_login_success=lambda u: None,
            on_go_to_register=lambda: None,
            on_back_to_landing=lambda: None,
            on_go_to_forgot_password=lambda: forgot_clicked.append(True)
        )
        lv.pack()
        root.update()

        # Simulate clicking Forgot Password link
        lv._handle_forgot_password()
        self.assertEqual(len(forgot_clicked), 1, "Forgot Password link should trigger callback.")

        # 2. ForgotPasswordView widgets
        login_clicked = []
        landing_clicked = []
        fp = ForgotPasswordView(
            root,
            on_go_to_login=lambda: login_clicked.append(True),
            on_back_to_landing=lambda: landing_clicked.append(True)
        )
        fp.pack()
        root.update()

        # Verify entry widgets and placeholders
        self.assertEqual(fp.email_entry._placeholder_text, "Enter your registered email address")
        self.assertEqual(fp.token_entry._placeholder_text, "Enter reset token (e.g. A8B2C4D1)")
        self.assertEqual(fp.new_pwd_entry._placeholder_text, "New password (min. 6 characters)")
        self.assertEqual(fp.confirm_pwd_entry._placeholder_text, "Confirm new password")

        # Verify password masking
        self.assertEqual(fp.new_pwd_entry._entry.cget("show"), "")  # while placeholder active
        fp.new_pwd_entry._entry.focus_set()
        root.update()
        self.assertEqual(fp.new_pwd_entry._entry.cget("show"), "●")  # after focus

        root.destroy()


if __name__ == "__main__":
    unittest.main()
