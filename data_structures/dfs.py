"""
CAMPUSX — Discover People Behind the Work System
Data Structure: Depth-First Search (DFS) Algorithms for Academic Networks
"""

from typing import Any, Dict, List, Optional, Set
from data_structures.graph import CollaborationGraph


def find_all_collaboration_paths(
    graph: CollaborationGraph,
    start_id: int,
    target_id: int,
    max_depth: int = 4
) -> List[Dict[str, Any]]:
    """
    Find all distinct collaboration paths between two researchers up to max_depth using DFS.
    Useful for discovering alternative academic connections and interdisciplinary bridges.
    """
    if not graph.has_node(start_id) or not graph.has_node(target_id):
        return []

    discovered_paths: List[Dict[str, Any]] = []

    def dfs(curr_id: int, target_id: int, visited: Set[int], current_path: List[int]):
        if len(current_path) - 1 > max_depth:
            return

        if curr_id == target_id:
            hops = len(current_path) - 1
            path_nodes = [graph.nodes[nid].to_dict() for nid in current_path]
            edges_info = []
            for i in range(hops):
                u = current_path[i]
                v = current_path[i + 1]
                edge = graph.get_edge(u, v)
                edges_info.append({
                    "from_id": u,
                    "from_name": graph.nodes[u].name,
                    "to_id": v,
                    "to_name": graph.nodes[v].name,
                    "paper_count": edge.weight if edge else 1
                })
            discovered_paths.append({
                "hops": hops,
                "path_ids": list(current_path),
                "path_nodes": path_nodes,
                "edges": edges_info,
                "summary": " → ".join(graph.nodes[nid].name for nid in current_path)
            })
            return

        for neighbor_id, _ in graph.get_neighbors(curr_id):
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                current_path.append(neighbor_id)
                dfs(neighbor_id, target_id, visited, current_path)
                current_path.pop()
                visited.remove(neighbor_id)

    visited_set = {start_id}
    dfs(start_id, target_id, visited_set, [start_id])

    # Sort paths by hop count (shorter first)
    discovered_paths.sort(key=lambda p: p["hops"])
    return discovered_paths


def detect_research_clusters(
    graph: CollaborationGraph
) -> List[Dict[str, Any]]:
    """
    Find all connected components (research clusters) across the campus using DFS.
    Returns cluster metrics, lead researchers, and dominant research areas.
    """
    visited: Set[int] = set()
    clusters: List[Dict[str, Any]] = []

    for node_id in graph.nodes:
        if node_id not in visited:
            component_nodes: List[int] = []

            # Standard DFS stack
            stack = [node_id]
            visited.add(node_id)

            while stack:
                curr = stack.pop()
                component_nodes.append(curr)

                for neighbor_id, _ in graph.get_neighbors(curr):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        stack.append(neighbor_id)

            # Analyze cluster composition
            cluster_members = [graph.nodes[nid].to_dict() for nid in component_nodes]
            all_areas: Dict[str, int] = {}
            for nid in component_nodes:
                for area in graph.nodes[nid].areas:
                    all_areas[area] = all_areas.get(area, 0) + 1

            top_areas = sorted(all_areas.items(), key=lambda x: x[1], reverse=True)[:3]

            clusters.append({
                "cluster_id": len(clusters) + 1,
                "size": len(component_nodes),
                "member_ids": component_nodes,
                "members": cluster_members,
                "dominant_areas": [a[0] for a in top_areas],
                "lead_researcher": max(cluster_members, key=lambda m: m["citation_count"])["name"] if cluster_members else ""
            })

    # Sort clusters by size descending
    clusters.sort(key=lambda c: c["size"], reverse=True)
    return clusters


def run_dfs_traversal(
    graph: CollaborationGraph,
    start_id: int
) -> List[Dict[str, Any]]:
    """Return the sequential depth-first traversal of researchers."""
    if not graph.has_node(start_id):
        return []

    traversal_order = []
    visited: Set[int] = set()
    step_counter = [1]

    def dfs(curr_id: int, depth: int):
        visited.add(curr_id)
        node = graph.nodes[curr_id]
        traversal_order.append({
            "step": step_counter[0],
            "id": curr_id,
            "name": node.name,
            "department": node.department,
            "institution": node.institution,
            "depth": depth
        })
        step_counter[0] += 1

        for neighbor_id, _ in sorted(graph.get_neighbors(curr_id), key=lambda x: graph.nodes[x[0]].name):
            if neighbor_id not in visited:
                dfs(neighbor_id, depth + 1)

    dfs(start_id, 0)
    return traversal_order
