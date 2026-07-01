"""
engine/chart_wheel.py — Static SVG natal chart wheel renderer.
Whole Sign house system. No external dependencies.

Aspect-web rendering model
--------------------------
Three visually distinct layers are drawn inside the central circle
before planet markers, so bodies always read on top:

  Layer A — Ghost Web
    All computed aspects drawn at very low opacity (~0.08).
    Creates atmospheric depth; visible only on close inspection.
    Every major aspect is present; no filtering.

  Layer B — Structural Web
    Aspects that meet at least one of:
      · score >= structural_threshold  (default 0.35)
      · orb <= 3.0°
      · involves Sun, Moon, ASC, or MC
    Drawn at medium opacity (~0.45), slightly thicker lines.
    Reveals the chart's core tension/support architecture.

  Layer C — Narrative Web
    The top N aspects by importance score (default 7).
    High opacity (0.95), thickest lines, optional SVG glow filter.
    These are the aspects the interpretation prose will reference.

Scoring model
-------------
  importance_score = aspect_base_weight
                   * average(body_weight_1, body_weight_2)
                   * orb_strength

  where:
    aspect_base_weight  — Conjunction=1.0 … Sextile=0.6
    body_weight         — Sun/Moon/ASC/MC=1.0 … asteroids=0.35
    orb_strength        — max(0, 1 − orb / max_orb)   ∈ [0, 1]

Rendering order (SVG painter's algorithm)
-----------------------------------------
  1. Wheel background + zodiac segments
  2. Sign boundary radial lines + ring circles
  3. Sign glyphs + house numbers
  4. Axis lines (ASC/DSC, MC/IC)
  5. Ghost aspect web          ← new
  6. Structural aspect web     ← new
  7. Narrative aspect web      ← new
  8. Planet body dots + labels (always on top of web)
  9. Angle marker labels

Public API
----------
build_chart_wheel_data(payload, report_type)
    → dict | None

render_natal_wheel_svg(chart_wheel_data, compact=False, config=None)
    → str  (self-contained inline SVG)

Toggle the aspect web via the config dict:
    render_natal_wheel_svg(data, config={"show_aspect_web": False})
"""

import math

# ── Zodiac tables ──────────────────────────────────────────────

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_GLYPHS = {
    "Aries": "♈", "Taurus": "♉", "Gemini": "♊", "Cancer": "♋",
    "Leo": "♌", "Virgo": "♍", "Libra": "♎", "Scorpio": "♏",
    "Sagittarius": "♐", "Capricorn": "♑", "Aquarius": "♒", "Pisces": "♓",
}

SIGN_ELEMENT = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

ELEMENT_FILL = {
    "Fire":  "rgba(220,100,40,0.28)",
    "Earth": "rgba(70,155,90,0.28)",
    "Air":   "rgba(80,175,230,0.28)",
    "Water": "rgba(130,80,220,0.28)",
}

# ── Body labels ────────────────────────────────────────────────

PLANET_ABBREV = {
    "Sun": "Su",  "Moon": "Mo",  "Mercury": "Me", "Venus": "Ve",
    "Mars": "Ma", "Jupiter": "Ju", "Saturn": "Sa", "Uranus": "Ur",
    "Neptune": "Ne", "Pluto": "Pl", "Chiron": "Ch",
    "North_Node": "NN", "South_Node": "SN", "Lilith_BML": "Li",
    "Vertex": "Vx",
    "Ascendant": "ASC", "Midheaven": "MC",
    "Descendant": "DSC", "Imum_Coeli": "IC",
}

STANDARD_PLANET_ORDER = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    "Chiron", "North_Node", "South_Node", "Lilith_BML",
]

# Bodies shown in the compact Personal Forecast wheel (ordered)
PERSONAL_BODIES = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"}
PERSONAL_ANGLE_NAMES = ["Ascendant", "Midheaven", "Vertex"]
FULL_ANGLE_NAMES = ["Ascendant", "Midheaven", "Descendant", "Imum_Coeli"]

# ── Aspect web: colour palette (mirrors EO design tokens) ─────
#
# Aspect family drives visual language:
#   Conjunction  — gold solid beam   (fusion, anchor)
#   Opposition   — cyan solid beam   (axis, polarity)
#   Square       — amber solid line  (tension, friction)
#   Trine        — green soft line   (flow, ease)
#   Sextile      — purple dashed     (latent potential)

ASPECT_COLORS = {
    "Conjunction": "#FFD080",   # --gold
    "Opposition":  "#88DDFF",   # --accent
    "Square":      "#FFBB66",   # --amber
    "Trine":       "#88FFCC",   # --green
    "Sextile":     "#C0A0FF",   # --purple
}

# Base importance weight per aspect type
ASPECT_BASE_WEIGHT = {
    "Conjunction": 1.00,
    "Opposition":  0.90,
    "Square":      0.85,
    "Trine":       0.75,
    "Sextile":     0.60,
}

# Maximum orb used for orb-strength normalisation
ASPECT_MAX_ORB = {
    "Conjunction": 10.0,
    "Opposition":  10.0,
    "Square":      10.0,
    "Trine":       10.0,
    "Sextile":      6.0,
}

# Stroke dash pattern per aspect type (used from Structural layer upward)
ASPECT_DASH = {
    "Conjunction": "",             # solid
    "Opposition":  "",             # solid
    "Square":      "",             # solid
    "Trine":       "6 3",          # long-dash
    "Sextile":     "3 3",          # short-dash / dotted
}

# Importance weight per body; reflects astrological prominence
BODY_WEIGHT = {
    "Sun": 1.00, "Moon": 1.00, "Ascendant": 1.00, "Midheaven": 1.00,
    "Descendant": 0.80, "Imum_Coeli": 0.80,
    "Mercury": 0.75, "Venus": 0.75, "Mars": 0.75,
    "Jupiter": 0.70, "Saturn": 0.70,
    "Uranus": 0.55, "Neptune": 0.55, "Pluto": 0.55,
    "Chiron": 0.45, "North_Node": 0.45, "South_Node": 0.45,
    "Lilith_BML": 0.40, "Vertex": 0.40,
}
_DEFAULT_BODY_WEIGHT = 0.35

# Bodies that always elevate an aspect to at least the Structural layer
LUMINARIES_ANGLES = {"Sun", "Moon", "Ascendant", "Midheaven"}

# ── Default chart configuration ───────────────────────────────

DEFAULT_CHART_CONFIG: dict = {
    # Master switch — set False to render without any aspect web
    "show_aspect_web":        True,
    "aspect_web_mode":        "layered",   # "layered" is the only mode right now

    # Per-layer enable flags
    "show_ghost_aspects":      True,
    "show_structural_aspects": True,
    "show_narrative_aspects":  True,

    # Number of top-scored aspects to promote to the Narrative layer
    "max_narrative_aspects":   7,

    # Visual parameters
    "ghost_opacity":           0.08,
    "structural_opacity":      0.45,
    "narrative_opacity":       0.95,
    "ghost_stroke_width":      0.6,
    "structural_stroke_width": 1.2,
    "narrative_stroke_width":  2.0,
    "narrative_glow":          True,       # SVG feGaussianBlur bloom on narrative lines

    # Minimum score to qualify for Structural layer (orb and luminary rules can override)
    "structural_threshold":    0.35,
}


# ── Data builder ───────────────────────────────────────────────

def build_chart_wheel_data(payload: dict, report_type: str = "year_ahead") -> "dict | None":
    """
    Builds chart_wheel_data from a natal payload.
    Returns None if the payload is missing the Ascendant (wheel cannot render).

    The returned dict includes a processed 'aspects' list with each aspect
    tagged with its layer (ghost / structural / narrative), score, and colour.
    """
    if not isinstance(payload, dict):
        return None

    angles = payload.get("angles") or {}
    standard_planets = payload.get("standard_planets") or {}

    asc_data = angles.get("Ascendant") or {}
    if not isinstance(asc_data, dict) or "longitude" not in asc_data:
        return None

    asc_lon = float(asc_data["longitude"])
    asc_sign_idx = int(asc_lon // 30) % 12
    asc_sign = ZODIAC_SIGNS[asc_sign_idx]

    is_compact = report_type == "personal_forecast"
    body_filter = PERSONAL_BODIES if is_compact else None

    bodies: list = []

    # ── Standard planets ────────────────────────────────────
    for name in STANDARD_PLANET_ORDER:
        if body_filter and name not in body_filter:
            continue
        data = standard_planets.get(name)
        if not isinstance(data, dict) or "longitude" not in data:
            continue
        deg = int(data.get("degree", 0))
        mins = int(data.get("minute", 0))
        sign = data.get("sign", "")
        retro = bool(data.get("retrograde", False))
        bodies.append({
            "name": name,
            "longitude": float(data["longitude"]),
            "sign": sign,
            "degree": deg,
            "minute": mins,
            "position": f"{deg}°{mins:02d}' {sign}" + (" Rx" if retro else ""),
            "house": int(data.get("house") or 0),
            "retrograde": retro,
            "abbrev": PLANET_ABBREV.get(name, name[:2]),
            "category": "planet",
        })

    # ── Nodes from nodes dict (only if not already in standard_planets) ──
    if not is_compact:
        nodes_dict = payload.get("nodes") or {}
        for name in ("North_Node", "South_Node"):
            if any(b["name"] == name for b in bodies):
                continue
            data = nodes_dict.get(name)
            if isinstance(data, dict) and "longitude" in data:
                deg = int(data.get("degree", 0))
                mins = int(data.get("minute", 0))
                sign = data.get("sign", "")
                bodies.append({
                    "name": name,
                    "longitude": float(data["longitude"]),
                    "sign": sign,
                    "degree": deg,
                    "minute": mins,
                    "position": f"{deg}°{mins:02d}' {sign}",
                    "house": int(data.get("house") or 0),
                    "retrograde": False,
                    "abbrev": PLANET_ABBREV.get(name, name[:2]),
                    "category": "node",
                })

    # ── Angles ──────────────────────────────────────────────
    angle_names = PERSONAL_ANGLE_NAMES if is_compact else FULL_ANGLE_NAMES
    default_houses = {
        "Ascendant": 1, "Midheaven": 10,
        "Descendant": 7, "Imum_Coeli": 4,
    }
    for name in angle_names:
        data = angles.get(name)
        if name == "Vertex" and not isinstance(data, dict):
            data = standard_planets.get("Vertex")
        if not isinstance(data, dict) or "longitude" not in data:
            continue
        deg = int(data.get("degree", 0))
        mins = int(data.get("minute", 0))
        sign = data.get("sign", "")
        bodies.append({
            "name": name,
            "longitude": float(data["longitude"]),
            "sign": sign,
            "degree": deg,
            "minute": mins,
            "position": f"{deg}°{mins:02d}' {sign}",
            "house": int(data.get("house") or default_houses.get(name, 0)),
            "retrograde": False,
            "abbrev": PLANET_ABBREV.get(name, name[:3]),
            "category": "angle",
        })

    # ── Whole Sign house ring ────────────────────────────────
    whole_sign_houses = [
        {
            "house": i + 1,
            "sign": ZODIAC_SIGNS[(asc_sign_idx + i) % 12],
            "sign_index": (asc_sign_idx + i) % 12,
            "longitude_start": float(((asc_sign_idx + i) % 12) * 30),
        }
        for i in range(12)
    ]

    # ── Aspect web processing ────────────────────────────────
    # Build a complete longitude lookup that covers all bodies in this chart
    # plus all standard planets and angles so aspect references resolve even
    # for bodies not rendered (e.g. outer planets filtered from compact chart).
    body_lon_map: dict = {}
    for name, data in standard_planets.items():
        if isinstance(data, dict) and "longitude" in data:
            body_lon_map[name] = float(data["longitude"])
    for name, data in angles.items():
        if isinstance(data, dict) and "longitude" in data:
            body_lon_map[name] = float(data["longitude"])
    # Also add the canonical angle aliases used in some aspect payloads
    for alias, canonical in [("ASC", "Ascendant"), ("MC", "Midheaven"),
                              ("DSC", "Descendant"), ("IC", "Imum_Coeli")]:
        if canonical in body_lon_map and alias not in body_lon_map:
            body_lon_map[alias] = body_lon_map[canonical]

    # Restrict to bodies that are actually rendered on this wheel
    rendered_names = {b["name"] for b in bodies}

    raw_aspects = payload.get("aspects") or []
    processed_aspects = _process_aspects(
        raw_aspects, body_lon_map, rendered_names,
        DEFAULT_CHART_CONFIG, is_compact,
    )

    return {
        "asc_longitude": asc_lon,
        "asc_sign": asc_sign,
        "asc_sign_index": asc_sign_idx,
        "bodies": bodies,
        "whole_sign_houses": whole_sign_houses,
        "aspects": processed_aspects,
        "report_type": report_type,
    }


# ── SVG geometry helpers ───────────────────────────────────────

def _svg_angle(lon: float, asc_lon: float) -> float:
    """Ecliptic longitude → SVG angle (degrees CW from right).
    ASC always lands at 180° (left, 9-o'clock).
    MC  always lands at 270° (top, 12-o'clock).
    """
    return (180.0 - lon + asc_lon) % 360.0


def _pt(cx: float, cy: float, r: float, angle_deg: float) -> tuple:
    """Polar → Cartesian in SVG space."""
    rad = math.radians(angle_deg)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _arc_sector(cx: float, cy: float, r_out: float, r_in: float,
                lon_start: float, lon_end: float, asc_lon: float) -> str:
    """
    SVG path for a filled annular sector (donut slice) spanning 30° of zodiac.
    30° is always < 180°, so large-arc-flag is always 0.
    The zodiac sweeps CCW visually → sweep-flag=0 on outer arc, 1 on inner.
    """
    a1 = _svg_angle(lon_start, asc_lon)
    a2 = _svg_angle(lon_end, asc_lon)

    ox1, oy1 = _pt(cx, cy, r_out, a1)
    ox2, oy2 = _pt(cx, cy, r_out, a2)
    ix2, iy2 = _pt(cx, cy, r_in, a2)
    ix1, iy1 = _pt(cx, cy, r_in, a1)

    return (
        f"M {ox1:.3f} {oy1:.3f} "
        f"A {r_out:.1f} {r_out:.1f} 0 0 0 {ox2:.3f} {oy2:.3f} "
        f"L {ix2:.3f} {iy2:.3f} "
        f"A {r_in:.1f} {r_in:.1f} 0 0 1 {ix1:.3f} {iy1:.3f} Z"
    )


# ── Lane assignment for label collision avoidance ──────────────

def _assign_lanes(bodies: list, asc_lon: float, min_sep: float = 9.0) -> list:
    """
    Assigns each body a lane (0 = outer, 1 = inner) so that neighbouring
    planets at similar longitudes alternate lanes rather than overlap.
    """
    if not bodies:
        return bodies

    sorted_bodies = sorted(bodies, key=lambda b: b["longitude"])
    lanes: list = []
    result = []

    for body in sorted_bodies:
        sa = _svg_angle(body["longitude"], asc_lon)

        def nearest_dist(lane_id):
            same = [ang for ang, ln in lanes if ln == lane_id]
            if not same:
                return 999.0
            return min(min(abs(sa - a), 360 - abs(sa - a)) for a in same)

        lane = 0 if nearest_dist(0) >= min_sep else 1
        lanes.append((sa, lane))
        result.append({**body, "lane": lane})

    return result


# ── Aspect scoring and layer assignment ───────────────────────

def _score_aspect(aspect: str, orb: float, body_1: str, body_2: str) -> float:
    """
    Returns a [0, 1] importance score for one aspect.

    importance = aspect_base_weight
               * average(body_weight_1, body_weight_2)
               * orb_strength

    Exact aspects score higher; wide-orb aspects approach zero.
    """
    base = ASPECT_BASE_WEIGHT.get(aspect, 0.5)
    max_orb = ASPECT_MAX_ORB.get(aspect, 10.0)
    orb_strength = max(0.0, 1.0 - abs(orb) / max_orb)
    w1 = BODY_WEIGHT.get(body_1, _DEFAULT_BODY_WEIGHT)
    w2 = BODY_WEIGHT.get(body_2, _DEFAULT_BODY_WEIGHT)
    return base * ((w1 + w2) / 2.0) * orb_strength


def _process_aspects(
    payload_aspects: list,
    body_lon_map: dict,
    rendered_names: set,
    config: dict,
    is_compact: bool = False,
) -> list:
    """
    Converts raw aspect records from the natal payload into layered,
    scored aspect dicts ready for SVG rendering.

    Each output record contains:
      body_1, body_2, aspect, orb
      score           — float [0, 1]
      color           — hex string from ASPECT_COLORS
      lon_1, lon_2    — ecliptic longitudes of the two bodies
      is_ghost        — always True (every aspect is ghost-eligible)
      is_structural   — True when aspect meets structural criteria
      is_narrative    — True for the top-N highest-scored aspects
      involves_luminary — True when Sun/Moon/ASC/MC is a participant

    Only aspects where BOTH bodies are present in body_lon_map are kept.
    An aspect where one body is not rendered (but is in body_lon_map) is
    still kept — the line will project from the correct longitude even if
    no visible dot exists at that position.

    Compact mode applies tighter thresholds:
      · structural_threshold raised to 0.50
      · max_narrative_aspects reduced to 4
      · ghost layer disabled (too cluttered in a small chart)
    """
    if not payload_aspects:
        return []

    structural_threshold = config.get("structural_threshold", 0.35)
    max_narrative = config.get("max_narrative_aspects", 7)

    if is_compact:
        structural_threshold = max(structural_threshold, 0.50)
        max_narrative = min(max_narrative, 4)

    scored: list = []
    for raw in payload_aspects:
        b1 = raw.get("body_1", "")
        b2 = raw.get("body_2", "")
        aspect = raw.get("aspect", "")
        orb = abs(float(raw.get("orb", 5.0)))

        if not b1 or not b2 or not aspect:
            continue
        if aspect not in ASPECT_BASE_WEIGHT:
            continue

        lon_1 = body_lon_map.get(b1)
        lon_2 = body_lon_map.get(b2)
        if lon_1 is None or lon_2 is None:
            continue

        score = _score_aspect(aspect, orb, b1, b2)
        involves_luminary = bool({b1, b2} & LUMINARIES_ANGLES)
        color = ASPECT_COLORS.get(aspect, "#888888")

        scored.append({
            "body_1": b1, "body_2": b2,
            "aspect": aspect, "orb": orb,
            "score": score,
            "color": color,
            "lon_1": lon_1, "lon_2": lon_2,
            "involves_luminary": involves_luminary,
            "is_ghost": True,
            "is_structural": False,   # filled below
            "is_narrative": False,    # filled below
        })

    if not scored:
        return []

    # Sort descending by score for narrative selection
    scored.sort(key=lambda a: a["score"], reverse=True)

    # Structural: score threshold OR tight orb OR involves a luminary/angle
    for asp in scored:
        asp["is_structural"] = (
            asp["score"] >= structural_threshold
            or asp["orb"] <= 3.0
            or asp["involves_luminary"]
        )

    # Narrative: top-N from the structural pool; fall back to global top-N
    narrative_pool = [a for a in scored if a["is_structural"]]
    if not narrative_pool:
        narrative_pool = scored
    for asp in narrative_pool[:max_narrative]:
        asp["is_narrative"] = True

    return scored


# ── Aspect web SVG renderer (helper) ──────────────────────────

def _render_aspect_lines(
    lines: list,
    aspects: list,
    layer: str,            # "ghost" | "structural" | "narrative"
    cx: float,
    cy: float,
    body_pos_map: dict,
    asc_lon: float,
    config: dict,
    r_fallback: float = 130.0,
) -> None:
    """
    Appends SVG line elements for one aspect layer to `lines`.

    Each line runs from the exact screen position of body A to the exact
    screen position of body B, as recorded in body_pos_map.  This means
    lines stretch across the full wheel and terminate at the body dots.

    body_pos_map : {body_name: (x, y)}  — populated from rendered dot coords.
    r_fallback   : radius used when a body is absent from body_pos_map
                   (e.g. outer planets filtered from the compact wheel).

    Layer characteristics
    ─────────────────────
    Ghost:      opacity 0.08, width 0.6, no dash, faint texture
    Structural: opacity 0.45, width 1.2, dash pattern per aspect family
    Narrative:  opacity 0.95, width 2.0, optional SVG glow filter
    """
    layer_filter = {
        "ghost":      lambda a: a.get("is_ghost", True),
        "structural": lambda a: a.get("is_structural", False),
        "narrative":  lambda a: a.get("is_narrative", False),
    }.get(layer, lambda a: False)

    opacity = {
        "ghost":      config.get("ghost_opacity",      0.08),
        "structural": config.get("structural_opacity", 0.45),
        "narrative":  config.get("narrative_opacity",  0.95),
    }[layer]

    base_width = {
        "ghost":      config.get("ghost_stroke_width",      0.6),
        "structural": config.get("structural_stroke_width", 1.2),
        "narrative":  config.get("narrative_stroke_width",  2.0),
    }[layer]

    use_glow = layer == "narrative" and config.get("narrative_glow", True)
    use_dash = layer in ("structural", "narrative")

    filtered = [a for a in aspects if layer_filter(a)]
    if not filtered:
        return

    gid = f"aw-{layer}"
    class_attr = ' class="cw-narr-layer"' if layer == "narrative" else ""
    filter_attr = ' filter="url(#aw-glow)"' if use_glow else ""
    lines.append(f'<g id="{gid}"{class_attr} opacity="{opacity}"{filter_attr}>')

    for asp in filtered:
        color = asp["color"]
        b1, b2 = asp["body_1"], asp["body_2"]

        if b1 in body_pos_map:
            x1, y1 = body_pos_map[b1]
        else:
            x1, y1 = _pt(cx, cy, r_fallback, _svg_angle(asp["lon_1"], asc_lon))

        if b2 in body_pos_map:
            x2, y2 = body_pos_map[b2]
        else:
            x2, y2 = _pt(cx, cy, r_fallback, _svg_angle(asp["lon_2"], asc_lon))

        # Narrative Conjunction/Opposition: use a slightly thicker stroke
        aspect_type = asp.get("aspect", "")
        if layer == "narrative" and aspect_type in ("Conjunction", "Opposition"):
            width = base_width * 1.15
        elif layer == "narrative" and aspect_type in ("Trine", "Sextile"):
            width = base_width * 0.80
        else:
            width = base_width

        dash_str = ""
        if use_dash:
            dash_val = ASPECT_DASH.get(aspect_type, "")
            if dash_val:
                dash_str = f' stroke-dasharray="{dash_val}"'

        lines.append(
            f'<line stroke="{color}" stroke-width="{width:.2f}"{dash_str}'
            f' x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}"/>'
        )

    lines.append("</g>")


# ── SVG renderer ───────────────────────────────────────────────

def render_natal_wheel_svg(
    chart_wheel_data: dict,
    compact: bool = False,
    config: "dict | None" = None,
) -> str:
    """
    Generates a self-contained inline SVG natal chart wheel.

    Parameters
    ----------
    chart_wheel_data : dict
        Output of build_chart_wheel_data().  Returns "" if falsy.
    compact : bool
        True for the smaller Personal Forecast mini-wheel (320 px).
    config : dict, optional
        Override keys from DEFAULT_CHART_CONFIG.
        Example — disable the web entirely:
            render_natal_wheel_svg(data, config={"show_aspect_web": False})

    Rendering layers (painter's algorithm, back to front)
    ─────────────────────────────────────────────────────
    1  wheel background + zodiac segment fills
    2  sign boundary radial lines + ring circles
    3  sign glyphs + house numbers
    4  axis lines (ASC/DSC, MC/IC)
    5  ghost aspect web
    6  structural aspect web
    7  narrative aspect web
    8  planet body dots + abbreviation labels
    9  angle marker labels
    10 centre label
    """
    if not chart_wheel_data:
        return ""

    # Merge caller config over defaults
    cfg: dict = {**DEFAULT_CHART_CONFIG, **(config or {})}

    asc_lon = (
        chart_wheel_data["asc_lon"]
        if "asc_lon" in chart_wheel_data
        else chart_wheel_data["asc_longitude"]
    )
    bodies   = chart_wheel_data.get("bodies", [])
    wsh      = chart_wheel_data.get("whole_sign_houses", [])
    aspects  = chart_wheel_data.get("aspects", [])

    # ── Dimensions ─────────────────────────────────────────
    if compact:
        SIZE      = 320
        R_OUT     = 133
        R_ZIN     = 116
        R_TICK    = 116
        R_PL_O    = 100
        R_PL_I    = 82
        R_HN      = 64
        R_INNER   = 52
        FONT_SIGN = 9
        FONT_PL   = 8
        FONT_HN   = 7
    else:
        SIZE      = 480
        R_OUT     = 200
        R_ZIN     = 176
        R_TICK    = 176
        R_PL_O    = 154
        R_PL_I    = 130
        R_HN      = 102
        R_INNER   = 80
        FONT_SIGN = 11
        FONT_PL   = 9
        FONT_HN   = 8

    CX = CY = SIZE / 2.0

    lines: list = []

    # ── SVG open ───────────────────────────────────────────
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" '
        f'width="100%" style="max-width:{SIZE}px;display:block;margin:0 auto;" '
        f'aria-label="Natal chart wheel">'
    )

    # ── Defs ───────────────────────────────────────────────
    lines.append("<defs>")

    # Glow filter for Narrative layer (soft bloom, no JS required)
    # Composites a blurred copy behind the sharp original line.
    lines.append(
        '<filter id="aw-glow" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="2.2" result="blur"/>'
        '<feMerge>'
        '<feMergeNode in="blur"/>'
        '<feMergeNode in="SourceGraphic"/>'
        '</feMerge>'
        '</filter>'
    )

    lines.append(
        "<style>"
        ".cw-bg{fill:#0d0d1a;}"
        ".cw-ring{fill:none;stroke:#25253a;stroke-width:0.8;}"
        ".cw-div{stroke:#25253a;stroke-width:0.9;fill:none;}"
        ".cw-div-major{stroke:#3a3a55;stroke-width:1.4;fill:none;}"
        ".cw-sign{font-family:serif;dominant-baseline:central;text-anchor:middle;}"
        ".cw-pl{font-family:Arial,sans-serif;dominant-baseline:central;text-anchor:middle;}"
        ".cw-hn{fill:#8390AB;font-family:Arial,sans-serif;"
        "dominant-baseline:central;text-anchor:middle;}"
        ".cw-angle-label{fill:#FFD080;font-family:Arial,sans-serif;font-weight:bold;"
        "dominant-baseline:central;text-anchor:middle;}"
        ".cw-pl-dot{fill:#C8CDE8;}"
        ".cw-angle-dot{fill:#FFD080;}"
        ".cw-asc-line{stroke:#FFD080;stroke-width:1.6;}"
        ".cw-mc-line{stroke:#C0A0FF;stroke-width:1.2;}"
        ".cw-horizon{stroke:#3a3a55;stroke-width:0.7;stroke-dasharray:4,3;}"
        "@media print{"
        ".cw-bg{fill:#fff;}"
        ".cw-ring{stroke:#ccc;}"
        ".cw-div{stroke:#ccc;}"
        ".cw-div-major{stroke:#aaa;}"
        ".cw-hn{fill:#777;}"
        ".cw-angle-label{fill:#333;}"
        ".cw-pl-dot{fill:#444;}"
        ".cw-angle-dot{fill:#333;}"
        ".cw-asc-line{stroke:#333;}"
        ".cw-mc-line{stroke:#666;}"
        ".cw-narr-layer{filter:none;}"
        "}"
        "</style>"
    )
    lines.append("</defs>")

    # ══════════════════════════════════════════════════════
    # LAYER 1: Wheel background + zodiac segment fills
    # ══════════════════════════════════════════════════════
    lines.append(f'<circle class="cw-bg" cx="{CX}" cy="{CY}" r="{R_OUT}"/>')

    for i, sign in enumerate(ZODIAC_SIGNS):
        lon_start = float(i * 30)
        lon_end = float((i + 1) * 30)
        elem = SIGN_ELEMENT.get(sign, "Air")
        fill = ELEMENT_FILL[elem]
        d = _arc_sector(CX, CY, R_OUT, R_ZIN, lon_start, lon_end, asc_lon)
        lines.append(f'<path d="{d}" fill="{fill}" stroke="none"/>')

    # ══════════════════════════════════════════════════════
    # LAYER 2: Sign boundaries + ring circles
    # ══════════════════════════════════════════════════════
    for i in range(12):
        lon = float(i * 30)
        sa = _svg_angle(lon, asc_lon)
        is_cardinal = (i % 3 == 0)
        cls = "cw-div-major" if is_cardinal else "cw-div"
        x1, y1 = _pt(CX, CY, R_INNER, sa)
        x2, y2 = _pt(CX, CY, R_OUT, sa)
        lines.append(
            f'<line class="{cls}" x1="{x1:.2f}" y1="{y1:.2f}" '
            f'x2="{x2:.2f}" y2="{y2:.2f}"/>'
        )

    for r in (R_OUT, R_ZIN, R_INNER):
        lines.append(f'<circle class="cw-ring" cx="{CX}" cy="{CY}" r="{r}"/>')

    # ══════════════════════════════════════════════════════
    # LAYER 3: Sign names (curved textPath) + house numbers
    # ══════════════════════════════════════════════════════
    # Arc radius sits just inside the ring mid-line so text is visually
    # centred radially (ascenders point toward R_OUT, descenders toward R_ZIN).
    glyph_r = (R_OUT + R_ZIN) / 2.0
    sign_font = 9.0 if not compact else 6.5
    # Nudge the text arc slightly inward so cap-tops clear the ring's outer edge.
    r_text = glyph_r - sign_font * 0.25

    sign_color_map = {
        "Fire": "#FF9966", "Earth": "#88CCAA",
        "Air": "#88DDFF",  "Water": "#BB99FF",
    }

    for i, sign in enumerate(ZODIAC_SIGNS):
        lon_start = float(i * 30)
        # svg_angle decreases by 1° per 1° of longitude, so the sign's
        # start has the HIGHER svg angle and its end has the LOWER one.
        a_start = _svg_angle(lon_start, asc_lon)
        a_end   = (a_start - 30.0) % 360.0
        a_mid   = (a_start - 15.0) % 360.0

        col = sign_color_map.get(SIGN_ELEMENT.get(sign, "Air"), "#AABBCC")

        # Choose arc direction so text reads left-to-right from the viewer.
        #   Upper half (a_mid 180°–360°): CW arc — from a_end up to a_start.
        #   Lower half (a_mid   0°–180°): CCW arc — from a_start down to a_end.
        # This ensures the path tangent at the sign's midpoint always points
        # in the +x direction (rightward), giving naturally upright letters.
        if 180.0 < a_mid <= 360.0:
            px1, py1 = _pt(CX, CY, r_text, a_end)
            px2, py2 = _pt(CX, CY, r_text, a_start)
            sweep = 1   # CW
        else:
            px1, py1 = _pt(CX, CY, r_text, a_start)
            px2, py2 = _pt(CX, CY, r_text, a_end)
            sweep = 0   # CCW

        arc_d = (
            f"M {px1:.3f},{py1:.3f} "
            f"A {r_text:.1f},{r_text:.1f} 0 0,{sweep} "
            f"{px2:.3f},{py2:.3f}"
        )
        arc_id = f"cw-zsa-{i}"

        # Invisible path provides the curve geometry for textPath.
        lines.append(f'<path id="{arc_id}" d="{arc_d}" fill="none" stroke="none"/>')
        lines.append(
            f'<text font-family="Georgia,\'Book Antiqua\',Palatino,serif" '
            f'font-size="{sign_font:.1f}" fill="{col}">'
            f'<textPath href="#{arc_id}" startOffset="50%" text-anchor="middle">'
            f'{sign}'
            f'</textPath>'
            f'</text>'
        )

    if not compact and wsh:
        for house_info in wsh:
            sign_idx = house_info["sign_index"]
            mid_lon = sign_idx * 30.0 + 15.0
            sa = _svg_angle(mid_lon, asc_lon)
            hx, hy = _pt(CX, CY, R_HN, sa)
            lines.append(
                f'<text class="cw-hn" x="{hx:.2f}" y="{hy:.2f}" '
                f'font-size="{FONT_HN}">{house_info["house"]}</text>'
            )

    # ══════════════════════════════════════════════════════
    # LAYER 4: Axis lines (ASC/DSC, MC/IC)
    # ══════════════════════════════════════════════════════
    asc_sa = _svg_angle(asc_lon, asc_lon)   # always 180°
    dsc_sa = _svg_angle((asc_lon + 180.0) % 360.0, asc_lon)   # always 0°

    ax1, ay1 = _pt(CX, CY, R_INNER, asc_sa)
    ax2, ay2 = _pt(CX, CY, R_ZIN, asc_sa)
    lines.append(
        f'<line class="cw-asc-line" '
        f'x1="{ax1:.2f}" y1="{ay1:.2f}" x2="{ax2:.2f}" y2="{ay2:.2f}"/>'
    )
    dx1, dy1 = _pt(CX, CY, R_INNER, dsc_sa)
    dx2, dy2 = _pt(CX, CY, R_ZIN, dsc_sa)
    lines.append(
        f'<line class="cw-horizon" '
        f'x1="{dx1:.2f}" y1="{dy1:.2f}" x2="{dx2:.2f}" y2="{dy2:.2f}"/>'
    )

    mc_data = next((b for b in bodies if b["name"] == "Midheaven"), None)
    if mc_data:
        mc_sa = _svg_angle(mc_data["longitude"], asc_lon)
        ic_sa = (mc_sa + 180.0) % 360.0
        mx1, my1 = _pt(CX, CY, R_INNER, mc_sa)
        mx2, my2 = _pt(CX, CY, R_ZIN, mc_sa)
        lines.append(
            f'<line class="cw-mc-line" '
            f'x1="{mx1:.2f}" y1="{my1:.2f}" x2="{mx2:.2f}" y2="{my2:.2f}"/>'
        )
        ix1, iy1 = _pt(CX, CY, R_INNER, ic_sa)
        ix2, iy2 = _pt(CX, CY, R_ZIN, ic_sa)
        lines.append(
            f'<line class="cw-horizon" '
            f'x1="{ix1:.2f}" y1="{iy1:.2f}" x2="{ix2:.2f}" y2="{iy2:.2f}"/>'
        )

    # ── Pre-compute body positions (needed for aspect web AND planet rendering) ──
    # Lanes must be assigned before the aspect web so that line endpoints
    # land exactly on the dots that will be drawn in Layer 8.
    planet_bodies = [b for b in bodies if b["category"] != "angle"]
    angle_bodies  = [b for b in bodies if b["category"] == "angle"]
    laned = _assign_lanes(planet_bodies, asc_lon)

    # body_pos_map: {name → (x, y)} at the rendered dot position
    body_pos_map: dict = {}
    for body in laned:
        sa = _svg_angle(body["longitude"], asc_lon)
        r_place = R_PL_O if body.get("lane", 0) == 0 else R_PL_I
        body_pos_map[body["name"]] = _pt(CX, CY, r_place, sa)
    for body in angle_bodies:
        sa = _svg_angle(body["longitude"], asc_lon)
        body_pos_map[body["name"]] = _pt(CX, CY, R_TICK, sa)

    # ══════════════════════════════════════════════════════
    # LAYERS 5–7: Aspect web  (ghost → structural → narrative)
    # ══════════════════════════════════════════════════════
    if cfg.get("show_aspect_web", True) and aspects:
        # In compact mode the ghost layer is suppressed to keep the chart
        # readable at small size.
        show_ghost = cfg.get("show_ghost_aspects", True) and not compact
        show_structural = cfg.get("show_structural_aspects", True)
        show_narrative  = cfg.get("show_narrative_aspects",  True)

        if show_ghost:
            _render_aspect_lines(
                lines, aspects, "ghost", CX, CY,
                body_pos_map, asc_lon, cfg, r_fallback=R_PL_O,
            )
        if show_structural:
            _render_aspect_lines(
                lines, aspects, "structural", CX, CY,
                body_pos_map, asc_lon, cfg, r_fallback=R_PL_O,
            )
        if show_narrative:
            _render_aspect_lines(
                lines, aspects, "narrative", CX, CY,
                body_pos_map, asc_lon, cfg, r_fallback=R_PL_O,
            )

    # ══════════════════════════════════════════════════════
    # LAYER 8: Planet body dots + labels  (always on top of web)
    # ══════════════════════════════════════════════════════
    for body in laned:
        sa = _svg_angle(body["longitude"], asc_lon)
        lane = body.get("lane", 0)
        r_place = R_PL_O if lane == 0 else R_PL_I

        # degree tick at inner zodiac edge
        tx1, ty1 = _pt(CX, CY, R_TICK - 4, sa)
        tx2, ty2 = _pt(CX, CY, R_TICK + 4, sa)
        lines.append(
            f'<line stroke="#47516A" stroke-width="0.8" '
            f'x1="{tx1:.2f}" y1="{ty1:.2f}" x2="{tx2:.2f}" y2="{ty2:.2f}"/>'
        )

        px, py = _pt(CX, CY, r_place, sa)
        lines.append(
            f'<circle class="cw-pl-dot" cx="{px:.2f}" cy="{py:.2f}" r="2.5"/>'
        )

        lx, ly = _pt(CX, CY, r_place + 11, sa)
        text_col = "#E7E9F1"
        if body.get("retrograde"):
            abbrev = f'{body["abbrev"]}r'
            text_col = "#FF9966"
        else:
            abbrev = body["abbrev"]

        lines.append(
            f'<text class="cw-pl" x="{lx:.2f}" y="{ly:.2f}" '
            f'font-size="{FONT_PL}" fill="{text_col}">{abbrev}</text>'
        )

    # ══════════════════════════════════════════════════════
    # LAYER 9: Angle marker labels
    # ══════════════════════════════════════════════════════
    for body in angle_bodies:
        sa = _svg_angle(body["longitude"], asc_lon)
        lx, ly = _pt(CX, CY, R_ZIN - 14, sa)
        lines.append(
            f'<text class="cw-angle-label" x="{lx:.2f}" y="{ly:.2f}" '
            f'font-size="{FONT_PL + 1}">{body["abbrev"]}</text>'
        )
        dx, dy = _pt(CX, CY, R_TICK, sa)
        lines.append(
            f'<circle class="cw-angle-dot" cx="{dx:.2f}" cy="{dy:.2f}" r="3"/>'
        )

    # ══════════════════════════════════════════════════════
    # LAYER 10: Centre label
    # ══════════════════════════════════════════════════════
    asc_sign = chart_wheel_data.get("asc_sign", "")
    glyph = SIGN_GLYPHS.get(asc_sign, "")
    lines.append(
        f'<text font-family="serif" font-size="{FONT_SIGN - 1}" fill="#5A607A" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'x="{CX}" y="{CY - 6}">{glyph}</text>'
    )
    lines.append(
        f'<text font-family="Arial,sans-serif" font-size="{FONT_HN}" fill="#47516A" '
        f'text-anchor="middle" dominant-baseline="central" '
        f'x="{CX}" y="{CY + 7}">ASC {asc_sign[:3].upper()}</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)
