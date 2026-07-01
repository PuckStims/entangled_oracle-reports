import math
import uuid

# ── Thematic Palettes ──────────────────────────────────────────

THEME_COLORS = {
    "vibrant": {
        "inner_life_rest": "#66AADD",
        "career_visibility": "#FFB84D",
        "relationship_focus": "#FF88BB",
        "structural_growth": "#88DD99",
        "transformation": "#C0A0FF",
        "default": "#8899AA",
        "event_marker": "#FFD080",
        "node_glow": "#FFFFFF",
        "node_aura": "#FFD080"
    },
    "monochrome": {
        "default": "#888888",
        "event_marker": "#444444",
        "node_glow": "#000000",
        "node_aura": "#888888"
    }
}

# ── Configuration Defaults ─────────────────────────────────────

DEFAULT_RIVER_CONFIG = {
    "compact": {"width": 400, "height": 120, "base_thick": 4, "max_thick": 24, "wave_amp": 15, "font_size": 9},
    "medium":  {"width": 800, "height": 200, "base_thick": 8, "max_thick": 45, "wave_amp": 35, "font_size": 12},
    "wide":    {"width": 1200, "height": 280, "base_thick": 12, "max_thick": 70, "wave_amp": 60, "font_size": 14},
    # The 'Amped' variant for maximum visual drama
    "amped":   {"width": 1200, "height": 380, "base_thick": 6, "max_thick": 120, "wave_amp": 110, "font_size": 16},
}

# ── Data Builder ───────────────────────────────────────────────

def build_temporal_river_data(months, palette_name="vibrant", events=None, config=None):
    """
    Normalizes month data, identifies peaks, maps events, and prepares
    the thematic colour flow for the renderer.
    """
    if not months:
        return None
        
    cfg = config or {}
    palette = THEME_COLORS.get(palette_name, THEME_COLORS["vibrant"])
    
    processed_months = []
    max_score = -1.0
    peak_index = 0
    
    # Safely evaluate bounds
    for i, m in enumerate(months):
        score = float(m.get("score", 0.0))
        if score > max_score:
            max_score = score
            peak_index = i
            
        theme = m.get("theme", "default")
        color = palette.get(theme, palette.get("default"))
        
        processed_months.append({
            "index": i,
            "label": m.get("label", f"M{i+1}"),
            "score": score,
            "theme": theme,
            "color": color,
            "is_peak": False
        })
        
    if processed_months:
        processed_months[peak_index]["is_peak"] = True
        
    # Map events to specific nodes
    processed_events = []
    if events:
        for ev in events:
            idx = int(ev.get("month_index", 0))
            if 0 <= idx < len(processed_months):
                processed_events.append({
                    "index": idx,
                    "label": ev.get("label", "*"),
                    "score": float(ev.get("score", 0.5))
                })

    return {
        "months": processed_months,
        "events": processed_events,
        "palette_name": palette_name,
        "palette": palette
    }

# ── SVG Geometry Helpers ───────────────────────────────────────

def _build_ribbon_path(points):
    """
    Builds a bidirectional SVG path forming a filled ribbon.
    Takes a list of tuples: (x, y_top, y_bottom)
    """
    if not points:
        return ""
        
    d = [f"M {points[0][0]:.2f} {points[0][1]:.2f}"]
    
    # Top edge (left to right)
    for i in range(len(points) - 1):
        p0 = points[i]
        p1 = points[i+1]
        cp_dist = (p1[0] - p0[0]) * 0.45 # Horizontal control point weighting
        d.append(f"C {p0[0] + cp_dist:.2f} {p0[1]:.2f}, {p1[0] - cp_dist:.2f} {p1[1]:.2f}, {p1[0]:.2f} {p1[1]:.2f}")
        
    # Cap right edge
    d.append(f"L {points[-1][0]:.2f} {points[-1][2]:.2f}")
    
    # Bottom edge (right to left)
    for i in range(len(points) - 1, 0, -1):
        p1 = points[i]
        p0 = points[i-1]
        cp_dist = (p1[0] - p0[0]) * 0.45
        d.append(f"C {p1[0] - cp_dist:.2f} {p1[2]:.2f}, {p0[0] + cp_dist:.2f} {p0[2]:.2f}, {p0[0]:.2f} {p0[2]:.2f}")
        
    d.append("Z")
    return " ".join(d)

# ── SVG Renderer ───────────────────────────────────────────────

def render_temporal_river_svg(river_data, variant="amped", show_labels=True, config=None):
    """
    Renders the temporal river into a self-contained inline SVG string.
    Gracefully handles varied month lengths and formats cleanly for print.
    """
    if not river_data or not river_data.get("months"):
        return ""
        
    # Resolve sizing configuration
    base_cfg = DEFAULT_RIVER_CONFIG.get(variant, DEFAULT_RIVER_CONFIG["amped"])
    cfg = {**base_cfg, **(config or {})}
    
    W = cfg["width"]
    H = cfg["height"]
    base_thick = cfg["base_thick"]
    max_thick = cfg["max_thick"]
    wave_amp = cfg["wave_amp"]
    
    months = river_data["months"]
    events = river_data["events"]
    palette = river_data["palette"]
    
    num_months = len(months)
    
    # Ensure unique IDs if multiple rivers render on one page
    uid = uuid.uuid4().hex[:6]
    grad_id = f"river-grad-{uid}"
    glow_id = f"river-glow-{uid}"
    heavy_glow_id = f"river-heavy-glow-{uid}"
    
    lines = []
    
    # ── SVG Open & Defs ────────────────────────────────────────
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" aria-label="Temporal River Visualization">')
    lines.append("<defs>")
    
    # Soft bloom filter for event nodes
    lines.append(f'<filter id="{glow_id}" x="-50%" y="-50%" width="200%" height="200%">')
    lines.append('<feGaussianBlur stdDeviation="3" result="blur"/>')
    lines.append('<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>')
    lines.append('</filter>')

    # Heavy bloom filter for the peak activation node
    lines.append(f'<filter id="{heavy_glow_id}" x="-100%" y="-100%" width="300%" height="300%">')
    lines.append('<feGaussianBlur stdDeviation="8" result="blur"/>')
    lines.append('<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>')
    lines.append('</filter>')
    
    # Linear Gradient mapping themes horizontally
    lines.append(f'<linearGradient id="{grad_id}" x1="0%" y1="0%" x2="100%" y2="0%">')
    for m in months:
        offset_pct = (m["index"] / max(1, num_months - 1)) * 100
        lines.append(f'<stop offset="{offset_pct:.1f}%" stop-color="{m["color"]}"/>')
    lines.append('</linearGradient>')
    
    # Print-safe CSS embedded
    lines.append("<style>")
    lines.append(f"""
        .tr-ribbon {{ fill: url(#{grad_id}); opacity: 0.90; }}
        .tr-ribbon-core {{ fill: none; stroke: rgba(255,255,255,0.3); stroke-width: 1.5; }}
        .tr-label {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; fill: #667085; font-size: {cfg['font_size']}px; text-anchor: middle; font-weight: bold; letter-spacing: 1px; }}
        .tr-peak-aura {{ fill: {palette.get('node_aura', '#FFF')}; opacity: 0.4; }}
        .tr-peak-dot {{ fill: {palette.get('node_glow', '#FFF')}; }}
        .tr-peak-spark {{ stroke: {palette.get('node_glow', '#FFF')}; stroke-width: 2.5; stroke-linecap: round; }}
        .tr-event {{ fill: {palette.get('event_marker', '#FFD')}; }}
        .tr-event-label {{ font-family: 'Georgia', serif; font-style: italic; fill: #9CA3AF; font-size: {cfg['font_size'] - 1}px; text-anchor: middle; }}
        
        @media print {{
            .tr-ribbon {{ opacity: 1.0; stroke: #888; stroke-width: 0.5; }}
            .tr-ribbon-core {{ display: none; }}
            .tr-label {{ fill: #333; }}
            .tr-event {{ stroke: #333; stroke-width: 1; }}
            .tr-peak-aura {{ display: none; }}
            .tr-peak-dot {{ filter: none; stroke: #333; stroke-width: 1; fill: #FFF; }}
            .tr-peak-spark {{ stroke: #333; }}
        }}
    """)
    lines.append("</style>")
    lines.append("</defs>")
    
    # ── Geometry Calculation ───────────────────────────────────
    pad_x = W * 0.08 
    step_x = (W - (pad_x * 2)) / max(1, num_months - 1) if num_months > 1 else W
    
    ribbon_points = []
    center_y = H * 0.45 
    
    for i, m in enumerate(months):
        x = pad_x + (i * step_x)
        # 1.5 cycle sine wave across the timeline 
        y_offset = math.sin((i / max(1, num_months - 1)) * math.pi * 3) * wave_amp
        y = center_y + y_offset
        
        # Exponential curve for thickness to make peaks pop drastically
        score_curve = math.pow(m["score"], 1.5)
        t = base_thick + (score_curve * max_thick)
        
        y_top = y - (t / 2)
        y_bottom = y + (t / 2)
        
        ribbon_points.append((x, y_top, y_bottom, y, t))
        
    # ── Layer 1: The River Ribbon & Core Energy Line ───────────
    path_d = _build_ribbon_path([(pt[0], pt[1], pt[2]) for pt in ribbon_points])
    lines.append(f'<path class="tr-ribbon" d="{path_d}"/>')
    
    # Draw a thin, bright "energy core" line flowing right through the middle
    core_d = "M " + " L ".join([f"{pt[0]:.2f} {pt[3]:.2f}" for pt in ribbon_points])
    # Smooth the core line using a simpler path for elegance
    smooth_core = [f"M {ribbon_points[0][0]:.2f} {ribbon_points[0][3]:.2f}"]
    for i in range(len(ribbon_points) - 1):
        p0 = ribbon_points[i]
        p1 = ribbon_points[i+1]
        cp_dist = (p1[0] - p0[0]) * 0.45
        smooth_core.append(f"C {p0[0] + cp_dist:.2f} {p0[3]:.2f}, {p1[0] - cp_dist:.2f} {p1[3]:.2f}, {p1[0]:.2f} {p1[3]:.2f}")
    
    lines.append(f'<path class="tr-ribbon-core" d="{" ".join(smooth_core)}"/>')
    
    # ── Layer 2: Luminous Peak Node (Amped Up) ─────────────────
    for i, m in enumerate(months):
        if m.get("is_peak"):
            pt = ribbon_points[i]
            r = pt[4] * 0.20 + 3  
            
            # Outer massive aura
            lines.append(f'<circle class="tr-peak-aura" cx="{pt[0]:.2f}" cy="{pt[3]:.2f}" r="{r * 2.8:.2f}" filter="url(#{heavy_glow_id})"/>')
            # Inner intense core
            lines.append(f'<circle class="tr-peak-dot" cx="{pt[0]:.2f}" cy="{pt[3]:.2f}" r="{r:.2f}" filter="url(#{glow_id})"/>')
            
            # Crosshair sparks shooting out of the node
            spark_len = r * 1.8
            lines.append(f'<line class="tr-peak-spark" x1="{pt[0]-spark_len:.2f}" y1="{pt[3]:.2f}" x2="{pt[0]+spark_len:.2f}" y2="{pt[3]:.2f}"/>')
            lines.append(f'<line class="tr-peak-spark" x1="{pt[0]:.2f}" y1="{pt[3]-spark_len:.2f}" x2="{pt[0]:.2f}" y2="{pt[3]+spark_len:.2f}"/>')

    # ── Layer 3: Event Markers (Stretched Starburst) ───────────
    for ev in events:
        idx = ev["index"]
        if idx < len(ribbon_points):
            pt = ribbon_points[idx]
            # Draw an elongated 4-point star for an event
            w, h = 4, 12
            dx, dy = pt[0], pt[3]
            star_d = f"M {dx} {dy - h} Q {dx} {dy} {dx + w} {dy} Q {dx} {dy} {dx} {dy + h} Q {dx} {dy} {dx - w} {dy} Q {dx} {dy} {dx} {dy - h} Z"
            
            lines.append(f'<path class="tr-event" d="{star_d}" filter="url(#{glow_id})"/>')
            
            if show_labels:
                # Place event label above the highest vertical bound of the ribbon segment
                label_y = min(pt[1], pt[3] - h) - 15
                lines.append(f'<text class="tr-event-label" x="{dx:.2f}" y="{label_y:.2f}">{ev["label"]}</text>')

    # ── Layer 4: Month Labels & Grid lines ─────────────────────
    if show_labels:
        for i, m in enumerate(months):
            pt = ribbon_points[i]
            label_y = H - (cfg["font_size"])
            
            lines.append(f'<text class="tr-label" x="{pt[0]:.2f}" y="{label_y:.2f}">{m["label"]}</text>')
            
            # Connecting grid line
            lines.append(f'<line x1="{pt[0]:.2f}" y1="{pt[2] + 10:.2f}" x2="{pt[0]:.2f}" y2="{label_y - 18:.2f}" stroke="#374151" stroke-width="0.8" stroke-dasharray="1 4"/>')

    lines.append("</svg>")
    return "\n".join(lines)