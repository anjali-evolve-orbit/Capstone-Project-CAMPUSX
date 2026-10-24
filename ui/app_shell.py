"""
CAMPUSX — Discover People Behind the Work System
App Shell: Sidebar Navigation, Top Context Bar, and Dynamic View Container
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, Optional
from ui.theme import (
    Theme,
    get_logo_image,
    get_icon_image,
    create_card,
    create_badge
)


class AppShell(ctk.CTkFrame):
    """Main desktop frame hosting the Sidebar, Top Context Bar, and Central Dynamic Content Frame."""

    def __init__(
        self,
        parent,
        current_user: Optional[Dict[str, Any]],
        on_logout: Callable[[], None],
        on_search_query: Callable[[str], None],
        on_navigate: Optional[Callable[[str], None]] = None
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.user = current_user or {}
        self.on_logout = on_logout
        self.on_search_query = on_search_query
        self.on_navigate = on_navigate

        self.current_tab = "dashboard"
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}

        self._build_layout()

    def _build_layout(self):
        # 1. Left Sidebar
        self.sidebar = ctk.CTkFrame(self, fg_color=Theme.WHITE, width=240, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # 2. Right Main Area
        self.main_container = ctk.CTkFrame(self, fg_color=Theme.SOFT_BG)
        self.main_container.pack(side="right", fill="both", expand=True)

        # 2a. Top Context Bar
        self._build_topbar()

        # 2b. Central Dynamic Content Frame
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color=Theme.SOFT_BG)
        self.content_frame.pack(fill="both", expand=True)

    def _build_sidebar(self):
        # Top Logo
        logo_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_box.pack(fill="x", padx=16, pady=(18, 20))

        logo_img = get_logo_image(size=(180, 48))
        if logo_img:
            lbl = ctk.CTkLabel(logo_box, image=logo_img, text="")
            lbl.pack(anchor="w")
        else:
            lbl = ctk.CTkLabel(
                logo_box,
                text="CAMPUSX",
                font=(Theme.FONT_FAMILY, 20, "bold"),
                text_color=Theme.NAVY
            )
            lbl.pack(anchor="w")

        # Navigation Items
        nav_items = [
            ("dashboard", "Dashboard", "📊"),
            ("researchers", "Researchers", "👥"),
            ("papers", "Papers", "📄"),
            ("research_areas", "Research Areas", "🔬"),
            ("communities", "Communities", "🏛️"),
            ("network", "Network", "🕸️"),
            ("recommendations", "Recommendations", "✨")
        ]
        # Insert My Profile after main navs
        nav_items.insert(3, ("my_profile", "My Profile", "👤"))

        self.nav_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_box.pack(fill="x", padx=12)

        for tab_id, label, icon in nav_items:
            btn = ctk.CTkButton(
                self.nav_box,
                text=f"  {icon}  {label}",
                anchor="w",
                font=(Theme.FONT_FAMILY, 12, "bold"),
                fg_color="transparent",
                hover_color=Theme.MUTED_BG,
                text_color=Theme.SECONDARY_TEXT,
                corner_radius=8,
                height=40,
                command=lambda tid=tab_id: self._on_nav_clicked(tid)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[tab_id] = btn

        # Bottom Area: Settings and Logout
        bottom_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_box.pack(side="bottom", fill="x", padx=12, pady=16)

        settings_btn = ctk.CTkButton(
            bottom_box,
            text="  ⚙️  Settings",
            anchor="w",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.SECONDARY_TEXT,
            corner_radius=8,
            height=36,
            command=lambda: self._on_nav_clicked("settings")
        )
        settings_btn.pack(fill="x", pady=2)
        self.nav_buttons["settings"] = settings_btn

        logout_btn = ctk.CTkButton(
            bottom_box,
            text="  🚪  Logout",
            anchor="w",
            font=Theme.FONT_BODY_BOLD,
            fg_color="transparent",
            hover_color="#FEE2E2",
            text_color=Theme.DANGER,
            corner_radius=8,
            height=36,
            command=self.on_logout
        )
        logout_btn.pack(fill="x", pady=2)

    def _build_topbar(self):
        """Top bar with search input, institution context, and user profile."""
        topbar = ctk.CTkFrame(self.main_container, fg_color=Theme.WHITE, height=62, corner_radius=0)
        topbar.pack(fill="x", padx=0, pady=(0, 2))
        topbar.pack_propagate(False)

        inner = ctk.CTkFrame(topbar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25)

        # Left: Search Bar
        search_frame = ctk.CTkFrame(inner, fg_color="transparent")
        search_frame.pack(side="left", pady=12)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search CAMPUSX across researchers, papers, areas...",
            width=380,
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.SOFT_BG
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._handle_search())

        search_btn = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self._handle_search,
            width=70,
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE,
            hover_color=Theme.NAVY,
            font=Theme.FONT_BODY_BOLD
        )
        search_btn.pack(side="left")

        # Right: Academic Context Badge & User Profile
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.pack(side="right", pady=12)

        inst_name = self.user.get("institution_name") or self.user.get("custom_institution") or "St. John Campus"
        dept_name = self.user.get("department_name") or self.user.get("custom_department") or "General"

        context_badge = create_badge(
            right_frame,
            text=f"🏛️ {inst_name} · {dept_name}",
            bg_color="#EBF4FF",
            text_color=Theme.ACADEMIC_BLUE
        )
        context_badge.pack(side="left", padx=(0, 14))

        # Pending connection requests badge in top bar
        req_count = 0
        try:
            uid = self.user.get("id")
            if uid:
                res = api_client.get_researcher_by_user(uid)
                rid = res.get("id") if res else None
                if rid:
                    pending = api_client.get_received_connection_requests(rid, status="PENDING")
                    req_count = len(pending) if isinstance(pending, list) else 0
        except Exception:
            req_count = 0

        if req_count > 0:
            req_btn = ctk.CTkButton(
                right_frame,
                text=f"🔔 {req_count} Request{'s' if req_count != 1 else ''}",
                fg_color="#FEF3C7",
                hover_color="#FDE68A",
                text_color="#B45309",
                font=(Theme.FONT_FAMILY, 11, "bold"),
                height=32,
                corner_radius=16,
                command=lambda: self._on_nav_clicked("my_profile")
            )
            req_btn.pack(side="left", padx=(0, 14))

        # Profile Pill (clickable to navigate to My Profile)
        user_name = self.user.get("full_name", "User")
        initials = "".join([w[0] for w in user_name.split() if w])[:2]

        prof_box = ctk.CTkFrame(right_frame, fg_color=Theme.MUTED_BG, corner_radius=18, height=36, cursor="hand2")
        prof_box.pack(side="left")

        av = ctk.CTkLabel(
            prof_box,
            text=initials,
            font=(Theme.FONT_FAMILY, 11, "bold"),
            fg_color=Theme.ACADEMIC_BLUE,
            text_color=Theme.WHITE,
            corner_radius=16,
            width=28,
            height=28
        )
        av.pack(side="left", padx=(4, 6), pady=4)

        u_lbl = ctk.CTkLabel(
            prof_box,
            text=user_name,
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.NAVY
        )
        u_lbl.pack(side="left", padx=(0, 12))

        prof_box.bind("<Button-1>", lambda e: self._on_nav_clicked("my_profile"))
        u_lbl.bind("<Button-1>", lambda e: self._on_nav_clicked("my_profile"))
        av.bind("<Button-1>", lambda e: self._on_nav_clicked("my_profile"))

    def _handle_search(self):
        query = self.search_entry.get().strip()
        if query:
            self.on_search_query(query)

    def _on_nav_clicked(self, tab_id: str):
        self.set_active_tab(tab_id)
        if self.on_navigate:
            self.on_navigate(tab_id)

    def set_active_tab(self, tab_id: str):
        """Update active button highlight in sidebar."""
        self.current_tab = tab_id
        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color="#EEF2FF",
                    text_color=Theme.ACADEMIC_BLUE
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=Theme.SECONDARY_TEXT
                )
