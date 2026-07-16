"""
Tests for engine/location_services.py.

Covers:
- Birth UTC instant / Julian Day preservation under relocation
- No mutation of the natal payload
- Relocated house changes for a destination far from the birth Ascendant
- Stable relocated angle output shape
- Destination resolution from a bare place name or common state abbreviation
  (offline resolver reuse)
- Clear errors/warnings for missing or unsupported inputs

Destinations in this file include both explicit "City, Country" forms and
ordinary US state abbreviation forms that previously collided with ISO
country codes.
"""
import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from engine.location_services import (
    UNSUPPORTED_METHODS,
    build_relocated_payload,
    compare_natal_to_relocated,
)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _sign_for(longitude: float) -> str:
    return SIGNS[int((longitude % 360) // 30)]


def _zodiac_position(longitude: float) -> dict:
    longitude = longitude % 360
    degree_decimal = longitude % 30
    return {
        "sign": _sign_for(longitude),
        "degree": int(degree_decimal),
        "minute": int((degree_decimal % 1) * 60),
        "degree_decimal": round(degree_decimal, 4),
        "formatted": f"{degree_decimal:.2f} {_sign_for(longitude)}",
    }


def _whole_sign_house(longitude: float, asc_longitude: float) -> int:
    body_index = int((longitude % 360) // 30)
    asc_index = int((asc_longitude % 360) // 30)
    return ((body_index - asc_index) % 12) + 1


def _body(longitude: float, asc_longitude: float, speed: float = 1.0) -> dict:
    return {
        "longitude": round(longitude % 360, 4),
        "speed": speed,
        "retrograde": speed < 0,
        "house": _whole_sign_house(longitude, asc_longitude),
        **_zodiac_position(longitude),
    }


def _angle(longitude: float) -> dict:
    return {
        "longitude": round(longitude % 360, 4),
        **_zodiac_position(longitude),
    }


def _houses(asc_longitude: float) -> dict:
    asc_index = int((asc_longitude % 360) // 30)
    houses = {}
    for offset in range(12):
        sign_index = (asc_index + offset) % 12
        cusp_longitude = sign_index * 30.0
        houses[f"House_{offset + 1}"] = {
            "longitude": cusp_longitude,
            **_zodiac_position(cusp_longitude),
        }
    return houses


def _build_natal_payload() -> dict:
    """
    A Chicago-birth natal payload, hand-built (not run through Swiss
    Ephemeris / the offline resolver) so these tests stay fast and fully
    deterministic. Ascendant is placed in early Aries so a destination on
    the opposite side of the globe reliably produces a different
    relocated Ascendant sign.
    """
    asc_longitude = 5.0  # Aries
    julian_day = 2448088.933333  # 1990-06-15 14:22 UTC-ish, arbitrary but fixed

    standard_planets = {
        "Sun": _body(84.0, asc_longitude, speed=1.0),
        "Moon": _body(122.0, asc_longitude, speed=13.0),
        "Mercury": _body(88.0, asc_longitude, speed=1.2),
        "Venus": _body(61.0, asc_longitude, speed=1.0),
        "Mars": _body(3.0, asc_longitude, speed=0.5),
        "Jupiter": _body(244.0, asc_longitude, speed=0.1),
        "Saturn": _body(276.0, asc_longitude, speed=0.08),
        "Uranus": _body(274.0, asc_longitude, speed=0.03),
        "Neptune": _body(286.0, asc_longitude, speed=0.02),
        "Pluto": _body(231.0, asc_longitude, speed=0.01),
    }

    angles = {
        "Ascendant": _angle(asc_longitude),
        "Midheaven": _angle(270.0),
        "Descendant": _angle(asc_longitude + 180.0),
        "Imum_Coeli": _angle(90.0),
        "Vertex": {**_angle(210.0), "house": _whole_sign_house(210.0, asc_longitude)},
    }

    aspects = [
        {"body_1": "Sun", "body_2": "Moon", "aspect": "Square", "orb": 2.0, "angle": 38.0},
        {"body_1": "Sun", "body_2": "Ascendant", "aspect": "Conjunction", "orb": 1.0, "angle": 79.0},
        {"body_1": "Venus", "body_2": "Midheaven", "aspect": "Trine", "orb": 3.5, "angle": 151.0},
    ]

    return {
        "simple_mode": False,
        "location": "Chicago, Illinois, United States",
        "birth_location": "Chicago, Illinois, United States",
        "user_profile": {
            "resolved_location": "Chicago, Illinois, United States",
            "resolved_coordinates": {"latitude": 41.85, "longitude": -87.65},
            "timezone": "America/Chicago",
            "local_datetime": "1990-06-15T14:22:00-05:00",
            "utc_datetime": "1990-06-15T19:22:00+00:00",
            "julian_day": julian_day,
            "house_system": "Whole Sign",
            "simple_mode": False,
            "birth_time_state": "exact_birth_time",
            "birth_time_confidence": "exact_birth_time",
            "methodology_id": "tropical_whole",
            "methodology_label": "Tropical zodiac + Whole Sign houses",
            "zodiac": "Tropical",
            "methodology": {
                "id": "tropical_whole",
                "label": "Tropical zodiac + Whole Sign houses",
                "zodiac": "Tropical",
                "house_system": "Whole Sign",
            },
        },
        "angles": angles,
        "houses": _houses(asc_longitude),
        "standard_planets": standard_planets,
        "custom_asteroids": {
            "Kassandra": _body(270.0, asc_longitude, speed=0.2),
            "Sirene": _body(91.0, asc_longitude, speed=0.2),
        },
        "aspects": aspects,
    }


# A destination roughly opposite Chicago's Ascendant, offline-resolvable,
# no US-state-code collision risk (see module docstring).
SYDNEY = {"display_name": "Sydney, Australia", "latitude": -33.8678, "longitude": 151.2073, "timezone": "Australia/Sydney"}


# ── Birth UTC instant / Julian Day preservation ────────────────────────────

def test_relocated_payload_preserves_julian_day_exactly():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    assert relocated["birth_utc_preserved"]["julian_day"] == natal["user_profile"]["julian_day"]
    assert relocated["birth_utc_preserved"]["utc_datetime"] == natal["user_profile"]["utc_datetime"]


def test_compare_confirms_birth_instant_preserved():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)
    comparison = compare_natal_to_relocated(natal, relocated)

    assert comparison["birth_instant_preserved"] is True


def test_missing_julian_day_raises_clear_error():
    natal = _build_natal_payload()
    del natal["user_profile"]["julian_day"]

    with pytest.raises(ValueError, match="julian_day"):
        build_relocated_payload(natal, SYDNEY)


# ── No mutation of the natal payload ───────────────────────────────────────

def test_build_relocated_payload_does_not_mutate_natal_payload():
    natal = _build_natal_payload()
    natal_snapshot = copy.deepcopy(natal)

    build_relocated_payload(natal, SYDNEY)

    assert natal == natal_snapshot


def test_compare_natal_to_relocated_does_not_mutate_either_payload():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)
    natal_snapshot = copy.deepcopy(natal)
    relocated_snapshot = copy.deepcopy(relocated)

    compare_natal_to_relocated(natal, relocated)

    assert natal == natal_snapshot
    assert relocated == relocated_snapshot


def test_relocated_body_records_are_independent_copies():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    relocated["standard_planets"]["Sun"]["house"] = 999

    assert natal["standard_planets"]["Sun"]["house"] != 999


# ── Relocated house changes ────────────────────────────────────────────────

def test_relocated_ascendant_differs_from_natal_for_distant_destination():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    assert relocated["angles"]["Ascendant"]["longitude"] != natal["angles"]["Ascendant"]["longitude"]


def test_at_least_one_body_changes_house_for_distant_destination():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)
    comparison = compare_natal_to_relocated(natal, relocated)

    assert comparison["changed_house_count"] > 0
    changed = [body for body, entry in comparison["house_changes"].items() if entry["changed"]]
    assert changed, "expected at least one body to change Whole Sign house"


def test_planetary_longitudes_are_reassigned_not_recomputed():
    """Longitude is location-invariant: the destination changes houses, not positions."""
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    for body_name, natal_body in natal["standard_planets"].items():
        assert relocated["standard_planets"][body_name]["longitude"] == natal_body["longitude"]


def test_relocated_payload_excludes_eo_custom_asteroid_load():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    assert natal["custom_asteroids"], "fixture should include custom asteroid data"
    assert relocated["custom_asteroids"] == {}


# ── Stable relocated angle output shape ────────────────────────────────────

def test_relocated_angles_carry_all_canonical_keys():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    for angle_name in ("Ascendant", "Midheaven", "Descendant", "Imum_Coeli", "Vertex"):
        angle = relocated["angles"][angle_name]
        assert "longitude" in angle
        assert "sign" in angle

    assert "house" in relocated["angles"]["Vertex"]


def test_relocated_houses_are_fully_populated():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    assert len(relocated["houses"]) == 12
    for index in range(1, 13):
        assert f"House_{index}" in relocated["houses"]


def test_relocated_descendant_and_ic_are_opposite_asc_and_mc():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    asc = relocated["angles"]["Ascendant"]["longitude"]
    dsc = relocated["angles"]["Descendant"]["longitude"]
    mc = relocated["angles"]["Midheaven"]["longitude"]
    ic = relocated["angles"]["Imum_Coeli"]["longitude"]

    assert round(abs((dsc - asc) % 360), 4) == 180.0
    assert round(abs((ic - mc) % 360), 4) == 180.0


# ── Destination resolution from a bare place name ──────────────────────────

def test_destination_resolves_from_place_name_offline():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, {"location": "Tokyo, Japan"})

    assert relocated["destination"]["display_name"] == "Tokyo, Japan"
    assert relocated["destination"]["latitude"] == pytest.approx(35.6895, abs=0.01)
    assert relocated["destination"]["longitude"] == pytest.approx(139.6917, abs=0.01)
    assert relocated["destination"]["timezone"] == "Asia/Tokyo"


def test_destination_resolves_state_abbreviation_when_country_code_collides():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, {"location": "Chicago, IL"})

    assert relocated["destination"]["display_name"] == "Chicago, Illinois, United States"
    assert relocated["destination"]["latitude"] == pytest.approx(41.85, abs=0.01)
    assert relocated["destination"]["longitude"] == pytest.approx(-87.65, abs=0.01)
    assert relocated["destination"]["timezone"] == "America/Chicago"


def test_unresolvable_destination_name_raises_clear_error():
    natal = _build_natal_payload()

    with pytest.raises(ValueError, match="Could not resolve destination"):
        build_relocated_payload(natal, {"location": "Nowhereplacezzz12345"})


def test_destination_missing_coordinates_and_name_raises():
    natal = _build_natal_payload()

    with pytest.raises(ValueError, match="latitude/longitude"):
        build_relocated_payload(natal, {"timezone": "America/Chicago"})


# ── Warnings for missing/unsupported inputs ────────────────────────────────

def test_missing_destination_timezone_produces_warning_not_error():
    natal = _build_natal_payload()
    destination = {"display_name": "Sydney, Australia", "latitude": -33.8678, "longitude": 151.2073}

    relocated = build_relocated_payload(natal, destination)

    assert any("timezone" in warning for warning in relocated["warnings"])


def test_angle_linked_aspects_are_excluded_and_warned_about():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)

    for aspect in relocated["aspects"]:
        assert aspect["body_1"] not in {"Ascendant", "Descendant", "Midheaven", "Imum_Coeli", "Vertex"}
        assert aspect["body_2"] not in {"Ascendant", "Descendant", "Midheaven", "Imum_Coeli", "Vertex"}

    # Sun-Moon (body-to-body) survives; Sun-Ascendant does not.
    kept_pairs = {(a["body_1"], a["body_2"]) for a in relocated["aspects"]}
    assert ("Sun", "Moon") in kept_pairs
    assert any("excluded" in warning for warning in relocated["warnings"])


def test_compare_lists_unsupported_methods_explicitly():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)
    comparison = compare_natal_to_relocated(natal, relocated)

    assert set(comparison["unsupported_methods"]) == set(UNSUPPORTED_METHODS)
    assert "astrocartography" in comparison["unsupported_methods"]
    assert "local_space" in comparison["unsupported_methods"]
    assert "parans" in comparison["unsupported_methods"]
    assert "relocated_returns" in comparison["unsupported_methods"]


def test_compare_does_not_recompute_natal_condition():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)
    comparison = compare_natal_to_relocated(natal, relocated)

    assert "natal_condition_note" in comparison
    assert "condition_score" not in comparison
    assert "dignity" not in comparison


# ── Relocated angle contacts (evaluate_angularity reuse) ───────────────────

def test_relocated_angle_contacts_are_structured_not_prose():
    natal = _build_natal_payload()
    relocated = build_relocated_payload(natal, SYDNEY)
    comparison = compare_natal_to_relocated(natal, relocated)

    for body_name, contact in comparison["relocated_angle_contacts"].items():
        assert body_name in relocated["standard_planets"]
        assert body_name not in natal["custom_asteroids"]
        assert contact["angle"] in {"Ascendant", "Descendant", "Midheaven", "Imum_Coeli"}
        assert isinstance(contact["orb"], (int, float))


def test_empty_natal_payload_raises():
    with pytest.raises(ValueError):
        build_relocated_payload({}, SYDNEY)


def test_empty_destination_raises():
    natal = _build_natal_payload()
    with pytest.raises(ValueError):
        build_relocated_payload(natal, {})
