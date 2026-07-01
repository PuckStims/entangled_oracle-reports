"""
Planetary angularity — house placement and exact angle-conjunction detection.

CR-01: Uses canonical angle names from formulas.standard.normalization.
       Shorthand aliases (ASC, MC, DSC, IC) are resolved via ANGLE_ALIAS_MAP for
       any caller-supplied data; internal lookups always use canonical names.
"""
from __future__ import annotations

from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.normalization import ANGLE_ALIAS_MAP, CANONICAL_ANGLE_NAMES
from selectors.utils import get_body_data

MethodRegistry.register(
    method_id="planetary_angularity",
    category="core_standard",
    lineage_tags=["traditional", "hellenistic", "medieval"],
    requires_exact_time=True,
    required_data=["angles", "standard_planets"],
)

HOUSE_TYPES: dict[int, str] = {
    1: "angular",   4: "angular",   7: "angular",   10: "angular",
    2: "succedent", 5: "succedent", 8: "succedent", 11: "succedent",
    3: "cadent",    6: "cadent",    9: "cadent",    12: "cadent",
}

# Four chart axes checked for conjunction (Vertex excluded from condition angularity).
AXIS_ANGLES = ("Ascendant", "Descendant", "Midheaven", "Imum_Coeli")


def _shortest_arc(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2) % 360
    return min(diff, 360 - diff)


def evaluate_angularity(payload: dict, body_name: str, angle_orb: float = 8.0) -> dict:
    """
    Evaluates a planet's angularity state (accidental dignity baseline).

    The payload's angles dict is expected to use canonical names.
    If it contains shorthand keys (ASC, MC, etc.), they are resolved via ANGLE_ALIAS_MAP.

    Returns:
        house_number (int | None)
        house_type (str): 'angular' | 'succedent' | 'cadent' | 'unknown'
        is_conjunct_angle (bool)
        conjunct_angle_name (str | None): canonical name
        orb (float | None)
    """
    body_data = get_body_data(payload, body_name)
    if not body_data:
        return {
            "house_number":      None,
            "house_type":        "unknown",
            "is_conjunct_angle": False,
            "conjunct_angle_name": None,
            "orb":               None,
            "methodology":       get_active_methodology_metadata(),
        }

    house_number = body_data.get("house")
    house_type   = HOUSE_TYPES.get(house_number, "unknown")

    is_conjunct  = False
    conjunct_name: str | None = None
    closest_orb:  float | None = None
    body_lon = body_data.get("longitude")

    if body_lon is not None:
        # Normalise angle keys in the payload in case they use shorthand
        raw_angles = payload.get("angles", {})
        angles: dict[str, dict] = {
            ANGLE_ALIAS_MAP.get(k, k): v for k, v in raw_angles.items()
        }

        for angle_name in AXIS_ANGLES:
            angle_data = angles.get(angle_name)
            if not angle_data:
                continue
            angle_lon = angle_data.get("longitude")
            if angle_lon is None:
                continue
            dist = _shortest_arc(body_lon, angle_lon)
            if dist <= angle_orb and (closest_orb is None or dist < closest_orb):
                is_conjunct  = True
                conjunct_name = angle_name
                closest_orb  = round(dist, 4)

    return {
        "house_number":        house_number,
        "house_type":          house_type,
        "is_conjunct_angle":   is_conjunct,
        "conjunct_angle_name": conjunct_name,
        "orb":                 closest_orb,
        "methodology":         get_active_methodology_metadata(),
    }
