"""
CAMPUSX — Discover People Behind the Work System
Research Areas View: Interactive Grid of Campus Disciplines & Metrics
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, List
from api_client.client import api_client
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge
)


class ResearchAreasView(ctk.CTkScrollableFrame):
    """Grid displaying academic research areas, metrics, and associated researchers."""

    def __init__(self, parent, on_explore_area: Callable[[int, str], None]):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_explore_area = on_explore_area

        self.areas: List[Dict[str, Any]] = []
        self._load_areas()
        self._build_header()
        self._build_grid()

    def _load_areas(self):
        try:
            self.areas = api_client.get_research_areas()
        except Exception:
            self.areas = []

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(20, 15))

        title = ctk.CTkLabel(head, text="Research Areas & Disciplines", font=Theme.FONT_TITLE, text_color=Theme.NAVY)
        title.pack(side="left")

        badge = create_badge(head, text=f"{len(self.areas)} Active Disciplines", bg_color="#EBF4FF", text_color=Theme.ACADEMIC_BLUE)
        badge.pack(side="left", padx=12)

    def _build_grid(self):
        if not self.areas:
            empty = create_card(self)
            empty.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(empty, text="No research areas currently registered.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(pady=30)
            return

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=(0, 30))
        grid.columnconfigure((0, 1, 2), weight=1, uniform="area_grid")

        # Visual icon mapping
        icon_map = {
            "Artificial Intelligence": "🧠",
            "Machine Learning": "⚙️",
            "Cybersecurity": "🛡️",
            "Data Science": "📊",
            "Internet of Things": "📡",
            "Computer Networks": "🌐",
            "Software Engineering": "💻",
            "Natural Language Processing": "💬",
            "Cloud & Distributed Systems": "☁️",
            "Healthcare & Biomedical Informatics": "🩺"
        }

        for idx, a in enumerate(self.areas):
            row = idx // 3
            col = idx % 3

            card = create_card(grid)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=18, pady=18)

            # Icon Box
            icon_char = icon_map.get(a["name"], "🔬")
            icon_lbl = ctk.CTkLabel(
                inner,
                text=icon_char,
                font=(Theme.FONT_FAMILY, 24),
                fg_color="#EEF2FF",
                corner_radius=10,
                width=46,
                height=46
            )
            icon_lbl.pack(anchor="w", pady=(0, 10))

            t_lbl = ctk.CTkLabel(inner, text=a["name"], font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY, wraplength=210, justify="left")
            t_lbl.pack(anchor="w", pady=(0, 6))

            desc_lbl = ctk.CTkLabel(
                inner,
                text=a.get("description", ""),
                font=Theme.FONT_CAPTION,
                text_color=Theme.DARK_TEXT,
                wraplength=210,
                justify="left"
            )
            desc_lbl.pack(anchor="w", pady=(0, 14))

            # Metrics
            met_box = ctk.CTkFrame(inner, fg_color=Theme.SOFT_BG, corner_radius=6)
            met_box.pack(fill="x", pady=(0, 12))

            met_inner = ctk.CTkFrame(met_box, fg_color="transparent")
            met_inner.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(
                met_inner,
                text=f"👥 {a.get('researcher_count', 0)} Researchers   ·   📄 {a.get('paper_count', 0)} Papers",
                font=Theme.FONT_CAPTION,
                text_color=Theme.PURPLE
            ).pack(anchor="center")

            # Explore Button
            explore_btn = create_primary_button(
                inner,
                text="Explore Discipline →",
                command=lambda aid=a["id"], aname=a["name"]: self.on_explore_area(aid, aname),
                height=32
            )
            explore_btn.pack(fill="x")
