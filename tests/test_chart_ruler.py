"""
Tests for formulas/standard/chart_ruler.py.

Covers:
- Ascendant-gated unavailability (CR-07)
- Confidence states on every return path
- Per-body station threshold (CR-03)
- Ruler identification (traditional primary + modern co-ruler)
- Luminary support detection
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.chart_ruler import evaluate_chart_ruler
from formulas.standard.confidence import (
    ANGLE_DEPENDENT_UNAVAILABLE,
    EXACT_BIRTH_TIME,
)


def _body(sign, house=5, degree=15.0, speed=1.0, longitude=None):
    if longitude is None:
        longitude = float(list(["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                                 "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
                                 ]).index(sign) * 30 + degree)
    return {
        "longitude": longitude, "speed": speed, "retrograde": speed < 0,
        "house": house, "sign": sign, "degree": int(degree),
        "minute": 0, "degree_decimal": degree,
    }


def _make_payload(asc_sign="Aries", asc_lon=0.0, planets=None, aspects=None):
    default_planets = {
        "Sun":     _body("Cancer", house=10, degree=15.0, longitude=105.0, speed=1.0),
        "Moon":    _body("Virgo",  house=6,  degree=10.0, longitude=160.0, speed=13.0),
        "Mercury": _body("Leo",    house=5,  degree=5.0,  longitude=125.0, speed=1.2),
        "Venus":   _body("Gemini", house=3,  degree=20.0, longitude=80.0,  speed=1.0),
        "Mars":    _body("Aries",  house=1,  degree=10.0, longitude=10.0,  speed=0.6),
        "Jupiter": _body("Taurus", house=2,  degree=5.0,  longitude=35.0,  speed=0.1),
        "Saturn":  _body("Pisces", house=12, degree=5.0,  longitude=335.0, speed=0.1),
        "Uranus":  _body("Taurus", house=2,  degree=20.0, longitude=50.0,  speed=0.04),
        "Neptune": _body("Pisces", house=12, degree=2.0,  longitude=332.0, speed=0.02),
        "Pluto":   _body("Aquarius", house=11, degree=2.0, longitude=302.0, speed=0.015),
    }
    if planets:
        default_planets.update(planets)
    return {
        "standard_planets": default_planets,
        "angles": {"Ascendant": {"longitude": asc_lon, "sign": asc_sign}},
        "houses": {
            f"House_{i}": {"sign": s, "longitude": float((i-1)*30),
                           "degree": 0, "minute": 0, "degree_decimal": 0.0}
            for i, s in enumerate(
                ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                 "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"], 1
            )
        },
        "aspects": aspects or [],
    }


# ── CR-07: Missing Ascendant ──────────────────────────────────────────────────

def test_missing_ascendant_returns_unavailable():
    payload = _make_payload()
    payload["angles"] = {}
    result = evaluate_chart_ruler(payload)
    assert result["status"] == "unavailable"
    assert result["confidence"] == ANGLE_DEPENDENT_UNAVAILABLE
    assert result["missing_inputs"]


def test_missing_ascendant_sign_returns_unavailable():
    payload = _make_payload()
    payload["angles"]["Ascendant"] = {"longitude": 0.0}  # no sign
    result = evaluate_chart_ruler(payload)
    assert result["status"] == "unavailable"
    assert result["confidence"] == ANGLE_DEPENDENT_UNAVAILABLE


# ── Successful ruler identification ──────────────────────────────────────────

def test_aries_rising_ruler_is_mars():
    payload = _make_payload(asc_sign="Aries")
    result  = evaluate_chart_ruler(payload)
    assert result["status"]        == "success"
    assert result["primary_ruler"] == "Mars"
    assert result["confidence"]    == EXACT_BIRTH_TIME
    assert result["missing_inputs"] == []


def test_scorpio_rising_has_modern_co_ruler():
    payload = _make_payload(asc_sign="Scorpio", asc_lon=210.0)
    # Add Scorpio Ascendant — Mars is primary, Pluto is modern co-ruler
    result  = evaluate_chart_ruler(payload)
    assert result["status"]          == "success"
    assert result["primary_ruler"]   == "Mars"
    assert result["modern_co_ruler"] == "Pluto"


def test_aquarius_rising_has_modern_co_ruler():
    payload = _make_payload(asc_sign="Aquarius", asc_lon=300.0)
    result  = evaluate_chart_ruler(payload)
    assert result["primary_ruler"]   == "Saturn"
    assert result["modern_co_ruler"] == "Uranus"


def test_leo_rising_no_modern_co_ruler():
    payload = _make_payload(asc_sign="Leo", asc_lon=120.0)
    result  = evaluate_chart_ruler(payload)
    assert result["primary_ruler"]   == "Sun"
    assert result["modern_co_ruler"] is None


# ── CR-03: Station threshold ──────────────────────────────────────────────────

def test_mars_stationary_detected_at_per_body_threshold():
    # Mars threshold = 0.05; speed 0.04 → stationary
    payload = _make_payload(asc_sign="Aries", planets={
        "Mars": _body("Aries", house=1, degree=10.0, longitude=10.0, speed=0.04)
    })
    result = evaluate_chart_ruler(payload)
    assert result["condition_record"]["motion"]["is_stationary"] is True


def test_mars_not_stationary_above_threshold():
    # Mars speed 0.06 → NOT stationary
    payload = _make_payload(asc_sign="Aries", planets={
        "Mars": _body("Aries", house=1, degree=10.0, longitude=10.0, speed=0.06)
    })
    result = evaluate_chart_ruler(payload)
    assert result["condition_record"]["motion"]["is_stationary"] is False


def test_sun_never_stationary():
    # Sun is not in STATION_THRESHOLDS → never stationary
    payload = _make_payload(asc_sign="Leo", asc_lon=120.0, planets={
        "Sun": _body("Leo", house=1, degree=10.0, longitude=130.0, speed=0.0)
    })
    result = evaluate_chart_ruler(payload)
    assert result["condition_record"]["motion"]["is_stationary"] is False


# ── Condition record structure ────────────────────────────────────────────────

def test_condition_record_has_required_keys():
    payload = _make_payload(asc_sign="Aries")
    result  = evaluate_chart_ruler(payload)
    cr = result["condition_record"]
    for key in ("placement", "motion", "dignity", "angularity", "sect", "luminary_integration"):
        assert key in cr, f"Missing condition_record key: {key}"


def test_motion_keys_present():
    payload = _make_payload(asc_sign="Aries")
    result  = evaluate_chart_ruler(payload)
    motion  = result["condition_record"]["motion"]
    for key in ("is_retrograde", "is_stationary", "speed"):
        assert key in motion, f"Missing motion key: {key}"


def test_retrograde_ruler_is_recorded_not_penalised():
    # Retrograde should appear in motion, not as a hidden score penalty
    payload = _make_payload(asc_sign="Aries", planets={
        "Mars": _body("Aries", house=1, degree=10.0, longitude=10.0, speed=-0.4)
    })
    result = evaluate_chart_ruler(payload)
    assert result["condition_record"]["motion"]["is_retrograde"] is True
    assert result["status"] == "success"


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
