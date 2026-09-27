"""
CAMPUSX — Discover People Behind the Work System
Papers View: Searchable and Filterable Directory of Campus Publications
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional
from api_client.client import api_client
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge
)


class PapersView(ctk.CTkFrame):
    """Academic paper listing with multi-facet filters (year, area, author, institution) and search."""

    def __init__(self, parent, on_select_paper: Callable[[int], None]):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_select_paper = on_select_paper

        self.areas: List[Dict[str, Any]] = []
        self.institutions: List[Dict[str, Any]] = []
        self.papers: List[Dict[str, Any]] = []

        self._load_metadata()
        self._build_header()
        self._build_filters_bar()
        self._build_results_area()
        self._apply_filters()

    def _load_metadata(self):
        try:
            self.areas = api_client.get_research_areas()
            self.institutions = api_client.get_institutions()
        except Exception:
            self.areas = []
            self.institutions = []

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(20, 10))

        ctk.CTkLabel(head, text="Research Papers & Publications", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(side="left")
        self.count_badge = create_badge(head, text="Loading...", bg_color="#F3F0FF", text_color=Theme.PURPLE)
        self.count_badge.pack(side="left", padx=12)

    def _build_filters_bar(self):
        bar = create_card(self, fg_color=Theme.WHITE)
        bar.pack(fill="x", padx=25, pady=(0, 15))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Search Query
        self.search_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Search papers by title, abstract or venue...",
            width=280,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.SOFT_BG
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._apply_filters())

        # Year Filter
        years = ["All Years", "2024", "2023", "2022", "2021", "2020"]
        self.year_var = ctk.StringVar(value=years[0])
        self.year_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.year_var,
            values=years,
            command=lambda v: self._apply_filters(),
            width=110,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.MUTED_BG,
            button_color="#CBD5E1",
            text_color=Theme.DARK_TEXT
        )
        self.year_menu.pack(side="left", padx=(0, 8))

        # Area Filter
        area_names = ["All Areas"] + [a["name"] for a in self.areas]
        self.area_var = ctk.StringVar(value=area_names[0])
        self.area_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.area_var,
            values=area_names,
            command=lambda v: self._apply_filters(),
            width=160,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.MUTED_BG,
            button_color="#CBD5E1",
            text_color=Theme.DARK_TEXT
        )
        self.area_menu.pack(side="left", padx=(0, 8))

        # Institution Filter
        inst_names = ["All Institutions"] + [i["name"] for i in self.institutions if not i.get("is_custom")]
        self.inst_var = ctk.StringVar(value=inst_names[0])
        self.inst_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.inst_var,
            values=inst_names,
            command=lambda v: self._apply_filters(),
            width=160,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.MUTED_BG,
            button_color="#CBD5E1",
            text_color=Theme.DARK_TEXT
        )
        self.inst_menu.pack(side="left", padx=(0, 8))

        # Actions
        create_primary_button(inner, text="Filter", command=self._apply_filters, width=70, height=34).pack(side="left", padx=(0, 6))
        create_secondary_button(inner, text="Reset", command=self._reset_filters, width=70, height=34).pack(side="left")

    def _build_results_area(self):
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color=Theme.SOFT_BG)
        self.scroll_area.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def _reset_filters(self):
        self.search_entry.delete(0, "end")
        self.year_var.set("All Years")
        self.area_var.set("All Areas")
        self.inst_var.set("All Institutions")
        self._apply_filters()

    def _apply_filters(self):
        for widget in self.scroll_area.winfo_children():
            widget.destroy()

        search_term = self.search_entry.get().strip() or None

        year_val = self.year_var.get()
        year_filter = int(year_val) if year_val != "All Years" else None

        area_val = self.area_var.get()
        area_id = None
        if area_val != "All Areas":
            a_obj = next((a for a in self.areas if a["name"] == area_val), None)
            area_id = a_obj["id"] if a_obj else None

        inst_val = self.inst_var.get()
        inst_id = None
        if inst_val != "All Institutions":
            i_obj = next((i for i in self.institutions if i["name"] == inst_val), None)
            inst_id = i_obj["id"] if i_obj else None

        try:
            self.papers = api_client.get_papers(
                year=year_filter,
                area_id=area_id,
                institution_id=inst_id,
                search=search_term
            )
        except Exception:
            self.papers = []

        self.count_badge.configure(text=f"{len(self.papers)} Papers Found")

        if not self.papers:
            empty = create_card(self.scroll_area)
            empty.pack(fill="x", pady=20)
            ctk.CTkLabel(empty, text="No papers match the specified search and filter criteria.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(pady=30)
            return

        for p in self.papers:
            card = create_card(self.scroll_area)
            card.pack(fill="x", pady=6)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=16)

            # Top: Area badge & citations
            top_meta = ctk.CTkFrame(inner, fg_color="transparent")
            top_meta.pack(fill="x", pady=(0, 4))

            area_name = p.get("primary_area_name", "Academic Research")
            create_badge(top_meta, text=f"🔬 {area_name}", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left")

            cit_count = p.get("citation_count", 0)
            create_badge(top_meta, text=f"⭐ {cit_count} Citations", bg_color="#F3F0FF", text_color=Theme.PURPLE).pack(side="right")

            # Title
            t_lbl = ctk.CTkLabel(
                inner,
                text=p["title"],
                font=Theme.FONT_SUBTITLE,
                text_color=Theme.NAVY,
                anchor="w",
                justify="left"
            )
            t_lbl.pack(anchor="w", pady=(4, 6))

            # Abstract Preview
            abstract = p.get("abstract", "")
            if len(abstract) > 220:
                abstract = abstract[:220] + "..."
            ctk.CTkLabel(
                inner,
                text=abstract,
                font=Theme.FONT_BODY,
                text_color=Theme.DARK_TEXT,
                wraplength=760,
                justify="left"
            ).pack(anchor="w", pady=(0, 10))

            # Bottom: Authors, Venue, Year & Action
            bot = ctk.CTkFrame(inner, fg_color="transparent")
            bot.pack(fill="x")

            auth_list = [a["name"] for a in p.get("authors", [])]
            auth_str = ", ".join(auth_list) if auth_list else "Campus Researchers"
            venue_str = f"🏛️ {p.get('venue', 'Scholarly Journal')} ({p.get('publication_year')})  ·  Authors: {auth_str}"

            ctk.CTkLabel(
                bot,
                text=venue_str,
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=600,
                justify="left"
            ).pack(side="left")

            create_secondary_button(
                bot,
                text="View Details →",
                command=lambda pid=p["id"]: self.on_select_paper(pid),
                width=110,
                height=30
            ).pack(side="right")
