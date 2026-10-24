"""
CAMPUSX — Discover People Behind the Work System
Paper Details View: Full Abstract, Author Profiles, Related Areas, and Similar Papers
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


class PaperDetailsView(ctk.CTkScrollableFrame):
    """Detailed view for an individual academic research paper."""

    def __init__(
        self,
        parent,
        paper_id: int,
        on_back: Callable[[], None],
        on_select_researcher: Callable[[int], None],
        on_select_paper: Callable[[int], None]
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.paper_id = paper_id
        self.on_back = on_back
        self.on_select_researcher = on_select_researcher
        self.on_select_paper = on_select_paper

        self.paper: Optional[Dict[str, Any]] = None
        self._load_paper()
        self._build_ui()

    def _load_paper(self):
        try:
            self.paper = api_client.get_paper_detail(self.paper_id)
        except Exception:
            self.paper = None

    def _build_ui(self):
        # Back Button Row
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        back_btn = ctk.CTkButton(
            top_bar,
            text="← Back to Papers Directory",
            command=self.on_back,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=180,
            height=30
        )
        back_btn.pack(side="left")

        if not self.paper:
            err_card = create_card(self)
            err_card.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(err_card, text="Research paper could not be loaded.", font=Theme.FONT_BODY, text_color=Theme.DANGER).pack(pady=30)
            return

        p = self.paper

        # 1. Header Card (Title, Metadata, Badges)
        head_card = create_card(self)
        head_card.pack(fill="x", padx=25, pady=(0, 15))

        h_inner = ctk.CTkFrame(head_card, fg_color="transparent")
        h_inner.pack(fill="both", expand=True, padx=25, pady=22)

        # Badges Row
        badge_row = ctk.CTkFrame(h_inner, fg_color="transparent")
        badge_row.pack(fill="x", pady=(0, 8))

        # Show ALL research areas as chips
        all_areas = p.get("research_areas") or []
        if not all_areas:
            # Fall back to primary_area_name if junction table data absent
            pname = p.get("primary_area_name", "Academic Research")
            all_areas = [{"name": pname}]
        for area in all_areas:
            create_badge(badge_row, text=f"🔬 {area.get('name', '')}", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(0, 6))

        create_badge(badge_row, text=f"📅 Published {p.get('publication_year')}", bg_color="#F1F5F9", text_color=Theme.DARK_TEXT).pack(side="left", padx=8)

        create_badge(badge_row, text=f"⭐ {p.get('citation_count', 0)} Citations", bg_color="#F3F0FF", text_color=Theme.PURPLE).pack(side="left")

        # Title
        t_lbl = ctk.CTkLabel(
            h_inner,
            text=p["title"],
            font=Theme.FONT_TITLE,
            text_color=Theme.NAVY,
            wraplength=760,
            justify="left"
        )
        t_lbl.pack(anchor="w", pady=(4, 8))

        venue_txt = f"Venue: {p.get('venue', 'Academic Publication')}   |   DOI: {p.get('doi', 'N/A')}"
        ctk.CTkLabel(h_inner, text=venue_txt, font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

        # 2. Abstract Section
        abs_card = create_card(self)
        abs_card.pack(fill="x", padx=25, pady=(0, 15))

        abs_inner = ctk.CTkFrame(abs_card, fg_color="transparent")
        abs_inner.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(abs_inner, text="Abstract", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 8))
        abstract_txt = p.get("abstract") or "No abstract provided."
        ctk.CTkLabel(
            abs_inner,
            text=abstract_txt,
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=740,
            justify="left"
        ).pack(anchor="w")

        # 3. Authors Section
        auth_card = create_card(self)
        auth_card.pack(fill="x", padx=25, pady=(0, 15))

        auth_inner = ctk.CTkFrame(auth_card, fg_color="transparent")
        auth_inner.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(auth_inner, text="Paper Authors", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 12))

        authors = p.get("authors", [])
        if not authors:
            ctk.CTkLabel(auth_inner, text="No author data recorded.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
        else:
            auth_grid = ctk.CTkFrame(auth_inner, fg_color="transparent")
            auth_grid.pack(fill="x")
            auth_grid.columnconfigure((0, 1), weight=1, uniform="auth_grid")

            for idx, a in enumerate(authors):
                row_idx = idx // 2
                col = idx % 2

                a_box = ctk.CTkFrame(auth_grid, fg_color=Theme.SOFT_BG, border_color=Theme.BORDER, border_width=1, corner_radius=8)
                a_box.grid(row=row_idx, column=col, padx=6, pady=6, sticky="nsew")

                box_inner = ctk.CTkFrame(a_box, fg_color="transparent")
                box_inner.pack(fill="both", expand=True, padx=14, pady=12)

                top_auth = ctk.CTkFrame(box_inner, fg_color="transparent")
                top_auth.pack(fill="x")

                initials = "".join([part[0] for part in a["name"].split() if part])[:2]
                av_lbl = ctk.CTkLabel(
                    top_auth,
                    text=initials,
                    font=(Theme.FONT_FAMILY, 12, "bold"),
                    fg_color=a.get("avatar_color", Theme.ACADEMIC_BLUE),
                    text_color=Theme.WHITE,
                    corner_radius=16,
                    width=32,
                    height=32
                )
                av_lbl.pack(side="left", padx=(0, 10))

                text_col = ctk.CTkFrame(top_auth, fg_color="transparent")
                text_col.pack(side="left", fill="both", expand=True)

                a_name = ctk.CTkLabel(text_col, text=a["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY)
                a_name.pack(anchor="w")

                # Show role if available (lead_author / co_author)
                role = a.get("role", "")
                role_display = "⭐ Lead Author" if role in ("lead_author", "corresponding") else ("Co-Author" if role == "co_author" else a.get("designation", ""))
                role_color = "#15803D" if "Lead" in role_display else Theme.SECONDARY_TEXT
                ctk.CTkLabel(text_col, text=role_display, font=Theme.FONT_CAPTION, text_color=role_color).pack(anchor="w")

                dept_inst = f"{a.get('department_name', '')} · {a.get('institution_name', '')}"
                ctk.CTkLabel(box_inner, text=dept_inst, font=Theme.FONT_CAPTION, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(6, 8))

                view_prof_btn = create_secondary_button(
                    box_inner,
                    text="View Researcher Profile →",
                    command=lambda aid=a["id"]: self.on_select_researcher(aid),
                    width=170,
                    height=26
                )
                view_prof_btn.pack(anchor="w")

        # 4. Related Papers in Same Research Area

        rel_papers = p.get("related_papers", [])
        if rel_papers:
            rel_card = create_card(self)
            rel_card.pack(fill="x", padx=25, pady=(0, 30))

            rel_inner = ctk.CTkFrame(rel_card, fg_color="transparent")
            rel_inner.pack(fill="both", expand=True, padx=25, pady=20)

            ctk.CTkLabel(rel_inner, text="Related Papers in this Research Area", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 10))

            for rp in rel_papers:
                r_row = ctk.CTkFrame(rel_inner, fg_color=Theme.MUTED_BG, corner_radius=8)
                r_row.pack(fill="x", pady=4)

                r_inner = ctk.CTkFrame(r_row, fg_color="transparent")
                r_inner.pack(fill="x", padx=14, pady=10)

                left_c = ctk.CTkFrame(r_inner, fg_color="transparent")
                left_c.pack(side="left", fill="both", expand=True)

                ctk.CTkLabel(left_c, text=rp["title"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w")
                ctk.CTkLabel(left_c, text=f"Year: {rp.get('publication_year')}  ·  Venue: {rp.get('venue')}", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(2, 0))

                create_secondary_button(
                    r_inner,
                    text="Open Paper →",
                    command=lambda rpid=rp["id"]: self.on_select_paper(rpid),
                    width=100,
                    height=28
                ).pack(side="right")
