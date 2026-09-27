"""
CAMPUSX — Discover People Behind the Work System
Recommendations View: Interest-Based Researcher Discovery with Explainable Rationales
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional, Set
from api_client.client import api_client
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge
)


class RecommendationsView(ctk.CTkScrollableFrame):
    """Personalized researcher recommendation system powered by interest overlap analysis."""

    def __init__(
        self,
        parent,
        current_user: Optional[Dict[str, Any]],
        on_select_researcher: Callable[[int], None]
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.user = current_user or {}
        self.on_select_researcher = on_select_researcher

        self.available_areas: List[str] = []
        self.selected_interests: Set[str] = set()
        self.interest_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.recommendations: List[Dict[str, Any]] = []

        self._load_available_areas()
        self._build_header()
        self._build_interest_selector()
        self._build_results_area()
        self._fetch_recommendations()

    def _load_available_areas(self):
        try:
            all_areas = api_client.get_research_areas()
            self.available_areas = [a.get("name") for a in all_areas if a.get("name")]
        except Exception:
            self.available_areas = [
                "Artificial Intelligence",
                "Machine Learning",
                "Cybersecurity",
                "Data Science",
                "Internet of Things",
                "Computer Networks",
                "Software Engineering",
                "Natural Language Processing",
                "Cloud & Distributed Systems",
                "Healthcare & Biomedical Informatics"
            ]

        if self.user.get("id"):
            try:
                researcher = api_client.get_researcher_by_user(self.user["id"])
                profile_areas = [a.get("name") for a in researcher.get("areas", []) if a.get("name")]
                if profile_areas:
                    self.selected_interests = set(profile_areas[:4])
                    return
            except Exception:
                pass

        if not self.selected_interests and self.available_areas:
            self.selected_interests = set(self.available_areas[:2])

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(20, 10))

        title = ctk.CTkLabel(head, text="Personalized Researcher Recommendations", font=Theme.FONT_TITLE, text_color=Theme.NAVY)
        title.pack(side="left")

        badge = create_badge(head, text="✨ Interest Overlap Matching", bg_color="#EEF2FF", text_color=Theme.PURPLE)
        badge.pack(side="left", padx=12)

    def _build_interest_selector(self):
        """Card allowing user to toggle research interests to recalculate recommendations."""
        card = create_card(self)
        card.pack(fill="x", padx=25, pady=(0, 15))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            inner,
            text="Customize Your Research Interests & Topics",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            inner,
            text="The recommendations are computed from available research areas and your current researcher profile.",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 12))

        chips_grid = ctk.CTkFrame(inner, fg_color="transparent")
        chips_grid.pack(fill="x", pady=(0, 14))

        if not self.available_areas:
            ctk.CTkLabel(
                inner,
                text="No research areas are available yet. Add or sync your campus data first.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w")
            return

        for idx, area in enumerate(self.available_areas):
            row = idx // 5
            col = idx % 5
            chips_grid.columnconfigure(col, weight=1)

            var = ctk.BooleanVar(value=(area in self.selected_interests))
            cb = ctk.CTkCheckBox(
                chips_grid,
                text=area,
                variable=var,
                command=lambda a=area, v=var: self._on_interest_toggled(a, v),
                font=Theme.FONT_CAPTION,
                text_color=Theme.DARK_TEXT,
                fg_color=Theme.ACADEMIC_BLUE,
                hover_color=Theme.NAVY,
                corner_radius=4,
                checkbox_width=18,
                checkbox_height=18
            )
            cb.grid(row=row, column=col, padx=4, pady=4, sticky="w")
            self.interest_checkboxes[area] = cb

        btn_box = ctk.CTkFrame(inner, fg_color="transparent")
        btn_box.pack(fill="x")

        apply_btn = create_primary_button(
            btn_box,
            text="Recalculate Recommendations  ↻",
            command=self._fetch_recommendations,
            width=220,
            height=34
        )
        apply_btn.pack(side="left")

    def _on_interest_toggled(self, area: str, var: ctk.BooleanVar):
        if var.get():
            self.selected_interests.add(area)
        else:
            self.selected_interests.discard(area)

    def _build_results_area(self):
        self.results_container = ctk.CTkFrame(self, fg_color="transparent")
        self.results_container.pack(fill="x", padx=25, pady=(0, 30))

    def _fetch_recommendations(self):
        # Clear existing
        for widget in self.results_container.winfo_children():
            widget.destroy()

        if not self.selected_interests:
            empty = create_card(self.results_container)
            empty.pack(fill="x", pady=10)
            ctk.CTkLabel(
                empty,
                text="Please select at least one research interest above to view recommendations.",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            ).pack(pady=24)
            return

        dept = self.user.get("department_name") or self.user.get("custom_department")
        inst = self.user.get("institution_name") or self.user.get("custom_institution")

        try:
            self.recommendations = api_client.get_recommendations(
                interests=list(self.selected_interests),
                department=dept,
                institution=inst,
                limit=6
            )
        except Exception as e:
            self.recommendations = []

        if not self.recommendations:
            empty = create_card(self.results_container)
            empty.pack(fill="x", pady=10)
            ctk.CTkLabel(
                empty,
                text="No researchers found with matching interests at this time.",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            ).pack(pady=24)
            return

        ctk.CTkLabel(
            self.results_container,
            text=f"Discovered {len(self.recommendations)} Recommended Scholars Matching Your Focus",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(10, 10))

        # Render 2-column recommendation cards
        grid = ctk.CTkFrame(self.results_container, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="rec_cards")

        for idx, item in enumerate(self.recommendations):
            row = idx // 2
            col = idx % 2

            r = item["researcher"]
            card = create_card(grid)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=16, pady=16)

            # Top: Avatar, Name, Score Badge
            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x", pady=(0, 8))

            initials = "".join([part[0] for part in r["name"].split() if part])[:2]
            av_lbl = ctk.CTkLabel(
                top,
                text=initials,
                font=(Theme.FONT_FAMILY, 13, "bold"),
                fg_color=r.get("avatar_color", Theme.ACADEMIC_BLUE),
                text_color=Theme.WHITE,
                corner_radius=18,
                width=36,
                height=36
            )
            av_lbl.pack(side="left", padx=(0, 10))

            header_text = ctk.CTkFrame(top, fg_color="transparent")
            header_text.pack(side="left", fill="both", expand=True)

            r_name = ctk.CTkLabel(header_text, text=r["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY)
            r_name.pack(anchor="w")

            desig = ctk.CTkLabel(header_text, text=f"{r.get('designation', '')}", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT)
            desig.pack(anchor="w")

            score_badge = create_badge(
                top,
                text=f"Match Score: {item['score']}",
                bg_color="#FEF3C7",
                text_color="#B45309"
            )
            score_badge.pack(side="right")

            # Explanation Box (Key requirement)
            expl_box = ctk.CTkFrame(inner, fg_color="#F0FDF4", border_color="#BBF7D0", border_width=1, corner_radius=8)
            expl_box.pack(fill="x", pady=(6, 8))

            expl_inner = ctk.CTkFrame(expl_box, fg_color="transparent")
            expl_inner.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(
                expl_inner,
                text=f"💡 {item['explanation']}",
                font=Theme.FONT_CAPTION,
                text_color="#15803D",
                wraplength=340,
                justify="left"
            ).pack(anchor="w")

            # Affiliation & Research Areas
            dept_inst = f"🏛️ {r.get('department_name', '')} · {r.get('institution_name', '')}"
            ctk.CTkLabel(inner, text=dept_inst, font=Theme.FONT_CAPTION, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(0, 6))

            areas = r.get("areas", [])
            if areas:
                areas_box = ctk.CTkFrame(inner, fg_color="transparent")
                areas_box.pack(fill="x", pady=(0, 10))
                for a in areas[:3]:
                    create_badge(areas_box, text=a, bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(0, 4))

            # Bottom CTA
            bot = ctk.CTkFrame(inner, fg_color="transparent")
            bot.pack(fill="x")

            ctk.CTkLabel(
                bot,
                text=f"📚 {r.get('publication_count', 0)} Papers · ⭐ {r.get('citation_count', 0)} Citations",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(side="left")

            create_secondary_button(
                bot,
                text="View Profile →",
                command=lambda rid=r["id"]: self.on_select_researcher(rid),
                width=110,
                height=28
            ).pack(side="right")
