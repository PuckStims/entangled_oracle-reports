"""
Targeted tests for the Round 3 CR-07 confidence-state fix in
formulas/standard/planetary_condition.py's _resolve_confidence().

Bug (pre-existing, found while sampling Location Services output in
Round 2.5): natal_modifiers[body].confidence -- surfaced via
PlanetConditionRecord.confidence -- always reported "exact_birth_time"
regardless of the chart's actual birth-time state. The old check only
tested whether an Ascendant longitude was present and whether angularity
resolved to a real house_type. Both are always true even for a
simple_mode chart's noon-placeholder Ascendant, so the check could never
actually detect an unknown or approximate birth time in practice.

This file proves: confidence now reflects
payload.user_profile.birth_time_state / simple_mode; every other
pre-existing branch (angle-dependent-unavailable, the house_type-unknown
fallback, and plain exact-birth-time) is unchanged.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.planetary_condition import evaluate_all_planetary_conditions


def _payload(*, asc_lon=0.0, birth_time_state=None, simple_mode=False, angles=None, sun_house=2):
    """Minimal payload: one Sun placement, one Ascendant, optional birth-time metadata."""
    if angles is None:
        angles = {"Ascendant": {"longitude": asc_lon, "sign": "Aries"}}

    sun = {
        "longitude": asc_lon + 40.0, "speed": 1.0, "retrograde": False,
        "sign": "Taurus", "degree": 10, "minute": 0, "degree_decimal": 10.0,
    }
    if sun_house is not None:
        sun["house"] = sun_house

    user_profile = {"simple_mode": simple_mode}
    if birth_time_state is not None:
        user_profile["birth_time_state"] = birth_time_state

    return {
        "simple_mode": simple_mode,
        "user_profile": user_profile,
        "standard_planets": {"Sun": sun},
        "angles": angles,
        "houses": {},
        "aspects": [],
    }


# ── The fix itself ──────────────────────────────────────────────────────────

def test_exact_birth_time_confidence_is_preserved():
    payload = _payload(birth_time_state="exact_birth_time")
    result = evaluate_all_planetary_conditions(payload)
    assert result["Sun"].confidence == "exact_birth_time"


def test_approximate_birth_time_is_no_longer_reported_as_exact():
    payload = _payload(birth_time_state="approximate_birth_time")
    result = evaluate_all_planetary_conditions(payload)
    assert result["Sun"].confidence == "approximate_birth_time"


def test_unknown_birth_time_is_no_longer_reported_as_exact():
    payload = _payload(birth_time_state="unknown_birth_time")
    result = evaluate_all_planetary_conditions(payload)
    assert result["Sun"].confidence == "unknown_birth_time"


def test_simple_mode_without_explicit_birth_time_state_is_unknown():
    """Some hand-built fixtures (e.g. tests/phase2_fixtures.py's simple_dob_only)
    set simple_mode without an explicit birth_time_state string."""
    payload = _payload(simple_mode=True)
    result = evaluate_all_planetary_conditions(payload)
    assert result["Sun"].confidence == "unknown_birth_time"


# ── Preserved prior behavior (no explicit birth-time metadata at all) ──────

def test_missing_birth_time_metadata_falls_back_to_prior_exact_behavior():
    payload = _payload()
    del payload["user_profile"]["simple_mode"]
    result = evaluate_all_planetary_conditions(payload)
    assert result["Sun"].confidence == "exact_birth_time"


def test_missing_birth_time_metadata_with_unknown_house_type_falls_back_to_approximate():
    payload = _payload(sun_house=None)  # no "house" key -> angularity house_type == "unknown"
    del payload["user_profile"]["simple_mode"]
    result = evaluate_all_planetary_conditions(payload)
    assert result["Sun"].confidence == "approximate_birth_time"


def test_missing_ascendant_is_still_angle_dependent_unavailable():
    payload = _payload(birth_time_state="exact_birth_time", angles={})
    result = evaluate_all_planetary_conditions(payload)
    assert result["Sun"].confidence == "angle_dependent_unavailable"


# ── End-to-end through the real natal engine ────────────────────────────────

def test_end_to_end_real_chart_unknown_time_is_distinct_from_exact():
    from engine.natal_engine import generate_payload

    exact = generate_payload({"name": "x", "date": "1985-11-02", "time": "14:00", "location": "Portland, Oregon"})
    unknown = generate_payload({"name": "x", "date": "1985-11-02", "location": "Portland, Oregon", "simple_mode": True})

    exact_conditions = evaluate_all_planetary_conditions(exact)
    unknown_conditions = evaluate_all_planetary_conditions(unknown)

    assert exact_conditions["Jupiter"].confidence == "exact_birth_time"
    assert unknown_conditions["Jupiter"].confidence == "unknown_birth_time"
    for record in unknown_conditions.values():
        assert record.confidence != "exact_birth_time"
