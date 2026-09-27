"""
CAMPUSX — Discover People Behind the Work System
Data Structure: Recommendation Engine based on Jaccard & Area Overlap Similarity
"""

from typing import Any, Dict, List, Optional, Set


class ResearchRecommendationEngine:
    """
    Computes research interest similarity between a user/query profile
    and campus researchers, producing clear, explainable match justifications.
    """

    # Domain affinity map for related research disciplines
    RELATED_DOMAINS = {
        "Artificial Intelligence": {"Machine Learning", "Data Science", "Natural Language Processing"},
        "Machine Learning": {"Artificial Intelligence", "Data Science", "Computer Networks"},
        "Cybersecurity": {"Computer Networks", "Internet of Things", "Cloud & Distributed Systems"},
        "Data Science": {"Artificial Intelligence", "Machine Learning", "Healthcare & Biomedical Informatics"},
        "Internet of Things": {"Computer Networks", "Cybersecurity", "Cloud & Distributed Systems"},
        "Computer Networks": {"Internet of Things", "Cybersecurity", "Cloud & Distributed Systems"},
        "Software Engineering": {"Cloud & Distributed Systems", "Data Science"},
        "Natural Language Processing": {"Artificial Intelligence", "Data Science"},
        "Cloud & Distributed Systems": {"Software Engineering", "Computer Networks", "Cybersecurity"},
        "Healthcare & Biomedical Informatics": {"Data Science", "Machine Learning", "Artificial Intelligence"}
    }

    @classmethod
    def get_related_areas(cls, areas: Set[str]) -> Set[str]:
        """Expand areas with closely related disciplines."""
        related = set()
        for a in areas:
            if a in cls.RELATED_DOMAINS:
                related.update(cls.RELATED_DOMAINS[a])
        return related

    @classmethod
    def recommend_for_interests(
        cls,
        user_interests: List[str],
        user_department: Optional[str] = None,
        user_institution: Optional[str] = None,
        researchers: List[Dict[str, Any]] = None,
        exclude_id: Optional[int] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Rank researchers based on area overlap, domain affinity, and departmental context.
        Generates an explicit natural-language rationale for each recommendation.
        """
        if not researchers:
            return []

        user_interest_set = {i.strip() for i in user_interests if i.strip()}
        related_user_areas = cls.get_related_areas(user_interest_set)

        scored_candidates = []

        for r in researchers:
            r_id = r.get("id")
            if exclude_id and r_id == exclude_id:
                continue

            r_areas = set(r.get("areas", []))
            if not r_areas and isinstance(r.get("research_areas"), list):
                r_areas = set(r.get("research_areas"))

            # 1. Direct overlap
            direct_overlap = user_interest_set.intersection(r_areas)
            # 2. Indirect related overlap
            indirect_overlap = related_user_areas.intersection(r_areas) - direct_overlap

            # Score calculations
            # Direct matches weighted heavily (3.0 per match)
            # Related matches weighted (1.0 per match)
            # Department bonus (1.5)
            # Institution bonus (0.5)
            direct_score = len(direct_overlap) * 3.0
            indirect_score = len(indirect_overlap) * 1.0

            dept_bonus = 0.0
            same_dept = False
            if user_department and r.get("department_name") == user_department:
                dept_bonus = 1.5
                same_dept = True

            inst_bonus = 0.0
            same_inst = False
            if user_institution and r.get("institution_name") == user_institution:
                inst_bonus = 0.5
                same_inst = True

            # Jaccard index between user interests and researcher areas
            union = user_interest_set.union(r_areas)
            jaccard = (len(direct_overlap) / len(union)) if union else 0.0

            total_score = direct_score + indirect_score + dept_bonus + inst_bonus + (jaccard * 2.0)

            # Skip if zero relevance and not same department
            if total_score <= 0.5 and not direct_overlap:
                continue

            # Generate natural language explanation
            reasons = []
            if direct_overlap:
                overlap_str = " and ".join(sorted(direct_overlap))
                reasons.append(f"your interests directly overlap in {overlap_str}")

            if indirect_overlap and not direct_overlap:
                ind_str = " and ".join(sorted(indirect_overlap))
                reasons.append(f"research in related field of {ind_str}")

            if same_dept:
                reasons.append(f"shared department ({r.get('department_name')})")
            elif same_inst and not direct_overlap:
                reasons.append(f"affiliation at {r.get('institution_name')}")

            if reasons:
                explanation = "Recommended because " + ", plus ".join(reasons) + "."
            else:
                explanation = f"Recommended based on campus research activity in {', '.join(r_areas)}."

            scored_candidates.append({
                "score": round(total_score, 2),
                "jaccard_similarity": round(jaccard, 3),
                "overlapping_areas": list(direct_overlap),
                "related_areas": list(indirect_overlap),
                "explanation": explanation,
                "researcher": r
            })

        # Sort highest score first, then by citations
        scored_candidates.sort(
            key=lambda x: (x["score"], x["researcher"].get("citation_count", 0)),
            reverse=True
        )

        return scored_candidates[:limit]
