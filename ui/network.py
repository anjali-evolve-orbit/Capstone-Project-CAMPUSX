"""
CAMPUSX — Discover People Behind the Work System
Network View: Academic Collaboration Network, Interactive Graph Visualization,
Real-Time Adjacency List Graph, BFS Shortest Path, Level-by-Level BFS, DFS Traversal,
and Research Cluster (Connected Components) Exploration.
"""

import math
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import customtkinter as ctk

try:
    import networkx as nx
except ImportError:
    nx = None

from api_client.client import api_client, APIClientError
from services.network_service import NetworkService
from services.research_service import ResearchService
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge
)


class NetworkView(ctk.CTkFrame):
    """
    Academic Collaboration Network Dashboard.
    Demonstrates graph data structures (Adjacency List) and graph traversal algorithms
    (BFS Shortest Path, BFS Traversal, DFS Traversal, Connected Components).
    """

    def __init__(
        self,
        parent,
        current_user: Optional[Dict[str, Any]] = None,
        on_select_researcher: Optional[Callable[[int], None]] = None
    ):
        super().__init__(parent, fg_color=Theme.SOFT_BG)
        self.current_user = current_user or {}
        self.on_select_researcher = on_select_researcher or (lambda _id: None)

        # Graph Data & Topology
        self.graph_data: Dict[str, Any] = {"nodes": [], "edges": [], "stats": {}}
        self.clusters: List[Dict[str, Any]] = []
        self.node_positions: Dict[int, Tuple[float, float]] = {}
        self.normalized_layout: Dict[int, Tuple[float, float]] = {}

        # Mappings
        self.name_to_id: Dict[str, int] = {}
        self.id_to_name: Dict[int, str] = {}
        self.nodes_by_id: Dict[int, Dict[str, Any]] = {}
        self.adjacency_map: Dict[int, List[Tuple[int, int]]] = {}  # u -> list of (v, weight)

        # Selection & Highlighting State
        self.current_researcher_id: Optional[int] = None
        self.selected_node_id: Optional[int] = None
        self.target_node_id: Optional[int] = None
        self.highlighted_collaborators: Set[int] = set()
        self.highlighted_path_nodes: Set[int] = set()
        self.highlighted_path_edges: Set[Tuple[int, int]] = set()
        self.highlighted_traversal_steps: Dict[int, int] = {}  # nid -> step_num
        self.highlighted_cluster_nodes: Set[int] = set()

        # Canvas Dimensions & Hover State
        self.canvas_width: int = 650
        self.canvas_height: int = 500
        self.hovered_node_id: Optional[int] = None

        # Initialize Data & UI
        self._load_network_data()
        self._resolve_current_researcher()
        self._build_header()
        self._build_overview_cards()
        self._build_main_layout()

        # Default selection: Selected Researcher (Researcher A)
        default_id = self.current_researcher_id or (self.graph_data["nodes"][0]["id"] if self.graph_data.get("nodes") else None)
        if default_id:
            self._select_researcher_by_id(default_id, update_dropdown=True)

        self._calculate_node_layout()
        self.after(50, self._draw_graph)

    # =========================================================================
    # DATA LOADING & INITIALIZATION
    # =========================================================================

    def _resolve_current_researcher(self):
        user_id = self.current_user.get("id")
        if not user_id:
            return
        try:
            profile = api_client.get_researcher_by_user(int(user_id))
            self.current_researcher_id = profile.get("id")
        except Exception:
            try:
                profile = ResearchService.get_researcher_by_user(int(user_id))
                self.current_researcher_id = profile.get("id") if profile else None
            except Exception:
                self.current_researcher_id = None

    def _load_network_data(self):
        """Fetch network graph and connected component clusters from API or Service."""
        try:
            self.graph_data = api_client.get_network_graph()
        except Exception:
            try:
                self.graph_data = NetworkService.get_network_data()
            except Exception:
                self.graph_data = {"nodes": [], "edges": [], "stats": {}}

        try:
            self.clusters = api_client.get_clusters()
        except Exception:
            try:
                self.clusters = NetworkService.get_research_clusters()
            except Exception:
                self.clusters = []

        # Index nodes & build fast adjacency lookup
        nodes = self.graph_data.get("nodes", [])
        self.nodes_by_id = {n["id"]: n for n in nodes}
        self.name_to_id = {n["name"]: n["id"] for n in nodes}
        self.id_to_name = {n["id"]: n["name"] for n in nodes}

        self.adjacency_map = {n["id"]: [] for n in nodes}
        for edge in self.graph_data.get("edges", []):
            u, v, w = edge["source"], edge["target"], edge.get("weight", 1)
            if u in self.adjacency_map and v in self.adjacency_map:
                self.adjacency_map[u].append((v, w))
                self.adjacency_map[v].append((u, w))

    # =========================================================================
    # UI CONSTRUCTION: HEADER & METRIC OVERVIEW CARDS
    # =========================================================================

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=25, pady=(15, 6))

        title_box = ctk.CTkFrame(head, fg_color="transparent")
        title_box.pack(side="left")

        title = ctk.CTkLabel(
            title_box,
            text="ACADEMIC COLLABORATION NETWORK",
            font=Theme.FONT_TITLE,
            text_color=Theme.NAVY
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Explore how researchers are connected through academic collaboration and joint publications.",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        subtitle.pack(anchor="w")

        concept_badge = create_badge(
            head,
            text="Graph: Adjacency List  ·  Node: Researcher  ·  Edge: Academic Collaboration",
            bg_color="#EBF4FF",
            text_color=Theme.ACADEMIC_BLUE,
            font=Theme.FONT_BODY_BOLD
        )
        concept_badge.pack(side="right", pady=5)

    def _build_overview_cards(self):
        """Top 4 metric summary cards showing real dynamic statistics calculated from MySQL/Graph."""
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=25, pady=(0, 12))
        row.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        stats = self.graph_data.get("stats", {})
        total_nodes = stats.get("total_researchers", len(self.graph_data.get("nodes", [])))
        total_edges = stats.get("total_collaborations", len(self.graph_data.get("edges", [])))
        total_clusters = len(self.clusters)

        # 1. Researchers Count
        c1 = create_card(row)
        c1.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(c1, text="RESEARCHERS (NODES)", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(c1, text=str(total_nodes), font=Theme.FONT_TITLE, text_color=Theme.NAVY).pack(anchor="w", padx=14, pady=(0, 10))

        # 2. Collaborations Count
        c2 = create_card(row)
        c2.grid(row=0, column=1, sticky="nsew", padx=6)
        ctk.CTkLabel(c2, text="COLLABORATION EDGES", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(c2, text=str(total_edges), font=Theme.FONT_TITLE, text_color=Theme.ACADEMIC_BLUE).pack(anchor="w", padx=14, pady=(0, 10))

        # 3. Connected Components Count
        c3 = create_card(row)
        c3.grid(row=0, column=2, sticky="nsew", padx=6)
        ctk.CTkLabel(c3, text="CONNECTED COMPONENTS", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(c3, text=str(total_clusters), font=Theme.FONT_TITLE, text_color=Theme.PURPLE).pack(anchor="w", padx=14, pady=(0, 10))

        # 4. Selected Researcher Name
        c4 = create_card(row)
        c4.grid(row=0, column=3, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(c4, text="SELECTED RESEARCHER", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=14, pady=(10, 0))
        self.overview_selected_lbl = ctk.CTkLabel(
            c4,
            text="None selected",
            font=Theme.FONT_SECTION,
            text_color="#B45309"
        )
        self.overview_selected_lbl.pack(anchor="w", padx=14, pady=(0, 10))

    # =========================================================================
    # UI CONSTRUCTION: MAIN SPLIT LAYOUT (LEFT GRAPH, RIGHT DETAILS/ALGORITHMS)
    # =========================================================================

    def _build_main_layout(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=(0, 18))
        container.columnconfigure(0, weight=3)
        container.columnconfigure(1, weight=2)
        container.rowconfigure(0, weight=1)

        # ---------------------------------------------------------------------
        # LEFT: COLLABORATION GRAPH CANVAS CARD
        # ---------------------------------------------------------------------
        canvas_card = create_card(container)
        canvas_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        c_header = ctk.CTkFrame(canvas_card, fg_color="transparent")
        c_header.pack(fill="x", padx=16, pady=(12, 6))

        c_title_box = ctk.CTkFrame(c_header, fg_color="transparent")
        c_title_box.pack(side="left")
        ctk.CTkLabel(
            c_title_box,
            text="Collaboration Graph Visualization",
            font=Theme.FONT_SECTION,
            text_color=Theme.NAVY
        ).pack(anchor="w")
        ctk.CTkLabel(
            c_title_box,
            text="Click any node to select researcher & highlight direct collaborators",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT
        ).pack(anchor="w")

        # Quick toolbar buttons on canvas card
        c_tools = ctk.CTkFrame(c_header, fg_color="transparent")
        c_tools.pack(side="right")

        reset_btn = ctk.CTkButton(
            c_tools,
            text="↺ Reset View",
            command=self._reset_network_view,
            width=90,
            height=28,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.WHITE,
            text_color=Theme.NAVY,
            border_color=Theme.BORDER,
            border_width=1,
            hover_color=Theme.MUTED_BG,
            font=Theme.FONT_CAPTION
        )
        reset_btn.pack(side="left", padx=4)

        cluster_btn = ctk.CTkButton(
            c_tools,
            text="🌐 Clusters",
            command=self._run_clusters,
            width=85,
            height=28,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color="#F3F0FF",
            text_color=Theme.PURPLE,
            hover_color="#E9D5FF",
            font=Theme.FONT_CAPTION
        )
        cluster_btn.pack(side="left", padx=4)

        # Graph CTkCanvas
        self.canvas = ctk.CTkCanvas(
            canvas_card,
            bg=Theme.WHITE,
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(4, 6))
        self.canvas.bind("<Configure>", lambda e: self._on_canvas_resize())
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)

        # Legend Bar below canvas
        legend_bar = ctk.CTkFrame(canvas_card, fg_color=Theme.SOFT_BG, height=36, corner_radius=6)
        legend_bar.pack(fill="x", padx=12, pady=(0, 10))

        legend_items = [
            ("● Researcher", Theme.DARK_TEXT, "#E2E8F0"),
            ("★ Current User", "#15803D", "#DCFCE7"),
            ("● Selected (A)", "#B45309", "#FEF3C7"),
            ("● Direct Collaborator", "#0369A1", "#E0F2FE"),
            ("● Target (B)", "#7E22CE", "#F3E8FF"),
            ("━━ Collaboration Path", Theme.PURPLE, None)
        ]
        for label, text_col, bg_col in legend_items:
            if bg_col:
                create_badge(legend_bar, text=label, bg_color=bg_col, text_color=text_col, font=Theme.FONT_CAPTION).pack(side="left", padx=5, pady=4)
            else:
                ctk.CTkLabel(legend_bar, text=label, font=Theme.FONT_CAPTION, text_color=text_col).pack(side="left", padx=5, pady=4)

        # ---------------------------------------------------------------------
        # RIGHT: CONTROLS, SELECTED RESEARCHER, AND ALGORITHM RESULT PANEL
        # ---------------------------------------------------------------------
        control_card = create_card(container)
        control_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self.control_scroll = ctk.CTkScrollableFrame(control_card, fg_color="transparent")
        self.control_scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # --- SECTION 1: SELECTED RESEARCHER DETAILS CARD ---
        self.details_card = create_card(self.control_scroll, fg_color=Theme.WHITE)
        self.details_card.pack(fill="x", pady=(0, 12))

        det_inner = ctk.CTkFrame(self.details_card, fg_color="transparent")
        det_inner.pack(fill="x", padx=14, pady=12)

        det_header = ctk.CTkFrame(det_inner, fg_color="transparent")
        det_header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(det_header, text="SELECTED RESEARCHER", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left")

        self.view_profile_btn = ctk.CTkButton(
            det_header,
            text="View Full Profile →",
            command=self._open_selected_profile,
            width=120,
            height=24,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color="#EFF6FF",
            text_color=Theme.ACADEMIC_BLUE,
            hover_color="#DBEAFE",
            font=Theme.FONT_CAPTION
        )
        self.view_profile_btn.pack(side="right")

        self.det_name_lbl = ctk.CTkLabel(det_inner, text="Select a researcher", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY)
        self.det_name_lbl.pack(anchor="w", pady=(0, 2))

        self.det_meta_lbl = ctk.CTkLabel(det_inner, text="", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT)
        self.det_meta_lbl.pack(anchor="w", pady=(0, 8))

        # Direct Collaborators Sub-Section
        self.collab_sec_lbl = ctk.CTkLabel(det_inner, text="Direct Collaborators (0)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT)
        self.collab_sec_lbl.pack(anchor="w", pady=(2, 2))

        self.collab_chips_frame = ctk.CTkFrame(det_inner, fg_color="transparent")
        self.collab_chips_frame.pack(fill="x", pady=(0, 8))

        # Research Areas Sub-Section
        ctk.CTkLabel(det_inner, text="Research Areas", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.areas_chips_frame = ctk.CTkFrame(det_inner, fg_color="transparent")
        self.areas_chips_frame.pack(fill="x", pady=(0, 8))

        # Skills Sub-Section
        ctk.CTkLabel(det_inner, text="Skills", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.skills_chips_frame = ctk.CTkFrame(det_inner, fg_color="transparent")
        self.skills_chips_frame.pack(fill="x", pady=(0, 4))

        # --- SECTION 2: COLLABORATION ANALYSIS (A/B SELECTION & ALGORITHMS) ---
        analysis_card = create_card(self.control_scroll, fg_color=Theme.WHITE)
        analysis_card.pack(fill="x", pady=(0, 12))

        ana_inner = ctk.CTkFrame(analysis_card, fg_color="transparent")
        ana_inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(ana_inner, text="COLLABORATION ANALYSIS", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(ana_inner, text="Graph Path & Traversal Algorithms", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 10))

        # Researcher A dropdown
        ctk.CTkLabel(ana_inner, text="Researcher A (Source)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        researcher_names = sorted(list(self.name_to_id.keys())) if self.name_to_id else ["No researchers"]
        self.src_var = ctk.StringVar(value=researcher_names[0] if researcher_names else "")
        self.src_menu = ctk.CTkOptionMenu(
            ana_inner,
            variable=self.src_var,
            values=researcher_names,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE,
            command=self._on_src_dropdown_change
        )
        self.src_menu.pack(fill="x", pady=(0, 8))

        # Researcher B dropdown
        ctk.CTkLabel(ana_inner, text="Researcher B (Target)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        second_name = researcher_names[1] if len(researcher_names) > 1 else (researcher_names[0] if researcher_names else "")
        self.tgt_var = ctk.StringVar(value=second_name)
        self.tgt_menu = ctk.CTkOptionMenu(
            ana_inner,
            variable=self.tgt_var,
            values=researcher_names,
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.NAVY,
            command=self._on_tgt_dropdown_change
        )
        self.tgt_menu.pack(fill="x", pady=(0, 12))

        # Action Buttons
        btn_box = ctk.CTkFrame(ana_inner, fg_color="transparent")
        btn_box.pack(fill="x")

        # 1. Shortest Path (BFS)
        bfs_btn = create_primary_button(
            btn_box,
            text="⚡ Find Shortest Collaboration Path",
            command=self._run_bfs_shortest_path,
            height=36
        )
        bfs_btn.configure(fg_color=Theme.PURPLE, hover_color="#5849BE")
        bfs_btn.pack(fill="x", pady=3)

        # 2. BFS Traversal
        bfs_trav_btn = create_secondary_button(
            btn_box,
            text="🌊 Run BFS Traversal (Level-by-Level)",
            command=self._run_bfs_traversal,
            height=34
        )
        bfs_trav_btn.pack(fill="x", pady=3)

        # 3. DFS Traversal
        dfs_trav_btn = create_secondary_button(
            btn_box,
            text="🌲 Run DFS Traversal (Deep Exploration)",
            command=self._run_dfs_traversal,
            height=34
        )
        dfs_trav_btn.pack(fill="x", pady=3)

        # --- SECTION 3: ALGORITHM RESULT PANEL ---
        self.result_card = create_card(self.control_scroll, fg_color=Theme.WHITE)
        self.result_card.pack(fill="x", pady=(0, 12))

        res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        res_inner.pack(fill="x", padx=14, pady=12)

        res_head = ctk.CTkFrame(res_inner, fg_color="transparent")
        res_head.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(res_head, text="ALGORITHM RESULT", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left")
        self.algo_badge = create_badge(res_head, text="Ready", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE)
        self.algo_badge.pack(side="right")

        self.res_title = ctk.CTkLabel(res_inner, text="Select researchers & execute an algorithm", font=Theme.FONT_SECTION, text_color=Theme.NAVY)
        self.res_title.pack(anchor="w", pady=(0, 4))

        self.res_content = ctk.CTkLabel(
            res_inner,
            text="Click 'Find Shortest Collaboration Path' to calculate the degrees of separation between Researcher A and Researcher B, or run BFS/DFS traversals.",
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=340,
            justify="left"
        )
        self.res_content.pack(anchor="w")

        # --- SECTION 4: DATA STRUCTURE & ALGORITHMIC EXPLANATION PANEL ---
        ds_card = create_card(self.control_scroll, fg_color="#F8FAFC")
        ds_card.pack(fill="x", pady=(0, 4))

        ds_inner = ctk.CTkFrame(ds_card, fg_color="transparent")
        ds_inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(ds_inner, text="DATA STRUCTURE USED", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(ds_inner, text="Graph ADT (Adjacency List)", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 6))

        ds_desc = (
            "• Representation: Adjacency List Dictionary (O(V + E) space)\n"
            "• Node (Vertex): Researcher profile in MySQL\n"
            "• Edge: Academic Collaboration (Co-Authorship)\n"
            "• Edge Weight: Joint publication count\n\n"
            "ALGORITHMS IMPLEMENTED:\n"
            "• BFS (Breadth-First Search): Explores co-authors level-by-level using a FIFO queue; guarantees the shortest academic collaboration path.\n"
            "• DFS (Depth-First Search): Explores deep collaborative branches recursively using LIFO order.\n"
            "• Connected Components: Partitions researchers into isolated or interdisciplinary research clusters using DFS."
        )
        ctk.CTkLabel(
            ds_inner,
            text=ds_desc,
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT,
            wraplength=340,
            justify="left"
        ).pack(anchor="w")

    # =========================================================================
    # GRAPH LAYOUT CALCULATION (NETWORKX SPRING LAYOUT)
    # =========================================================================

    def _calculate_node_layout(self):
        """
        Calculates 2D positions for all researcher nodes using NetworkX force-directed
        spring layout. Disconnected components and isolated researchers are spaced cleanly.
        """
        nodes = self.graph_data.get("nodes", [])
        if not nodes:
            return

        w = self.canvas.winfo_width() or self.canvas_width
        h = self.canvas.winfo_height() or self.canvas_height
        self.canvas_width = max(w, 400)
        self.canvas_height = max(h, 350)

        # Build NetworkX graph if available
        if nx is not None:
            G = nx.Graph()
            for n in nodes:
                G.add_node(n["id"])
            for e in self.graph_data.get("edges", []):
                G.add_edge(e["source"], e["target"], weight=e.get("weight", 1))

            # Fixed seed ensures deterministic, stable positions across clicks & renders
            raw_pos = nx.spring_layout(G, k=0.45, iterations=80, seed=42)

            xs = [p[0] for p in raw_pos.values()]
            ys = [p[1] for p in raw_pos.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            self.normalized_layout.clear()
            for nid, (x, y) in raw_pos.items():
                nx_norm = (x - min_x) / (max_x - min_x + 1e-9)
                ny_norm = (y - min_y) / (max_y - min_y + 1e-9)
                self.normalized_layout[nid] = (float(nx_norm), float(ny_norm))
        else:
            # Fallback circular layout if NetworkX is missing
            num_nodes = len(nodes)
            self.normalized_layout.clear()
            for idx, node in enumerate(nodes):
                angle = 2 * math.pi * idx / num_nodes
                r = 0.42 if (idx % 2 == 0) else 0.36
                nx_norm = 0.5 + r * math.cos(angle)
                ny_norm = 0.5 + r * math.sin(angle)
                self.normalized_layout[node["id"]] = (nx_norm, ny_norm)

        self._scale_layout_to_canvas()

    def _scale_layout_to_canvas(self):
        """Map normalized layout (0..1) to current canvas screen coordinates with padding."""
        margin_x = 55
        margin_y = 50
        usable_w = max(100, self.canvas_width - 2 * margin_x)
        usable_h = max(100, self.canvas_height - 2 * margin_y)

        self.node_positions.clear()
        for nid, (nx_val, ny_val) in self.normalized_layout.items():
            screen_x = margin_x + nx_val * usable_w
            screen_y = margin_y + ny_val * usable_h
            self.node_positions[nid] = (screen_x, screen_y)

    def _on_canvas_resize(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 50 and h > 50 and (w != self.canvas_width or h != self.canvas_height):
            self.canvas_width = w
            self.canvas_height = h
            self._scale_layout_to_canvas()
            self._draw_graph()

    # =========================================================================
    # GRAPH RENDERING ON CANVAS
    # =========================================================================

    def _draw_graph(self):
        """Renders edges, nodes, halos, collaborator rings, and shortest paths."""
        if not self.winfo_exists():
            return

        self.canvas.delete("all")
        nodes = self.graph_data.get("nodes", [])
        edges = self.graph_data.get("edges", [])

        if not nodes or not self.node_positions:
            self.canvas.create_text(
                self.canvas_width / 2,
                self.canvas_height / 2,
                text="No collaboration network available yet.\nCollaborations between researchers will appear here.",
                fill=Theme.SECONDARY_TEXT,
                font=(Theme.FONT_FAMILY, 12),
                justify="center"
            )
            return

        # 1. DRAW EDGES
        for edge in edges:
            u, v = edge["source"], edge["target"]
            if u not in self.node_positions or v not in self.node_positions:
                continue

            x1, y1 = self.node_positions[u]
            x2, y2 = self.node_positions[v]
            pair = (min(u, v), max(u, v))

            # Edge Styling Priority: Shortest Path > Direct Collaborator > Normal
            if pair in self.highlighted_path_edges:
                line_color = Theme.PURPLE
                line_width = 4
            elif (self.selected_node_id == u and v in self.highlighted_collaborators) or \
                 (self.selected_node_id == v and u in self.highlighted_collaborators):
                line_color = "#0284C7"  # Deep sky blue
                line_width = 2.5
            else:
                line_color = "#E2E8F0"
                line_width = max(1.2, min(edge.get("weight", 1) * 1.2, 3.5))

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=line_color,
                width=line_width,
                capstyle="round"
            )

        # 2. DRAW NODES
        node_radius = 16

        for node in nodes:
            nid = node["id"]
            if nid not in self.node_positions:
                continue

            x, y = self.node_positions[nid]

            is_current_user = (nid == self.current_researcher_id)
            is_selected = (nid == self.selected_node_id)
            is_collaborator = (nid in self.highlighted_collaborators)
            is_target = (nid == self.target_node_id)
            is_in_path = (nid in self.highlighted_path_nodes)
            is_in_cluster = (nid in self.highlighted_cluster_nodes)
            traversal_step = self.highlighted_traversal_steps.get(nid)

            # OUTER GLOW RINGS (Visual indicators for graph states)
            if is_selected:
                # Golden/Amber glow for Researcher A
                self.canvas.create_oval(
                    x - node_radius - 8, y - node_radius - 8,
                    x + node_radius + 8, y + node_radius + 8,
                    fill="#FEF3C7", outline="#F59E0B", width=2.5
                )
            elif is_in_path:
                # Purple glow for Shortest Path
                self.canvas.create_oval(
                    x - node_radius - 7, y - node_radius - 7,
                    x + node_radius + 7, y + node_radius + 7,
                    fill="#EDE9FE", outline=Theme.PURPLE, width=2.5
                )
            elif is_collaborator:
                # Cyan/Sky glow for Direct Collaborators
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#E0F2FE", outline="#0284C7", width=2
                )
            elif is_target:
                # Violet glow for Target Researcher B
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#F3E8FF", outline="#9333EA", width=2
                )
            elif is_in_cluster:
                # Emerald glow for Cluster Members
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#DCFCE7", outline="#16A34A", width=2
                )
            elif is_current_user:
                # Green ring for Current Logged-in User
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#F0FDF4", outline="#16A34A", width=1.8
                )

            # NODE FILL COLOR
            if is_selected:
                fill_color = "#D97706"
                border_color = Theme.WHITE
            elif is_in_path:
                fill_color = Theme.PURPLE
                border_color = Theme.WHITE
            elif is_collaborator:
                fill_color = "#0284C7"
                border_color = Theme.WHITE
            else:
                fill_color = node.get("avatar_color", Theme.ACADEMIC_BLUE)
                border_color = Theme.WHITE

            # Main Node Circle
            self.canvas.create_oval(
                x - node_radius, y - node_radius,
                x + node_radius, y + node_radius,
                fill=fill_color,
                outline=border_color,
                width=2
            )

            # Center Initials
            initials = "".join([w[0] for w in node["name"].split() if w])[:2].upper()
            self.canvas.create_text(
                x, y,
                text=initials,
                fill=Theme.WHITE,
                font=(Theme.FONT_FAMILY, 9, "bold")
            )

            # Traversal Step Badge (if BFS/DFS traversal was run)
            if traversal_step:
                badge_x = x + node_radius + 2
                badge_y = y - node_radius + 2
                self.canvas.create_oval(
                    badge_x - 7, badge_y - 7,
                    badge_x + 7, badge_y + 7,
                    fill="#10B981", outline=Theme.WHITE, width=1.5
                )
                self.canvas.create_text(
                    badge_x, badge_y,
                    text=str(traversal_step),
                    fill=Theme.WHITE,
                    font=(Theme.FONT_FAMILY, 7, "bold")
                )

            # Current User Star Badge
            if is_current_user and not traversal_step:
                star_x = x + node_radius + 2
                star_y = y - node_radius + 2
                self.canvas.create_oval(
                    star_x - 6, star_y - 6,
                    star_x + 6, star_y + 6,
                    fill="#16A34A", outline=Theme.WHITE, width=1.5
                )
                self.canvas.create_text(
                    star_x, star_y,
                    text="★",
                    fill=Theme.WHITE,
                    font=(Theme.FONT_FAMILY, 7, "bold")
                )

            # Label Below Node (Readable Researcher Name)
            name_parts = node["name"].split()
            display_name = name_parts[-1] if len(name_parts) > 1 else node["name"]
            if is_selected:
                text_color = "#92400E"
                font_weight = "bold"
            elif is_in_path:
                text_color = Theme.PURPLE
                font_weight = "bold"
            elif is_collaborator:
                text_color = "#0369A1"
                font_weight = "bold"
            else:
                text_color = Theme.DARK_TEXT
                font_weight = "normal"

            self.canvas.create_text(
                x, y + node_radius + 12,
                text=display_name,
                fill=text_color,
                font=(Theme.FONT_FAMILY, 8, font_weight)
            )

    # =========================================================================
    # INTERACTIVE CANVAS EVENTS (CLICK TO SELECT, MOUSE MOTION)
    # =========================================================================

    def _on_canvas_click(self, event):
        """Clicking any node on the canvas selects that researcher as Researcher A."""
        cx, cy = event.x, event.y
        clicked_id = None
        min_dist = float("inf")

        for nid, (x, y) in self.node_positions.items():
            dist = math.hypot(cx - x, cy - y)
            if dist <= 24 and dist < min_dist:
                min_dist = dist
                clicked_id = nid

        if clicked_id:
            self._select_researcher_by_id(clicked_id, update_dropdown=True)

    def _on_canvas_motion(self, event):
        """Changes mouse cursor to hand2 when hovering over a node."""
        cx, cy = event.x, event.y
        hovered = None

        for nid, (x, y) in self.node_positions.items():
            if math.hypot(cx - x, cy - y) <= 22:
                hovered = nid
                break

        if hovered != self.hovered_node_id:
            self.hovered_node_id = hovered
            self.canvas.configure(cursor="hand2" if hovered else "")

    # =========================================================================
    # RESEARCHER SELECTION & DETAILS UPDATE
    # =========================================================================

    def _select_researcher_by_id(self, researcher_id: int, update_dropdown: bool = False):
        """
        Activates a researcher as the Selected Researcher (Researcher A):
        1. Highlights the node on the graph.
        2. Identifies and highlights direct collaborators.
        3. Updates the Selected Researcher details panel.
        4. Updates the Overview counter card.
        5. Synchronizes the dropdown menu.
        """
        if researcher_id not in self.nodes_by_id:
            return

        self.selected_node_id = researcher_id
        res_data = self.nodes_by_id[researcher_id]
        name = res_data["name"]

        if update_dropdown and name in self.name_to_id:
            self.src_var.set(name)

        # Identify direct collaborators from adjacency map
        neighbor_tuples = self.adjacency_map.get(researcher_id, [])
        self.highlighted_collaborators = {v for v, _ in neighbor_tuples}

        # Clear old traversal/cluster highlights (keep current target)
        self.highlighted_traversal_steps.clear()
        self.highlighted_cluster_nodes.clear()

        # Update overview card
        self.overview_selected_lbl.configure(text=name)

        # Update Selected Researcher details card
        self._update_details_panel(researcher_id, res_data, neighbor_tuples)

        # Redraw graph
        self._draw_graph()

    def _update_details_panel(self, researcher_id: int, node_data: Dict[str, Any], neighbors: List[Tuple[int, int]]):
        """Populate the Selected Researcher panel with full academic profile and collaborator chips."""
        self.det_name_lbl.configure(text=node_data.get("name", "Researcher"))

        # Fetch detailed profile from API/Service to get latest areas and skills
        detailed_profile = {}
        try:
            detailed_profile = api_client.get_researcher_detail(researcher_id)
        except Exception:
            try:
                detailed_profile = ResearchService.get_researcher_detail(researcher_id) or {}
            except Exception:
                detailed_profile = {}

        desig = detailed_profile.get("designation") or node_data.get("designation", "Faculty Researcher")
        dept = detailed_profile.get("department_name") or node_data.get("department", "Engineering")
        inst = detailed_profile.get("institution_name") or node_data.get("institution", "CampusX")
        self.det_meta_lbl.configure(text=f"{desig} · {dept}\n{inst}")

        # 1. Direct Collaborators List
        num_collabs = len(neighbors)
        self.collab_sec_lbl.configure(text=f"Direct Collaborators ({num_collabs})")

        for child in self.collab_chips_frame.winfo_children():
            child.destroy()

        if neighbors:
            for neighbor_id, papers in neighbors:
                collab_name = self.id_to_name.get(neighbor_id, f"Researcher #{neighbor_id}")
                btn = ctk.CTkButton(
                    self.collab_chips_frame,
                    text=f"{collab_name} ({papers} 📄)",
                    command=lambda nid=neighbor_id: self._select_researcher_by_id(nid, update_dropdown=True),
                    height=24,
                    corner_radius=12,
                    fg_color="#E0F2FE",
                    text_color="#0369A1",
                    hover_color="#BAE6FD",
                    font=Theme.FONT_CAPTION
                )
                btn.pack(side="left", padx=3, pady=2)
        else:
            ctk.CTkLabel(
                self.collab_chips_frame,
                text="No direct collaborators recorded yet.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w")

        # 2. Research Areas Tags
        for child in self.areas_chips_frame.winfo_children():
            child.destroy()

        areas = detailed_profile.get("areas", []) or node_data.get("areas", [])
        if areas:
            for area in areas:
                area_text = area.get("name") if isinstance(area, dict) else str(area)
                create_badge(
                    self.areas_chips_frame,
                    text=area_text,
                    bg_color="#EEF2FF",
                    text_color=Theme.ACADEMIC_BLUE,
                    font=Theme.FONT_CAPTION
                ).pack(side="left", padx=3, pady=2)
        else:
            ctk.CTkLabel(
                self.areas_chips_frame,
                text="No research areas listed.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w")

        # 3. Skills Tags
        for child in self.skills_chips_frame.winfo_children():
            child.destroy()

        skills = detailed_profile.get("skills", [])
        if skills:
            for skill in skills[:6]:  # Show up to 6 skills
                skill_name = skill.get("name") if isinstance(skill, dict) else str(skill)
                create_badge(
                    self.skills_chips_frame,
                    text=skill_name,
                    bg_color="#F1F5F9",
                    text_color=Theme.NAVY,
                    font=Theme.FONT_CAPTION
                ).pack(side="left", padx=3, pady=2)
        else:
            ctk.CTkLabel(
                self.skills_chips_frame,
                text="No skills listed yet.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w")

    def _open_selected_profile(self):
        """Navigate to the full profile of the currently selected researcher."""
        if self.selected_node_id:
            self.on_select_researcher(self.selected_node_id)

    # =========================================================================
    # DROPDOWN EVENT HANDLERS
    # =========================================================================

    def _on_src_dropdown_change(self, selected_name: str):
        nid = self.name_to_id.get(selected_name)
        if nid:
            self._select_researcher_by_id(nid, update_dropdown=False)

    def _on_tgt_dropdown_change(self, selected_name: str):
        nid = self.name_to_id.get(selected_name)
        if nid:
            self.target_node_id = nid
            # Clear old shortest path when target changes
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self._draw_graph()

    # =========================================================================
    # ALGORITHM 1: SHORTEST COLLABORATION PATH (BFS)
    # =========================================================================

    def _run_bfs_shortest_path(self):
        """Calculate and highlight the real shortest collaboration path using BFS."""
        src_name = self.src_var.get()
        tgt_name = self.tgt_var.get()
        src_id = self.name_to_id.get(src_name)
        tgt_id = self.name_to_id.get(tgt_name)

        if not src_id or not tgt_id:
            self.res_title.configure(text="Invalid Selection")
            self.res_content.configure(text="Please select valid researchers from the dropdowns.")
            return

        self.target_node_id = tgt_id

        try:
            res = api_client.run_bfs(src_id, tgt_id)
        except Exception:
            try:
                res = NetworkService.execute_bfs_path(src_id, tgt_id)
            except Exception as e:
                self.res_title.configure(text="BFS Execution Error")
                self.res_content.configure(text=f"An error occurred: {str(e)}")
                return

        if res.get("found"):
            path = res.get("path_ids", [])
            self.highlighted_path_nodes = set(path)
            self.highlighted_path_edges = {
                (min(path[i], path[i+1]), max(path[i], path[i+1]))
                for i in range(len(path)-1)
            }
            self.highlighted_traversal_steps.clear()
            self.highlighted_cluster_nodes.clear()
            self._draw_graph()

            hops = res.get("hops", len(path) - 1)
            chain = " → ".join(n["name"] for n in res.get("path_nodes", []))

            self.algo_badge.configure(text="BFS Path Found", fg_color="#F3E8FF", text_color=Theme.PURPLE)
            self.res_title.configure(text=f"Shortest Collaboration Path ({hops} Degree{'s' if hops != 1 else ''} of Separation)")

            out = f"Collaboration Chain:\n{chain}\n\n"
            out += f"Path Length: {hops} collaboration{'s' if hops != 1 else ''}\n\n"
            out += "Step-by-step Joint Co-authorship Links:\n"
            for edge in res.get("edges", []):
                out += f"• {edge['from_name']} 🤝 {edge['to_name']}: {edge.get('paper_count', 1)} joint paper(s)\n"

            out += "\nGraph Theory Rationale:\n"
            out += "Breadth-First Search (BFS) explores all neighbors at distance d before moving to d+1, mathematically guaranteeing the shortest collaborative chain."

            self.res_content.configure(text=out)
        else:
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self._draw_graph()

            self.algo_badge.configure(text="No Path", fg_color="#FEE2E2", text_color="#B91C1C")
            self.res_title.configure(text="No Collaboration Path Exists")
            self.res_content.configure(
                text=f"No collaboration path exists between {src_name} and {tgt_name}.\n\n"
                     "They belong to disconnected research clusters in the academic network graph. "
                     "No joint publications or transitive co-authors connect these two scholars."
            )

    # =========================================================================
    # ALGORITHM 2: BFS TRAVERSAL (LEVEL-BY-LEVEL EXPLORATION)
    # =========================================================================

    def _run_bfs_traversal(self):
        """Run level-by-level BFS traversal starting from Researcher A."""
        src_name = self.src_var.get()
        src_id = self.name_to_id.get(src_name)

        if not src_id:
            return

        try:
            traversal = api_client.get_bfs_traversal(src_id)
        except Exception:
            try:
                traversal = NetworkService.get_bfs_traversal(src_id)
            except Exception as e:
                self.res_title.configure(text="BFS Traversal Error")
                self.res_content.configure(text=f"Error: {str(e)}")
                return

        if traversal:
            self.highlighted_traversal_steps = {item["id"]: item["step"] for item in traversal}
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self.highlighted_cluster_nodes.clear()
            self._draw_graph()

            self.algo_badge.configure(text="BFS Traversal", fg_color="#E0F2FE", text_color="#0369A1")
            self.res_title.configure(text=f"BFS Level-by-Level Traversal ({len(traversal)} Visited)")

            out = f"Starting Scholar: {src_name}\n"
            out += "Traversal Order (Level-by-Level):\n\n"
            for item in traversal[:12]:
                depth_label = f"Level {item.get('depth', 0)}" if item.get("depth", 0) > 0 else "Source (Level 0)"
                out += f"{item['step']}. {item['name']} ({depth_label})\n"

            if len(traversal) > 12:
                out += f"... and {len(traversal) - 12} more researchers.\n"

            out += "\nAlgorithmic Behavior:\n"
            out += "BFS explores the collaboration network level-by-level starting from the selected researcher, visiting 1st-degree co-authors first, then 2nd-degree mutual collaborators."

            self.res_content.configure(text=out)

    # =========================================================================
    # ALGORITHM 3: DFS TRAVERSAL (DEEP EXPLORATION)
    # =========================================================================

    def _run_dfs_traversal(self):
        """Run recursive DFS traversal starting from Researcher A."""
        src_name = self.src_var.get()
        src_id = self.name_to_id.get(src_name)

        if not src_id:
            return

        try:
            traversal = api_client.get_dfs_traversal(src_id)
        except Exception:
            try:
                traversal = NetworkService.get_dfs_traversal(src_id)
            except Exception as e:
                self.res_title.configure(text="DFS Traversal Error")
                self.res_content.configure(text=f"Error: {str(e)}")
                return

        if traversal:
            self.highlighted_traversal_steps = {item["id"]: item["step"] for item in traversal}
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self.highlighted_cluster_nodes.clear()
            self._draw_graph()

            self.algo_badge.configure(text="DFS Traversal", fg_color="#FEF3C7", text_color="#B45309")
            self.res_title.configure(text=f"DFS Deep Traversal ({len(traversal)} Visited)")

            out = f"Starting Scholar: {src_name}\n"
            out += "Traversal Order (Depth-First):\n\n"
            for item in traversal[:12]:
                depth_label = f"Depth {item.get('depth', 0)}"
                out += f"{item['step']}. {item['name']} ({depth_label})\n"

            if len(traversal) > 12:
                out += f"... and {len(traversal) - 12} more researchers.\n"

            out += "\nAlgorithmic Behavior:\n"
            out += "DFS explores one collaboration path deeply using a recursive LIFO call stack before backtracking to explore other connected researchers."

            self.res_content.configure(text=out)

    # =========================================================================
    # ALGORITHM 4: CONNECTED COMPONENTS / RESEARCH CLUSTERS
    # =========================================================================

    def _run_clusters(self):
        """Detect and display connected components (research clusters) across campus."""
        try:
            clusters = api_client.get_clusters()
        except Exception:
            try:
                clusters = NetworkService.get_research_clusters()
            except Exception as e:
                self.res_title.configure(text="Cluster Detection Error")
                self.res_content.configure(text=f"Error: {str(e)}")
                return

        self.clusters = clusters
        self.algo_badge.configure(text="Connected Components", fg_color="#DCFCE7", text_color="#15803D")
        self.res_title.configure(text=f"Research Collaboration Clusters ({len(clusters)} Components)")

        out = f"Detected {len(clusters)} connected components across the campus graph:\n\n"
        for c in clusters[:6]:
            lead = c.get("lead_researcher", "Campus Scholar")
            size = c.get("size", len(c.get("member_ids", [])))
            areas = ", ".join(c.get("dominant_areas", [])[:2]) or "Interdisciplinary"
            out += f"• Cluster #{c['cluster_id']}: {size} Researchers\n"
            out += f"  Lead Scholar: {lead}\n"
            out += f"  Dominant Fields: {areas}\n\n"

        out += "Graph Theory Concept:\n"
        out += "A connected component is a maximal subgraph where any two researchers are connected by at least one collaborative path."

        # Highlight primary largest cluster members
        if clusters:
            primary_members = clusters[0].get("member_ids", [])
            self.highlighted_cluster_nodes = set(primary_members)
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self.highlighted_traversal_steps.clear()
            self._draw_graph()

        self.res_content.configure(text=out)

    # =========================================================================
    # RESET NETWORK VIEW
    # =========================================================================

    def _reset_network_view(self):
        """Restores the graph and algorithm panel to default normal state."""
        self.highlighted_path_nodes.clear()
        self.highlighted_path_edges.clear()
        self.highlighted_traversal_steps.clear()
        self.highlighted_cluster_nodes.clear()

        # Re-highlight currently selected node and its direct collaborators
        if self.selected_node_id:
            neighbors = self.adjacency_map.get(self.selected_node_id, [])
            self.highlighted_collaborators = {v for v, _ in neighbors}

        self._draw_graph()

        self.algo_badge.configure(text="Normal Graph", fg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE)
        self.res_title.configure(text="Network Graph Reset")
        self.res_content.configure(
            text="Highlights cleared. The graph shows the standard academic collaboration topology. "
                 "Select researchers above to execute shortest path or traversals."
        )
