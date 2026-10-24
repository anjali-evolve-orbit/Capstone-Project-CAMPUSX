"""
CAMPUSX — Discover People Behind the Work System
Forgot Password View: Secure Academic Authentication Reset
"""

from typing import Optional
import customtkinter as ctk
from api_client.client import api_client, APIClientError
from services.auth_service import AuthService
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    get_logo_image
)


class ForgotPasswordView(ctk.CTkFrame):
    """
    Password Reset View allowing users to request a time-limited single-use token
    and securely set a new password.
    """

    def __init__(self, parent, on_go_to_login, on_back_to_landing):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_go_to_login = on_go_to_login
        self.on_back_to_landing = on_back_to_landing

        self._build_ui()

    def _build_ui(self):
        # Center outer wrapper
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # Top navigation link
        nav_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        nav_row.pack(fill="x", pady=(0, 10))

        back_to_login_btn = ctk.CTkButton(
            nav_row,
            text="← Back to Sign In",
            command=self.on_go_to_login,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY,
            width=140,
            height=28
        )
        back_to_login_btn.pack(side="left")

        # Main Card container
        card = create_card(wrapper, width=460, corner_radius=Theme.RADIUS_CARD)
        card.pack()

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=38, pady=30, fill="both")

        # Official Logo
        logo_img = get_logo_image(size=(190, 50))
        if logo_img:
            logo_lbl = ctk.CTkLabel(inner, image=logo_img, text="")
            logo_lbl.pack(pady=(0, 10))
        else:
            title = ctk.CTkLabel(
                inner,
                text="CAMPUSX",
                font=(Theme.FONT_FAMILY, 24, "bold"),
                text_color=Theme.NAVY
            )
            title.pack(pady=(0, 4))

        # Title & Subtitle
        header_lbl = ctk.CTkLabel(
            inner,
            text="Reset Account Password",
            font=(Theme.FONT_FAMILY, 18, "bold"),
            text_color=Theme.NAVY
        )
        header_lbl.pack(pady=(0, 4))

        sub_lbl = ctk.CTkLabel(
            inner,
            text="Enter your registered campus email to receive a secure reset token.",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT,
            wraplength=380
        )
        sub_lbl.pack(pady=(0, 14))

        # Message & Status Banner container
        self.message_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.message_frame.pack(fill="x", pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            self.message_frame,
            text="",
            font=Theme.FONT_CAPTION,
            wraplength=380,
            justify="left"
        )
        self.status_label.pack(fill="x")

        # =====================================================================
        # STEP 1: Request Reset Token Section
        # =====================================================================
        ctk.CTkLabel(
            inner,
            text="1. Registered Email Address",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.DARK_TEXT
        ).pack(anchor="w", pady=(2, 4))

        self.email_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Enter your registered email address",
            width=380,
            height=38,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.WHITE
        )
        self.email_entry.pack(pady=(0, 8))
        if hasattr(self.email_entry, "_canvas"):
            self.email_entry._canvas.bind("<Button-1>", lambda e: self.email_entry.after_idle(self.email_entry._entry.focus_set))

        self.request_token_btn = create_primary_button(
            inner,
            text="Request Reset Token",
            command=self._handle_request_token,
            width=380,
            height=36
        )
        self.request_token_btn.pack(pady=(0, 16))

        # Divider
        divider = ctk.CTkFrame(inner, height=1, fg_color=Theme.BORDER)
        divider.pack(fill="x", pady=(0, 16))

        # =====================================================================
        # STEP 2: Enter Token & Set New Password Section
        # =====================================================================
        ctk.CTkLabel(
            inner,
            text="2. Enter Reset Token & New Password",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.DARK_TEXT
        ).pack(anchor="w", pady=(0, 4))

        # Token Field
        self.token_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Enter reset token (e.g. A8B2C4D1)",
            width=380,
            height=38,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.WHITE
        )
        self.token_entry.pack(pady=(0, 8))
        if hasattr(self.token_entry, "_canvas"):
            self.token_entry._canvas.bind("<Button-1>", lambda e: self.token_entry.after_idle(self.token_entry._entry.focus_set))

        # New Password
        self.new_pwd_entry = ctk.CTkEntry(
            inner,
            placeholder_text="New password (min. 6 characters)",
            show="●",
            width=380,
            height=38,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.WHITE
        )
        self.new_pwd_entry.pack(pady=(0, 8))
        if hasattr(self.new_pwd_entry, "_canvas"):
            self.new_pwd_entry._canvas.bind("<Button-1>", lambda e: self.new_pwd_entry.after_idle(self.new_pwd_entry._entry.focus_set))

        # Confirm New Password
        self.confirm_pwd_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Confirm new password",
            show="●",
            width=380,
            height=38,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.WHITE
        )
        self.confirm_pwd_entry.pack(pady=(0, 14))
        if hasattr(self.confirm_pwd_entry, "_canvas"):
            self.confirm_pwd_entry._canvas.bind("<Button-1>", lambda e: self.confirm_pwd_entry.after_idle(self.confirm_pwd_entry._entry.focus_set))

        # Reset Password Submit Button
        self.reset_btn = create_primary_button(
            inner,
            text="Reset Password",
            command=self._handle_reset_password,
            width=380,
            height=38
        )
        self.reset_btn.pack(pady=(0, 12))

        # Allow Enter key in confirm field to submit reset
        self.confirm_pwd_entry.bind("<Return>", lambda event: self._handle_reset_password())

        # Success return button (hidden until successful reset)
        self.return_to_login_btn = create_secondary_button(
            inner,
            text="Return to Sign In",
            command=self.on_go_to_login,
            width=380,
            height=36
        )

    def _show_message(self, text: str, msg_type: str = "error"):
        """Display styled message in banner area."""
        if msg_type == "error":
            color = Theme.DANGER
        elif msg_type == "success":
            color = Theme.SUCCESS
        elif msg_type == "warning":
            color = "#D97706"  # Warm amber
        else:
            color = Theme.ACADEMIC_BLUE

        self.status_label.configure(text=text, text_color=color)

    def _handle_request_token(self):
        """Send password reset token request to the backend."""
        email = self.email_entry.get().strip()

        if not email:
            self._show_message("Please enter your registered email address.", "error")
            return

        if not AuthService.is_valid_email(email):
            self._show_message("Please enter a valid email address.", "error")
            return

        self._show_message("Requesting reset token...", "info")
        self.request_token_btn.configure(state="disabled", text="Sending Request...")

        try:
            res = api_client.forgot_password(email)
            message = res.get("message", "Reset request processed.")
            email_configured = res.get("email_configured", False)
            dev_token = res.get("dev_token")

            if email_configured:
                self._show_message(
                    f"✓ {message}\n"
                    f"Please check your inbox and copy the 8-character token into Step 2 below.",
                    "success"
                )
            else:
                # Email is not configured. Clearly report missing configuration.
                report_txt = f"⚠️ {message}"
                if dev_token:
                    report_txt += (
                        f"\n\n[Local Development / Test Mode]:"
                        f"\nYour generated reset token is: {dev_token}"
                        f"\n(Automatically populated in the token field below for testing)."
                    )
                    self.token_entry.delete(0, "end")
                    self.token_entry.insert(0, dev_token)
                self._show_message(report_txt, "warning")

        except APIClientError as e:
            self._show_message(str(e), "error")
        except Exception as e:
            self._show_message(f"Connection error: {str(e)}", "error")
        finally:
            self.request_token_btn.configure(state="normal", text="Request Reset Token")

    def _handle_reset_password(self):
        """Validate inputs and submit password reset with token."""
        token = self.token_entry.get().strip()
        new_pwd = self.new_pwd_entry.get()
        confirm_pwd = self.confirm_pwd_entry.get()

        if not token:
            self._show_message("Please enter the reset token received for your account.", "error")
            return

        if not new_pwd:
            self._show_message("Please enter a new password.", "error")
            return

        if len(new_pwd) < 6:
            self._show_message("Password must be at least 6 characters long.", "error")
            return

        if new_pwd != confirm_pwd:
            self._show_message("Passwords do not match. Please re-enter.", "error")
            return

        self._show_message("Resetting password...", "info")
        self.reset_btn.configure(state="disabled", text="Updating Password...")

        try:
            res = api_client.reset_password(token, new_pwd, confirm_pwd)
            success_msg = res.get("message", "Password has been successfully reset!")
            self._show_message(f"✓ {success_msg}\nYou can now sign in with your new password.", "success")

            # Disable fields to prevent duplicate resets
            self.token_entry.configure(state="disabled")
            self.new_pwd_entry.configure(state="disabled")
            self.confirm_pwd_entry.configure(state="disabled")
            self.reset_btn.pack_forget()

            # Display prominent Return to Sign In button
            self.return_to_login_btn.pack(pady=(0, 10))

        except APIClientError as e:
            self._show_message(str(e), "error")
            self.reset_btn.configure(state="normal", text="Reset Password")
        except Exception as e:
            self._show_message(f"Connection error: {str(e)}", "error")
            self.reset_btn.configure(state="normal", text="Reset Password")
