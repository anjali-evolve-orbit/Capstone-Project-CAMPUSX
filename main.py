"""
CAMPUSX — Discover People Behind the Work System
Main Desktop Application Entry Point (Python CustomTkinter & FastAPI Integration)
"""

import sys
import os
import time
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import customtkinter as ctk
from PIL import Image

from config import PROJECT_NAME, TAGLINE, LOGO_PATH, ASSETS_DIR, API_PORT
from api_client.client import api_client
from ui.theme import Theme
from ui.landing import LandingView
from ui.login import LoginView
from ui.register import RegisterView
from ui.app_shell import AppShell
from ui.dashboard import DashboardView
from ui.researchers import ResearchersView
from ui.researcher_profile import ResearcherProfileView
from ui.papers import PapersView
from ui.paper_details import PaperDetailsView
from ui.research_areas import ResearchAreasView
from ui.communities import CommunitiesView
from ui.network import NetworkView
from ui.recommendations import RecommendationsView
from ui.search_view import CategorizedSearchView
from ui.settings import SettingsView


class CampusXApp(ctk.CTk):
    """Primary CustomTkinter Window for CAMPUSX."""

    def __init__(self):
        super().__init__()

        # Window Setup
        self.title(f"{PROJECT_NAME} — {TAGLINE}")
        self.geometry("1240x780")
        self.minsize(1080, 680)

        # Set Window Icon if available
        icon_path = ASSETS_DIR / "campusx_icon.png"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.current_user: Optional[Dict[str, Any]] = None
        self.app_shell: Optional[AppShell] = None
        self.active_view = None

        # Container for screens (Landing, Login, Register, AppShell)
        self.main_container = ctk.CTkFrame(self, fg_color=Theme.SOFT_BG)
        self.main_container.pack(fill="both", expand=True)

        # Start background API if needed and show Landing view
        self._ensure_api_server()
        self.show_landing()

    def _ensure_api_server(self):
        """Check if FastAPI is running, else start it in a background thread."""
        is_healthy, _ = api_client.check_health()
        if not is_healthy:
            def run_server():
                import uvicorn
                from api.main import app
                uvicorn.run(app, host="127.0.0.1", port=API_PORT, log_level="warning")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(1.2)  # Give server a brief moment to bind port

    def _clear_main_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # --- Screen Transitions ---

    def show_landing(self):
        """Display Landing Page."""
        self._clear_main_container()
        self.app_shell = None
        landing = LandingView(
            parent=self.main_container,
            on_explore=self._on_explore_campus,
            on_get_started=self.show_register,
            on_login=self.show_login
        )
        landing.pack(fill="both", expand=True)

    def show_login(self):
        """Display Login Screen."""
        self._clear_main_container()
        self.app_shell = None
        login = LoginView(
            parent=self.main_container,
            on_login_success=self._on_auth_success,
            on_go_to_register=self.show_register,
            on_back_to_landing=self.show_landing
        )
        login.pack(fill="both", expand=True)

    def show_register(self):
        """Display Registration Screen."""
        self._clear_main_container()
        self.app_shell = None
        register = RegisterView(
            parent=self.main_container,
            on_register_success=self._on_auth_success,
            on_go_to_login=self.show_login,
            on_back_to_landing=self.show_landing
        )
        register.pack(fill="both", expand=True)

    def _on_explore_campus(self):
        """Explore Campus: If not logged in, auto-login with default demo scholar account or go to login."""
        try:
            res = api_client.login("student@campusx.edu", "CampusX@2026")
            self._on_auth_success(res.get("user"))
        except Exception:
            self.show_login()

    def _on_auth_success(self, user: Dict[str, Any]):
        """Authenticated: Load the App Shell and default to Dashboard."""
        self.current_user = user
        self._clear_main_container()

        self.app_shell = AppShell(
            parent=self.main_container,
            current_user=self.current_user,
            on_logout=self._on_logout,
            on_search_query=self._on_global_search,
            on_navigate=self.navigate_tab
        )
        self.app_shell.pack(fill="both", expand=True)

        # Default to Dashboard
        self.navigate_tab("dashboard")

    def _on_logout(self):
        """Log out and return to Landing page."""
        api_client.logout()
        self.current_user = None
        self.show_landing()

    def _clear_content(self):
        """Clear existing active view in AppShell content frame safely before creating new view."""
        if not self.app_shell:
            return
        if self.active_view is not None:
            try:
                self.active_view.destroy()
            except Exception:
                pass
            self.active_view = None
        for widget in self.app_shell.content_frame.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

    def _on_global_search(self, query: str):
        """Execute global categorized search and open search results view."""
        if not self.app_shell:
            return
        self._clear_content()
        self.active_view = CategorizedSearchView(
            parent=self.app_shell.content_frame,
            query=query,
            on_back=lambda: self.navigate_tab("dashboard"),
            on_select_researcher=self.show_researcher_profile,
            on_select_paper=self.show_paper_details,
            on_select_area=self._on_select_area
        )
        self.active_view.pack(fill="both", expand=True)

    # --- In-App Navigation ---

    def navigate_tab(self, tab_id: str, param: Optional[Any] = None):
        """Switch active sub-view inside App Shell."""
        if not self.app_shell:
            return

        self.app_shell.set_active_tab(tab_id)
        # Clear existing active view before creating the new one
        self._clear_content()

        parent = self.app_shell.content_frame
        # Special handling for My Profile: resolve researcher by current user.
        if tab_id == "my_profile":
            try:
                if not self.current_user or not self.current_user.get("id"):
                    self._clear_content()
                    notice = ctk.CTkFrame(parent, fg_color=Theme.WHITE)
                    notice.pack(fill="both", expand=True, padx=25, pady=25)
                    ctk.CTkLabel(notice, text="Your researcher profile is not available yet.", font=Theme.FONT_TITLE, text_color=Theme.SECONDARY_TEXT).pack(pady=12)
                    return
                res = api_client.get_researcher_by_user(self.current_user.get("id"))
                researcher_id = res.get("id")
                view = ResearcherProfileView(
                    parent=parent,
                    researcher_id=researcher_id,
                    on_back=lambda: self.navigate_tab("researchers"),
                    on_select_paper=self.show_paper_details,
                    on_select_researcher=self.show_researcher_profile,
                    current_user=self.current_user
                )
                self.active_view = view
                self.active_view.pack(fill="both", expand=True)
                return
            except Exception:
                self._clear_content()
                notice = ctk.CTkFrame(parent, fg_color=Theme.WHITE)
                notice.pack(fill="both", expand=True, padx=25, pady=25)
                ctk.CTkLabel(notice, text="Your researcher profile is not available yet.", font=Theme.FONT_TITLE, text_color=Theme.SECONDARY_TEXT).pack(pady=12)
                return

        if tab_id == "dashboard":
            view = DashboardView(
                parent=parent,
                current_user=self.current_user,
                on_navigate=self.navigate_tab
            )
        elif tab_id == "researchers":
            view = ResearchersView(
                parent=parent,
                on_select_researcher=self.show_researcher_profile
            )
        elif tab_id == "researcher_profile":
            if param is None:
                self._clear_content()
                notice = ctk.CTkFrame(parent, fg_color=Theme.WHITE)
                notice.pack(fill="both", expand=True, padx=25, pady=25)
                ctk.CTkLabel(notice, text="Researcher profile is not available.", font=Theme.FONT_TITLE, text_color=Theme.SECONDARY_TEXT).pack(pady=12)
                return
            view = ResearcherProfileView(
                parent=parent,
                researcher_id=int(param),
                on_back=lambda: self.navigate_tab("researchers"),
                on_select_paper=self.show_paper_details,
                on_select_researcher=self.show_researcher_profile,
                current_user=self.current_user
            )
        elif tab_id == "papers":
            view = PapersView(
                parent=parent,
                on_select_paper=self.show_paper_details
            )
        elif tab_id == "paper_details":
            view = PaperDetailsView(
                parent=parent,
                paper_id=param or 1,
                on_back=lambda: self.navigate_tab("papers"),
                on_select_researcher=self.show_researcher_profile,
                on_select_paper=self.show_paper_details
            )
        elif tab_id == "research_areas":
            view = ResearchAreasView(
                parent=parent,
                on_explore_area=self._on_select_area
            )
        elif tab_id == "communities":
            view = CommunitiesView(
                parent=parent,
                on_select_researcher=self.show_researcher_profile
            )
        elif tab_id == "network":
            view = NetworkView(
                parent=parent,
                current_user=self.current_user,
                on_select_researcher=self.show_researcher_profile
            )
        elif tab_id == "recommendations":
            view = RecommendationsView(
                parent=parent,
                current_user=self.current_user,
                on_select_researcher=self.show_researcher_profile
            )
        elif tab_id == "settings":
            view = SettingsView(
                parent=parent,
                current_user=self.current_user
            )
        else:
            view = DashboardView(
                parent=parent,
                current_user=self.current_user,
                on_navigate=self.navigate_tab
            )

        self.active_view = view
        self.active_view.pack(fill="both", expand=True)

    def show_researcher_profile(self, researcher_id: int):
        self.navigate_tab("researcher_profile", param=researcher_id)

    def show_paper_details(self, paper_id: int):
        self.navigate_tab("paper_details", param=paper_id)

    def _on_select_area(self, area_id: int, area_name: str):
        """Navigate to researchers and filter by area."""
        self.navigate_tab("researchers")


def main():
    print(f"Starting {PROJECT_NAME} — {TAGLINE}...")
    app = CampusXApp()
    app.mainloop()


if __name__ == "__main__":
    main()
