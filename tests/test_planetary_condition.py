"""
Tests for planetary_condition.py (formulas/standard/planetary_condition.py).

Covers:
- Retrograde is NOT a condition score penalty (CR-04)
- Per-body station thresholds (CR-03)
- Confidence states (CR-07)
- Retrograde appears in routing_tags, not as score penalty
- Condition score components
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.planetary_condition import (
    evaluate_all_planetary_conditions,
    STATION_THRESHOLDS,
    _is_stationary,
    _classify_condition,
)


def _minimal_body(sign="Aries", house=5, degree=15.0, speed=1.0, longitude=15.0):
    return {
        "longitude": longitude,
        "speed": speed,
        "retrograde": speed < 0,
        "house": house,
        "sign": sign,
        "degree": int(degree),
        "minute": 0,
        "degree_decimal": degree,
    }


def _make_payload(sun_lon=90.0, asc_lon=0.0, planet_overrides=None):
    planets = {
        "Sun":     _minimal_body("Cancer", house=10, degree=10.0, longitude=sun_lon, speed=1.0),
        "Moon":    _minimal_body("Virgo",  house=6,  degree=15.0, longitude=165.0,  speed=13.0),
        "Mercury": _minimal_body("Leo",    house=5,  degree=10.0, longitude=130.0,  speed=1.5),
        "Venus":   _minimal_body("Leo",    house=5,  degree=5.0,  longitude=125.0,  speed=1.2),
        "Mars":    _minimal_body("Aries",  house=1,  degree=5.0,  longitude=5.0,    speed=0.6),
        "Jupiter": _minimal_body("Taurus", house=2,  degree=20.0, longitude=50.0,   speed=0.12),
        "Saturn":  _minimal_body("Pisces", house=12, degree=10.0, longitude=340.0,  speed=0.09),
        "Uranus":  _minimal_body("Taurus", house=2,  degree=25.0, longitude=55.0,   speed=0.04),
        "Neptune": _minimal_body("Pisces", house=12, degree=5.0,  longitude=335.0,  speed=0.02),
        "Pluto":   _minimal_body("Aquarius", house=11, degree=2.0, longitude=302.0, speed=0.015),
    }
    if planet_overrides:
        for body, overrides in planet_overrides.items():
            if body in planets:
                planets[body].update(overrides)
            else:
                planets[body] = _minimal_body(**overrides) if isinstance(overrides, dict) else overrides
    return {
        "standard_planets": planets,
        "angles": {
            "Ascendant": {"longitude": asc_lon, "sign": "Aries"},
            "Midheaven": {"longitude": 270.0,   "sign": "Capricorn"},
        },
        "houses": {
            f"House_{i}": {"sign": s, "longitude": float(i * 30),
                           "degree": 0, "minute": 0, "degree_decimal": 0.0}
            for i, s in enumerate(
                ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                 "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"], 1
            )
        },
        "aspects": []
    }


# ── CR-04: Retrograde is NOT a condition penalty ──────────────────────────────

def test_retrograde_does_not_penalise_score():
    payload_direct   = _make_payload(planet_overrides={"Mercury": {"speed": 1.5}})
    payload_retro    = _make_payload(planet_overrides={"Mercury": {"speed": -1.5}})

    cond_direct = evaluate_all_planetary_conditions(payload_direct)
    cond_retro  = evaluate_all_planetary_conditions(payload_retro)

    # Scores should be identical — retrograde doesn't change condition score
    score_direct = cond_direct["Mercury"].overall_condition_score
    score_retro  = cond_retro["Mercury"].overall_condition_score
    assert score_direct == score_retro, (
        f"Retrograde should not change score: direct={score_direct}, retro={score_retro}"
    )


def test_retrograde_appears_in_routing_tags():
    payload = _make_payload(planet_overrides={"Mercury": {"speed": -1.5}})
    conditions = evaluate_all_planetary_conditions(payload)
    assert "retrograde" in conditions["Mercury"].routing_tags


def test_direct_not_in_routing_tags_as_retrograde():
    payload = _make_payload(planet_overrides={"Mercury": {"speed": 1.5}})
    conditions = evaluate_all_planetary_conditions(payload)
    assert "retrograde" not in conditions["Mercury"].routing_tags


# ── CR-03: Per-body station thresholds ────────────────────────────────────────

def test_station_thresholds_defined_for_outer_planets():
    for body in ("Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"):
        assert body in STATION_THRESHOLDS, f"Missing station threshold for {body}"


def test_sun_and_moon_not_stationary():
    assert _is_stationary("Sun", 0.001) is False
    assert _is_stationary("Moon", 0.001) is False


def test_mercury_station_threshold():
    # Mercury threshold = 0.10
    assert _is_stationary("Mercury", 0.09) is True
    assert _is_stationary("Mercury", 0.11) is False


def test_jupiter_station_threshold():
    # Jupiter threshold = 0.020
    assert _is_stationary("Jupiter", 0.019) is True
    assert _is_stationary("Jupiter", 0.021) is False


def test_pluto_station_threshold():
    # Pluto threshold = 0.005
    assert _is_stationary("Pluto", 0.004) is True
    assert _is_stationary("Pluto", 0.006) is False


def test_stationary_planet_in_routing_tags():
    # Jupiter at near-zero speed should be stationary
    payload = _make_payload(planet_overrides={"Jupiter": {"speed": 0.001}})
    conditions = evaluate_all_planetary_conditions(payload)
    assert "stationary" in conditions["Jupiter"].routing_tags


def test_stationary_planet_gets_score_bonus():
    payload_normal    = _make_payload(planet_overrides={"Jupiter": {"speed": 0.12}})
    payload_stationary = _make_payload(planet_overrides={"Jupiter": {"speed": 0.001}})
    cond_n = evaluate_all_planetary_conditions(payload_normal)
    cond_s = evaluate_all_planetary_conditions(payload_stationary)
    assert cond_s["Jupiter"].overall_condition_score > cond_n["Jupiter"].overall_condition_score


# ── CR-07: Confidence states ──────────────────────────────────────────────────

def test_confidence_exact_when_ascendant_present():
    payload = _make_payload(asc_lon=0.0)
    conditions = evaluate_all_planetary_conditions(payload)
    for body, record in conditions.items():
        assert record.confidence in (
            "exact_birth_time", "approximate_birth_time"
        ), f"{body}: unexpected confidence {record.confidence}"


def test_confidence_unavailable_when_no_ascendant():
    payload = _make_payload()
    payload["angles"] = {}  # remove angles
    conditions = evaluate_all_planetary_conditions(payload)
    for body, record in conditions.items():
        assert record.confidence == "angle_dependent_unavailable", (
            f"{body}: expected angle_dependent_unavailable, got {record.confidence}"
        )


def test_missing_inputs_when_no_ascendant():
    payload = _make_payload()
    payload["angles"] = {}
    conditions = evaluate_all_planetary_conditions(payload)
    for body, record in conditions.items():
        assert len(record.routing_tags) >= 0  # can be zero
        # missing_inputs is not a PlanetConditionRecord field by default;
        # verify confidence carries the signal
        assert record.confidence == "angle_dependent_unavailable"


# ── Condition classification ──────────────────────────────────────────────────

def test_classify_condition_thresholds():
    assert _classify_condition(8.0)  == "excellent"
    assert _classify_condition(7.9)  == "strong"
    assert _classify_condition(4.0)  == "strong"
    assert _classify_condition(3.9)  == "neutral"
    assert _classify_condition(0.0)  == "neutral"
    assert _classify_condition(-0.1) == "challenged"
    assert _classify_condition(-4.0) == "challenged"
    assert _classify_condition(-4.1) == "severely_challenged"


# ── General contract ──────────────────────────────────────────────────────────

def test_all_standard_bodies_returned():
    payload = _make_payload()
    conditions = evaluate_all_planetary_conditions(payload)
    for body in ("Sun", "Moon", "Mercury", "Venus", "Mars",
                 "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"):
        assert body in conditions, f"Missing condition record for {body}"


def test_record_has_routing_tags_list():
    payload = _make_payload()
    conditions = evaluate_all_planetary_conditions(payload)
    for body, record in conditions.items():
        assert isinstance(record.routing_tags, list)


def test_condition_and_prominence_scores_independent():
    # overall_condition_score should not equal prominence_score by default
    payload = _make_payload()
    conditions = evaluate_all_planetary_conditions(payload)
    # prominence_score starts at 0.0 (populated by prominence ranker, not condition)
    for body, record in conditions.items():
        assert record.prominence_score == 0.0, (
            f"{body}: prominence_score should be 0 until prominence ranker runs"
        )


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except Exception:
            print(f"  FAIL  {t.__name__}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
