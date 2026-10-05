"""
CAMPUSX — Discover People Behind the Work System
Research Service: Researchers, Papers, Research Areas, Communities, and Dashboard Stats
"""

from typing import Any, Dict, List, Optional
from database.connection import db


class ResearchService:

    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """Fetch platform summary metrics, highlights, and recent papers."""
        counts = {
            "researchers": db.execute_query("SELECT COUNT(*) as c FROM researchers;")[0]["c"],
            "papers": db.execute_query("SELECT COUNT(*) as c FROM papers;")[0]["c"],
            "areas": db.execute_query("SELECT COUNT(*) as c FROM research_areas;")[0]["c"],
            "communities": db.execute_query("SELECT COUNT(*) as c FROM communities;")[0]["c"]
        }

        # Featured Research Areas with researcher counts
        featured_areas_query = """
            SELECT ra.id, ra.name, ra.description, ra.icon_name,
                   COUNT(DISTINCT rra.researcher_id) as researcher_count,
                   COUNT(DISTINCT pa.paper_id) as paper_count
            FROM research_areas ra
            LEFT JOIN researcher_areas rra ON ra.id = rra.research_area_id
            LEFT JOIN paper_areas pa ON ra.id = pa.research_area_id
            GROUP BY ra.id, ra.name, ra.description, ra.icon_name
            ORDER BY paper_count DESC, researcher_count DESC
            LIMIT 4;
        """
        featured_areas = db.execute_query(featured_areas_query)

        # Recent Papers
        recent_papers_query = """
            SELECT p.id, p.title, p.publication_year, p.venue, p.citation_count,
                   ra.name as primary_area_name
            FROM papers p
            LEFT JOIN research_areas ra ON p.primary_area_id = ra.id
            ORDER BY p.publication_year DESC, p.id DESC
            LIMIT 3;
        """
        recent_papers = db.execute_query(recent_papers_query)
        for paper in recent_papers:
            authors_query = """
                SELECT r.id, r.name FROM researchers r
                JOIN paper_authors pa ON r.id = pa.researcher_id
                WHERE pa.paper_id = %s
                ORDER BY pa.author_order ASC;
            """
            paper["authors"] = db.execute_query(authors_query, (paper["id"],))

        # Researcher Highlights (top by citations)
        highlights_query = """
            SELECT r.id, r.name, r.designation, r.citation_count, r.h_index, r.avatar_color,
                   i.name as institution_name, d.name as department_name
            FROM researchers r
            LEFT JOIN institutions i ON r.institution_id = i.id
            LEFT JOIN departments d ON r.department_id = d.id
            ORDER BY r.citation_count DESC
            LIMIT 3;
        """
        highlights = db.execute_query(highlights_query)

        return {
            "counts": counts,
            "featured_areas": featured_areas,
            "recent_papers": recent_papers,
            "highlights": highlights
        }

    @staticmethod
    def get_researchers(
        institution_id: Optional[int] = None,
        department_id: Optional[int] = None,
        area_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch researchers list with dynamic filtering and research areas."""
        where_clauses = ["1=1"]
        params = []

        if institution_id:
            where_clauses.append("r.institution_id = %s")
            params.append(institution_id)

        if department_id:
            where_clauses.append("r.department_id = %s")
            params.append(department_id)

        if area_id:
            where_clauses.append("EXISTS (SELECT 1 FROM researcher_areas ra WHERE ra.researcher_id = r.id AND ra.research_area_id = %s)")
            params.append(area_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            where_clauses.append("(r.name LIKE %s OR r.designation LIKE %s OR d.name LIKE %s)")
            params.extend([term, term, term])

        query = f"""
            SELECT r.id, r.name, r.designation, r.bio, r.avatar_color,
                   r.citation_count, r.h_index, r.email, r.website,
                   r.institution_id, r.department_id,
                   i.name as institution_name, d.name as department_name,
                   (SELECT COUNT(*) FROM paper_authors pa WHERE pa.researcher_id = r.id) as publication_count
            FROM researchers r
            LEFT JOIN institutions i ON r.institution_id = i.id
            LEFT JOIN departments d ON r.department_id = d.id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY r.citation_count DESC, r.name ASC;
        """
        researchers = db.execute_query(query, tuple(params))

        # Attach areas to each researcher
        for r in researchers:
            areas_query = """
                SELECT ra.id, ra.name FROM research_areas ra
                JOIN researcher_areas rra ON ra.id = rra.research_area_id
                WHERE rra.researcher_id = %s
                ORDER BY ra.name ASC;
            """
            area_rows = db.execute_query(areas_query, (r["id"],))
            r["areas"] = [a["name"] for a in area_rows]
            r["area_ids"] = [a["id"] for a in area_rows]

        return researchers

    @staticmethod
    def ensure_researcher_for_user(
        user_id: int,
        full_name: Optional[str] = None,
        institution_id: Optional[int] = None,
        department_id: Optional[int] = None,
        designation: Optional[str] = None,
        bio: Optional[str] = None,
        email: Optional[str] = None,
        website: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create or reuse the researcher record for a logged-in user."""
        existing = db.execute_query(
            "SELECT id FROM researchers WHERE user_id = %s LIMIT 1;",
            (user_id,)
        )
        if existing:
            return ResearchService.get_researcher_detail(existing[0]["id"])

        # Check by email if user_id was not yet set (e.g. seeded researchers)
        check_email = (email or "").strip().lower()
        if not check_email:
            u_check = db.execute_query("SELECT email FROM users WHERE id = %s LIMIT 1;", (user_id,))
            if u_check:
                check_email = (u_check[0].get("email") or "").strip().lower()

        if check_email:
            existing_email = db.execute_query(
                "SELECT id, user_id FROM researchers WHERE LOWER(email) = LOWER(%s) LIMIT 1;",
                (check_email,)
            )
            if existing_email:
                rid = existing_email[0]["id"]
                if existing_email[0].get("user_id") is None:
                    db.execute_non_query("UPDATE researchers SET user_id = %s WHERE id = %s;", (user_id, rid))
                return ResearchService.get_researcher_detail(rid)

        user = db.execute_query(
            """
            SELECT u.id, u.full_name, u.email, u.role, u.institution_id, u.department_id,
                   u.custom_institution, u.custom_department
            FROM users u
            WHERE u.id = %s LIMIT 1;
            """,
            (user_id,)
        )
        if not user:
            return None
        user_row = user[0]

        name = (full_name or user_row.get("full_name") or "Researcher").strip()
        user_email = email or user_row.get("email")
        inst_id = institution_id if institution_id is not None else user_row.get("institution_id")
        dept_id = department_id if department_id is not None else user_row.get("department_id")
        role = (user_row.get("role") or "Student").strip()
        if role == "Faculty":
            default_designation = "Faculty Researcher"
        elif role == "Researcher":
            default_designation = "Researcher"
        else:
            default_designation = "Student Researcher"
        design = (designation or default_designation).strip() or default_designation
        bio_text = (bio or f"{role} researcher at the campus exploring interdisciplinary academic work.").strip()
        website_url = website or "https://campusx.edu"

        researcher_id = db.execute_non_query(
            """
            INSERT INTO researchers (
                user_id, name, designation, institution_id, department_id,
                bio, avatar_color, citation_count, h_index, email, website
            ) VALUES (%s, %s, %s, %s, %s, %s, '#1E4E8C', 0, 0, %s, %s);
            """,
            (user_id, name, design, inst_id, dept_id, bio_text, user_email, website_url)
        )
        return ResearchService.get_researcher_detail(researcher_id)

    @staticmethod
    def get_researcher_detail(researcher_id: int) -> Optional[Dict[str, Any]]:
        """Fetch complete detailed profile for a single researcher."""
        query = """
            SELECT r.id, r.user_id, r.user_id, r.name, r.designation, r.bio, r.avatar_color,
                   r.citation_count, r.h_index, r.email, r.website,
                   r.institution_id, r.department_id,
                   i.name as institution_name, d.name as department_name
            FROM researchers r
            LEFT JOIN institutions i ON r.institution_id = i.id
            LEFT JOIN departments d ON r.department_id = d.id
            WHERE r.id = %s LIMIT 1;
        """
        rows = db.execute_query(query, (researcher_id,))
        if not rows:
            return None

        researcher = rows[0]

        # Research Areas
        areas_query = """
            SELECT ra.id, ra.name, ra.icon_name FROM research_areas ra
            JOIN researcher_areas rra ON ra.id = rra.research_area_id
            WHERE rra.researcher_id = %s;
        """
        researcher["areas"] = db.execute_query(areas_query, (researcher_id,))
        researcher["area_names"] = [a["name"] for a in researcher["areas"]]

        # Publications
        papers_query = """
            SELECT p.id, p.title, p.abstract, p.publication_year, p.venue,
                   p.citation_count, p.doi, ra.name as primary_area_name
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            LEFT JOIN research_areas ra ON p.primary_area_id = ra.id
            WHERE pa.researcher_id = %s
            ORDER BY p.publication_year DESC;
        """
        papers = db.execute_query(papers_query, (researcher_id,))
        for p in papers:
            auth_query = """
                SELECT r.id, r.name FROM researchers r
                JOIN paper_authors pa ON r.id = pa.researcher_id
                WHERE pa.paper_id = %s ORDER BY pa.author_order ASC;
            """
            p["authors"] = db.execute_query(auth_query, (p["id"],))
        researcher["publications"] = papers

        # Direct Connected Collaborators
        collabs_query = """
            SELECT c.paper_count, c.joint_papers_desc,
                   CASE WHEN c.researcher1_id = %s THEN c.researcher2_id ELSE c.researcher1_id END as collaborator_id,
                   r.name as collaborator_name, r.designation, r.avatar_color,
                   d.name as department_name, i.name as institution_name
            FROM collaborations c
            JOIN researchers r ON (
                r.id = CASE WHEN c.researcher1_id = %s THEN c.researcher2_id ELSE c.researcher1_id END
            )
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN institutions i ON r.institution_id = i.id
            WHERE c.researcher1_id = %s OR c.researcher2_id = %s
            ORDER BY c.paper_count DESC;
        """
        researcher["connected_researchers"] = db.execute_query(
            collabs_query,
            (researcher_id, researcher_id, researcher_id, researcher_id)
        )

        # Skills
        skills_query = """
            SELECT s.id, s.name FROM skills s
            JOIN researcher_skills rs ON s.id = rs.skill_id
            WHERE rs.researcher_id = %s
            ORDER BY s.name ASC;
        """
        researcher["skills"] = db.execute_query(skills_query, (researcher_id,))

        return researcher

    @staticmethod
    def get_researcher_by_user(user_id: int) -> Optional[Dict[str, Any]]:
        """Return the researcher record for a given user_id, creating it if needed."""
        query = """
            SELECT r.id FROM researchers r
            WHERE r.user_id = %s LIMIT 1;
        """
        rows = db.execute_query(query, (user_id,))
        if rows:
            return ResearchService.get_researcher_detail(rows[0]["id"])

        user = db.execute_query(
            "SELECT full_name, email, institution_id, department_id, role FROM users WHERE id = %s LIMIT 1;",
            (user_id,)
        )
        if not user:
            return None
        return ResearchService.ensure_researcher_for_user(
            user_id=user_id,
            full_name=user[0].get("full_name"),
            institution_id=user[0].get("institution_id"),
            department_id=user[0].get("department_id"),
            designation=(user[0].get("role") or "Student Researcher"),
            email=user[0].get("email")
        )

    @staticmethod
    def create_paper(
        title: str,
        publication_year: int,
        venue: Optional[str],
        doi: Optional[str],
        abstract: Optional[str],
        primary_area_id: Optional[int],
        author_ids: list,
        url: Optional[str] = None,
        research_area_ids: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Create a paper, associate authors (paper_authors) and areas (paper_areas).

        Returns the created paper record.
        """
        clean_title = (title or "").strip()
        if not clean_title:
            raise ValueError("Paper title is required.")
        if publication_year is None or not isinstance(publication_year, int):
            raise ValueError("Publication year is required and must be numeric.")

        insert_query = """
            INSERT INTO papers (title, abstract, publication_year, venue, citation_count, doi, pdf_url, primary_area_id)
            VALUES (%s, %s, %s, %s, 0, %s, %s, %s)
        """
        paper_id = db.execute_non_query(insert_query, (clean_title, abstract, publication_year, venue, doi, url, primary_area_id))

        seen_authors = set()
        order = 1
        for aid in author_ids or []:
            if aid in seen_authors:
                continue
            seen_authors.add(aid)
            db.execute_non_query(
                "INSERT INTO paper_authors (paper_id, researcher_id, author_order) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE author_order = VALUES(author_order)",
                (paper_id, aid, order)
            )
            order += 1

        area_ids = []
        if primary_area_id:
            area_ids.append(primary_area_id)
        for area_id in research_area_ids or []:
            if area_id and area_id not in area_ids:
                area_ids.append(area_id)

        for area_id in area_ids:
            db.execute_non_query(
                "INSERT INTO paper_areas (paper_id, research_area_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE research_area_id = research_area_id",
                (paper_id, area_id)
            )

        return ResearchService.get_paper_detail(paper_id)

    @staticmethod
    def get_skills(query: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List skills, optionally filtering by a case-insensitive partial match."""
        params: List[Any] = []
        where_clause = "1=1"
        if query and query.strip():
            term = f"%{query.strip()}%"
            where_clause = "LOWER(name) LIKE LOWER(%s)"
            params.append(term)

        try:
            limit_val = int(getattr(limit, "default", limit))
        except Exception:
            limit_val = 50

        sql = f"SELECT id, name FROM skills WHERE {where_clause} ORDER BY name ASC LIMIT %s;"
        params.append(limit_val)
        return db.execute_query(sql, tuple(params))

    @staticmethod
    def ensure_skill(name: str) -> Optional[int]:
        """Create a skill if it does not already exist, matching case-insensitively."""
        clean = (name or "").strip()
        if not clean:
            return None
        row = db.execute_query(
            "SELECT id FROM skills WHERE LOWER(name) = LOWER(%s) LIMIT 1;",
            (clean,)
        )
        if row:
            return row[0]["id"]
        return db.execute_non_query("INSERT INTO skills (name) VALUES (%s)", (clean,))

    @staticmethod
    def update_researcher_skills(researcher_id: int, skills: list) -> bool:
        """Replace the researcher's skills with the provided list (names), deduplicating case-insensitively."""
        clean = []
        seen = set()
        for s in skills or []:
            if s and isinstance(s, str):
                n = s.strip()
                if n and n.lower() not in seen:
                    seen.add(n.lower())
                    clean.append(n)

        skill_ids = []
        for name in clean:
            sid = ResearchService.ensure_skill(name)
            if sid is not None:
                skill_ids.append(sid)

        db.execute_non_query("DELETE FROM researcher_skills WHERE researcher_id = %s", (researcher_id,))
        for sid in skill_ids:
            db.execute_non_query(
                "INSERT INTO researcher_skills (researcher_id, skill_id) VALUES (%s, %s)",
                (researcher_id, sid)
            )

        return True

    @staticmethod
    def update_researcher_profile(researcher_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update profile fields for the given researcher."""
        row = db.execute_query("SELECT user_id, name, designation, institution_id, department_id, bio, email, website FROM researchers WHERE id = %s LIMIT 1;", (researcher_id,))
        if not row:
            return None

        current = row[0]
        new_name = (updates.get("name") or current["name"]).strip() or current["name"]
        new_designation = (updates.get("designation") or current["designation"]).strip() or current["designation"]
        new_institution_id = updates.get("institution_id", current["institution_id"])
        new_department_id = updates.get("department_id", current["department_id"])
        new_bio = updates.get("bio") if updates.get("bio") is not None else current["bio"]
        new_website = updates.get("website") if updates.get("website") is not None else current["website"]

        db.execute_non_query(
            """
            UPDATE researchers
            SET name = %s,
                designation = %s,
                institution_id = %s,
                department_id = %s,
                bio = %s,
                website = %s
            WHERE id = %s;
            """,
            (new_name, new_designation, new_institution_id, new_department_id, new_bio, new_website, researcher_id)
        )

        user_id = current.get("user_id")
        if user_id:
            db.execute_non_query(
                "UPDATE users SET full_name = %s, institution_id = %s, department_id = %s WHERE id = %s;",
                (new_name, new_institution_id, new_department_id, user_id)
            )

        return ResearchService.get_researcher_detail(researcher_id)

    @staticmethod
    def update_researcher_areas(researcher_id: int, area_ids: list) -> bool:
        """Replace all research area links for a researcher."""
        clean = []
        seen = set()
        for area_id in area_ids or []:
            if area_id is None:
                continue
            try:
                area_id_int = int(area_id)
            except (TypeError, ValueError):
                continue
            if area_id_int not in seen:
                seen.add(area_id_int)
                clean.append(area_id_int)

        db.execute_non_query("DELETE FROM researcher_areas WHERE researcher_id = %s", (researcher_id,))
        for area_id in clean:
            db.execute_non_query(
                "INSERT INTO researcher_areas (researcher_id, research_area_id) VALUES (%s, %s)",
                (researcher_id, area_id)
            )
        return True

    @staticmethod
    def get_papers(
        year: Optional[int] = None,
        area_id: Optional[int] = None,
        author_id: Optional[int] = None,
        institution_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch papers with filtering and authors."""
        where_clauses = ["1=1"]
        params = []

        if year:
            where_clauses.append("p.publication_year = %s")
            params.append(year)

        if area_id:
            where_clauses.append("EXISTS (SELECT 1 FROM paper_areas pa WHERE pa.paper_id = p.id AND pa.research_area_id = %s)")
            params.append(area_id)

        if author_id:
            where_clauses.append("EXISTS (SELECT 1 FROM paper_authors pauth WHERE pauth.paper_id = p.id AND pauth.researcher_id = %s)")
            params.append(author_id)

        if institution_id:
            where_clauses.append("""
                EXISTS (
                    SELECT 1 FROM paper_authors pauth
                    JOIN researchers r ON pauth.researcher_id = r.id
                    WHERE pauth.paper_id = p.id AND r.institution_id = %s
                )
            """)
            params.append(institution_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            where_clauses.append("(p.title LIKE %s OR p.abstract LIKE %s OR p.venue LIKE %s)")
            params.extend([term, term, term])

        query = f"""
            SELECT p.id, p.title, p.abstract, p.publication_year, p.venue,
                   p.citation_count, p.doi, p.pdf_url, p.primary_area_id,
                   ra.name as primary_area_name
            FROM papers p
            LEFT JOIN research_areas ra ON p.primary_area_id = ra.id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY p.publication_year DESC, p.citation_count DESC;
        """
        papers = db.execute_query(query, tuple(params))

        for p in papers:
            auth_query = """
                SELECT r.id, r.name, r.designation, i.name as institution_name
                FROM researchers r
                JOIN paper_authors pa ON r.id = pa.researcher_id
                LEFT JOIN institutions i ON r.institution_id = i.id
                WHERE pa.paper_id = %s ORDER BY pa.author_order ASC;
            """
            p["authors"] = db.execute_query(auth_query, (p["id"],))

        return papers

    @staticmethod
    def get_paper_detail(paper_id: int) -> Optional[Dict[str, Any]]:
        """Fetch complete detailed view for a single academic paper."""
        query = """
            SELECT p.id, p.title, p.abstract, p.publication_year, p.venue,
                   p.citation_count, p.doi, p.pdf_url, p.primary_area_id,
                   ra.name as primary_area_name
            FROM papers p
            LEFT JOIN research_areas ra ON p.primary_area_id = ra.id
            WHERE p.id = %s LIMIT 1;
        """
        rows = db.execute_query(query, (paper_id,))
        if not rows:
            return None
        paper = rows[0]

        # Authors
        auth_query = """
            SELECT r.id, r.name, r.designation, r.avatar_color,
                   d.name as department_name, i.name as institution_name
            FROM researchers r
            JOIN paper_authors pa ON r.id = pa.researcher_id
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN institutions i ON r.institution_id = i.id
            WHERE pa.paper_id = %s ORDER BY pa.author_order ASC;
        """
        paper["authors"] = db.execute_query(auth_query, (paper_id,))

        # Related Areas
        areas_query = """
            SELECT ra.id, ra.name FROM research_areas ra
            JOIN paper_areas pa ON ra.id = pa.research_area_id
            WHERE pa.paper_id = %s;
        """
        paper["areas"] = db.execute_query(areas_query, (paper_id,))

        # Related Papers in same primary research area
        if paper["primary_area_id"]:
            related_papers_query = """
                SELECT p.id, p.title, p.publication_year, p.venue, p.citation_count
                FROM papers p
                WHERE p.primary_area_id = %s AND p.id != %s
                ORDER BY p.citation_count DESC LIMIT 3;
            """
            paper["related_papers"] = db.execute_query(related_papers_query, (paper["primary_area_id"], paper_id))
        else:
            paper["related_papers"] = []

        return paper

    @staticmethod
    def get_research_areas() -> List[Dict[str, Any]]:
        """Fetch all research areas with count metrics."""
        query = """
            SELECT ra.id, ra.name, ra.description, ra.icon_name,
                   COUNT(DISTINCT rra.researcher_id) as researcher_count,
                   COUNT(DISTINCT pa.paper_id) as paper_count
            FROM research_areas ra
            LEFT JOIN researcher_areas rra ON ra.id = rra.research_area_id
            LEFT JOIN paper_areas pa ON ra.id = pa.research_area_id
            GROUP BY ra.id, ra.name, ra.description, ra.icon_name
            ORDER BY ra.name ASC;
        """
        return db.execute_query(query)

    @staticmethod
    def get_communities(
        institution_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch campus communities with member counts."""
        where_clauses = ["1=1"]
        params = []

        if institution_id:
            where_clauses.append("c.institution_id = %s")
            params.append(institution_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            where_clauses.append("(c.name LIKE %s OR c.description LIKE %s OR c.category LIKE %s)")
            params.extend([term, term, term])

        query = f"""
            SELECT c.id, c.name, c.description, c.category, c.member_count,
                   c.institution_id, i.name as institution_name
            FROM communities c
            LEFT JOIN institutions i ON c.institution_id = i.id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY c.member_count DESC, c.name ASC;
        """
        communities = db.execute_query(query, tuple(params))

        # Attach key members
        for c in communities:
            members_query = """
                SELECT r.id, r.name, r.designation, cm.role
                FROM researchers r
                JOIN community_members cm ON r.id = cm.researcher_id
                WHERE cm.community_id = %s
                LIMIT 5;
            """
            c["key_members"] = db.execute_query(members_query, (c["id"],))

        return communities
