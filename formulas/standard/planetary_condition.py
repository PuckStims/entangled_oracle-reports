"""
Planetary condition — aggregates dignity, angularity, sect, and motion into
a unified PlanetConditionRecord for each standard planet.

CR-03: Per-body station thresholds replace the universal 0.05 deg/day threshold.
CR-04: Retrograde is NOT a condition score penalty; it is a routing_tag descriptor.
CR-07: Confidence states use controlled constants from formulas.standard.confidence.
CR-09: PlanetConditionRecord imported from formulas.standard.contracts.
"""
from __future__ import annotations

from typing import Dict

from formulas.standard.angularity import evaluate_angularity
from formulas.standard.confidence import (
    ANGLE_DEPENDENT_UNAVAILABLE,
    APPROXIMATE_BIRTH_TIME,
    EXACT_BIRTH_TIME,
    UNKNOWN_BIRTH_TIME,
    VALID_CONFIDENCE_STATES,
)
from formulas.standard.contracts import PlanetConditionRecord
from formulas.standard.dignity import evaluate_dignity
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.sect import evaluate_chart_sect, evaluate_planetary_sect
from formulas.standard.standard_config import ANGULARITY_WEIGHTS
from selectors.utils import get_body_data

MethodRegistry.register(
    method_id="evaluate_all_planetary_conditions",
    category="core_standard",
    lineage_tags=["traditional", "modern_synthesis"],
    requires_exact_time=False,
    required_data=["standard_planets", "angles", "houses"],
)

STANDARD_BODIES = (
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
)

# CR-03: Per-body station thresholds (degrees/day).
# Sun and Moon do not station; North_Node, South_Node, Lilith_BML are omitted.
STATION_THRESHOLDS: Dict[str, float] = {
    "Mercury": 0.10,
    "Venus":   0.07,
    "Mars":    0.05,
    "Jupiter": 0.020,
    "Saturn":  0.012,
    "Uranus":  0.007,
    "Neptune": 0.005,
    "Pluto":   0.005,
    "Chiron":  0.007,
}


def _is_stationary(body_name: str, speed: float) -> bool:
    """True when abs(speed) is within the body's per-body station threshold."""
    threshold = STATION_THRESHOLDS.get(body_name)
    if threshold is None:
        return False
    return abs(speed) < threshold


def _calculate_base_condition_score(
    dignity: dict,
    angularity: dict,
    sect: dict,
    motion: dict,
) -> float:
    """
    Raw condition score from essential and accidental dignity components.

    CR-04: No retrograde penalty. Retrograde → routing_tag only.
    Station remains a bonus only when detected via per-body threshold (CR-03).
    """
    score = dignity.get("dignity_score", 0.0)

    house_type = angularity.get("house_type", "unknown")
    if house_type in ANGULARITY_WEIGHTS:
        multiplier = ANGULARITY_WEIGHTS[house_type]["multiplier"]
        score += 3.0 if multiplier > 1.0 else (-1.0 if multiplier < 1.0 else 0.0)

    if angularity.get("is_conjunct_angle"):
        score += 4.0

    if sect.get("is_in_sect"):
        score += 2.0

    if motion.get("is_stationary"):
        score += 3.0

    return score


def _classify_condition(score: float) -> str:
    if score >= 8.0:
        return "excellent"
    if score >= 4.0:
        return "strong"
    if score >= 0.0:
        return "neutral"
    if score >= -4.0:
        return "challenged"
    return "severely_challenged"


def _resolve_confidence(payload: dict, angularity: dict) -> str:
    """
    CR-07 confidence state for a single body's condition record.

    Reflects the chart's actual recorded birth-time state
    (payload.user_profile.birth_time_state / birth_time_confidence)
    first. A noon-placeholder Ascendant computed for a simple_mode/
    unknown-time chart still resolves to a real house_type, so the
    original Ascendant/house_type-only check could never actually detect
    an unknown or approximate birth time in practice -- it only ever
    fired for payloads missing angles entirely. Falls back to that
    original check only when the payload carries no explicit birth-time
    state at all (e.g. minimal hand-built test payloads), preserving
    prior behavior for those.
    """
    asc_lon = payload.get("angles", {}).get("Ascendant", {}).get("longitude")
    if asc_lon is None:
        return ANGLE_DEPENDENT_UNAVAILABLE

    profile = payload.get("user_profile")
    profile = profile if isinstance(profile, dict) else {}
    birth_time_state = profile.get("birth_time_state") or profile.get("birth_time_confidence")

    if birth_time_state in VALID_CONFIDENCE_STATES:
        return birth_time_state

    if bool(payload.get("simple_mode") or profile.get("simple_mode")):
        return UNKNOWN_BIRTH_TIME

    if angularity.get("house_type") == "unknown":
        return APPROXIMATE_BIRTH_TIME

    return EXACT_BIRTH_TIME


def evaluate_all_planetary_conditions(
    payload: dict,
) -> Dict[str, PlanetConditionRecord]:
    """
    Builds a PlanetConditionRecord for every standard planet in the payload.

    CR-04: Retrograde → routing_tags only, no score impact.
    CR-03: Station detection uses per-body thresholds.
    CR-07: Each record carries a controlled confidence state.
    """
    chart_sect = evaluate_chart_sect(payload)
    methodology = get_active_methodology_metadata()
    conditions: Dict[str, PlanetConditionRecord] = {}

    for body_name in STANDARD_BODIES:
        body_data = get_body_data(payload, body_name)
        if not body_data:
            continue

        dignity_profile    = evaluate_dignity(payload, body_name)
        angularity_profile = evaluate_angularity(payload, body_name)
        sect_profile       = evaluate_planetary_sect(payload, body_name, chart_sect)

        speed         = body_data.get("speed", 0.0)
        is_retrograde = speed < 0
        is_stationary = _is_stationary(body_name, speed)

        motion_profile = {
            "speed":         speed,
            "is_retrograde": is_retrograde,
            "is_stationary": is_stationary,
            "is_luminary":   body_name in ("Sun", "Moon"),
        }

        raw_score      = _calculate_base_condition_score(
            dignity_profile, angularity_profile, sect_profile, motion_profile
        )
        classification = _classify_condition(raw_score)
        confidence     = _resolve_confidence(payload, angularity_profile)

        routing_tags: list[str] = []
        if is_retrograde:
            routing_tags.append("retrograde")
        if is_stationary:
            routing_tags.append("stationary")

        conditions[body_name] = PlanetConditionRecord(
            body=body_name,
            overall_condition_score=raw_score,
            condition_classification=classification,
            essential_dignity=dignity_profile,
            accidental_dignity=angularity_profile,
            sect_condition=sect_profile,
            motion_condition=motion_profile,
            angularity=angularity_profile.get("house_type", "unknown"),
            house_context=body_data.get("house", 0),
            aspect_network={},
            rulership_context={},
            dispositor_context={},
            reception_context={},
            supporting_factors=[],
            pressure_factors=[],
            routing_tags=routing_tags,
            confidence=confidence,
            methodology_id=methodology["id"],
            methodology_label=methodology["label"],
            zodiac=methodology["zodiac"],
            house_system=methodology["house_system"],
            audit_data={"chart_sect": chart_sect},
        )

    return conditions
