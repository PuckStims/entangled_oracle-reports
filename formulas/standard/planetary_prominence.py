"""
Planetary prominence — structural centrality ranking.

Prominence is intentionally separate from condition:
  condition  asks: how well-supported / healthy is this planet?
  prominence asks: how structurally dominant / loud is this planet in the chart?

A retrograde planet can be highly prominent.
A well-dignified planet can be low prominence.
Station detection defers to per-body thresholds already resolved in the condition layer.
"""
from __future__ import annotations

from typing import Any, Dict, List

from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.planetary_condition import evaluate_all_planetary_conditions
from formulas.standard.standard_config import PROMINENCE_TIERS

MethodRegistry.register(
    method_id="planetary_prominence",
    category="core_standard",
    lineage_tags=["hellenistic", "modern_synthesis"],
    requires_exact_time=True,
    required_data=["angles", "standard_planets", "houses"],
)

PROMINENCE_WEIGHTS: Dict[str, float] = {
    "is_chart_ruler":     5.0,
    "is_luminary":        4.0,
    "is_conjunct_angle":  4.0,
    "is_angular_house":   3.0,
    "is_stationing":      3.0,
    "has_major_dignity":  2.0,
    "is_modern_co_ruler": 1.5,
    "is_succedent_house": 1.0,
}

THEORETICAL_MAX = 18.0


def _determine_tier(normalized_score: float) -> str:
    if normalized_score >= PROMINENCE_TIERS["DOMINANT"]:
        return "DOMINANT"
    if normalized_score >= PROMINENCE_TIERS["PROMINENT"]:
        return "PROMINENT"
    if normalized_score >= PROMINENCE_TIERS["PRESENT"]:
        return "PRESENT"
    return "BACKGROUND"


def evaluate_prominence(payload: dict) -> Dict[str, Any]:
    """
    Evaluates structural prominence for all standard planets.

    Uses condition records for per-body motion/angularity/dignity flags.
    Does NOT read overall_condition_score — prominence and condition are independent.
    """
    conditions  = evaluate_all_planetary_conditions(payload)
    ruler_data  = evaluate_chart_ruler(payload)

    primary_ruler   = ruler_data.get("primary_ruler")   if ruler_data.get("status") == "success" else None
    modern_co_ruler = ruler_data.get("modern_co_ruler") if ruler_data.get("status") == "success" else None

    scored_planets: List[Dict[str, Any]] = []

    for body_name, record in conditions.items():
        raw_score = 0.0
        drivers:  List[str] = []

        if body_name == primary_ruler:
            raw_score += PROMINENCE_WEIGHTS["is_chart_ruler"]
            drivers.append("Ascendant Ruler")
        elif body_name == modern_co_ruler:
            raw_score += PROMINENCE_WEIGHTS["is_modern_co_ruler"]
            drivers.append("Modern Ascendant Co-Ruler")

        if record.motion_condition.get("is_luminary"):
            raw_score += PROMINENCE_WEIGHTS["is_luminary"]
            drivers.append("Luminary")

        if record.accidental_dignity.get("is_conjunct_angle"):
            raw_score += PROMINENCE_WEIGHTS["is_conjunct_angle"]
            angle_label = record.accidental_dignity.get("conjunct_angle_name", "Angle")
            drivers.append(f"Conjunct {angle_label}")

        house_type = record.accidental_dignity.get("house_type")
        if house_type == "angular":
            raw_score += PROMINENCE_WEIGHTS["is_angular_house"]
            drivers.append("Angular House Placement")
        elif house_type == "succedent":
            raw_score += PROMINENCE_WEIGHTS["is_succedent_house"]

        if record.motion_condition.get("is_stationary"):
            raw_score += PROMINENCE_WEIGHTS["is_stationing"]
            drivers.append("Stationary Motion")

        if record.essential_dignity.get("is_domicile") or record.essential_dignity.get("is_exalted"):
            raw_score += PROMINENCE_WEIGHTS["has_major_dignity"]
            drivers.append("Major Essential Dignity")

        scored_planets.append({"body": body_name, "raw_score": raw_score, "drivers": drivers})

    actual_max = max((p["raw_score"] for p in scored_planets), default=1.0)
    ceiling    = max(THEORETICAL_MAX, actual_max)

    for p in scored_planets:
        p["normalized_score"] = round(p["raw_score"] / ceiling, 4)
        p["tier"]             = _determine_tier(p["normalized_score"])

    scored_planets.sort(key=lambda x: x["normalized_score"], reverse=True)

    return {
        "primary_ruler":      primary_ruler,
        "highest_prominence": scored_planets[0]["body"] if scored_planets else None,
        "rankings":           scored_planets,
        "methodology":        get_active_methodology_metadata(),
    }
