"""
CAMPUSX — Discover People Behind the Work System
Settings View: Account Settings, Database & API Server Diagnostics
"""

import customtkinter as ctk
from typing import Any, Dict, Optional
from config import PROJECT_NAME, TAGLINE, APP_VERSION, DB_HOST, DB_PORT, DB_NAME, DB_USER
from api_client.client import api_client
from ui.theme import Theme, create_card, create_badge


class SettingsView(ctk.CTkScrollableFrame):
    """Platform settings and technical status information."""

    def __init__(self, parent, current_user: Optional[Dict[str, Any]]):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.user = current_user or {}
        self._build_ui()

    def _build_ui(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(head, text="Account & Platform Settings", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(side="left")

        # 1. User Profile Details
        user_card = create_card(self)
        user_card.pack(fill="x", padx=25, pady=(0, 15))

        u_inner = ctk.CTkFrame(user_card, fg_color="transparent")
        u_inner.pack(fill="both", expand=True, padx=22, pady=18)

        ctk.CTkLabel(u_inner, text="User Account Information", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 10))

        details = [
            ("Full Name", self.user.get("full_name", "N/A")),
            ("Email", self.user.get("email", "N/A")),
            ("Academic Role", self.user.get("role", "Student")),
            ("Institution", self.user.get("institution_name") or self.user.get("custom_institution") or "St. John Campus"),
            ("Department", self.user.get("department_name") or self.user.get("custom_department") or "N/A")
        ]

        for k, v in details:
            row = ctk.CTkFrame(u_inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{k}:", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT, width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(v), font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(side="left")

        # 2. System Architecture & Technical Diagnostics Card
        sys_card = create_card(self)
        sys_card.pack(fill="x", padx=25, pady=(0, 20))

        s_inner = ctk.CTkFrame(sys_card, fg_color="transparent")
        s_inner.pack(fill="both", expand=True, padx=22, pady=18)

        ctk.CTkLabel(s_inner, text="Technical Architecture & Connectivity", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 10))

        healthy, msg = api_client.check_health()
        status_txt = "ONLINE (Connected)" if healthy else "OFFLINE"
        status_bg = "#DCFCE7" if healthy else "#FEE2E2"
        status_fg = "#15803D" if healthy else Theme.DANGER

        diag = [
            ("System Identity", f"{PROJECT_NAME} — {TAGLINE}"),
            ("Application Version", APP_VERSION),
            ("Database Engine", f"MySQL 8.0 ({DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME})"),
            ("Database Mode", "MySQL Exclusive (Direct Connection Pooling)"),
            ("Data Structures", "Graph ADT, Breadth-First Search (BFS), Depth-First Search (DFS)"),
            ("Frontend UI", "Python CustomTkinter Desktop Client"),
            ("Backend Architecture", "FastAPI REST API (JSON / HTTP)")
        ]

        for label, val in diag:
            row = ctk.CTkFrame(s_inner, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"{label}:", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT, width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(val), font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(side="left")

        status_row = ctk.CTkFrame(s_inner, fg_color="transparent")
        status_row.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(status_row, text="API Server Status:", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT, width=180, anchor="w").pack(side="left")
        create_badge(status_row, text=status_txt, bg_color=status_bg, text_color=status_fg).pack(side="left")
