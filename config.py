"""
config.py — Entangled Oracle Report Generator
All thresholds, mappings, and path configuration lives here.
Change things here, not scattered through the codebase.
"""
import os

# ── Paths ──────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_DIR  = os.path.join(BASE_DIR, "products")
ARCHIVE_DIR   = os.path.join(BASE_DIR, "archive")
BLOCKS_DIR    = PRODUCTS_DIR
TEMPLATES_DIR = PRODUCTS_DIR
OUTPUT_DIR    = os.path.join(BASE_DIR, "output")

REPORT_BLOCK_DIRS = {
    "daily_horoscope":  os.path.join(PRODUCTS_DIR, "daily_horoscope", "blocks"),
    "weekly_horoscope": os.path.join(PRODUCTS_DIR, "weekly_horoscope", "blocks"),
    "year_ahead":       os.path.join(PRODUCTS_DIR, "year_ahead", "blocks", "plainspeak"),
    "personal_forecast": os.path.join(PRODUCTS_DIR, "personal_forecast", "blocks", "shared"),
    "soul_ecosystem":   os.path.join(PRODUCTS_DIR, "soul_ecosystem", "blocks"),
    "soul_journey":     os.path.join(PRODUCTS_DIR, "soul_ecosystem", "blocks"),
    "identity_profile": os.path.join(PRODUCTS_DIR, "identity_profile", "blocks"),
    "shared":           os.path.join(PRODUCTS_DIR, "identity_profile", "blocks"),
    "location_services": os.path.join(PRODUCTS_DIR, "location_services", "blocks", "plainspeak"),
    "synastry":         os.path.join(PRODUCTS_DIR, "synastry", "blocks", "plainspeak"),
}

# ── Score Tier Thresholds ──────────────────────────────────────
SCORE_TIERS = {
    "DOMINANT": 0.65,
    "PRESENT":  0.35,
    "SUBTLE":   0.0
}

AHL_TIERS = {
    "DEEP":    4.0,
    "PRESENT": 2.0
}

# ── Orb Configuration (degrees) ───────────────────────────────
ORB_CONFIG = {
    "base_orbs": {
        "Sun": 10, "Moon": 10, "Mercury": 6, "Venus": 6,
        "Mars": 6, "Jupiter": 8, "Saturn": 8,
        "Uranus": 5, "Neptune": 5, "Pluto": 4,
        "Chiron": 4, "Default": 3
    },
    "aspect_multipliers": {
        "Conjunction": 1.0, "Opposition": 1.0,
        "Trine": 0.8, "Square": 0.8, "Sextile": 0.5
    },
    "max_orb_for_angle":    3.0,
    "max_orb_synastry":     5.0,
    "activation_tight_orb": 1.0,
    "activation_wide_orb":  3.0
}

# ── Planet Weight Modifiers (dominant aspect selection) ────────
# These weights shape natal dominant-aspect ranking only.
# They are intentionally distinct from engine.transit_engine.PLANET_SIGNIFICANCE,
# which scores forecast-event salience. Do not reconcile the two tables.
PLANET_WEIGHTS = {
    "Sun": 3.0, "Moon": 3.0, "Ascendant": 3.0, "Midheaven": 3.0,
    "Mercury": 2.0, "Venus": 2.0, "Mars": 2.0,
    "Jupiter": 1.5, "Saturn": 1.5,
    "Uranus": 1.0, "Neptune": 1.0, "Pluto": 1.0, "Chiron": 1.0
}

# ── Major Aspects ──────────────────────────────────────────────
MAJOR_ASPECTS = [
    ("Conjunction", 0), ("Opposition", 180),
    ("Trine", 120), ("Square", 90), ("Sextile", 60)
]

# ── Aspect Character ───────────────────────────────────────────
ASPECT_CHARACTERS = {
    "Conjunction": "flowing", "Trine": "flowing", "Sextile": "flowing",
    "Square": "challenging", "Opposition": "challenging"
}

# ── Element Mapping ────────────────────────────────────────────
SIGN_ELEMENTS = {
    "fire":  ["Aries", "Leo", "Sagittarius"],
    "earth": ["Taurus", "Virgo", "Capricorn"],
    "air":   ["Gemini", "Libra", "Aquarius"],
    "water": ["Cancer", "Scorpio", "Pisces"]
}

# ── Modality Mapping ───────────────────────────────────────────
SIGN_MODALITIES = {
    "cardinal": ["Aries", "Cancer", "Libra", "Capricorn"],
    "fixed":    ["Taurus", "Leo", "Scorpio", "Aquarius"],
    "mutable":  ["Gemini", "Virgo", "Sagittarius", "Pisces"]
}

# ── House to Human Domain ──────────────────────────────────────
HOUSE_DOMAINS = {
    1:  "Identity / Personal Growth",
    2:  "Money / Resources",
    3:  "Communication / Learning",
    4:  "Home / Family",
    5:  "Creativity / Romance",
    6:  "Work / Health / Routine",
    7:  "Relationships / Partnership",
    8:  "Transformation / Shared Resources",
    9:  "Beliefs / Travel / Expansion",
    10: "Career / Public Life",
    11: "Community / Friendships / Goals",
    12: "Spirituality / Inner Life / Rest"
}

# ── House Theme Phrases (appended to planet blocks) ────────────
HOUSE_THEMES = {
    1:  "in your personal identity and self-expression",
    2:  "in your relationship with resources and security",
    3:  "in your thinking, communication, and learning",
    4:  "in your sense of home, family, and foundation",
    5:  "in your creativity, play, and heart connections",
    6:  "in your daily work, health, and service",
    7:  "in your closest partnerships and relationships",
    8:  "in your experience of transformation and depth",
    9:  "in your beliefs, expansion, and search for meaning",
    10: "in your vocation, public role, and lasting contribution",
    11: "in your community, friendships, and collective purpose",
    12: "in your inner world, spiritual life, and hidden depths"
}

# ── Chaldean Day Rulers ────────────────────────────────────────
# datetime.weekday(): 0=Monday ... 6=Sunday
DAY_RULERS = {
    6: "Sun", 0: "Moon", 1: "Mars", 2: "Mercury",
    3: "Jupiter", 4: "Venus", 5: "Saturn"
}

# ── Intensity Levels ───────────────────────────────────────────
# (min_score, reader_label, symbol)
INTENSITY_LEVELS = [
    (0.80, "Key Window",  "✦"),
    (0.60, "Significant", "◆"),
    (0.40, "Active",      "●"),
    (0.20, "Background",  "○"),
    (0.00, "Passing",     "○"),
]

# ── Duration Modifiers (min_days, modifier) ────────────────────
DURATION_MODIFIERS = [
    (90, 1.35), (42, 1.15), (14, 1.00), (0, 0.75)
]

# ── Landmark Qualification ─────────────────────────────────────
LANDMARK_MIN_SCORE = 0.65
LANDMARK_MIN_DAYS  = 42
LANDMARK_MAX_COUNT = 5

# ── Transit Priority ───────────────────────────────────────────
PRIORITY_A_PLANETS = ["Saturn", "Uranus", "Neptune", "Pluto", "Jupiter"]
PRIORITY_B_PLANETS = ["Mars"]

# ── Proprietary Index Dimension Names ─────────────────────────
INDEX_DIMENSION_NAMES = {
    "KVQ":      "Your Foresight Pattern",
    "MKI":      "Your Knowledge Legacy",
    "RWI":      "Your Reality Field",
    "DFIS":     "Your Power Current",
    "NGE":      "Your Narrative Gravity",
    "CATALYST": "Your Impact Radius",
    "AHL":      "Your Ancestral Thread",
    "MAGNETIC": "Your Magnetic Frequency",
}

# ── Year Ahead Content Packs ───────────────────────────────────
# Each pack maps category keys to absolute block file paths, plus an
# integration_themes dict that translates dominant slow planet → theme key.
# All year_ahead block selection routes through these mappings — no
# "if content_pack ==" checks are scattered elsewhere.
_YEAR_AHEAD_PLAINSPEAK_DIR = os.path.join(PRODUCTS_DIR, "year_ahead", "blocks", "plainspeak")
_YEAR_AHEAD_EO_DIR = os.path.join(PRODUCTS_DIR, "year_ahead", "blocks", "entangled_oracle")
_YEAR_AHEAD_SHARED_DIR = os.path.join(PRODUCTS_DIR, "year_ahead", "blocks", "shared")
_PERSONAL_FORECAST_DIR = os.path.join(PRODUCTS_DIR, "personal_forecast", "blocks", "shared")
_PERSONAL_FORECAST_BLOCKS = os.path.join(
    _PERSONAL_FORECAST_DIR, "EO_Standard_Personal_Forecast_Blocks.json"
)
# Transit-only climate notes (not natal-chart content) — genuinely shared
# across report types rather than duplicated per pack/report.
_RETROGRADE_CLUSTER_BLOCKS = os.path.join(_PERSONAL_FORECAST_DIR, "retrograde_cluster_blocks.json")
_VOID_OF_COURSE_BLOCKS = os.path.join(_PERSONAL_FORECAST_DIR, "void_of_course_moon_blocks.json")

CONTENT_PACKS = {
    "plainspeak": {
        # All transit blocks route through the single file in plainspeak/ -
        # there is no separate entangled_oracle transit file anymore.
        "transits":          os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_standard_transit_blocks.json"),
        "monthly_snapshots": os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "monthly_snapshot.json"),
        "ingresses":         os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "house_ingress.json"),
        "eclipses":          os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "eclipse_blocks.json"),
        "stations":          os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "station_blocks.json"),
        "forecast_climate":  os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Standard_Forecast_Climate_Blocks.json"),
        "year_overview":     os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "year_overview.json"),
        "year_integration":  os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "year_integration.json"),
        "year_texture_progressions": os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "progression_blocks.json"),
        "year_texture_solar_arc":    os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "solar_arc_blocks.json"),
        "annual_profections":        os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "annual_profection_blocks.json"),
        "zodiacal_releasing":        os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "zodiacal_releasing_blocks.json"),
        "exact_returns":             os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "return_blocks.json"),
        "forecast_synthesis_blocks": os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "forecast_synthesis_blocks.json"),
        "predictive_chapters":       os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "predictive_chapters.json"),
        "personal_predictive_chapters": os.path.join(_PERSONAL_FORECAST_DIR, "predictive_chapters.json"),
        "personal_predictive_candidates": os.path.join(_PERSONAL_FORECAST_DIR, "predictive_candidates.json"),
        "standard_natal_foundation": os.path.join(_YEAR_AHEAD_SHARED_DIR, "Standard_Natal_Foundation_Blocks.json"),
        # Shared until a separate legacy Personal Forecast voice library exists.
        "personal_forecast":  _PERSONAL_FORECAST_BLOCKS,
        "retrograde_cluster_blocks": _RETROGRADE_CLUSTER_BLOCKS,
        "void_of_course_moon_blocks": _VOID_OF_COURSE_BLOCKS,
        # Archetypal integration blocks (written separately; infrastructure only)
        "archetypal_opening_blocks": os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_Year_Ahead_Archetypal_Opening_Blocks.json"),
        "refraction_bridges":        os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_Year_Ahead_Refraction_Bridges.json"),
        "convergence_blocks":        os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_Year_Ahead_Convergence_Blocks.json"),
        # Plainspeak eclipse blocks are keyed by planet-order index
        # (ECLIPSE_TARGET_KEYS: Sun=1, Moon=2, ... Jupiter=6 ...).
        "eclipse_key": "natal_target_key",
        "integration_themes": {
            "Saturn":  "structural_sovereignty",
            "Jupiter": "pattern_literacy",
            "Uranus":  "relational_architecture",
            "Neptune": "somatic_grounding",
            "Pluto":   "shadow_rekindling",
        },
    },
    "entangled_oracle": {
        # Same single transit file as the plainspeak pack (see note above).
        "transits":          os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_standard_transit_blocks.json"),
        "monthly_snapshots": os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Standard_Monthly_Snapshot_Blocks.json"),
        "ingresses":         os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Standard_House_Ingress.json"),
        # Eclipse/year_overview/year_integration content now lives in blocks/plainspeak/
        # (fixed content only exists there now; blocks/entangled_oracle/ no longer has these).
        "eclipses":          os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_Standard_Eclipse_Blocks.json"),
        "stations":          os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Standard_Station_Blocks_Revised.json"),
        "forecast_climate":  os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Standard_Forecast_Climate_Blocks.json"),
        "year_overview":     os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_Standard_Year_Overview_Blocks.json"),
        "year_integration":  os.path.join(_YEAR_AHEAD_PLAINSPEAK_DIR, "EO_Standard_Year_Integration_Blocks.json"),
        "year_texture_progressions": os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Standard_Progression_Blocks.json"),
        "year_texture_solar_arc":    os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Standard_Solar_Arc_Blocks.json"),
        "standard_natal_foundation": os.path.join(_YEAR_AHEAD_SHARED_DIR, "Standard_Natal_Foundation_Blocks.json"),
        "personal_forecast":  _PERSONAL_FORECAST_BLOCKS,
        "retrograde_cluster_blocks": _RETROGRADE_CLUSTER_BLOCKS,
        "void_of_course_moon_blocks": _VOID_OF_COURSE_BLOCKS,
        # Archetypal integration blocks (written separately; infrastructure only)
        "archetypal_opening_blocks": os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Year_Ahead_Archetypal_Opening_Blocks.json"),
        "refraction_bridges":        os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Year_Ahead_Refraction_Bridges.json"),
        "convergence_blocks":        os.path.join(_YEAR_AHEAD_EO_DIR, "EO_Year_Ahead_Convergence_Blocks.json"),
        # EO eclipse blocks are keyed by Whole Sign house number (1–12).
        # Using natal_target_key (planet-order index) would select the wrong block.
        "eclipse_key": "natal_house",
        "integration_themes": {
            "Saturn":  "discipline_growth",
            "Jupiter": "expansion_opportunity",
            "Uranus":  "disruption_liberation",
            "Neptune": "dissolution_vision",
            "Pluto":   "transformation_power",
        },
    },
}

# ── Canonical Semantic Color Tokens ───────────────────────────
# These are the meaning-layer tokens. Templates reference these
# via CSS variables. Never hardcode palette colors in templates.

PALETTE_VIBRANT = {
    # Base
    "bg":        "#07070B",
    "surface":   "#101018",
    "surface_2": "#151522",
    "border":    "#242436",
    "text":      "#E6E2DA",
    "muted":     "#8B8798",
    "subtle":    "#555266",
    # Semantic
    "identity":      "#00FFB2",
    "growth":        "#BF7FFF",
    "relationships": "#FF6BAE",
    "creativity":    "#FFD000",
    "vocation":      "#4D6AFF",
    "home":          "#00C46E",
    "spiritual":     "#00DDBB",
    # Legacy aliases (keep for backward compat)
    "accent":  "#00FFB2",
    "purple":  "#BF7FFF",
    "gold":    "#FFD000",
    "rose":    "#FF6BAE",
    "ember":   "#FF9868",
    "blue":    "#88DDFF",
}

PALETTE_MUTED = {
    # Base
    "bg":        "#F8F4EE",
    "surface":   "#F0EBE3",
    "surface_2": "#E8E2D8",
    "border":    "#D4CBC0",
    "text":      "#2A2420",
    "muted":     "#7A6E66",
    "subtle":    "#A89E96",
    # Semantic
    "identity":      "#C4E8DF",
    "growth":        "#D4C8EC",
    "relationships": "#ECC8D8",
    "creativity":    "#ECD898",
    "vocation":      "#C0C4E8",
    "home":          "#B8D8C4",
    "spiritual":     "#B8DDD8",
    # Legacy aliases
    "accent":  "#C4E8DF",
    "purple":  "#D4C8EC",
    "gold":    "#ECD898",
    "rose":    "#ECC8D8",
    "ember":   "#D4B8A8",
    "blue":    "#C0C4E8",
}

PALETTES = {
    "vibrant": PALETTE_VIBRANT,
    "muted":   PALETTE_MUTED,
}
