"""
Essential dignity matrix — Domicile, Exaltation, Triplicity, Term, Face/Decan,
Detriment, and Fall.

CR-06:
  - Face/Decan implemented via Chaldean face rulers (+1 point each).
  - classical_score and modern_modifier are independent output fields.
  - Triplicity convention: Dorothean day/night rulers (documented as TRIPLICITY_CONVENTION).
  - Outer planets (Uranus, Neptune, Pluto, Chiron) excluded from Triplicity, Term, Face.
  - is_peregrine is a technical/internal flag; peregrine_applicable = False for outer planets.
  - Outer-planet peregrine policy: the classical peregrine concept does not extend to
    Uranus, Neptune, Pluto, or Chiron, so peregrine_applicable is set False for them.
"""
from __future__ import annotations

from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.sect import evaluate_chart_sect
from selectors.utils import get_body_data, get_sign_element

MethodRegistry.register(
    method_id="essential_dignity_expanded",
    category="core_standard",
    lineage_tags=["ptolemaic", "renaissance", "modern_synthesis"],
    requires_exact_time=False,
    required_data=["standard_planets"],
    time_requirement="birth_time_optional",
)

OUTER_PLANETS = frozenset({"Uranus", "Neptune", "Pluto", "Chiron"})

# ── Domicile & Detriment ──────────────────────────────────────────────────────

TRADITIONAL_DOMICILE: dict[str, str] = {
    "Aries": "Mars",       "Taurus": "Venus",   "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",         "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

MODERN_DOMICILE: dict[str, str] = {
    "Scorpio": "Pluto", "Aquarius": "Uranus", "Pisces": "Neptune",
}

DETRIMENT_MAP: dict[str, str] = {
    "Aries": "Venus",     "Taurus": "Mars",    "Gemini": "Jupiter",
    "Cancer": "Saturn",   "Leo": "Saturn",      "Virgo": "Jupiter",
    "Libra": "Mars",      "Scorpio": "Venus",   "Sagittarius": "Mercury",
    "Capricorn": "Moon",  "Aquarius": "Sun",    "Pisces": "Mercury",
}

# ── Exaltation & Fall ─────────────────────────────────────────────────────────

EXALTATION_MAP: dict[str, str] = {
    "Sun": "Aries", "Moon": "Taurus", "Mercury": "Virgo", "Venus": "Pisces",
    "Mars": "Capricorn", "Jupiter": "Cancer", "Saturn": "Libra",
}

FALL_MAP: dict[str, str] = {
    "Sun": "Libra", "Moon": "Scorpio", "Mercury": "Pisces", "Venus": "Virgo",
    "Mars": "Cancer", "Jupiter": "Capricorn", "Saturn": "Aries",
}

# ── Triplicity — Dorothean day/night convention ───────────────────────────────

TRIPLICITY_CONVENTION = "dorothean_day_night"

TRIPLICITY_MAP: dict[str, dict[str, str]] = {
    "fire":  {"day": "Sun",    "night": "Jupiter"},
    "earth": {"day": "Venus",  "night": "Moon"},
    "air":   {"day": "Saturn", "night": "Mercury"},
    "water": {"day": "Venus",  "night": "Mars"},
}

# ── Ptolemaic Terms/Bounds ────────────────────────────────────────────────────

TERMS_PTOLEMAIC: dict[str, list[tuple[int, str]]] = {
    "Aries":       [(6, "Jupiter"), (14, "Venus"),   (21, "Mercury"), (26, "Mars"),    (30, "Saturn")],
    "Taurus":      [(8, "Venus"),   (15, "Mercury"),  (22, "Jupiter"), (26, "Saturn"),  (30, "Mars")],
    "Gemini":      [(7, "Mercury"), (14, "Jupiter"),  (21, "Venus"),   (25, "Saturn"),  (30, "Mars")],
    "Cancer":      [(6, "Mars"),    (13, "Jupiter"),  (20, "Mercury"), (27, "Venus"),   (30, "Saturn")],
    "Leo":         [(6, "Saturn"),  (13, "Mercury"),  (19, "Venus"),   (25, "Jupiter"), (30, "Mars")],
    "Virgo":       [(7, "Mercury"), (13, "Venus"),    (18, "Jupiter"), (24, "Saturn"),  (30, "Mars")],
    "Libra":       [(6, "Saturn"),  (14, "Venus"),    (21, "Jupiter"), (28, "Mercury"), (30, "Mars")],
    "Scorpio":     [(6, "Mars"),    (14, "Jupiter"),  (21, "Venus"),   (27, "Mercury"), (30, "Saturn")],
    "Sagittarius": [(8, "Jupiter"), (14, "Venus"),    (19, "Mercury"), (25, "Saturn"),  (30, "Mars")],
    "Capricorn":   [(6, "Venus"),   (12, "Mercury"),  (19, "Jupiter"), (25, "Mars"),    (30, "Saturn")],
    "Aquarius":    [(6, "Saturn"),  (12, "Mercury"),  (20, "Venus"),   (25, "Jupiter"), (30, "Mars")],
    "Pisces":      [(8, "Venus"),   (14, "Jupiter"),  (20, "Mercury"), (26, "Mars"),    (30, "Saturn")],
}

# ── Face/Decan — Chaldean faces (10° each) ───────────────────────────────────

FACES_CHALDEAN: dict[str, list[tuple[int, str]]] = {
    "Aries":       [(10, "Mars"),    (20, "Sun"),     (30, "Venus")],
    "Taurus":      [(10, "Mercury"), (20, "Moon"),    (30, "Saturn")],
    "Gemini":      [(10, "Jupiter"), (20, "Mars"),    (30, "Sun")],
    "Cancer":      [(10, "Venus"),   (20, "Mercury"), (30, "Moon")],
    "Leo":         [(10, "Saturn"),  (20, "Jupiter"), (30, "Mars")],
    "Virgo":       [(10, "Sun"),     (20, "Venus"),   (30, "Mercury")],
    "Libra":       [(10, "Moon"),    (20, "Saturn"),  (30, "Jupiter")],
    "Scorpio":     [(10, "Mars"),    (20, "Sun"),     (30, "Venus")],
    "Sagittarius": [(10, "Mercury"), (20, "Moon"),    (30, "Saturn")],
    "Capricorn":   [(10, "Jupiter"), (20, "Mars"),    (30, "Sun")],
    "Aquarius":    [(10, "Venus"),   (20, "Mercury"), (30, "Moon")],
    "Pisces":      [(10, "Saturn"),  (20, "Jupiter"), (30, "Mars")],
}


def _get_term_ruler(sign: str, degree: float) -> str:
    for max_deg, planet in TERMS_PTOLEMAIC.get(sign, []):
        if degree < max_deg:
            return planet
    return "unknown"


def _get_face_ruler(sign: str, degree: float) -> str:
    for max_deg, planet in FACES_CHALDEAN.get(sign, []):
        if degree < max_deg:
            return planet
    return "unknown"


def evaluate_dignity(payload: dict, body_name: str) -> dict:
    """
    Returns the complete dignity profile for one planet.

    Score summary:
        Domicile  +5 | Detriment  -5
        Exaltation +4 | Fall       -4
        Triplicity +3
        Term/Bound +2
        Face/Decan +1

    Output fields:
        is_domicile, is_exalted, is_triplicity, is_term, is_face,
        is_detriment, is_fall,
        is_peregrine (internal/technical — do not surface as client language),
        peregrine_applicable (False for outer planets),
        modern_ruler,
        classical_score (traditional dignity layers only),
        modern_modifier (outer-planet domicile bonus),
        dignity_score   (classical_score + modern_modifier; backward-compat aggregate).
    """
    body_data = get_body_data(payload, body_name)
    if not body_data:
        return {}

    sign   = body_data.get("sign")
    degree = body_data.get("degree_decimal", 0.0) % 30.0  # 0–29.99° within sign

    chart_sect = evaluate_chart_sect(payload)
    is_outer   = body_name in OUTER_PLANETS

    result: dict = {
        "is_domicile":          False,
        "is_exalted":           False,
        "is_triplicity":        False,
        "is_term":              False,
        "is_face":              False,
        "is_detriment":         False,
        "is_fall":              False,
        "is_peregrine":         not is_outer,  # outer planets: flag not applicable
        "peregrine_applicable": not is_outer,
        "modern_ruler":         False,
        "classical_score":      0.0,
        "modern_modifier":      0.0,
    }

    # ── Domicile & Detriment ──────────────────────────────────────────────────
    if TRADITIONAL_DOMICILE.get(sign) == body_name:
        result["is_domicile"]    = True
        result["is_peregrine"]   = False
        result["classical_score"] += 5.0
    elif MODERN_DOMICILE.get(sign) == body_name:
        result["is_domicile"]    = True
        result["modern_ruler"]   = True
        result["is_peregrine"]   = False
        result["modern_modifier"] += 5.0

    if DETRIMENT_MAP.get(sign) == body_name:
        result["is_detriment"]   = True
        result["classical_score"] -= 5.0

    # ── Exaltation & Fall ─────────────────────────────────────────────────────
    if EXALTATION_MAP.get(body_name) == sign:
        result["is_exalted"]     = True
        result["is_peregrine"]   = False
        result["classical_score"] += 4.0

    if FALL_MAP.get(body_name) == sign:
        result["is_fall"]        = True
        result["classical_score"] -= 4.0

    # ── Sub-dignity layers (classical planets only) ───────────────────────────
    if not is_outer:
        element = get_sign_element(sign)
        if element and chart_sect in ("day", "night"):
            trip_ruler = TRIPLICITY_MAP.get(element, {}).get(chart_sect)
            if trip_ruler == body_name:
                result["is_triplicity"]  = True
                result["is_peregrine"]   = False
                result["classical_score"] += 3.0

        term_ruler = _get_term_ruler(sign, degree)
        if term_ruler == body_name:
            result["is_term"]        = True
            result["is_peregrine"]   = False
            result["classical_score"] += 2.0

        face_ruler = _get_face_ruler(sign, degree)
        if face_ruler == body_name:
            result["is_face"]        = True
            result["is_peregrine"]   = False
            result["classical_score"] += 1.0

    result["dignity_score"] = result["classical_score"] + result["modern_modifier"]
    result["methodology"] = get_active_methodology_metadata()
    return result
