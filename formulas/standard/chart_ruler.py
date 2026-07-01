"""
Chart ruler identification and condition assessment.

CR-03: Per-body station thresholds replace the universal 0.05 deg/day threshold.
CR-07: Returns controlled confidence states; gates on Ascendant availability.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from formulas.standard.angularity import evaluate_angularity
from formulas.standard.confidence import ANGLE_DEPENDENT_UNAVAILABLE, EXACT_BIRTH_TIME
from formulas.standard.dignity import MODERN_DOMICILE, TRADITIONAL_DOMICILE, evaluate_dignity
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.planetary_condition import STATION_THRESHOLDS, _is_stationary
from formulas.standard.sect import evaluate_chart_sect, evaluate_planetary_sect
from selectors.utils import get_angle_data, get_aspect_from_payload, get_body_data

MethodRegistry.register(
    method_id="chart_ruler_evaluation",
    category="core_standard",
    lineage_tags=["traditional", "hellenistic", "modern_synthesis"],
    requires_exact_time=True,
    required_data=["angles", "standard_planets"],
)


def _get_rulers_for_sign(sign: str) -> Dict[str, Optional[str]]:
    """Traditional primary ruler + modern co-ruler (if any)."""
    return {
        "primary_ruler":   TRADITIONAL_DOMICILE.get(sign),
        "modern_co_ruler": MODERN_DOMICILE.get(sign),
    }


def _check_luminary_support(payload: dict, body_name: str) -> Dict[str, Any]:
    sun_aspect  = get_aspect_from_payload(payload, body_name, "Sun")
    moon_aspect = get_aspect_from_payload(payload, body_name, "Moon")
    return {
        "aspects_sun":      bool(sun_aspect),
        "sun_aspect_type":  sun_aspect.get("aspect") if sun_aspect else None,
        "aspects_moon":     bool(moon_aspect),
        "moon_aspect_type": moon_aspect.get("aspect") if moon_aspect else None,
    }


def evaluate_chart_ruler(payload: dict) -> Dict[str, Any]:
    """
    Identifies the Chart Ruler and builds a condition record.

    CR-07: Returns confidence and missing_inputs on every code path.
    Returns status='unavailable' when Ascendant is missing (unknown birth time).
    """
    methodology = get_active_methodology_metadata()
    ascendant_data = get_angle_data(payload, "Ascendant")
    if not ascendant_data or not ascendant_data.get("sign"):
        return {
            "status":         "unavailable",
            "confidence":     ANGLE_DEPENDENT_UNAVAILABLE,
            "missing_inputs": ["Ascendant (exact birth time required)"],
            "reason":         "Missing or invalid Ascendant; birth time may be unknown.",
            "methodology":    methodology,
        }

    ascendant_sign     = ascendant_data["sign"]
    rulers             = _get_rulers_for_sign(ascendant_sign)
    primary_ruler_name = rulers["primary_ruler"]

    if not primary_ruler_name:
        return {
            "status":         "error",
            "confidence":     ANGLE_DEPENDENT_UNAVAILABLE,
            "missing_inputs": [],
            "reason":         f"No ruler mapped for sign {ascendant_sign}.",
            "methodology":    methodology,
        }

    ruler_data = get_body_data(payload, primary_ruler_name)
    if not ruler_data:
        return {
            "status":         "error",
            "confidence":     ANGLE_DEPENDENT_UNAVAILABLE,
            "missing_inputs": [primary_ruler_name],
            "reason":         f"Ruler {primary_ruler_name} missing from payload.",
            "methodology":    methodology,
        }

    chart_sect         = evaluate_chart_sect(payload)
    dignity_profile    = evaluate_dignity(payload, primary_ruler_name)
    angularity_profile = evaluate_angularity(payload, primary_ruler_name)
    sect_profile       = evaluate_planetary_sect(payload, primary_ruler_name, chart_sect)
    luminary_support   = _check_luminary_support(payload, primary_ruler_name)

    speed         = ruler_data.get("speed", 0.0)
    is_retrograde = speed < 0
    is_stationary = _is_stationary(primary_ruler_name, speed)

    return {
        "status":          "success",
        "confidence":      EXACT_BIRTH_TIME,
        "missing_inputs":  [],
        "ascendant_sign":  ascendant_sign,
        "primary_ruler":   primary_ruler_name,
        "modern_co_ruler": rulers["modern_co_ruler"],
        "methodology":     methodology,
        "condition_record": {
            "placement": {
                "sign":           ruler_data.get("sign"),
                "house":          ruler_data.get("house"),
                "degree_decimal": ruler_data.get("degree_decimal"),
            },
            "motion": {
                "is_retrograde": is_retrograde,
                "is_stationary": is_stationary,
                "speed":         speed,
            },
            "dignity":              dignity_profile,
            "angularity":           angularity_profile,
            "sect":                 sect_profile,
            "luminary_integration": luminary_support,
        },
    }
