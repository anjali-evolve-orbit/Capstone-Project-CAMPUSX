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


class RecommendationRequest(BaseModel):
    interests: List[str]
    department: Optional[str] = None
    institution: Optional[str] = None
    exclude_id: Optional[int] = None
    limit: int = 6


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


# 6. Research Areas Endpoints
@app.get("/api/research-areas")
def list_research_areas():
    try:
        return ResearchService.get_research_areas()
    except DatabaseConnectionError as err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(err))


# 7. Communities Endpoints
@app.get("/api/communities")
def list_communities(
    institution_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    try:
        return ResearchService.get_communities(institution_id, search)
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


@app.get("/api/network/dfs")
def run_dfs(start_id: int = Query(...), target_id: int = Query(...), max_depth: int = Query(4)):
    try:
        return NetworkService.execute_dfs_paths(start_id, target_id, max_depth)
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
