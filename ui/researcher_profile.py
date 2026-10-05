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

        metrics_row = ctk.CTkFrame(info_col, fg_color="transparent")
        metrics_row.pack(anchor="w", pady=(10, 0))

        for label, value, fg in [
            ("Publications", pub_count, Theme.PURPLE),
            ("Research Areas", area_count, Theme.ACADEMIC_BLUE),
            ("Skills", skill_count, Theme.CYAN),
            ("Citations", p.get("citation_count", 0), Theme.NAVY),
            ("h-index", p.get("h_index", 0), Theme.SECONDARY_TEXT),
        ]:
            box = ctk.CTkFrame(metrics_row, fg_color="#F8FAFC", corner_radius=10, border_width=1, border_color="#E2E8F0")
            box.pack(side="left", padx=(0, 8), pady=2)
            ctk.CTkLabel(box, text=f"{label}: {value}", font=Theme.FONT_CAPTION, text_color=fg, height=28).pack(padx=8, pady=4)

        # Right Metrics Pill
        metrics_col = ctk.CTkFrame(h_inner, fg_color="transparent")
        metrics_col.pack(side="right", padx=(10, 0))

        if self._is_editable(p):
            edit_header_btn = create_primary_button(metrics_col, text="Edit Profile", command=self._open_edit_profile, width=140, height=34)
            edit_header_btn.pack(pady=(0, 8))

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
                sb = create_badge(self._skills_container, text=s.get("name", s), bg_color="#F3F4F6", text_color=Theme.NAVY, font=Theme.FONT_BODY)
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
        ctk.CTkLabel(
            pub_inner,
            text=f"My Publications ({len(pubs)})",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 12))

        if self._is_editable(p):
            btn_row = ctk.CTkFrame(pub_inner, fg_color="transparent")
            btn_row.pack(anchor="e", pady=(0, 10))
            create_primary_button(btn_row, text="+ Add Paper", command=self._open_add_paper, width=120, height=30).pack(side="right")

        if not pubs:
            ctk.CTkLabel(pub_inner, text="No publications added yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
            if self._is_editable(p):
                create_secondary_button(pub_inner, text="Add Paper", command=self._open_add_paper, width=120, height=28).pack(anchor="w", pady=(10, 0))
        else:
            for paper in pubs:
                p_item = ctk.CTkFrame(pub_inner, fg_color=Theme.MUTED_BG, corner_radius=8)
                p_item.pack(fill="x", pady=4)

                p_row = ctk.CTkFrame(p_item, fg_color="transparent")
                p_row.pack(fill="x", padx=14, pady=10)

                left_info = ctk.CTkFrame(p_row, fg_color="transparent")
                left_info.pack(side="left", fill="both", expand=True)

                t_lbl = ctk.CTkLabel(
                    left_info,
                    text=paper["title"],
                    font=Theme.FONT_BODY_BOLD,
                    text_color=Theme.NAVY,
                    anchor="w",
                    justify="left"
                )
                t_lbl.pack(anchor="w")

                auth_names = ", ".join(a["name"] for a in paper.get("authors", []))
                sub_meta = f"Authors: {auth_names}  ·  Year: {paper.get('publication_year')}  ·  Venue: {paper.get('venue')}"
                ctk.CTkLabel(left_info, text=sub_meta, font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT, anchor="w").pack(anchor="w", pady=(2, 0))

                right_action = ctk.CTkFrame(p_row, fg_color="transparent")
                right_action.pack(side="right", padx=(10, 0))

                create_secondary_button(
                    right_action,
                    text="Paper Details →",
                    command=lambda pid=paper["id"]: self.on_select_paper(pid),
                    width=110,
                    height=28
                ).pack()

        # 4. Collaboration Network & Connected Researchers
        net_card = create_card(self)
        net_card.pack(fill="x", padx=25, pady=(0, 30))

        net_inner = ctk.CTkFrame(net_card, fg_color="transparent")
        net_inner.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(
            net_inner,
            text="Collaboration Network & Connected Researchers",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            net_inner,
            text="Discovered direct academic co-authorship relationships in the campus collaboration graph:",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 12))

        collabs = p.get("connected_researchers", [])
        if not collabs:
            ctk.CTkLabel(
                net_inner,
                text="No direct collaborations recorded in the network graph.",
                font=Theme.FONT_BODY,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w", pady=10)
        else:
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
        try:
            parent_win = self.winfo_toplevel()
            px = parent_win.winfo_rootx()
            py = parent_win.winfo_rooty()
            pw = parent_win.winfo_width()
            ph = parent_win.winfo_height()
            x = px + max(0, (pw - width) // 2)
            y = py + max(0, (ph - height) // 2)
        except Exception:
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

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
        self._setup_dialog(win, "Edit Skills", 600, 600)

        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(container, text="Edit Skills", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            container,
            text="Search and select multiple skills. Selected skills appear as removable badges below:",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w", pady=(0, 10))

        # Selected skills state management
        selected_lookup = {}
        selected_order = []
        for s in self.profile.get("skills", []):
            name = str(s.get("name") if isinstance(s, dict) else s).strip()
            if name:
                key = name.lower()
                if key not in selected_lookup:
                    selected_lookup[key] = name
                    selected_order.append(name)

        # 1. Selected Skills Chips Container
        ctk.CTkLabel(container, text="Selected Skills", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w", pady=(4, 4))
        selected_chips_frame = ctk.CTkScrollableFrame(container, fg_color="#F8FAFC", corner_radius=8, height=90)
        selected_chips_frame.pack(fill="x", pady=(0, 12))

        def add_skill(name: str):
            clean = (name or "").strip()
            if not clean:
                return
            key = clean.lower()
            if key not in selected_lookup:
                selected_lookup[key] = clean
                selected_order.append(clean)
                refresh_selected_chips()
                refresh_suggestions()

        def remove_skill(name: str):
            clean = (name or "").strip()
            key = clean.lower()
            if key in selected_lookup:
                del selected_lookup[key]
                selected_order[:] = [n for n in selected_order if n.lower() != key]
                refresh_selected_chips()
                refresh_suggestions()

        def refresh_selected_chips():
            if not win.winfo_exists() or not selected_chips_frame.winfo_exists():
                return
            for child in selected_chips_frame.winfo_children():
                try:
                    child.destroy()
                except Exception:
                    pass

            if not selected_order:
                ctk.CTkLabel(
                    selected_chips_frame,
                    text="No skills selected yet. Search below to add skills.",
                    font=Theme.FONT_CAPTION,
                    text_color=Theme.SECONDARY_TEXT
                ).pack(anchor="w", padx=8, pady=10)
                return

            flow_box = ctk.CTkFrame(selected_chips_frame, fg_color="transparent")
            flow_box.pack(fill="x", padx=4, pady=4)

            for name in selected_order:
                chip = ctk.CTkFrame(flow_box, fg_color="#EEF2FF", corner_radius=14)
                chip.pack(side="left", padx=4, pady=4)

                ctk.CTkLabel(
                    chip,
                    text=f" {name} ",
                    font=Theme.FONT_BODY,
                    text_color=Theme.ACADEMIC_BLUE
                ).pack(side="left", padx=(8, 2), pady=3)

                ctk.CTkButton(
                    chip,
                    text="✕",
                    width=22,
                    height=22,
                    fg_color="transparent",
                    hover_color="#DBEAFE",
                    text_color=Theme.DANGER,
                    font=("Segoe UI", 11, "bold"),
                    command=lambda n=name: remove_skill(n)
                ).pack(side="left", padx=(2, 6), pady=3)

        # 2. Search Skills Input
        ctk.CTkLabel(container, text="Search Skills", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        search_entry = ctk.CTkEntry(container, width=560, height=36, placeholder_text="Search skills (e.g. Python, MySQL, FastAPI)...")
        search_entry.pack(fill="x", pady=(0, 10))

        # 3. Available Skills / Suggestions Frame
        ctk.CTkLabel(container, text="Available Skills (click to toggle)", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))
        suggestion_frame = ctk.CTkScrollableFrame(container, fg_color="transparent", height=180)
        suggestion_frame.pack(fill="both", expand=True, pady=(0, 10))

        status_lbl = ctk.CTkLabel(container, text="", font=Theme.FONT_BODY, text_color=Theme.DANGER)
        status_lbl.pack(anchor="w", pady=(0, 6))

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

            normalized_matches = [str(item.get("name") or "").strip() for item in matches if str(item.get("name") or "").strip()]
            match_map = {m.lower(): m for m in normalized_matches}

            if not normalized_matches and not query:
                ctk.CTkLabel(suggestion_frame, text="Type above to search across available skills.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=12)
                return

            if not normalized_matches and query:
                no_res = ctk.CTkLabel(suggestion_frame, text=f'No existing skills found matching "{query}".', font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT)
                no_res.pack(anchor="w", pady=(6, 4))
                add_btn = create_primary_button(
                    suggestion_frame,
                    text=f'+ Add "{query}" to Skills',
                    command=lambda q=query: (add_skill(q), search_entry.delete(0, "end"), refresh_suggestions()),
                    width=200,
                    height=30
                )
                add_btn.pack(anchor="w", pady=(0, 8))
                return

            for skill_name in normalized_matches:
                is_selected = skill_name.lower() in selected_lookup
                row = ctk.CTkFrame(suggestion_frame, fg_color="#F8FAFC" if not is_selected else "#EEF2FF", corner_radius=6)
                row.pack(fill="x", pady=2)

                s_lbl = ctk.CTkLabel(
                    row,
                    text=f"  {skill_name}",
                    font=Theme.FONT_BODY_BOLD if is_selected else Theme.FONT_BODY,
                    text_color=Theme.ACADEMIC_BLUE if is_selected else Theme.DARK_TEXT
                )
                s_lbl.pack(side="left", padx=8, pady=6)

                if is_selected:
                    rem_btn = ctk.CTkButton(
                        row,
                        text="✓ Added (Remove)",
                        width=110,
                        height=26,
                        fg_color="#DBEAFE",
                        hover_color="#BFDBFE",
                        text_color=Theme.ACADEMIC_BLUE,
                        font=Theme.FONT_CAPTION,
                        command=lambda n=skill_name: remove_skill(n)
                    )
                    rem_btn.pack(side="right", padx=8, pady=4)
                else:
                    add_row_btn = ctk.CTkButton(
                        row,
                        text="+ Add",
                        width=70,
                        height=26,
                        fg_color=Theme.ACADEMIC_BLUE,
                        hover_color="#173D6E",
                        text_color=Theme.WHITE,
                        font=Theme.FONT_CAPTION,
                        command=lambda n=skill_name: add_skill(n)
                    )
                    add_row_btn.pack(side="right", padx=8, pady=4)

            # Option to add custom skill if user's search isn't exactly matched
            if query and query.lower() not in match_map and query.lower() not in selected_lookup:
                custom_row = ctk.CTkFrame(suggestion_frame, fg_color="transparent")
                custom_row.pack(fill="x", pady=(8, 4))
                add_btn = create_primary_button(
                    custom_row,
                    text=f'+ Add "{query}" as New Skill',
                    command=lambda q=query: (add_skill(q), search_entry.delete(0, "end"), refresh_suggestions()),
                    width=210,
                    height=30
                )
                add_btn.pack(anchor="w")

        def _on_key_release(_event=None):
            if win.winfo_exists():
                refresh_suggestions()

        search_entry.bind("<KeyRelease>", _on_key_release)
        refresh_selected_chips()
        refresh_suggestions()

        # Action Buttons Row
        action_row = ctk.CTkFrame(container, fg_color="transparent")
        action_row.pack(fill="x", pady=(6, 0))

        def _save_skills():
            if not win.winfo_exists():
                return
            skill_names = list(selected_lookup.values())
            try:
                api_client.update_researcher_skills(self.researcher_id, skill_names)
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
            text="Save Skills",
            command=_save_skills,
            width=140,
            height=34
        ).pack(side="right")

    def _open_add_paper(self):
        win = ctk.CTkToplevel(self)
        self._setup_dialog(win, "Add Research Paper", 640, 620)

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        ctk.CTkLabel(scroll, text="Add Research Paper", font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(scroll, text="Record an academic paper, conference publication, or journal article:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 14))

        # Title
        ctk.CTkLabel(scroll, text="Title *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        title_entry = ctk.CTkEntry(scroll, width=560, height=34, placeholder_text="e.g. Scalable Graph Neural Networks for Academic Collaboration")
        title_entry.pack(anchor="w", pady=(0, 10))

        # Publication Year
        ctk.CTkLabel(scroll, text="Publication Year *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        year_entry = ctk.CTkEntry(scroll, width=200, height=34, placeholder_text="e.g. 2024")
        year_entry.pack(anchor="w", pady=(0, 10))

        # Venue / Journal / Conference
        ctk.CTkLabel(scroll, text="Venue / Journal / Conference", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        venue_entry = ctk.CTkEntry(scroll, width=560, height=34, placeholder_text="e.g. IEEE Transactions on Knowledge and Data Engineering")
        venue_entry.pack(anchor="w", pady=(0, 10))

        # DOI / URL
        ctk.CTkLabel(scroll, text="DOI / URL (optional)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        doi_entry = ctk.CTkEntry(scroll, width=560, height=34, placeholder_text="e.g. 10.1109/TKDE.2024.10452 or https://...")
        doi_entry.pack(anchor="w", pady=(0, 10))

        # Primary Research Area
        area_options = []
        try:
            area_options = api_client.get_research_areas()
        except Exception:
            area_options = []
        area_names = [a["name"] for a in area_options if a.get("name")]
        area_map = {a["name"]: a["id"] for a in area_options if a.get("name")}
        sel_area_var = ctk.StringVar(value=area_names[0] if area_names else "General")

        ctk.CTkLabel(scroll, text="Primary Research Area *", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        primary_area_menu = ctk.CTkOptionMenu(
            scroll,
            variable=sel_area_var,
            values=area_names if area_names else ["General"],
            width=560,
            height=34,
            fg_color=Theme.ACADEMIC_BLUE
        )
        primary_area_menu.pack(anchor="w", pady=(0, 10))

        # Abstract
        ctk.CTkLabel(scroll, text="Abstract", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        abstract_box = ctk.CTkTextbox(scroll, width=560, height=110)
        abstract_box.pack(anchor="w", pady=(0, 12))

        status_lbl = ctk.CTkLabel(scroll, text="", font=Theme.FONT_BODY, text_color=Theme.DANGER)
        status_lbl.pack(anchor="w", pady=(0, 8))

        # Buttons
        action_row = ctk.CTkFrame(scroll, fg_color="transparent")
        action_row.pack(fill="x", pady=(6, 12))

        def _save_paper():
            if not win.winfo_exists():
                return
            t = title_entry.get().strip()
            if not t:
                status_lbl.configure(text="Paper title is required.", text_color=Theme.DANGER)
                return
            y_str = year_entry.get().strip()
            if not y_str or not y_str.isdigit() or len(y_str) != 4:
                status_lbl.configure(text="Please enter a valid 4-digit publication year (e.g. 2024).", text_color=Theme.DANGER)
                return
            year_int = int(y_str)
            if year_int < 1900 or year_int > 2100:
                status_lbl.configure(text="Year must be between 1900 and 2100.", text_color=Theme.DANGER)
                return

            v_val = venue_entry.get().strip() or None
            d_val = doi_entry.get().strip() or None
            abs_val = abstract_box.get("1.0", "end").strip() or None
            primary_id = area_map.get(sel_area_var.get())

            payload = {
                "title": t,
                "publication_year": year_int,
                "venue": v_val,
                "doi": d_val,
                "url": d_val if d_val and (d_val.startswith("http://") or d_val.startswith("https://")) else None,
                "abstract": abs_val,
                "primary_area_id": primary_id,
                "research_area_ids": [primary_id] if primary_id else [],
                "author_ids": [self.researcher_id]
            }
            try:
                api_client.create_paper(payload)
                win.destroy()
                if self.winfo_exists():
                    self._refresh_profile()
            except Exception as exc:
                if win.winfo_exists():
                    status_lbl.configure(text=f"Failed to add paper: {exc}", text_color=Theme.DANGER)

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
            text="Save Paper",
            command=_save_paper,
            width=140,
            height=34
        ).pack(side="right")
