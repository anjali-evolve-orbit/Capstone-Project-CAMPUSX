"""
CAMPUSX — Discover People Behind the Work System
Researchers View: Filterable and Searchable Researcher Directory
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


class ResearchersView(ctk.CTkFrame):
    """Searchable and filterable directory of campus researchers."""

    def __init__(self, parent, on_select_researcher: Callable[[int], None]):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_select_researcher = on_select_researcher

        self.institutions: List[Dict[str, Any]] = []
        self.departments: List[Dict[str, Any]] = []
        self.areas: List[Dict[str, Any]] = []
        self.researchers: List[Dict[str, Any]] = []

        self._load_filters_data()
        self._build_header()
        self._build_filters_bar()
        self._build_results_area()
        self._apply_filters()

    def _load_filters_data(self):
        try:
            self.institutions = api_client.get_institutions()
            self.departments = api_client.get_departments()
            self.areas = api_client.get_research_areas()
        except Exception:
            self.institutions = []
            self.departments = []
            self.areas = []

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(20, 10))

        title = ctk.CTkLabel(head, text="Researchers Directory", font=Theme.FONT_TITLE, text_color=Theme.NAVY)
        title.pack(side="left")

        self.count_badge = create_badge(head, text="Loading...", bg_color="#EBF4FF", text_color=Theme.ACADEMIC_BLUE)
        self.count_badge.pack(side="left", padx=12)

    def _build_filters_bar(self):
        """Filter bar: Search text, Institution dropdown, Department dropdown, Area dropdown."""
        bar = create_card(self, fg_color=Theme.WHITE)
        bar.pack(fill="x", padx=25, pady=(0, 15))

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        # Search Box
        self.search_entry = ctk.CTkEntry(
            inner,
            placeholder_text="Search researcher by name, area or department...",
            width=260,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            fg_color=Theme.SOFT_BG
        )
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._apply_filters())

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

        # Department Filter
        dept_names = ["All Departments"] + [d["name"] for d in self.departments if not d.get("is_custom")]
        self.dept_var = ctk.StringVar(value=dept_names[0])
        self.dept_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.dept_var,
            values=dept_names,
            command=lambda v: self._apply_filters(),
            width=160,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.MUTED_BG,
            button_color="#CBD5E1",
            text_color=Theme.DARK_TEXT
        )
        self.dept_menu.pack(side="left", padx=(0, 8))

        # Research Area Filter
        area_names = ["All Areas"] + [a["name"] for a in self.areas]
        self.area_var = ctk.StringVar(value=area_names[0])
        self.area_menu = ctk.CTkOptionMenu(
            inner,
            variable=self.area_var,
            values=area_names,
            command=lambda v: self._apply_filters(),
            width=140,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.MUTED_BG,
            button_color="#CBD5E1",
            text_color=Theme.DARK_TEXT
        )
        self.area_menu.pack(side="left", padx=(0, 8))

        # Filter Action Buttons
        filter_btn = create_primary_button(
            inner,
            text="Filter",
            command=self._apply_filters,
            width=70,
            height=34
        )
        filter_btn.pack(side="left", padx=(0, 6))

        reset_btn = create_secondary_button(
            inner,
            text="Reset",
            command=self._reset_filters,
            width=70,
            height=34
        )
        reset_btn.pack(side="left")

    def _build_results_area(self):
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color=Theme.SOFT_BG)
        self.scroll_area.pack(fill="both", expand=True, padx=25, pady=(0, 20))

    def _reset_filters(self):
        self.search_entry.delete(0, "end")
        self.inst_var.set("All Institutions")
        self.dept_var.set("All Departments")
        self.area_var.set("All Areas")
        self._apply_filters()

    def _apply_filters(self):
        # Clear existing cards
        for widget in self.scroll_area.winfo_children():
            widget.destroy()

        search_term = self.search_entry.get().strip() or None

        inst_name = self.inst_var.get()
        inst_id = None
        if inst_name != "All Institutions":
            inst_obj = next((i for i in self.institutions if i["name"] == inst_name), None)
            inst_id = inst_obj["id"] if inst_obj else None

        dept_name = self.dept_var.get()
        dept_id = None
        if dept_name != "All Departments":
            dept_obj = next((d for d in self.departments if d["name"] == dept_name), None)
            dept_id = dept_obj["id"] if dept_obj else None

        area_name = self.area_var.get()
        area_id = None
        if area_name != "All Areas":
            area_obj = next((a for a in self.areas if a["name"] == area_name), None)
            area_id = area_obj["id"] if area_obj else None

        try:
            self.researchers = api_client.get_researchers(
                institution_id=inst_id,
                department_id=dept_id,
                area_id=area_id,
                search=search_term
            )
        except Exception as e:
            self.researchers = []

        self.count_badge.configure(text=f"{len(self.researchers)} Researchers Found")

        if not self.researchers:
            empty_box = create_card(self.scroll_area)
            empty_box.pack(fill="x", pady=20)
            ctk.CTkLabel(
                empty_box,
                text="No researchers found matching the selected filters.",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            ).pack(pady=30)
            return

        # Render 2-column grid of researcher cards
        grid = ctk.CTkFrame(self.scroll_area, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="res_grid")

        for idx, r in enumerate(self.researchers):
            row = idx // 2
            col = idx % 2

            card = create_card(grid)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=16, pady=16)

            # Top: Avatar, Name, Designation
            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x", pady=(0, 10))

            initials = "".join([part[0] for part in r["name"].split() if part])[:2]
            av_col = r.get("avatar_color", Theme.ACADEMIC_BLUE)

            av_lbl = ctk.CTkLabel(
                top,
                text=initials,
                font=(Theme.FONT_FAMILY, 14, "bold"),
                fg_color=av_col,
                text_color=Theme.WHITE,
                corner_radius=20,
                width=42,
                height=42
            )
            av_lbl.pack(side="left", padx=(0, 12))

            header_text = ctk.CTkFrame(top, fg_color="transparent")
            header_text.pack(side="left", fill="both", expand=True)

            name_lbl = ctk.CTkLabel(header_text, text=r["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY)
            name_lbl.pack(anchor="w")

            desig_lbl = ctk.CTkLabel(
                header_text,
                text=f"{r.get('designation', '')}",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            )
            desig_lbl.pack(anchor="w")

            inst_lbl = ctk.CTkLabel(
                inner,
                text=f"🏛️ {r.get('department_name', '')} · {r.get('institution_name', '')}",
                font=Theme.FONT_CAPTION,
                text_color=Theme.DARK_TEXT,
                wraplength=340,
                justify="left"
            )
            inst_lbl.pack(anchor="w", pady=(0, 8))

            # Research Areas Pills
            areas = r.get("areas", [])
            if areas:
                areas_box = ctk.CTkFrame(inner, fg_color="transparent")
                areas_box.pack(fill="x", pady=(0, 8))
                for area in areas[:3]:
                    badge = create_badge(areas_box, text=area, bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE)
                    badge.pack(side="left", padx=(0, 4))

            # Bottom Metrics (Publications & Citations)
            bot = ctk.CTkFrame(inner, fg_color="transparent")
            bot.pack(fill="x", pady=(6, 0))

            metrics_lbl = ctk.CTkLabel(
                bot,
                text=f"📚 {r.get('publication_count', 0)} Publications   |   ⭐ {r.get('citation_count', 0)} Citations",
                font=Theme.FONT_CAPTION,
                text_color=Theme.PURPLE
            )
            metrics_lbl.pack(side="left")

            view_btn = create_secondary_button(
                bot,
                text="View Profile →",
                command=lambda rid=r["id"]: self.on_select_researcher(rid),
                width=110,
                height=28
            )
            view_btn.pack(side="right")
