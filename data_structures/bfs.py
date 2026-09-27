"""
CAMPUSX — Discover People Behind the Work System
Data Structure: Breadth-First Search (BFS) Algorithms for Academic Networks
"""

from collections import deque
from typing import Any, Dict, List, Optional, Set
from data_structures.graph import CollaborationGraph


def find_shortest_collaboration_path(
    graph: CollaborationGraph,
    start_id: int,
    target_id: int
) -> Dict[str, Any]:
    """
    Find the shortest academic collaboration path between two researchers using BFS.
    Guarantees the minimum degree-of-separation path.
    """
    if not graph.has_node(start_id) or not graph.has_node(target_id):
        return {
            "found": False,
            "error": "One or both researcher IDs do not exist in the graph.",
            "path_ids": [],
            "path_nodes": [],
            "hops": 0
        }

    if start_id == target_id:
        node = graph.nodes[start_id]
        return {
            "found": True,
            "path_ids": [start_id],
            "path_nodes": [node.to_dict()],
            "hops": 0,
            "edges": [],
            "explanation": f"Self-connection: {node.name} is the same researcher."
        }

    # BFS Queue stores: (current_node_id, [path_ids])
    queue = deque([(start_id, [start_id])])
    visited: Set[int] = {start_id}

    while queue:
        curr_id, path = queue.popleft()

        for neighbor_id, edge in graph.get_neighbors(curr_id):
            if neighbor_id == target_id:
                full_path = path + [target_id]
                hops = len(full_path) - 1

                # Build detailed step-by-step nodes & edge metadata
                path_nodes = [graph.nodes[nid].to_dict() for nid in full_path]
                edges_info = []
                for i in range(hops):
                    u = full_path[i]
                    v = full_path[i + 1]
                    e = graph.get_edge(u, v)
                    edges_info.append({
                        "from_id": u,
                        "from_name": graph.nodes[u].name,
                        "to_id": v,
                        "to_name": graph.nodes[v].name,
                        "paper_count": e.weight if e else 1,
                        "description": e.description if e else ""
                    })

                # Human-readable explanation
                start_name = graph.nodes[start_id].name
                target_name = graph.nodes[target_id].name
                if hops == 1:
                    exp = f"Direct Collaboration: {start_name} and {target_name} have directly co-authored {edges_info[0]['paper_count']} paper(s)."
                elif hops == 2:
                    inter_name = graph.nodes[full_path[1]].name
                    exp = f"2-Hop Connection: {start_name} is connected to {target_name} via mutual collaborator {inter_name}."
                else:
                    middle_names = " → ".join(graph.nodes[nid].name for nid in full_path[1:-1])
                    exp = f"{hops}-Hop Collaboration Chain: {start_name} → {middle_names} → {target_name}."

                return {
                    "found": True,
                    "algorithm": "Breadth-First Search (BFS)",
                    "hops": hops,
                    "degrees_of_separation": hops,
                    "path_ids": full_path,
                    "path_nodes": path_nodes,
                    "edges": edges_info,
                    "explanation": exp
                }

            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append((neighbor_id, path + [neighbor_id]))

    # No connection path exists
    start_name = graph.nodes[start_id].name
    target_name = graph.nodes[target_id].name
    return {
        "found": False,
        "algorithm": "Breadth-First Search (BFS)",
        "hops": -1,
        "path_ids": [],
        "path_nodes": [],
        "edges": [],
        "explanation": f"No collaboration path found between {start_name} and {target_name}. They belong to disconnected research clusters."
    }


def explore_collaboration_rings(
    graph: CollaborationGraph,
    start_id: int,
    max_hops: int = 3
) -> Dict[str, Any]:
    """
    Explore collaboration rings layer-by-layer using BFS.
    Returns researchers categorized as 1st degree (direct), 2nd degree, and 3rd degree.
    """
    if not graph.has_node(start_id):
        return {"rings": {}, "error": "Researcher not found"}

    visited: Set[int] = {start_id}
    current_layer = {start_id}
    rings: Dict[int, List[Dict[str, Any]]] = {}

    for hop in range(1, max_hops + 1):
        next_layer = set()
        ring_members = []
        for curr_id in current_layer:
            for neighbor_id, edge in graph.get_neighbors(curr_id):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    next_layer.add(neighbor_id)
                    ring_members.append({
                        "researcher": graph.nodes[neighbor_id].to_dict(),
                        "connected_via_id": curr_id,
                        "connected_via_name": graph.nodes[curr_id].name,
                        "joint_papers": edge.weight
                    })
        rings[hop] = ring_members
        current_layer = next_layer
        if not current_layer:
            break

    return {
        "start_researcher": graph.nodes[start_id].to_dict(),
        "total_reachable": len(visited) - 1,
        "rings": rings
    }


def run_bfs_traversal(
    graph: CollaborationGraph,
    start_id: int
) -> List[Dict[str, Any]]:
    """Return the sequential order of visited researchers during BFS traversal."""
    if not graph.has_node(start_id):
        return []

    traversal_order = []
    queue = deque([(start_id, 0)])
    visited = {start_id}

    step = 1
    while queue:
        curr_id, depth = queue.popleft()
        node = graph.nodes[curr_id]
        traversal_order.append({
            "step": step,
            "id": curr_id,
            "name": node.name,
            "department": node.department,
            "institution": node.institution,
            "depth": depth
        })
        step += 1

        for neighbor_id, _ in sorted(graph.get_neighbors(curr_id), key=lambda x: graph.nodes[x[0]].name):
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append((neighbor_id, depth + 1))

    return traversal_order
