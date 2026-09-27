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

    # --- Research Areas ---
    def get_research_areas(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/api/research-areas")

    # --- Communities ---
    def get_communities(
        self,
        institution_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if institution_id:
            params["institution_id"] = institution_id
        if search:
            params["search"] = search
        return self._request("GET", "/api/communities", params=params)

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


# Global client instance
api_client = CampusXAPIClient()
