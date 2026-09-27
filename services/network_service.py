"""
CAMPUSX — Discover People Behind the Work System
Network Service: Bridges MySQL Collaborations into Graph ADT, BFS, DFS, and Recommendations
"""

from typing import Any, Dict, List, Optional
from database.connection import db
from data_structures.graph import CollaborationGraph
from data_structures.bfs import find_shortest_collaboration_path, explore_collaboration_rings, run_bfs_traversal
from data_structures.dfs import find_all_collaboration_paths, detect_research_clusters, run_dfs_traversal
from data_structures.search import CategorizedSearchEngine
from data_structures.recommendation import ResearchRecommendationEngine
from services.research_service import ResearchService


class NetworkService:
    _cached_graph: Optional[CollaborationGraph] = None

    @classmethod
    def build_graph(cls, force_reload: bool = False) -> CollaborationGraph:
        """Construct CollaborationGraph from MySQL database records."""
        if cls._cached_graph is not None and not force_reload:
            return cls._cached_graph

        graph = CollaborationGraph()

        # 1. Fetch all researchers and attach their areas
        researchers = ResearchService.get_researchers()
        for r in researchers:
            graph.add_node(r["id"], {
                "id": r["id"],
                "name": r["name"],
                "designation": r["designation"],
                "institution": r.get("institution_name", ""),
                "department": r.get("department_name", ""),
                "areas": r.get("areas", []),
                "citation_count": r.get("citation_count", 0),
                "avatar_color": r.get("avatar_color", "#1E4E8C")
            })

        # 2. Fetch all collaborations (edges)
        collab_rows = db.execute_query(
            "SELECT researcher1_id, researcher2_id, paper_count, joint_papers_desc FROM collaborations;"
        )
        for c in collab_rows:
            graph.add_collaboration(
                c["researcher1_id"],
                c["researcher2_id"],
                c["paper_count"],
                c.get("joint_papers_desc", "")
            )

        cls._cached_graph = graph
        return graph

    @classmethod
    def get_network_data(cls) -> Dict[str, Any]:
        """Return serialized graph for canvas/matplotlib rendering."""
        graph = cls.build_graph()
        return graph.to_network_dict()

    @classmethod
    def execute_bfs_path(cls, start_id: int, target_id: int) -> Dict[str, Any]:
        """Execute BFS shortest path finding between two researchers."""
        graph = cls.build_graph()
        return find_shortest_collaboration_path(graph, start_id, target_id)

    @classmethod
    def execute_dfs_paths(cls, start_id: int, target_id: int, max_depth: int = 4) -> List[Dict[str, Any]]:
        """Execute DFS multi-path exploration between two researchers."""
        graph = cls.build_graph()
        return find_all_collaboration_paths(graph, start_id, target_id, max_depth)

    @classmethod
    def get_research_clusters(cls) -> List[Dict[str, Any]]:
        """Identify connected components using DFS."""
        graph = cls.build_graph()
        return detect_research_clusters(graph)

    @classmethod
    def get_bfs_traversal(cls, start_id: int) -> List[Dict[str, Any]]:
        graph = cls.build_graph()
        return run_bfs_traversal(graph, start_id)

    @classmethod
    def get_dfs_traversal(cls, start_id: int) -> List[Dict[str, Any]]:
        graph = cls.build_graph()
        return run_dfs_traversal(graph, start_id)

    @classmethod
    def get_recommendations(
        cls,
        interests: List[str],
        department: Optional[str] = None,
        institution: Optional[str] = None,
        exclude_id: Optional[int] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """Recommend researchers matching given interests using overlap algorithm."""
        all_researchers = ResearchService.get_researchers()
        return ResearchRecommendationEngine.recommend_for_interests(
            user_interests=interests,
            user_department=department,
            user_institution=institution,
            researchers=all_researchers,
            exclude_id=exclude_id,
            limit=limit
        )

    @classmethod
    def global_search(cls, query: str) -> Dict[str, Any]:
        """Perform categorized search across Researchers, Papers, Areas, and Communities."""
        researchers = ResearchService.get_researchers()
        papers = ResearchService.get_papers()
        areas = ResearchService.get_research_areas()
        communities = ResearchService.get_communities()
        return CategorizedSearchEngine.search(query, researchers, papers, areas, communities)
