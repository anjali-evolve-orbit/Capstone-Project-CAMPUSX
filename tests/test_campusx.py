"""
CAMPUSX — Discover People Behind the Work System
Automated Test Suite: Database, Data Structures, FastAPI Endpoints, and API Client
"""

import sys
import unittest
import uuid
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import db
from data_structures.graph import CollaborationGraph
from data_structures.bfs import find_shortest_collaboration_path, explore_collaboration_rings
from data_structures.dfs import find_all_collaboration_paths, detect_research_clusters
from data_structures.search import CategorizedSearchEngine
from data_structures.recommendation import ResearchRecommendationEngine
from services.ecosystem_service import EcosystemService
from services.auth_service import AuthService
from services.research_service import ResearchService
from services.network_service import NetworkService
from api_client.client import api_client
import main as campusx_main


class TestCampusXDataStructures(unittest.TestCase):
    """Test Suite for Data Structures: Graph ADT, BFS, DFS, Search, and Recommendations."""

    def setUp(self):
        self.graph = CollaborationGraph()
        self.graph.add_node(1, {"id": 1, "name": "Dr. Nilesh Patil", "areas": ["Artificial Intelligence", "Machine Learning"]})
        self.graph.add_node(2, {"id": 2, "name": "Dr. Sneha More", "areas": ["Cybersecurity"]})
        self.graph.add_node(3, {"id": 3, "name": "Dr. Rahul Varma", "areas": ["Machine Learning", "Artificial Intelligence"]})
        self.graph.add_node(4, {"id": 4, "name": "Prof. Anita Deshmukh", "areas": ["Data Science"]})

        self.graph.add_collaboration(1, 3, paper_count=3, description="Federated ML")
        self.graph.add_collaboration(3, 2, paper_count=2, description="Adversarial Defense")
        self.graph.add_collaboration(1, 4, paper_count=1, description="Knowledge Graph")

    def test_graph_properties(self):
        self.assertEqual(self.graph.get_nodes_count(), 4)
        self.assertEqual(self.graph.get_edges_count(), 3)
        self.assertTrue(self.graph.has_edge(1, 3))
        self.assertTrue(self.graph.has_edge(3, 1))  # undirected
        self.assertFalse(self.graph.has_edge(1, 2))  # not direct

    def test_bfs_shortest_path(self):
        # Path 1 -> 2 should be [1, 3, 2] in 2 hops
        result = find_shortest_collaboration_path(self.graph, 1, 2)
        self.assertTrue(result["found"])
        self.assertEqual(result["hops"], 2)
        self.assertEqual(result["path_ids"], [1, 3, 2])
        self.assertIn("Dr. Rahul Varma", result["explanation"])

    def test_bfs_direct_connection(self):
        result = find_shortest_collaboration_path(self.graph, 1, 3)
        self.assertTrue(result["found"])
        self.assertEqual(result["hops"], 1)
        self.assertEqual(result["path_ids"], [1, 3])

    def test_dfs_all_paths(self):
        paths = find_all_collaboration_paths(self.graph, 1, 2, max_depth=3)
        self.assertGreaterEqual(len(paths), 1)
        self.assertEqual(paths[0]["path_ids"], [1, 3, 2])

    def test_dfs_clusters(self):
        clusters = detect_research_clusters(self.graph)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["size"], 4)

    def test_recommendation_algorithm(self):
        researchers = [self.graph.nodes[nid].to_dict() for nid in self.graph.nodes]
        recs = ResearchRecommendationEngine.recommend_for_interests(
            user_interests=["Artificial Intelligence", "Machine Learning"],
            researchers=researchers
        )
        self.assertGreaterEqual(len(recs), 1)
        # Dr. Nilesh Patil and Dr. Rahul Varma both have AI + ML
        top_names = [r["researcher"]["name"] for r in recs[:2]]
        self.assertIn("Dr. Nilesh Patil", top_names)
        self.assertIn("Recommended because", recs[0]["explanation"])

    def test_categorized_search(self):
        researchers = [{"name": "Dr. Nilesh Patil", "areas": ["Artificial Intelligence"]}]
        papers = [{"title": "Scalable Graph Neural Networks", "abstract": "Discovery"}]
        areas = [{"name": "Artificial Intelligence", "description": "AI systems"}]
        communities = [{"name": "AI & Intelligent Systems Lab", "description": "Lab"}]

        res = CategorizedSearchEngine.search("Artificial Intelligence", researchers, papers, areas, communities)
        self.assertGreaterEqual(res["total_results"], 2)
        self.assertIn("researchers", res["results"])
        self.assertIn("areas", res["results"])


class TestCampusXDatabaseAndServices(unittest.TestCase):
    """Test Suite for MySQL Database and Service Layer."""

    def test_mysql_connection(self):
        is_alive, msg = db.test_connection()
        self.assertTrue(is_alive, f"MySQL connection failed: {msg}")

    def test_ecosystem_hierarchy(self):
        campuses = EcosystemService.get_campuses()
        self.assertGreaterEqual(len(campuses), 1)

        institutions = EcosystemService.get_institutions(campuses[0]["id"])
        self.assertGreaterEqual(len(institutions), 3)

        sjcem = next(i for i in institutions if "Engineering" in i["name"])
        departments = EcosystemService.get_departments(sjcem["id"])
        self.assertGreaterEqual(len(departments), 6)

    def test_auth_login(self):
        ok, msg, user = AuthService.login("student@campusx.edu", "CampusX@2026")
        self.assertTrue(ok)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "student@campusx.edu")

    def test_dashboard_stats(self):
        stats = ResearchService.get_dashboard_stats()
        self.assertIn("counts", stats)
        self.assertGreaterEqual(stats["counts"]["researchers"], 10)
        self.assertGreaterEqual(stats["counts"]["papers"], 10)

    def test_network_bfs_service(self):
        # Dr. Nilesh Patil (id=1) -> Dr. Sneha More (id=2)
        res = NetworkService.execute_bfs_path(1, 2)
        self.assertTrue(res["found"])
        self.assertEqual(res["hops"], 2)

    def test_user_researcher_link_is_created_once(self):
        email = f"profile_user_{uuid.uuid4().hex[:8]}@campusx.edu"
        user_id = db.execute_non_query(
            """
            INSERT INTO users (full_name, email, password_hash, role, campus_id, institution_id, department_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            ("Test Researcher", email, "demo_hash", "Student", 1, 1, 1)
        )
        researcher = None
        try:
            researcher = ResearchService.ensure_researcher_for_user(user_id)
            self.assertIsNotNone(researcher)
            self.assertEqual(researcher["user_id"], user_id)
            self.assertEqual(researcher["name"], "Test Researcher")

            duplicate = ResearchService.ensure_researcher_for_user(user_id)
            self.assertEqual(duplicate["id"], researcher["id"])

            count = db.execute_query(
                "SELECT COUNT(*) as c FROM researchers WHERE user_id = %s;",
                (user_id,)
            )[0]["c"]
            self.assertEqual(count, 1)
        finally:
            if researcher and researcher.get("id"):
                db.execute_non_query("DELETE FROM researchers WHERE id = %s;", (researcher["id"],))
            db.execute_non_query("DELETE FROM users WHERE id = %s;", (user_id,))


class TestCampusXAPIClient(unittest.TestCase):
    """Test Suite for FastAPI Endpoints via API Client."""

    def test_api_health(self):
        ok, project = api_client.check_health()
        self.assertTrue(ok)
        self.assertEqual(project, "CAMPUSX")

    def test_api_researchers(self):
        researchers = api_client.get_researchers()
        self.assertGreaterEqual(len(researchers), 10)

    def test_api_papers(self):
        papers = api_client.get_papers()
        self.assertGreaterEqual(len(papers), 10)

    def test_api_network_bfs(self):
        bfs = api_client.run_bfs(1, 2)
        self.assertTrue(bfs.get("found"))
        self.assertEqual(bfs.get("hops"), 2)


class TestCampusXNavigation(unittest.TestCase):
    def test_my_profile_routes_to_profile_view(self):
        class StubProfileView:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            def pack(self, *args, **kwargs):
                return None

        class DummyContentFrame:
            pass

        original_profile_view = campusx_main.ResearcherProfileView
        original_get_researcher_by_user = campusx_main.api_client.get_researcher_by_user
        campusx_main.ResearcherProfileView = StubProfileView
        campusx_main.api_client.get_researcher_by_user = lambda user_id: {"id": 99, "user_id": user_id}

        try:
            app = campusx_main.CampusXApp.__new__(campusx_main.CampusXApp)
            app.app_shell = type(
                "StubShell",
                (),
                {"content_frame": DummyContentFrame(), "set_active_tab": lambda self, tab_id: None}
            )()
            app.active_view = None
            app.current_user = {"id": 42}
            app._clear_content = lambda: None
            app.show_researcher_profile = lambda *args, **kwargs: None
            app.show_paper_details = lambda *args, **kwargs: None
            app._on_select_area = lambda *args, **kwargs: None
            app.navigate_tab("my_profile")
            self.assertIsInstance(app.active_view, StubProfileView)
        finally:
            campusx_main.ResearcherProfileView = original_profile_view
            campusx_main.api_client.get_researcher_by_user = original_get_researcher_by_user


if __name__ == "__main__":
    unittest.main()
