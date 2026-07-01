import math
import uuid

# ── Index Mapping & Thematic Palettes ──────────────────────────

# Maps the proprietary index keys to their Mesh Node display names
NODE_MAPPING = {
    "KVQ": "Identity",
    "RWI": "Reality Field",
    "MKI": "Knowledge Legacy",
    "NGE": "Narrative",
    "DFIS": "Power Current",
    "CATALYST": "Impact Radius"
}

THEME_COLORS = {
    "node_core": "#FFFFFF",
    "node_aura": "#C0A0FF",
    "edge_high_tension": "#FFD080",
    "edge_med_tension": "#88DDFF",
    "edge_low_tension": "#3A3A55",
    "text_primary": "#E7E9F1",
    "text_secondary": "#8390AB"
}

# ── Configuration Defaults ─────────────────────────────────────

DEFAULT_MESH_CONFIG = {
    "compact": {"size": 400, "node_radius": 6, "font_size": 10},
    "medium":  {"size": 800, "node_radius": 12, "font_size": 14},
    "wide":    {"size": 1200, "node_radius": 18, "font_size": 18},
}

# ── Data Builder ───────────────────────────────────────────────

def build_mesh_data(computed_indexes: dict, config: dict = None) -> dict:
    """
    Extracts the normalized scores from the EAS proprietary indexes
    and calculates the interaction tension matrix for the edges.
    """
    if not computed_indexes:
        return None

    nodes = []
    
    # Ensure a stable, ordered layout for the radial geometry
    ordered_keys = ["KVQ", "RWI", "MKI", "NGE", "DFIS", "CATALYST"]
    
    for key in ordered_keys:
        index_data = computed_indexes.get(key, {})
        # Use normalized score (0.0 - 1.0)
        score = index_data.get("score", 0.1)  # Default to low baseline if missing
        
        nodes.append({
            "key": key,
            "label": NODE_MAPPING.get(key, key),
            "archetype": index_data.get("archetype", "Unknown"),
            "score": score
        })
        
    # Calculate unique edges (complete graph)
    edges = []
    num_nodes = len(nodes)
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            # Tension is the product of the two nodes' activation
            # Squaring it slightly exaggerates the drop-off for dynamic range
            tension = (nodes[i]["score"] * nodes[j]["score"]) ** 1.2
            edges.append({
                "source": i,
                "target": j,
                "tension": min(1.0, tension)
            })

    return {
        "nodes": nodes,
        "edges": edges
    }

# ── SVG Geometry Helpers ───────────────────────────────────────

def _pt(cx: float, cy: float, r: float, angle_deg: float) -> tuple:
    """Polar to Cartesian coordinates."""
    rad = math.radians(angle_deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)

# ── SVG Renderer ───────────────────────────────────────────────

def render_mesh_svg(mesh_data: dict, variant="medium", show_labels=True, config: dict = None) -> str:
    """
    Renders the Constellation Mesh into a self-contained inline SVG string.
    """
    if not mesh_data or not mesh_data.get("nodes"):
        return ""
        
    base_cfg = DEFAULT_MESH_CONFIG.get(variant, DEFAULT_MESH_CONFIG["medium"])
    cfg = {**base_cfg, **(config or {})}
    
    SIZE = cfg["size"]
    CX = SIZE / 2.0
    CY = SIZE / 2.0
    
    # Leave room for labels around the perimeter
    MESH_RADIUS = (SIZE / 2.0) * 0.65 
    
    nodes = mesh_data["nodes"]
    edges = mesh_data["edges"]
    num_nodes = len(nodes)
    
    uid = uuid.uuid4().hex[:6]
    glow_id = f"mesh-glow-{uid}"
    
    lines = []
    
    # ── SVG Open & Defs ────────────────────────────────────────
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="100%" aria-label="Constellation Mesh">')
    lines.append("<defs>")
    
    # Node bloom filter
    lines.append(f'<filter id="{glow_id}" x="-50%" y="-50%" width="200%" height="200%">')
    lines.append('<feGaussianBlur stdDeviation="4" result="blur"/>')
    lines.append('<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>')
    lines.append('</filter>')
    
    lines.append("<style>")
    lines.append(f"""
        .cm-bg {{ fill: #0d0d1a; }}
        .cm-node-core {{ fill: {THEME_COLORS["node_core"]}; }}
        .cm-node-aura {{ fill: {THEME_COLORS["node_aura"]}; opacity: 0.6; mix-blend-mode: screen; }}
        .cm-label {{ font-family: 'Georgia', serif; font-size: {cfg["font_size"]}px; fill: {THEME_COLORS["text_primary"]}; text-anchor: middle; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; }}
        .cm-sublabel {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: {cfg["font_size"] - 3}px; fill: {THEME_COLORS["text_secondary"]}; text-anchor: middle; font-style: italic; }}
        
        @media print {{
            .cm-bg {{ fill: #ffffff; }}
            .cm-node-core {{ fill: #333333; }}
            .cm-node-aura {{ display: none; }}
            .cm-label, .cm-sublabel {{ fill: #111111; }}
        }}
    """)
    lines.append("</style>")
    lines.append("</defs>")
    
    # Optional Background (can be commented out if overlaying on existing report canvas)
    lines.append(f'<rect class="cm-bg" width="{SIZE}" height="{SIZE}"/>')
    
    # Calculate exact node positions based on a pentagon/hexagon
    # Starts at top (270 degrees in SVG space)
    angle_step = 360.0 / max(1, num_nodes)
    node_coords = []
    for i in range(num_nodes):
        angle = 270.0 + (i * angle_step)
        x, y = _pt(CX, CY, MESH_RADIUS, angle)
        node_coords.append((x, y, angle))

    # ── Layer 1: Edges (The Mesh) ──────────────────────────────
    # Render edges back-to-front by tension (lowest tension in back)
    sorted_edges = sorted(edges, key=lambda e: e["tension"])
    
    for edge in sorted_edges:
        p1 = node_coords[edge["source"]]
        p2 = node_coords[edge["target"]]
        t = edge["tension"]
        
        # Style calculation based on tension
        if t > 0.65:
            color = THEME_COLORS["edge_high_tension"]
            width = 2.5 + (t * 2)
            opacity = 0.9
        elif t > 0.3:
            color = THEME_COLORS["edge_med_tension"]
            width = 1.0 + (t * 1.5)
            opacity = 0.6
        else:
            color = THEME_COLORS["edge_low_tension"]
            width = 0.8
            opacity = 0.4
            
        # Curvature calculation:
        # High tension = straight line. Low tension = slacked line curving towards center (CX, CY).
        slack = 1.0 - t
        # Control point pulls toward the center proportional to the slack
        mid_x = (p1[0] + p2[0]) / 2.0
        mid_y = (p1[1] + p2[1]) / 2.0
        
        cp_x = mid_x + (CX - mid_x) * slack * 0.8
        cp_y = mid_y + (CY - mid_y) * slack * 0.8
        
        path_d = f"M {p1[0]:.2f} {p1[1]:.2f} Q {cp_x:.2f} {cp_y:.2f} {p2[0]:.2f} {p2[1]:.2f}"
        
        # High tension lines get a subtle glow
        filter_str = f' filter="url(#{glow_id})"' if t > 0.65 else ""
        
        # In print mode, override to a simple grey stroke
        lines.append(f'<path d="{path_d}" stroke="{color}" stroke-width="{width:.2f}" fill="none" opacity="{opacity:.2f}"{filter_str} class="cm-edge"/>')
        
    # ── Layer 2: Nodes ─────────────────────────────────────────
    for i, node in enumerate(nodes):
        x, y, angle = node_coords[i]
        score = node["score"]
        
        # Node scale driven by score (baseline + scaled amount)
        r = cfg["node_radius"] * 0.4 + (cfg["node_radius"] * score)
        
        # Outer Aura
        lines.append(f'<circle class="cm-node-aura" cx="{x:.2f}" cy="{y:.2f}" r="{r * 2.5:.2f}" filter="url(#{glow_id})"/>')
        # Solid Core
        lines.append(f'<circle class="cm-node-core" cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}"/>')
        
    # ── Layer 3: Labels ────────────────────────────────────────
    if show_labels:
        for i, node in enumerate(nodes):
            x, y, angle = node_coords[i]
            
            # Push labels outward from the nodes based on the angle
            # so they don't overlap the mesh
            label_dist = MESH_RADIUS + (cfg["node_radius"] * 3.5)
            lx, ly = _pt(CX, CY, label_dist, angle)
            
            # Adjust baseline slightly so multi-line text centers on the point
            lines.append(f'<text class="cm-label" x="{lx:.2f}" y="{ly - 2:.2f}">{node["label"]}</text>')
            lines.append(f'<text class="cm-sublabel" x="{lx:.2f}" y="{ly + cfg["font_size"] + 2:.2f}">{node["archetype"]}</text>')

    lines.append("</svg>")
    return "\n".join(lines)