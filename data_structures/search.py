"""
CAMPUSX — Discover People Behind the Work System
Data Structure: Multi-Entity Categorized Search Index
"""

import re
from typing import Any, Dict, List, Optional


class CategorizedSearchEngine:
    """
    In-memory categorized search engine that indexes and ranks matches
    across Researchers, Papers, Research Areas, and Communities.
    """

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [w.lower() for w in re.split(r"\W+", text) if w]

    @staticmethod
    def _calculate_score(query_tokens: List[str], text: str) -> float:
        """Calculate relevance score based on token exact and prefix matches."""
        score = 0.0
        text_lower = text.lower()
        text_tokens = re.split(r"\W+", text_lower)

        for q in query_tokens:
            if q == text_lower:
                score += 10.0
            elif q in text_lower:
                score += 3.0

            for t in text_tokens:
                if t == q:
                    score += 5.0
                elif t.startswith(q):
                    score += 2.0

        return score

    @classmethod
    def search(
        cls,
        query: str,
        researchers: List[Dict[str, Any]],
        papers: List[Dict[str, Any]],
        areas: List[Dict[str, Any]],
        communities: List[Dict[str, Any]],
        limit_per_category: int = 10
    ) -> Dict[str, Any]:
        """
        Execute categorized search across all academic entities.
        Returns:
            {
                "query": query,
                "total_results": N,
                "counts": {"researchers": X, "papers": Y, "areas": Z, "communities": W},
                "results": {
                    "researchers": [...],
                    "papers": [...],
                    "areas": [...],
                    "communities": [...]
                }
            }
        """
        query_clean = query.strip()
        if not query_clean:
            return {
                "query": query,
                "total_results": 0,
                "counts": {"researchers": 0, "papers": 0, "areas": 0, "communities": 0},
                "results": {"researchers": [], "papers": [], "areas": [], "communities": []}
            }

        q_tokens = cls._tokenize(query_clean)

        # 1. Match Researchers
        scored_researchers = []
        for r in researchers:
            searchable = f"{r.get('name', '')} {r.get('designation', '')} {r.get('department_name', '')} {r.get('institution_name', '')} {' '.join(r.get('areas', []))} {r.get('bio', '')}"
            score = cls._calculate_score(q_tokens, searchable)
            if score > 0:
                scored_researchers.append((score, r))
        scored_researchers.sort(key=lambda x: x[0], reverse=True)
        matched_researchers = [item[1] for item in scored_researchers[:limit_per_category]]

        # 2. Match Papers
        scored_papers = []
        for p in papers:
            authors_str = " ".join(a.get("name", "") if isinstance(a, dict) else str(a) for a in p.get("authors", []))
            searchable = f"{p.get('title', '')} {p.get('abstract', '')} {p.get('venue', '')} {p.get('primary_area_name', '')} {authors_str}"
            score = cls._calculate_score(q_tokens, searchable)
            if score > 0:
                scored_papers.append((score, p))
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        matched_papers = [item[1] for item in scored_papers[:limit_per_category]]

        # 3. Match Research Areas
        scored_areas = []
        for a in areas:
            searchable = f"{a.get('name', '')} {a.get('description', '')}"
            score = cls._calculate_score(q_tokens, searchable)
            if score > 0:
                scored_areas.append((score, a))
        scored_areas.sort(key=lambda x: x[0], reverse=True)
        matched_areas = [item[1] for item in scored_areas[:limit_per_category]]

        # 4. Match Communities
        scored_communities = []
        for c in communities:
            searchable = f"{c.get('name', '')} {c.get('description', '')} {c.get('category', '')} {c.get('institution_name', '')}"
            score = cls._calculate_score(q_tokens, searchable)
            if score > 0:
                scored_communities.append((score, c))
        scored_communities.sort(key=lambda x: x[0], reverse=True)
        matched_communities = [item[1] for item in scored_communities[:limit_per_category]]

        total = len(matched_researchers) + len(matched_papers) + len(matched_areas) + len(matched_communities)

        return {
            "query": query,
            "total_results": total,
            "counts": {
                "researchers": len(matched_researchers),
                "papers": len(matched_papers),
                "areas": len(matched_areas),
                "communities": len(matched_communities)
            },
            "results": {
                "researchers": matched_researchers,
                "papers": matched_papers,
                "areas": matched_areas,
                "communities": matched_communities
            }
        }
