"""
CAMPUSX — Discover People Behind the Work System
Login View: Clean, Professional Academic Authentication
"""

from typing import Optional
from pathlib import Path
import customtkinter as ctk
from config import BASE_DIR
from api_client.client import api_client, APIClientError
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    get_logo_image
)


class LoginView(ctk.CTkFrame):
    """Clean professional login page matching CAMPUSX brand identity."""

    def __init__(
        self,
        parent,
        on_login_success,
        on_go_to_register,
        on_back_to_landing,
        on_go_to_forgot_password=None,
        saved_email: Optional[str] = None
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_login_success = on_login_success
        self.on_go_to_register = on_go_to_register
        self.on_back_to_landing = on_back_to_landing
        self.on_go_to_forgot_password = on_go_to_forgot_password
        self._initial_saved_email = saved_email

        self._build_ui()

    def _build_ui(self):
        # Outer wrapper centering card
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        # Back link
        back_btn = ctk.CTkButton(
            wrapper,
            text="← Back to CAMPUSX Home",
            command=self.on_back_to_landing,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY,
            width=180,
            height=30
        )
        back_btn.pack(anchor="w", pady=(0, 10))

        # Card container
        card = create_card(wrapper, width=440, corner_radius=Theme.RADIUS_CARD)
        card.pack()

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=38, pady=32, fill="both")

        # Official Logo
        logo_img = get_logo_image(size=(200, 52))
        if logo_img:
            logo_lbl = ctk.CTkLabel(inner, image=logo_img, text="")
            logo_lbl.pack(pady=(0, 14))
        else:
            title = ctk.CTkLabel(
                inner,
                text="CAMPUSX",
                font=(Theme.FONT_FAMILY, 24, "bold"),
                text_color=Theme.NAVY
            )
            title.pack(pady=(0, 6))

        subtitle = ctk.CTkLabel(
            inner,
            text="Sign in to your campus research account",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        subtitle.pack(pady=(0, 20))

        # Error display label (hidden by default)
        self.error_label = ctk.CTkLabel(
            inner,
            text="",
            text_color=Theme.DANGER,
            font=Theme.FONT_CAPTION,
            wraplength=340
        )
        self.error_label.pack(pady=(0, 6))

        # Email Field
        email_lbl = ctk.CTkLabel(inner, text="Email Address", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT)
        email_lbl.pack(anchor="w", pady=(4, 4))
        self.email_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Enter your email address",
            width=360,
            height=38,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.WHITE
        )
        self.email_entry.pack(pady=(0, 14))

        # Ensure clicking anywhere on the email entry focuses it cleanly
        if hasattr(self.email_entry, "_canvas"):
            self.email_entry._canvas.bind("<Button-1>", lambda event: self.email_entry.after_idle(self.email_entry._entry.focus_set))

        # Password Field
        pass_lbl = ctk.CTkLabel(inner, text="Password", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT)
        pass_lbl.pack(anchor="w", pady=(4, 4))
        self.password_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Enter your password",
            show="●",
            width=360,
            height=38,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.WHITE
        )
        self.password_entry.pack(pady=(0, 12))

        # Ensure clicking anywhere on the password entry focuses it cleanly
        if hasattr(self.password_entry, "_canvas"):
            self.password_entry._canvas.bind("<Button-1>", lambda event: self.password_entry.after_idle(self.password_entry._entry.focus_set))

        # Options Row: Remember Me Checkbox (left) and Forgot Password? link (right)
        options_row = ctk.CTkFrame(inner, fg_color="transparent")
        options_row.pack(fill="x", pady=(0, 18))

        self.remember_var = ctk.BooleanVar(value=True)
        rem_check = ctk.CTkCheckBox(
            options_row,
            text="Remember me",
            variable=self.remember_var,
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT,
            fg_color=Theme.ACADEMIC_BLUE,
            hover_color=Theme.NAVY,
            corner_radius=4,
            checkbox_width=18,
            checkbox_height=18
        )
        rem_check.pack(side="left")

        forgot_btn = ctk.CTkButton(
            options_row,
            text="Forgot Password?",
            command=self._handle_forgot_password,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=120,
            height=24
        )
        forgot_btn.pack(side="right")

        # Populate email only if intentionally saved with Remember Me
        persisted_email = self._initial_saved_email or self._load_saved_email()
        if persisted_email:
            self.email_entry.insert(0, persisted_email)
            self.remember_var.set(True)

        # Login Button
        self.login_btn = create_primary_button(
            inner,
            text="Sign In",
            command=self._handle_login,
            width=360,
            height=40
        )
        self.login_btn.pack(pady=(0, 16))

        # Link to Register
        reg_box = ctk.CTkFrame(inner, fg_color="transparent")
        reg_box.pack()

        no_acc_lbl = ctk.CTkLabel(
            reg_box,
            text="Don't have an account?",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        no_acc_lbl.pack(side="left", padx=(0, 6))

        reg_link = ctk.CTkButton(
            reg_box,
            text="Register here",
            command=self.on_go_to_register,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=100,
            height=28
        )
        reg_link.pack(side="left")

        # Allow pressing Enter in password field to submit
        self.password_entry.bind("<Return>", lambda event: self._handle_login())

    def _handle_forgot_password(self):
        if self.on_go_to_forgot_password:
            self.on_go_to_forgot_password()

    def _handle_login(self):
        email = self.email_entry.get().strip()
        pwd = self.password_entry.get().strip()

        if not email or not pwd:
            self.error_label.configure(text="Please enter both email and password.")
            return

        self.error_label.configure(text="")
        self.login_btn.configure(state="disabled", text="Authenticating...")

        try:
            res = api_client.login(email, pwd)
            user = res.get("user")
            if self.remember_var.get():
                self._save_remembered_email(email)
            else:
                self._clear_remembered_email()
            self.on_login_success(user)
        except APIClientError as e:
            self.error_label.configure(text=str(e))
        except Exception as e:
            self.error_label.configure(text=f"Connection error: {str(e)}")
        finally:
            self.login_btn.configure(state="normal", text="Sign In")

    @staticmethod
    def _load_saved_email() -> Optional[str]:
        """Load intentionally saved email if Remember Me was previously used."""
        for path in (BASE_DIR / ".remembered_email", BASE_DIR / ".saved_email"):
            try:
                if path.is_file():
                    content = path.read_text(encoding="utf-8").strip()
                    if content:
                        return content
            except Exception:
                pass
        return None

    @staticmethod
    def _save_remembered_email(email: str) -> None:
        """Persist email when Remember Me is checked upon successful login."""
        try:
            (BASE_DIR / ".remembered_email").write_text(email.strip(), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _clear_remembered_email() -> None:
        """Clear persisted email when Remember Me is unchecked upon login."""
        for path in (BASE_DIR / ".remembered_email", BASE_DIR / ".saved_email"):
            try:
                if path.is_file():
                    path.unlink()
            except Exception:
                pass
