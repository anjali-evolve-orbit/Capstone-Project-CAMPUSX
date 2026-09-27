"""
CAMPUSX — Discover People Behind the Work System
Network View: Researcher Collaboration Graph, Interactive BFS, DFS, and Path Finding
"""

import math
import customtkinter as ctk
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from api_client.client import api_client
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge
)


class NetworkView(ctk.CTkFrame):
    """Interactive collaboration graph with readable layout and clear empty states."""

    def __init__(self, parent, current_user: Optional[Dict[str, Any]] = None, on_select_researcher: Optional[Callable[[int], None]] = None):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.current_user = current_user or {}
        self.on_select_researcher = on_select_researcher or (lambda _id: None)

        self.graph_data: Dict[str, Any] = {"nodes": [], "edges": []}
        self.node_positions: Dict[int, Tuple[float, float]] = {}
        self.highlighted_nodes: Set[int] = set()
        self.highlighted_edges: Set[Tuple[int, int]] = set()
        self.current_researcher_id = None

        self._load_network()
        self._resolve_current_researcher()
        self._build_header()
        self._build_layout()
        self._calculate_node_layout()
        self._draw_graph()

    def _resolve_current_researcher(self):
        user_id = self.current_user.get("id")
        if not user_id:
            return
        try:
            profile = api_client.get_researcher_by_user(int(user_id))
            self.current_researcher_id = profile.get("id")
        except Exception:
            self.current_researcher_id = None

    def _load_network(self):
        try:
            self.graph_data = api_client.get_network_graph()
        except Exception:
            self.graph_data = {"nodes": [], "edges": []}

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(15, 8))

        title = ctk.CTkLabel(head, text="Academic Collaboration Network", font=Theme.FONT_TITLE, text_color=Theme.NAVY)
        title.pack(side="left")

        stats = self.graph_data.get("stats", {})
        n_count = stats.get("total_researchers", len(self.graph_data.get("nodes", [])))
        e_count = stats.get("total_collaborations", len(self.graph_data.get("edges", [])))

        badge = create_badge(
            head,
            text=f"Graph: {n_count} Researcher Nodes · {e_count} Collaboration Edges",
            bg_color="#EBF4FF",
            text_color=Theme.ACADEMIC_BLUE
        )
        badge.pack(side="left", padx=12)

        legend = create_badge(
            head,
            text="Legend: current researcher highlighted · collaboration path in purple",
            bg_color="#F3F0FF",
            text_color=Theme.PURPLE
        )
        legend.pack(side="right")

    def _build_layout(self):
        """Split screen: Left canvas for visual network, right panel for BFS/DFS controls & explanations."""
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)

        # 1. Left Canvas Card
        canvas_card = create_card(container)
        canvas_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        c_header = ctk.CTkFrame(canvas_card, fg_color="transparent")
        c_header.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(c_header, text="Network Topology (Adjacency List Graph)", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(side="left")

        legend_box = ctk.CTkFrame(c_header, fg_color="transparent")
        legend_box.pack(side="right")
        create_badge(legend_box, text="● Standard Node", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=2)
        create_badge(legend_box, text="● Highlighted Path", bg_color="#CFFAFE", text_color="#0891B2").pack(side="left", padx=2)

        self.canvas = ctk.CTkCanvas(
            canvas_card,
            bg=Theme.WHITE,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.canvas.bind("<Configure>", lambda e: self._on_canvas_resize())

        if not self.graph_data.get("nodes"):
            empty = ctk.CTkFrame(canvas_card, fg_color="transparent")
            empty.pack(fill="both", expand=True, padx=20, pady=40)
            ctk.CTkLabel(empty, text="No collaboration network is available yet.", font=Theme.FONT_SUBTITLE, text_color=Theme.SECONDARY_TEXT).pack(pady=(20, 8))
            ctk.CTkLabel(empty, text="Once researchers are linked by papers or collaboration records, the graph will appear here.", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT, wraplength=420, justify="center").pack()

        # 2. Right Controls & Explanation Panel
        control_card = create_card(container)
        control_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.control_scroll = ctk.CTkScrollableFrame(control_card, fg_color="transparent")
        self.control_scroll.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            self.control_scroll,
            text="Data Structure Graph Algorithms",
            font=Theme.FONT_SUBTITLE,
            text_color=Theme.NAVY
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            self.control_scroll,
            text="Execute genuine BFS and DFS traversals to discover shortest collaboration chains and academic clusters:",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT,
            wraplength=320,
            justify="left"
        ).pack(anchor="w", pady=(0, 14))

        # Dropdowns for Researcher A and Researcher B
        nodes = self.graph_data.get("nodes", [])
        self.name_to_id = {n["name"]: n["id"] for n in nodes}
        researcher_names = sorted(list(self.name_to_id.keys())) if self.name_to_id else ["No researchers"]

        # Source Researcher
        ctk.CTkLabel(self.control_scroll, text="Researcher A (Source)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.src_var = ctk.StringVar(value=researcher_names[0] if researcher_names else "")
        self.src_menu = ctk.CTkOptionMenu(
            self.control_scroll,
            variable=self.src_var,
            values=researcher_names,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE
        )
        self.src_menu.pack(fill="x", pady=(0, 10))

        # Target Researcher
        ctk.CTkLabel(self.control_scroll, text="Researcher B (Target)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        second_name = researcher_names[1] if len(researcher_names) > 1 else researcher_names[0]
        self.tgt_var = ctk.StringVar(value=second_name)
        self.tgt_menu = ctk.CTkOptionMenu(
            self.control_scroll,
            variable=self.tgt_var,
            values=researcher_names,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE
        )
        self.tgt_menu.pack(fill="x", pady=(0, 14))

        # Algorithm Action Buttons
        btn_box = ctk.CTkFrame(self.control_scroll, fg_color="transparent")
        btn_box.pack(fill="x", pady=(0, 12))

        # Primary BFS Button
        bfs_btn = create_primary_button(
            btn_box,
            text="⚡ Run BFS (Find Shortest Path)",
            command=self._run_bfs,
            height=36
        )
        bfs_btn.configure(fg_color=Theme.PURPLE, hover_color="#5849BE")
        bfs_btn.pack(fill="x", pady=3)

        # Secondary DFS Button
        dfs_btn = create_secondary_button(
            btn_box,
            text="🔍 Run DFS (Explore Alternative Routes)",
            command=self._run_dfs,
            height=36
        )
        dfs_btn.pack(fill="x", pady=3)

        # Clusters Button
        cluster_btn = create_secondary_button(
            btn_box,
            text="🌐 Detect Research Clusters (DFS)",
            command=self._run_clusters,
            height=34
        )
        cluster_btn.pack(fill="x", pady=3)

        # Reset Button
        reset_btn = ctk.CTkButton(
            btn_box,
            text="Reset Highlights",
            command=self._reset_highlight,
            fg_color="transparent",
            hover_color=Theme.MUTED_BG,
            text_color=Theme.SECONDARY_TEXT,
            font=Theme.FONT_CAPTION,
            height=26
        )
        reset_btn.pack(fill="x", pady=2)

        # Output / Results Card
        self.output_card = create_card(self.control_scroll, fg_color=Theme.SOFT_BG)
        self.output_card.pack(fill="x", pady=(10, 0))

        self.output_inner = ctk.CTkFrame(self.output_card, fg_color="transparent")
        self.output_inner.pack(fill="both", expand=True, padx=14, pady=12)

        self.output_title = ctk.CTkLabel(
            self.output_inner,
            text="Algorithm Output & Explanation",
            font=Theme.FONT_BODY_BOLD,
            text_color=Theme.NAVY
        )
        self.output_title.pack(anchor="w", pady=(0, 4))

        self.output_text = ctk.CTkLabel(
            self.output_inner,
            text="Select two researchers above and click 'Run BFS' to discover the shortest collaboration chain.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT,
            wraplength=310,
            justify="left"
        )
        self.output_text.pack(anchor="w")

    def _calculate_node_layout(self):
        """Distribute nodes in a clean circular / force layout across canvas dimensions."""
        nodes = self.graph_data.get("nodes", [])
        if not nodes:
            return

        w = self.canvas.winfo_width() or 600
        h = self.canvas.winfo_height() or 480

        center_x = w / 2.0
        center_y = h / 2.0
        radius = min(w, h) * 0.38

        num_nodes = len(nodes)
        self.node_positions.clear()

        for idx, node in enumerate(nodes):
            angle = 2 * math.pi * idx / num_nodes
            # Minor radial jitter to prevent rigid overlap
            r = radius if (idx % 2 == 0) else radius * 0.88
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            self.node_positions[node["id"]] = (x, y)

    def _on_canvas_resize(self):
        self._calculate_node_layout()
        self._draw_graph()

    def _draw_graph(self):
        """Render all edges, nodes, badges, and highlighted traversal paths on canvas."""
        self.canvas.delete("all")
        nodes = self.graph_data.get("nodes", [])
        edges = self.graph_data.get("edges", [])

        if not nodes or not self.node_positions:
            return

        if not nodes:
            self.canvas.create_text(
                (self.canvas.winfo_width() or 500) / 2,
                (self.canvas.winfo_height() or 300) / 2,
                text="Graph unavailable",
                fill=Theme.SECONDARY_TEXT,
                font=(Theme.FONT_FAMILY, 12, "bold")
            )
            return

        for edge in edges:
            u, v = edge["source"], edge["target"]
            if u in self.node_positions and v in self.node_positions:
                x1, y1 = self.node_positions[u]
                x2, y2 = self.node_positions[v]

                pair = (min(u, v), max(u, v))
                is_highlighted = pair in self.highlighted_edges

                if is_highlighted:
                    line_color = Theme.PURPLE
                    line_width = 4
                else:
                    line_color = "#CBD5E1"
                    line_width = max(1, min(edge.get("weight", 1), 3))

                self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=line_width, capstyle="round")

        node_radius = 16
        for node in nodes:
            nid = node["id"]
            if nid not in self.node_positions:
                continue

            x, y = self.node_positions[nid]
            is_highlighted = nid in self.highlighted_nodes

            if self.current_researcher_id == nid:
                self.canvas.create_oval(
                    x - node_radius - 7, y - node_radius - 7,
                    x + node_radius + 7, y + node_radius + 7,
                    fill="#DCFCE7",
                    outline="#16A34A",
                    width=2
                )

            if is_highlighted:
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#CFFAFE",
                    outline=Theme.CYAN,
                    width=2
                )
                fill_col = Theme.PURPLE
                outline_col = Theme.NAVY
            else:
                fill_col = node.get("avatar_color", Theme.ACADEMIC_BLUE)
                outline_col = Theme.WHITE

            # Node circle
            self.canvas.create_oval(
                x - node_radius, y - node_radius,
                x + node_radius, y + node_radius,
                fill=fill_col,
                outline=outline_col,
                width=2
            )

            # Node Label (Researcher initials inside, last name below)
            initials = "".join([w[0] for w in node["name"].split() if w])[:2]
            self.canvas.create_text(
                x, y,
                text=initials,
                fill=Theme.WHITE,
                font=(Theme.FONT_FAMILY, 9, "bold")
            )

            # Name snippet under node
            last_name = node["name"].split()[-1]
            text_color = Theme.PURPLE if is_highlighted else Theme.DARK_TEXT
            self.canvas.create_text(
                x, y + node_radius + 12,
                text=last_name,
                fill=text_color,
                font=(Theme.FONT_FAMILY, 8, "bold" if is_highlighted else "normal")
            )

    def _run_bfs(self):
        """Execute BFS shortest path and highlight visually."""
        src_name = self.src_var.get()
        tgt_name = self.tgt_var.get()
        src_id = self.name_to_id.get(src_name)
        tgt_id = self.name_to_id.get(tgt_name)

        if not src_id or not tgt_id:
            self.output_text.configure(text="Please select valid researchers.")
            return

        try:
            res = api_client.run_bfs(src_id, tgt_id)
        except Exception as e:
            self.output_text.configure(text=f"BFS Execution Error: {str(e)}")
            return

        if res.get("found"):
            path = res.get("path_ids", [])
            self.highlighted_nodes = set(path)
            self.highlighted_edges = {(min(path[i], path[i+1]), max(path[i], path[i+1])) for i in range(len(path)-1)}
            self._draw_graph()

            hops = res.get("hops", 0)
            exp = res.get("explanation", "")

            out = f"⚡ BFS Result: Shortest Path Found ({hops} degree(s) of separation)\n\n"
            out += f"Chain: {' → '.join(n['name'] for n in res.get('path_nodes', []))}\n\n"
            out += f"Rationale: {exp}\n\n"
            out += "Step-by-step Collaboration Links:\n"
            for edge in res.get("edges", []):
                out += f"• {edge['from_name']} 🤝 {edge['to_name']}: {edge['paper_count']} joint publication(s)\n"

            self.output_title.configure(text="BFS Shortest Path Discovered")
            self.output_text.configure(text=out)
        else:
            self._reset_highlight()
            self.output_title.configure(text="No BFS Path")
            self.output_text.configure(text=res.get("explanation", "No path exists between the selected researchers."))

    def _run_dfs(self):
        """Execute DFS multi-path exploration and display."""
        src_name = self.src_var.get()
        tgt_name = self.tgt_var.get()
        src_id = self.name_to_id.get(src_name)
        tgt_id = self.name_to_id.get(tgt_name)

        if not src_id or not tgt_id:
            return

        try:
            paths = api_client.run_dfs(src_id, tgt_id, max_depth=4)
        except Exception as e:
            self.output_text.configure(text=f"DFS Error: {str(e)}")
            return

        if paths:
            # Highlight first discovered DFS path
            first_path = paths[0].get("path_ids", [])
            self.highlighted_nodes = set(first_path)
            self.highlighted_edges = {(min(first_path[i], first_path[i+1]), max(first_path[i], first_path[i+1])) for i in range(len(first_path)-1)}
            self._draw_graph()

            out = f"🔍 DFS Result: Discovered {len(paths)} distinct collaborative routes (Max depth: 4 hops)\n\n"
            for idx, p in enumerate(paths[:4], 1):
                out += f"Route #{idx} ({p['hops']} hops):\n{p['summary']}\n\n"

            self.output_title.configure(text=f"DFS Exploration ({len(paths)} Paths)")
            self.output_text.configure(text=out)
        else:
            self._reset_highlight()
            self.output_title.configure(text="No DFS Routes")
            self.output_text.configure(text="No alternative routes found within depth limit.")

    def _run_clusters(self):
        """Execute DFS connected components detection."""
        try:
            clusters = api_client.get_clusters()
        except Exception as e:
            self.output_text.configure(text=f"Cluster detection error: {str(e)}")
            return

        out = f"🌐 DFS Component Analysis: Detected {len(clusters)} connected research clusters across campus.\n\n"
        for c in clusters:
            lead = c.get("lead_researcher", "Campus Scholar")
            areas = ", ".join(c.get("dominant_areas", [])[:2])
            out += f"Cluster #{c['cluster_id']}: {c['size']} Researchers\n"
            out += f"• Lead Scholar: {lead}\n"
            out += f"• Dominant Fields: {areas or 'Interdisciplinary'}\n\n"

        self.output_title.configure(text="Campus Research Clusters")
        self.output_text.configure(text=out)

    def _reset_highlight(self):
        self.highlighted_nodes.clear()
        self.highlighted_edges.clear()
        self._draw_graph()
        self.output_title.configure(text="Network Graph Reset")
        self.output_text.configure(text="Graph view reset. Select researchers above to run BFS or DFS.")
