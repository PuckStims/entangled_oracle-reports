"""
Established-niche body governance and specialist context evaluation.
"""

from __future__ import annotations

from typing import Any

from config import MAJOR_ASPECTS
from formulas.governance_registry import (
    ASTEROID_ELIGIBILITY_REGISTRY,
    METHOD_STATUS_ESTABLISHED_NICHE,
    REPORT_PROFILE_CORE_STANDARD_ONLY,
    get_body_registry_record,
    get_report_layer_profile,
    layer_allows,
)
from formulas.standard.confidence import ANGLE_DEPENDENT_UNAVAILABLE, EXACT_BIRTH_TIME
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from selectors.utils import angle_exists, angular_distance, get_angle_data, get_angle_longitude, get_aspect_from_payload, get_body_data

SPECIALIST_BODY_POLICIES = {
    "Chiron": {
        "display_name": "Chiron",
        "method_name": "specialist_body_context",
        "eligible_report_types": ("soul_ecosystem",),
        "default_visibility": "supporting_context",
        "allowed_use_cases": (
            "natal sign placement",
            "natal house placement",
            "natal aspect context",
            "angle contact",
            "retrograde context",
            "forecast activation",
        ),
        "restricted_use_cases": (
            "not part of core-standard dominance scoring",
            "not permitted to override chart ruler",
            "not permitted to override luminaries",
            "not part of traditional dignity",
            "not part of traditional dispositorship",
            "not part of sect",
            "not part of house rulership",
        ),
        "tradition_tags": ["modern", "specialist"],
    },
    "Lilith_BML": {
        "display_name": "Black Moon Lilith",
        "method_name": "specialist_body_context",
        "eligible_report_types": ("soul_ecosystem", "year_ahead", "personal_forecast"),
        "default_visibility": "expanded_section",
        "allowed_use_cases": (
            "sign",
            "Whole Sign house",
            "major aspects",
            "angle contact",
            "forecast activation",
            "technical appendix",
            "expanded report sections",
        ),
        "restricted_use_cases": (
            "not interchangeable with asteroid Lilith",
            "not permitted to become EO proprietary evidence unless explicitly defined",
        ),
        "tradition_tags": ["modern", "lunar_apogee", "specialist"],
    },
}

for key, record in ASTEROID_ELIGIBILITY_REGISTRY.items():
    SPECIALIST_BODY_POLICIES.setdefault(
        key,
        {
            "display_name": record.display_name,
            "method_name": "specialist_body_context",
            "eligible_report_types": record.eligible_report_types,
            "default_visibility": record.default_visibility,
            "allowed_use_cases": record.allowed_use_cases,
            "restricted_use_cases": record.restricted_use_cases,
            "tradition_tags": list(record.lineage),
        },
    )

ANGLE_NAMES = ("Ascendant", "Midheaven", "Descendant", "Imum_Coeli")


def _major_aspects_for_body(payload: dict, body_key: str) -> list[dict[str, Any]]:
    matches = []
    for aspect in payload.get("aspects", []):
        if aspect.get("body_1") == body_key or aspect.get("body_2") == body_key:
            matches.append(aspect)
    return matches


def _angle_contacts(payload: dict, body_key: str) -> tuple[list[dict[str, Any]], str]:
    user_profile = payload.get("user_profile", {}) if isinstance(payload, dict) else {}
    if bool(user_profile.get("simple_mode") or payload.get("simple_mode")):
        return [], ANGLE_DEPENDENT_UNAVAILABLE

    body_data = get_body_data(payload, body_key)
    longitude = body_data.get("longitude")
    if not isinstance(longitude, (int, float)):
        return [], ANGLE_DEPENDENT_UNAVAILABLE

    contacts = []
    for angle_name in ANGLE_NAMES:
        if not angle_exists(payload, angle_name):
            continue
        angle_longitude = get_angle_longitude(payload, angle_name)
        if not isinstance(angle_longitude, (int, float)):
            continue
        distance = angular_distance(float(longitude), float(angle_longitude))
        for aspect_name, exact in MAJOR_ASPECTS:
            orb = abs(distance - exact)
            if orb <= 3.0:
                contacts.append(
                    {
                        "angle": angle_name,
                        "aspect": aspect_name,
                        "orb": round(orb, 4),
                    }
                )
                break
    return contacts, EXACT_BIRTH_TIME


def evaluate_specialist_body(
    payload: dict,
    body_key: str,
    report_type: str,
    report_profile: str | None = None,
) -> dict[str, Any]:
    methodology = get_active_methodology_metadata()
    policy = SPECIALIST_BODY_POLICIES.get(body_key)
    registry_record = get_body_registry_record(body_key)
    report_profile = report_profile or get_report_layer_profile(report_type)
    report_allowed = layer_allows(METHOD_STATUS_ESTABLISHED_NICHE, report_profile)

    if not policy or not registry_record:
        return {
            "method_status": METHOD_STATUS_ESTABLISHED_NICHE,
            "method_name": "specialist_body_context",
            "body_or_point": body_key,
            "visibility_state": "suppressed",
            "report_eligibility": report_profile,
            "confidence_state": ANGLE_DEPENDENT_UNAVAILABLE,
            "supporting_inputs": [],
            "limitations": ["unregistered_specialist_body"],
            "methodology": methodology,
        }

    body_data = get_body_data(payload, body_key)
    if not body_data:
        return {
            "method_status": METHOD_STATUS_ESTABLISHED_NICHE,
            "method_name": policy["method_name"],
            "tradition_tags": policy["tradition_tags"],
            "body_or_point": body_key,
            "formula_version": "3.0.0",
            "report_eligibility": report_profile,
            "visibility_state": "suppressed",
            "birth_time_dependency": "angle_contacts_and_house_require_exact_time",
            "confidence_state": ANGLE_DEPENDENT_UNAVAILABLE,
            "supporting_inputs": [],
            "limitations": ["body_missing_from_payload"],
            "methodology": methodology,
        }

    aspects = _major_aspects_for_body(payload, body_key)
    angle_contacts, angle_confidence = _angle_contacts(payload, body_key)
    confidence_state = EXACT_BIRTH_TIME if angle_confidence == EXACT_BIRTH_TIME else angle_confidence
    visibility_state = policy["default_visibility"]
    limitations = []

    if report_type not in policy["eligible_report_types"]:
        visibility_state = "suppressed"
        limitations.append("body_not_report_eligible")
    if not report_allowed:
        visibility_state = "suppressed"
        limitations.append("report_profile_excludes_established_niche")
    if angle_confidence == ANGLE_DEPENDENT_UNAVAILABLE:
        limitations.append("angle_contacts_unavailable_without_exact_birth_time")

    return {
        "method_status": METHOD_STATUS_ESTABLISHED_NICHE,
        "method_name": policy["method_name"],
        "tradition_tags": policy["tradition_tags"],
        "body_or_point": body_key,
        "formula_version": "3.0.0",
        "report_eligibility": report_profile,
        "visibility_state": visibility_state,
        "birth_time_dependency": "angle_contacts_and_house_require_exact_time",
        "confidence_state": confidence_state,
        "supporting_inputs": ["longitude", "sign", "degree_decimal", "house", "speed", "retrograde"] + (["aspects"] if aspects else []),
        "limitations": limitations,
        "allowed_use_cases": list(policy["allowed_use_cases"]),
        "restricted_use_cases": list(policy["restricted_use_cases"]),
        "data": {
            "display_name": policy["display_name"],
            "sign": body_data.get("sign"),
            "house": body_data.get("house"),
            "degree_decimal": body_data.get("degree_decimal"),
            "retrograde": body_data.get("retrograde"),
            "speed": body_data.get("speed"),
            "major_aspects": aspects,
            "angle_contacts": angle_contacts,
        },
        "methodology": methodology,
    }


def evaluate_selected_specialist_bodies(
    payload: dict,
    report_type: str,
    body_keys: list[str] | None = None,
    report_profile: str | None = None,
) -> dict[str, dict[str, Any]]:
    selected = body_keys or ["Chiron", "Lilith_BML", "Lilith_Asteroid"]
    return {
        body_key: evaluate_specialist_body(payload, body_key, report_type, report_profile)
        for body_key in selected
    }
