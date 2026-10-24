"""
CAMPUSX — Automated Tests for Academic Collaboration Network and Communities
Verifies Network Graph, BFS Shortest Path, DFS Traversal, Cluster Detection,
and Community Details, Join/Leave Functionality, Duplicate Prevention, and Member Counts.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database.connection import db
from services.network_service import NetworkService
from services.research_service import ResearchService
from api_client.client import api_client, APIClientError


class TestCollaborationNetwork(unittest.TestCase):
    """Test suite for Academic Collaboration Network (Graph ADT, BFS, DFS, Clusters)."""

    def setUp(self):
        # Refresh graph
        self.graph = NetworkService.build_graph(force_reload=True)

    def test_network_metrics_calculation(self):
        """1. Verify researcher and edge counts are dynamically calculated."""
        net_dict = NetworkService.get_network_data()
        self.assertIn("nodes", net_dict)
        self.assertIn("edges", net_dict)
        self.assertIn("stats", net_dict)

        nodes = net_dict["nodes"]
        edges = net_dict["edges"]
        stats = net_dict["stats"]

        self.assertEqual(stats["total_researchers"], len(nodes))
        self.assertEqual(stats["total_collaborations"], len(edges))
        self.assertGreaterEqual(len(nodes), 12)  # Seeded genuine faculty
        self.assertGreaterEqual(len(edges), 10)

    def test_shortest_path_exists(self):
        """2. Verify BFS finds shortest collaboration path when one exists."""
        # Dr. Nilesh Patil (id=1) -> Dr. Sneha More (id=2)
        res = NetworkService.execute_bfs_path(1, 2)
        self.assertTrue(res["found"])
        self.assertEqual(res["hops"], 2)
        self.assertEqual(res["path_ids"], [1, 3, 2])
        self.assertIn("Dr. Rahul Varma", res["explanation"])

    def test_direct_collaboration(self):
        """3. Verify BFS on direct collaborators returns 1 hop."""
        # Dr. Nilesh Patil (id=1) <-> Dr. Rahul Varma (id=3)
        res = NetworkService.execute_bfs_path(1, 3)
        self.assertTrue(res["found"])
        self.assertEqual(res["hops"], 1)
        self.assertEqual(res["path_ids"], [1, 3])

    def test_no_path_handling(self):
        """4. Verify BFS correctly reports no path when researchers are disconnected."""
        # Demo Student (id=13) is an isolated scholar with no co-authored papers yet
        res = NetworkService.execute_bfs_path(13, 1)
        self.assertFalse(res["found"])
        self.assertEqual(res["hops"], -1)
        self.assertEqual(res["path_ids"], [])
        self.assertIn("No collaboration path found", res["explanation"])

    def test_dfs_traversal(self):
        """5. Verify DFS traversal explores connected scholars in depth-first order."""
        traversal = NetworkService.get_dfs_traversal(1)
        self.assertGreater(len(traversal), 1)
        self.assertEqual(traversal[0]["id"], 1)
        self.assertEqual(traversal[0]["step"], 1)

    def test_cluster_detection(self):
        """6. Verify research cluster detection groups researchers into connected components."""
        clusters = NetworkService.get_research_clusters()
        self.assertIsInstance(clusters, list)
        self.assertGreaterEqual(len(clusters), 1)

        # Main component should contain all connected faculty
        main_cluster = clusters[0]
        self.assertGreaterEqual(main_cluster["size"], 10)
        self.assertIn(1, main_cluster["member_ids"])
        self.assertIn(2, main_cluster["member_ids"])
        self.assertIn(3, main_cluster["member_ids"])


class TestAcademicCommunities(unittest.TestCase):
    """Test suite for Academic & Research Communities (Details, Join, Leave, Counts, Persistence)."""

    @classmethod
    def setUpClass(cls):
        # Demo Student user (id=1)
        cls.test_user_id = 1
        cls.test_community_id = 3  # Smart Campus & IoT Innovation Cluster

        # Ensure researcher profile exists for test user
        cls.researcher = ResearchService.ensure_researcher_for_user(cls.test_user_id)
        assert cls.researcher is not None, "Failed to resolve researcher for test user"
        cls.researcher_id = cls.researcher["id"]

        # Clean any prior membership in test community
        db.execute_non_query(
            "DELETE FROM community_members WHERE community_id = %s AND researcher_id = %s;",
            (cls.test_community_id, cls.researcher_id)
        )
        # Update member_count
        db.execute_non_query(
            "UPDATE communities SET member_count = (SELECT COUNT(*) FROM community_members WHERE community_id = %s) WHERE id = %s;",
            (cls.test_community_id, cls.test_community_id)
        )

    @classmethod
    def tearDownClass(cls):
        # Clean test user membership
        db.execute_non_query(
            "DELETE FROM community_members WHERE community_id = %s AND researcher_id = %s;",
            (cls.test_community_id, cls.researcher_id)
        )
        db.execute_non_query(
            "UPDATE communities SET member_count = (SELECT COUNT(*) FROM community_members WHERE community_id = %s) WHERE id = %s;",
            (cls.test_community_id, cls.test_community_id)
        )

    def test_1_get_community_detail(self):
        """1. Verify opening community details returns real information, leads, and areas."""
        detail = ResearchService.get_community_detail(self.test_community_id, user_id=self.test_user_id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["id"], self.test_community_id)
        self.assertEqual(detail["name"], "Smart Campus & IoT Innovation Cluster")
        self.assertIn("faculty_leads", detail)
        self.assertIn("members", detail)
        self.assertIn("research_areas", detail)
        self.assertFalse(detail["is_member"])  # Not joined yet

    def test_2_join_community(self):
        """2. Verify user can join a community, member count increments, and membership is saved in MySQL."""
        # Initial count
        init_cnt = db.execute_query(
            "SELECT COUNT(*) as c FROM community_members WHERE community_id = %s;",
            (self.test_community_id,)
        )[0]["c"]

        ok, msg, data = ResearchService.join_community(self.test_community_id, self.test_user_id)
        self.assertTrue(ok)
        self.assertTrue(data["is_member"])
        self.assertEqual(data["member_count"], init_cnt + 1)

        # Verify persisted in database
        persisted = db.execute_query(
            "SELECT id, role, joined_at FROM community_members WHERE community_id = %s AND researcher_id = %s;",
            (self.test_community_id, self.researcher_id)
        )
        self.assertEqual(len(persisted), 1)
        self.assertIsNotNone(persisted[0]["joined_at"])

    def test_3_prevent_duplicate_membership(self):
        """3. Verify duplicate membership is prevented."""
        ok, msg, data = ResearchService.join_community(self.test_community_id, self.test_user_id)
        self.assertFalse(ok)
        self.assertIn("already a member", msg.lower())

    def test_4_my_communities_list(self):
        """4. Verify joined community appears in user's 'My Communities' list."""
        my_list = ResearchService.get_user_communities(self.test_user_id)
        my_ids = [c["id"] for c in my_list]
        self.assertIn(self.test_community_id, my_ids)

    def test_5_leave_community(self):
        """5. Verify user can leave a community, member count decrements, and row is removed from MySQL."""
        before_cnt = db.execute_query(
            "SELECT COUNT(*) as c FROM community_members WHERE community_id = %s;",
            (self.test_community_id,)
        )[0]["c"]

        ok, msg, data = ResearchService.leave_community(self.test_community_id, self.test_user_id)
        self.assertTrue(ok)
        self.assertFalse(data["is_member"])
        self.assertEqual(data["member_count"], before_cnt - 1)

        # Verify deleted in database
        check = db.execute_query(
            "SELECT id FROM community_members WHERE community_id = %s AND researcher_id = %s;",
            (self.test_community_id, self.researcher_id)
        )
        self.assertEqual(len(check), 0)

    def test_6_unauthenticated_or_invalid_user(self):
        """6. Verify unauthenticated actions fail gracefully."""
        # Non-existent user
        ok, msg, _ = ResearchService.leave_community(self.test_community_id, 999999)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
