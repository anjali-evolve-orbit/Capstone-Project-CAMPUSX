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

from api_client.client import api_client
from services.network_service import NetworkService
from services.research_service import ResearchService
from ui.theme import (
    Theme,
    create_card,
    create_primary_button,
    create_secondary_button,
    create_badge,
    enable_mousewheel
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
        self.normalized_connected: Dict[int, Tuple[float, float]] = {}
        self.connected_node_ids: List[int] = []
        self.isolated_node_ids: List[int] = []

        # Unique Mappings & Option Menus
        self.nodes_by_id: Dict[int, Dict[str, Any]] = {}
        self.id_to_name: Dict[int, str] = {}
        self.dropdown_labels: List[str] = []
        self.label_to_id: Dict[str, int] = {}
        self.id_to_label: Dict[int, str] = {}
        self.adjacency_map: Dict[int, List[Tuple[int, int]]] = {}  # u -> list of (v, weight)

        # Selection & Highlighting State
        self.current_researcher_id: Optional[int] = None
        self.selected_node_id: Optional[int] = None      # Researcher A (Source)
        self.target_node_id: Optional[int] = None        # Researcher B (Target)
        self.highlighted_collaborators: Set[int] = set()
        self.highlighted_path_nodes: Set[int] = set()
        self.highlighted_path_edges: Set[Tuple[int, int]] = set()
        self.highlighted_traversal_steps: Dict[int, int] = {}  # nid -> step_num
        self.highlighted_cluster_nodes: Set[int] = set()

        # Canvas Dimensions & Hover State
        self.canvas_width: int = 680
        self.canvas_height: int = 520
        self.hovered_node_id: Optional[int] = None

        # Initialize Data & UI
        self._load_network_data()
        self._resolve_current_researcher()
        self._build_header()
        self._build_overview_cards()
        self._build_main_layout()

        # Default selections: Researcher A (current user or 1st node), Researcher B (2nd node)
        nodes = self.graph_data.get("nodes", [])
        default_a = self.current_researcher_id or (nodes[0]["id"] if nodes else None)
        default_b = None
        if nodes:
            for n in nodes:
                if n["id"] != default_a:
                    default_b = n["id"]
                    break
            if default_b is None:
                default_b = default_a

        if default_a:
            self._select_researcher_by_id(default_a, update_dropdown=True)
        if default_b:
            self._set_target_researcher_by_id(default_b, update_dropdown=True)

        self._calculate_node_layout()
        self.after(60, self._draw_graph)

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

        # Index nodes & build lookup structures
        nodes = self.graph_data.get("nodes", [])
        self.nodes_by_id = {n["id"]: n for n in nodes}
        self.id_to_name = {n["id"]: n["name"] for n in nodes}

        # Build adjacency map
        self.adjacency_map = {n["id"]: [] for n in nodes}
        for edge in self.graph_data.get("edges", []):
            u, v, w = edge["source"], edge["target"], edge.get("weight", 1)
            if u in self.adjacency_map and v in self.adjacency_map:
                self.adjacency_map[u].append((v, w))
                self.adjacency_map[v].append((u, w))

        # Partition into connected vs isolated nodes based on actual degree
        self.connected_node_ids = [nid for nid, neighbors in self.adjacency_map.items() if len(neighbors) > 0]
        self.isolated_node_ids = [nid for nid, neighbors in self.adjacency_map.items() if len(neighbors) == 0]

        # Build 100% collision-free dropdown options: "Name (Dept) · ID:X"
        self.dropdown_labels = []
        self.label_to_id = {}
        self.id_to_label = {}
        for n in sorted(nodes, key=lambda x: (x.get("department") or "", x["name"])):
            nid = n["id"]
            name = n["name"]
            dept = n.get("department", "")
            if dept:
                label = f"{name} ({dept}) · ID:{nid}"
            else:
                label = f"{name} · ID:{nid}"
            self.dropdown_labels.append(label)
            self.label_to_id[label] = nid
            self.id_to_label[nid] = label

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
            text="Explore collaborative academic topology, degrees of separation, and research clusters.",
            font=Theme.FONT_BODY,
            text_color=Theme.SECONDARY_TEXT
        )
        subtitle.pack(anchor="w")

        concept_badge = create_badge(
            head,
            text="Graph ADT: Adjacency List  ·  Node: Researcher  ·  Edge: Academic Collaboration",
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
        ctk.CTkLabel(c4, text="SELECTED RESEARCHER (A)", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=14, pady=(10, 0))
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
            text="Left-click node: Select Researcher A  ·  Right-click: Set Target B  ·  Hover for details",
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
        self.canvas.bind("<Button-1>", self._on_canvas_left_click)
        self.canvas.bind("<Button-2>", self._on_canvas_right_click)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Leave>", self._on_canvas_leave)

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
        enable_mousewheel(self.control_scroll)

        # --- SECTION 1: SELECTED RESEARCHER DETAILS CARD ---
        self.details_card = create_card(self.control_scroll, fg_color=Theme.WHITE)
        self.details_card.pack(fill="x", pady=(0, 12))

        det_inner = ctk.CTkFrame(self.details_card, fg_color="transparent")
        det_inner.pack(fill="x", padx=14, pady=12)

        det_header = ctk.CTkFrame(det_inner, fg_color="transparent")
        det_header.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(det_header, text="SELECTED RESEARCHER", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left")

        actions_box = ctk.CTkFrame(det_header, fg_color="transparent")
        actions_box.pack(side="right")

        self.set_target_btn = ctk.CTkButton(
            actions_box,
            text="Set as Target (B)",
            command=self._set_current_selected_as_target,
            width=105,
            height=24,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color="#F3E8FF",
            text_color=Theme.PURPLE,
            hover_color="#E9D5FF",
            font=Theme.FONT_CAPTION
        )
        self.set_target_btn.pack(side="left", padx=(0, 4))

        self.view_profile_btn = ctk.CTkButton(
            actions_box,
            text="Full Profile →",
            command=self._open_selected_profile,
            width=85,
            height=24,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color="#EFF6FF",
            text_color=Theme.ACADEMIC_BLUE,
            hover_color="#DBEAFE",
            font=Theme.FONT_CAPTION
        )
        self.view_profile_btn.pack(side="left")

        # Researcher Name & Metadata
        self.det_name_lbl = ctk.CTkLabel(det_inner, text="Select a researcher", font=Theme.FONT_SUBTITLE, text_color=Theme.NAVY)
        self.det_name_lbl.pack(anchor="w", pady=(2, 2))

        self.det_meta_lbl = ctk.CTkLabel(det_inner, text="", font=Theme.FONT_BODY, text_color=Theme.SECONDARY_TEXT, justify="left")
        self.det_meta_lbl.pack(anchor="w", pady=(0, 6))

        # Metrics chips row (Citations, Co-authors, Papers)
        self.metrics_row = ctk.CTkFrame(det_inner, fg_color="transparent")
        self.metrics_row.pack(fill="x", pady=(0, 10))

        # Direct Collaborators Sub-Section
        self.collab_sec_lbl = ctk.CTkLabel(det_inner, text="Direct Collaborators (0)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT)
        self.collab_sec_lbl.pack(anchor="w", pady=(2, 2))

        self.collab_chips_frame = ctk.CTkFrame(det_inner, fg_color="transparent")
        self.collab_chips_frame.pack(fill="x", pady=(0, 8))

        # Research Areas Sub-Section
        self.areas_sec_lbl = ctk.CTkLabel(det_inner, text="Research Areas", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT)
        self.areas_sec_lbl.pack(anchor="w", pady=(2, 2))

        self.areas_chips_frame = ctk.CTkFrame(det_inner, fg_color="transparent")
        self.areas_chips_frame.pack(fill="x", pady=(0, 8))

        # Skills Sub-Section
        self.skills_sec_lbl = ctk.CTkLabel(det_inner, text="Skills & Expertise", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT)
        self.skills_sec_lbl.pack(anchor="w", pady=(2, 2))

        self.skills_chips_frame = ctk.CTkFrame(det_inner, fg_color="transparent")
        self.skills_chips_frame.pack(fill="x", pady=(0, 4))

        # --- SECTION 2: COLLABORATION ANALYSIS (A/B SELECTION & ALGORITHMS) ---
        analysis_card = create_card(self.control_scroll, fg_color=Theme.WHITE)
        analysis_card.pack(fill="x", pady=(0, 12))

        ana_inner = ctk.CTkFrame(analysis_card, fg_color="transparent")
        ana_inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(ana_inner, text="COLLABORATION ANALYSIS", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(ana_inner, text="Graph Path & Traversal Algorithms", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 8))

        # Researcher A dropdown
        ctk.CTkLabel(ana_inner, text="Researcher A (Source Scholar)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        self.src_var = ctk.StringVar(value=self.dropdown_labels[0] if self.dropdown_labels else "No researchers")
        self.src_menu = ctk.CTkOptionMenu(
            ana_inner,
            variable=self.src_var,
            values=self.dropdown_labels if self.dropdown_labels else ["No researchers"],
            height=34,
            corner_radius=Theme.RADIUS_INPUT,
            fg_color=Theme.ACADEMIC_BLUE,
            command=self._on_src_dropdown_change
        )
        self.src_menu.pack(fill="x", pady=(0, 8))

        # Swap button
        swap_bar = ctk.CTkFrame(ana_inner, fg_color="transparent")
        swap_bar.pack(fill="x", pady=(0, 4))
        swap_btn = ctk.CTkButton(
            swap_bar,
            text="⇄ Swap A and B",
            command=self._swap_researchers_a_and_b,
            width=110,
            height=26,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.MUTED_BG,
            text_color=Theme.NAVY,
            hover_color="#E2E8F0",
            font=Theme.FONT_CAPTION
        )
        swap_btn.pack(side="right")

        # Researcher B dropdown
        ctk.CTkLabel(ana_inner, text="Researcher B (Target Scholar)", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
        second_val = self.dropdown_labels[1] if len(self.dropdown_labels) > 1 else (self.dropdown_labels[0] if self.dropdown_labels else "")
        self.tgt_var = ctk.StringVar(value=second_val)
        self.tgt_menu = ctk.CTkOptionMenu(
            ana_inner,
            variable=self.tgt_var,
            values=self.dropdown_labels if self.dropdown_labels else ["No researchers"],
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
            text="⚡ Find Shortest Collaboration Path (BFS)",
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

        # 4. Connected Components / Research Clusters (DFS)
        clusters_btn = create_secondary_button(
            btn_box,
            text="🧩 Detect Research Clusters (Components)",
            command=self._run_clusters,
            height=34
        )
        clusters_btn.pack(fill="x", pady=3)

        # 5. Reset Graph to Default State
        reset_btn = create_secondary_button(
            btn_box,
            text="🔄 Reset Graph to Default State",
            command=self._reset_network_view,
            height=34
        )
        reset_btn.pack(fill="x", pady=3)

        # --- SECTION 3: ALGORITHM RESULT PANEL ---
        self.result_card = create_card(self.control_scroll, fg_color=Theme.WHITE)
        self.result_card.pack(fill="x", pady=(0, 12))

        self.res_inner = ctk.CTkFrame(self.result_card, fg_color="transparent")
        self.res_inner.pack(fill="x", padx=14, pady=12)

        res_head = ctk.CTkFrame(self.res_inner, fg_color="transparent")
        res_head.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(res_head, text="ALGORITHM RESULT", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(side="left")
        self.algo_badge = create_badge(res_head, text="Ready", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE)
        self.algo_badge.pack(side="right")

        self.res_title = ctk.CTkLabel(self.res_inner, text="Select researchers & execute an algorithm", font=Theme.FONT_SECTION, text_color=Theme.NAVY)
        self.res_title.pack(anchor="w", pady=(0, 4))

        # Dynamic container for rich algorithm output widgets
        self.res_body_container = ctk.CTkFrame(self.res_inner, fg_color="transparent")
        self.res_body_container.pack(fill="x", pady=(4, 0))

        # Default message
        self._set_default_result_message()

        # --- SECTION 4: DATA STRUCTURE & ALGORITHMIC EXPLANATION PANEL ---
        ds_card = create_card(self.control_scroll, fg_color="#F8FAFC")
        ds_card.pack(fill="x", pady=(0, 4))

        ds_inner = ctk.CTkFrame(ds_card, fg_color="transparent")
        ds_inner.pack(fill="x", padx=14, pady=12)

        ctk.CTkLabel(ds_inner, text="DATA STRUCTURE & COMPLEXITY", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(ds_inner, text="Graph ADT (Adjacency List)", font=Theme.FONT_SECTION, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 6))

        ds_desc = (
            "• Representation: Adjacency List Dictionary (O(V + E) space)\n"
            "• Node (Vertex): Researcher profile in MySQL database\n"
            "• Edge: Academic Collaboration (Co-Authorship)\n"
            "• Edge Weight: Joint publication count (co-authored papers)\n\n"
            "ALGORITHMS IMPLEMENTED:\n"
            "• BFS (Breadth-First Search): Explores neighbors layer-by-layer using a FIFO queue; guarantees the shortest collaboration path (O(V + E) time).\n"
            "• DFS (Depth-First Search): Explores deep collaborative branches recursively using LIFO stack order.\n"
            "• Connected Components: Partitions the campus network into disjoint collaboration clusters using DFS."
        )
        ctk.CTkLabel(
            ds_inner,
            text=ds_desc,
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT,
            wraplength=340,
            justify="left"
        ).pack(anchor="w")

    def _set_default_result_message(self):
        for child in self.res_body_container.winfo_children():
            child.destroy()
        lbl = ctk.CTkLabel(
            self.res_body_container,
            text="Click 'Find Shortest Collaboration Path' to calculate the degrees of separation between Researcher A and Researcher B, or run BFS/DFS traversals.",
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=340,
            justify="left"
        )
        lbl.pack(anchor="w")

    # =========================================================================
    # GRAPH LAYOUT CALCULATION (COMPONENT-AWARE + ANTI-COLLISION RELAXATION)
    # =========================================================================

    def _calculate_node_layout(self):
        """
        Calculates 2D positions for all researcher nodes.
        Separates the connected collaboration network from disconnected/isolated researchers
        to prevent any overlapping, crowding, or squishing.
        """
        nodes = self.graph_data.get("nodes", [])
        if not nodes:
            return

        w = self.canvas.winfo_width() or self.canvas_width
        h = self.canvas.winfo_height() or self.canvas_height
        self.canvas_width = max(w, 450)
        self.canvas_height = max(h, 400)

        # 1. Compute normalized layout for connected subgraph
        self.normalized_connected.clear()
        if self.connected_node_ids:
            if nx is not None:
                subG = nx.Graph()
                for nid in self.connected_node_ids:
                    subG.add_node(nid)
                for e in self.graph_data.get("edges", []):
                    u, v = e["source"], e["target"]
                    if u in self.connected_node_ids and v in self.connected_node_ids:
                        subG.add_edge(u, v, weight=e.get("weight", 1))

                # Generous k=1.3 allows connected nodes to expand
                raw_pos = nx.spring_layout(subG, k=1.35, iterations=120, seed=42)
                xs = [float(p[0]) for p in raw_pos.values()]
                ys = [float(p[1]) for p in raw_pos.values()]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                span_x = max(max_x - min_x, 1e-6)
                span_y = max(max_y - min_y, 1e-6)

                for nid, (rx, ry) in raw_pos.items():
                    nx_val = (float(rx) - min_x) / span_x
                    ny_val = (float(ry) - min_y) / span_y
                    self.normalized_connected[nid] = (nx_val, ny_val)
            else:
                # Fallback circular layout for connected nodes
                num_c = len(self.connected_node_ids)
                for idx, nid in enumerate(self.connected_node_ids):
                    angle = 2 * math.pi * idx / num_c
                    r = 0.42 if (idx % 2 == 0) else 0.35
                    nx_val = 0.5 + r * math.cos(angle)
                    ny_val = 0.5 + r * math.sin(angle)
                    self.normalized_connected[nid] = (nx_val, ny_val)

        self._scale_layout_to_canvas()

    def _scale_layout_to_canvas(self):
        """Map normalized layout to screen coordinates with guaranteed minimum node distances."""
        w = self.canvas_width
        h = self.canvas_height

        margin_x = 48.0
        margin_y = 48.0

        # Partition canvas: if isolated nodes exist, allocate right column for them
        has_isolated = len(self.isolated_node_ids) > 0
        if has_isolated:
            main_w = w * 0.73
            iso_w = w - main_w
        else:
            main_w = float(w)
            iso_w = 0.0

        usable_main_w = max(120.0, main_w - margin_x - 30.0)
        usable_main_h = max(120.0, h - 2 * margin_y)

        self.node_positions.clear()

        # 1. Place connected nodes in the primary area
        pts: Dict[int, List[float]] = {}
        for nid, (nx_val, ny_val) in self.normalized_connected.items():
            screen_x = margin_x + nx_val * usable_main_w
            screen_y = margin_y + ny_val * usable_main_h
            pts[nid] = [screen_x, screen_y]

        # 2. Anti-collision relaxation: enforce minimum 80px distance between connected nodes
        min_allowed = 80.0
        conn_keys = list(pts.keys())
        for _ in range(45):
            moved = False
            for i in range(len(conn_keys)):
                for j in range(i + 1, len(conn_keys)):
                    n1 = conn_keys[i]
                    n2 = conn_keys[j]
                    dx = pts[n1][0] - pts[n2][0]
                    dy = pts[n1][1] - pts[n2][1]
                    dist = math.hypot(dx, dy)
                    if dist < 1e-4:
                        dx, dy = 1.0, 1.0
                        dist = math.hypot(dx, dy)
                    if dist < min_allowed:
                        moved = True
                        overlap = (min_allowed - dist) * 0.5
                        ux, uy = dx / dist, dy / dist
                        pts[n1][0] += ux * overlap * 0.5
                        pts[n1][1] += uy * overlap * 0.5
                        pts[n2][0] -= ux * overlap * 0.5
                        pts[n2][1] -= uy * overlap * 0.5

            # Clamp within main network bounds
            for nid in conn_keys:
                pts[nid][0] = max(margin_x, min(pts[nid][0], margin_x + usable_main_w))
                pts[nid][1] = max(margin_y, min(pts[nid][1], margin_y + usable_main_h))

            if not moved:
                break

        for nid, p in pts.items():
            self.node_positions[nid] = (float(p[0]), float(p[1]))

        # 3. Place isolated/disconnected nodes in an organized right-hand shelf
        if has_isolated:
            iso_start_x = main_w + 12.0
            iso_usable_w = max(60.0, iso_w - 24.0)
            cols = 2 if len(self.isolated_node_ids) > 5 else 1
            col_w = iso_usable_w / cols
            total_rows = math.ceil(len(self.isolated_node_ids) / cols)
            row_h = usable_main_h / max(1, total_rows)

            for idx, nid in enumerate(self.isolated_node_ids):
                col = idx % cols
                row = idx // cols
                ix = iso_start_x + (col + 0.5) * col_w
                iy = margin_y + (row + 0.5) * row_h
                self.node_positions[nid] = (float(ix), float(iy))

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

    def _format_node_label(self, full_name: str, nid: int) -> str:
        """Create a clean, human-readable label that never overflows or duplicates."""
        parts = full_name.split()
        if len(parts) == 1:
            return full_name[:14]
        if parts[0] in ("Dr.", "Prof.", "Mr.", "Ms.", "Mrs."):
            if len(parts) >= 3:
                return f"{parts[0]} {parts[1][0]}. {parts[2]}"
            return f"{parts[0]} {parts[1]}"
        if len(parts) == 2:
            return f"{parts[0]} {parts[1][0]}."
        return f"{parts[0]} {parts[-1][0]}."

    def _draw_graph(self):
        """Renders edges, weight tags, nodes, halos, collaborator rings, and shortest paths."""
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

        # 1. DRAW SECTION DIVIDERS & LABELS (IF ISOLATED NODES EXIST)
        if self.isolated_node_ids:
            divider_x = self.canvas_width * 0.73
            # Subtle dashed vertical divider
            self.canvas.create_line(
                divider_x, 24, divider_x, self.canvas_height - 20,
                fill="#E2E8F0", width=1.2, dash=(4, 4)
            )
            # Section titles
            self.canvas.create_text(
                45, 20,
                text=f"COLLABORATION NETWORK ({len(self.connected_node_ids)} Researchers · {len(edges)} Edges)",
                anchor="w",
                fill=Theme.SECONDARY_TEXT,
                font=(Theme.FONT_FAMILY, 8, "bold")
            )
            self.canvas.create_text(
                divider_x + 12, 20,
                text=f"INDEPENDENT SCHOLARS ({len(self.isolated_node_ids)})",
                anchor="w",
                fill=Theme.SECONDARY_TEXT,
                font=(Theme.FONT_FAMILY, 8, "bold")
            )

        # 2. DRAW EDGES
        for edge in edges:
            u, v = edge["source"], edge["target"]
            if u not in self.node_positions or v not in self.node_positions:
                continue

            x1, y1 = self.node_positions[u]
            x2, y2 = self.node_positions[v]
            pair = (min(u, v), max(u, v))
            weight = edge.get("weight", 1)

            # Edge Styling Priority: Shortest Path > Direct Collaborator > Normal
            if pair in self.highlighted_path_edges:
                line_color = Theme.PURPLE
                line_width = 3.8
            elif (self.selected_node_id == u and v in self.highlighted_collaborators) or \
                 (self.selected_node_id == v and u in self.highlighted_collaborators):
                line_color = "#0284C7"  # Sky blue
                line_width = 2.6
            else:
                # Subtle slate gray, visible but elegant
                line_color = "#CBD5E1"
                line_width = 1.6 + min(weight - 1, 3) * 0.4

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=line_color,
                width=line_width,
                capstyle="round"
            )

            # Draw paper count badge at edge midpoint for highlighted edges or multi-paper collaborations
            if pair in self.highlighted_path_edges or (self.selected_node_id in (u, v) and (u in self.highlighted_collaborators or v in self.highlighted_collaborators)) or weight > 1:
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                pill_bg = "#F3E8FF" if pair in self.highlighted_path_edges else "#F1F5F9"
                pill_fg = Theme.PURPLE if pair in self.highlighted_path_edges else Theme.DARK_TEXT
                self.canvas.create_oval(
                    mx - 9, my - 7, mx + 9, my + 7,
                    fill=pill_bg, outline="#CBD5E1", width=1
                )
                self.canvas.create_text(
                    mx, my,
                    text=str(weight),
                    fill=pill_fg,
                    font=(Theme.FONT_FAMILY, 7, "bold")
                )

        # 3. DRAW NODES
        node_radius = 17.0

        for node in nodes:
            nid = node["id"]
            if nid not in self.node_positions:
                continue

            x, y = self.node_positions[nid]

            is_current_user = (nid == self.current_researcher_id)
            is_selected = (nid == self.selected_node_id)
            is_target = (nid == self.target_node_id)
            is_collaborator = (nid in self.highlighted_collaborators)
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
            elif is_target:
                # Violet glow for Target Researcher B
                self.canvas.create_oval(
                    x - node_radius - 7, y - node_radius - 7,
                    x + node_radius + 7, y + node_radius + 7,
                    fill="#F3E8FF", outline="#9333EA", width=2.5
                )
            elif is_in_path:
                # Purple glow for Shortest Path
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#EDE9FE", outline=Theme.PURPLE, width=2.2
                )
            elif is_collaborator:
                # Sky Blue glow for Direct Collaborators
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#E0F2FE", outline="#0284C7", width=2.0
                )
            elif is_in_cluster:
                # Emerald glow for Cluster Members
                self.canvas.create_oval(
                    x - node_radius - 6, y - node_radius - 6,
                    x + node_radius + 6, y + node_radius + 6,
                    fill="#DCFCE7", outline="#16A34A", width=2.0
                )
            elif is_current_user:
                # Green ring for Current Logged-in User
                self.canvas.create_oval(
                    x - node_radius - 5, y - node_radius - 5,
                    x + node_radius + 5, y + node_radius + 5,
                    fill="#F0FDF4", outline="#16A34A", width=1.8
                )

            # NODE FILL COLOR (Matches legend strictly)
            if is_selected:
                fill_color = "#D97706"  # Amber-600
                border_color = Theme.WHITE
            elif is_target:
                fill_color = "#7E22CE"  # Violet-700
                border_color = Theme.WHITE
            elif is_in_path:
                fill_color = "#6D28D9"  # Purple-700
                border_color = Theme.WHITE
            elif is_collaborator:
                fill_color = "#0284C7"  # Sky Blue
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
                width=2.0
            )

            # Center Initials
            initials = "".join([w[0] for w in node["name"].split() if w])[:2].upper()
            self.canvas.create_text(
                x, y,
                text=initials,
                fill=Theme.WHITE,
                font=(Theme.FONT_FAMILY, 9, "bold")
            )

            # Role Badges: "A" on top-left of selected, "B" on top-right of target
            if is_selected:
                bx, by = x - node_radius + 1, y - node_radius + 1
                self.canvas.create_oval(bx - 7, by - 7, bx + 7, by + 7, fill="#B45309", outline=Theme.WHITE, width=1.5)
                self.canvas.create_text(bx, by, text="A", fill=Theme.WHITE, font=(Theme.FONT_FAMILY, 7, "bold"))
            elif is_target:
                bx, by = x + node_radius - 1, y - node_radius + 1
                self.canvas.create_oval(bx - 7, by - 7, bx + 7, by + 7, fill="#581C87", outline=Theme.WHITE, width=1.5)
                self.canvas.create_text(bx, by, text="B", fill=Theme.WHITE, font=(Theme.FONT_FAMILY, 7, "bold"))

            # Traversal Step Badge (if BFS/DFS traversal was run)
            if traversal_step and not is_selected:
                badge_x = x + node_radius + 2
                badge_y = y - node_radius + 2
                self.canvas.create_oval(
                    badge_x - 8, badge_y - 8,
                    badge_x + 8, badge_y + 8,
                    fill="#10B981", outline=Theme.WHITE, width=1.5
                )
                self.canvas.create_text(
                    badge_x, badge_y,
                    text=str(traversal_step),
                    fill=Theme.WHITE,
                    font=(Theme.FONT_FAMILY, 8, "bold")
                )

            # Current User Star Badge
            if is_current_user and not is_selected and not is_target and not traversal_step:
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

            # Format Readable Label Below Node
            display_name = self._format_node_label(node["name"], nid)
            if is_selected:
                text_color = "#92400E"
                font_weight = "bold"
            elif is_target:
                text_color = "#6B21A8"
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

            label_y = y + node_radius + 11
            # White mask pill behind label prevents any edge lines from cutting through text
            approx_half_w = len(display_name) * 3.3 + 4
            self.canvas.create_rectangle(
                x - approx_half_w, label_y - 7,
                x + approx_half_w, label_y + 7,
                fill=Theme.WHITE, outline=""
            )
            self.canvas.create_text(
                x, label_y,
                text=display_name,
                fill=text_color,
                font=(Theme.FONT_FAMILY, 8, font_weight)
            )

        # 4. DRAW HOVER TOOLTIP (IF A NODE IS HOVERED)
        if self.hovered_node_id and self.hovered_node_id in self.nodes_by_id:
            self._draw_hover_tooltip(self.hovered_node_id)

    def _draw_hover_tooltip(self, nid: int):
        """Draw an elegant canvas tooltip near the hovered node with full profile context."""
        node = self.nodes_by_id[nid]
        x, y = self.node_positions.get(nid, (0, 0))

        full_name = node.get("name", "Researcher")
        desig = node.get("designation") or "Researcher"
        dept = node.get("department") or ""
        inst = node.get("institution") or "CampusX"
        neighbors = self.adjacency_map.get(nid, [])
        collab_count = len(neighbors)
        citations = node.get("citation_count", 0)

        line1 = full_name
        line2 = f"{desig} · {dept}" if dept else desig
        line3 = f"🏛️ {inst}"
        line4 = f"🤝 {collab_count} Direct Collaborators  ·  📑 {citations} Citations"
        line5 = "Left-click: Select A  ·  Right-click: Set B"

        lines = [line1, line2, line3, line4, line5]

        # Calculate tooltip box placement
        box_w = 260.0
        box_h = 92.0
        bx = min(x + 20, self.canvas_width - box_w - 10)
        by = min(y - 30, self.canvas_height - box_h - 10)
        if bx < 10:
            bx = 10
        if by < 10:
            by = y + 25

        # Background card with shadow effect
        self.canvas.create_rectangle(bx + 2, by + 2, bx + box_w + 2, by + box_h + 2, fill="#E2E8F0", outline="")
        self.canvas.create_rectangle(bx, by, bx + box_w, by + box_h, fill=Theme.WHITE, outline=Theme.BORDER, width=1.2)

        # Text inside tooltip
        self.canvas.create_text(bx + 10, by + 14, text=line1, anchor="w", fill=Theme.NAVY, font=(Theme.FONT_FAMILY, 9, "bold"))
        self.canvas.create_text(bx + 10, by + 30, text=line2, anchor="w", fill=Theme.DARK_TEXT, font=(Theme.FONT_FAMILY, 8))
        self.canvas.create_text(bx + 10, by + 46, text=line3, anchor="w", fill=Theme.SECONDARY_TEXT, font=(Theme.FONT_FAMILY, 7))
        self.canvas.create_text(bx + 10, by + 63, text=line4, anchor="w", fill="#0369A1", font=(Theme.FONT_FAMILY, 7, "bold"))
        self.canvas.create_text(bx + 10, by + 79, text=line5, anchor="w", fill="#64748B", font=(Theme.FONT_FAMILY, 7, "italic"))

    # =========================================================================
    # INTERACTIVE CANVAS EVENTS (LEFT CLICK, RIGHT CLICK, HOVER)
    # =========================================================================

    def _find_node_at_coords(self, cx: float, cy: float) -> Optional[int]:
        clicked_id = None
        min_dist = float("inf")
        for nid, (x, y) in self.node_positions.items():
            dist = math.hypot(cx - x, cy - y)
            if dist <= 26.0 and dist < min_dist:
                min_dist = dist
                clicked_id = nid
        return clicked_id

    def _on_canvas_left_click(self, event):
        """Left-click selects researcher as Researcher A (Source)."""
        clicked_id = self._find_node_at_coords(event.x, event.y)
        if clicked_id:
            self._select_researcher_by_id(clicked_id, update_dropdown=True)

    def _on_canvas_right_click(self, event):
        """Right-click designates researcher as Researcher B (Target)."""
        clicked_id = self._find_node_at_coords(event.x, event.y)
        if clicked_id:
            self._set_target_researcher_by_id(clicked_id, update_dropdown=True)

    def _on_canvas_motion(self, event):
        """Changes mouse cursor and shows live hover tooltip."""
        hovered = self._find_node_at_coords(event.x, event.y)
        if hovered != self.hovered_node_id:
            self.hovered_node_id = hovered
            self.canvas.configure(cursor="hand2" if hovered else "")
            self._draw_graph()

    def _on_canvas_leave(self, event):
        if self.hovered_node_id is not None:
            self.hovered_node_id = None
            self._draw_graph()

    # =========================================================================
    # RESEARCHER SELECTION & DETAILS UPDATE
    # =========================================================================

    def _select_researcher_by_id(self, researcher_id: int, update_dropdown: bool = False):
        """
        Activates a researcher as Researcher A (Source):
        1. Highlights the node on the graph in Amber.
        2. Identifies and highlights direct collaborators in Sky Blue.
        3. Updates the Selected Researcher details panel with live MySQL data.
        4. Updates the Overview counter card.
        5. Synchronizes the Researcher A dropdown menu.
        """
        if researcher_id not in self.nodes_by_id:
            return

        self.selected_node_id = researcher_id
        res_data = self.nodes_by_id[researcher_id]
        name = res_data["name"]

        if update_dropdown and researcher_id in self.id_to_label:
            self.src_var.set(self.id_to_label[researcher_id])

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

    def _set_target_researcher_by_id(self, researcher_id: int, update_dropdown: bool = False):
        """Designates a researcher as Researcher B (Target) and highlights in Violet."""
        if researcher_id not in self.nodes_by_id:
            return

        self.target_node_id = researcher_id
        if update_dropdown and researcher_id in self.id_to_label:
            self.tgt_var.set(self.id_to_label[researcher_id])

        # Clear old path highlights when target changes
        self.highlighted_path_nodes.clear()
        self.highlighted_path_edges.clear()
        self._draw_graph()

    def _set_current_selected_as_target(self):
        """Button action in researcher details card to set currently viewed scholar as Target B."""
        if self.selected_node_id:
            self._set_target_researcher_by_id(self.selected_node_id, update_dropdown=True)

    def _swap_researchers_a_and_b(self):
        """Swap Researcher A and Researcher B selections."""
        if not self.selected_node_id or not self.target_node_id:
            return

        old_a = self.selected_node_id
        old_b = self.target_node_id

        self.target_node_id = old_a
        if old_a in self.id_to_label:
            self.tgt_var.set(self.id_to_label[old_a])

        self._select_researcher_by_id(old_b, update_dropdown=True)

    def _update_details_panel(self, researcher_id: int, node_data: Dict[str, Any], neighbors: List[Tuple[int, int]]):
        """Populate the Selected Researcher panel with full academic profile, wrapped chips, and non-clipping text."""
        self.det_name_lbl.configure(text=node_data.get("name", "Researcher"))

        # Fetch detailed profile from API/Service for areas and skills
        detailed_profile: Dict[str, Any] = {}
        try:
            detailed_profile = api_client.get_researcher_detail(researcher_id) or {}
        except Exception:
            try:
                detailed_profile = ResearchService.get_researcher_detail(researcher_id) or {}
            except Exception:
                detailed_profile = {}

        desig = detailed_profile.get("designation") or node_data.get("designation", "")
        dept = detailed_profile.get("department_name") or node_data.get("department", "")
        inst = detailed_profile.get("institution_name") or node_data.get("institution", "")

        meta_parts = []
        if desig and desig.strip():
            meta_parts.append(desig.strip())
        if dept and dept.strip():
            meta_parts.append(dept.strip())
        first_line = " · ".join(meta_parts) if meta_parts else "Academic Scholar"
        inst_line = inst.strip() if (inst and inst.strip()) else "CampusX Academic Network"

        self.det_meta_lbl.configure(text=f"{first_line}\n🏛️ {inst_line}")

        # Metrics row
        for child in self.metrics_row.winfo_children():
            child.destroy()

        cit_cnt = detailed_profile.get("citation_count", node_data.get("citation_count", 0))
        pub_cnt = len(detailed_profile.get("publications", []))
        create_badge(self.metrics_row, text=f"📑 {cit_cnt} Citations", bg_color="#F1F5F9", text_color=Theme.NAVY).pack(side="left", padx=(0, 4))
        create_badge(self.metrics_row, text=f"📚 {pub_cnt} Papers", bg_color="#F1F5F9", text_color=Theme.NAVY).pack(side="left", padx=4)
        create_badge(self.metrics_row, text=f"🤝 {len(neighbors)} Co-authors", bg_color="#E0F2FE", text_color="#0369A1").pack(side="left", padx=4)

        # 1. Direct Collaborators List (Non-clipping, wrapped chip layout)
        num_collabs = len(neighbors)
        self.collab_sec_lbl.configure(text=f"Direct Collaborators ({num_collabs})")

        for child in self.collab_chips_frame.winfo_children():
            child.destroy()

        if neighbors:
            curr_row = ctk.CTkFrame(self.collab_chips_frame, fg_color="transparent")
            curr_row.pack(fill="x", pady=2)
            curr_w = 0.0

            for neighbor_id, papers in neighbors:
                collab_name = self.id_to_name.get(neighbor_id, f"Researcher #{neighbor_id}")
                btn_text = f"{collab_name} ({papers} 📄)"
                approx_w = len(btn_text) * 7.5 + 26.0

                if curr_w > 0 and (curr_w + approx_w > 330.0):
                    curr_row = ctk.CTkFrame(self.collab_chips_frame, fg_color="transparent")
                    curr_row.pack(fill="x", pady=2)
                    curr_w = 0.0

                btn = ctk.CTkButton(
                    curr_row,
                    text=btn_text,
                    command=lambda nid=neighbor_id: self._select_researcher_by_id(nid, update_dropdown=True),
                    height=26,
                    corner_radius=13,
                    fg_color="#E0F2FE",
                    text_color="#0369A1",
                    hover_color="#BAE6FD",
                    font=Theme.FONT_CAPTION
                )
                btn.pack(side="left", padx=3, pady=2)
                curr_w += approx_w
        else:
            ctk.CTkLabel(
                self.collab_chips_frame,
                text="ℹ️ No direct collaborators recorded in the campus network yet.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=340,
                justify="left"
            ).pack(anchor="w")

        # 2. Research Areas (Non-clipping, wrapped chip layout)
        for child in self.areas_chips_frame.winfo_children():
            child.destroy()

        areas = detailed_profile.get("areas", []) or node_data.get("areas", [])
        if areas:
            curr_row = ctk.CTkFrame(self.areas_chips_frame, fg_color="transparent")
            curr_row.pack(fill="x", pady=2)
            curr_w = 0.0

            for area in areas:
                area_text = area.get("name") if isinstance(area, dict) else str(area)
                approx_w = len(area_text) * 7.2 + 22.0

                if curr_w > 0 and (curr_w + approx_w > 330.0):
                    curr_row = ctk.CTkFrame(self.areas_chips_frame, fg_color="transparent")
                    curr_row.pack(fill="x", pady=2)
                    curr_w = 0.0

                create_badge(
                    curr_row,
                    text=area_text,
                    bg_color="#EEF2FF",
                    text_color=Theme.ACADEMIC_BLUE,
                    font=Theme.FONT_CAPTION
                ).pack(side="left", padx=3, pady=2)
                curr_w += approx_w
        else:
            ctk.CTkLabel(
                self.areas_chips_frame,
                text="No research areas listed.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w")

        # 3. Skills (Non-clipping, wrapped chip layout)
        for child in self.skills_chips_frame.winfo_children():
            child.destroy()

        skills = detailed_profile.get("skills", [])
        if skills:
            curr_row = ctk.CTkFrame(self.skills_chips_frame, fg_color="transparent")
            curr_row.pack(fill="x", pady=2)
            curr_w = 0.0

            for skill in skills:
                skill_name = skill.get("name") if isinstance(skill, dict) else str(skill)
                approx_w = len(skill_name) * 7.2 + 22.0

                if curr_w > 0 and (curr_w + approx_w > 330.0):
                    curr_row = ctk.CTkFrame(self.skills_chips_frame, fg_color="transparent")
                    curr_row.pack(fill="x", pady=2)
                    curr_w = 0.0

                create_badge(
                    curr_row,
                    text=skill_name,
                    bg_color="#F1F5F9",
                    text_color=Theme.NAVY,
                    font=Theme.FONT_CAPTION
                ).pack(side="left", padx=3, pady=2)
                curr_w += approx_w
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

    def _on_src_dropdown_change(self, selected_label: str):
        nid = self.label_to_id.get(selected_label)
        if nid:
            self._select_researcher_by_id(nid, update_dropdown=False)

    def _on_tgt_dropdown_change(self, selected_label: str):
        nid = self.label_to_id.get(selected_label)
        if nid:
            self._set_target_researcher_by_id(nid, update_dropdown=False)

    # =========================================================================
    # ALGORITHM 1: SHORTEST COLLABORATION PATH (BFS)
    # =========================================================================

    def _run_bfs_shortest_path(self):
        """Calculate and highlight the real shortest collaboration path using BFS."""
        src_id = self.selected_node_id or self.label_to_id.get(self.src_var.get())
        tgt_id = self.target_node_id or self.label_to_id.get(self.tgt_var.get())

        if not src_id or not tgt_id:
            self.algo_badge.configure(text="Invalid Selection", fg_color="#FEE2E2", text_color="#B91C1C")
            self.res_title.configure(text="Select Both Researchers")
            self._render_plain_result("Please select valid researchers from both dropdown menus above.")
            return

        self.target_node_id = tgt_id

        # Execute BFS algorithm via API / Service
        try:
            res = api_client.run_bfs(src_id, tgt_id)
        except Exception:
            try:
                res = NetworkService.execute_bfs_path(src_id, tgt_id)
            except Exception as e:
                self.algo_badge.configure(text="Execution Error", fg_color="#FEE2E2", text_color="#B91C1C")
                self.res_title.configure(text="BFS Error")
                self._render_plain_result(f"An error occurred executing BFS: {str(e)}")
                return

        src_name = self.id_to_name.get(src_id, f"Researcher #{src_id}")
        tgt_name = self.id_to_name.get(tgt_id, f"Researcher #{tgt_id}")

        for child in self.res_body_container.winfo_children():
            child.destroy()

        if src_id == tgt_id:
            self.highlighted_path_nodes = {src_id}
            self.highlighted_path_edges.clear()
            self._draw_graph()

            self.algo_badge.configure(text="Self-Connection", fg_color="#FEF3C7", text_color="#B45309")
            self.res_title.configure(text="Same Researcher Selected (0 Hops)")

            ctk.CTkLabel(
                self.res_body_container,
                text=f"Researcher A and Researcher B are the same scholar ({src_name}).",
                font=Theme.FONT_BODY,
                text_color=Theme.NAVY
            ).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                self.res_body_container,
                text="Degrees of Separation: 0\nCollaboration Edges Traversed: 0",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT
            ).pack(anchor="w")
            return

        if res.get("found"):
            path = res.get("path_ids", [])
            hops = res.get("hops", len(path) - 1)
            edges_info = res.get("edges", [])

            self.highlighted_path_nodes = set(path)
            self.highlighted_path_edges = {
                (min(path[i], path[i + 1]), max(path[i], path[i + 1]))
                for i in range(len(path) - 1)
            }
            self.highlighted_traversal_steps.clear()
            self.highlighted_cluster_nodes.clear()
            self._draw_graph()

            self.algo_badge.configure(text="BFS Path Found", fg_color="#F3E8FF", text_color=Theme.PURPLE)
            self.res_title.configure(text=f"Shortest Path Found ({hops} Degree{'s' if hops != 1 else ''} of Separation)")

            # Summary Metric Badges Frame
            metrics_box = ctk.CTkFrame(self.res_body_container, fg_color="transparent")
            metrics_box.pack(fill="x", pady=(0, 8))
            create_badge(metrics_box, text=f"Edges Traversed: {hops}", bg_color="#F3E8FF", text_color=Theme.PURPLE).pack(side="left", padx=(0, 4))
            create_badge(metrics_box, text=f"Total Nodes: {len(path)} Scholars", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=4)
            total_papers = sum(e.get("paper_count", 1) for e in edges_info)
            create_badge(metrics_box, text=f"Joint Papers: {total_papers}", bg_color="#E0F2FE", text_color="#0369A1").pack(side="left", padx=4)

            # Collaboration Chain Display
            ctk.CTkLabel(self.res_body_container, text="Collaboration Chain:", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
            chain_names = [self.id_to_name.get(nid, f"#{nid}") for nid in path]
            chain_box = ctk.CTkFrame(self.res_body_container, fg_color="#FAF5FF", corner_radius=6)
            chain_box.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                chain_box,
                text=" ➔ ".join(chain_names),
                font=Theme.FONT_BODY_BOLD,
                text_color=Theme.PURPLE,
                wraplength=330,
                justify="left"
            ).pack(anchor="w", padx=10, pady=8)

            # Step-by-step links
            ctk.CTkLabel(self.res_body_container, text="Step-by-Step Co-authorship Links:", font=Theme.FONT_BODY_BOLD, text_color=Theme.DARK_TEXT).pack(anchor="w", pady=(2, 2))
            for idx, edge in enumerate(edges_info):
                step_card = ctk.CTkFrame(self.res_body_container, fg_color="#F8FAFC", corner_radius=6)
                step_card.pack(fill="x", pady=2)
                step_text = f"Step {idx + 1}: {edge.get('from_name')} 🤝 {edge.get('to_name')}"
                paper_text = f"{edge.get('paper_count', 1)} joint paper(s)"
                ctk.CTkLabel(step_card, text=step_text, font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w", padx=8, pady=(4, 0))
                ctk.CTkLabel(step_card, text=f"Collaborative evidence: {paper_text}", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", padx=8, pady=(0, 4))

            # Graph Theory Rationale
            rationale_box = ctk.CTkFrame(self.res_body_container, fg_color="transparent")
            rationale_box.pack(fill="x", pady=(8, 0))
            ctk.CTkLabel(rationale_box, text="Graph Theory Rationale:", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w")
            ctk.CTkLabel(
                rationale_box,
                text="Breadth-First Search (BFS) explores all neighbors at degree d before moving to d+1, mathematically guaranteeing the shortest collaboration chain.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=340,
                justify="left"
            ).pack(anchor="w")

        else:
            # No path exists
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self._draw_graph()

            self.algo_badge.configure(text="No Path", fg_color="#FEE2E2", text_color="#B91C1C")
            self.res_title.configure(text="No Collaboration Path Exists")

            metrics_box = ctk.CTkFrame(self.res_body_container, fg_color="transparent")
            metrics_box.pack(fill="x", pady=(0, 8))
            create_badge(metrics_box, text="Edges Traversed: 0", bg_color="#FEE2E2", text_color="#B91C1C").pack(side="left", padx=(0, 4))
            create_badge(metrics_box, text="Connection: Disconnected", bg_color="#FEE2E2", text_color="#B91C1C").pack(side="left", padx=4)

            err_card = ctk.CTkFrame(self.res_body_container, fg_color="#FEF2F2", corner_radius=6)
            err_card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(
                err_card,
                text=f"No collaboration path exists between {src_name} and {tgt_name}.\n\n"
                     "They belong to disconnected research clusters in the academic graph. "
                     "No joint publications or transitive co-authors connect these two scholars.",
                font=Theme.FONT_BODY,
                text_color="#991B1B",
                wraplength=330,
                justify="left"
            ).pack(anchor="w", padx=10, pady=8)

            ctk.CTkLabel(
                self.res_body_container,
                text="Algorithmic Proof:\n"
                     "BFS completely traversed the reachable component of the source researcher without encountering the target. "
                     "Both nodes are displayed on the graph without inventing false collaboration edges.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=340,
                justify="left"
            ).pack(anchor="w")

    def _render_plain_result(self, text: str):
        for child in self.res_body_container.winfo_children():
            child.destroy()
        ctk.CTkLabel(
            self.res_body_container,
            text=text,
            font=Theme.FONT_BODY,
            text_color=Theme.DARK_TEXT,
            wraplength=340,
            justify="left"
        ).pack(anchor="w")

    # =========================================================================
    # ALGORITHM 2: BFS TRAVERSAL (LEVEL-BY-LEVEL EXPLORATION)
    # =========================================================================

    def _run_bfs_traversal(self):
        """Run level-by-level BFS traversal starting from Researcher A."""
        src_id = self.selected_node_id or self.label_to_id.get(self.src_var.get())

        if not src_id:
            return

        try:
            traversal = api_client.get_bfs_traversal(src_id)
        except Exception:
            try:
                traversal = NetworkService.get_bfs_traversal(src_id)
            except Exception as e:
                self.algo_badge.configure(text="Traversal Error", fg_color="#FEE2E2", text_color="#B91C1C")
                self.res_title.configure(text="BFS Traversal Error")
                self._render_plain_result(f"Error: {str(e)}")
                return

        for child in self.res_body_container.winfo_children():
            child.destroy()

        if traversal:
            self.highlighted_traversal_steps = {item["id"]: item["step"] for item in traversal}
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self.highlighted_cluster_nodes.clear()
            self._draw_graph()

            src_name = self.id_to_name.get(src_id, f"Researcher #{src_id}")
            max_depth = max(item.get("depth", 0) for item in traversal)

            self.algo_badge.configure(text="BFS Traversal", fg_color="#E0F2FE", text_color="#0369A1")
            self.res_title.configure(text=f"BFS Level-by-Level ({len(traversal)} Visited)")

            # Stats badges
            stat_box = ctk.CTkFrame(self.res_body_container, fg_color="transparent")
            stat_box.pack(fill="x", pady=(0, 8))
            create_badge(stat_box, text=f"Scholars Visited: {len(traversal)}", bg_color="#E0F2FE", text_color="#0369A1").pack(side="left", padx=(0, 4))
            create_badge(stat_box, text=f"Max Level: {max_depth}", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=4)

            ctk.CTkLabel(self.res_body_container, text=f"Starting Scholar: {src_name}", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 6))

            # Group researchers by depth/level
            levels: Dict[int, List[Dict[str, Any]]] = {}
            for item in traversal:
                d = item.get("depth", 0)
                levels.setdefault(d, []).append(item)

            for d in sorted(levels.keys()):
                lvl_card = ctk.CTkFrame(self.res_body_container, fg_color="#F8FAFC", corner_radius=6)
                lvl_card.pack(fill="x", pady=2)
                lvl_title = "Level 0 (Source)" if d == 0 else (f"Level {d} (Direct Co-authors)" if d == 1 else f"Level {d} (Mutual Collaborators)")
                ctk.CTkLabel(lvl_card, text=lvl_title, font=Theme.FONT_BODY_BOLD, text_color=Theme.ACADEMIC_BLUE).pack(anchor="w", padx=8, pady=(4, 2))

                members_text = ", ".join(f"[#{it['step']}] {it['name']}" for it in levels[d])
                ctk.CTkLabel(lvl_card, text=members_text, font=Theme.FONT_CAPTION, text_color=Theme.DARK_TEXT, wraplength=325, justify="left").pack(anchor="w", padx=8, pady=(0, 4))

            # Rationale
            ctk.CTkLabel(
                self.res_body_container,
                text="\nAlgorithmic Behavior:\n"
                     "BFS uses a FIFO (First-In, First-Out) queue. It completely explores all 1st-degree co-authors before branching to 2nd-degree mutual collaborators.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=340,
                justify="left"
            ).pack(anchor="w")

    # =========================================================================
    # ALGORITHM 3: DFS TRAVERSAL (DEEP EXPLORATION)
    # =========================================================================

    def _run_dfs_traversal(self):
        """Run recursive DFS traversal starting from Researcher A."""
        src_id = self.selected_node_id or self.label_to_id.get(self.src_var.get())

        if not src_id:
            return

        try:
            traversal = api_client.get_dfs_traversal(src_id)
        except Exception:
            try:
                traversal = NetworkService.get_dfs_traversal(src_id)
            except Exception as e:
                self.algo_badge.configure(text="Traversal Error", fg_color="#FEE2E2", text_color="#B91C1C")
                self.res_title.configure(text="DFS Traversal Error")
                self._render_plain_result(f"Error: {str(e)}")
                return

        for child in self.res_body_container.winfo_children():
            child.destroy()

        if traversal:
            self.highlighted_traversal_steps = {item["id"]: item["step"] for item in traversal}
            self.highlighted_path_nodes.clear()
            self.highlighted_path_edges.clear()
            self.highlighted_cluster_nodes.clear()
            self._draw_graph()

            src_name = self.id_to_name.get(src_id, f"Researcher #{src_id}")
            max_depth = max(item.get("depth", 0) for item in traversal)

            self.algo_badge.configure(text="DFS Deep Search", fg_color="#FEF3C7", text_color="#B45309")
            self.res_title.configure(text=f"DFS Exploration ({len(traversal)} Visited)")

            stat_box = ctk.CTkFrame(self.res_body_container, fg_color="transparent")
            stat_box.pack(fill="x", pady=(0, 8))
            create_badge(stat_box, text=f"Scholars Visited: {len(traversal)}", bg_color="#FEF3C7", text_color="#B45309").pack(side="left", padx=(0, 4))
            create_badge(stat_box, text=f"Max Branch Depth: {max_depth}", bg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE).pack(side="left", padx=4)

            ctk.CTkLabel(self.res_body_container, text=f"Starting Scholar: {src_name}", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w", pady=(0, 6))

            # Display sequential exploration
            for item in traversal[:10]:
                step_card = ctk.CTkFrame(self.res_body_container, fg_color="#F8FAFC", corner_radius=6)
                step_card.pack(fill="x", pady=2)
                d_indent = "  " * min(item.get("depth", 0), 4)
                ctk.CTkLabel(
                    step_card,
                    text=f"{d_indent}[Step {item['step']}] {item['name']} (Depth {item.get('depth', 0)})",
                    font=Theme.FONT_BODY_BOLD,
                    text_color=Theme.DARK_TEXT
                ).pack(anchor="w", padx=8, pady=4)

            if len(traversal) > 10:
                ctk.CTkLabel(self.res_body_container, text=f"... and {len(traversal) - 10} more scholars in branch.", font=Theme.FONT_CAPTION, text_color=Theme.SECONDARY_TEXT).pack(anchor="w", pady=2)

            ctk.CTkLabel(
                self.res_body_container,
                text="\nAlgorithmic Behavior:\n"
                     "DFS uses a LIFO (Last-In, First-Out) recursion stack. It plunges down a single collaborative branch as deeply as possible before backtracking.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=340,
                justify="left"
            ).pack(anchor="w")

    # =========================================================================
    # ALGORITHM 4: CONNECTED COMPONENTS / RESEARCH CLUSTERS
    # =========================================================================

    def _run_clusters(self):
        """Detect and display connected components (research clusters) across campus using DFS."""
        try:
            clusters = api_client.get_clusters()
        except Exception:
            try:
                clusters = NetworkService.get_research_clusters()
            except Exception as e:
                self.algo_badge.configure(text="Cluster Error", fg_color="#FEE2E2", text_color="#B91C1C")
                self.res_title.configure(text="Cluster Detection Error")
                self._render_plain_result(f"Error: {str(e)}")
                return

        self.clusters = clusters
        for child in self.res_body_container.winfo_children():
            child.destroy()

        self.algo_badge.configure(text="Connected Components", fg_color="#DCFCE7", text_color="#15803D")
        self.res_title.configure(text=f"Research Clusters ({len(clusters)} Components)")

        # Summary box
        stat_box = ctk.CTkFrame(self.res_body_container, fg_color="transparent")
        stat_box.pack(fill="x", pady=(0, 8))
        create_badge(stat_box, text=f"Components: {len(clusters)}", bg_color="#DCFCE7", text_color="#15803D").pack(side="left", padx=(0, 4))

        # Main cluster vs isolated
        main_cluster = clusters[0] if clusters else None
        if main_cluster and main_cluster.get("size", 0) > 1:
            mc_card = ctk.CTkFrame(self.res_body_container, fg_color="#F0FDF4", corner_radius=6)
            mc_card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(mc_card, text=f"Main Collaboration Network (Cluster #1)", font=Theme.FONT_BODY_BOLD, text_color="#166534").pack(anchor="w", padx=10, pady=(6, 2))
            lead = main_cluster.get("lead_researcher", "Campus Scholar")
            size = main_cluster.get("size", 0)
            areas = ", ".join(main_cluster.get("dominant_areas", [])[:3]) or "Interdisciplinary"
            ctk.CTkLabel(mc_card, text=f"• {size} Connected Researchers\n• Lead Scholar: {lead}\n• Dominant Fields: {areas}", font=Theme.FONT_CAPTION, text_color="#15803D", justify="left").pack(anchor="w", padx=10, pady=(0, 6))

            # Action button to highlight main cluster on canvas
            highlight_btn = ctk.CTkButton(
                mc_card,
                text="Highlight Main Network on Graph",
                command=lambda: self._highlight_cluster(main_cluster.get("member_ids", [])),
                height=24,
                corner_radius=4,
                fg_color="#16A34A",
                text_color=Theme.WHITE,
                font=Theme.FONT_CAPTION
            )
            highlight_btn.pack(anchor="w", padx=10, pady=(0, 8))

        isolated_count = sum(1 for c in clusters if c.get("size", 0) == 1)
        if isolated_count > 0:
            iso_card = ctk.CTkFrame(self.res_body_container, fg_color="#F8FAFC", corner_radius=6)
            iso_card.pack(fill="x", pady=(0, 8))
            ctk.CTkLabel(iso_card, text=f"Independent Scholars ({isolated_count} Components)", font=Theme.FONT_BODY_BOLD, text_color=Theme.NAVY).pack(anchor="w", padx=10, pady=(6, 2))
            ctk.CTkLabel(
                iso_card,
                text="Researchers who have not yet co-authored joint papers in this database. "
                     "Displayed cleanly on the right shelf without inventing false edges.",
                font=Theme.FONT_CAPTION,
                text_color=Theme.SECONDARY_TEXT,
                wraplength=325,
                justify="left"
            ).pack(anchor="w", padx=10, pady=(0, 6))

        # Algorithmic explanation
        ctk.CTkLabel(
            self.res_body_container,
            text="Graph Theory Rationale:\n"
                 "A connected component is an equivalence class under mutual reachability, detected across the entire graph using DFS component labeling.",
            font=Theme.FONT_CAPTION,
            text_color=Theme.SECONDARY_TEXT,
            wraplength=340,
            justify="left"
        ).pack(anchor="w")

        # Automatically highlight primary cluster
        if main_cluster:
            self._highlight_cluster(main_cluster.get("member_ids", []))

    def _highlight_cluster(self, member_ids: List[int]):
        self.highlighted_cluster_nodes = set(member_ids)
        self.highlighted_path_nodes.clear()
        self.highlighted_path_edges.clear()
        self.highlighted_traversal_steps.clear()
        self._draw_graph()

    # =========================================================================
    # RESET NETWORK VIEW
    # =========================================================================

    def _reset_network_view(self):
        """Restores the graph and algorithm panel to default normal state."""
        self.highlighted_path_nodes.clear()
        self.highlighted_path_edges.clear()
        self.highlighted_traversal_steps.clear()
        self.highlighted_cluster_nodes.clear()

        # Restore default Researcher A and B
        nodes = self.graph_data.get("nodes", [])
        default_a = self.current_researcher_id or (nodes[0]["id"] if nodes else None)
        default_b = None
        if nodes:
            for n in nodes:
                if n["id"] != default_a:
                    default_b = n["id"]
                    break
            if default_b is None:
                default_b = default_a

        if default_a:
            self._select_researcher_by_id(default_a, update_dropdown=True)
        if default_b:
            self._set_target_researcher_by_id(default_b, update_dropdown=True)

        self._draw_graph()

        self.algo_badge.configure(text="Normal Graph", fg_color="#EEF2FF", text_color=Theme.ACADEMIC_BLUE)
        self.res_title.configure(text="Network Graph Reset")
        self._set_default_result_message()
