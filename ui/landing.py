"""
CAMPUSX — Discover People Behind the Work System
Landing Page: Hero, Feature Discovery Cards, and Academic Ecosystem Hierarchy
"""

import customtkinter as ctk
from config import PROJECT_NAME, TAGLINE, SUPPORTING_TEXT
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge,
    get_logo_image,
    enable_mousewheel
)


class LandingView(ctk.CTkScrollableFrame):
    """Modern Landing Page showcasing CAMPUSX identity and ecosystem discovery."""

    def __init__(self, parent, on_explore, on_get_started, on_login):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        # Ensure mouse-wheel scrolling works on Windows/Linux
        enable_mousewheel(self)
        self.on_explore = on_explore
        self.on_get_started = on_get_started
        self.on_login = on_login

        self._build_header()
        self._build_hero()
        self._build_features_section()
        self._build_ecosystem_section()
        self._build_footer()

    def _build_header(self):
        """Top navigation bar of landing page."""
        nav_frame = ctk.CTkFrame(self, fg_color=Theme.WHITE, height=70, corner_radius=0)
        nav_frame.pack(fill="x", padx=0, pady=(0, 20))
        nav_frame.pack_propagate(False)

        inner = ctk.CTkFrame(nav_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40)

        # Brand Logo
        logo_img = get_logo_image(size=(180, 48))
        if logo_img:
            logo_lbl = ctk.CTkLabel(inner, image=logo_img, text="")
            logo_lbl.pack(side="left", pady=10)
        else:
            logo_text = ctk.CTkLabel(
                inner,
                text=PROJECT_NAME,
                font=(Theme.FONT_FAMILY, 22, "bold"),
                text_color=Theme.NAVY
            )
            logo_text.pack(side="left", pady=15)

        # Right CTA Buttons
        btn_box = ctk.CTkFrame(inner, fg_color="transparent")
        btn_box.pack(side="right", pady=15)

        login_btn = create_secondary_button(
            btn_box,
            text="Login",
            command=self.on_login,
            width=90,
            height=34
        )
        login_btn.pack(side="left", padx=(0, 12))

        start_btn = create_primary_button(
            btn_box,
            text="Get Started",
            command=self.on_get_started,
            width=110,
            height=34
        )
        start_btn.pack(side="left")

    def _build_hero(self):
        """Hero Section: Brand Name, Tagline, Supporting Text, and Primary CTAs."""
        hero_card = create_card(self, fg_color=Theme.WHITE, corner_radius=Theme.RADIUS_CARD)
        hero_card.pack(fill="x", padx=40, pady=(0, 30))

        inner = ctk.CTkFrame(hero_card, fg_color="transparent")
        inner.pack(padx=50, pady=45)

        # Small Category Badge
        badge = create_badge(
            inner,
            text="CAMPUS KNOWLEDGE & COLLABORATION NETWORK",
            bg_color="#EEF2FF",
            text_color=Theme.PURPLE
        )
        badge.pack(pady=(0, 12))

        # Project Name
        title_lbl = ctk.CTkLabel(
            inner,
            text=PROJECT_NAME,
            font=(Theme.FONT_FAMILY, 38, "bold"),
            text_color=Theme.NAVY
        )
        title_lbl.pack(pady=(0, 6))

        # Tagline
        tagline_lbl = ctk.CTkLabel(
            inner,
            text=TAGLINE,
            font=(Theme.FONT_FAMILY, 20, "bold"),
            text_color=Theme.ACADEMIC_BLUE
        )
        tagline_lbl.pack(pady=(0, 16))

        # Supporting text
        desc_lbl = ctk.CTkLabel(
            inner,
            text=SUPPORTING_TEXT,
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.SECONDARY_TEXT,
            wraplength=680,
            justify="center"
        )
        desc_lbl.pack(pady=(0, 26))

        # Action Buttons
        cta_frame = ctk.CTkFrame(inner, fg_color="transparent")
        cta_frame.pack()

        explore_btn = create_primary_button(
            cta_frame,
            text="Explore Campus  →",
            command=self.on_explore,
            width=170,
            height=44
        )
        explore_btn.configure(font=(Theme.FONT_FAMILY, 13, "bold"), fg_color=Theme.ACADEMIC_BLUE)
        explore_btn.pack(side="left", padx=10)

        get_started_btn = create_secondary_button(
            cta_frame,
            text="Get Started",
            command=self.on_get_started,
            width=130,
            height=44
        )
        get_started_btn.configure(font=(Theme.FONT_FAMILY, 13, "bold"))
        get_started_btn.pack(side="left", padx=10)

        login_sub = ctk.CTkButton(
            cta_frame,
            text="Login",
            command=self.on_login,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=(Theme.FONT_FAMILY, 13, "bold"),
            width=90,
            height=44
        )
        login_sub.pack(side="left", padx=5)

    def _build_features_section(self):
        """Explore CAMPUSX: 4 Core Capabilities Cards."""
        section_box = ctk.CTkFrame(self, fg_color="transparent")
        section_box.pack(fill="x", padx=40, pady=(0, 30))

        # Section Header
        lbl = ctk.CTkLabel(
            section_box,
            text="Explore CAMPUSX",
            font=Theme.FONT_TITLE,
            text_color=Theme.NAVY
        )
        lbl.pack(anchor="w", pady=(0, 4))

        sub = ctk.CTkLabel(
            section_box,
            text="Navigate the multidimensional academic intelligence network across your institution.",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        sub.pack(anchor="w", pady=(0, 16))

        # 4 Cards Grid
        grid_frame = ctk.CTkFrame(section_box, fg_color="transparent")
        grid_frame.pack(fill="x")
        grid_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="feat_cards")

        cards_data = [
            ("Researchers", "Discover researchers and their areas of expertise.", "👥", Theme.ACADEMIC_BLUE, "#EBF4FF"),
            ("Research Papers", "Explore academic work, publications and research contributions.", "📄", Theme.PURPLE, "#F3F0FF"),
            ("Research Areas", "Find research topics and people working in those areas.", "🔬", Theme.CYAN, "#E6FFFA"),
            ("Communities", "Discover academic and research communities across your campus.", "🏛️", Theme.NAVY, "#F1F5F9")
        ]

        for idx, (title, desc, icon, accent_col, icon_bg) in enumerate(cards_data):
            card = create_card(grid_frame)
            card.grid(row=0, column=idx, padx=8, pady=5, sticky="nsew")

            card_inner = ctk.CTkFrame(card, fg_color="transparent")
            card_inner.pack(fill="both", expand=True, padx=18, pady=20)

            # Icon Box
            icon_lbl = ctk.CTkLabel(
                card_inner,
                text=icon,
                font=(Theme.FONT_FAMILY, 24),
                fg_color=icon_bg,
                corner_radius=10,
                width=46,
                height=46
            )
            icon_lbl.pack(anchor="w", pady=(0, 12))

            card_title = ctk.CTkLabel(
                card_inner,
                text=title,
                font=Theme.FONT_SUBTITLE,
                text_color=Theme.NAVY
            )
            card_title.pack(anchor="w", pady=(0, 6))

            card_desc = ctk.CTkLabel(
                card_inner,
                text=desc,
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=170,
                justify="left"
            )
            card_desc.pack(anchor="w")

    def _build_ecosystem_section(self):
        """Explore Your Academic Ecosystem Hierarchy Visualizer."""
        eco_card = create_card(self, fg_color=Theme.WHITE)
        eco_card.pack(fill="x", padx=40, pady=(0, 30))

        inner = ctk.CTkFrame(eco_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=30, pady=30)

        # Header
        h_lbl = ctk.CTkLabel(
            inner,
            text="Explore Your Academic Ecosystem",
            font=Theme.FONT_TITLE,
            text_color=Theme.NAVY
        )
        h_lbl.pack(anchor="center", pady=(0, 6))

        sub_lbl = ctk.CTkLabel(
            inner,
            text="CAMPUSX organizes scholarly discovery across the natural institutional hierarchy:",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        sub_lbl.pack(anchor="center", pady=(0, 24))

        # Hierarchy Flow Cards
        flow_frame = ctk.CTkFrame(inner, fg_color="transparent")
        flow_frame.pack(fill="x", pady=10)

        steps = [
            ("1. Campus", "Central university ecosystem", "#EBF4FF", Theme.ACADEMIC_BLUE),
            ("2. Institution", "Colleges & Schools", "#F3F0FF", Theme.PURPLE),
            ("3. Department", "Academic programs & branches", "#E6FFFA", "#0D9488"),
            ("4. Researchers", "Faculty, students & scholars", "#FEF3C7", "#D97706"),
            ("5. Research Areas", "Disciplines & publications", "#FCE7F3", "#DB2777"),
            ("6. Connections", "Graph collaboration network", "#EDE9FE", Theme.PURPLE)
        ]

        # Render sequential step cards with arrow indicators
        for i, (title, subtitle, bg, fg) in enumerate(steps):
            box = ctk.CTkFrame(
                flow_frame,
                fg_color=bg,
                border_color=Theme.BORDER,
                border_width=1,
                corner_radius=10,
                height=90
            )
            box.pack(side="left", fill="both", expand=True, padx=4)
            box.pack_propagate(False)

            t = ctk.CTkLabel(box, text=title, font=Theme.FONT_BODY_BOLD, text_color=fg)
            t.pack(pady=(16, 2))

            s = ctk.CTkLabel(
                box,
                text=subtitle,
                font=Theme.FONT_CAPTION,
                text_color=Theme.DARK_TEXT,
                wraplength=110,
                justify="center"
            )
            s.pack()

            if i < len(steps) - 1:
                arrow = ctk.CTkLabel(
                    flow_frame,
                    text="→",
                    font=(Theme.FONT_FAMILY, 16, "bold"),
                    text_color=Theme.SECONDARY_TEXT
                )
                arrow.pack(side="left", padx=2)

    def _build_footer(self):
        """Landing page footer."""
        foot_frame = ctk.CTkFrame(self, fg_color="transparent")
        foot_frame.pack(fill="x", padx=40, pady=(10, 40))

        lbl = ctk.CTkLabel(
            foot_frame,
            text=f"{PROJECT_NAME} — {TAGLINE}  |  Scalable Institution-Neutral Architecture",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        )
        lbl.pack(anchor="center")
