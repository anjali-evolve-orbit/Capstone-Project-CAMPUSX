"""
CAMPUSX — Discover People Behind the Work System
Login View: Clean, Professional Academic Authentication
"""

import customtkinter as ctk
from api_client.client import api_client, APIClientError
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    get_logo_image
)


class LoginView(ctk.CTkFrame):
    """Clean professional login page matching CAMPUSX brand identity."""

    def __init__(self, parent, on_login_success, on_go_to_register, on_back_to_landing):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_login_success = on_login_success
        self.on_go_to_register = on_go_to_register
        self.on_back_to_landing = on_back_to_landing

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
            placeholder_text="e.g. student@campusx.edu",
            width=360,
            height=38,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.WHITE
        )
        self.email_entry.pack(pady=(0, 14))
        self.email_entry.insert(0, "student@campusx.edu")  # Convenient demo default

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
        self.password_entry.insert(0, "CampusX@2026")  # Convenient demo default

        # Remember Me Checkbox
        self.remember_var = ctk.BooleanVar(value=True)
        rem_check = ctk.CTkCheckBox(
            inner,
            text="Remember me on this campus device",
            variable=self.remember_var,
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT,
            fg_color=Theme.ACADEMIC_BLUE,
            hover_color=Theme.NAVY,
            corner_radius=4,
            checkbox_width=18,
            checkbox_height=18
        )
        rem_check.pack(anchor="w", pady=(0, 20))

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
            self.on_login_success(user)
        except APIClientError as e:
            self.error_label.configure(text=str(e))
        except Exception as e:
            self.error_label.configure(text=f"Connection error: {str(e)}")
        finally:
            self.login_btn.configure(state="normal", text="Sign In")
