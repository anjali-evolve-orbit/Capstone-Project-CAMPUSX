"""
CAMPUSX — Discover People Behind the Work System
Communities View: Academic and Research Groups Across Campus
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


class CommunitiesView(ctk.CTkScrollableFrame):
    """Academic communities, research collectives, and laboratory groups directory."""

    def __init__(self, parent, on_select_researcher: Callable[[int], None]):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_select_researcher = on_select_researcher

        self.communities: List[Dict[str, Any]] = []
        self._load_communities()
        self._build_header()
        self._build_list()

    def _load_communities(self):
        self.loading = True
        self.error = None
        try:
            self.communities = api_client.get_communities()
        except Exception as exc:
            self.communities = []
            self.error = str(exc)
        finally:
            self.loading = False

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(20, 15))

        title = ctk.CTkLabel(head, text="Academic & Research Communities", font=Theme.FONT_TITLE, text_color=Theme.NAVY)
        title.pack(side="left")

        badge = create_badge(head, text=f"{len(self.communities)} Active Collectives", bg_color="#F1F5F9", text_color=Theme.NAVY)
        badge.pack(side="left", padx=12)

    def _build_list(self):
        if self.loading:
            loading = create_card(self)
            loading.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(loading, text="Loading communities…", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(pady=30)
            return

        if self.error:
            error = create_card(self)
            error.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(error, text="Unable to load communities right now.", font=Theme.FONT_BODY_BOLD, text_color=Theme.DANGER).pack(pady=(20, 6))
            ctk.CTkLabel(error, text=self.error, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT, wraplength=600, justify="left").pack(pady=(0, 20))
            return

        if not self.communities:
            empty = create_card(self)
            empty.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(empty, text="No communities recorded for this campus yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(pady=30)
            return

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=(0, 30))
        grid.columnconfigure((0, 1), weight=1, uniform="comm_grid")

        for idx, c in enumerate(self.communities):
            row = idx // 2
            col = idx % 2

            card = create_card(grid)
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=20, pady=18)

            # Top: Category & Member Count
            top = ctk.CTkFrame(inner, fg_color="transparent")
            top.pack(fill="x", pady=(0, 6))

            create_badge(top, text=c.get("category", "Research Group"), bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left")
            create_badge(top, text=f"👥 {c.get('member_count', 0)} Members", bg_color="#F3F0FF", text_color=Theme.PURPLE).pack(side="right")

            # Name
            t_lbl = ctk.CTkLabel(inner, text=c["name"], font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY, wraplength=340, justify="left")
            t_lbl.pack(anchor="w", pady=(4, 6))

            # Affiliation
            inst_name = c.get("institution_name", "Campus Wide")
            ctk.CTkLabel(inner, text=f"🏛️ Affiliation: {inst_name}", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 8))

            # Description
            desc = c.get("description", "")
            ctk.CTkLabel(inner, text=desc, font=Theme.FONT_BODY, text_color=Theme.DARK_TEXT, wraplength=340, justify="left").pack(anchor="w", pady=(0, 12))

            # Key Members Pills
            members = c.get("key_members", [])
            if members:
                m_frame = ctk.CTkFrame(inner, fg_color=Theme.SOFT_BG, corner_radius=8)
                m_frame.pack(fill="x", pady=(0, 10))

                m_inner = ctk.CTkFrame(m_frame, fg_color="transparent")
                m_inner.pack(fill="x", padx=10, pady=8)

                ctk.CTkLabel(m_inner, text="Faculty Leads & Active Scholars:", font=Theme.FONT_CAPTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
                for m in members[:3]:
                    btn = ctk.CTkButton(
                        m_inner,
                        text=f"• {m['name']} ({m.get('role', 'Member')})",
                        command=lambda mid=m["id"]: self.on_select_researcher(mid),
                        fg_color="transparent",
                        hover_color=Theme.MUTED_BG,
                        text_color=Theme.ACADEMIC_BLUE,
                        font=Theme.FONT_CAPTION,
                        anchor="w",
                        height=20
                    )
                    btn.pack(anchor="w")
