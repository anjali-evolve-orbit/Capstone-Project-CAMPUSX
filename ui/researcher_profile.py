"""
CAMPUSX — Discover People Behind the Work System
Researcher Profile: Detailed Biography, Publications, Areas, and Collaboration Network
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

    def _load_profile(self):
        try:
            self.profile = api_client.get_researcher_detail(self.researcher_id)
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

        if self.current_user and p.get("user_id") and self.current_user.get("id") == p.get("user_id"):
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
            if self.current_user and p.get("user_id") and self.current_user.get("id") == p.get("user_id"):
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
            if self.current_user and p.get("user_id") and self.current_user.get("id") == p.get("user_id"):
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
            if self.current_user and p.get("user_id") and self.current_user.get("id") == p.get("user_id"):
                create_secondary_button(self._skills_container, text="Add Skills", command=self._open_skills_editor, width=120, height=28).pack(anchor="w", pady=(8, 0))

        editable = False
        try:
            editable = bool(self.current_user and p.get("user_id") and self.current_user.get("id") == p.get("user_id"))
        except Exception:
            editable = False
        if editable:
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

        if self.current_user and p.get("user_id") and self.current_user.get("id") == p.get("user_id"):
            btn_row = ctk.CTkFrame(pub_inner, fg_color="transparent")
            btn_row.pack(anchor="e", pady=(0, 10))
            create_primary_button(btn_row, text="+ Add Paper", command=self._open_add_paper, width=120, height=30).pack(side="right")

        if not pubs:
            ctk.CTkLabel(pub_inner, text="No publications added yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
            if self.current_user and p.get("user_id") and self.current_user.get("id") == p.get("user_id"):
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
        for w in self.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        self._load_profile()
        self._build_ui()

    def _open_edit_profile(self):
        if not self.profile:
            return
        win = ctk.CTkToplevel(self)
        win.title("Edit Profile")
        win.geometry("620x500")

        frame = ctk.CTkFrame(win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(frame, text="Full Name", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        name_entry = ctk.CTkEntry(frame, width=560)
        name_entry.insert(0, self.profile.get("name", ""))
        name_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(frame, text="Designation", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        designation_entry = ctk.CTkEntry(frame, width=560)
        designation_entry.insert(0, self.profile.get("designation", ""))
        designation_entry.pack(anchor="w", pady=(0, 8))

        institution_options = []
        try:
            institution_options = api_client.get_institutions()
        except Exception:
            institution_options = []
        institution_names = [item.get("name") for item in institution_options if item.get("name")]
        institution_map = {item.get("name"): item.get("id") for item in institution_options if item.get("name")}
        current_inst_name = self.profile.get("institution_name") or ""
        selected_institution = ctk.StringVar(value=current_inst_name if current_inst_name in institution_map else (institution_names[0] if institution_names else ""))
        ctk.CTkLabel(frame, text="Institution", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        institution_menu = ctk.CTkOptionMenu(frame, variable=selected_institution, values=institution_names, width=560)
        institution_menu.pack(anchor="w", pady=(0, 8))

        department_options = []
        try:
            department_options = api_client.get_departments(self.profile.get("institution_id")) if self.profile.get("institution_id") else []
        except Exception:
            department_options = []
        department_names = [item.get("name") for item in department_options if item.get("name")]
        department_map = {item.get("name"): item.get("id") for item in department_options if item.get("name")}
        current_dept_name = self.profile.get("department_name") or ""
        selected_department = ctk.StringVar(value=current_dept_name if current_dept_name in department_map else (department_names[0] if department_names else ""))
        ctk.CTkLabel(frame, text="Department", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        department_menu = ctk.CTkOptionMenu(frame, variable=selected_department, values=department_names, width=560)
        department_menu.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(frame, text="Email (read-only)", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        email_entry = ctk.CTkEntry(frame, width=560)
        email_entry.insert(0, self.profile.get("email", ""))
        email_entry.configure(state="disabled")
        email_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(frame, text="Website", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        website_entry = ctk.CTkEntry(frame, width=560)
        website_entry.insert(0, self.profile.get("website", ""))
        website_entry.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(frame, text="Bio", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        bio_box = ctk.CTkTextbox(frame, width=560, height=110)
        bio_box.insert("1.0", self.profile.get("bio", ""))
        bio_box.pack(anchor="w", pady=(0, 10))

        status = ctk.CTkLabel(frame, text="", font=Theme.FONT_BODY, text_color=Theme.SUCCESS)
        status.pack(anchor="w", pady=(0, 8))

        def _save():
            institution_id = institution_map.get(selected_institution.get()) if selected_institution.get() in institution_map else self.profile.get("institution_id")
            department_id = department_map.get(selected_department.get()) if selected_department.get() in department_map else self.profile.get("department_id")
            payload = {
                "name": name_entry.get().strip(),
                "designation": designation_entry.get().strip(),
                "institution_id": institution_id,
                "department_id": department_id,
                "bio": bio_box.get("1.0", "end").strip() or None,
                "website": website_entry.get().strip() or None
            }
            if not payload["name"]:
                status.configure(text="Name is required.", text_color=Theme.DANGER)
                return
            try:
                api_client.update_researcher_profile(self.researcher_id, payload)
                status.configure(text="Profile saved.", text_color=Theme.SUCCESS)
                win.destroy()
                self._refresh_profile()
            except Exception as exc:
                status.configure(text=str(exc), text_color=Theme.DANGER)

        action_row = ctk.CTkFrame(frame, fg_color="transparent")
        action_row.pack(fill="x", pady=(12, 0))
        ctk.CTkButton(action_row, text="Cancel", command=win.destroy, fg_color="transparent", text_color=Theme.SECONDARY_TEXT, width=110).pack(side="left")
        create_primary_button(action_row, text="Save Changes", command=_save, width=150).pack(side="right", padx=(8, 0))

    def _open_edit_areas(self):
        if not self.profile:
            return
        win = ctk.CTkToplevel(self)
        win.title("Edit Research Areas")
        win.geometry("500x420")

        frame = ctk.CTkFrame(win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(frame, text="Select your research areas", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 8))
        current_ids = {a.get("id") for a in self.profile.get("areas", []) if a.get("id") is not None}

        area_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        area_frame.pack(fill="both", expand=True)

        try:
            area_rows = api_client.get_research_areas()
        except Exception as exc:
            area_rows = []
            ctk.CTkLabel(frame, text=f"Unable to load research areas: {exc}", font=Theme.FONT_BODY, text_color=Theme.DANGER).pack(anchor="w", pady=8)

        selected = {}
        for area in area_rows:
            area_id = area.get("id")
            var = ctk.BooleanVar(value=(area_id in current_ids))
            cb = ctk.CTkCheckBox(
                area_frame,
                text=area.get("name", "Untitled area"),
                variable=var,
                font=Theme.FONT_BODY,
                text_color=Theme.DARK_TEXT,
                checkbox_width=18,
                checkbox_height=18,
                fg_color=Theme.ACADEMIC_BLUE
            )
            cb.pack(anchor="w", pady=3)
            selected[area_id] = var

        status = ctk.CTkLabel(frame, text="", font=Theme.FONT_BODY, text_color=Theme.SUCCESS)
        status.pack(anchor="w", pady=(10, 6))

        def _save():
            chosen = [area_id for area_id, var in selected.items() if var.get() and area_id is not None]
            try:
                api_client.update_researcher_areas(self.researcher_id, chosen)
                status.configure(text="Research areas updated.", text_color=Theme.SUCCESS)
                win.destroy()
                self._refresh_profile()
            except Exception as exc:
                status.configure(text=str(exc), text_color=Theme.DANGER)

        action_row = ctk.CTkFrame(frame, fg_color="transparent")
        action_row.pack(anchor="w")
        create_primary_button(action_row, text="Save Areas", command=_save, width=120).pack(side="left", padx=(0, 8))
        ctk.CTkButton(action_row, text="Cancel", command=win.destroy, fg_color="transparent", text_color=Theme.SECONDARY_TEXT).pack(side="left")

    def _toggle_edit_skills(self):
        self._open_skills_editor()

    def _open_skills_editor(self):
        if not self.profile:
            return

        win = ctk.CTkToplevel(self)
        win.title("Edit Skills")
        win.geometry("560x520")
        win.minsize(520, 440)

        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=14, pady=14)

        ctk.CTkLabel(frm, text="Edit Skills", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 8))

        search_var = ctk.StringVar(value="")
        search_entry = ctk.CTkEntry(frm, width=520, placeholder_text="Search skills")
        search_entry.pack(fill="x", pady=(0, 8))

        selected_lookup = {}
        selected_order = []
        for skill in self.profile.get("skills", []):
            name = str(skill.get("name") or skill).strip()
            if not name:
                continue
            key = name.lower()
            if key not in selected_lookup:
                selected_lookup[key] = name
                selected_order.append(name)

        suggestion_frame = ctk.CTkScrollableFrame(frm, fg_color="transparent", height=150)
        suggestion_frame.pack(fill="x", pady=(0, 10))

        selected_frame = ctk.CTkFrame(frm, fg_color="transparent")
        selected_frame.pack(fill="x", pady=(0, 10))

        status = ctk.CTkLabel(frm, text="", font=Theme.FONT_BODY, text_color=Theme.SUCCESS)
        status.pack(anchor="w", pady=(0, 8))

        def add_selected_skill(name: str):
            clean = (name or "").strip()
            if not clean:
                return
            key = clean.lower()
            if key not in selected_lookup:
                selected_lookup[key] = clean
                selected_order.append(clean)
                refresh_selected_skills()
                refresh_suggestions()

        def remove_selected_skill(name: str):
            clean = (name or "").strip()
            key = clean.lower()
            if key in selected_lookup:
                del selected_lookup[key]
                selected_order[:] = [n for n in selected_order if n.lower() != key]
                refresh_selected_skills()
                refresh_suggestions()

        def refresh_selected_skills():
            for child in selected_frame.winfo_children():
                child.destroy()

            if not selected_order:
                ctk.CTkLabel(selected_frame, text="No skills selected yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
                return

            chip_container = ctk.CTkFrame(selected_frame, fg_color="transparent")
            chip_container.pack(anchor="w")
            for name in selected_order:
                chip = ctk.CTkFrame(chip_container, fg_color="#EEF2FF", corner_radius=14)
                chip.pack(side="left", padx=(0, 6), pady=2)
                ctk.CTkLabel(chip, text=f"  {name} ", font=Theme.FONT_CAPTION, text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=(8, 0), pady=4)
                ctk.CTkButton(
                    chip,
                    text="✕",
                    width=20,
                    height=20,
                    fg_color="transparent",
                    hover_color="#DDE7FF",
                    text_color=Theme.ACADEMIC_BLUE,
                    command=lambda n=name: remove_selected_skill(n)
                ).pack(side="left", padx=(4, 8), pady=4)

        def refresh_suggestions():
            for child in suggestion_frame.winfo_children():
                child.destroy()

            query = search_var.get().strip()
            try:
                matches = api_client.get_skills(query, limit=20)
            except Exception:
                matches = []

            # Show a helpful custom add action when the search does not match an existing skill.
            normalized_matches = [str(item.get("name") or "").strip() for item in matches if str(item.get("name") or "").strip()]
            match_names = {name.lower(): name for name in normalized_matches}

            if not normalized_matches:
                if query:
                    no_match = ctk.CTkLabel(suggestion_frame, text='No matching skill found.', font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT)
                    no_match.pack(anchor="w", pady=(4, 6))
                    add_custom = create_primary_button(
                        suggestion_frame,
                        text=f'+ Add "{query}"',
                        command=lambda: add_selected_skill(query),
                        width=180,
                        height=28
                    )
                    add_custom.pack(anchor="w", pady=(0, 6))
                else:
                    ctk.CTkLabel(suggestion_frame, text="Start typing to find skills.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=8)
                return

            for skill_name in normalized_matches:
                selected = skill_name.lower() in selected_lookup
                cb = ctk.CTkCheckBox(
                    suggestion_frame,
                    text=skill_name,
                    variable=ctk.BooleanVar(value=selected),
                    command=lambda n=skill_name: (add_selected_skill(n) if n.lower() not in selected_lookup else remove_selected_skill(n)),
                    checkbox_width=18,
                    checkbox_height=18,
                    fg_color=Theme.ACADEMIC_BLUE,
                    text_color=Theme.DARK_TEXT,
                    font=Theme.FONT_BODY
                )
                cb.pack(anchor="w", pady=3)

            if query and query.lower() not in match_names:
                add_custom = create_primary_button(
                    suggestion_frame,
                    text=f'+ Add "{query}"',
                    command=lambda: add_selected_skill(query),
                    width=180,
                    height=28
                )
                add_custom.pack(anchor="w", pady=(8, 0))

        search_entry.bind("<KeyRelease>", lambda _event: refresh_suggestions())
        refresh_selected_skills()
        refresh_suggestions()

        btn_row = ctk.CTkFrame(frm, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 0))

        def _save():
            skill_names = list(selected_lookup.values())
            try:
                api_client.update_researcher_skills(self.researcher_id, skill_names)
                status.configure(text="Skills saved successfully.", text_color=Theme.SUCCESS)
                win.destroy()
                self._refresh_profile()
            except Exception as exc:
                status.configure(text=str(exc), text_color=Theme.DANGER)

        ctk.CTkButton(btn_row, text="Cancel", command=win.destroy, fg_color="transparent", text_color=Theme.SECONDARY_TEXT, width=110).pack(side="left")
        create_primary_button(btn_row, text="Save Skills", command=_save, width=150).pack(side="right")

    def _open_add_paper(self):
        win = ctk.CTkToplevel(self)
        win.title("Add Paper")
        win.geometry("640x520")

        frm = ctk.CTkFrame(win, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=12, pady=12)

        # Fields: Title, Year, Venue, DOI, Abstract, Primary Area
        ctk.CTkLabel(frm, text="Title", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        title_entry = ctk.CTkEntry(frm, width=580)
        title_entry.pack(pady=(0, 8))

        ctk.CTkLabel(frm, text="Publication Year", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        year_entry = ctk.CTkEntry(frm, width=200)
        year_entry.pack(pady=(0, 8))

        ctk.CTkLabel(frm, text="Venue / Journal / Conference", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        venue_entry = ctk.CTkEntry(frm, width=580)
        venue_entry.pack(pady=(0, 8))

        ctk.CTkLabel(frm, text="DOI / URL (optional)", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        doi_entry = ctk.CTkEntry(frm, width=580)
        doi_entry.pack(pady=(0, 8))

        ctk.CTkLabel(frm, text="Research Areas (select one or more)", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        areas = []
        selected_area_vars = {}
        try:
            areas = api_client.get_research_areas()
        except Exception:
            areas = []

        area_frame = ctk.CTkScrollableFrame(frm, fg_color="transparent", width=560, height=120)
        area_frame.pack(pady=(0, 8), fill="both")
        if areas:
            for area in areas:
                var = ctk.BooleanVar(value=False)
                selected_area_vars[area.get("id")] = var
                ctk.CTkCheckBox(
                    area_frame,
                    text=area.get("name", "Untitled area"),
                    variable=var,
                    checkbox_width=18,
                    checkbox_height=18,
                    fg_color=Theme.ACADEMIC_BLUE,
                    text_color=Theme.DARK_TEXT,
                    font=Theme.FONT_BODY
                ).pack(anchor="w", pady=2)
        else:
            ctk.CTkLabel(area_frame, text="No research areas are available yet.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")

        ctk.CTkLabel(frm, text="Abstract (optional)", font=Theme.FONT_BODY_BOLD).pack(anchor="w", pady=(2, 2))
        abstract_box = ctk.CTkTextbox(frm, width=580, height=110)
        abstract_box.pack(pady=(0, 8))

        status = ctk.CTkLabel(frm, text="", font=Theme.FONT_BODY)
        status.pack(pady=(4, 8))

        btn_row = ctk.CTkFrame(frm, fg_color="transparent")
        btn_row.pack()

        def _save_paper():
            title = title_entry.get().strip()
            year_text = year_entry.get().strip()
            venue = venue_entry.get().strip() or None
            doi = doi_entry.get().strip() or None
            abstract = abstract_box.get("1.0", "end").strip() or None
            if not title:
                status.configure(text="Please enter a paper title.", text_color=Theme.DANGER)
                return
            try:
                year = int(year_text)
            except Exception:
                status.configure(text="Please enter a valid publication year.", text_color=Theme.DANGER)
                return

            primary_area_id = None
            selected_ids = []
            for area_id, var in selected_area_vars.items():
                if var.get():
                    selected_ids.append(int(area_id))
                    if primary_area_id is None:
                        primary_area_id = int(area_id)

            payload = {
                "title": title,
                "publication_year": year,
                "venue": venue,
                "doi": doi,
                "url": doi if doi and (doi.startswith("http://") or doi.startswith("https://")) else None,
                "abstract": abstract,
                "primary_area_id": primary_area_id,
                "research_area_ids": selected_ids,
                "author_ids": [self.researcher_id]
            }
            try:
                api_client.create_paper(payload)
                status.configure(text="Paper saved.", text_color=Theme.SUCCESS)
                win.destroy()
                self._refresh_profile()
            except Exception as e:
                status.configure(text=str(e), text_color=Theme.DANGER)

        save_btn = create_primary_button(btn_row, text="Save Paper", command=_save_paper, width=120)
        save_btn.pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Cancel", command=win.destroy, fg_color="transparent").pack(side="left", padx=6)
