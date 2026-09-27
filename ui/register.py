"""
CAMPUSX — Discover People Behind the Work System
Registration View: Dynamic Hierarchy (Campus -> Institution -> Department), "Other" Option Support
"""

import customtkinter as ctk
from typing import Any, Dict, List, Optional
from api_client.client import api_client, APIClientError
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    get_logo_image,
    enable_mousewheel
)


class RegisterView(ctk.CTkScrollableFrame):
    """User registration flow with dynamic dropdowns and custom institution/department handling."""

    def __init__(self, parent, on_register_success, on_go_to_login, on_back_to_landing):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        enable_mousewheel(self)
        self.on_register_success = on_register_success
        self.on_go_to_login = on_go_to_login
        self.on_back_to_landing = on_back_to_landing

        self.campuses: List[Dict[str, Any]] = []
        self.institutions: List[Dict[str, Any]] = []
        self.departments: List[Dict[str, Any]] = []

        self._load_metadata()
        self._build_ui()

    def _load_metadata(self):
        try:
            self.campuses = api_client.get_campuses()
            self.institutions = api_client.get_institutions()
        except Exception:
            self.campuses = [{"id": 1, "name": "St. John Technical & Educational Campus"}]
            self.institutions = [{"id": 1, "name": "St. John College of Engineering & Management"}]

    def _build_ui(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(pady=30, padx=20)

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
        back_btn.pack(anchor="w", pady=(0, 8))

        card = create_card(wrapper, width=540, corner_radius=Theme.RADIUS_CARD)
        card.pack()

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=30, fill="both")

        # Official Logo
        logo_img = get_logo_image(size=(190, 50))
        if logo_img:
            logo_lbl = ctk.CTkLabel(inner, image=logo_img, text="")
            logo_lbl.pack(pady=(0, 10))
        else:
            logo_lbl = ctk.CTkLabel(
                inner,
                text="CAMPUSX",
                font=(Theme.FONT_FAMILY, 22, "bold"),
                text_color=Theme.NAVY
            )
            logo_lbl.pack(pady=(0, 6))

        sub = ctk.CTkLabel(
            inner,
            text="Create your academic discovery account",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        sub.pack(pady=(0, 16))

        # Status / Error Label
        self.error_label = ctk.CTkLabel(
            inner,
            text="",
            text_color=Theme.DANGER,
            font=Theme.FONT_CAPTION,
            wraplength=420
        )
        self.error_label.pack(pady=(0, 6))

        # 1. Full Name
        ctk.CTkLabel(inner, text="Full Name", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.name_entry = ctk.CTkEntry(inner, placeholder_text="e.g. Anjali Patel", width=420, height=36, corner_radius=Theme.RADIUS_INPUT)
        self.name_entry.pack(pady=(0, 10))

        # 2. Email Address
        ctk.CTkLabel(inner, text="Campus / Institutional Email", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.email_entry = ctk.CTkEntry(inner, placeholder_text="e.g. anjali.patel@campusx.edu", width=420, height=36, corner_radius=Theme.RADIUS_INPUT)
        self.email_entry.pack(pady=(0, 10))

        # 3. Password & Confirm Password (2-column layout)
        pwd_box = ctk.CTkFrame(inner, fg_color="transparent")
        pwd_box.pack(fill="x", pady=(0, 10))
        pwd_box.columnconfigure((0, 1), weight=1)

        p1_box = ctk.CTkFrame(pwd_box, fg_color="transparent")
        p1_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(p1_box, text="Password", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.pass1_entry = ctk.CTkEntry(p1_box, show="●", placeholder_text="Min. 6 chars", width=200, height=36, corner_radius=Theme.RADIUS_INPUT)
        self.pass1_entry.pack(fill="x")

        p2_box = ctk.CTkFrame(pwd_box, fg_color="transparent")
        p2_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(p2_box, text="Confirm Password", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.pass2_entry = ctk.CTkEntry(p2_box, show="●", placeholder_text="Re-enter password", width=200, height=36, corner_radius=Theme.RADIUS_INPUT)
        self.pass2_entry.pack(fill="x")

        # 4. Role Selection
        ctk.CTkLabel(inner, text="Academic Role", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.role_var = ctk.StringVar(value="Student")
        self.role_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.role_var,
            values=["Student", "Researcher", "Faculty", "Other"],
            width=420,
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE
        )
        self.role_menu.pack(pady=(0, 10))

        # 5. Campus Selection
        ctk.CTkLabel(inner, text="Campus Ecosystem", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        campus_names = [c["name"] for c in self.campuses] or ["St. John Technical & Educational Campus"]
        self.campus_var = ctk.StringVar(value=campus_names[0])
        self.campus_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.campus_var,
            values=campus_names,
            width=420,
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE
        )
        self.campus_menu.pack(pady=(0, 10))

        # 6. Institution / College Dropdown
        ctk.CTkLabel(inner, text="Institution / College", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        inst_options = [i["name"] for i in self.institutions if not i.get("is_custom")]
        inst_options.append("Other Institution")
        self.inst_var = ctk.StringVar(value=inst_options[0] if inst_options else "Other Institution")
        self.inst_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.inst_var,
            values=inst_options,
            command=self._on_institution_changed,
            width=420,
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE
        )
        self.inst_menu.pack(pady=(0, 10))

        # Custom Institution Input (shown only if 'Other' is selected)
        self.custom_inst_frame = ctk.CTkFrame(inner, fg_color="transparent")
        ctk.CTkLabel(
            self.custom_inst_frame,
            text="Enter Institution Name",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.PURPLE
        ).pack(anchor="w", pady=(2, 2))
        self.custom_inst_entry = ctk.CTkEntry(
            self.custom_inst_frame,
            placeholder_text="e.g. St. Francis Institute of Technology",
            width=420,
            height=36,
            corner_radius=Theme.RADIUS_INPUT
        )
        self.custom_inst_entry.pack(pady=(0, 10))

        # 7. Department / Program Dropdown
        ctk.CTkLabel(inner, text="Department / Program", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.dept_var = ctk.StringVar(value="Loading...")
        self.dept_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.dept_var,
            values=["Loading..."],
            command=self._on_department_changed,
            width=420,
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE
        )
        self.dept_menu.pack(pady=(0, 10))

        # Custom Department Input (shown only if 'Other' is selected)
        self.custom_dept_frame = ctk.CTkFrame(inner, fg_color="transparent")
        ctk.CTkLabel(
            self.custom_dept_frame,
            text="Enter Department / Program",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.PURPLE
        ).pack(anchor="w", pady=(2, 2))
        self.custom_dept_entry = ctk.CTkEntry(
            self.custom_dept_frame,
            placeholder_text="e.g. Biomedical Instrumentation",
            width=420,
            height=36,
            corner_radius=Theme.RADIUS_INPUT
        )
        self.custom_dept_entry.pack(pady=(0, 10))

        # Populate departments for initial institution
        self._on_institution_changed(self.inst_var.get())

        # Register CTA Button
        self.register_btn = create_primary_button(
            inner,
            text="Complete Registration",
            command=self._handle_register,
            width=420,
            height=42
        )
        self.register_btn.pack(pady=(10, 14))

        # Link to Login
        foot_box = ctk.CTkFrame(inner, fg_color="transparent")
        foot_box.pack()

        ctk.CTkLabel(foot_box, text="Already have an account?", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            foot_box,
            text="Login",
            command=self.on_go_to_login,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=60,
            height=28
        ).pack(side="left")

    def _on_institution_changed(self, selected_name: str):
        """Dynamic department update when institution changes; reveals 'Other' text input if needed."""
        if selected_name == "Other Institution":
            self.custom_inst_frame.pack(fill="x", before=self.dept_menu)
            dept_options = ["Other Department / Program"]
            self.dept_menu.configure(values=dept_options)
            self.dept_var.set(dept_options[0])
            self._on_department_changed("Other Department / Program")
        else:
            self.custom_inst_frame.pack_forget()

            # Find selected institution ID
            inst_obj = next((i for i in self.institutions if i["name"] == selected_name), None)
            if inst_obj:
                try:
                    depts = api_client.get_departments(institution_id=inst_obj["id"])
                    dept_options = [d["name"] for d in depts if not d.get("is_custom")]
                    dept_options.append("Other Department / Program")
                except Exception:
                    dept_options = ["Computer Engineering", "Information Technology", "Other Department / Program"]
            else:
                dept_options = ["Other Department / Program"]

            self.dept_menu.configure(values=dept_options)
            self.dept_var.set(dept_options[0])
            self._on_department_changed(dept_options[0])

    def _on_department_changed(self, selected_dept: str):
        """Reveal custom department text field if 'Other' is chosen."""
        if "Other" in selected_dept:
            self.custom_dept_frame.pack(fill="x", after=self.dept_menu)
        else:
            self.custom_dept_frame.pack_forget()

    def _handle_register(self):
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        p1 = self.pass1_entry.get().strip()
        p2 = self.pass2_entry.get().strip()
        role = self.role_var.get()
        campus_name = self.campus_var.get()
        inst_name = self.inst_var.get()
        dept_name = self.dept_var.get()

        # Validations
        if not name:
            self.error_label.configure(text="Please enter your full name.")
            return
        if not email:
            self.error_label.configure(text="Please enter your email address.")
            return
        if len(p1) < 6:
            self.error_label.configure(text="Password must be at least 6 characters.")
            return
        if p1 != p2:
            self.error_label.configure(text="Passwords do not match. Please re-enter.")
            return

        # Resolve Campus ID
        campus_obj = next((c for c in self.campuses if c["name"] == campus_name), None)
        campus_id = campus_obj["id"] if campus_obj else 1

        # Resolve Institution
        custom_inst_val = None
        if inst_name == "Other Institution":
            custom_inst_val = self.custom_inst_entry.get().strip()
            if not custom_inst_val:
                self.error_label.configure(text="Please enter your Institution name.")
                return
            inst_id = 999
        else:
            inst_obj = next((i for i in self.institutions if i["name"] == inst_name), None)
            inst_id = inst_obj["id"] if inst_obj else 1

        # Resolve Department
        custom_dept_val = None
        if "Other" in dept_name:
            custom_dept_val = self.custom_dept_entry.get().strip()
            if not custom_dept_val:
                self.error_label.configure(text="Please enter your Department / Program name.")
                return
            dept_id = 999
        else:
            depts = api_client.get_departments(institution_id=inst_id)
            dept_obj = next((d for d in depts if d["name"] == dept_name), None)
            dept_id = dept_obj["id"] if dept_obj else 1

        self.error_label.configure(text="")
        self.register_btn.configure(state="disabled", text="Creating Account...")

        try:
            res = api_client.register(
                full_name=name,
                email=email,
                password=p1,
                role=role,
                campus_id=campus_id,
                institution_id=inst_id,
                department_id=dept_id,
                custom_institution=custom_inst_val,
                custom_department=custom_dept_val
            )
            user = res.get("user")
            self.on_register_success(user)
        except APIClientError as e:
            self.error_label.configure(text=str(e))
        except Exception as e:
            self.error_label.configure(text=f"Registration failed: {str(e)}")
        finally:
            self.register_btn.configure(state="normal", text="Complete Registration")
