"""
CAMPUSX — Discover People Behind the Work System
Communities View: Academic and Research Groups Across Campus
Features: Real Database Member Counts, Join/Leave Functionality, My Communities Filter,
and Dedicated Full Community Details Page.
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional
from api_client.client import api_client, APIClientError
from services.research_service import ResearchService
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge,
    enable_mousewheel
)


class CommunitiesView(ctk.CTkScrollableFrame):
    """Academic communities, research collectives, and laboratory groups directory."""

    def __init__(
        self,
        parent,
        on_select_researcher: Callable[[int], None],
        current_user: Optional[Dict[str, Any]] = None
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.on_select_researcher = on_select_researcher
        self.current_user = current_user or {}

        # View state
        self.current_tab: str = "all"  # "all" or "my"
        self.active_detail_id: Optional[int] = None
        self.communities: List[Dict[str, Any]] = []
        self.my_communities: List[Dict[str, Any]] = []
        self.status_message: Optional[str] = None
        self.status_type: str = "info"  # "success", "error", "info"
        self.loading: bool = False
        self.error: Optional[str] = None

        enable_mousewheel(self)
        self._load_data()
        self._render_view()

    # =========================================================================
    # DATA LOADING & BACKEND INTEGRATION
    # =========================================================================

    def _get_user_id(self) -> Optional[int]:
        uid = self.current_user.get("id")
        if uid:
            try:
                return int(uid)
            except (ValueError, TypeError):
                pass
        if api_client.current_user:
            cuid = api_client.current_user.get("id")
            if cuid:
                try:
                    return int(cuid)
                except (ValueError, TypeError):
                    pass
        return None

    def _load_data(self):
        self.loading = True
        self.error = None
        user_id = self._get_user_id()

        try:
            # 1. Load all communities with live membership flag for current user
            try:
                self.communities = api_client.get_communities(user_id=user_id)
            except Exception:
                self.communities = ResearchService.get_communities(user_id=user_id)

            # 2. Load user's joined communities
            if user_id:
                try:
                    self.my_communities = api_client.get_my_communities(user_id=user_id)
                except Exception:
                    self.my_communities = ResearchService.get_user_communities(user_id)
            else:
                self.my_communities = []

        except Exception as exc:
            self.error = str(exc)
            self.communities = []
            self.my_communities = []
        finally:
            self.loading = False

    # =========================================================================
    # RENDER DISPATCHER
    # =========================================================================

    def _render_view(self):
        for widget in self.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

        if self.active_detail_id is not None:
            self._render_community_details_view(self.active_detail_id)
        else:
            self._render_communities_list_view()

    # =========================================================================
    # LIST VIEW (ALL COMMUNITIES & MY COMMUNITIES)
    # =========================================================================

    def _render_communities_list_view(self):
        # 1. Header
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(20, 10))

        title_box = ctk.CTkFrame(head, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="Academic & Research Communities",
            font=Theme.FONT_TITLE,
            text_color=Theme.NAVY
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Connect with faculty-led labs, student chapters, and interdisciplinary collectives across campus.",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        subtitle.pack(anchor="w")

        # Tabs / Filter on the right
        tab_box = ctk.CTkFrame(head, fg_color=Theme.MUTED_BG, corner_radius=Theme.RADIUS_BUTTON, height=36)
        tab_box.pack(side="right", pady=5)

        all_active = (self.current_tab == "all")
        all_btn = ctk.CTkButton(
            tab_box,
            text=f"🌐 All Communities ({len(self.communities)})",
            command=lambda: self._switch_tab("all"),
            height=30,
            corner_radius=Theme.RADIUS_BUTTON - 2,
            fg_color=Theme.WHITE if all_active else "transparent",
            text_color=Theme.NAVY if all_active else Theme.SECONDARY_TEXT,
            hover_color=Theme.WHITE,
            font=Theme.FONT_BODY_BOLD if all_active else Theme.FONT_BODY
        )
        all_btn.pack(side="left", padx=3, pady=3)

        my_active = (self.current_tab == "my")
        my_btn = ctk.CTkButton(
            tab_box,
            text=f"⭐ My Communities ({len(self.my_communities)})",
            command=lambda: self._switch_tab("my"),
            height=30,
            corner_radius=Theme.RADIUS_BUTTON - 2,
            fg_color=Theme.WHITE if my_active else "transparent",
            text_color=Theme.NAVY if my_active else Theme.SECONDARY_TEXT,
            hover_color=Theme.WHITE,
            font=Theme.FONT_BODY_BOLD if my_active else Theme.FONT_BODY
        )
        my_btn.pack(side="left", padx=3, pady=3)

        # 2. Status Banner (if any join/leave feedback)
        if self.status_message:
            s_bg = "#DCFCE7" if self.status_type == "success" else ("#FEE2E2" if self.status_type == "error" else "#EBF4FF")
            s_fg = "#166534" if self.status_type == "success" else ("#991B1B" if self.status_type == "error" else Theme.ACADEMIC_BLUE)

            banner = ctk.CTkFrame(self, fg_color=s_bg, corner_radius=8)
            banner.pack(fill="x", padx=25, pady=(0, 14))

            inner_b = ctk.CTkFrame(banner, fg_color="transparent")
            inner_b.pack(fill="x", padx=14, pady=10)

            ctk.CTkLabel(
                inner_b,
                text=self.status_message,
                font=Theme.FONT_BODY_BOLD,
                text_color=s_fg
            ).pack(side="left")

            close_btn = ctk.CTkButton(
                inner_b,
                text="✕",
                command=self._clear_status,
                width=24,
                height=24,
                fg_color="transparent",
                text_color=s_fg,
                hover_color=s_bg,
                font=Theme.FONT_BODY_BOLD
            )
            close_btn.pack(side="right")

        # 3. Loading & Error States
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

        # 4. Active List Selection
        display_list = self.my_communities if self.current_tab == "my" else self.communities

        # Empty State for My Communities
        if self.current_tab == "my" and not display_list:
            empty_card = create_card(self)
            empty_card.pack(fill="x", padx=25, pady=20)
            inner_e = ctk.CTkFrame(empty_card, fg_color="transparent")
            inner_e.pack(fill="both", expand=True, padx=30, pady=40)

            ctk.CTkLabel(inner_e, text="⭐", font=(Theme.FONT_FAMILY, 36)).pack(pady=(0, 8))
            ctk.CTkLabel(inner_e, text="You Haven't Joined Any Communities Yet", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(pady=(0, 6))
            ctk.CTkLabel(
                inner_e,
                text="Collaborate with faculty and fellow researchers by joining active campus collectives. "
                     "Browse available research groups, lab teams, and interest clusters in All Communities.",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=540,
                justify="center"
            ).pack(pady=(0, 20))

            explore_btn = create_primary_button(
                inner_e,
                text="Browse All Communities →",
                command=lambda: self._switch_tab("all"),
                height=38,
                width=220
            )
            explore_btn.pack()
            return

        # Empty State for All Communities
        if not display_list:
            empty = create_card(self)
            empty.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(empty, text="No communities recorded for this campus yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(pady=30)
            return

        # 5. Communities Cards Grid
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=25, pady=(0, 30))
        grid.columnconfigure((0, 1), weight=1, uniform="comm_grid")

        for idx, c in enumerate(display_list):
            row = idx // 2
            col = idx % 2
            self._render_community_card(grid, c, row, col)

    def _render_community_card(self, parent: ctk.CTkFrame, c: Dict[str, Any], row: int, col: int):
        cid = c["id"]
        is_member = c.get("is_member", False)
        member_cnt = c.get("member_count", 0)

        card = create_card(parent)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        # Top Bar: Category badge, Joined pill, and live Member Count badge
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))

        create_badge(top, text=c.get("category", "Research Group"), bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left")

        # Right badges: Joined status badge + Real dynamic member count
        cnt_badge = create_badge(top, text=f"👥 {member_cnt} Members", bg_color="#F3F0FF", text_color=Theme.PURPLE)
        cnt_badge.pack(side="right")

        if is_member:
            create_badge(top, text="✓ Joined", bg_color="#DCFCE7", text_color="#15803D").pack(side="right", padx=(0, 6))

        # Title / Community Name
        t_lbl = ctk.CTkLabel(
            inner,
            text=c["name"],
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY,
            wraplength=340,
            justify="left"
        )
        t_lbl.pack(anchor="w", pady=(6, 4))

        # Affiliation
        inst_name = c.get("institution_name", "Campus Wide")
        ctk.CTkLabel(
            inner,
            text=f"🏛️ Affiliation: {inst_name}",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 6))

        # Description
        desc = c.get("description", "")
        ctk.CTkLabel(
            inner,
            text=desc,
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=340,
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        # Key Members / Faculty Leads
        members = c.get("key_members", [])
        if members:
            m_frame = ctk.CTkFrame(inner, fg_color=Theme.SOFT_BG, corner_radius=8)
            m_frame.pack(fill="x", pady=(0, 12))

            m_inner = ctk.CTkFrame(m_frame, fg_color="transparent")
            m_inner.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(
                m_inner,
                text="Faculty Leads & Active Scholars:",
                font=Theme.FONT_CAPTION,
                text_color=Theme.NAVY
            ).pack(anchor="w", pady=(0, 4))

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

        # Bottom Action Bar: "View Details" and "Join/Leave" Button
        btn_bar = ctk.CTkFrame(inner, fg_color="transparent")
        btn_bar.pack(fill="x", pady=(4, 0))

        details_btn = create_secondary_button(
            btn_bar,
            text="View Details →",
            command=lambda cid=cid: self._open_community_details(cid),
            height=32,
            width=110
        )
        details_btn.pack(side="left")

        # Real Join / Leave action button
        if is_member:
            leave_btn = ctk.CTkButton(
                btn_bar,
                text="Leave Community",
                command=lambda cid=cid: self._handle_leave_community(cid),
                height=32,
                corner_radius=Theme.RADIUS_BUTTON,
                fg_color="#FEE2E2",
                hover_color="#FECACA",
                text_color=Theme.DANGER,
                font=Theme.FONT_BODY_BOLD
            )
            leave_btn.pack(side="right")
        else:
            join_btn = create_primary_button(
                btn_bar,
                text="Join Community",
                command=lambda cid=cid: self._handle_join_community(cid),
                height=32,
                width=130
            )
            join_btn.pack(side="right")

    # =========================================================================
    # DEDICATED COMMUNITY DETAILS PAGE
    # =========================================================================

    def _render_community_details_view(self, community_id: int):
        user_id = self._get_user_id()
        detail: Optional[Dict[str, Any]] = None

        try:
            try:
                detail = api_client.get_community_detail(community_id, user_id=user_id)
            except Exception:
                detail = ResearchService.get_community_detail(community_id, user_id=user_id)
        except Exception as exc:
            self.error = str(exc)

        # Back Navigation Bar
        nav_bar = ctk.CTkFrame(self, fg_color="transparent")
        nav_bar.pack(fill="x", padx=25, pady=(16, 8))

        back_btn = create_secondary_button(
            nav_bar,
            text="← Back to Communities",
            command=self._close_community_details,
            height=32,
            width=170
        )
        back_btn.pack(side="left")

        # Status Message (if join/leave was clicked inside details)
        if self.status_message:
            s_bg = "#DCFCE7" if self.status_type == "success" else ("#FEE2E2" if self.status_type == "error" else "#EBF4FF")
            s_fg = "#166534" if self.status_type == "success" else ("#991B1B" if self.status_type == "error" else Theme.ACADEMIC_BLUE)

            banner = ctk.CTkFrame(self, fg_color=s_bg, corner_radius=8)
            banner.pack(fill="x", padx=25, pady=(4, 10))

            inner_b = ctk.CTkFrame(banner, fg_color="transparent")
            inner_b.pack(fill="x", padx=14, pady=8)

            ctk.CTkLabel(
                inner_b,
                text=self.status_message,
                font=Theme.FONT_BODY_BOLD,
                text_color=s_fg
            ).pack(side="left")

            close_btn = ctk.CTkButton(
                inner_b,
                text="✕",
                command=self._clear_status,
                width=24,
                height=24,
                fg_color="transparent",
                text_color=s_fg,
                hover_color=s_bg,
                font=Theme.FONT_BODY_BOLD
            )
            close_btn.pack(side="right")

        if not detail:
            err_card = create_card(self)
            err_card.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(err_card, text="Community details could not be retrieved.", font=Theme.FONT_TITLE, text_color=Theme.DANGER).pack(pady=20)
            return

        is_member = detail.get("is_member", False)
        member_cnt = detail.get("member_count", 0)

        # --- 1. HERO HEADER CARD ---
        hero_card = create_card(self, fg_color=Theme.WHITE)
        hero_card.pack(fill="x", padx=25, pady=(0, 14))

        hero_inner = ctk.CTkFrame(hero_card, fg_color="transparent")
        hero_inner.pack(fill="x", padx=24, pady=20)

        # Top pill row
        p_row = ctk.CTkFrame(hero_inner, fg_color="transparent")
        p_row.pack(fill="x", pady=(0, 8))

        create_badge(p_row, text=detail.get("category", "Research Collective"), bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left")
        create_badge(p_row, text=f"👥 {member_cnt} Total Members", bg_color="#F3F0FF", text_color=Theme.PURPLE).pack(side="left", padx=8)

        if is_member:
            role_text = detail.get("user_role") or "Active Member"
            create_badge(p_row, text=f"✓ You are a {role_text}", bg_color="#DCFCE7", text_color="#15803D").pack(side="left")

        # Title & Affiliation
        title_box = ctk.CTkFrame(hero_inner, fg_color="transparent")
        title_box.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            title_box,
            text=detail["name"],
            font=Theme.FONT_HERO,
            text_color=Theme.NAVY,
            wraplength=640,
            justify="left"
        ).pack(anchor="w")

        inst_str = detail.get("institution_name") or "Campus-wide Consortium"
        ctk.CTkLabel(
            title_box,
            text=f"🏛️ Campus Affiliation: {inst_str}",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(2, 0))

        # Join / Leave Action Bar inside Hero
        action_bar = ctk.CTkFrame(hero_inner, fg_color="transparent")
        action_bar.pack(fill="x", pady=(10, 0))

        if is_member:
            leave_btn = ctk.CTkButton(
                action_bar,
                text="Leave Community",
                command=lambda cid=community_id: self._handle_leave_community(cid),
                height=36,
                corner_radius=Theme.RADIUS_BUTTON,
                fg_color="#FEE2E2",
                hover_color="#FECACA",
                text_color=Theme.DANGER,
                font=Theme.FONT_BODY_BOLD
            )
            leave_btn.pack(side="left")
        else:
            join_btn = create_primary_button(
                action_bar,
                text="Join This Community",
                command=lambda cid=community_id: self._handle_join_community(cid),
                height=36,
                width=180
            )
            join_btn.pack(side="left")

        # --- 2. DESCRIPTION & OBJECTIVES CARD ---
        desc_card = create_card(self, fg_color=Theme.WHITE)
        desc_card.pack(fill="x", padx=25, pady=(0, 14))

        d_inner = ctk.CTkFrame(desc_card, fg_color="transparent")
        d_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            d_inner,
            text="ABOUT & MISSION OBJECTIVES",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            d_inner,
            text="Community Mission & Scope",
            font=Theme.FONT_SECTION,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            d_inner,
            text=detail.get("description", "No detailed description recorded."),
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=660,
            justify="left"
        ).pack(anchor="w", pady=(0, 12))

        # Specific objectives bullet list
        obj_box = ctk.CTkFrame(d_inner, fg_color=Theme.SOFT_BG, corner_radius=8)
        obj_box.pack(fill="x", pady=(0, 4))
        obj_inner = ctk.CTkFrame(obj_box, fg_color="transparent")
        obj_inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(obj_inner, text="Key Academic Objectives:", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 6))
        objectives = [
            "Foster cross-departmental research collaborations and co-authored publications.",
            "Host bi-weekly academic seminars, paper readings, and thesis defense discussions.",
            "Share specialized lab equipment, dataset repositories, and high-performance computing resources.",
            "Mentor undergraduate and postgraduate scholars in advanced research methodologies."
        ]
        for obj in objectives:
            ctk.CTkLabel(obj_inner, text=f"•  {obj}", font=Theme.FONT_BODY, text_color=Theme.DARK_TEXT, wraplength=620, justify="left").pack(anchor="w", pady=2)

        # --- 3. FACULTY LEADS & COORDINATORS ---
        leads_card = create_card(self, fg_color=Theme.WHITE)
        leads_card.pack(fill="x", padx=25, pady=(0, 14))

        l_inner = ctk.CTkFrame(leads_card, fg_color="transparent")
        l_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(
            l_inner,
            text="LEADERSHIP & ADVISORY",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            l_inner,
            text="Faculty Leads & Principal Investigators",
            font=Theme.FONT_SECTION,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 12))

        leads = detail.get("faculty_leads", [])
        if leads:
            for lead in leads:
                lead_box = ctk.CTkFrame(l_inner, fg_color=Theme.SOFT_BG, corner_radius=8)
                lead_box.pack(fill="x", pady=4)

                lb_inner = ctk.CTkFrame(lead_box, fg_color="transparent")
                lb_inner.pack(fill="x", padx=14, pady=10)

                # Avatar initials
                init = "".join([w[0] for w in lead["name"].split() if w])[:2].upper()
                av = ctk.CTkLabel(
                    lb_inner,
                    text=init,
                    font=(Theme.FONT_FAMILY, 11, "bold"),
                    fg_color=lead.get("avatar_color", Theme.ACADEMIC_BLUE),
                    text_color=Theme.WHITE,
                    corner_radius=16,
                    width=32,
                    height=32
                )
                av.pack(side="left", padx=(0, 10))

                info_f = ctk.CTkFrame(lb_inner, fg_color="transparent")
                info_f.pack(side="left")

                ctk.CTkLabel(
                    info_f,
                    text=lead["name"],
                    font=Theme.FONT_BODY_BOLD,
                    text_color=Theme.NAVY
                ).pack(anchor="w")

                role_str = lead.get("role", "Faculty Lead")
                desig_str = lead.get("designation") or "Researcher"
                dept_str = lead.get("department_name") or "Academic Department"
                ctk.CTkLabel(
                    info_f,
                    text=f"{role_str} · {desig_str} ({dept_str})",
                    font=Theme.FONT_CAPTION,
                    text_color=Theme.SECONDARY_TEXT
                ).pack(anchor="w")

                prof_btn = ctk.CTkButton(
                    lb_inner,
                    text="View Profile →",
                    command=lambda mid=lead["id"]: self.on_select_researcher(mid),
                    width=100,
                    height=28,
                    corner_radius=Theme.RADIUS_BUTTON,
                    fg_color="#EFF6FF",
                    text_color=Theme.ACADEMIC_BLUE,
                    hover_color="#DBEAFE",
                    font=Theme.FONT_CAPTION
                )
                prof_btn.pack(side="right")
        else:
            ctk.CTkLabel(l_inner, text="No faculty leads officially assigned yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

        # --- 4. ASSOCIATED RESEARCH AREAS ---
        areas_card = create_card(self, fg_color=Theme.WHITE)
        areas_card.pack(fill="x", padx=25, pady=(0, 14))

        a_inner = ctk.CTkFrame(areas_card, fg_color="transparent")
        a_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(a_inner, text="TAXONOMY & FOCUS", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(a_inner, text="Associated Research Areas & Topics", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 10))

        areas = detail.get("research_areas", [])
        if areas:
            a_chip_frame = ctk.CTkFrame(a_inner, fg_color="transparent")
            a_chip_frame.pack(fill="x")

            curr_row = ctk.CTkFrame(a_chip_frame, fg_color="transparent")
            curr_row.pack(fill="x", pady=2)
            curr_w = 0.0

            for area in areas:
                name = area.get("name") if isinstance(area, dict) else str(area)
                approx_w = len(name) * 7.5 + 24.0

                if curr_w > 0 and (curr_w + approx_w > 620.0):
                    curr_row = ctk.CTkFrame(a_chip_frame, fg_color="transparent")
                    curr_row.pack(fill="x", pady=2)
                    curr_w = 0.0

                create_badge(
                    curr_row,
                    text=f"🔬 {name}",
                    bg_color="#EEF2FF",
                    text_color=Theme.ACADEMIC_BLUE,
                    font=Theme.FONT_BODY_BOLD
                ).pack(side="left", padx=4, pady=3)
                curr_w += approx_w
        else:
            ctk.CTkLabel(a_inner, text="General interdisciplinary collective covering campus-wide research.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

        # --- 5. ACTUAL COMMUNITY MEMBERS DIRECTORY ---
        mem_card = create_card(self, fg_color=Theme.WHITE)
        mem_card.pack(fill="x", padx=25, pady=(0, 14))

        m_sec_inner = ctk.CTkFrame(mem_card, fg_color="transparent")
        m_sec_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(m_sec_inner, text="ROSTER", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(m_sec_inner, text=f"Community Members ({len(detail.get('members', []))})", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 10))

        members = detail.get("members", [])
        if members:
            for m in members:
                m_row = ctk.CTkFrame(m_sec_inner, fg_color=Theme.SOFT_BG, corner_radius=6)
                m_row.pack(fill="x", pady=3)

                mr_inner = ctk.CTkFrame(m_row, fg_color="transparent")
                mr_inner.pack(fill="x", padx=12, pady=8)

                # Initials
                init = "".join([w[0] for w in m["name"].split() if w])[:2].upper()
                av = ctk.CTkLabel(
                    mr_inner,
                    text=init,
                    font=(Theme.FONT_FAMILY, 9, "bold"),
                    fg_color=m.get("avatar_color", Theme.ACADEMIC_BLUE),
                    text_color=Theme.WHITE,
                    corner_radius=14,
                    width=28,
                    height=28
                )
                av.pack(side="left", padx=(0, 8))

                name_box = ctk.CTkFrame(mr_inner, fg_color="transparent")
                name_box.pack(side="left")

                ctk.CTkLabel(name_box, text=m["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w")
                desig_line = f"{m.get('designation', 'Scholar')} · {m.get('department_name', 'General')}"
                ctk.CTkLabel(name_box, text=desig_line, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

                # Role badge
                create_badge(
                    mr_inner,
                    text=m.get("role", "Member"),
                    bg_color="#F1F5F9",
                    text_color=Theme.NAVY,
                    font=Theme.FONT_CAPTION
                ).pack(side="right", padx=(8, 0))

                # Profile button
                v_btn = ctk.CTkButton(
                    mr_inner,
                    text="Profile",
                    command=lambda mid=m["id"]: self.on_select_researcher(mid),
                    width=60,
                    height=24,
                    corner_radius=4,
                    fg_color="transparent",
                    text_color=Theme.ACADEMIC_BLUE,
                    hover_color=Theme.MUTED_BG,
                    font=Theme.FONT_CAPTION
                )
                v_btn.pack(side="right")
        else:
            ctk.CTkLabel(m_sec_inner, text="No members currently registered in this community.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

        # --- 6. ANNOUNCEMENTS & ACTIVITIES STATUS ---
        ann_card = create_card(self, fg_color=Theme.WHITE)
        ann_card.pack(fill="x", padx=25, pady=(0, 30))

        ann_inner = ctk.CTkFrame(ann_card, fg_color="transparent")
        ann_inner.pack(fill="x", padx=24, pady=18)

        ctk.CTkLabel(ann_inner, text="COMMUNICATIONS & EVENTS", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(ann_inner, text="Announcements & Activities", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            ann_inner,
            text="ℹ️ No announcements or activities have been posted for this collective yet. "
                 "Future event announcements and workshop schedules will appear in this section once scheduled by community leads.",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT,
            wraplength=640,
            justify="left"
        ).pack(anchor="w")

    # =========================================================================
    # USER INTERACTIONS: JOIN / LEAVE / TABS
    # =========================================================================

    def _switch_tab(self, tab: str):
        self.current_tab = tab
        self.active_detail_id = None
        self._clear_status()
        self._load_data()
        self._render_view()

    def _open_community_details(self, community_id: int):
        self.active_detail_id = community_id
        self._clear_status()
        self._render_view()

    def _close_community_details(self):
        self.active_detail_id = None
        self._clear_status()
        self._load_data()
        self._render_view()

    def _clear_status(self):
        self.status_message = None
        self.status_type = "info"

    def _handle_join_community(self, community_id: int):
        user_id = self._get_user_id()
        if not user_id:
            self.status_message = "Please sign in to join an academic community."
            self.status_type = "error"
            self._render_view()
            return

        try:
            try:
                res = api_client.join_community(community_id, user_id=user_id)
                msg = res.get("message", "Successfully joined the community!")
            except Exception:
                ok, msg, _ = ResearchService.join_community(community_id, user_id=user_id)
                if not ok:
                    raise APIClientError(msg)

            self.status_message = msg
            self.status_type = "success"
        except Exception as exc:
            self.status_message = str(exc)
            self.status_type = "error"

        self._load_data()
        self._render_view()

    def _handle_leave_community(self, community_id: int):
        user_id = self._get_user_id()
        if not user_id:
            self.status_message = "Please sign in to manage community membership."
            self.status_type = "error"
            self._render_view()
            return

        try:
            try:
                res = api_client.leave_community(community_id, user_id=user_id)
                msg = res.get("message", "Successfully left the community.")
            except Exception:
                ok, msg, _ = ResearchService.leave_community(community_id, user_id=user_id)
                if not ok:
                    raise APIClientError(msg)

            self.status_message = msg
            self.status_type = "success"
        except Exception as exc:
            self.status_message = str(exc)
            self.status_type = "error"

        self._load_data()
        self._render_view()
