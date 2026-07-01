"""
selectors/utils.py — Core Utility Functions

Shared helpers used by:
- formulas/standard_indexes.py
- formulas/proprietary_indexes.py
- selectors/block_selector.py
- selectors/variable_resolver.py

This version is safe when an optional asteroid or angle is unavailable.
Missing bodies return no score rather than being treated as 0° Aries.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from formulas.standard.normalization import normalize_angle_name
from config import (
    MAJOR_ASPECTS,
    ORB_CONFIG,
    SCORE_TIERS,
    SIGN_ELEMENTS,
    SIGN_MODALITIES,
)


# ── Payload Navigation ─────────────────────────────────────────

def get_body_data(payload: dict, body: str) -> dict:
    """
    Returns a body's data dictionary from standard planets or custom asteroids.

    Missing bodies and unavailable asteroid records return an empty dictionary.
    """
    standard_planets = payload.get("standard_planets", {})
    custom_asteroids = payload.get("custom_asteroids", {})

    standard_data = standard_planets.get(body)
    if isinstance(standard_data, dict):
        return standard_data

    asteroid_data = custom_asteroids.get(body)
    if isinstance(asteroid_data, dict):
        return asteroid_data

    return {}


def body_exists(payload: dict, body: str) -> bool:
    """Returns True only when a usable body record is present."""
    return bool(get_body_data(payload, body))


def get_body_longitude(payload: dict, body: str) -> float | None:
    """
    Returns a body's ecliptic longitude.

    Returns None when the body is unavailable instead of inventing 0.0°.
    """
    longitude = get_body_data(payload, body).get("longitude")

    if isinstance(longitude, (int, float)):
        return float(longitude)

    return None


def get_body_sign(payload: dict, body: str) -> str:
    """Returns the zodiac sign for a body, or an empty string if unavailable."""
    return get_body_data(payload, body).get("sign", "")


def get_body_house(payload: dict, body: str) -> int:
    """Returns the Whole Sign house number for a body, or 0 if unavailable."""
    house = get_body_data(payload, body).get("house", 0)

    if isinstance(house, int):
        return house

    return 0


def is_retrograde(payload: dict, body: str) -> bool:
    """Returns True when a body is retrograde; False when unavailable."""
    return bool(get_body_data(payload, body).get("retrograde", False))


def get_angle_data(payload: dict, angle_name: str) -> dict:
    """
    Returns data for an angle.

    Valid names include:
    Ascendant, Midheaven, Descendant, Imum_Coeli, Vertex.
    """
    canonical_name = normalize_angle_name(angle_name)
    angles = payload.get("angles", {})
    angle = angles.get(canonical_name)

    if not isinstance(angle, dict) and canonical_name != angle_name:
        angle = angles.get(angle_name)

    if isinstance(angle, dict):
        return angle

    return {}


def angle_exists(payload: dict, angle_name: str) -> bool:
    """Returns True only when a usable angle record is present."""
    return bool(get_angle_data(payload, angle_name))


def get_angle_longitude(payload: dict, angle_name: str) -> float | None:
    """
    Returns an angle longitude.

    Returns None when unavailable instead of treating it as 0.0° Aries.
    """
    longitude = get_angle_data(payload, angle_name).get("longitude")

    if isinstance(longitude, (int, float)):
        return float(longitude)

    return None


# ── Aspect Geometry ────────────────────────────────────────────

def angular_distance(longitude_a: float, longitude_b: float) -> float:
    """Returns the shortest angular distance between two zodiac longitudes."""
    difference = abs(longitude_a - longitude_b) % 360
    return min(difference, 360 - difference)


def get_aspect_from_payload(payload: dict, body_a: str, body_b: str) -> dict | None:
    """
    Looks up a precomputed natal aspect from the payload aspect matrix.

    Returns None when no aspect exists.
    """
    for aspect in payload.get("aspects", []):
        first_body = aspect.get("body_1")
        second_body = aspect.get("body_2")

        if (
            (first_body == body_a and second_body == body_b)
            or
            (first_body == body_b and second_body == body_a)
        ):
            return aspect

    return None


def get_max_orb(
    body_a: str,
    body_b: str,
    aspect_type: str,
    orb_config: dict | None = None,
) -> float:
    """
    Returns the configured maximum orb for a body pair and aspect type.
    """
    if orb_config is None:
        orb_config = ORB_CONFIG

    base_orbs = orb_config.get("base_orbs", {})
    default_orb = base_orbs.get("Default", 5.0)

    orb_a = base_orbs.get(body_a, default_orb)
    orb_b = base_orbs.get(body_b, default_orb)

    aspect_multipliers = orb_config.get("aspect_multipliers", {})
    multiplier = aspect_multipliers.get(aspect_type, 1.0)

    return max(orb_a, orb_b) * multiplier


def aspect_strength(
    payload: dict,
    body_a: str,
    body_b: str,
    allowed_aspects: list,
    orb_config: dict | None = None,
) -> float:
    """
    Returns normalized natal aspect strength from 0.0 to 1.0.

    A missing body, absent aspect, disallowed aspect, or out-of-orb aspect
    returns 0.0 safely.
    """
    if not body_exists(payload, body_a):
        return 0.0

    if not body_exists(payload, body_b):
        return 0.0

    if orb_config is None:
        orb_config = ORB_CONFIG

    aspect = get_aspect_from_payload(payload, body_a, body_b)

    if not aspect:
        return 0.0

    aspect_name = aspect.get("aspect")

    if aspect_name not in allowed_aspects:
        return 0.0

    actual_orb = aspect.get("orb")

    if not isinstance(actual_orb, (int, float)):
        return 0.0

    maximum_orb = get_max_orb(
        body_a,
        body_b,
        aspect_name,
        orb_config,
    )

    if maximum_orb <= 0:
        return 0.0

    return max(0.0, (maximum_orb - actual_orb) / maximum_orb)


def aspect_strength_angle(
    payload: dict,
    body: str,
    angle_name: str,
    allowed_aspects: list,
    orb_config: dict | None = None,
) -> float:
    """
    Returns normalized direct aspect strength between a body and an angle.

    This deliberately calculates body-to-angle geometry from longitudes
    rather than depending on the precomputed payload aspect list.
    """
    if not body_exists(payload, body):
        return 0.0

    if not angle_exists(payload, angle_name):
        return 0.0

    if orb_config is None:
        orb_config = ORB_CONFIG

    body_longitude = get_body_longitude(payload, body)
    angle_longitude = get_angle_longitude(payload, angle_name)

    if body_longitude is None or angle_longitude is None:
        return 0.0

    distance = angular_distance(body_longitude, angle_longitude)
    maximum_orb = orb_config.get("max_orb_for_angle", 5.0)

    if maximum_orb <= 0:
        return 0.0

    strongest_match = 0.0

    for aspect_name, aspect_angle in MAJOR_ASPECTS:
        if aspect_name not in allowed_aspects:
            continue

        actual_orb = abs(distance - aspect_angle)

        if actual_orb <= maximum_orb:
            strength = max(
                0.0,
                (maximum_orb - actual_orb) / maximum_orb,
            )
            strongest_match = max(strongest_match, strength)

    return strongest_match


# ── House, Sign, and Modality Helpers ──────────────────────────

def house_match(payload: dict, body: str, house_number: int) -> int:
    """Returns 1 when a body occupies the requested house, otherwise 0."""
    return 1 if get_body_house(payload, body) == house_number else 0


def sign_element_match(payload: dict, body: str, element: str) -> int:
    """Returns 1 when a body's sign belongs to the requested element."""
    sign = get_body_sign(payload, body)
    return 1 if sign in SIGN_ELEMENTS.get(element.lower(), []) else 0


def get_sign_element(sign: str) -> str:
    """Returns fire, earth, air, water, or unknown for a zodiac sign."""
    for element, signs in SIGN_ELEMENTS.items():
        if sign in signs:
            return element

    return "unknown"


def get_sign_modality(sign: str) -> str:
    """Returns cardinal, fixed, mutable, or unknown for a zodiac sign."""
    for modality, signs in SIGN_MODALITIES.items():
        if sign in signs:
            return modality

    return "unknown"


def get_body_modality(payload: dict, body: str) -> str:
    """Returns the modality of a body's zodiac sign."""
    return get_sign_modality(get_body_sign(payload, body))


def count_in_houses(payload: dict, bodies: list, house_number: int) -> int:
    """Counts how many listed bodies occupy a specified house."""
    return sum(
        1
        for body in bodies
        if get_body_house(payload, body) == house_number
    )


def stellium_weight(
    payload: dict,
    zone: str | int,
    zone_type: str = "house",
) -> int:
    """
    Counts available bodies in a house or zodiac sign.

    zone_type:
    - "house": zone should be an integer from 1 to 12
    - "sign": zone should be a zodiac sign name
    """
    count = 0

    for group in (
        payload.get("standard_planets", {}),
        payload.get("custom_asteroids", {}),
    ):
        for data in group.values():
            if not isinstance(data, dict):
                continue

            if zone_type == "house" and data.get("house") == zone:
                count += 1

            elif zone_type == "sign" and data.get("sign") == zone:
                count += 1

    return count


# ── Score Helpers ──────────────────────────────────────────────

def get_score_tier(score: float) -> str:
    """Maps a normalized 0.0–1.0 score to DOMINANT, PRESENT, or SUBTLE."""
    if score >= SCORE_TIERS["DOMINANT"]:
        return "DOMINANT"

    if score >= SCORE_TIERS["PRESENT"]:
        return "PRESENT"

    return "SUBTLE"
