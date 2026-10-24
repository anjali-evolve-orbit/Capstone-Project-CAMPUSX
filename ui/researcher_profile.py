"""
CAMPUSX — Discover People Behind the Work System
Researcher Profile: Detailed Biography, Publications, Areas, and Collaboration Network
"""

import customtkinter as ctk
from typing import Any, Callable, Dict, Optional
from api_client.client import api_client
from services.research_service import ResearchService
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge
)
from ui.theme import enable_mousewheel


class ResearcherProfileView(ctk.CTkScrollableFrame):
    """Detailed profile view for an individual researcher."""

    def __init__(
        self,
        parent,
        researcher_id: int,
        on_back: Callable[[], None],
        on_select_paper: Callable[[int], None],
        on_select_researcher: Callable[[int], None]
    ,
        current_user: Optional[Dict[str, Any]] = None
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        enable_mousewheel(self)
        self.researcher_id = researcher_id
        self.on_back = on_back
        self.on_select_paper = on_select_paper
        self.on_select_researcher = on_select_researcher
        self.current_user = current_user

        self.profile: Optional[Dict[str, Any]] = None
        self._editing_skills = False
        self._edit_skills_list = []
        self._load_profile()
        self._build_ui()

    def _is_editable(self, p: Optional[Dict[str, Any]] = None) -> bool:
        """Verify whether the current user is allowed to edit this researcher profile."""
        if not self.current_user:
            return False
        prof = p if p is not None else self.profile
        if not prof:
            return False
        curr_uid = self.current_user.get("id")
        prof_uid = prof.get("user_id")
        if curr_uid is not None and prof_uid is not None and int(curr_uid) == int(prof_uid):
            return True
        curr_email = (self.current_user.get("email") or "").strip().lower()
        prof_email = (prof.get("email") or "").strip().lower()
        if curr_email and prof_email and curr_email == prof_email:
            return True
        return False

    def _load_profile(self):
        try:
            self.profile = api_client.get_researcher_detail(self.researcher_id)
        except Exception:
            try:
                self.profile = ResearchService.get_researcher_detail(self.researcher_id)
            except Exception:
                self.profile = None

    def _get_current_researcher_id(self) -> Optional[int]:
        """Return the researcher_id of the logged-in user, or None if not found."""
        if not self.current_user:
            return None
        uid = self.current_user.get("id")
        if uid is None:
            return None
        try:
            results = api_client.search_researchers("")
            email = (self.current_user.get("email") or "").strip().lower()
            for r in results:
                if (r.get("user_id") is not None and int(r["user_id"]) == int(uid)) or \
                   (email and (r.get("email") or "").strip().lower() == email):
                    return r["id"]
        except Exception:
            pass
        return None

    def _render_connection_button(self):
        """Draw the appropriate connection action button based on current status."""
        frame = getattr(self, "_conn_btn_frame", None)
        if not frame or not frame.winfo_exists():
            return
        for child in frame.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass

        current_rid = self._get_current_researcher_id()
        if current_rid is None:
            return  # Not logged in as a researcher

        try:
            status_data = api_client.get_connection_status(current_rid, self.researcher_id)
            status = (status_data.get("status") or "NONE").upper()
            conn_id = status_data.get("request_id") or status_data.get("connection_id")
        except Exception:
            status = "NONE"
            conn_id = None

        if status == "NONE":
            btn = create_primary_button(
                frame, text="🔗 Connect", width=140, height=34,
                command=lambda: self._send_connect_request(current_rid)
            )
            btn.pack()
        elif status == "PENDING_SENT":
            btn = ctk.CTkButton(
                frame, text="⏳ Request Sent (Cancel)", width=170, height=34,
                fg_color="#F59E0B", hover_color="#D97706",
                text_color=Theme.WHITE, font=Theme.FONT_BODY_BOLD,
                command=lambda: self._cancel_request(conn_id, current_rid)
            )
            btn.pack()
        elif status == "PENDING_RECEIVED":
            # Show Accept + Reject side by side
            accept_btn = ctk.CTkButton(
                frame, text="✅ Accept", width=90, height=34,
                fg_color="#16A34A", hover_color="#15803D",
                text_color=Theme.WHITE, font=Theme.FONT_BODY_BOLD,
                command=lambda: self._accept_request(conn_id, current_rid)
            )
            accept_btn.pack(side="left", padx=(0, 6))
            reject_btn = ctk.CTkButton(
                frame, text="✕ Reject", width=80, height=34,
                fg_color=Theme.DANGER, hover_color="#B91C1C",
                text_color=Theme.WHITE, font=Theme.FONT_BODY_BOLD,
                command=lambda: self._reject_request(conn_id, current_rid)
            )
            reject_btn.pack(side="left")
        elif status == "ACCEPTED":
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack()
            ctk.CTkLabel(
                row,
                text="✓ Connected",
                font=Theme.FONT_BODY_BOLD,
                text_color="#16A34A"
            ).pack(side="left", padx=(0, 8))
            disc_btn = ctk.CTkButton(
                row,
                text="Disconnect",
                width=85,
                height=28,
                fg_color="transparent",
                hover_color="#FEE2E2",
                text_color=Theme.DANGER,
                font=Theme.FONT_CAPTION,
                command=lambda: self._confirm_disconnect(conn_id, current_rid, self.profile.get("name", "Researcher"))
            )
            disc_btn.pack(side="left")
        elif status == "REJECTED":
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack()
            ctk.CTkLabel(
                row,
                text="Request Declined",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(side="left", padx=(0, 8))
            btn = ctk.CTkButton(
                row,
                text="🔗 Connect Again",
                width=120,
                height=30,
                fg_color=Theme.ACADEMIC_BLUE,
                hover_color=Theme.NAVY,
                text_color=Theme.WHITE,
                font=Theme.FONT_CAPTION,
                command=lambda: self._send_connect_request(current_rid)
            )
            btn.pack(side="left")

    def _send_connect_request(self, sender_id: int):
        try:
            api_client.send_connection_request(sender_id, self.researcher_id)
            self._render_connection_button()
            self._refresh_profile()
        except Exception:
            self._render_connection_button()

    def _cancel_request(self, conn_id: Optional[int], current_rid: int):
        if conn_id is None:
            return
        try:
            api_client.cancel_connection_request(conn_id, current_rid)
            self._render_connection_button()
            self._refresh_profile()
        except Exception:
            pass

    def _accept_request(self, conn_id: Optional[int], current_rid: int):
        if conn_id is None:
            return
        try:
            api_client.accept_connection_request(conn_id, current_rid)
            self._render_connection_button()
            self._refresh_profile()
        except Exception:
            pass

    def _reject_request(self, conn_id: Optional[int], current_rid: int):
        if conn_id is None:
            return
        try:
            api_client.reject_connection_request(conn_id, current_rid)
            self._render_connection_button()
            self._refresh_profile()
        except Exception:
            pass

    def _confirm_disconnect(self, conn_id: Optional[int], current_rid: int, peer_name: str):
        if conn_id is None or current_rid is None:
            return
        modal = ctk.CTkToplevel(self)
        self._setup_dialog(modal, "Disconnect Connection", 420, 210)

        inner = ctk.CTkFrame(modal, fg_color=Theme.WHITE)
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            inner,
            text=f"Disconnect with {peer_name}?",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(
            inner,
            text=f"Are you sure you want to remove {peer_name} from your connections? You will no longer receive their research updates in your activity feed.",
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=370,
            justify="left"
        ).pack(anchor="w", pady=(0, 20))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")

        def do_disconnect():
            try:
                api_client.disconnect_researcher(conn_id, current_rid)
            except Exception:
                pass
            try:
                modal.destroy()
            except Exception:
                pass
            self._refresh_profile()

        ctk.CTkButton(
            btn_row,
            text="Yes, Disconnect",
            fg_color=Theme.DANGER,
            hover_color="#B91C1C",
            text_color=Theme.WHITE,
            font=Theme.FONT_BODY_BOLD,
            width=130,
            height=34,
            command=do_disconnect
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.DARK_TEXT,
            font=Theme.FONT_BODY,
            width=80,
            height=34,
            command=modal.destroy
        ).pack(side="right")

    def _build_incoming_requests_section(self):
        """Build the incoming connection requests section for the logged-in researcher."""
        current_rid = self._get_current_researcher_id()
        if not current_rid:
            return

        try:
            incoming = api_client.get_received_connection_requests(current_rid, status="PENDING")
            if not isinstance(incoming, list):
                incoming = []
        except Exception:
            incoming = []

        req_card = create_card(self)
        req_card.pack(fill="x", padx=25, pady=(0, 15))

        r_inner = ctk.CTkFrame(req_card, fg_color="transparent")
        r_inner.pack(fill="both", expand=True, padx=20, pady=16)

        hdr_row = ctk.CTkFrame(r_inner, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            hdr_row,
            text="📥 Connection Requests",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(side="left")

        badge_bg = "#FEF3C7" if incoming else "#E2E8F0"
        badge_fg = "#D97706" if incoming else Theme.SECONDARY_TEXT
        badge_txt = f"{len(incoming)} Pending Request{'s' if len(incoming) != 1 else ''}"
        create_badge(hdr_row, text=badge_txt, bg_color=badge_bg, text_color=badge_fg).pack(side="right")

        if not incoming:
            empty_box = ctk.CTkFrame(r_inner, fg_color=Theme.SOFT_BG, corner_radius=8)
            empty_box.pack(fill="x", pady=4)
            ctk.CTkLabel(
                empty_box,
                text="✓ You're all caught up! No pending connection requests at this time.",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            ).pack(padx=16, pady=12, anchor="w")
            return

        for req in incoming:
            req_id = req["id"]
            s_name = req.get("sender_name", "Researcher")
            s_desig = req.get("sender_designation", "")
            s_dept = req.get("department_name", "")
            s_inst = req.get("institution_name", "")
            s_color = req.get("sender_avatar_color") or Theme.ACADEMIC_BLUE
            s_initials = "".join([part[0] for part in s_name.split() if part])[:2]
            s_areas = req.get("areas", [])
            s_skills = req.get("skills", [])

            item_box = ctk.CTkFrame(r_inner, fg_color=Theme.SOFT_BG, border_color="#E2E8F0", border_width=1, corner_radius=10)
            item_box.pack(fill="x", pady=5)

            item_inner = ctk.CTkFrame(item_box, fg_color="transparent")
            item_inner.pack(fill="both", expand=True, padx=14, pady=12)

            s_av = ctk.CTkLabel(
                item_inner,
                text=s_initials,
                font=(Theme.FONT_FAMILY, 14, "bold"),
                fg_color=s_color,
                text_color=Theme.WHITE,
                corner_radius=20,
                width=40,
                height=40
            )
            s_av.pack(side="left", padx=(0, 12))

            det_col = ctk.CTkFrame(item_inner, fg_color="transparent")
            det_col.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(det_col, text=s_name, font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w")

            meta_str = f"{s_desig}" + (f" · {s_dept}" if s_dept else "") + (f" · {s_inst}" if s_inst else "")
            ctk.CTkLabel(det_col, text=meta_str, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(1, 4))

            tags = []
            if s_areas:
                tags.extend([f"🔬 {a}" for a in s_areas[:2]])
            if s_skills:
                tags.extend([f"💡 {s}" for s in s_skills[:2]])
            if tags:
                tag_row = ctk.CTkFrame(det_col, fg_color="transparent")
                tag_row.pack(anchor="w")
                for t in tags:
                    ctk.CTkLabel(
                        tag_row,
                        text=t,
                        font=(Theme.FONT_FAMILY, 9),
                        fg_color="#EEF2FF",
                        text_color=Theme.ACADEMIC_BLUE,
                        corner_radius=6,
                        height=18
                    ).pack(side="left", padx=(0, 6))

            act_col = ctk.CTkFrame(item_inner, fg_color="transparent")
            act_col.pack(side="right", padx=(10, 0))

            create_secondary_button(
                act_col,
                text="View Profile →",
                command=lambda sid=req["sender_id"]: self.on_select_researcher(sid),
                width=110,
                height=32
            ).pack(side="left", padx=(0, 8))

            accept_btn = ctk.CTkButton(
                act_col,
                text="✅ Accept",
                fg_color="#16A34A",
                hover_color="#15803D",
                text_color=Theme.WHITE,
                font=Theme.FONT_BODY_BOLD,
                width=90,
                height=32,
                command=lambda rid=req_id: self._accept_request(rid, current_rid)
            )
            accept_btn.pack(side="left", padx=(0, 6))

            reject_btn = ctk.CTkButton(
                act_col,
                text="✕ Reject",
                fg_color=Theme.DANGER,
                hover_color="#B91C1C",
                text_color=Theme.WHITE,
                font=Theme.FONT_BODY_BOLD,
                width=80,
                height=32,
                command=lambda rid=req_id: self._reject_request(rid, current_rid)
            )
            reject_btn.pack(side="left")

    def _build_connections_section(self):
        """Build the Accepted Connections (My Connections) section with rich profiles, publications, and disconnect support."""
        current_rid = self._get_current_researcher_id()
        is_my_profile = self._is_editable(self.profile)

        try:
            conns = api_client.get_researcher_connections(self.researcher_id)
            if not isinstance(conns, list):
                conns = []
        except Exception:
            conns = []

        conn_card = create_card(self)
        conn_card.pack(fill="x", padx=25, pady=(0, 15))

        c_inner = ctk.CTkFrame(conn_card, fg_color="transparent")
        c_inner.pack(fill="both", expand=True, padx=20, pady=16)

        hdr_row = ctk.CTkFrame(c_inner, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(0, 4))

        sec_title = "🤝 My Connections" if is_my_profile else "🤝 Connected Researchers"
        ctk.CTkLabel(hdr_row, text=sec_title, font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(side="left")

        badge_txt = f"{len(conns)} Connection{'s' if len(conns) != 1 else ''}"
        create_badge(hdr_row, text=badge_txt, bg_color="#EBF4FF", text_color=Theme.ACADEMIC_BLUE).pack(side="right")

        sub_desc = "Accepted peer connections across campus with direct academic ties:" if is_my_profile else "Accepted peer connections for this researcher:"
        ctk.CTkLabel(c_inner, text=sub_desc, font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 12))

        if not conns:
            empty_box = ctk.CTkFrame(c_inner, fg_color=Theme.SOFT_BG, corner_radius=8)
            empty_box.pack(fill="x", pady=6)
            msg = "No accepted connections yet. Discover researchers in the directory and connect to build your academic network!" if is_my_profile else "No accepted connections recorded yet."
            ctk.CTkLabel(empty_box, text=msg, font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(padx=16, pady=14, anchor="w")
        else:
            grid = ctk.CTkFrame(c_inner, fg_color="transparent")
            grid.pack(fill="x")
            grid.columnconfigure((0, 1), weight=1, uniform="conn_grid")

            for idx, c in enumerate(conns):
                row = idx // 2
                col = idx % 2

                box = ctk.CTkFrame(grid, fg_color=Theme.SOFT_BG, border_color="#E2E8F0", border_width=1, corner_radius=10)
                box.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

                b_inner = ctk.CTkFrame(box, fg_color="transparent")
                b_inner.pack(fill="both", expand=True, padx=14, pady=12)

                top_r = ctk.CTkFrame(b_inner, fg_color="transparent")
                top_r.pack(fill="x")

                c_initials = "".join([part[0] for part in c["name"].split() if part])[:2]
                c_color = c.get("avatar_color") or Theme.ACADEMIC_BLUE

                c_av = ctk.CTkLabel(
                    top_r,
                    text=c_initials,
                    font=(Theme.FONT_FAMILY, 12, "bold"),
                    fg_color=c_color,
                    text_color=Theme.WHITE,
                    corner_radius=16,
                    width=32,
                    height=32
                )
                c_av.pack(side="left", padx=(0, 10))

                info_top = ctk.CTkFrame(top_r, fg_color="transparent")
                info_top.pack(side="left", fill="both", expand=True)

                c_name = ctk.CTkLabel(info_top, text=c["name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY)
                c_name.pack(anchor="w")

                c_desig = f"{c.get('designation', '')} · {c.get('department_name', '')}"
                ctk.CTkLabel(info_top, text=c_desig, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

                pub_ct = c.get("publication_count", 0)
                create_badge(top_r, text=f"📄 {pub_ct} Paper{'s' if pub_ct != 1 else ''}", bg_color="#F3F0FF", text_color=Theme.PURPLE).pack(side="right")

                areas = c.get("areas", [])
                skills = c.get("skills", [])
                tag_items = []
                if areas:
                    tag_items.extend([f"🔬 {a}" for a in areas[:2]])
                if skills:
                    tag_items.extend([f"💡 {s}" for s in skills[:2]])
                if tag_items:
                    tag_row = ctk.CTkFrame(b_inner, fg_color="transparent")
                    tag_row.pack(anchor="w", pady=(8, 4))
                    for tag in tag_items:
                        ctk.CTkLabel(
                            tag_row,
                            text=tag,
                            font=(Theme.FONT_FAMILY, 9),
                            fg_color="#EEF2FF",
                            text_color=Theme.ACADEMIC_BLUE,
                            corner_radius=6,
                            height=20
                        ).pack(side="left", padx=(0, 6))

                action_row = ctk.CTkFrame(b_inner, fg_color="transparent")
                action_row.pack(fill="x", pady=(8, 0))

                prof_btn = create_secondary_button(
                    action_row,
                    text="View Profile →",
                    command=lambda cid=c["researcher_id"]: self.on_select_researcher(cid),
                    width=120,
                    height=28
                )
                prof_btn.pack(side="left")

                if is_my_profile:
                    disc_btn = ctk.CTkButton(
                        action_row,
                        text="Disconnect",
                        fg_color="transparent",
                        hover_color="#FEE2E2",
                        text_color=Theme.DANGER,
                        font=Theme.FONT_CAPTION,
                        width=80,
                        height=28,
                        command=lambda conn_id=c["connection_id"], p_name=c["name"]: self._confirm_disconnect(conn_id, current_rid, p_name)
                    )
                    disc_btn.pack(side="right")

    def _build_connection_activity_section(self):
        """Build the Connection Activity Feed section showing updates from accepted connections."""
        current_rid = self._get_current_researcher_id()
        if not current_rid:
            return

        try:
            activities = api_client.get_connection_activity(current_rid, limit=20)
            if not isinstance(activities, list):
                activities = []
        except Exception:
            activities = []

        act_card = create_card(self)
        act_card.pack(fill="x", padx=25, pady=(0, 15))

        a_inner = ctk.CTkFrame(act_card, fg_color="transparent")
        a_inner.pack(fill="both", expand=True, padx=20, pady=16)

        hdr_row = ctk.CTkFrame(a_inner, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(hdr_row, text="⚡ Updates from Connections", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(side="left")

        act_badge = f"{len(activities)} Recent Update{'s' if len(activities) != 1 else ''}"
        create_badge(hdr_row, text=act_badge, bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="right")

        ctk.CTkLabel(
            a_inner,
            text="Real-time academic activities, publications, skills, and research interest updates from your accepted connections:",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 12))

        if not activities:
            empty_box = ctk.CTkFrame(a_inner, fg_color=Theme.SOFT_BG, corner_radius=8)
            empty_box.pack(fill="x", pady=6)
            ctk.CTkLabel(
                empty_box,
                text="No recent updates from your connections yet. When your connected peers publish new papers, add skills, or expand their research areas, their updates will appear here.",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=650,
                justify="left"
            ).pack(padx=16, pady=14, anchor="w")
            return

        for act in activities:
            act_type = act.get("activity_type", "PAPER")
            badge_text = act.get("badge_text", "Update")
            r_name = act.get("researcher_name", "Researcher")
            r_color = act.get("avatar_color") or Theme.ACADEMIC_BLUE
            r_initials = "".join([part[0] for part in r_name.split() if part])[:2]
            desc = act.get("description", "")
            created_at = act.get("created_at", "")
            target_id = act.get("target_id")

            row_box = ctk.CTkFrame(a_inner, fg_color=Theme.SOFT_BG, border_color="#E2E8F0", border_width=1, corner_radius=10)
            row_box.pack(fill="x", pady=5)

            r_line = ctk.CTkFrame(row_box, fg_color="transparent")
            r_line.pack(fill="both", expand=True, padx=14, pady=10)

            ctk.CTkLabel(
                r_line,
                text=r_initials,
                font=(Theme.FONT_FAMILY, 11, "bold"),
                fg_color=r_color,
                text_color=Theme.WHITE,
                corner_radius=15,
                width=30,
                height=30
            ).pack(side="left", padx=(0, 10))

            info_col = ctk.CTkFrame(r_line, fg_color="transparent")
            info_col.pack(side="left", fill="both", expand=True)

            top_line = ctk.CTkFrame(info_col, fg_color="transparent")
            top_line.pack(anchor="w")

            ctk.CTkLabel(top_line, text=r_name, font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(side="left", padx=(0, 8))

            badge_bg = "#F3F0FF" if act_type == "PAPER" else ("#ECFDF5" if act_type == "SKILL" else "#EBF4FF")
            badge_fg = Theme.PURPLE if act_type == "PAPER" else ("#059669" if act_type == "SKILL" else Theme.ACADEMIC_BLUE)
            ctk.CTkLabel(
                top_line,
                text=badge_text,
                font=(Theme.FONT_FAMILY, 10, "bold"),
                fg_color=badge_bg,
                text_color=badge_fg,
                corner_radius=6,
                height=20
            ).pack(side="left", padx=(0, 10))

            if created_at:
                ctk.CTkLabel(top_line, text=f"🕒 {created_at}", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left")

            ctk.CTkLabel(info_col, text=desc, font=Theme.FONT_BODY, text_color=Theme.DARK_TEXT, wraplength=520, justify="left").pack(anchor="w", pady=(2, 0))

            act_btns = ctk.CTkFrame(r_line, fg_color="transparent")
            act_btns.pack(side="right", padx=(8, 0))

            if act_type == "PAPER" and target_id:
                create_secondary_button(
                    act_btns,
                    text="View Paper →",
                    command=lambda pid=target_id: self.on_select_paper(pid),
                    width=100,
                    height=28
                ).pack(side="left", padx=(0, 6))

            create_secondary_button(
                act_btns,
                text="Profile →",
                command=lambda rid=act["researcher_id"]: self.on_select_researcher(rid),
                width=80,
                height=28
            ).pack(side="left")

    def _build_collaboration_suggestions_section(self):
        """Build the Suggested Collaborators section based on shared areas and skills."""
        current_rid = self._get_current_researcher_id()
        if not current_rid:
            return

        try:
            suggestions = api_client.get_collaboration_suggestions(current_rid, limit=4)
            if not isinstance(suggestions, list):
                suggestions = []
        except Exception:
            suggestions = []

        sug_card = create_card(self)
        sug_card.pack(fill="x", padx=25, pady=(0, 20))

        s_inner = ctk.CTkFrame(sug_card, fg_color="transparent")
        s_inner.pack(fill="both", expand=True, padx=20, pady=16)

        hdr_row = ctk.CTkFrame(s_inner, fg_color="transparent")
        hdr_row.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            hdr_row,
            text="💡 Collaboration Suggestions",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(side="left")

        create_badge(
            hdr_row,
            text=f"{len(suggestions)} Recommended",
            bg_color="#FEF3C7" if suggestions else "#E2E8F0",
            text_color="#D97706" if suggestions else Theme.SECONDARY_TEXT
        ).pack(side="right")

        ctk.CTkLabel(
            s_inner,
            text="Researchers recommended based on shared research areas, complementary skills, and academic synergy:",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 12))

        if not suggestions:
            empty_box = ctk.CTkFrame(s_inner, fg_color=Theme.SOFT_BG, corner_radius=8)
            empty_box.pack(fill="x", pady=4)
            ctk.CTkLabel(
                empty_box,
                text="No collaboration recommendations found right now. Add more research areas or skills to discover matches!",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            ).pack(padx=16, pady=12, anchor="w")
            return

        grid = ctk.CTkFrame(s_inner, fg_color="transparent")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="sug_col")

        for idx, sug in enumerate(suggestions):
            s_id = sug["id"]
            s_name = sug.get("name", "Researcher")
            s_desig = sug.get("designation", "")
            s_dept = sug.get("department_name", "")
            s_inst = sug.get("institution_name", "")
            s_color = sug.get("avatar_color") or Theme.ACADEMIC_BLUE
            s_initials = "".join([part[0] for part in s_name.split() if part])[:2]
            match_reason = sug.get("match_reason") or "Complementary Research Profile"

            row_i = idx // 2
            col_i = idx % 2

            box = ctk.CTkFrame(grid, fg_color=Theme.SOFT_BG, border_color="#E2E8F0", border_width=1, corner_radius=10)
            box.grid(row=row_i, column=col_i, padx=6, pady=6, sticky="nsew")

            b_inner = ctk.CTkFrame(box, fg_color="transparent")
            b_inner.pack(fill="both", expand=True, padx=12, pady=12)

            top_row = ctk.CTkFrame(b_inner, fg_color="transparent")
            top_row.pack(fill="x")

            av = ctk.CTkLabel(
                top_row,
                text=s_initials,
                font=(Theme.FONT_FAMILY, 12, "bold"),
                fg_color=s_color,
                text_color=Theme.WHITE,
                corner_radius=18,
                width=36,
                height=36
            )
            av.pack(side="left", padx=(0, 10))

            info = ctk.CTkFrame(top_row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(info, text=s_name, font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY, anchor="w").pack(anchor="w")
            sub_meta = f"{s_desig} · {s_dept}" if s_desig and s_dept else (s_desig or s_dept or s_inst)
            ctk.CTkLabel(info, text=sub_meta, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT, anchor="w").pack(anchor="w")

            # Match Reason badge
            reason_box = ctk.CTkFrame(b_inner, fg_color="transparent")
            reason_box.pack(anchor="w", pady=(8, 4))
            create_badge(
                reason_box,
                text=f"🎯 {match_reason}",
                bg_color="#EEF2FF",
                text_color=Theme.ACADEMIC_BLUE,
                font=(Theme.FONT_FAMILY, 9)
            ).pack(side="left")

            # Action Buttons Row
            actions = ctk.CTkFrame(b_inner, fg_color="transparent")
            actions.pack(fill="x", pady=(8, 0))

            create_secondary_button(
                actions,
                text="View Profile →",
                command=lambda sid=s_id: self.on_select_researcher(sid),
                width=100,
                height=28
            ).pack(side="left")

            conn_btn = ctk.CTkButton(
                actions,
                text="🔗 Connect",
                width=90,
                height=28,
                fg_color=Theme.ACADEMIC_BLUE,
                hover_color="#173D6E",
                text_color=Theme.WHITE,
                font=Theme.FONT_CAPTION
            )
            conn_btn.pack(side="right")

            def _make_req_handler(target_id, btn):
                def _handler():
                    try:
                        btn.configure(text="Sending...", state="disabled")
                        api_client.send_connection_request(current_rid, target_id)
                        btn.configure(text="✓ Requested", fg_color="#64748B", state="disabled")
                    except Exception:
                        btn.configure(text="Failed", fg_color=Theme.DANGER, state="normal")
                return _handler

            conn_btn.configure(command=_make_req_handler(s_id, conn_btn))


    def _build_ui(self):
        # Back Button Row
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=25, pady=(15, 10))

        back_btn = ctk.CTkButton(
            top_bar,
            text="← Back to Directory",
            command=self.on_back,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD,
            width=140,
            height=30
        )
        back_btn.pack(side="left")

        # Distinguish between explicit failure (None) and an empty-but-valid profile ({}).
        if self.profile is None:
            err_card = create_card(self)
            err_card.pack(fill="x", padx=25, pady=20)
            ctk.CTkLabel(
                err_card,
                text="Researcher profile could not be loaded.",
                font=Theme.FONT_BODY,
                text_color=Theme.DANGER
            ).pack(pady=30)
            return

        p = self.profile

        # 1. Header Card (Avatar, Name, Affiliation, Key Metrics)
        header_card = create_card(self)
        header_card.pack(fill="x", padx=25, pady=(0, 15))

        h_inner = ctk.CTkFrame(header_card, fg_color="transparent")
        h_inner.pack(fill="both", expand=True, padx=25, pady=22)

        # Avatar initials circle
        initials = "".join([part[0] for part in p["name"].split() if part])[:2]
        av_col = p.get("avatar_color", Theme.ACADEMIC_BLUE)

        av_lbl = ctk.CTkLabel(
            h_inner,
            text=initials,
            font=(Theme.FONT_FAMILY, 22, "bold"),
            fg_color=av_col,
            text_color=Theme.WHITE,
            corner_radius=32,
            width=64,
            height=64
        )
        av_lbl.pack(side="left", padx=(0, 18))

        # Main Info
        info_col = ctk.CTkFrame(h_inner, fg_color="transparent")
        info_col.pack(side="left", fill="both", expand=True)

        name_lbl = ctk.CTkLabel(info_col, text=p["name"], font=Theme.FONT_TITLE, text_color=Theme.NAVY)
        name_lbl.pack(anchor="w")

        desig_lbl = ctk.CTkLabel(
            info_col,
            text=f"{p.get('designation', '')}  ·  {p.get('department_name', '')}  ·  {p.get('institution_name', '')}",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        desig_lbl.pack(anchor="w", pady=(2, 6))

        # Contact line
        contact_txt = f"📧 {p.get('email', 'N/A')}   |   🌐 {p.get('website') or 'No website'}"
        ctk.CTkLabel(info_col, text=contact_txt, font=Theme.FONT_CAPTION, text_color=Theme.DARK_TEXT).pack(anchor="w")

        pub_count = len(p.get("publications", []))
        area_count = len(p.get("areas", []))
        skill_count = len(p.get("skills", []))
        try:
            conns = api_client.get_researcher_connections(self.researcher_id)
            conn_count = len(conns) if isinstance(conns, list) else 0
        except Exception:
            conn_count = 0

        # Pending incoming requests — only relevant on own profile
        pending_count = 0
        if self._is_editable(p):
            current_rid = self._get_current_researcher_id()
            if current_rid:
                try:
                    pending_count = api_client.get_pending_incoming_count(current_rid)
                except Exception:
                    pending_count = 0

        metrics_row = ctk.CTkFrame(info_col, fg_color="transparent")
        metrics_row.pack(anchor="w", pady=(10, 0))

        stat_items = [
            ("Connections", conn_count, Theme.ACADEMIC_BLUE),
            ("Publications", pub_count, Theme.PURPLE),
            ("Research Areas", area_count, Theme.ACADEMIC_BLUE),
            ("Skills", skill_count, Theme.CYAN),
            ("Citations", p.get("citation_count", 0), Theme.NAVY),
            ("h-index", p.get("h_index", 0), Theme.SECONDARY_TEXT),
        ]
        if self._is_editable(p):
            stat_items.append(("Pending Requests", pending_count, "#D97706" if pending_count else Theme.SECONDARY_TEXT))

        for label, value, fg in stat_items:
            box = ctk.CTkFrame(metrics_row, fg_color="#F8FAFC", corner_radius=10, border_width=1, border_color="#E2E8F0")
            box.pack(side="left", padx=(0, 8), pady=2)
            ctk.CTkLabel(box, text=f"{label}: {value}", font=Theme.FONT_CAPTION, text_color=fg, height=28).pack(padx=8, pady=4)

        # Right Metrics Pill
        metrics_col = ctk.CTkFrame(h_inner, fg_color="transparent")
        metrics_col.pack(side="right", padx=(10, 0))

        if self._is_editable(p):
            edit_header_btn = create_primary_button(metrics_col, text="Edit Profile", command=self._open_edit_profile, width=140, height=34)
            edit_header_btn.pack(pady=(0, 8))
        else:
            # Connection action button — shown only when viewing another researcher
            self._conn_btn_frame = ctk.CTkFrame(metrics_col, fg_color="transparent")
            self._conn_btn_frame.pack(pady=(0, 8))
            self._render_connection_button()


        cit_box = ctk.CTkFrame(metrics_col, fg_color="#F3F0FF", corner_radius=10)
        cit_box.pack(pady=4)
        ctk.CTkLabel(
            cit_box,
            text=f"  ⭐ {p.get('citation_count', 0)} Total Citations  ",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.PURPLE,
            height=30
        ).pack(padx=8, pady=4)

        h_box = ctk.CTkFrame(metrics_col, fg_color="#EBF4FF", corner_radius=10)
        h_box.pack(pady=4)
        ctk.CTkLabel(
            h_box,
            text=f"  📊 h-index: {p.get('h_index', 0)}  ",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.ACADEMIC_BLUE,
            height=30
        ).pack(padx=8, pady=4)

        # Incoming Connection Requests (for logged-in user profile)
        if self._is_editable(p):
            self._build_incoming_requests_section()

        # 2. About & Research Areas Section (2 columns)
        two_col = ctk.CTkFrame(self, fg_color="transparent")
        two_col.pack(fill="x", padx=25, pady=(0, 15))
        two_col.columnconfigure(0, weight=2)
        two_col.columnconfigure(1, weight=1)

        # Left: About (Bio)
        about_card = create_card(two_col)
        about_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        about_inner = ctk.CTkFrame(about_card, fg_color="transparent")
        about_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(about_inner, text="About the Researcher", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 8))
        bio_text = p.get("bio")
        if bio_text:
            ctk.CTkLabel(
                about_inner,
                text=bio_text,
                font=Theme.FONT_BODY,
                text_color=Theme.DARK_TEXT,
                wraplength=480,
                justify="left"
            ).pack(anchor="w")
        else:
            ctk.CTkLabel(about_inner, text="No bio added yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
            if self._is_editable(p):
                create_secondary_button(about_inner, text="Add Bio", command=self._open_edit_profile, width=100, height=28).pack(anchor="w", pady=(8, 0))

        # Right: Research Areas
        areas_card = create_card(two_col)
        areas_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        areas_inner = ctk.CTkFrame(areas_card, fg_color="transparent")
        areas_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(areas_inner, text="Research Areas", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 10))
        areas = p.get("areas", [])
        if areas:
            for a in areas:
                badge = create_badge(
                    areas_inner,
                    text=f"🔬 {a.get('name', '')}",
                    bg_color="#EEF2FF",
                    text_color=Theme.ACADEMIC_BLUE,
                    font=Theme.FONT_BODY
                )
                badge.pack(anchor="w", pady=3)
        else:
            ctk.CTkLabel(areas_inner, text="No research areas added yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
            if self._is_editable(p):
                create_secondary_button(areas_inner, text="Add Research Areas", command=self._open_edit_areas, width=150, height=28).pack(anchor="w", pady=(8, 0))

        # Skills (distinct from Research Areas)
        ctk.CTkLabel(areas_inner, text="Skills", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(10, 6))
        skills = p.get("skills", [])
        self._skills_container = ctk.CTkFrame(areas_inner, fg_color="transparent")
        self._skills_container.pack(fill="both", expand=True)
        if skills:
            for s in skills:
                if isinstance(s, dict):
                    s_name = s.get("name", "")
                    s_prof = s.get("proficiency_level", "Intermediate")
                else:
                    s_name = str(s)
                    s_prof = "Intermediate"
                badge_txt = f"⚡ {s_name}  •  {s_prof}"
                sb = create_badge(self._skills_container, text=badge_txt, bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE, font=Theme.FONT_BODY)
                sb.pack(anchor="w", pady=3)
        else:
            ctk.CTkLabel(self._skills_container, text="No skills added yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
            if self._is_editable(p):
                create_secondary_button(self._skills_container, text="Add Skills", command=self._open_skills_editor, width=120, height=28).pack(anchor="w", pady=(8, 0))

        if self._is_editable(p):
            profile_actions = ctk.CTkFrame(areas_inner, fg_color="transparent")
            profile_actions.pack(anchor="e", pady=(6, 0))

            self._edit_profile_btn = create_secondary_button(profile_actions, text="Edit Profile", command=self._open_edit_profile, width=110, height=28)
            self._edit_profile_btn.pack(side="left", padx=(0, 6))

            self._edit_areas_btn = create_secondary_button(profile_actions, text="Edit Research Areas", command=self._open_edit_areas, width=160, height=28)
            self._edit_areas_btn.pack(side="left", padx=(0, 6))

            self._edit_btn = create_secondary_button(profile_actions, text="Edit Skills", command=self._toggle_edit_skills, width=110, height=28)
            self._edit_btn.pack(side="left", padx=(0, 6))

            self._add_paper_btn = create_primary_button(profile_actions, text="+ Add Paper", command=self._open_add_paper, width=120, height=30)
            self._add_paper_btn.pack(side="left")

        # 3. Publications Section
        pub_card = create_card(self)
        pub_card.pack(fill="x", padx=25, pady=(0, 15))

        pub_inner = ctk.CTkFrame(pub_card, fg_color="transparent")
        pub_inner.pack(fill="both", expand=True, padx=20, pady=16)

        pubs = p.get("publications", [])
        is_owner = self._is_editable(p)

        pub_hdr = ctk.CTkFrame(pub_inner, fg_color="transparent")
        pub_hdr.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            pub_hdr,
            text=f"My Publications ({len(pubs)})" if is_owner else f"Publications ({len(pubs)})",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(side="left")

        create_badge(
            pub_hdr,
            text=f"{len(pubs)} Published",
            bg_color="#EEF2FF" if pubs else "#E2E8F0",
            text_color=Theme.ACADEMIC_BLUE if pubs else Theme.SECONDARY_TEXT
        ).pack(side="left", padx=(10, 0))

        if is_owner:
            create_primary_button(pub_hdr, text="+ Add Paper", command=self._open_add_paper, width=120, height=30).pack(side="right")

        if not pubs:
            ctk.CTkLabel(pub_inner, text="No publications added yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
            if is_owner:
                create_secondary_button(pub_inner, text="Add Paper", command=self._open_add_paper, width=120, height=28).pack(anchor="w", pady=(10, 0))
        else:
            for paper in pubs:
                p_item = ctk.CTkFrame(pub_inner, fg_color=Theme.MUTED_BG, corner_radius=8)
                p_item.pack(fill="x", pady=5)

                p_row = ctk.CTkFrame(p_item, fg_color="transparent")
                p_row.pack(fill="x", padx=14, pady=10)

                left_info = ctk.CTkFrame(p_row, fg_color="transparent")
                left_info.pack(side="left", fill="both", expand=True)

                # Clickable Paper Title
                title_btn = ctk.CTkButton(
                    left_info,
                    text=f"📄  {paper['title']}",
                    font=Theme.FONT_BODY_BOLD,
                    text_color=Theme.NAVY,
                    fg_color="transparent",
                    hover_color="#E2E8F0",
                    anchor="w",
                    command=lambda pid=paper["id"]: self.on_select_paper(pid)
                )
                title_btn.pack(anchor="w", pady=(0, 3))

                # Clickable Co-Authors
                authors = paper.get("authors", [])
                if authors:
                    auth_frame = ctk.CTkFrame(left_info, fg_color="transparent")
                    auth_frame.pack(anchor="w", pady=(1, 3))
                    ctk.CTkLabel(auth_frame, text="Authors: ", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left")
                    for a_idx, author in enumerate(authors):
                        a_name = author.get("name", "Unknown")
                        a_id = author.get("id")
                        a_btn = ctk.CTkButton(
                            auth_frame,
                            text=a_name,
                            font=Theme.FONT_CAPTION,
                            text_color=Theme.ACADEMIC_BLUE,
                            fg_color="transparent",
                            hover_color="#DBEAFE",
                            height=20,
                            command=(lambda aid=a_id: self.on_select_researcher(aid)) if a_id else None
                        )
                        a_btn.pack(side="left", padx=1)
                        if a_idx < len(authors) - 1:
                            ctk.CTkLabel(auth_frame, text=",", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left", padx=(0, 2))

                # Publication Metadata: Year · Venue · Citations
                meta_parts = []
                if paper.get("publication_year"):
                    meta_parts.append(f"Year: {paper['publication_year']}")
                if paper.get("venue"):
                    meta_parts.append(f"Venue: {paper['venue']}")
                if paper.get("citation_count"):
                    meta_parts.append(f"⭐ {paper['citation_count']} Citations")
                if meta_parts:
                    meta_str = "  ·  ".join(meta_parts)
                    ctk.CTkLabel(left_info, text=meta_str, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT, anchor="w").pack(anchor="w", pady=(1, 2))

                # DOI / URL
                doi = paper.get("doi") or paper.get("pdf_url")
                if doi:
                    doi_frame = ctk.CTkFrame(left_info, fg_color="transparent")
                    doi_frame.pack(anchor="w", pady=(1, 3))
                    ctk.CTkLabel(doi_frame, text=f"🔗 DOI / Link: {doi}", font=Theme.FONT_CAPTION, text_color=Theme.ACADEMIC_BLUE).pack(side="left")

                # Research Areas per Paper
                areas = paper.get("areas", [])
                p_area_name = paper.get("primary_area_name")
                if areas or p_area_name:
                    area_row = ctk.CTkFrame(left_info, fg_color="transparent")
                    area_row.pack(anchor="w", pady=(4, 0))
                    if p_area_name:
                        create_badge(area_row, text=f"⭐ {p_area_name}", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(0, 6))
                    for a_item in areas:
                        if a_item != p_area_name:
                            create_badge(area_row, text=f"🔬 {a_item}", bg_color="#F1F5F9", text_color=Theme.DARK_TEXT).pack(side="left", padx=(0, 6))

                # Right Action Buttons
                right_action = ctk.CTkFrame(p_row, fg_color="transparent")
                right_action.pack(side="right", padx=(10, 0), anchor="center")

                create_secondary_button(
                    right_action,
                    text="Paper Details →",
                    command=lambda pid=paper["id"]: self.on_select_paper(pid),
                    width=110,
                    height=28
                ).pack(side="top", pady=2)

                if is_owner:
                    edit_del_row = ctk.CTkFrame(right_action, fg_color="transparent")
                    edit_del_row.pack(side="top", pady=(4, 0))

                    create_secondary_button(
                        edit_del_row,
                        text="✏️ Edit",
                        command=lambda p_obj=paper: self._open_edit_paper(p_obj),
                        width=60,
                        height=26
                    ).pack(side="left", padx=(0, 4))

                    ctk.CTkButton(
                        edit_del_row,
                        text="🗑️ Delete",
                        command=lambda pid=paper["id"], ptitle=paper["title"]: self._confirm_delete_paper(pid, ptitle),
                        width=70,
                        height=26,
                        fg_color="transparent",
                        hover_color="#FEE2E2",
                        text_color=Theme.DANGER,
                        font=Theme.FONT_CAPTION
                    ).pack(side="left")

        # 4. Accepted Connections (My Connections)
        self._build_connections_section()

        # 5. Activity Feed & Collaboration Suggestions (for logged-in user profile)
        if is_owner:
            self._build_connection_activity_section()
            self._build_collaboration_suggestions_section()

        # 5. Direct Academic Co-Authorship Graph
        collabs = p.get("connected_researchers", [])
        if collabs:
            net_card = create_card(self)
            net_card.pack(fill="x", padx=25, pady=(0, 30))

            net_inner = ctk.CTkFrame(net_card, fg_color="transparent")
            net_inner.pack(fill="both", expand=True, padx=20, pady=16)

            ctk.CTkLabel(
                net_inner,
                text="Direct Academic Co-Authorship Graph",
                font=Theme.FONT_SUBTITLE,
                text_color=Theme.NAVY
            ).pack(anchor="w", pady=(0, 4))

            ctk.CTkLabel(
                net_inner,
                text="Discovered direct academic co-authorship relationships from published papers:",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w", pady=(0, 12))

            collab_grid = ctk.CTkFrame(net_inner, fg_color="transparent")
            collab_grid.pack(fill="x")
            collab_grid.columnconfigure((0, 1), weight=1, uniform="collab_grid")

            for idx, c in enumerate(collabs):
                row = idx // 2
                col = idx % 2

                c_box = ctk.CTkFrame(collab_grid, fg_color=Theme.SOFT_BG, border_color=Theme.BORDER, border_width=1, corner_radius=8)
                c_box.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

                c_inner = ctk.CTkFrame(c_box, fg_color="transparent")
                c_inner.pack(fill="both", expand=True, padx=12, pady=10)

                top_collab = ctk.CTkFrame(c_inner, fg_color="transparent")
                top_collab.pack(fill="x")

                c_name = ctk.CTkLabel(top_collab, text=c["collaborator_name"], font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY)
                c_name.pack(side="left")

                badge = create_badge(
                    top_collab,
                    text=f"{c.get('paper_count', 1)} Joint Paper(s)",
                    bg_color="#EBF4FF",
                    text_color=Theme.ACADEMIC_BLUE
                )
                badge.pack(side="right")

                c_dept = ctk.CTkLabel(
                    c_inner,
                    text=f"{c.get('designation', '')} · {c.get('department_name', '')}",
                    font=Theme.FONT_CAPTION,
                    text_color=Theme.SECONDARY_TEXT
                )
                c_dept.pack(anchor="w", pady=(2, 6))

                prof_btn = create_secondary_button(
                    c_inner,
                    text="View Collaborator Profile →",
                    command=lambda cid=c["collaborator_id"]: self.on_select_researcher(cid),
                    width=150,
                    height=26
                )
                prof_btn.pack(anchor="w")

    def _refresh_profile(self):
        if not self.winfo_exists():
            return
        for w in self.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self._load_profile()
        self._build_ui()

    def _setup_dialog(self, win: ctk.CTkToplevel, title: str, width: int, height: int):
        """Configure popup dialog to open in front of CAMPUSX main window with correct lifecycle."""
        win.title(f"{title} — CAMPUSX")
        win.configure(fg_color=Theme.WHITE)
        try:
            parent_win = self.winfo_toplevel()
            win.transient(parent_win)
        except Exception:
            pass
        win.lift()
        win.focus_force()
        win.attributes("-topmost", True)
        win.after(250, lambda: win.attributes("-topmost", False) if win.winfo_exists() else None)

        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        # Ensure dialog dimensions never overflow screen bounds
        actual_h = min(height, max(420, sh - 120))
        actual_w = min(width, max(520, sw - 60))

        try:
            parent_win = self.winfo_toplevel()
            px = parent_win.winfo_rootx()
            py = parent_win.winfo_rooty()
            pw = parent_win.winfo_width()
            ph = parent_win.winfo_height()
            x = max(10, px + (pw - actual_w) // 2)
            y = max(10, py + (ph - actual_h) // 2)
        except Exception:
            x = max(10, (sw - actual_w) // 2)
            y = max(10, (sh - actual_h) // 2)

        win.geometry(f"{actual_w}x{actual_h}+{x}+{y}")
        win.minsize(min(actual_w, 520), min(actual_h, 420))

    def _open_edit_profile(self):
        if not self.profile:
            return
        win = ctk.CTkToplevel(self)
        self._setup_dialog(win, "Edit Profile", 640, 590)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(scroll, text="Edit Profile", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Update your personal details, academic affiliation, and bio:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 14))

        # Full Name
        ctk.CTkLabel(scroll, text="Full Name *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        name_entry = ctk.CTkEntry(scroll, width=560, height=34)
        name_entry.insert(0, self.profile.get("name", ""))
        name_entry.pack(anchor="w", pady=(0, 10))

        # Designation
        ctk.CTkLabel(scroll, text="Designation *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        designation_entry = ctk.CTkEntry(scroll, width=560, height=34)
        designation_entry.insert(0, self.profile.get("designation", ""))
        designation_entry.pack(anchor="w", pady=(0, 10))

        # Institution
        institution_options = []
        try:
            institution_options = api_client.get_institutions()
        except Exception:
            institution_options = []
        institution_names = [item["name"] for item in institution_options if item.get("name")]
        institution_map = {item["name"]: item["id"] for item in institution_options if item.get("name")}
        curr_inst = self.profile.get("institution_name") or (institution_names[0] if institution_names else "")
        selected_inst_var = ctk.StringVar(value=curr_inst if curr_inst in institution_map else (institution_names[0] if institution_names else ""))

        ctk.CTkLabel(scroll, text="Institution", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        institution_menu = ctk.CTkOptionMenu(
            scroll,
            variable=selected_inst_var,
            values=institution_names if institution_names else ["No institutions available"],
            width=560,
            height=34,
            fg_color=Theme.ACADEMIC_BLUE
        )
        institution_menu.pack(anchor="w", pady=(0, 10))

        # Department
        dept_map = {}
        curr_inst_id = institution_map.get(selected_inst_var.get())
        dept_opts = []
        try:
            dept_opts = api_client.get_departments(curr_inst_id) if curr_inst_id else []
        except Exception:
            dept_opts = []
        dept_names = [d["name"] for d in dept_opts if d.get("name")]
        for d in dept_opts:
            if d.get("name"):
                dept_map[d["name"]] = d["id"]
        curr_dept = self.profile.get("department_name") or (dept_names[0] if dept_names else "")
        selected_dept_var = ctk.StringVar(value=curr_dept if curr_dept in dept_map else (dept_names[0] if dept_names else ""))

        ctk.CTkLabel(scroll, text="Department / Program", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        department_menu = ctk.CTkOptionMenu(
            scroll,
            variable=selected_dept_var,
            values=dept_names if dept_names else ["No departments available"],
            width=560,
            height=34,
            fg_color=Theme.ACADEMIC_BLUE
        )
        department_menu.pack(anchor="w", pady=(0, 10))

        def _on_inst_changed(chosen_inst):
            inst_id = institution_map.get(chosen_inst)
            try:
                new_depts = api_client.get_departments(inst_id) if inst_id else []
            except Exception:
                new_depts = []
            dept_map.clear()
            new_names = [d["name"] for d in new_depts if d.get("name")]
            for d in new_depts:
                if d.get("name"):
                    dept_map[d["name"]] = d["id"]
            if new_names:
                department_menu.configure(values=new_names)
                selected_dept_var.set(new_names[0])
            else:
                department_menu.configure(values=["No departments available"])
                selected_dept_var.set("No departments available")

        institution_menu.configure(command=_on_inst_changed)

        # Email (READ ONLY)
        ctk.CTkLabel(scroll, text="Email (Read Only)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        email_entry = ctk.CTkEntry(scroll, width=560, height=34, fg_color="#F1F5F9", text_color=Theme.SECONDARY_TEXT)
        email_entry.insert(0, self.profile.get("email") or "Not registered")
        email_entry.configure(state="disabled")
        email_entry.pack(anchor="w", pady=(0, 10))

        # Website
        ctk.CTkLabel(scroll, text="Website URL", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        website_entry = ctk.CTkEntry(scroll, width=560, height=34)
        website_entry.insert(0, self.profile.get("website") or "")
        website_entry.pack(anchor="w", pady=(0, 10))

        # Bio
        ctk.CTkLabel(scroll, text="Biography", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        bio_box = ctk.CTkTextbox(scroll, width=560, height=100)
        bio_box.insert("1.0", self.profile.get("bio") or "")
        bio_box.pack(anchor="w", pady=(0, 12))

        # Status Label
        status_lbl = ctk.CTkLabel(scroll, text="", font=Theme.FONT_BODY, text_color=Theme.DANGER)
        status_lbl.pack(anchor="w", pady=(0, 10))

        # Buttons
        action_row = ctk.CTkFrame(scroll, fg_color="transparent")
        action_row.pack(fill="x", pady=(8, 12))

        def _save():
            if not win.winfo_exists():
                return
            name_val = name_entry.get().strip()
            if not name_val:
                status_lbl.configure(text="Full Name is required.", text_color=Theme.DANGER)
                return
            desig_val = designation_entry.get().strip()
            if not desig_val:
                status_lbl.configure(text="Designation is required.", text_color=Theme.DANGER)
                return

            inst_id = institution_map.get(selected_inst_var.get())
            dept_id = dept_map.get(selected_dept_var.get())
            bio_val = bio_box.get("1.0", "end").strip() or None
            web_val = website_entry.get().strip() or None

            payload = {
                "name": name_val,
                "designation": desig_val,
                "institution_id": inst_id,
                "department_id": dept_id,
                "bio": bio_val,
                "website": web_val
            }
            try:
                api_client.update_researcher_profile(self.researcher_id, payload)
                win.destroy()
                if self.winfo_exists():
                    self._refresh_profile()
            except Exception as exc:
                if win.winfo_exists():
                    status_lbl.configure(text=f"Save failed: {exc}", text_color=Theme.DANGER)

        ctk.CTkButton(
            action_row,
            text="Cancel",
            command=win.destroy,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.SECONDARY_TEXT,
            width=110,
            height=34
        ).pack(side="left")

        create_primary_button(
            action_row,
            text="Save Changes",
            command=_save,
            width=150,
            height=34
        ).pack(side="right")

    def _open_edit_areas(self):
        if not self.profile:
            return
        win = ctk.CTkToplevel(self)
        self._setup_dialog(win, "Edit Research Areas", 520, 520)

        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(container, text="Edit Research Areas", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(container, text="Select or unselect the academic fields for this profile:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 12))

        current_ids = {a.get("id") for a in self.profile.get("areas", []) if a.get("id") is not None}

        area_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", height=300)
        area_frame.pack(fill="both", expand=True, pady=(0, 10))

        try:
            area_rows = api_client.get_research_areas()
        except Exception as exc:
            area_rows = []
            ctk.CTkLabel(area_frame, text=f"Unable to load research areas: {exc}", font=Theme.FONT_BODY, text_color=Theme.DANGER).pack(anchor="w", pady=8)

        selected_vars = {}
        for area in area_rows:
            area_id = area.get("id")
            var = ctk.BooleanVar(value=(area_id in current_ids))
            selected_vars[area_id] = var
            cb = ctk.CTkCheckBox(
                area_frame,
                text=area.get("name", "Untitled Area"),
                variable=var,
                font=Theme.FONT_BODY,
                text_color=Theme.DARK_TEXT,
                checkbox_width=20,
                checkbox_height=20,
                fg_color=Theme.ACADEMIC_BLUE
            )
            cb.pack(anchor="w", pady=4)

        status_lbl = ctk.CTkLabel(container, text="", font=Theme.FONT_BODY, text_color=Theme.DANGER)
        status_lbl.pack(anchor="w", pady=(2, 6))

        action_row = ctk.CTkFrame(container, fg_color="transparent")
        action_row.pack(fill="x", pady=(6, 0))

        def _save_areas():
            if not win.winfo_exists():
                return
            chosen = [aid for aid, var in selected_vars.items() if var.get() and aid is not None]
            try:
                api_client.update_researcher_areas(self.researcher_id, chosen)
                win.destroy()
                if self.winfo_exists():
                    self._refresh_profile()
            except Exception as exc:
                if win.winfo_exists():
                    status_lbl.configure(text=f"Save failed: {exc}", text_color=Theme.DANGER)

        ctk.CTkButton(
            action_row,
            text="Cancel",
            command=win.destroy,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.SECONDARY_TEXT,
            width=110,
            height=34
        ).pack(side="left")

        create_primary_button(
            action_row,
            text="Save Areas",
            command=_save_areas,
            width=140,
            height=34
        ).pack(side="right")

    def _toggle_edit_skills(self):
        self._open_skills_editor()

    _open_edit_skills = _toggle_edit_skills

    def _open_skills_editor(self):
        if not self.profile:
            return

        win = ctk.CTkToplevel(self)
        self._setup_dialog(win, "Edit Skills", 640, 560)

        # ── Sticky Action Row at BOTTOM (Always visible on screen) ──
        action_row = ctk.CTkFrame(win, fg_color=Theme.SOFT_BG, height=58, corner_radius=0)
        action_row.pack(side="bottom", fill="x")

        # Thin separator line above action row
        ctk.CTkFrame(win, fg_color=Theme.BORDER, height=1).pack(side="bottom", fill="x")

        # Status label in bottom bar
        bottom_status_lbl = ctk.CTkLabel(
            action_row,
            text="",
            font=Theme.FONT_BODY_BOLD,
            text_color="#15803D"
        )
        bottom_status_lbl.pack(side="left", padx=20, pady=12)

        # ── Scrollable content area ──
        scroll_area = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll_area.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        ctk.CTkLabel(scroll_area, text="Edit Skills & Proficiency", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            scroll_area,
            text="Manage your academic & technical skills. Set proficiency levels and click Save Changes to persist.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 10))

        PROFICIENCY_LEVELS = ["Beginner", "Intermediate", "Advanced", "Expert"]
        PROF_COLORS = {
            "Beginner": ("#E0F2FE", "#0369A1"),
            "Intermediate": ("#EEF2FF", Theme.ACADEMIC_BLUE),
            "Advanced": ("#F0FDF4", "#15803D"),
            "Expert": ("#FEF3C7", "#92400E"),
        }

        # skill_name.lower() -> {"name": str, "proficiency_level": str}
        selected_lookup: dict = {}
        selected_order: list = []  # ordered list of lowercase keys

        # Pre-populate from profile
        for s in self.profile.get("skills", []):
            if isinstance(s, dict):
                name = str(s.get("name") or "").strip()
                prof = str(s.get("proficiency_level") or "Intermediate").strip()
            else:
                name = str(s).strip()
                prof = "Intermediate"
            if name:
                key = name.lower()
                if key not in selected_lookup:
                    selected_lookup[key] = {"name": name, "proficiency_level": prof}
                    selected_order.append(key)

        # Top section banner for selected skills
        sel_hdr_row = ctk.CTkFrame(scroll_area, fg_color="transparent")
        sel_hdr_row.pack(fill="x", pady=(4, 4))
        ctk.CTkLabel(sel_hdr_row, text="Selected Skills", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(side="left")
        skill_count_badge = create_badge(sel_hdr_row, text=f"{len(selected_order)} Skills", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE)
        skill_count_badge.pack(side="left", padx=8)

        # Top status feedback label
        top_status_lbl = ctk.CTkLabel(scroll_area, text="", font=Theme.FONT_BODY, text_color="#15803D")
        top_status_lbl.pack(anchor="w", pady=(0, 4))

        selected_chips_outer = ctk.CTkScrollableFrame(scroll_area, fg_color="#F8FAFC", corner_radius=8, height=150)
        selected_chips_outer.pack(fill="x", pady=(0, 8))

        def update_status(text: str, color: str):
            top_status_lbl.configure(text=text, text_color=color)
            bottom_status_lbl.configure(text=text, text_color=color)

        def refresh_selected_chips():
            if not win.winfo_exists() or not selected_chips_outer.winfo_exists():
                return
            for child in selected_chips_outer.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass

            skill_count_badge.configure(text=f"{len(selected_order)} Skills")

            if not selected_order:
                ctk.CTkLabel(
                    selected_chips_outer,
                    text="No skills selected yet. Search or add skills below.",
                    font=Theme.FONT_CAPTION,
                    text_color=Theme.SECONDARY_TEXT
                ).pack(anchor="w", padx=10, pady=12)
                return

            for key in list(selected_order):
                entry = selected_lookup.get(key)
                if not entry:
                    continue
                skill_name = entry["name"]
                prof = entry["proficiency_level"]
                bg_col, txt_col = PROF_COLORS.get(prof, PROF_COLORS["Intermediate"])

                chip_row = ctk.CTkFrame(selected_chips_outer, fg_color=bg_col, corner_radius=10)
                chip_row.pack(fill="x", padx=6, pady=3)

                inner = ctk.CTkFrame(chip_row, fg_color="transparent")
                inner.pack(fill="x", padx=8, pady=4)

                # Skill name
                ctk.CTkLabel(
                    inner,
                    text=f"  ⚡ {skill_name}",
                    font=Theme.FONT_BODY_BOLD,
                    text_color=txt_col
                ).pack(side="left")

                # Proficiency dropdown
                prof_var = ctk.StringVar(value=prof)

                def _on_prof_change(new_prof, k=key):
                    if k in selected_lookup:
                        selected_lookup[k]["proficiency_level"] = new_prof
                        update_status(f'Updated "{selected_lookup[k]["name"]}" to {new_prof}. Click "Save Changes" to apply.', "#0369A1")
                    refresh_selected_chips()

                prof_menu = ctk.CTkOptionMenu(
                    inner,
                    variable=prof_var,
                    values=PROFICIENCY_LEVELS,
                    width=120,
                    height=26,
                    fg_color=txt_col,
                    button_color=txt_col,
                    text_color=Theme.WHITE,
                    font=Theme.FONT_CAPTION,
                    command=lambda v, k=key: _on_prof_change(v, k)
                )
                prof_menu.pack(side="left", padx=(12, 4))

                # Remove button
                ctk.CTkButton(
                    inner,
                    text="✕",
                    width=26,
                    height=26,
                    fg_color="transparent",
                    hover_color="#DBEAFE",
                    text_color=Theme.DANGER,
                    font=("Segoe UI", 11, "bold"),
                    command=lambda k=key: _remove_skill(k)
                ).pack(side="right", padx=(4, 2))

        def _remove_skill(key: str):
            if key in selected_lookup:
                removed_name = selected_lookup[key]["name"]
                del selected_lookup[key]
                selected_order[:] = [k for k in selected_order if k != key]
                update_status(f'Removed "{removed_name}". Click "Save Changes" to apply.', "#D97706")
                refresh_selected_chips()
                refresh_suggestions()

        def _add_skill(name: str):
            clean = (name or "").strip()
            if not clean:
                return
            key = clean.lower()
            if key in selected_lookup:
                update_status(f'Skill "{clean}" is already in your skills list.', "#D97706")
                return
            selected_lookup[key] = {"name": clean, "proficiency_level": "Intermediate"}
            selected_order.append(key)
            update_status(f'Added "{clean}" (Intermediate). Click "Save Changes" to save.', "#15803D")
            refresh_selected_chips()
            refresh_suggestions()

        # ── Search & Add Skills Section ──
        ctk.CTkLabel(scroll_area, text="Search & Add Skills", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(8, 2))
        search_entry = ctk.CTkEntry(scroll_area, width=580, height=36, placeholder_text="Type skill name (e.g. Python, Deep Learning, MySQL)...")
        search_entry.pack(fill="x", pady=(0, 6))

        suggestion_frame = ctk.CTkScrollableFrame(scroll_area, fg_color="transparent", height=140)
        suggestion_frame.pack(fill="both", expand=True, pady=(0, 8))

        def refresh_suggestions():
            if not win.winfo_exists() or not suggestion_frame.winfo_exists():
                return
            for child in suggestion_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass

            query = search_entry.get().strip()
            try:
                matches = api_client.get_skills(query=query if query else None, limit=50)
            except Exception:
                matches = []

            normalized = [str(item.get("name") or "").strip() for item in matches if str(item.get("name") or "").strip()]
            match_lower_set = {m.lower() for m in normalized}

            if not normalized and not query:
                ctk.CTkLabel(suggestion_frame, text="Type above to search or discover available skills.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=8)
                return

            if not normalized and query:
                ctk.CTkLabel(suggestion_frame, text=f'No existing skill found for "{query}".', font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(4, 2))
                create_primary_button(
                    suggestion_frame,
                    text=f'+ Add "{query}" as New Skill',
                    command=lambda q=query: (_add_skill(q), search_entry.delete(0, "end"), refresh_suggestions()),
                    width=230, height=30
                ).pack(anchor="w", pady=(0, 8))
                return

            for skill_name in normalized:
                is_selected = skill_name.lower() in selected_lookup
                row = ctk.CTkFrame(suggestion_frame, fg_color="#EEF2FF" if is_selected else "#F8FAFC", corner_radius=6)
                row.pack(fill="x", pady=2)

                ctk.CTkLabel(
                    row,
                    text=f"  {skill_name}",
                    font=Theme.FONT_BODY_BOLD if is_selected else Theme.FONT_BODY,
                    text_color=Theme.ACADEMIC_BLUE if is_selected else Theme.DARK_TEXT
                ).pack(side="left", padx=8, pady=5)

                if is_selected:
                    ctk.CTkButton(
                        row, text="✓ Added (Remove)", width=120, height=26,
                        fg_color="#DBEAFE", hover_color="#BFDBFE",
                        text_color=Theme.ACADEMIC_BLUE, font=Theme.FONT_CAPTION,
                        command=lambda n=skill_name: _remove_skill(n.lower())
                    ).pack(side="right", padx=8, pady=4)
                else:
                    ctk.CTkButton(
                        row, text="+ Add", width=70, height=26,
                        fg_color=Theme.ACADEMIC_BLUE, hover_color="#173D6E",
                        text_color=Theme.WHITE, font=Theme.FONT_CAPTION,
                        command=lambda n=skill_name: _add_skill(n)
                    ).pack(side="right", padx=8, pady=4)

            # Custom skill option
            if query and query.lower() not in match_lower_set and query.lower() not in selected_lookup:
                custom_row = ctk.CTkFrame(suggestion_frame, fg_color="transparent")
                custom_row.pack(fill="x", pady=(6, 2))
                create_primary_button(
                    custom_row,
                    text=f'+ Add "{query}" as New Skill',
                    command=lambda q=query: (_add_skill(q), search_entry.delete(0, "end"), refresh_suggestions()),
                    width=230, height=30
                ).pack(anchor="w")

        search_entry.bind("<KeyRelease>", lambda _e: refresh_suggestions() if win.winfo_exists() else None)
        refresh_selected_chips()
        refresh_suggestions()

        # ── Save Changes Handler ──
        def _save_skills():
            if not win.winfo_exists():
                return
            skill_dicts = [v for v in selected_lookup.values()]
            try:
                update_status("Saving skills to database...", Theme.ACADEMIC_BLUE)
                win.update_idletasks()
                api_client.update_researcher_skills(self.researcher_id, skill_dicts)
                update_status("✓ Skills & proficiency levels saved successfully!", "#15803D")
                win.update_idletasks()
                if self.winfo_exists():
                    self._refresh_profile()
                win.after(600, lambda: win.destroy() if win.winfo_exists() else None)
            except Exception as exc:
                if win.winfo_exists():
                    update_status(f"Save failed: {exc}", Theme.DANGER)

        # ── Buttons in Sticky Action Row ──
        ctk.CTkButton(
            action_row,
            text="Cancel",
            command=win.destroy,
            fg_color="transparent",
            hover_color="#E2E8F0",
            text_color=Theme.SECONDARY_TEXT,
            font=Theme.FONT_BODY,
            width=100,
            height=36
        ).pack(side="right", padx=(0, 16), pady=10)

        save_btn = create_primary_button(
            action_row,
            text="💾 Save Changes",
            command=_save_skills,
            width=160,
            height=36
        )
        save_btn.pack(side="right", padx=(0, 10), pady=10)


    def _open_add_paper(self):
        win = ctk.CTkToplevel(self)
        self._setup_dialog(win, "Add Research Paper", 660, 680)

        # ── Sticky Action Row at BOTTOM (Always visible) ──
        action_row = ctk.CTkFrame(win, fg_color=Theme.SOFT_BG, height=58, corner_radius=0)
        action_row.pack(side="bottom", fill="x")

        ctk.CTkFrame(win, fg_color=Theme.BORDER, height=1).pack(side="bottom", fill="x")

        # Bottom status label
        bottom_status_lbl = ctk.CTkLabel(action_row, text="", font=Theme.FONT_BODY_BOLD, text_color=Theme.DANGER)
        bottom_status_lbl.pack(side="left", padx=20, pady=12)

        # ── Scrollable Body ──
        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        ctk.CTkLabel(scroll, text="Add Research Paper", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Record an academic paper, conference publication, or journal article:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 14))

        # Title
        ctk.CTkLabel(scroll, text="Title *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        title_entry = ctk.CTkEntry(scroll, width=580, height=34, placeholder_text="e.g. Scalable Graph Neural Networks for Academic Collaboration")
        title_entry.pack(fill="x", pady=(0, 10))

        # Publication Year
        ctk.CTkLabel(scroll, text="Publication Year *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        year_entry = ctk.CTkEntry(scroll, width=200, height=34, placeholder_text="e.g. 2024")
        year_entry.pack(anchor="w", pady=(0, 10))

        # Venue / Journal / Conference
        ctk.CTkLabel(scroll, text="Venue / Journal / Conference", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        venue_entry = ctk.CTkEntry(scroll, width=580, height=34, placeholder_text="e.g. IEEE Transactions on Knowledge and Data Engineering")
        venue_entry.pack(fill="x", pady=(0, 10))

        # DOI / URL
        ctk.CTkLabel(scroll, text="DOI / URL (optional)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        doi_entry = ctk.CTkEntry(scroll, width=580, height=34, placeholder_text="e.g. 10.1109/TKDE.2024.10452 or https://...")
        doi_entry.pack(fill="x", pady=(0, 10))

        # ── 1. PRIMARY RESEARCH AREA ──
        area_raw = []
        try:
            area_raw = api_client.get_research_areas()
        except Exception:
            pass
        area_map: dict = {a["name"]: a["id"] for a in area_raw if a.get("name") and a.get("id")}
        initial_areas_list = list(area_map.keys()) if area_map else ["General Academic Research"]

        ctk.CTkLabel(scroll, text="Primary Research Area *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(scroll, text="Select the primary discipline for this publication (required):", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))

        primary_area_row = ctk.CTkFrame(scroll, fg_color="transparent")
        primary_area_row.pack(fill="x", pady=(0, 4))

        primary_area_var = ctk.StringVar(value=initial_areas_list[0])

        primary_area_menu = ctk.CTkOptionMenu(
            primary_area_row,
            variable=primary_area_var,
            values=initial_areas_list,
            width=380,
            height=34,
            fg_color=Theme.ACADEMIC_BLUE,
            button_color="#173D6E"
        )
        primary_area_menu.pack(side="left", padx=(0, 10))

        # Primary badge row to clearly distinguish primary area
        primary_badge_row = ctk.CTkFrame(scroll, fg_color="transparent")
        primary_badge_row.pack(fill="x", pady=(0, 10))

        primary_badge_lbl = create_badge(
            primary_badge_row,
            text=f"⭐ Primary Field: {primary_area_var.get()}",
            bg_color="#EEF2FF",
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD
        )
        primary_badge_lbl.pack(side="left")

        def _on_primary_change(new_val):
            primary_badge_lbl.configure(text=f"⭐ Primary Field: {new_val}")
            # If newly selected primary was in additional areas, remove it from additional
            if new_val in selected_additional_areas:
                selected_additional_areas.pop(new_val, None)
                refresh_additional_chips()

        primary_area_menu.configure(command=_on_primary_change)

        # ── "+ New Research Area" Modal ──
        def _open_add_new_area_modal():
            if not win.winfo_exists():
                return
            modal = ctk.CTkToplevel(win)
            modal.title("Add New Research Area — CAMPUSX")
            modal.geometry("440x220")
            modal.resizable(False, False)
            modal.grab_set()

            ctk.CTkLabel(modal, text="Create New Research Area", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", padx=20, pady=(16, 2))
            ctk.CTkLabel(modal, text="Enter a new academic domain or research field:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=20, pady=(0, 8))

            new_area_entry = ctk.CTkEntry(modal, width=390, height=36, placeholder_text="e.g. Natural Language Processing, Robotics")
            new_area_entry.pack(padx=20, pady=(0, 6))

            modal_status = ctk.CTkLabel(modal, text="", font=Theme.FONT_CAPTION, text_color=Theme.DANGER)
            modal_status.pack(anchor="w", padx=20, pady=(0, 8))

            modal_btns = ctk.CTkFrame(modal, fg_color="transparent")
            modal_btns.pack(fill="x", padx=20, pady=(0, 16))

            def _create_area():
                name = new_area_entry.get().strip()
                if not name:
                    modal_status.configure(text="Research area name cannot be empty.", text_color=Theme.DANGER)
                    return
                # Case-insensitive duplicate check
                match_existing = next((k for k in area_map if k.lower() == name.lower()), None)
                if match_existing:
                    modal_status.configure(text=f'"{match_existing}" already exists. Selecting it now...', text_color="#D97706")
                    modal.update_idletasks()
                    primary_area_var.set(match_existing)
                    _on_primary_change(match_existing)
                    modal.after(600, modal.destroy)
                    return

                try:
                    result = api_client.create_research_area(name)
                    new_id = result.get("id") or result.get("area_id")
                    new_name = result.get("name", name)
                    if new_id:
                        area_map[new_name] = new_id
                        all_names = list(area_map.keys())
                        # Refresh dropdowns
                        primary_area_menu.configure(values=all_names)
                        additional_area_menu.configure(values=all_names)
                        # Set as primary automatically
                        primary_area_var.set(new_name)
                        _on_primary_change(new_name)
                    modal.destroy()
                except Exception as exc:
                    modal_status.configure(text=f"Error creating area: {exc}", text_color=Theme.DANGER)

            ctk.CTkButton(modal_btns, text="Cancel", command=modal.destroy, fg_color="transparent", hover_color="#E2E8F0", text_color=Theme.SECONDARY_TEXT, width=100, height=34).pack(side="left")
            create_primary_button(modal_btns, text="Create & Select", command=_create_area, width=150, height=34).pack(side="right")

        # "+ New Research Area" button right beside Primary dropdown
        new_area_btn = ctk.CTkButton(
            primary_area_row,
            text="+ New Research Area",
            width=160,
            height=34,
            fg_color=Theme.NAVY,
            hover_color="#0D2340",
            text_color=Theme.WHITE,
            font=Theme.FONT_BODY_BOLD,
            command=_open_add_new_area_modal
        )
        new_area_btn.pack(side="left")

        # ── 2. ADDITIONAL RESEARCH AREAS (Multi-Select with Chips) ──
        selected_additional_areas: dict = {}  # name -> id

        ctk.CTkLabel(scroll, text="Additional Research Areas (Optional)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(scroll, text="Associate one or more secondary research areas with this paper:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))

        additional_chips_frame = ctk.CTkScrollableFrame(scroll, fg_color="#F8FAFC", corner_radius=8, height=65)
        additional_chips_frame.pack(fill="x", pady=(0, 6))

        area_feedback_lbl = ctk.CTkLabel(scroll, text="", font=Theme.FONT_CAPTION, text_color="#D97706")
        area_feedback_lbl.pack(anchor="w", pady=(0, 2))

        def refresh_additional_chips():
            if not win.winfo_exists() or not additional_chips_frame.winfo_exists():
                return
            for child in additional_chips_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass

            if not selected_additional_areas:
                ctk.CTkLabel(
                    additional_chips_frame,
                    text="No additional research areas selected. Use the selector below to add more.",
                    font=Theme.FONT_CAPTION,
                    text_color=Theme.SECONDARY_TEXT
                ).pack(anchor="w", padx=8, pady=8)
                return

            flow = ctk.CTkFrame(additional_chips_frame, fg_color="transparent")
            flow.pack(fill="x", padx=4, pady=4)
            for name in list(selected_additional_areas.keys()):
                chip = ctk.CTkFrame(flow, fg_color="#EEF2FF", corner_radius=14)
                chip.pack(side="left", padx=4, pady=3)
                ctk.CTkLabel(chip, text=f"  🔬 {name}  ", font=Theme.FONT_BODY, text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(8, 2), pady=3)
                ctk.CTkButton(
                    chip, text="✕", width=22, height=22,
                    fg_color="transparent", hover_color="#DBEAFE",
                    text_color=Theme.DANGER, font=("Segoe UI", 10, "bold"),
                    command=lambda n=name: (_rm_additional_area(n))
                ).pack(side="left", padx=(0, 6))

        def _rm_additional_area(name: str):
            selected_additional_areas.pop(name, None)
            area_feedback_lbl.configure(text=f'Removed "{name}".', text_color=Theme.SECONDARY_TEXT)
            refresh_additional_chips()

        # Row to add additional area
        add_area_row = ctk.CTkFrame(scroll, fg_color="transparent")
        add_area_row.pack(fill="x", pady=(0, 10))

        additional_area_var = ctk.StringVar(value=initial_areas_list[0])
        additional_area_menu = ctk.CTkOptionMenu(
            add_area_row,
            variable=additional_area_var,
            values=initial_areas_list,
            width=380,
            height=32,
            fg_color="#334155",
            button_color="#1E293B"
        )
        additional_area_menu.pack(side="left", padx=(0, 8))

        def _add_additional_area():
            chosen = additional_area_var.get().strip()
            if not chosen or chosen not in area_map:
                return
            if chosen == primary_area_var.get():
                area_feedback_lbl.configure(text=f'"{chosen}" is already selected as the Primary Research Area.', text_color="#D97706")
                return
            if chosen in selected_additional_areas:
                area_feedback_lbl.configure(text=f'"{chosen}" is already in additional research areas.', text_color="#D97706")
                return
            selected_additional_areas[chosen] = area_map[chosen]
            area_feedback_lbl.configure(text=f'Added "{chosen}" as additional research area.', text_color="#15803D")
            refresh_additional_chips()

        ctk.CTkButton(
            add_area_row,
            text="+ Add Area",
            width=100,
            height=32,
            fg_color=Theme.ACADEMIC_BLUE,
            hover_color="#173D6E",
            text_color=Theme.WHITE,
            font=Theme.FONT_BODY,
            command=_add_additional_area
        ).pack(side="left")

        refresh_additional_chips()

        # ── 3. COLLABORATORS / CO-AUTHORS ──
        ctk.CTkLabel(scroll, text="Collaborators / Co-Authors", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(8, 2))
        ctk.CTkLabel(scroll, text="You are recorded as lead author. Search registered researchers below to add co-authors:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))

        # Lead Author Card (non-removable)
        creator_name = (self.profile or {}).get("name", "You")
        creator_row = ctk.CTkFrame(scroll, fg_color="#F0FDF4", corner_radius=8)
        creator_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            creator_row,
            text=f"  ⭐  {creator_name}  (Lead Author — You)",
            font=Theme.FONT_BODY_BOLD,
            text_color="#15803D"
        ).pack(side="left", padx=12, pady=7)

        # Selected co-authors: id -> name
        selected_coauthors: dict = {}

        coauthor_chips_frame = ctk.CTkScrollableFrame(scroll, fg_color="#F8FAFC", corner_radius=8, height=65)
        coauthor_chips_frame.pack(fill="x", pady=(0, 6))

        def refresh_coauthor_chips():
            if not win.winfo_exists() or not coauthor_chips_frame.winfo_exists():
                return
            for child in coauthor_chips_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
            if not selected_coauthors:
                ctk.CTkLabel(coauthor_chips_frame, text="No co-authors added yet. Search below to add registered researchers.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=8, pady=8)
                return
            flow = ctk.CTkFrame(coauthor_chips_frame, fg_color="transparent")
            flow.pack(fill="x", padx=4, pady=4)
            for rid, rname in list(selected_coauthors.items()):
                chip = ctk.CTkFrame(flow, fg_color="#EEF2FF", corner_radius=14)
                chip.pack(side="left", padx=4, pady=3)
                ctk.CTkLabel(chip, text=f"  👤 {rname} (Co-Author)  ", font=Theme.FONT_BODY, text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(8, 2), pady=3)
                ctk.CTkButton(
                    chip, text="✕", width=22, height=22,
                    fg_color="transparent", hover_color="#DBEAFE",
                    text_color=Theme.DANGER, font=("Segoe UI", 10, "bold"),
                    command=lambda r=rid: (selected_coauthors.pop(r, None), refresh_coauthor_chips(), refresh_collab_results())
                ).pack(side="left", padx=(0, 6))

        collab_search_entry = ctk.CTkEntry(
            scroll,
            width=580,
            height=34,
            placeholder_text="Search researchers by full name, partial name, or email (e.g. Vedika, Salunkhe)..."
        )
        collab_search_entry.pack(fill="x", pady=(0, 4))

        collab_results_frame = ctk.CTkScrollableFrame(scroll, fg_color="transparent", height=120)
        collab_results_frame.pack(fill="x", pady=(0, 10))

        def refresh_collab_results():
            if not win.winfo_exists() or not collab_results_frame.winfo_exists():
                return
            for child in collab_results_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
            q = collab_search_entry.get().strip()
            if not q:
                ctk.CTkLabel(collab_results_frame, text="Type a researcher name or email to search existing researchers.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=6)
                return
            try:
                results = api_client.search_researchers(q)
            except Exception:
                try:
                    results = api_client.get_researchers(search=q)
                except Exception:
                    results = []

            # Exclude lead author and already selected co-authors
            results = [r for r in results if r.get("id") != self.researcher_id and r.get("id") not in selected_coauthors]

            if not results:
                ctk.CTkLabel(collab_results_frame, text=f'No matching researchers found for "{q}".', font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=6)
                return

            for r in results[:10]:
                rname = r.get("name") or r.get("full_name") or "Unknown"
                rid = r.get("id")
                remail = r.get("email") or ""
                rdept = r.get("department_name") or r.get("designation") or ""
                sub_txt = f"{remail}   •   {rdept}" if remail and rdept else (remail or rdept)

                row = ctk.CTkFrame(collab_results_frame, fg_color="#F8FAFC", corner_radius=6)
                row.pack(fill="x", pady=2)

                info_col = ctk.CTkFrame(row, fg_color="transparent")
                info_col.pack(side="left", padx=8, pady=4, fill="x", expand=True)

                ctk.CTkLabel(info_col, text=f"👤 {rname}", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w")
                if sub_txt:
                    ctk.CTkLabel(info_col, text=sub_txt, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

                ctk.CTkButton(
                    row,
                    text="+ Add as Co-Author",
                    width=130,
                    height=28,
                    fg_color=Theme.ACADEMIC_BLUE,
                    hover_color="#173D6E",
                    text_color=Theme.WHITE,
                    font=Theme.FONT_CAPTION,
                    command=lambda i=rid, n=rname: (selected_coauthors.update({i: n}), refresh_coauthor_chips(), refresh_collab_results())
                ).pack(side="right", padx=8, pady=6)

        collab_search_entry.bind("<KeyRelease>", lambda _e: refresh_collab_results() if win.winfo_exists() else None)
        refresh_coauthor_chips()
        refresh_collab_results()

        # ── 4. ABSTRACT (Preserved completely) ──
        ctk.CTkLabel(scroll, text="Abstract", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(4, 2))
        abstract_box = ctk.CTkTextbox(scroll, width=580, height=100)
        abstract_box.pack(fill="x", pady=(0, 10))

        # Top error/status label
        top_error_lbl = ctk.CTkLabel(scroll, text="", font=Theme.FONT_BODY, text_color=Theme.DANGER)
        top_error_lbl.pack(anchor="w", pady=(0, 6))

        def show_error(msg: str):
            top_error_lbl.configure(text=msg, text_color=Theme.DANGER)
            bottom_status_lbl.configure(text=msg, text_color=Theme.DANGER)

        # ── 5. SAVE PAPER HANDLER ──
        def _save_paper():
            if not win.winfo_exists():
                return
            t = title_entry.get().strip()
            if not t:
                show_error("Paper title is required.")
                return
            y_str = year_entry.get().strip()
            if not y_str or not y_str.isdigit() or len(y_str) != 4:
                show_error("Please enter a valid 4-digit publication year (e.g. 2024).")
                return
            year_int = int(y_str)
            if year_int < 1900 or year_int > 2100:
                show_error("Year must be between 1900 and 2100.")
                return

            chosen_primary = primary_area_var.get().strip()
            if not chosen_primary or chosen_primary not in area_map:
                show_error("Please select a valid Primary Research Area.")
                return

            primary_id = area_map[chosen_primary]

            # Combine primary area with all additional areas (deduplicated)
            all_area_ids = [primary_id]
            for aid in selected_additional_areas.values():
                if aid and aid not in all_area_ids:
                    all_area_ids.append(aid)

            # Authors: creator first (author_order=1), followed by co-authors
            coauthor_ids = list(selected_coauthors.keys())
            all_author_ids = [self.researcher_id] + [cid for cid in coauthor_ids if cid != self.researcher_id]

            v_val = venue_entry.get().strip() or None
            d_val = doi_entry.get().strip() or None
            abs_val = abstract_box.get("1.0", "end").strip() or None

            payload = {
                "title": t,
                "publication_year": year_int,
                "venue": v_val,
                "doi": d_val,
                "url": d_val if d_val and (d_val.startswith("http://") or d_val.startswith("https://")) else None,
                "abstract": abs_val,
                "primary_area_id": primary_id,
                "research_area_ids": all_area_ids,
                "author_ids": all_author_ids
            }

            try:
                bottom_status_lbl.configure(text="Saving paper to database...", text_color=Theme.ACADEMIC_BLUE)
                win.update_idletasks()
                api_client.create_paper(payload)
                bottom_status_lbl.configure(text="✓ Paper published successfully!", text_color="#15803D")
                win.update_idletasks()
                if self.winfo_exists():
                    self._refresh_profile()
                win.after(600, lambda: win.destroy() if win.winfo_exists() else None)
            except Exception as exc:
                if win.winfo_exists():
                    show_error(f"Failed to add paper: {exc}")

        # ── Buttons in Sticky Bottom Action Bar ──
        ctk.CTkButton(
            action_row,
            text="Cancel",
            command=win.destroy,
            fg_color="transparent",
            hover_color="#E2E8F0",
            text_color=Theme.SECONDARY_TEXT,
            font=Theme.FONT_BODY,
            width=100,
            height=36
        ).pack(side="right", padx=(0, 16), pady=10)

        create_primary_button(
            action_row,
            text="Publish Paper",
            command=_save_paper,
            width=150,
            height=36
        ).pack(side="right", padx=(0, 10), pady=10)




    def _confirm_delete_paper(self, paper_id: int, paper_title: str):
        """Confirm and permanently delete a publication."""
        current_rid = self._get_current_researcher_id()
        if not current_rid:
            return

        modal = ctk.CTkToplevel(self)
        self._setup_dialog(modal, "Delete Publication", 440, 220)

        inner = ctk.CTkFrame(modal, fg_color=Theme.WHITE)
        inner.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            inner,
            text="Delete Publication?",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 6))

        truncated_title = paper_title if len(paper_title) <= 65 else paper_title[:62] + "..."
        ctk.CTkLabel(
            inner,
            text=f'Are you sure you want to permanently delete "{truncated_title}"?\n\nThis will remove the publication, author linkages, and area mappings from the database. This action cannot be undone.',
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=390,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        status_lbl = ctk.CTkLabel(inner, text="", font=Theme.FONT_CAPTION, text_color=Theme.DANGER)
        status_lbl.pack(anchor="w", pady=(0, 6))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            command=modal.destroy,
            fg_color="transparent",
            hover_color="#E2E8F0",
            text_color=Theme.SECONDARY_TEXT,
            font=Theme.FONT_BODY,
            width=90,
            height=32
        ).pack(side="right", padx=(8, 0))

        def _do_delete():
            try:
                status_lbl.configure(text="Deleting publication...", text_color=Theme.ACADEMIC_BLUE)
                modal.update_idletasks()
                api_client.delete_paper(paper_id, current_rid)
                modal.destroy()
                self._refresh_profile()
            except Exception as exc:
                status_lbl.configure(text=f"Failed to delete: {exc}", text_color=Theme.DANGER)

        del_btn = ctk.CTkButton(
            btn_row,
            text="Delete Paper",
            fg_color=Theme.DANGER,
            hover_color="#B91C1C",
            text_color=Theme.WHITE,
            font=Theme.FONT_BODY_BOLD,
            width=110,
            height=32,
            command=_do_delete
        )
        del_btn.pack(side="right")

    def _open_edit_paper(self, paper: Dict[str, Any]):
        """Open the Edit Research Paper dialog with pre-filled paper metadata."""
        win = ctk.CTkToplevel(self)
        self._setup_dialog(win, "Edit Research Paper", 660, 680)

        # Bottom action bar
        action_row = ctk.CTkFrame(win, fg_color=Theme.SOFT_BG, height=58, corner_radius=0)
        action_row.pack(side="bottom", fill="x")

        ctk.CTkFrame(win, fg_color=Theme.BORDER, height=1).pack(side="bottom", fill="x")

        bottom_status_lbl = ctk.CTkLabel(action_row, text="", font=Theme.FONT_BODY_BOLD, text_color=Theme.DANGER)
        bottom_status_lbl.pack(side="left", padx=20, pady=12)

        # Scrollable body
        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        ctk.CTkLabel(scroll, text="Edit Research Paper", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Update publication metadata, research areas, and co-authors:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 14))

        # Title
        ctk.CTkLabel(scroll, text="Title *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        title_entry = ctk.CTkEntry(scroll, width=580, height=34)
        title_entry.pack(fill="x", pady=(0, 10))
        title_entry.insert(0, paper.get("title", ""))

        # Publication Year
        ctk.CTkLabel(scroll, text="Publication Year *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        year_entry = ctk.CTkEntry(scroll, width=200, height=34)
        year_entry.pack(anchor="w", pady=(0, 10))
        year_entry.insert(0, str(paper.get("publication_year", "") or ""))

        # Venue / Journal / Conference
        ctk.CTkLabel(scroll, text="Venue / Journal / Conference", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        venue_entry = ctk.CTkEntry(scroll, width=580, height=34)
        venue_entry.pack(fill="x", pady=(0, 10))
        venue_entry.insert(0, paper.get("venue", "") or "")

        # DOI / URL
        ctk.CTkLabel(scroll, text="DOI / URL (optional)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        doi_entry = ctk.CTkEntry(scroll, width=580, height=34)
        doi_entry.pack(fill="x", pady=(0, 10))
        doi_entry.insert(0, paper.get("doi", "") or paper.get("pdf_url", "") or "")

        # Research Areas
        area_raw = []
        try:
            area_raw = api_client.get_research_areas()
        except Exception:
            pass
        area_map: dict = {a["name"]: a["id"] for a in area_raw if a.get("name") and a.get("id")}
        initial_areas_list = list(area_map.keys()) if area_map else ["General Academic Research"]

        p_primary = paper.get("primary_area_name")
        default_primary = p_primary if p_primary and p_primary in area_map else initial_areas_list[0]

        ctk.CTkLabel(scroll, text="Primary Research Area *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(4, 2))
        primary_area_row = ctk.CTkFrame(scroll, fg_color="transparent")
        primary_area_row.pack(fill="x", pady=(0, 4))

        primary_area_var = ctk.StringVar(value=default_primary)
        primary_area_menu = ctk.CTkOptionMenu(
            primary_area_row,
            variable=primary_area_var,
            values=initial_areas_list,
            width=380,
            height=34,
            fg_color=Theme.ACADEMIC_BLUE,
            button_color="#173D6E"
        )
        primary_area_menu.pack(side="left", padx=(0, 10))

        primary_badge_row = ctk.CTkFrame(scroll, fg_color="transparent")
        primary_badge_row.pack(fill="x", pady=(0, 10))
        primary_badge_lbl = create_badge(
            primary_badge_row,
            text=f"⭐ Primary Field: {primary_area_var.get()}",
            bg_color="#EEF2FF",
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD
        )
        primary_badge_lbl.pack(side="left")

        # Additional Research Areas
        selected_additional_areas = {}
        for a_name in paper.get("areas", []):
            if a_name != default_primary and a_name in area_map:
                selected_additional_areas[a_name] = area_map[a_name]

        ctk.CTkLabel(scroll, text="Additional Research Areas (Interdisciplinary)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(4, 2))
        additional_chips_frame = ctk.CTkScrollableFrame(scroll, fg_color="#F8FAFC", corner_radius=8, height=60)
        additional_chips_frame.pack(fill="x", pady=(0, 6))

        def refresh_additional_chips():
            if not win.winfo_exists() or not additional_chips_frame.winfo_exists():
                return
            for child in additional_chips_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
            if not selected_additional_areas:
                ctk.CTkLabel(additional_chips_frame, text="No additional areas selected.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=8, pady=6)
                return
            flow = ctk.CTkFrame(additional_chips_frame, fg_color="transparent")
            flow.pack(fill="x", padx=4, pady=4)
            for aname, aid in list(selected_additional_areas.items()):
                chip = ctk.CTkFrame(flow, fg_color="#EEF2FF", corner_radius=14)
                chip.pack(side="left", padx=4, pady=2)
                ctk.CTkLabel(chip, text=f"  🔬 {aname}  ", font=Theme.FONT_CAPTION, text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(6, 2), pady=2)
                ctk.CTkButton(
                    chip, text="✕", width=20, height=20,
                    fg_color="transparent", hover_color="#DBEAFE",
                    text_color=Theme.DANGER, font=("Segoe UI", 9, "bold"),
                    command=lambda n=aname: (selected_additional_areas.pop(n, None), refresh_additional_chips())
                ).pack(side="left", padx=(0, 4))

        def _on_primary_change(new_val):
            primary_badge_lbl.configure(text=f"⭐ Primary Field: {new_val}")
            if new_val in selected_additional_areas:
                selected_additional_areas.pop(new_val, None)
                refresh_additional_chips()

        primary_area_menu.configure(command=_on_primary_change)

        add_area_row = ctk.CTkFrame(scroll, fg_color="transparent")
        add_area_row.pack(fill="x", pady=(0, 12))
        add_area_var = ctk.StringVar(value=initial_areas_list[0])
        add_area_menu = ctk.CTkOptionMenu(add_area_row, variable=add_area_var, values=initial_areas_list, width=320, height=32, fg_color="#475569", button_color="#334155")
        add_area_menu.pack(side="left", padx=(0, 8))

        def _add_selected_additional_area():
            chosen = add_area_var.get().strip()
            if not chosen or chosen not in area_map:
                return
            if chosen == primary_area_var.get().strip():
                bottom_status_lbl.configure(text=f'"{chosen}" is already the Primary Area.', text_color=Theme.DANGER)
                return
            selected_additional_areas[chosen] = area_map[chosen]
            refresh_additional_chips()

        create_secondary_button(add_area_row, text="+ Add Area", command=_add_selected_additional_area, width=100, height=32).pack(side="left")
        refresh_additional_chips()

        # Co-Authors
        selected_coauthors = {}
        for author in paper.get("authors", []):
            a_id = author.get("id")
            if a_id and a_id != self.researcher_id:
                selected_coauthors[a_id] = author.get("name", "Unknown")

        ctk.CTkLabel(scroll, text="Co-Authors", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(6, 2))
        coauthor_chips_frame = ctk.CTkScrollableFrame(scroll, fg_color="#F8FAFC", corner_radius=8, height=65)
        coauthor_chips_frame.pack(fill="x", pady=(0, 6))

        def refresh_coauthor_chips():
            if not win.winfo_exists() or not coauthor_chips_frame.winfo_exists():
                return
            for child in coauthor_chips_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
            if not selected_coauthors:
                ctk.CTkLabel(coauthor_chips_frame, text="No co-authors added.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=8, pady=8)
                return
            flow = ctk.CTkFrame(coauthor_chips_frame, fg_color="transparent")
            flow.pack(fill="x", padx=4, pady=4)
            for rid, rname in list(selected_coauthors.items()):
                chip = ctk.CTkFrame(flow, fg_color="#EEF2FF", corner_radius=14)
                chip.pack(side="left", padx=4, pady=3)
                ctk.CTkLabel(chip, text=f"  👤 {rname} (Co-Author)  ", font=Theme.FONT_BODY, text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(8, 2), pady=3)
                ctk.CTkButton(
                    chip, text="✕", width=22, height=22,
                    fg_color="transparent", hover_color="#DBEAFE",
                    text_color=Theme.DANGER, font=("Segoe UI", 10, "bold"),
                    command=lambda r=rid: (selected_coauthors.pop(r, None), refresh_coauthor_chips(), refresh_collab_results())
                ).pack(side="left", padx=(0, 6))

        collab_search_entry = ctk.CTkEntry(scroll, width=580, height=34, placeholder_text="Search researchers to add as co-authors...")
        collab_search_entry.pack(fill="x", pady=(0, 4))

        collab_results_frame = ctk.CTkScrollableFrame(scroll, fg_color="transparent", height=110)
        collab_results_frame.pack(fill="x", pady=(0, 10))

        def refresh_collab_results():
            if not win.winfo_exists() or not collab_results_frame.winfo_exists():
                return
            for child in collab_results_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass
            q = collab_search_entry.get().strip()
            if not q:
                return
            try:
                results = api_client.search_researchers(q)
            except Exception:
                results = []
            results = [r for r in results if r.get("id") != self.researcher_id and r.get("id") not in selected_coauthors]
            if not results:
                ctk.CTkLabel(collab_results_frame, text=f'No matching researchers found for "{q}".', font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=4)
                return
            for r in results[:8]:
                rname = r.get("name") or "Unknown"
                rid = r.get("id")
                row = ctk.CTkFrame(collab_results_frame, fg_color="#F8FAFC", corner_radius=6)
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=f"👤 {rname}", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(side="left", padx=8, pady=4)
                ctk.CTkButton(
                    row,
                    text="+ Add as Co-Author",
                    width=130,
                    height=26,
                    fg_color=Theme.ACADEMIC_BLUE,
                    hover_color="#173D6E",
                    text_color=Theme.WHITE,
                    font=Theme.FONT_CAPTION,
                    command=lambda i=rid, n=rname: (selected_coauthors.update({i: n}), refresh_coauthor_chips(), refresh_collab_results())
                ).pack(side="right", padx=8, pady=4)

        collab_search_entry.bind("<KeyRelease>", lambda _e: refresh_collab_results() if win.winfo_exists() else None)
        refresh_coauthor_chips()

        # Abstract
        ctk.CTkLabel(scroll, text="Abstract", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(4, 2))
        abstract_box = ctk.CTkTextbox(scroll, width=580, height=100)
        abstract_box.pack(fill="x", pady=(0, 10))
        if paper.get("abstract"):
            abstract_box.insert("1.0", paper.get("abstract"))

        def show_error(msg: str):
            bottom_status_lbl.configure(text=msg, text_color=Theme.DANGER)

        def _save_updates():
            if not win.winfo_exists():
                return
            t = title_entry.get().strip()
            if not t:
                show_error("Paper title is required.")
                return
            y_str = year_entry.get().strip()
            if not y_str or not y_str.isdigit() or len(y_str) != 4:
                show_error("Please enter a valid 4-digit publication year (e.g. 2024).")
                return
            year_int = int(y_str)
            if year_int < 1900 or year_int > 2100:
                show_error("Year must be between 1900 and 2100.")
                return

            chosen_primary = primary_area_var.get().strip()
            if not chosen_primary or chosen_primary not in area_map:
                show_error("Please select a valid Primary Research Area.")
                return

            primary_id = area_map[chosen_primary]
            all_area_ids = [primary_id]
            for aid in selected_additional_areas.values():
                if aid and aid not in all_area_ids:
                    all_area_ids.append(aid)

            coauthor_ids = list(selected_coauthors.keys())
            all_author_ids = [self.researcher_id] + [cid for cid in coauthor_ids if cid != self.researcher_id]

            v_val = venue_entry.get().strip() or None
            d_val = doi_entry.get().strip() or None
            abs_val = abstract_box.get("1.0", "end").strip() or None

            payload = {
                "title": t,
                "publication_year": year_int,
                "venue": v_val,
                "doi": d_val,
                "url": d_val if d_val and (d_val.startswith("http://") or d_val.startswith("https://")) else None,
                "abstract": abs_val,
                "primary_area_id": primary_id,
                "research_area_ids": all_area_ids,
                "author_ids": all_author_ids
            }

            try:
                bottom_status_lbl.configure(text="Updating publication...", text_color=Theme.ACADEMIC_BLUE)
                win.update_idletasks()
                api_client.update_paper(paper["id"], self.researcher_id, payload)
                bottom_status_lbl.configure(text="✓ Paper updated successfully!", text_color="#15803D")
                win.update_idletasks()
                if self.winfo_exists():
                    self._refresh_profile()
                win.after(500, lambda: win.destroy() if win.winfo_exists() else None)
            except Exception as exc:
                if win.winfo_exists():
                    show_error(f"Failed to update paper: {exc}")

        ctk.CTkButton(
            action_row,
            text="Cancel",
            command=win.destroy,
            fg_color="transparent",
            hover_color="#E2E8F0",
            text_color=Theme.SECONDARY_TEXT,
            font=Theme.FONT_BODY,
            width=100,
            height=36
        ).pack(side="right", padx=(0, 16), pady=10)

        create_primary_button(
            action_row,
            text="Save Changes",
            command=_save_updates,
            width=140,
            height=36
        ).pack(side="right", padx=(0, 10), pady=10)
