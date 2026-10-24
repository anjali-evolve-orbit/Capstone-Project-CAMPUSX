"""
CAMPUSX — Discover People Behind the Work System
Research Service: Researchers, Papers, Research Areas, Communities, and Dashboard Stats
"""

import re
from typing import Any, Dict, List, Optional, Tuple
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
            clean_search = re.sub(r'\s+', ' ', search.strip())
            tokens = [t for t in clean_search.split(' ') if t]
            if tokens:
                token_clauses = []
                for tok in tokens:
                    tok_param = f"%{tok}%"
                    token_clauses.append("(r.name LIKE %s OR r.email LIKE %s OR r.designation LIKE %s OR d.name LIKE %s)")
                    params.extend([tok_param, tok_param, tok_param, tok_param])
                where_clauses.append("(" + " AND ".join(token_clauses) + ")")

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
                   p.citation_count, p.doi, p.pdf_url, p.primary_area_id,
                   ra.name as primary_area_name
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            LEFT JOIN research_areas ra ON p.primary_area_id = ra.id
            WHERE pa.researcher_id = %s
            ORDER BY p.publication_year DESC, p.id DESC;
        """
        papers = db.execute_query(papers_query, (researcher_id,))
        for p in papers:
            auth_query = """
                SELECT r.id, r.name, r.avatar_color, pa.author_order FROM researchers r
                JOIN paper_authors pa ON r.id = pa.researcher_id
                WHERE pa.paper_id = %s ORDER BY pa.author_order ASC;
            """
            p["authors"] = db.execute_query(auth_query, (p["id"],))

            p_areas_query = """
                SELECT ra.id, ra.name FROM research_areas ra
                JOIN paper_areas pa ON ra.id = pa.research_area_id
                WHERE pa.paper_id = %s
                ORDER BY ra.name ASC;
            """
            p_areas = db.execute_query(p_areas_query, (p["id"],))
            p["areas"] = [a["name"] for a in p_areas]
            p["area_ids"] = [a["id"] for a in p_areas]
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
            SELECT s.id, s.name, COALESCE(rs.proficiency_level, 'Intermediate') as proficiency_level
            FROM skills s
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
        """Replace the researcher's skills with the provided list (names or dicts with proficiency), deduplicating case-insensitively."""
        valid_proficiencies = {"Beginner", "Intermediate", "Advanced", "Expert"}
        clean_skills = []
        seen = set()

        for s in skills or []:
            name = ""
            proficiency = "Intermediate"
            if isinstance(s, dict):
                name = str(s.get("name") or "").strip()
                prof_val = str(s.get("proficiency_level") or "").strip().capitalize()
                if prof_val in valid_proficiencies:
                    proficiency = prof_val
            elif isinstance(s, str):
                name = s.strip()

            if name:
                key = name.lower()
                if key not in seen:
                    seen.add(key)
                    clean_skills.append((name, proficiency))

        skill_records = []
        for name, prof in clean_skills:
            sid = ResearchService.ensure_skill(name)
            if sid is not None:
                skill_records.append((sid, prof))

        db.execute_non_query("DELETE FROM researcher_skills WHERE researcher_id = %s", (researcher_id,))
        for sid, prof in skill_records:
            db.execute_non_query(
                "INSERT INTO researcher_skills (researcher_id, skill_id, proficiency_level) VALUES (%s, %s, %s)",
                (researcher_id, sid, prof)
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
                   d.name as department_name, i.name as institution_name,
                   pa.author_order,
                   CASE WHEN pa.author_order = 1 THEN 'lead_author' ELSE 'co_author' END as role
            FROM researchers r
            JOIN paper_authors pa ON r.id = pa.researcher_id
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN institutions i ON r.institution_id = i.id
            WHERE pa.paper_id = %s ORDER BY pa.author_order ASC;
        """
        paper["authors"] = db.execute_query(auth_query, (paper_id,))

        # Related Areas (including primary and additional areas)
        areas_query = """
            SELECT ra.id, ra.name FROM research_areas ra
            JOIN paper_areas pa ON ra.id = pa.research_area_id
            WHERE pa.paper_id = %s
            ORDER BY CASE WHEN ra.id = %s THEN 0 ELSE 1 END, ra.name ASC;
        """
        paper["areas"] = db.execute_query(areas_query, (paper_id, paper.get("primary_area_id")))
        paper["research_areas"] = paper["areas"]

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
    def create_research_area(
        name: str,
        description: Optional[str] = None,
        icon_name: Optional[str] = "AcademicCap"
    ) -> Dict[str, Any]:
        """Create a new research area or return existing one matching case-insensitively."""
        clean_name = (name or "").strip()
        if not clean_name:
            raise ValueError("Research area name is required and cannot be empty.")

        existing = db.execute_query(
            "SELECT id, name, description, icon_name FROM research_areas WHERE LOWER(TRIM(name)) = LOWER(%s) LIMIT 1;",
            (clean_name,)
        )
        if existing:
            return {
                "id": existing[0]["id"],
                "name": existing[0]["name"],
                "description": existing[0].get("description"),
                "icon_name": existing[0].get("icon_name"),
                "is_new": False
            }

        desc = (description or f"Academic research domain focusing on {clean_name}.").strip()
        icon = (icon_name or "AcademicCap").strip()
        new_id = db.execute_non_query(
            "INSERT INTO research_areas (name, description, icon_name) VALUES (%s, %s, %s);",
            (clean_name, desc, icon)
        )
        return {
            "id": new_id,
            "name": clean_name,
            "description": desc,
            "icon_name": icon,
            "is_new": True
        }

    @staticmethod
    def get_communities(
        institution_id: Optional[int] = None,
        search: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch campus communities with dynamic database member counts and user membership status."""
        where_clauses = ["1=1"]
        params = []

        if institution_id:
            where_clauses.append("c.institution_id = %s")
            params.append(institution_id)

        if search and search.strip():
            term = f"%{search.strip()}%"
            where_clauses.append("(c.name LIKE %s OR c.description LIKE %s OR c.category LIKE %s)")
            params.extend([term, term, term])

        # Resolve researcher_id if user_id is provided
        user_researcher_id = None
        if user_id:
            user_res = ResearchService.get_researcher_by_user(user_id)
            if user_res:
                user_researcher_id = user_res["id"]

        query = f"""
            SELECT c.id, c.name, c.description, c.category,
                   (SELECT COUNT(*) FROM community_members cm WHERE cm.community_id = c.id) as member_count,
                   c.institution_id, i.name as institution_name
            FROM communities c
            LEFT JOIN institutions i ON c.institution_id = i.id
            WHERE {" AND ".join(where_clauses)}
            ORDER BY member_count DESC, c.name ASC;
        """
        communities = db.execute_query(query, tuple(params))

        # Check user membership set if user_researcher_id is known
        joined_community_ids = set()
        if user_researcher_id:
            joined_rows = db.execute_query(
                "SELECT community_id FROM community_members WHERE researcher_id = %s;",
                (user_researcher_id,)
            )
            joined_community_ids = {row["community_id"] for row in joined_rows}

        # Attach key members and membership flag
        for c in communities:
            c["is_member"] = (c["id"] in joined_community_ids)
            members_query = """
                SELECT r.id, r.name, r.designation, cm.role
                FROM researchers r
                JOIN community_members cm ON r.id = cm.researcher_id
                WHERE cm.community_id = %s
                ORDER BY
                    CASE
                        WHEN cm.role LIKE '%Lead%' OR cm.role LIKE '%Advisor%' OR cm.role LIKE '%Investigator%' THEN 1
                        WHEN cm.role LIKE '%Senior%' OR cm.role LIKE '%Coordinator%' THEN 2
                        ELSE 3
                    END,
                    cm.id ASC
                LIMIT 5;
            """
            c["key_members"] = db.execute_query(members_query, (c["id"],))

        return communities

    @staticmethod
    def get_community_detail(community_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Fetch comprehensive details for an academic community including leads, members, and research areas."""
        query = """
            SELECT c.id, c.name, c.description, c.category,
                   (SELECT COUNT(*) FROM community_members cm WHERE cm.community_id = c.id) as member_count,
                   c.institution_id, c.created_at, i.name as institution_name
            FROM communities c
            LEFT JOIN institutions i ON c.institution_id = i.id
            WHERE c.id = %s LIMIT 1;
        """
        rows = db.execute_query(query, (community_id,))
        if not rows:
            return None
        comm = rows[0]

        # Check membership status for current user
        user_researcher_id = None
        if user_id:
            user_res = ResearchService.get_researcher_by_user(user_id)
            if user_res:
                user_researcher_id = user_res["id"]

        is_member = False
        user_role = None
        if user_researcher_id:
            mem_row = db.execute_query(
                "SELECT role FROM community_members WHERE community_id = %s AND researcher_id = %s LIMIT 1;",
                (community_id, user_researcher_id)
            )
            if mem_row:
                is_member = True
                user_role = mem_row[0].get("role", "Member")

        comm["is_member"] = is_member
        comm["user_role"] = user_role

        # Fetch all actual members from database
        members_query = """
            SELECT r.id, r.name, r.designation, r.email, r.avatar_color,
                   d.name as department_name, i.name as institution_name,
                   cm.role, cm.joined_at
            FROM community_members cm
            JOIN researchers r ON cm.researcher_id = r.id
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN institutions i ON r.institution_id = i.id
            WHERE cm.community_id = %s
            ORDER BY
                CASE
                    WHEN cm.role LIKE '%Lead%' OR cm.role LIKE '%Advisor%' OR cm.role LIKE '%Investigator%' THEN 1
                    WHEN cm.role LIKE '%Senior%' OR cm.role LIKE '%Coordinator%' THEN 2
                    ELSE 3
                END,
                cm.id ASC;
        """
        all_members = db.execute_query(members_query, (community_id,))
        comm["members"] = all_members

        # Filter faculty leads
        leads = [m for m in all_members if any(
            k in (m.get("role") or "").lower() for k in ["lead", "advisor", "investigator", "coordinator", "head"]
        )]
        if not leads and all_members:
            leads = all_members[:2]
        comm["faculty_leads"] = leads

        # Associated research areas (derived from active member researchers)
        areas_query = """
            SELECT DISTINCT ra.id, ra.name, ra.icon_name
            FROM community_members cm
            JOIN researcher_areas rra ON cm.researcher_id = rra.researcher_id
            JOIN research_areas ra ON rra.research_area_id = ra.id
            WHERE cm.community_id = %s
            ORDER BY ra.name ASC;
        """
        comm["research_areas"] = db.execute_query(areas_query, (community_id,))

        # Announcements & resources status (clean indicators rather than invented data)
        comm["announcements"] = []
        comm["resources"] = []

        return comm

    @staticmethod
    def join_community(community_id: int, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        """Join an academic community for the authenticated user."""
        # 1. Verify community exists
        c_check = db.execute_query("SELECT id, name FROM communities WHERE id = %s;", (community_id,))
        if not c_check:
            return False, "Community not found.", {}

        # 2. Ensure user has a valid researcher profile
        researcher = ResearchService.ensure_researcher_for_user(user_id)
        if not researcher:
            return False, "Could not resolve researcher profile for user.", {}

        researcher_id = researcher["id"]

        # 3. Check for existing membership (prevent duplicate)
        existing = db.execute_query(
            "SELECT id FROM community_members WHERE community_id = %s AND researcher_id = %s;",
            (community_id, researcher_id)
        )
        if existing:
            count = db.execute_query(
                "SELECT COUNT(*) as c FROM community_members WHERE community_id = %s;",
                (community_id,)
            )[0]["c"]
            return False, "You are already a member of this community.", {
                "community_id": community_id,
                "is_member": True,
                "member_count": count
            }

        # 4. Insert membership
        db.execute_non_query(
            "INSERT INTO community_members (community_id, researcher_id, role, joined_at) VALUES (%s, %s, %s, NOW());",
            (community_id, researcher_id, "Member")
        )

        # 5. Synchronize member_count column in communities table
        count = db.execute_query(
            "SELECT COUNT(*) as c FROM community_members WHERE community_id = %s;",
            (community_id,)
        )[0]["c"]
        db.execute_non_query(
            "UPDATE communities SET member_count = %s WHERE id = %s;",
            (count, community_id)
        )

        return True, f"Successfully joined {c_check[0]['name']}!", {
            "community_id": community_id,
            "is_member": True,
            "member_count": count
        }

    @staticmethod
    def leave_community(community_id: int, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        """Leave an academic community for the authenticated user."""
        # 1. Verify community exists
        c_check = db.execute_query("SELECT id, name FROM communities WHERE id = %s;", (community_id,))
        if not c_check:
            return False, "Community not found.", {}

        # 2. Resolve researcher
        researcher = ResearchService.get_researcher_by_user(user_id)
        if not researcher:
            return False, "You are not a member of this community.", {}

        researcher_id = researcher["id"]

        # 3. Check existing membership
        existing = db.execute_query(
            "SELECT id FROM community_members WHERE community_id = %s AND researcher_id = %s;",
            (community_id, researcher_id)
        )
        if not existing:
            count = db.execute_query(
                "SELECT COUNT(*) as c FROM community_members WHERE community_id = %s;",
                (community_id,)
            )[0]["c"]
            return False, "You are not a member of this community.", {
                "community_id": community_id,
                "is_member": False,
                "member_count": count
            }

        # 4. Delete membership
        db.execute_non_query(
            "DELETE FROM community_members WHERE community_id = %s AND researcher_id = %s;",
            (community_id, researcher_id)
        )

        # 5. Synchronize member_count column
        count = db.execute_query(
            "SELECT COUNT(*) as c FROM community_members WHERE community_id = %s;",
            (community_id,)
        )[0]["c"]
        db.execute_non_query(
            "UPDATE communities SET member_count = %s WHERE id = %s;",
            (count, community_id)
        )

        return True, f"Successfully left {c_check[0]['name']}.", {
            "community_id": community_id,
            "is_member": False,
            "member_count": count
        }

    @staticmethod
    def get_user_communities(user_id: int) -> List[Dict[str, Any]]:
        """Fetch all communities joined by the authenticated user."""
        researcher = ResearchService.get_researcher_by_user(user_id)
        if not researcher:
            return []

        researcher_id = researcher["id"]
        query = """
            SELECT c.id, c.name, c.description, c.category,
                   (SELECT COUNT(*) FROM community_members cm2 WHERE cm2.community_id = c.id) as member_count,
                   c.institution_id, i.name as institution_name,
                   cm.role as my_role, cm.joined_at, 1 as is_member
            FROM communities c
            JOIN community_members cm ON c.id = cm.community_id
            LEFT JOIN institutions i ON c.institution_id = i.id
            WHERE cm.researcher_id = %s
            ORDER BY cm.joined_at DESC, c.name ASC;
        """
        communities = db.execute_query(query, (researcher_id,))

        for c in communities:
            members_query = """
                SELECT r.id, r.name, r.designation, cm.role
                FROM researchers r
                JOIN community_members cm ON r.id = cm.researcher_id
                WHERE cm.community_id = %s
                ORDER BY
                    CASE
                        WHEN cm.role LIKE '%Lead%' OR cm.role LIKE '%Advisor%' OR cm.role LIKE '%Investigator%' THEN 1
                        WHEN cm.role LIKE '%Senior%' OR cm.role LIKE '%Coordinator%' THEN 2
                        ELSE 3
                    END,
                    cm.id ASC
                LIMIT 5;
            """
            c["key_members"] = db.execute_query(members_query, (c["id"],))

        return communities

    # -------------------------------------------------------------
    # RESEARCHER CONNECTION SYSTEM (PART 5)
    # -------------------------------------------------------------
    @staticmethod
    def send_connection_request(sender_researcher_id: int, receiver_researcher_id: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Send a connection request from sender to receiver."""
        if sender_researcher_id == receiver_researcher_id:
            return False, "You cannot send a connection request to yourself.", None

        # Verify both researchers exist
        s_row = db.execute_query("SELECT id, name FROM researchers WHERE id = %s LIMIT 1;", (sender_researcher_id,))
        r_row = db.execute_query("SELECT id, name FROM researchers WHERE id = %s LIMIT 1;", (receiver_researcher_id,))
        if not s_row or not r_row:
            return False, "Researcher profile not found.", None

        # Check existing connection or request
        existing = db.execute_query(
            """
            SELECT id, sender_id, receiver_id, status
            FROM researcher_connections
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            LIMIT 1;
            """,
            (sender_researcher_id, receiver_researcher_id, receiver_researcher_id, sender_researcher_id)
        )

        if existing:
            rec = existing[0]
            if rec["status"] == "ACCEPTED":
                return False, f"You are already connected with {r_row[0]['name']}.", rec
            if rec["status"] == "PENDING":
                if rec["sender_id"] == sender_researcher_id:
                    return False, "You already have a pending connection request sent to this researcher.", rec
                else:
                    return False, f"{r_row[0]['name']} has already sent you a connection request. Please check your Received Requests.", rec
            if rec["status"] == "REJECTED":
                # Previous request was rejected. Reset to pending from current sender
                db.execute_non_query(
                    """
                    UPDATE researcher_connections
                    SET sender_id = %s, receiver_id = %s, status = 'PENDING', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                    """,
                    (sender_researcher_id, receiver_researcher_id, rec["id"])
                )
                return True, f"Connection request sent to {r_row[0]['name']}.", {"id": rec["id"], "status": "PENDING"}

        req_id = db.execute_non_query(
            """
            INSERT INTO researcher_connections (sender_id, receiver_id, status)
            VALUES (%s, %s, 'PENDING');
            """,
            (sender_researcher_id, receiver_researcher_id)
        )
        return True, f"Connection request sent to {r_row[0]['name']}.", {"id": req_id, "status": "PENDING"}

    @staticmethod
    def get_connection_status(current_researcher_id: int, target_researcher_id: int) -> Dict[str, Any]:
        """Check connection relationship between current user and target researcher."""
        if current_researcher_id == target_researcher_id:
            return {"status": "SELF"}

        row = db.execute_query(
            """
            SELECT id, sender_id, receiver_id, status, created_at, updated_at
            FROM researcher_connections
            WHERE (sender_id = %s AND receiver_id = %s)
               OR (sender_id = %s AND receiver_id = %s)
            LIMIT 1;
            """,
            (current_researcher_id, target_researcher_id, target_researcher_id, current_researcher_id)
        )
        if not row:
            return {"status": "NONE"}

        r = row[0]
        req_id = r["id"]
        if r["status"] == "ACCEPTED":
            return {"status": "ACCEPTED", "request_id": req_id, "connection_id": req_id}
        if r["status"] == "PENDING":
            if r["sender_id"] == current_researcher_id:
                return {"status": "PENDING_SENT", "request_id": req_id, "connection_id": req_id}
            else:
                return {"status": "PENDING_RECEIVED", "request_id": req_id, "connection_id": req_id}
        return {
            "status": "REJECTED",
            "request_id": req_id,
            "connection_id": req_id,
            "was_sender": (r["sender_id"] == current_researcher_id)
        }

    @staticmethod
    def get_sent_connection_requests(sender_researcher_id: int) -> List[Dict[str, Any]]:
        """Fetch all connection requests sent by the researcher."""
        query = """
            SELECT rc.id, rc.sender_id, rc.receiver_id, rc.status, rc.created_at, rc.updated_at,
                   r.name as receiver_name, r.designation as receiver_designation,
                   r.avatar_color as receiver_avatar_color, r.email as receiver_email,
                   d.name as department_name, i.name as institution_name
            FROM researcher_connections rc
            JOIN researchers r ON rc.receiver_id = r.id
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN institutions i ON r.institution_id = i.id
            WHERE rc.sender_id = %s
            ORDER BY rc.created_at DESC;
        """
        return db.execute_query(query, (sender_researcher_id,))

    @staticmethod
    def get_received_connection_requests(receiver_researcher_id: int, status: Optional[str] = "PENDING") -> List[Dict[str, Any]]:
        """Fetch connection requests received by the researcher (default PENDING)."""
        where_status = "AND rc.status = %s" if status else ""
        params = (receiver_researcher_id, status) if status else (receiver_researcher_id,)
        query = f"""
            SELECT rc.id, rc.sender_id, rc.receiver_id, rc.status, rc.created_at, rc.updated_at,
                   r.name as sender_name, r.designation as sender_designation,
                   r.avatar_color as sender_avatar_color, r.email as sender_email,
                   r.bio as sender_bio,
                   d.name as department_name, i.name as institution_name
            FROM researcher_connections rc
            JOIN researchers r ON rc.sender_id = r.id
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN institutions i ON r.institution_id = i.id
            WHERE rc.receiver_id = %s {where_status}
            ORDER BY rc.created_at DESC;
        """
        rows = db.execute_query(query, params)
        for row in rows:
            sid = row["sender_id"]
            areas = db.execute_query(
                "SELECT ra.name FROM research_areas ra JOIN researcher_areas rra ON ra.id = rra.research_area_id WHERE rra.researcher_id = %s ORDER BY ra.name ASC LIMIT 3;",
                (sid,)
            )
            row["areas"] = [a["name"] for a in areas]
            skills = db.execute_query(
                "SELECT s.name, rs.proficiency_level FROM skills s JOIN researcher_skills rs ON s.id = rs.skill_id WHERE rs.researcher_id = %s ORDER BY s.name ASC LIMIT 3;",
                (sid,)
            )
            row["skills"] = [f"{s['name']}" for s in skills]
        return rows

    @staticmethod
    def accept_connection_request(request_id: int, current_researcher_id: int) -> Tuple[bool, str]:
        """Accept an incoming connection request addressed to current researcher."""
        row = db.execute_query(
            "SELECT id, sender_id, receiver_id, status FROM researcher_connections WHERE id = %s LIMIT 1;",
            (request_id,)
        )
        if not row:
            return False, "Connection request not found."
        rec = row[0]
        if rec["receiver_id"] != current_researcher_id:
            return False, "Unauthorized: you cannot accept a request addressed to another researcher."
        if rec["status"] == "ACCEPTED":
            return True, "Connection request is already accepted."
        if rec["status"] == "REJECTED":
            return False, "Cannot accept a rejected request. Please request a new connection."

        db.execute_non_query(
            "UPDATE researcher_connections SET status = 'ACCEPTED', updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
            (request_id,)
        )
        return True, "Connection request accepted successfully."

    @staticmethod
    def reject_connection_request(request_id: int, current_researcher_id: int) -> Tuple[bool, str]:
        """Reject an incoming connection request addressed to current researcher."""
        row = db.execute_query(
            "SELECT id, sender_id, receiver_id, status FROM researcher_connections WHERE id = %s LIMIT 1;",
            (request_id,)
        )
        if not row:
            return False, "Connection request not found."
        rec = row[0]
        if rec["receiver_id"] != current_researcher_id:
            return False, "Unauthorized: you cannot reject a request addressed to another researcher."
        if rec["status"] == "ACCEPTED":
            return False, "Cannot reject an already accepted connection. Please use Disconnect instead."
        if rec["status"] == "REJECTED":
            return True, "Connection request has already been rejected."

        db.execute_non_query(
            "UPDATE researcher_connections SET status = 'REJECTED', updated_at = CURRENT_TIMESTAMP WHERE id = %s;",
            (request_id,)
        )
        return True, "Connection request rejected."

    @staticmethod
    def cancel_connection_request(request_id: int, current_researcher_id: int) -> Tuple[bool, str]:
        """Cancel a pending connection request previously sent by current researcher."""
        row = db.execute_query(
            "SELECT id, sender_id, receiver_id, status FROM researcher_connections WHERE id = %s LIMIT 1;",
            (request_id,)
        )
        if not row:
            return False, "Connection request not found."
        rec = row[0]
        if rec["sender_id"] != current_researcher_id:
            return False, "Unauthorized: you cannot cancel a request sent by another researcher."
        if rec["status"] != "PENDING":
            return False, "Only pending connection requests can be cancelled."

        db.execute_non_query("DELETE FROM researcher_connections WHERE id = %s;", (request_id,))
        return True, "Connection request cancelled successfully."

    @staticmethod
    def disconnect_researcher(connection_id: int, current_researcher_id: int) -> Tuple[bool, str]:
        """Disconnect an accepted connection between current researcher and peer."""
        row = db.execute_query(
            "SELECT id, sender_id, receiver_id, status FROM researcher_connections WHERE id = %s LIMIT 1;",
            (connection_id,)
        )
        if not row:
            return False, "Connection record not found."
        rec = row[0]
        if current_researcher_id not in (rec["sender_id"], rec["receiver_id"]):
            return False, "Unauthorized: you are not part of this connection."

        db.execute_non_query("DELETE FROM researcher_connections WHERE id = %s;", (connection_id,))
        return True, "Disconnected successfully."

    @staticmethod
    def get_accepted_connections(researcher_id: int) -> List[Dict[str, Any]]:
        """Fetch all accepted connections for the specified researcher with rich metadata."""
        query = """
            SELECT rc.id as connection_id, rc.created_at as connected_since,
                   CASE WHEN rc.sender_id = %s THEN rc.receiver_id ELSE rc.sender_id END as researcher_id,
                   r.name, r.designation, r.avatar_color, r.email, r.bio,
                   d.name as department_name, i.name as institution_name,
                   (SELECT COUNT(*) FROM paper_authors pa WHERE pa.researcher_id = r.id) as publication_count
            FROM researcher_connections rc
            JOIN researchers r ON r.id = CASE WHEN rc.sender_id = %s THEN rc.receiver_id ELSE rc.sender_id END
            LEFT JOIN departments d ON r.department_id = d.id
            LEFT JOIN institutions i ON r.institution_id = i.id
            WHERE (rc.sender_id = %s OR rc.receiver_id = %s)
              AND rc.status = 'ACCEPTED'
            ORDER BY r.name ASC;
        """
        connections = db.execute_query(query, (researcher_id, researcher_id, researcher_id, researcher_id))
        for conn in connections:
            rid = conn["researcher_id"]
            areas = db.execute_query(
                "SELECT ra.name FROM research_areas ra JOIN researcher_areas rra ON ra.id = rra.research_area_id WHERE rra.researcher_id = %s ORDER BY ra.name ASC LIMIT 4;",
                (rid,)
            )
            conn["areas"] = [a["name"] for a in areas]
            skills = db.execute_query(
                "SELECT s.name, rs.proficiency_level FROM skills s JOIN researcher_skills rs ON s.id = rs.skill_id WHERE rs.researcher_id = %s ORDER BY s.name ASC LIMIT 5;",
                (rid,)
            )
            conn["skills"] = [f"{s['name']} ({s['proficiency_level']})" for s in skills]
        return connections

    @staticmethod
    def get_connection_activity(researcher_id: int, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Fetch real database activity feed from accepted connections:
        - Published a new paper
        - Added or updated skills
        - Updated research interests / areas
        Only includes accepted connections, excludes own updates, and sorts chronologically.
        """
        # 1. Find all accepted connection peer IDs
        peer_rows = db.execute_query(
            """
            SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END as peer_id
            FROM researcher_connections
            WHERE (sender_id = %s OR receiver_id = %s)
              AND status = 'ACCEPTED';
            """,
            (researcher_id, researcher_id, researcher_id)
        )
        peer_ids = [p["peer_id"] for p in peer_rows if p.get("peer_id")]
        if not peer_ids:
            return []

        placeholders = ", ".join(["%s"] * len(peer_ids))
        activities: List[Dict[str, Any]] = []

        # 2. Papers published by peers
        papers_query = f"""
            SELECT
                p.id as target_id,
                p.title as title,
                p.created_at,
                p.publication_year,
                p.venue,
                r.id as researcher_id,
                r.name as researcher_name,
                r.avatar_color,
                r.designation as researcher_designation
            FROM papers p
            JOIN paper_authors pa ON p.id = pa.paper_id
            JOIN researchers r ON pa.researcher_id = r.id
            WHERE r.id IN ({placeholders})
              AND r.id != %s
            ORDER BY p.created_at DESC, p.id DESC
            LIMIT %s;
        """
        paper_params = list(peer_ids) + [researcher_id, limit]
        paper_rows = db.execute_query(papers_query, tuple(paper_params))
        for pr in paper_rows:
            activities.append({
                "activity_type": "PAPER",
                "badge_text": "📄 Published Paper",
                "researcher_id": pr["researcher_id"],
                "researcher_name": pr["researcher_name"],
                "researcher_designation": pr.get("researcher_designation", ""),
                "avatar_color": pr.get("avatar_color") or "#1E4E8C",
                "title": pr["title"],
                "description": f"Published '{pr['title']}' in {pr.get('venue') or 'academic venue'} ({pr.get('publication_year', '')})",
                "target_id": pr["target_id"],
                "created_at": pr["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(pr.get("created_at"), "strftime") else str(pr.get("created_at", ""))
            })

        # 3. Skills added by peers
        skills_query = f"""
            SELECT
                s.id as target_id,
                s.name as skill_name,
                rs.proficiency_level,
                rs.created_at,
                r.id as researcher_id,
                r.name as researcher_name,
                r.avatar_color,
                r.designation as researcher_designation
            FROM researcher_skills rs
            JOIN skills s ON rs.skill_id = s.id
            JOIN researchers r ON rs.researcher_id = r.id
            WHERE r.id IN ({placeholders})
              AND r.id != %s
            ORDER BY rs.created_at DESC, rs.id DESC
            LIMIT %s;
        """
        skill_params = list(peer_ids) + [researcher_id, limit]
        skill_rows = db.execute_query(skills_query, tuple(skill_params))
        for sr in skill_rows:
            activities.append({
                "activity_type": "SKILL",
                "badge_text": "💡 Added Skill",
                "researcher_id": sr["researcher_id"],
                "researcher_name": sr["researcher_name"],
                "researcher_designation": sr.get("researcher_designation", ""),
                "avatar_color": sr.get("avatar_color") or "#1E4E8C",
                "title": sr["skill_name"],
                "description": f"Added skill '{sr['skill_name']}' at {sr.get('proficiency_level', 'Intermediate')} level",
                "target_id": sr["target_id"],
                "created_at": sr["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(sr.get("created_at"), "strftime") else str(sr.get("created_at", ""))
            })

        # 4. Research areas added by peers
        areas_query = f"""
            SELECT
                ra.id as target_id,
                ra.name as area_name,
                rra.created_at,
                r.id as researcher_id,
                r.name as researcher_name,
                r.avatar_color,
                r.designation as researcher_designation
            FROM researcher_areas rra
            JOIN research_areas ra ON rra.research_area_id = ra.id
            JOIN researchers r ON rra.researcher_id = r.id
            WHERE r.id IN ({placeholders})
              AND r.id != %s
            ORDER BY rra.created_at DESC, rra.id DESC
            LIMIT %s;
        """
        area_params = list(peer_ids) + [researcher_id, limit]
        area_rows = db.execute_query(areas_query, tuple(area_params))
        for ar in area_rows:
            activities.append({
                "activity_type": "AREA",
                "badge_text": "🔬 Research Area",
                "researcher_id": ar["researcher_id"],
                "researcher_name": ar["researcher_name"],
                "researcher_designation": ar.get("researcher_designation", ""),
                "avatar_color": ar.get("avatar_color") or "#1E4E8C",
                "title": ar["area_name"],
                "description": f"Expanded research interests to include '{ar['area_name']}'",
                "target_id": ar["target_id"],
                "created_at": ar["created_at"].strftime("%Y-%m-%d %H:%M") if hasattr(ar.get("created_at"), "strftime") else str(ar.get("created_at", ""))
            })

        # Sort all activities by created_at DESC
        activities.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
        return activities[:limit]

    # -------------------------------------------------------------
    # PUBLICATION MANAGEMENT (DELETE, UPDATE)
    # -------------------------------------------------------------
    @staticmethod
    def delete_paper(paper_id: int, current_researcher_id: int) -> Tuple[bool, str]:
        """Delete a publication if the current researcher is an authorized author."""
        rows = db.execute_query(
            "SELECT 1 FROM paper_authors WHERE paper_id = %s AND researcher_id = %s LIMIT 1;",
            (paper_id, current_researcher_id)
        )
        if not rows:
            return False, "You are not authorized to delete this publication."

        affected = db.execute_non_query("DELETE FROM papers WHERE id = %s;", (paper_id,))
        if affected > 0:
            return True, "Publication deleted successfully."
        return False, "Failed to delete publication or publication not found."

    @staticmethod
    def update_paper(paper_id: int, current_researcher_id: int, updates: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Update publication metadata if the current researcher is an authorized author."""
        rows = db.execute_query(
            "SELECT 1 FROM paper_authors WHERE paper_id = %s AND researcher_id = %s LIMIT 1;",
            (paper_id, current_researcher_id)
        )
        if not rows:
            return False, "You are not authorized to edit this publication.", None

        title = (updates.get("title") or "").strip()
        if not title:
            return False, "Publication title cannot be empty.", None

        year = updates.get("publication_year")
        try:
            year = int(year)
        except (ValueError, TypeError):
            year = 2024

        venue = (updates.get("venue") or "").strip() or None
        abstract = (updates.get("abstract") or "").strip() or None
        doi = (updates.get("doi") or "").strip() or None
        pdf_url = (updates.get("pdf_url") or updates.get("url") or "").strip() or None
        primary_area_id = updates.get("primary_area_id")
        if primary_area_id is not None:
            try:
                primary_area_id = int(primary_area_id)
            except (ValueError, TypeError):
                primary_area_id = None

        db.execute_non_query(
            """
            UPDATE papers
            SET title = %s, publication_year = %s, venue = %s, abstract = %s,
                doi = %s, pdf_url = %s, primary_area_id = %s
            WHERE id = %s;
            """,
            (title, year, venue, abstract, doi, pdf_url, primary_area_id, paper_id)
        )

        research_area_ids = updates.get("research_area_ids")
        if research_area_ids is not None:
            db.execute_non_query("DELETE FROM paper_areas WHERE paper_id = %s;", (paper_id,))
            clean_area_ids = []
            if primary_area_id:
                clean_area_ids.append(primary_area_id)
            for aid in research_area_ids:
                try:
                    aid_int = int(aid)
                    if aid_int not in clean_area_ids:
                        clean_area_ids.append(aid_int)
                except (ValueError, TypeError):
                    pass
            for aid in clean_area_ids:
                db.execute_non_query(
                    "INSERT IGNORE INTO paper_areas (paper_id, research_area_id) VALUES (%s, %s);",
                    (paper_id, aid)
                )

        author_ids = updates.get("author_ids")
        if author_ids is not None:
            clean_author_ids = []
            if current_researcher_id not in clean_author_ids:
                clean_author_ids.append(current_researcher_id)
            for aid in author_ids:
                try:
                    aid_int = int(aid)
                    if aid_int not in clean_author_ids:
                        clean_author_ids.append(aid_int)
                except (ValueError, TypeError):
                    pass
            db.execute_non_query("DELETE FROM paper_authors WHERE paper_id = %s;", (paper_id,))
            for order, aid in enumerate(clean_author_ids, start=1):
                db.execute_non_query(
                    "INSERT INTO paper_authors (paper_id, researcher_id, author_order) VALUES (%s, %s, %s);",
                    (paper_id, aid, order)
                )

        updated_paper = ResearchService.get_paper_detail(paper_id)
        return True, "Publication updated successfully.", updated_paper

    # -------------------------------------------------------------
    # COLLABORATION SUGGESTIONS
    # -------------------------------------------------------------
    @staticmethod
    def get_collaboration_suggestions(researcher_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Suggest researchers to collaborate with based on shared research areas and skills.
        Strictly excludes:
        - The researcher themselves
        - Already connected researchers (status = 'ACCEPTED')
        - Researchers with pending connection requests (status = 'PENDING')
        """
        # 1. Fetch current researcher's area IDs and skill IDs
        my_areas = db.execute_query(
            "SELECT research_area_id FROM researcher_areas WHERE researcher_id = %s;",
            (researcher_id,)
        )
        my_area_ids = set(r["research_area_id"] for r in my_areas)

        my_skills = db.execute_query(
            "SELECT skill_id FROM researcher_skills WHERE researcher_id = %s;",
            (researcher_id,)
        )
        my_skill_ids = set(r["skill_id"] for r in my_skills)

        # 2. Excluded researcher IDs: self + anyone with connection record (ACCEPTED or PENDING)
        conn_rows = db.execute_query(
            """
            SELECT sender_id, receiver_id FROM researcher_connections
            WHERE (sender_id = %s OR receiver_id = %s)
              AND status IN ('ACCEPTED', 'PENDING');
            """,
            (researcher_id, researcher_id)
        )
        excluded_ids = {researcher_id}
        for cr in conn_rows:
            excluded_ids.add(cr["sender_id"])
            excluded_ids.add(cr["receiver_id"])

        placeholders = ", ".join(["%s"] * len(excluded_ids))
        candidates_query = f"""
            SELECT r.id, r.name, r.designation, r.avatar_color, r.bio,
                   i.name as institution_name, d.name as department_name,
                   (SELECT COUNT(*) FROM paper_authors pa WHERE pa.researcher_id = r.id) as publication_count,
                   (SELECT COUNT(*) FROM researcher_connections rc
                    WHERE (rc.sender_id = r.id OR rc.receiver_id = r.id) AND rc.status = 'ACCEPTED') as total_connections
            FROM researchers r
            LEFT JOIN institutions i ON r.institution_id = i.id
            LEFT JOIN departments d ON r.department_id = d.id
            WHERE r.id NOT IN ({placeholders})
            ORDER BY r.citation_count DESC, publication_count DESC
            LIMIT 50;
        """
        candidates = db.execute_query(candidates_query, tuple(excluded_ids))
        if not candidates:
            return []

        scored = []
        for c in candidates:
            cid = c["id"]
            c_areas = db.execute_query(
                """
                SELECT ra.id, ra.name FROM research_areas ra
                JOIN researcher_areas rra ON ra.id = rra.research_area_id
                WHERE rra.researcher_id = %s;
                """,
                (cid,)
            )
            c_area_dict = {a["id"]: a["name"] for a in c_areas}
            shared_areas = [c_area_dict[aid] for aid in my_area_ids if aid in c_area_dict]

            c_skills = db.execute_query(
                """
                SELECT s.id, s.name FROM skills s
                JOIN researcher_skills rs ON s.id = rs.skill_id
                WHERE rs.researcher_id = %s;
                """,
                (cid,)
            )
            c_skill_dict = {s["id"]: s["name"] for s in c_skills}
            shared_skills = [c_skill_dict[sid] for sid in my_skill_ids if sid in c_skill_dict]

            score = (len(shared_areas) * 2) + len(shared_skills)

            reasons = []
            if shared_areas:
                if len(shared_areas) == 1:
                    reasons.append(f"Shares {shared_areas[0]}")
                else:
                    reasons.append(f"Shares {len(shared_areas)} research areas")
            if shared_skills:
                if len(shared_skills) == 1:
                    reasons.append(f"Skilled in {shared_skills[0]}")
                else:
                    reasons.append(f"Shares {len(shared_skills)} skills")

            match_reason = " • ".join(reasons) if reasons else "Active Academic Network Member"

            c["shared_areas"] = shared_areas
            c["shared_skills"] = shared_skills
            c["areas"] = [a["name"] for a in c_areas]
            c["skills"] = [s["name"] for s in c_skills]
            c["match_score"] = score
            c["match_reason"] = match_reason
            scored.append(c)

        scored.sort(key=lambda x: (x["match_score"], x.get("publication_count", 0), x.get("total_connections", 0)), reverse=True)
        return scored[:limit]
