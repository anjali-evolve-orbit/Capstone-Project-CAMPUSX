"""
CAMPUSX — Discover People Behind the Work System
Categorized Search View: Multi-Entity Global Search Results
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, Optional
from api_client.client import api_client
from ui.theme import (
    Theme,
    create_card,
    create_secondary_button,
    create_badge
)
from ui.theme import enable_mousewheel


class CategorizedSearchView(ctk.CTkScrollableFrame):
    """Categorized results view for global search across Researchers, Papers, Areas, and Communities."""

    def __init__(
        self,
        parent,
        query: str,
        on_back: Callable[[], None],
        on_select_researcher: Callable[[int], None],
        on_select_paper: Callable[[int], None],
        on_select_area: Callable[[int, str], None]
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.query = query
        self.on_back = on_back
        self.on_select_researcher = on_select_researcher
        self.on_select_paper = on_select_paper
        self.on_select_area = on_select_area

        self.search_results: Dict[str, Any] = {}
        # enable mouse-wheel scrolling
        enable_mousewheel(self)
        self._load_results()
        self._build_header()
        self._build_results()

    def _load_results(self):
        try:
            self.search_results = api_client.global_search(self.query)
        except Exception:
            self.search_results = {
                "query": self.query,
                "total_results": 0,
                "counts": {"researchers": 0, "papers": 0, "areas": 0, "communities": 0},
                "results": {"researchers": [], "papers": [], "areas": [], "communities": []}
            }

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(15, 10))

        back_btn = ctk.CTkButton(
            head,
            text="← Back",
            command=self.on_back,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=80,
            height=30
        )
        back_btn.pack(side="left", padx=(0, 10))

        counts = self.search_results.get("counts", {})
        total = self.search_results.get("total_results", 0)

        t_lbl = ctk.CTkLabel(
            head,
            text=f"Search Results for '{self.query}' ({total} found)",
            font=Theme.FONT_TITLE,
            text_color=Theme.NAVY
        )
        t_lbl.pack(side="left")

    def _build_results(self):
        counts = self.search_results.get("counts", {})
        results = self.search_results.get("results", {})

        # 1. Researchers Category
        researchers = results.get("researchers", [])
        self._build_category_section(
            category_title=f"Researchers ({counts.get('researchers', 0)})",
            items=researchers,
            render_func=self._render_researcher_item
        )

        # 2. Papers Category
        papers = results.get("papers", [])
        self._build_category_section(
            category_title=f"Papers ({counts.get('papers', 0)})",
            items=papers,
            render_func=self._render_paper_item
        )

        # 3. Research Areas Category
        areas = results.get("areas", [])
        self._build_category_section(
            category_title=f"Research Areas ({counts.get('areas', 0)})",
            items=areas,
            render_func=self._render_area_item
        )

        # 4. Communities Category
        communities = results.get("communities", [])
        self._build_category_section(
            category_title=f"Communities ({counts.get('communities', 0)})",
            items=communities,
            render_func=self._render_community_item
        )

    def _build_category_section(self, category_title: str, items: list, render_func: Callable):
        section_card = create_card(self)
        section_card.pack(fill="x", padx=25, pady=8)

        inner = ctk.CTkFrame(section_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(inner, text=category_title, font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 8))

        if not items:
            ctk.CTkLabel(inner, text="No matches found in this category.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
        else:
            for item in items:
                render_func(inner, item)

    def _render_researcher_item(self, parent, r: Dict[str, Any]):
        row = ctk.CTkFrame(parent, fg_color=Theme.MUTED_BG, corner_radius=6)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(left, text=r["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text=f"{r.get('designation', '')} · {r.get('department_name', '')} · {r.get('institution_name', '')}",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w")

        create_secondary_button(
            inner,
            text="View Profile →",
            command=lambda rid=r["id"]: self.on_select_researcher(rid),
            width=110,
            height=26
        ).pack(side="right")

    def _render_paper_item(self, parent, p: Dict[str, Any]):
        row = ctk.CTkFrame(parent, fg_color=Theme.MUTED_BG, corner_radius=6)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(left, text=p["title"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text=f"Year: {p.get('publication_year')} · Venue: {p.get('venue')} · Citations: {p.get('citation_count', 0)}",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w")

        create_secondary_button(
            inner,
            text="View Paper →",
            command=lambda pid=p["id"]: self.on_select_paper(pid),
            width=110,
            height=26
        ).pack(side="right")

    def _render_area_item(self, parent, a: Dict[str, Any]):
        row = ctk.CTkFrame(parent, fg_color=Theme.MUTED_BG, corner_radius=6)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(left, text=f"🔬 {a['name']}", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w")
        ctk.CTkLabel(left, text=a.get("description", ""), font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

        create_secondary_button(
            inner,
            text="Explore Area →",
            command=lambda aid=a["id"], aname=a["name"]: self.on_select_area(aid, aname),
            width=110,
            height=26
        ).pack(side="right")

    def _render_community_item(self, parent, c: Dict[str, Any]):
        row = ctk.CTkFrame(parent, fg_color=Theme.MUTED_BG, corner_radius=6)
        row.pack(fill="x", pady=3)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(inner, text=f"🏛️ {c['name']}  ({c.get('member_count', 0)} members)", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(side="left")
        ctk.CTkLabel(inner, text=f"· {c.get('institution_name', '')}", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left", padx=8)
