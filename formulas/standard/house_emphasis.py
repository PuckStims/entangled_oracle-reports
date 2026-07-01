"""
House emphasis and resourcing — structural importance and ruler-condition accessibility
of the 12 astrological houses.

CR-05: house_emphasis_score and house_resourcing_score are independent outputs.
  house_emphasis_score   = occupancy + chart-ruler presence + angle presence (structural weight)
  house_resourcing_score = ruler condition impact (ease/friction of access)

A severely challenged ruler lowers resourcing only; it does NOT reduce structural emphasis.

Note: Natal payload angles lack a 'house' field (except Vertex). In Whole Sign each
house sign equals its cusp sign, so angle house is resolved by sign-matching.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.dignity import TRADITIONAL_DOMICILE
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.planetary_condition import evaluate_all_planetary_conditions
from formulas.standard.standard_config import PROMINENCE_TIERS

MethodRegistry.register(
    method_id="evaluate_house_emphasis",
    category="core_standard",
    lineage_tags=["hellenistic", "traditional", "modern_synthesis"],
    requires_exact_time=True,
    required_data=["angles", "standard_planets", "houses"],
)

OCCUPANCY_WEIGHTS: Dict[str, float] = {
    "luminary":          3.0,
    "personal":          2.0,
    "social":            2.0,
    "outer":             1.0,
    "chart_ruler_bonus": 2.0,
    "angle_bonus":       3.0,
}

RULER_CONDITION_RESOURCING: Dict[str, float] = {
    "excellent":          3.0,
    "strong":             1.5,
    "neutral":            0.0,
    "challenged":         0.0,     # CR-05: challenged ruler ≠ less emphasis
    "severely_challenged": -1.0,   # slight friction on access only
}

EMPHASIS_THEORETICAL_MAX   = 12.0
RESOURCING_THEORETICAL_MAX = 3.0


def _get_house_signs(payload: dict) -> Dict[int, str]:
    houses = payload.get("houses", {})
    return {
        i: houses.get(f"House_{i}", {}).get("sign", "unknown")
        for i in range(1, 13)
    }


def _get_body_category(body_name: str) -> str:
    if body_name in ("Sun", "Moon"):
        return "luminary"
    if body_name in ("Mercury", "Venus", "Mars"):
        return "personal"
    if body_name in ("Jupiter", "Saturn"):
        return "social"
    return "outer"


def _find_house_for_sign(sign: str, house_signs: Dict[int, str]) -> Optional[int]:
    """Whole Sign: the house whose cusp sign matches the angle's sign."""
    for house_num, house_sign in house_signs.items():
        if house_sign == sign:
            return house_num
    return None


def _determine_tier(normalized: float) -> str:
    if normalized >= PROMINENCE_TIERS["DOMINANT"]:
        return "DOMINANT"
    if normalized >= PROMINENCE_TIERS["PROMINENT"]:
        return "PROMINENT"
    if normalized >= PROMINENCE_TIERS["PRESENT"]:
        return "PRESENT"
    return "BACKGROUND"


def evaluate_house_emphasis(payload: dict) -> Dict[str, Any]:
    """
    Evaluates all 12 houses for structural emphasis and resourcing accessibility.

    Per-house output includes:
        house_emphasis_score / house_emphasis_normalized / house_emphasis_tier
        house_resourcing_score / house_resourcing_normalized
        occupants, emphasis_drivers, resourcing_drivers
    """
    house_signs = _get_house_signs(payload)
    conditions  = evaluate_all_planetary_conditions(payload)
    ruler_data  = evaluate_chart_ruler(payload)
    primary_ruler = ruler_data.get("primary_ruler") if ruler_data.get("status") == "success" else None

    house_records: Dict[int, Dict[str, Any]] = {
        i: {
            "house":                  i,
            "sign":                   house_signs.get(i),
            "ruler":                  TRADITIONAL_DOMICILE.get(house_signs.get(i, "unknown"), None),
            "occupants":              [],
            "house_emphasis_score":   0.0,
            "house_resourcing_score": 0.0,
            "emphasis_drivers":       [],
            "resourcing_drivers":     [],
        }
        for i in range(1, 13)
    }

    # ── 1. Occupancy → emphasis ───────────────────────────────────────────────
    for body_name, data in payload.get("standard_planets", {}).items():
        if not isinstance(data, dict):
            continue
        house_num = data.get("house")
        if not (house_num and 1 <= house_num <= 12):
            continue

        weight = OCCUPANCY_WEIGHTS.get(_get_body_category(body_name), 0.0)
        house_records[house_num]["house_emphasis_score"] += weight
        house_records[house_num]["occupants"].append(body_name)

        if body_name == primary_ruler:
            house_records[house_num]["house_emphasis_score"] += OCCUPANCY_WEIGHTS["chart_ruler_bonus"]
            house_records[house_num]["emphasis_drivers"].append(
                f"Occupied by Chart Ruler ({body_name})"
            )

    # ── 2. Angle presence bonus → emphasis ───────────────────────────────────
    # Angles lack a 'house' key in the payload; locate by sign-matching in Whole Sign.
    for angle_name in ("Ascendant", "Midheaven"):
        angle_sign = payload.get("angles", {}).get(angle_name, {}).get("sign")
        if not angle_sign:
            continue
        house_num = _find_house_for_sign(angle_sign, house_signs)
        if house_num:
            house_records[house_num]["house_emphasis_score"] += OCCUPANCY_WEIGHTS["angle_bonus"]
            house_records[house_num]["emphasis_drivers"].append(
                f"Contains exact {angle_name} degree"
            )

    # ── 3. Ruler condition → resourcing (independent of emphasis) ─────────────
    for i, record in house_records.items():
        ruler = record["ruler"]
        if ruler and ruler in conditions:
            ruler_condition = conditions[ruler].condition_classification
            delta = RULER_CONDITION_RESOURCING.get(ruler_condition, 0.0)
            record["house_resourcing_score"] += delta
            if delta > 0:
                record["resourcing_drivers"].append(
                    f"House Ruler ({ruler}) in {ruler_condition} condition"
                )
            elif delta < 0:
                record["resourcing_drivers"].append(
                    f"House Ruler ({ruler}) severely challenged (access friction)"
                )

    # ── 4. Normalise ──────────────────────────────────────────────────────────
    actual_emph = max((r["house_emphasis_score"] for r in house_records.values()), default=1.0)
    emph_ceil   = max(EMPHASIS_THEORETICAL_MAX, actual_emph)

    actual_res  = max((r["house_resourcing_score"] for r in house_records.values()), default=1.0)
    res_ceil    = max(RESOURCING_THEORETICAL_MAX, actual_res)

    scored_houses: List[Dict[str, Any]] = []
    for i, record in house_records.items():
        emph_norm = max(0.0, round(record["house_emphasis_score"] / emph_ceil, 4))
        res_raw   = record["house_resourcing_score"]
        # Allow negative resourcing to pass through; clamp only for display
        res_norm  = round(res_raw / res_ceil, 4) if res_ceil else 0.0

        record["house_emphasis_normalized"]   = emph_norm
        record["house_emphasis_tier"]         = _determine_tier(emph_norm)
        record["house_resourcing_score"]      = round(res_raw, 4)
        record["house_resourcing_normalized"] = round(res_norm, 4)
        scored_houses.append(record)

    scored_houses.sort(key=lambda x: x["house_emphasis_normalized"], reverse=True)

    return {
        "most_emphasized_house": (
            scored_houses[0]["house"]
            if scored_houses and scored_houses[0]["house_emphasis_normalized"] > 0
            else None
        ),
        "rankings": scored_houses,
        "methodology": get_active_methodology_metadata(),
    }
