"""
Luminary and broad chart-structure calculations for the standard natal layer.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from config import SIGN_ELEMENTS, SIGN_MODALITIES
from formulas.standard.confidence import ANGLE_DEPENDENT_UNAVAILABLE, EXACT_BIRTH_TIME
from formulas.standard.method_registry import MethodRegistry
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from formulas.standard.planetary_prominence import evaluate_prominence
from selectors.utils import angular_distance, get_aspect_from_payload, get_body_data, get_sign_element, get_sign_modality

MethodRegistry.register(
    method_id="chart_structure",
    category="core_standard",
    lineage_tags=["standard_natal_structure"],
    requires_exact_time=False,
    required_data=["standard_planets", "angles", "houses", "aspects"],
)

CORE_DISTRIBUTION_BODIES = (
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
)
EXPANDED_DISTRIBUTION_BODIES = (
    ("Uranus", "established_niche"),
    ("Neptune", "established_niche"),
    ("Pluto", "established_niche"),
    ("Chiron", "established_niche"),
)
POLARITY_SIGNS = {
    "yang": {"Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"},
    "yin": {"Taurus", "Cancer", "Virgo", "Scorpio", "Capricorn", "Pisces"},
}


def _all_distribution_counts(bodies: list[tuple[str, str]], payload: dict) -> dict[str, Any]:
    element_counts = Counter({"fire": 0, "earth": 0, "air": 0, "water": 0})
    modality_counts = Counter({"cardinal": 0, "fixed": 0, "mutable": 0})
    polarity_counts = Counter({"yang": 0, "yin": 0})
    included_bodies = []

    for body_name, status in bodies:
        body_data = get_body_data(payload, body_name)
        if not body_data:
            continue
        sign = body_data.get("sign", "")
        element = get_sign_element(sign)
        modality = get_sign_modality(sign)
        polarity = "yang" if sign in POLARITY_SIGNS["yang"] else "yin"
        if element in element_counts:
            element_counts[element] += 1
        if modality in modality_counts:
            modality_counts[modality] += 1
        polarity_counts[polarity] += 1
        included_bodies.append({"body": body_name, "status": status, "sign": sign})

    return {
        "element_counts": dict(element_counts),
        "modality_counts": dict(modality_counts),
        "polarity_counts": dict(polarity_counts),
        "weighted_counts": {
            "elements": dict(element_counts),
            "modalities": dict(modality_counts),
            "polarities": dict(polarity_counts),
            "weighting_logic": "uniform_body_weight",
        },
        "included_bodies": included_bodies,
    }


def _distribution_dominance(counts: dict[str, int], prominence_weights: dict[str, float], payload: dict, attribute: str) -> dict[str, Any]:
    structural_weights = Counter()
    for body_name, weight in prominence_weights.items():
        sign = get_body_data(payload, body_name).get("sign", "")
        if attribute == "element":
            key = get_sign_element(sign)
        elif attribute == "modality":
            key = get_sign_modality(sign)
        else:
            key = "yang" if sign in POLARITY_SIGNS["yang"] else "yin"
        structural_weights[key] += weight

    dominant_key = max(counts, key=lambda key: (counts[key], structural_weights.get(key, 0.0)))
    top_count = counts[dominant_key]
    runner_up = sorted(counts.values(), reverse=True)[1] if len(counts) > 1 else 0
    is_structurally_dominant = top_count > runner_up and structural_weights.get(dominant_key, 0.0) >= 0.9
    return {
        "dominant_key": dominant_key,
        "dominance_supported": is_structurally_dominant,
        "structural_weights": dict(structural_weights),
    }


def evaluate_chart_structure(payload: dict) -> dict[str, Any]:
    methodology = get_active_methodology_metadata()
    sun = get_body_data(payload, "Sun")
    moon = get_body_data(payload, "Moon")
    prominence = evaluate_prominence(payload)
    prominence_weights = {
        item["body"]: item.get("normalized_score", 0.0)
        for item in prominence.get("rankings", [])
    }

    lunar_phase = {
        "astronomical_phase_angle": None,
        "phase_category": "unavailable",
        "confidence": ANGLE_DEPENDENT_UNAVAILABLE,
    }
    sun_moon_architecture = {
        "state": "unavailable",
        "aspect": None,
        "sign_relationship": None,
        "house_relationship": None,
        "element_relationship": None,
        "modality_relationship": None,
        "aspect_strength": 0.0,
    }
    if sun and moon:
        angle = angular_distance(sun.get("longitude", 0.0), moon.get("longitude", 0.0))
        if angle < 45:
            category = "new_to_crescent"
        elif angle < 90:
            category = "crescent_to_quarter"
        elif angle < 135:
            category = "quarter_to_gibbous"
        elif angle < 180:
            category = "gibbous_to_full"
        else:
            category = "waning"
        lunar_phase = {
            "astronomical_phase_angle": round(angle, 4),
            "phase_category": category,
            "confidence": EXACT_BIRTH_TIME,
        }
        sun_moon_aspect = get_aspect_from_payload(payload, "Sun", "Moon")
        if sun_moon_aspect:
            aspect_type = sun_moon_aspect.get("aspect")
            if aspect_type in {"Trine", "Sextile"}:
                state = "direct_integration"
            elif aspect_type in {"Square", "Opposition"}:
                state = "productive_tension"
            else:
                state = "direct_integration"
            strength = max(0.0, 1.0 - (float(sun_moon_aspect.get("orb", 0.0)) / 10.0))
        else:
            aspect_type = None
            state = "contrast_without_major_aspect"
            strength = 0.0

        sun_sign = sun.get("sign", "")
        moon_sign = moon.get("sign", "")
        sun_moon_architecture = {
            "state": state,
            "aspect": aspect_type,
            "sign_relationship": "same_sign" if sun_sign == moon_sign else "different_signs",
            "house_relationship": "same_house" if sun.get("house") == moon.get("house") else "different_houses",
            "element_relationship": "reinforcing" if get_sign_element(sun_sign) == get_sign_element(moon_sign) else "contrasting",
            "modality_relationship": "reinforcing" if get_sign_modality(sun_sign) == get_sign_modality(moon_sign) else "contrasting",
            "aspect_strength": round(strength, 4),
        }

    simple_mode = bool(payload.get("user_profile", {}).get("simple_mode") or payload.get("simple_mode"))
    hemisphere = {
        "confidence": ANGLE_DEPENDENT_UNAVAILABLE if simple_mode else EXACT_BIRTH_TIME,
        "above_horizon": None,
        "below_horizon": None,
        "eastern": None,
        "western": None,
        "quadrants": {},
    }
    if not simple_mode:
        asc = payload.get("angles", {}).get("Ascendant", {}).get("longitude")
        mc = payload.get("angles", {}).get("Midheaven", {}).get("longitude")
        if isinstance(asc, (int, float)) and isinstance(mc, (int, float)):
            above = below = east = west = 0
            quadrants = Counter({"1": 0, "2": 0, "3": 0, "4": 0})
            for body_name in CORE_DISTRIBUTION_BODIES:
                body_data = get_body_data(payload, body_name)
                if not body_data:
                    continue
                body_lon = body_data.get("longitude")
                if not isinstance(body_lon, (int, float)):
                    continue
                diff = (body_lon - asc) % 360
                if diff < 180:
                    above += 1
                else:
                    below += 1
                if diff < 90 or diff >= 270:
                    east += 1
                else:
                    west += 1
                house = body_data.get("house")
                if house in {10, 11, 12}:
                    quadrants["1"] += 1
                elif house in {1, 2, 3}:
                    quadrants["2"] += 1
                elif house in {4, 5, 6}:
                    quadrants["3"] += 1
                elif house in {7, 8, 9}:
                    quadrants["4"] += 1
            hemisphere = {
                "confidence": EXACT_BIRTH_TIME,
                "above_horizon": above,
                "below_horizon": below,
                "eastern": east,
                "western": west,
                "quadrants": dict(quadrants),
            }

    core_distribution = _all_distribution_counts(
        [(body, "core_standard") for body in CORE_DISTRIBUTION_BODIES],
        payload,
    )
    expanded_distribution = _all_distribution_counts(
        [(body, "core_standard") for body in CORE_DISTRIBUTION_BODIES] + list(EXPANDED_DISTRIBUTION_BODIES),
        payload,
    )

    return {
        "methodology": methodology,
        "formula_version": "2.0.0",
        "lunar_phase": lunar_phase,
        "sun_moon_architecture": sun_moon_architecture,
        "hemisphere_and_quadrant": hemisphere,
        "core_standard_distribution": {
            **core_distribution,
            "dominance_assessment": {
                "elements": _distribution_dominance(core_distribution["element_counts"], prominence_weights, payload, "element"),
                "modalities": _distribution_dominance(core_distribution["modality_counts"], prominence_weights, payload, "modality"),
                "polarities": _distribution_dominance(core_distribution["polarity_counts"], prominence_weights, payload, "polarity"),
            },
        },
        "expanded_established_niche_distribution": {
            **expanded_distribution,
            "dominance_assessment": {
                "elements": _distribution_dominance(expanded_distribution["element_counts"], prominence_weights, payload, "element"),
                "modalities": _distribution_dominance(expanded_distribution["modality_counts"], prominence_weights, payload, "modality"),
                "polarities": _distribution_dominance(expanded_distribution["polarity_counts"], prominence_weights, payload, "polarity"),
            },
        },
    }
