"""
CAMPUSX — Discover People Behind the Work System
API Client: HTTP/JSON Communication Layer for CustomTkinter Frontend
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import requests

from config import API_BASE_URL

logger = logging.getLogger("campusx.api_client")


class APIClientError(Exception):
    """Raised when an API request fails."""
    pass


class CampusXAPIClient:
    """Client for frontend to communicate with FastAPI REST API."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.current_user: Optional[Dict[str, Any]] = None

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 8
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=timeout
            )
            if resp.status_code >= 400:
                try:
                    err_json = resp.json()
                    detail = err_json.get("detail", resp.text)
                except Exception:
                    detail = resp.text
                raise APIClientError(detail)
            return resp.json()
        except requests.exceptions.ConnectionError as ce:
            raise APIClientError(
                f"Cannot connect to CAMPUSX API Server at {self.base_url}.\n"
                f"Please ensure the FastAPI backend is running.\n\n"
                f"Start with: python -m uvicorn api.main:app --port 8000"
            ) from ce
        except requests.exceptions.RequestException as re:
            raise APIClientError(f"Network error: {str(re)}") from re

    # --- Health & Connectivity ---
    def check_health(self) -> Tuple[bool, str]:
        try:
            data = self._request("GET", "/api/health", timeout=3)
            return True, data.get("project", "CAMPUSX")
        except Exception as e:
            return False, str(e)

    # --- Authentication ---
    def login(self, email: str, password: str) -> Dict[str, Any]:
        data = self._request("POST", "/api/auth/login", json_data={"email": email, "password": password})
        self.current_user = data.get("user")
        return data

    def register(
        self,
        full_name: str,
        email: str,
        password: str,
        role: str = "Student",
        campus_id: Optional[int] = None,
        institution_id: Optional[int] = None,
        department_id: Optional[int] = None,
        custom_institution: Optional[str] = None,
        custom_department: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": role,
            "campus_id": campus_id,
            "institution_id": institution_id,
            "department_id": department_id,
            "custom_institution": custom_institution,
            "custom_department": custom_department
        }
        data = self._request("POST", "/api/auth/register", json_data=payload)
        self.current_user = data.get("user")
        return data

    def logout(self):
        self.current_user = None

    def forgot_password(self, email: str) -> Dict[str, Any]:
        """Request a password reset token for the given email address."""
        return self._request("POST", "/api/auth/forgot-password", json_data={"email": email})

    def reset_password(self, token: str, new_password: str, confirm_password: str) -> Dict[str, Any]:
        """Reset password using a single-use token."""
        return self._request(
            "POST",
            "/api/auth/reset-password",
            json_data={
                "token": token,
                "new_password": new_password,
                "confirm_password": confirm_password
            }
        )

    # --- Ecosystem Hierarchy ---
    def get_campuses(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/ecosystem/campuses")

    def get_institutions(self, campus_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"campus_id": campus_id} if campus_id else None
        return self._request("GET", "/api/ecosystem/institutions", params=params)

    def get_departments(self, institution_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {"institution_id": institution_id} if institution_id else None
        return self._request("GET", "/api/ecosystem/departments", params=params)

    # --- Dashboard & Metrics ---
    def get_dashboard_stats(self) -> Dict[str, Any]:
        return self._request("GET", "/api/stats")

    # --- Researchers ---
    def get_researchers(
        self,
        institution_id: Optional[int] = None,
        department_id: Optional[int] = None,
        area_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if institution_id:
            params["institution_id"] = institution_id
        if department_id:
            params["department_id"] = department_id
        if area_id:
            params["area_id"] = area_id
        if search:
            params["search"] = search
        return self._request("GET", "/api/researchers", params=params)

    def search_researchers(self, query: str) -> List[Dict[str, Any]]:
        """Search researchers by full name, partial name, email, or department."""
        return self.get_researchers(search=query)

    def get_researcher_detail(self, researcher_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/researchers/{researcher_id}")

    def get_researcher_by_user(self, user_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/researchers/by_user/{user_id}")

    def update_researcher_profile(self, researcher_id: int, profile: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/api/researchers/{researcher_id}", json_data=profile)

    def get_skills(self, query: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        if query:
            params["query"] = query
        return self._request("GET", "/api/skills", params=params)

    def update_researcher_skills(self, researcher_id: int, skills: list) -> Dict[str, Any]:
        payload = {"skills": skills}
        return self._request("POST", f"/api/researchers/{researcher_id}/skills", json_data=payload)

    def update_researcher_areas(self, researcher_id: int, area_ids: list) -> Dict[str, Any]:
        payload = {"area_ids": area_ids}
        return self._request("POST", f"/api/researchers/{researcher_id}/areas", json_data=payload)

    # --- Papers ---
    def get_papers(
        self,
        year: Optional[int] = None,
        area_id: Optional[int] = None,
        author_id: Optional[int] = None,
        institution_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if year:
            params["year"] = year
        if area_id:
            params["area_id"] = area_id
        if author_id:
            params["author_id"] = author_id
        if institution_id:
            params["institution_id"] = institution_id
        if search:
            params["search"] = search
        return self._request("GET", "/api/papers", params=params)

    def get_paper_detail(self, paper_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/api/papers/{paper_id}")

    def create_paper(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/api/papers", json_data=payload)

    def update_paper(self, paper_id: int, current_researcher_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a paper's metadata. Only authorized authors may update."""
        payload = {"current_researcher_id": current_researcher_id, **updates}
        return self._request("PUT", f"/api/papers/{paper_id}", json_data=payload)

    def delete_paper(self, paper_id: int, current_researcher_id: int) -> Dict[str, Any]:
        """Delete a paper. Only authorized authors may delete."""
        payload = {"current_researcher_id": current_researcher_id}
        return self._request("DELETE", f"/api/papers/{paper_id}", json_data=payload)

    # --- Research Areas ---
    def get_research_areas(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/research-areas")

    def create_research_area(self, name: str, description: Optional[str] = None, icon_name: Optional[str] = "AcademicCap") -> Dict[str, Any]:
        payload = {"name": name, "description": description, "icon_name": icon_name}
        return self._request("POST", "/api/research-areas", json_data=payload)

    # --- Communities ---
    def get_communities(
        self,
        institution_id: Optional[int] = None,
        search: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if institution_id:
            params["institution_id"] = institution_id
        if search:
            params["search"] = search
        uid = user_id or (self.current_user.get("id") if self.current_user else None)
        if uid:
            params["user_id"] = uid
        return self._request("GET", "/api/communities", params=params)

    def get_community_detail(self, community_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        params = {}
        uid = user_id or (self.current_user.get("id") if self.current_user else None)
        if uid:
            params["user_id"] = uid
        return self._request("GET", f"/api/communities/{community_id}", params=params)

    def join_community(self, community_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        uid = user_id or (self.current_user.get("id") if self.current_user else None)
        if not uid:
            raise APIClientError("User authentication is required to join a community.")
        return self._request("POST", f"/api/communities/{community_id}/join", json_data={"user_id": uid})

    def leave_community(self, community_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        uid = user_id or (self.current_user.get("id") if self.current_user else None)
        if not uid:
            raise APIClientError("User authentication is required to leave a community.")
        return self._request("POST", f"/api/communities/{community_id}/leave", json_data={"user_id": uid})

    def get_my_communities(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        uid = user_id or (self.current_user.get("id") if self.current_user else None)
        if not uid:
            return []
        return self._request("GET", "/api/communities/my/joined", params={"user_id": uid})

    # --- Network, Graph, BFS, DFS ---
    def get_network_graph(self) -> Dict[str, Any]:
        return self._request("GET", "/api/network/graph")

    def run_bfs(self, start_id: int, target_id: int) -> Dict[str, Any]:
        return self._request("GET", "/api/network/bfs", params={"start_id": start_id, "target_id": target_id})

    def run_dfs(self, start_id: int, target_id: int, max_depth: int = 4) -> List[Dict[str, Any]]:
        return self._request(
            "GET",
            "/api/network/dfs",
            params={"start_id": start_id, "target_id": target_id, "max_depth": max_depth}
        )

    def get_clusters(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/network/clusters")

    def get_bfs_traversal(self, start_id: int) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/network/bfs-traversal", params={"start_id": start_id})

    def get_dfs_traversal(self, start_id: int) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/network/dfs-traversal", params={"start_id": start_id})

    # --- Recommendations ---
    def get_recommendations(
        self,
        interests: List[str],
        department: Optional[str] = None,
        institution: Optional[str] = None,
        exclude_id: Optional[int] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        payload = {
            "interests": interests,
            "department": department,
            "institution": institution,
            "exclude_id": exclude_id,
            "limit": limit
        }
        return self._request("POST", "/api/recommendations", json_data=payload)

    # --- Global Search ---
    def global_search(self, query: str) -> Dict[str, Any]:
        return self._request("GET", "/api/search", params={"q": query})

    # --- Researcher Connections (Part 5) ---
    def send_connection_request(self, sender_id: int, receiver_id: int) -> Dict[str, Any]:
        payload = {"sender_researcher_id": sender_id, "receiver_researcher_id": receiver_id}
        return self._request("POST", "/api/connections/request", json_data=payload)

    def get_connection_status(self, current_id: int, target_id: int) -> Dict[str, Any]:
        params = {"current_id": current_id, "target_id": target_id}
        return self._request("GET", "/api/connections/status", params=params)

    def get_sent_connection_requests(self, researcher_id: int) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/connections/sent", params={"researcher_id": researcher_id})

    def get_received_connection_requests(self, researcher_id: int, status: Optional[str] = "PENDING") -> List[Dict[str, Any]]:
        params = {"researcher_id": researcher_id}
        if status:
            params["status"] = status
        return self._request("GET", "/api/connections/received", params=params)

    def accept_connection_request(self, request_id: int, current_researcher_id: int) -> Dict[str, Any]:
        payload = {"current_researcher_id": current_researcher_id}
        return self._request("POST", f"/api/connections/{request_id}/accept", json_data=payload)

    def reject_connection_request(self, request_id: int, current_researcher_id: int) -> Dict[str, Any]:
        payload = {"current_researcher_id": current_researcher_id}
        return self._request("POST", f"/api/connections/{request_id}/reject", json_data=payload)

    def cancel_connection_request(self, request_id: int, current_researcher_id: int) -> Dict[str, Any]:
        payload = {"current_researcher_id": current_researcher_id}
        return self._request("POST", f"/api/connections/{request_id}/cancel", json_data=payload)

    def disconnect_researcher(self, connection_id: int, current_researcher_id: int) -> Dict[str, Any]:
        payload = {"current_researcher_id": current_researcher_id}
        return self._request("POST", f"/api/connections/{connection_id}/disconnect", json_data=payload)

    def get_researcher_connections(self, researcher_id: int) -> List[Dict[str, Any]]:
        return self._request("GET", f"/api/connections/researcher/{researcher_id}")

    def get_connection_activity(self, researcher_id: int, limit: int = 25) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/connections/activity", params={"researcher_id": researcher_id, "limit": limit})

    def get_collaboration_suggestions(self, researcher_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """Return researchers suggested for collaboration based on shared areas/skills."""
        return self._request(
            "GET",
            f"/api/connections/suggestions/{researcher_id}",
            params={"limit": limit}
        )

    def get_pending_incoming_count(self, researcher_id: int) -> int:
        """Return count of pending incoming connection requests."""
        try:
            data = self._request("GET", "/api/connections/pending-count", params={"researcher_id": researcher_id})
            return data.get("count", 0)
        except Exception:
            return 0


# Global client instance
api_client = CampusXAPIClient()
