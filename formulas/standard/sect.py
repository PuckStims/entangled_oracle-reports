"""
Diurnal/nocturnal sect determination and planetary sect evaluation.

CR-02: Sect is determined via geometric horizon (ASC longitude), not Whole Sign house number.
CR-07: All outputs carry controlled confidence states from formulas.standard.confidence.
"""
from __future__ import annotations

from formulas.standard.confidence import (
    ANGLE_DEPENDENT_UNAVAILABLE,
    EXACT_BIRTH_TIME,
    PROVISIONAL_NEAR_HORIZON,
)
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.method_registry import MethodRegistry
from selectors.utils import get_body_data

MethodRegistry.register(
    method_id="chart_sect",
    category="core_standard",
    lineage_tags=["hellenistic", "traditional"],
    requires_exact_time=False,
    required_data=["angles", "standard_planets"],
    time_requirement="exact_birth_time_or_provisional",
)

DIURNAL_PLANETS = ("Sun", "Jupiter", "Saturn")
NOCTURNAL_PLANETS = ("Moon", "Venus", "Mars")

# Mercury convention (documented): Oriental = Morning Star = diurnal faction.
# Mercury is Oriental when (merc_lon - sun_lon) % 360 > 180.
MERCURY_SECT_CONVENTION = "oriental_diurnal"

# Degrees from the ASC/DSC axis within which sect result is flagged provisional.
HORIZON_PROXIMITY_THRESHOLD = 5.0


def _sun_above_horizon(sun_lon: float, asc_lon: float) -> bool:
    """
    True when the Sun occupies the upper hemisphere (above the geometric horizon).
    The upper arc runs counterclockwise from ASC through houses 12→11→10(MC)→9→8→7 to DSC.
    (sun_lon - asc_lon + 360) % 360 < 180  →  day chart.
    """
    return (sun_lon - asc_lon + 360.0) % 360.0 < 180.0


def evaluate_chart_sect(payload: dict) -> str:
    """
    Returns 'day', 'night', or 'unknown'.
    Backward-compatible string wrapper — call evaluate_chart_sect_detailed() for confidence.
    """
    return evaluate_chart_sect_detailed(payload)["sect"]


def evaluate_chart_sect_detailed(payload: dict) -> dict:
    """
    Determines chart sect with full confidence metadata.

    Returns:
        sect (str): 'day' | 'night' | 'unknown'
        confidence (str): CR-07 controlled state
        missing_inputs (list[str])
        sun_longitude (float, optional)
        asc_longitude (float, optional)
        sun_horizon_diff (float, optional)
    """
    methodology = get_active_methodology_metadata()
    sun_data = get_body_data(payload, "Sun")
    if not sun_data:
        return {
            "sect": "unknown",
            "confidence": ANGLE_DEPENDENT_UNAVAILABLE,
            "missing_inputs": ["Sun position"],
            "methodology": methodology,
        }

    sun_lon = sun_data.get("longitude")
    if sun_lon is None:
        return {
            "sect": "unknown",
            "confidence": ANGLE_DEPENDENT_UNAVAILABLE,
            "missing_inputs": ["Sun longitude"],
            "methodology": methodology,
        }

    asc_lon = payload.get("angles", {}).get("Ascendant", {}).get("longitude")
    if asc_lon is None:
        return {
            "sect": "unknown",
            "confidence": ANGLE_DEPENDENT_UNAVAILABLE,
            "missing_inputs": ["Ascendant longitude"],
            "methodology": methodology,
        }

    diff = (sun_lon - asc_lon + 360.0) % 360.0

    # Sun exactly on ASC or DSC axis — indeterminate
    if diff < 0.001 or abs(diff - 180.0) < 0.001:
        return {
            "sect": "unknown",
            "confidence": PROVISIONAL_NEAR_HORIZON,
            "missing_inputs": [],
            "sun_longitude": sun_lon,
            "asc_longitude": asc_lon,
            "sun_horizon_diff": round(diff, 4),
            "note": "Sun on horizon axis; sect indeterminate.",
            "methodology": methodology,
        }

    sect = "day" if diff < 180.0 else "night"

    near_asc = diff < HORIZON_PROXIMITY_THRESHOLD
    near_dsc = (180.0 - HORIZON_PROXIMITY_THRESHOLD) < diff < (180.0 + HORIZON_PROXIMITY_THRESHOLD)
    confidence = PROVISIONAL_NEAR_HORIZON if (near_asc or near_dsc) else EXACT_BIRTH_TIME

    return {
        "sect": sect,
        "confidence": confidence,
        "missing_inputs": [],
        "sun_longitude": sun_lon,
        "asc_longitude": asc_lon,
        "sun_horizon_diff": round(diff, 4),
        "methodology": methodology,
    }


def get_sect_light(chart_sect: str) -> str:
    if chart_sect == "day":
        return "Sun"
    if chart_sect == "night":
        return "Moon"
    return "unknown"


def evaluate_planetary_sect(payload: dict, body_name: str, chart_sect: str) -> dict:
    """
    Evaluates planetary sect condition.
    Mercury's sect is dynamic (Oriental/Occidental phase); see MERCURY_SECT_CONVENTION.
    """
    sect_faction = "neutral"

    if body_name == "Mercury":
        mercury_data = get_body_data(payload, "Mercury")
        sun_data = get_body_data(payload, "Sun")
        if mercury_data and sun_data:
            merc_lon = mercury_data.get("longitude", 0)
            sun_lon = sun_data.get("longitude", 0)
            # Oriental (Morning Star, behind Sun): (merc - sun) % 360 > 180 → diurnal
            sect_faction = "diurnal" if (merc_lon - sun_lon) % 360 > 180 else "nocturnal"
    elif body_name in DIURNAL_PLANETS:
        sect_faction = "diurnal"
    elif body_name in NOCTURNAL_PLANETS:
        sect_faction = "nocturnal"

    is_in_sect = (
        (chart_sect == "day"   and sect_faction == "diurnal") or
        (chart_sect == "night" and sect_faction == "nocturnal")
    )

    return {
        "chart_sect":     chart_sect,
        "planet_faction": sect_faction,
        "is_in_sect":     is_in_sect,
        "methodology":    get_active_methodology_metadata(),
    }
