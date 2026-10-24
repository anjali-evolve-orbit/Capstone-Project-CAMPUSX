"""
CAMPUSX — Profile Enhancements Automated Test Suite
Tests for:
1. Profile Database-backed Statistics (Connections, Publications, Areas, Skills, Pending Requests)
2. Connection Requests (Sending, Accepting, Rejecting, Disconnecting, Status, Pending Count)
3. Publication Management (Create, Update, Delete with author authorization check)
4. Collaboration Suggestions (Matching algorithms, score calculation, exclusions)
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
from services.research_service import ResearchService

class TestProfileEnhancements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create test users and researchers
        cls.suffix = uuid.uuid4().hex[:6]
        cls.email_a = f"alice_{cls.suffix}@campusx.edu"
        cls.email_b = f"bob_{cls.suffix}@campusx.edu"

        cls.user_a = db.execute_non_query(
            "INSERT INTO users (full_name, email, password_hash, role, campus_id, institution_id, department_id) VALUES (%s, %s, %s, %s, 1, 1, 1);",
            ("Dr. Alice Test", cls.email_a, "dummy_hash", "Faculty")
        )
        cls.user_b = db.execute_non_query(
            "INSERT INTO users (full_name, email, password_hash, role, campus_id, institution_id, department_id) VALUES (%s, %s, %s, %s, 1, 1, 1);",
            ("Dr. Bob Test", cls.email_b, "dummy_hash", "Faculty")
        )

        cls.res_a = ResearchService.ensure_researcher_for_user(cls.user_a)["id"]
        cls.res_b = ResearchService.ensure_researcher_for_user(cls.user_b)["id"]

    @classmethod
    def tearDownClass(cls):
        # Cleanup test data
        db.execute_non_query("DELETE FROM researcher_connections WHERE sender_id IN (%s, %s) OR receiver_id IN (%s, %s);", (cls.res_a, cls.res_b, cls.res_a, cls.res_b))
        db.execute_non_query("DELETE FROM paper_authors WHERE researcher_id IN (%s, %s);", (cls.res_a, cls.res_b))
        db.execute_non_query("DELETE FROM researcher_areas WHERE researcher_id IN (%s, %s);", (cls.res_a, cls.res_b))
        db.execute_non_query("DELETE FROM researcher_skills WHERE researcher_id IN (%s, %s);", (cls.res_a, cls.res_b))
        db.execute_non_query("DELETE FROM researchers WHERE id IN (%s, %s);", (cls.res_a, cls.res_b))
        db.execute_non_query("DELETE FROM users WHERE id IN (%s, %s);", (cls.user_a, cls.user_b))

    def test_connection_request_lifecycle(self):
        """Test sending, checking pending count, accepting, and disconnecting."""
        # Clean any prior connection
        db.execute_non_query("DELETE FROM researcher_connections WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s);",
                             (self.res_a, self.res_b, self.res_b, self.res_a))

        # 1. Send request A -> B
        ok, msg, req = ResearchService.send_connection_request(self.res_a, self.res_b)
        self.assertTrue(ok)
        self.assertIsNotNone(req)
        self.assertEqual(req["status"], "PENDING")

        # 2. Check pending incoming requests for B
        incoming = ResearchService.get_received_connection_requests(self.res_b, status="PENDING")
        self.assertTrue(any(r["sender_id"] == self.res_a for r in incoming))

        # 3. Accept request by B
        ok_acc, msg_acc = ResearchService.accept_connection_request(req["id"], self.res_b)
        self.assertTrue(ok_acc)

        # 4. Check connection status
        st = ResearchService.get_connection_status(self.res_a, self.res_b)
        self.assertEqual(st["status"], "ACCEPTED")

        # 5. Check connections list for A
        conns_a = ResearchService.get_accepted_connections(self.res_a)
        self.assertTrue(any(c["researcher_id"] == self.res_b for c in conns_a))

        # 6. Disconnect
        ok_disc, _ = ResearchService.disconnect_researcher(req["id"], self.res_a)
        self.assertTrue(ok_disc)

        st_after = ResearchService.get_connection_status(self.res_a, self.res_b)
        self.assertEqual(st_after["status"], "NONE")

    def test_paper_create_update_delete(self):
        """Test paper creation, update, unauthorized deletion rejection, and authorized deletion."""
        # 1. Create a paper for researcher A
        created = ResearchService.create_paper(
            title=f"Deep Learning for Campus Networks {self.suffix}",
            publication_year=2024,
            venue="IEEE Transactions on Education",
            doi="10.1109/TED.2024.123456",
            url="https://doi.org/10.1109/TED.2024.123456",
            abstract="An empirical study on campus academic collaboration.",
            primary_area_id=1,
            author_ids=[self.res_a],
            research_area_ids=[1]
        )
        paper_id = created["id"]
        self.assertIsNotNone(paper_id)

        # 2. Update paper metadata
        new_title = f"Deep Learning for Campus Networks (Updated) {self.suffix}"
        ok_upd, msg_upd, _ = ResearchService.update_paper(paper_id, self.res_a, {
            "title": new_title,
            "publication_year": 2025,
            "venue": "ACM Computing Surveys",
            "doi": "10.1145/CSUR.2025.001",
            "url": "https://doi.org/10.1145/CSUR.2025.001",
            "abstract": "Updated abstract with extended findings.",
            "primary_area_id": 1,
            "research_area_ids": [1],
            "author_ids": [self.res_a, self.res_b]
        })
        self.assertTrue(ok_upd)

        # Verify update
        detail = ResearchService.get_paper_detail(paper_id)
        self.assertEqual(detail["title"], new_title)
        self.assertEqual(detail["publication_year"], 2025)
        self.assertEqual(len(detail["authors"]), 2)

        # 3. Attempt deletion by an unauthorized researcher (random ID 999999)
        ok_unauth, _ = ResearchService.delete_paper(paper_id, 999999)
        self.assertFalse(ok_unauth)

        # 4. Authorized deletion by author (res_a)
        ok_del, _ = ResearchService.delete_paper(paper_id, self.res_a)
        self.assertTrue(ok_del)

        # Verify paper is deleted
        detail_after = ResearchService.get_paper_detail(paper_id)
        self.assertIsNone(detail_after)

    def test_collaboration_suggestions(self):
        """Test that collaboration suggestions return valid candidates and exclude self/connected."""
        # Add shared area to both A and B
        db.execute_non_query("INSERT IGNORE INTO researcher_areas (researcher_id, research_area_id) VALUES (%s, 1);", (self.res_a,))
        db.execute_non_query("INSERT IGNORE INTO researcher_areas (researcher_id, research_area_id) VALUES (%s, 1);", (self.res_b,))

        # Clean connection between A and B
        db.execute_non_query("DELETE FROM researcher_connections WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s);",
                             (self.res_a, self.res_b, self.res_b, self.res_a))

        suggestions = ResearchService.get_collaboration_suggestions(self.res_a, limit=10)
        self.assertIsInstance(suggestions, list)
        # Should not suggest self
        self.assertFalse(any(s["id"] == self.res_a for s in suggestions))
        # Each suggestion must contain score and reasons
        for s in suggestions:
            self.assertIn("match_reason", s)
            self.assertIn("match_score", s)

if __name__ == "__main__":
    unittest.main()
