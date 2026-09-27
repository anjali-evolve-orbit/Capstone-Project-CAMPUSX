"""
CAMPUSX — Discover People Behind the Work System
Dashboard View: Academic Summary Metrics, Featured Areas, Recent Papers, and Researcher Highlights
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, Optional
from api_client.client import api_client
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge
)


class DashboardView(ctk.CTkScrollableFrame):
    """Modern Academic Dashboard displaying platform intelligence, statistics, and highlights."""

    def __init__(
        self,
        parent,
        current_user: Optional[Dict[str, Any]],
        on_navigate: Callable[[str, Optional[int]], None]
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.user = current_user or {}
        self.on_navigate = on_navigate

        self.stats_data: Dict[str, Any] = {}
        self.recommendations: list = []

        self._load_data()
        self._build_welcome()
        self._build_stat_cards()
        self._build_featured_areas()
        self._build_recent_papers()
        self._build_researcher_highlights()
        self._build_recommendations_preview()

    def _load_data(self):
        try:
            self.stats_data = api_client.get_dashboard_stats()
        except Exception:
            self.stats_data = {
                "counts": {"researchers": 0, "papers": 0, "areas": 0, "communities": 0},
                "featured_areas": [],
                "recent_papers": [],
                "highlights": []
            }

        try:
            interests = []
            if self.user.get("id"):
                researcher = api_client.get_researcher_by_user(self.user["id"])
                interests = [a.get("name") for a in researcher.get("areas", []) if a.get("name")][:4]
            if not interests:
                interests = ["Artificial Intelligence", "Machine Learning"]
            self.recommendations = api_client.get_recommendations(interests=interests, limit=3)
        except Exception:
            self.recommendations = []

    def _build_welcome(self):
        """Personalized welcome hero card."""
        card = create_card(self, fg_color=Theme.WHITE)
        card.pack(fill="x", padx=25, pady=(20, 15))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=25, pady=20)

        # Left welcome info
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        user_name = self.user.get("full_name", "Academic Scholar")
        role = self.user.get("role", "Student")
        dept = self.user.get("department_name") or self.user.get("custom_department") or "Academic Department"
        inst = self.user.get("institution_name") or self.user.get("custom_institution") or "Campus Institute"

        welcome_lbl = ctk.CTkLabel(
            info_frame,
            text=f"Welcome to CAMPUSX, {user_name} 👋",
            font=Theme.FONT_TITLE,
            text_color=Theme.NAVY
        )
        welcome_lbl.pack(anchor="w", pady=(0, 4))

        sub_lbl = ctk.CTkLabel(
            info_frame,
            text=f"Affiliation: {dept} · {inst}  |  Role: {role}",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        sub_lbl.pack(anchor="w")

        # Right quick CTA
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")

        explore_net_btn = create_primary_button(
            btn_frame,
            text="Explore Graph Network  🕸",
            command=lambda: self.on_navigate("network", None),
            width=190,
            height=38
        )
        explore_net_btn.pack(pady=4)

    def _build_stat_cards(self):
        """4 Statistics cards (Researchers, Papers, Research Areas, Communities)."""
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="x", padx=25, pady=(0, 15))
        grid_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        counts = self.stats_data.get("counts", {})
        stat_configs = [
            ("Researchers", counts.get("researchers", 0), "👥", Theme.ACADEMIC_BLUE, "#EBF4FF", "researchers"),
            ("Research Papers", counts.get("papers", 0), "📄", Theme.PURPLE, "#F3F0FF", "papers"),
            ("Research Areas", counts.get("areas", 0), "🔬", Theme.CYAN, "#E6FFFA", "research_areas"),
            ("Communities", counts.get("communities", 0), "🏛️", Theme.NAVY, "#F1F5F9", "communities")
        ]

        for idx, (label, count, icon, fg_accent, bg_accent, nav_target) in enumerate(stat_configs):
            card = create_card(grid_frame)
            card.grid(row=0, column=idx, padx=6, sticky="nsew")

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="both", expand=True, padx=16, pady=16)

            top_row = ctk.CTkFrame(card_inner, fg_color="transparent")
            top_row.pack(fill="x", pady=(0, 8))

            icon_lbl = ctk.CTkLabel(
                top_row,
                text=icon,
                font=(Theme.FONT_FAMILY, 18),
                fg_color=bg_accent,
                corner_radius=8,
                width=36,
                height=36
            )
            icon_lbl.pack(side="left")

            count_lbl = ctk.CTkLabel(
                card_inner,
                text=str(count),
                font=(Theme.FONT_FAMILY, 28, "bold"),
                text_color=Theme.NAVY
            )
            count_lbl.pack(anchor="w")

            lbl = ctk.CTkLabel(
                card_inner,
                text=label,
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            )
            lbl.pack(anchor="w", pady=(0, 8))

            nav_btn = ctk.CTkButton(
                card_inner,
                text="View all →",
                command=lambda target=nav_target: self.on_navigate(target, None),
                fg_color="transparent",
                hover_color=Theme.MUTED_BG,
                text_color=fg_accent,
                font=Theme.FONT_CAPTION,
                anchor="w",
                height=22
            )
            nav_btn.pack(anchor="w")

    def _build_featured_areas(self):
        """Featured Research Areas."""
        areas = self.stats_data.get("featured_areas", [])
        if not areas:
            return

        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="x", padx=25, pady=(0, 15))

        h_row = ctk.CTkFrame(box, fg_color="transparent")
        h_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(h_row, text="Featured Research Areas", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(side="left")
        ctk.CTkButton(
            h_row,
            text="Explore All Areas →",
            command=lambda: self.on_navigate("research_areas", None),
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=140,
            height=28
        ).pack(side="right")

        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1, 2, 3), weight=1, uniform="feat_areas")

        for idx, area in enumerate(areas[:4]):
            card = create_card(grid)
            card.grid(row=0, column=idx, padx=6, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=14, pady=14)

            badge = create_badge(inner, text="Research Discipline", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE)
            badge.pack(anchor="w", pady=(0, 6))

            t = ctk.CTkLabel(inner, text=area["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY, wraplength=160, justify="left")
            t.pack(anchor="w", pady=(0, 4))

            stat_txt = f"{area.get('researcher_count', 0)} Researchers · {area.get('paper_count', 0)} Papers"
            s = ctk.CTkLabel(inner, text=stat_txt, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT)
            s.pack(anchor="w", pady=(0, 8))

            view_btn = ctk.CTkButton(
                inner,
                text="Explore Area",
                command=lambda aid=area["id"]: self.on_navigate("research_areas", aid),
                fg_color=Theme.MUTED_BG,
                hover_color="#E2E8F0",
                text_color=Theme.DARK_TEXT,
                corner_radius=6,
                font=Theme.FONT_CAPTION,
                height=26
            )
            view_btn.pack(fill="x")

    def _build_recent_papers(self):
        """Recent Research Papers."""
        papers = self.stats_data.get("recent_papers", [])
        if not papers:
            return

        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="x", padx=25, pady=(0, 15))

        h_row = ctk.CTkFrame(box, fg_color="transparent")
        h_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(h_row, text="Recent Research Papers", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(side="left")
        ctk.CTkButton(
            h_row,
            text="View All Papers →",
            command=lambda: self.on_navigate("papers", None),
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=130,
            height=28
        ).pack(side="right")

        for paper in papers:
            card = create_card(box)
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            # Left content
            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            t_lbl = ctk.CTkLabel(
                left,
                text=paper["title"],
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.NAVY,
                anchor="w",
                justify="left"
            )
            t_lbl.pack(anchor="w")

            authors_str = ", ".join(a["name"] for a in paper.get("authors", []))
            meta_str = f"Authors: {authors_str}  ·  Year: {paper.get('publication_year')}  ·  Venue: {paper.get('venue')}"
            meta_lbl = ctk.CTkLabel(left, text=meta_str, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT, anchor="w")
            meta_lbl.pack(anchor="w", pady=(2, 0))

            # Right details button
            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right", padx=(10, 0))

            det_btn = create_secondary_button(
                right,
                text="View Details",
                command=lambda pid=paper["id"]: self.on_navigate("paper_details", pid),
                width=100,
                height=30
            )
            det_btn.pack()

    def _build_researcher_highlights(self):
        """Researcher Highlights."""
        highlights = self.stats_data.get("highlights", [])
        if not highlights:
            return

        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="x", padx=25, pady=(0, 15))

        h_row = ctk.CTkFrame(box, fg_color="transparent")
        h_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(h_row, text="Researcher Highlights", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(side="left")
        ctk.CTkButton(
            h_row,
            text="View Directory →",
            command=lambda: self.on_navigate("researchers", None),
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=130,
            height=28
        ).pack(side="right")

        grid = ctk.CTkFrame(box, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1, 2), weight=1, uniform="high_grid")

        for idx, r in enumerate(highlights[:3]):
            card = create_card(grid)
            card.grid(row=0, column=idx, padx=6, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=16, pady=16)

            # Avatar initials badge
            initials = "".join([part[0] for part in r["name"].split() if part])[:2]
            av_col = r.get("avatar_color", Theme.ACADEMIC_BLUE)

            av_lbl = ctk.CTkLabel(
                inner,
                text=initials,
                font=(Theme.FONT_FAMILY, 14, "bold"),
                fg_color=av_col,
                text_color=Theme.WHITE,
                corner_radius=20,
                width=40,
                height=40
            )
            av_lbl.pack(anchor="w", pady=(0, 8))

            name_lbl = ctk.CTkLabel(inner, text=r["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY)
            name_lbl.pack(anchor="w")

            desig_lbl = ctk.CTkLabel(
                inner,
                text=f"{r.get('designation', '')}\n{r.get('department_name', '')}",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                justify="left"
            )
            desig_lbl.pack(anchor="w", pady=(2, 6))

            cit_lbl = ctk.CTkLabel(
                inner,
                text=f"📚 {r.get('citation_count', 0)} Citations  |  h-index: {r.get('h_index', 0)}",
                font=Theme.FONT_CAPTION,
                text_color=Theme.PURPLE
            )
            cit_lbl.pack(anchor="w", pady=(0, 10))

            prof_btn = create_secondary_button(
                inner,
                text="View Profile",
                command=lambda rid=r["id"]: self.on_navigate("researcher_profile", rid),
                width=110,
                height=28
            )
            prof_btn.pack(fill="x")

    def _build_recommendations_preview(self):
        """Recommended Researchers preview."""
        if not self.recommendations:
            return

        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="x", padx=25, pady=(0, 30))

        h_row = ctk.CTkFrame(box, fg_color="transparent")
        h_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(h_row, text="Recommended Researchers for You", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(side="left")
        ctk.CTkButton(
            h_row,
            text="View All Recommendations →",
            command=lambda: self.on_navigate("recommendations", None),
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=200,
            height=28
        ).pack(side="right")

        for item in self.recommendations[:2]:
            r = item["researcher"]
            card = create_card(box)
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=12)

            left = ctk.CTkFrame(inner, fg_color="transparent")
            left.pack(side="left", fill="both", expand=True)

            r_name = ctk.CTkLabel(left, text=r["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY)
            r_name.pack(anchor="w")

            expl = ctk.CTkLabel(
                left,
                text=item["explanation"],
                font=Theme.FONT_CAPTION,
                text_color=Theme.ACADEMIC_BLUE
            )
            expl.pack(anchor="w", pady=(2, 0))

            right = ctk.CTkFrame(inner, fg_color="transparent")
            right.pack(side="right")

            btn = create_secondary_button(
                right,
                text="Connect / View",
                command=lambda rid=r["id"]: self.on_navigate("researcher_profile", rid),
                width=120,
                height=30
            )
            btn.pack()
