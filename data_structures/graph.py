"""
CAMPUSX — Discover People Behind the Work System
Data Structure: Collaboration Graph ADT (Adjacency List)
"""

from typing import Any, Dict, List, Optional, Set, Tuple


class CollaborationNode:
    """Represents a researcher node in the collaboration network."""
    def __init__(self, researcher_id: int, data: Dict[str, Any]):
        self.id = researcher_id
        self.data = data
        self.name = data.get("name", f"Researcher #{researcher_id}")
        self.institution = data.get("institution", "")
        self.department = data.get("department", "")
        self.areas = data.get("areas", [])
        self.citation_count = data.get("citation_count", 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "institution": self.institution,
            "department": self.department,
            "areas": self.areas,
            "citation_count": self.citation_count,
            "avatar_color": self.data.get("avatar_color", "#1E4E8C"),
            "designation": self.data.get("designation", "")
        }


class CollaborationEdge:
    """Represents an academic collaboration edge between two researchers."""
    def __init__(self, u: int, v: int, weight: int = 1, description: str = ""):
        self.u = min(u, v)
        self.v = max(u, v)
        self.weight = weight  # joint paper count
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.u,
            "target": self.v,
            "weight": self.weight,
            "description": self.description
        }


class CollaborationGraph:
    """
    Undirected Weighted Graph representing the academic collaboration network.
    Implemented using an Adjacency List for optimal space and traversal performance.
    """
    def __init__(self):
        self.nodes: Dict[int, CollaborationNode] = {}
        # adjacency list: node_id -> {neighbor_id: CollaborationEdge}
        self.adj: Dict[int, Dict[int, CollaborationEdge]] = {}

    def add_node(self, researcher_id: int, data: Dict[str, Any]) -> CollaborationNode:
        """Add or update a researcher node in the graph."""
        node = CollaborationNode(researcher_id, data)
        self.nodes[researcher_id] = node
        if researcher_id not in self.adj:
            self.adj[researcher_id] = {}
        return node

    def add_collaboration(self, u: int, v: int, paper_count: int = 1, description: str = "") -> Optional[CollaborationEdge]:
        """Add an undirected collaboration edge between two researchers."""
        if u == v:
            return None
        if u not in self.nodes or v not in self.nodes:
            return None

        edge = CollaborationEdge(u, v, paper_count, description)
        self.adj[u][v] = edge
        self.adj[v][u] = edge
        return edge

    def get_neighbors(self, node_id: int) -> List[Tuple[int, CollaborationEdge]]:
        """Return list of (neighbor_id, edge) for a given researcher."""
        if node_id not in self.adj:
            return []
        return list(self.adj[node_id].items())

    def get_degree(self, node_id: int) -> int:
        """Degree of a researcher (number of distinct co-authors)."""
        return len(self.adj.get(node_id, {}))

    def has_node(self, node_id: int) -> bool:
        return node_id in self.nodes

    def has_edge(self, u: int, v: int) -> bool:
        return u in self.adj and v in self.adj[u]

    def get_edge(self, u: int, v: int) -> Optional[CollaborationEdge]:
        return self.adj.get(u, {}).get(v)

    def get_nodes_count(self) -> int:
        return len(self.nodes)

    def get_edges_count(self) -> int:
        total = sum(len(neighbors) for neighbors in self.adj.values())
        return total // 2

    def to_network_dict(self) -> Dict[str, Any]:
        """Convert entire graph to JSON format for visualization."""
        seen_edges = set()
        edges_list = []
        for u, neighbors in self.adj.items():
            for v, edge in neighbors.items():
                pair = (min(u, v), max(u, v))
                if pair not in seen_edges:
                    seen_edges.add(pair)
                    edges_list.append(edge.to_dict())

        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": edges_list,
            "stats": {
                "total_researchers": self.get_nodes_count(),
                "total_collaborations": self.get_edges_count()
            }
        }
