"""
CAMPUSX — Discover People Behind the Work System
FastAPI REST API Server
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import PROJECT_NAME, TAGLINE, APP_VERSION
from services.ecosystem_service import EcosystemService
from services.auth_service import AuthService
from services.research_service import ResearchService
from services.network_service import NetworkService
from database.connection import DatabaseConnectionError

app = FastAPI(
    title=f"{PROJECT_NAME} REST API",
    description=f"{TAGLINE} — Campus Academic Discovery Platform",
    version=APP_VERSION
)

# Enable CORS for desktop clients / local tooling
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Request Schemas ---

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "Student"
    campus_id: Optional[int] = None
    institution_id: Optional[int] = None
    department_id: Optional[int] = None
    custom_institution: Optional[str] = None
    custom_department: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str


class RecommendationRequest(BaseModel):
    interests: List[str]
    department: Optional[str] = None
    institution: Optional[str] = None
    exclude_id: Optional[int] = None
    limit: int = 6


class CommunityActionRequest(BaseModel):
    user_id: int


# --- Routes ---

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "project": PROJECT_NAME,
        "tagline": TAGLINE,
        "version": APP_VERSION,
        "database": "MySQL"
    }


# 1. Auth Endpoints
@app.post("/api/auth/register")
def register_user(req: RegisterRequest):
    try:
        ok, msg, user = AuthService.register(
            full_name=req.full_name,
            email=req.email,
            password=req.password,
            role=req.role,
            campus_id=req.campus_id,
            institution_id=req.institution_id,
            department_id=req.department_id,
            custom_institution=req.custom_institution,
            custom_department=req.custom_department
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg, "user": user}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/auth/login")
def login_user(req: LoginRequest):
    try:
        ok, msg, user = AuthService.login(req.email, req.password)
        if not ok:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)
        return {"success": True, "message": msg, "user": user}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/auth/forgot-password")
def forgot_password_endpoint(req: ForgotPasswordRequest):
    try:
        res = AuthService.request_password_reset(req.email)
        return res
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/api/auth/reset-password")
def reset_password_endpoint(req: ResetPasswordRequest):
    try:
        ok, msg = AuthService.reset_password(
            token=req.token,
            new_password=req.new_password,
            confirm_password=req.confirm_password
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 2. Ecosystem Endpoints
@app.get("/api/ecosystem/campuses")
def get_campuses():
    try:
        return EcosystemService.get_campuses()
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/ecosystem/institutions")
def get_institutions(campus_id: Optional[int] = Query(None)):
    try:
        return EcosystemService.get_institutions(campus_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/ecosystem/departments")
def get_departments(institution_id: Optional[int] = Query(None)):
    try:
        return EcosystemService.get_departments(institution_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 3. Dashboard Stats
@app.get("/api/stats")
def get_dashboard_stats():
    try:
        return ResearchService.get_dashboard_stats()
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 4. Researchers Endpoints
@app.get("/api/researchers")
def list_researchers(
    institution_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    area_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    try:
        return ResearchService.get_researchers(institution_id, department_id, area_id, search)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/researchers/{researcher_id}")
def get_researcher(researcher_id: int):
    try:
        researcher = ResearchService.get_researcher_detail(researcher_id)
        if not researcher:
            raise HTTPException(status_code=404, detail="Researcher not found")
        return researcher
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/researchers/by_user/{user_id}")
def get_researcher_by_user(user_id: int):
    try:
        researcher = ResearchService.get_researcher_by_user(user_id)
        if not researcher:
            raise HTTPException(status_code=404, detail="Researcher not found for user")
        return researcher
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.put("/api/researchers/{researcher_id}")
def update_researcher_profile(researcher_id: int, req: dict):
    try:
        profile = ResearchService.update_researcher_profile(researcher_id, req or {})
        if not profile:
            raise HTTPException(status_code=404, detail="Researcher not found")
        return {"success": True, "researcher": profile}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/skills")
def list_skills(query: Optional[str] = Query(None), limit: int = Query(50)):
    try:
        return ResearchService.get_skills(query, limit)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/researchers/{researcher_id}/skills")
def update_researcher_skills(researcher_id: int, req: dict):
    try:
        skills = req.get("skills") if isinstance(req, dict) else []
        ok = ResearchService.update_researcher_skills(researcher_id, skills or [])
        return {"success": True, "updated": ok}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/researchers/{researcher_id}/areas")
def update_researcher_areas(researcher_id: int, req: dict):
    try:
        area_ids = req.get("area_ids") if isinstance(req, dict) else []
        ok = ResearchService.update_researcher_areas(researcher_id, area_ids or [])
        return {"success": True, "updated": ok}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 5. Papers Endpoints
@app.get("/api/papers")
def list_papers(
    year: Optional[int] = Query(None),
    area_id: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    institution_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    try:
        return ResearchService.get_papers(year, area_id, author_id, institution_id, search)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/papers/{paper_id}")
def get_paper(paper_id: int):
    try:
        paper = ResearchService.get_paper_detail(paper_id)
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        return paper
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


class CreatePaperRequest(BaseModel):
    title: str
    publication_year: int
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    primary_area_id: Optional[int] = None
    research_area_ids: Optional[List[int]] = None
    author_ids: Optional[List[int]] = None


class UpdatePaperRequest(BaseModel):
    current_researcher_id: int
    title: Optional[str] = None
    publication_year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    primary_area_id: Optional[int] = None
    research_area_ids: Optional[List[int]] = None


class DeletePaperRequest(BaseModel):
    current_researcher_id: int


@app.post("/api/papers")
def create_paper(req: CreatePaperRequest):
    try:
        authors = req.author_ids or []
        paper = ResearchService.create_paper(
            title=req.title,
            publication_year=req.publication_year,
            venue=req.venue,
            doi=req.doi,
            abstract=req.abstract,
            primary_area_id=req.primary_area_id,
            author_ids=authors,
            url=req.url,
            research_area_ids=req.research_area_ids or []
        )
        return {"success": True, "paper": paper}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.put("/api/papers/{paper_id}")
def update_paper_endpoint(paper_id: int, req: UpdatePaperRequest):
    """Update a paper. Only authorized authors (paper_authors) may edit."""
    try:
        updates = {
            "title": req.title,
            "publication_year": req.publication_year,
            "venue": req.venue,
            "doi": req.doi,
            "url": req.url,
            "abstract": req.abstract,
            "primary_area_id": req.primary_area_id,
            "research_area_ids": req.research_area_ids,
        }
        # Strip None keys so existing values are preserved
        updates = {k: v for k, v in updates.items() if v is not None}
        ok, msg, paper = ResearchService.update_paper(paper_id, req.current_researcher_id, updates)
        if not ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        return {"success": True, "message": msg, "paper": paper}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.delete("/api/papers/{paper_id}")
def delete_paper_endpoint(paper_id: int, req: DeletePaperRequest):
    """Delete a paper. Only authorized authors (paper_authors) may delete."""
    try:
        ok, msg = ResearchService.delete_paper(paper_id, req.current_researcher_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        return {"success": True, "message": msg}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 6. Research Areas Endpoints
class CreateResearchAreaRequest(BaseModel):
    name: str
    description: Optional[str] = None
    icon_name: Optional[str] = "AcademicCap"


@app.get("/api/research-areas")
def list_research_areas():
    try:
        return ResearchService.get_research_areas()
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/research-areas")
def create_research_area_endpoint(req: CreateResearchAreaRequest):
    try:
        area = ResearchService.create_research_area(
            name=req.name,
            description=req.description,
            icon_name=req.icon_name
        )
        return {"success": True, "area": area}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 7. Communities Endpoints
@app.get("/api/communities")
def list_communities(
    institution_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None)
):
    try:
        return ResearchService.get_communities(institution_id, search, user_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/communities/my/joined")
def list_my_communities(user_id: int = Query(...)):
    try:
        return ResearchService.get_user_communities(user_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/communities/{community_id}")
def get_community_detail(community_id: int, user_id: Optional[int] = Query(None)):
    try:
        detail = ResearchService.get_community_detail(community_id, user_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Community not found")
        return detail
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/communities/{community_id}/join")
def join_community_endpoint(community_id: int, req: CommunityActionRequest):
    try:
        ok, msg, data = ResearchService.join_community(community_id, req.user_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg, "data": data}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/communities/{community_id}/leave")
def leave_community_endpoint(community_id: int, req: CommunityActionRequest):
    try:
        ok, msg, data = ResearchService.leave_community(community_id, req.user_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg, "data": data}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 8. Network & Graph Endpoints (Data Structures: Graph, BFS, DFS)
@app.get("/api/network/graph")
def get_network_graph():
    try:
        return NetworkService.get_network_data()
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/network/bfs")
def run_bfs(start_id: int = Query(...), target_id: int = Query(...)):
    try:
        return NetworkService.execute_bfs_path(start_id, target_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/network/bfs-traversal")
def get_bfs_traversal(start_id: int = Query(...)):
    try:
        return NetworkService.get_bfs_traversal(start_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/network/dfs")
def run_dfs(start_id: int = Query(...), target_id: int = Query(...), max_depth: int = Query(4)):
    try:
        return NetworkService.execute_dfs_paths(start_id, target_id, max_depth)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/network/dfs-traversal")
def get_dfs_traversal(start_id: int = Query(...)):
    try:
        return NetworkService.get_dfs_traversal(start_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/network/clusters")
def get_clusters():
    try:
        return NetworkService.get_research_clusters()
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 9. Recommendation Endpoint
@app.post("/api/recommendations")
def get_recommendations(req: RecommendationRequest):
    try:
        return NetworkService.get_recommendations(
            interests=req.interests,
            department=req.department,
            institution=req.institution,
            exclude_id=req.exclude_id,
            limit=req.limit
        )
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 10. Global Categorized Search Endpoint
@app.get("/api/search")
def search_all(q: str = Query(...)):
    try:
        return NetworkService.global_search(q)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 11. Researcher Connection Endpoints (Part 5)
class SendConnectionRequest(BaseModel):
    sender_researcher_id: int
    receiver_researcher_id: int


class ConnectionActionRequest(BaseModel):
    current_researcher_id: int


@app.post("/api/connections/request")
def send_connection_request_endpoint(req: SendConnectionRequest):
    try:
        ok, msg, data = ResearchService.send_connection_request(
            req.sender_researcher_id,
            req.receiver_researcher_id
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg, "data": data}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/connections/status")
def get_connection_status_endpoint(current_id: int = Query(...), target_id: int = Query(...)):
    try:
        return ResearchService.get_connection_status(current_id, target_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/connections/sent")
def get_sent_requests_endpoint(researcher_id: int = Query(...)):
    try:
        return ResearchService.get_sent_connection_requests(researcher_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/connections/received")
def get_received_requests_endpoint(researcher_id: int = Query(...), status_filter: Optional[str] = Query(None, alias="status")):
    try:
        return ResearchService.get_received_connection_requests(researcher_id, status=status_filter)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/connections/{request_id}/accept")
def accept_connection_request_endpoint(request_id: int, req: ConnectionActionRequest):
    try:
        ok, msg = ResearchService.accept_connection_request(request_id, req.current_researcher_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/connections/{request_id}/reject")
def reject_connection_request_endpoint(request_id: int, req: ConnectionActionRequest):
    try:
        ok, msg = ResearchService.reject_connection_request(request_id, req.current_researcher_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/connections/{request_id}/cancel")
def cancel_connection_request_endpoint(request_id: int, req: ConnectionActionRequest):
    try:
        ok, msg = ResearchService.cancel_connection_request(request_id, req.current_researcher_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.post("/api/connections/{connection_id}/disconnect")
def disconnect_connection_endpoint(connection_id: int, req: ConnectionActionRequest):
    try:
        ok, msg = ResearchService.disconnect_researcher(connection_id, req.current_researcher_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        return {"success": True, "message": msg}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/connections/researcher/{researcher_id}")
def get_researcher_connections_endpoint(researcher_id: int):
    try:
        return ResearchService.get_accepted_connections(researcher_id)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/connections/activity")
def get_connection_activity_endpoint(researcher_id: int = Query(...), limit: int = Query(25)):
    try:
        return ResearchService.get_connection_activity(researcher_id, limit)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/connections/suggestions/{researcher_id}")
def get_collaboration_suggestions_endpoint(researcher_id: int, limit: int = Query(4)):
    """Return suggested researchers to collaborate with, based on shared areas/skills."""
    try:
        return ResearchService.get_collaboration_suggestions(researcher_id, limit)
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


@app.get("/api/connections/pending-count")
def get_pending_incoming_count_endpoint(researcher_id: int = Query(...)):
    """Return the count of pending incoming connection requests for a researcher."""
    try:
        rows = ResearchService.get_received_connection_requests(researcher_id, status="PENDING")
        return {"count": len(rows) if isinstance(rows, list) else 0}
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))
