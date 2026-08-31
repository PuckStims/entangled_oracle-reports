"""
Tests for sect_calculation_algorithm.py (formulas/standard/sect.py).

Covers:
- Geometric horizon sect (CR-02)
- Confidence states (CR-07)
- Planetary sect faction assignment
- Mercury Oriental/Occidental convention
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.sect import (
    evaluate_chart_sect,
    evaluate_chart_sect_detailed,
    evaluate_planetary_sect,
    get_sect_light,
    MERCURY_SECT_CONVENTION,
)


def _make_payload(sun_lon, asc_lon=None, mercury_lon=None):
    """Minimal payload for sect tests."""
    payload = {
        "standard_planets": {
            "Sun": {"longitude": sun_lon, "speed": 1.0, "house": 10, "sign": "Capricorn",
                    "degree": 15, "minute": 0, "degree_decimal": 15.0},
        },
        "angles": {}
    }
    if asc_lon is not None:
        payload["angles"]["Ascendant"] = {"longitude": asc_lon, "sign": "Aries"}
    if mercury_lon is not None:
        payload["standard_planets"]["Mercury"] = {
            "longitude": mercury_lon, "speed": 1.2, "house": 11, "sign": "Capricorn",
            "degree": 10, "minute": 0, "degree_decimal": 10.0
        }
    return payload


# ── evaluate_chart_sect_detailed ──────────────────────────────────────────────

def test_day_chart_sun_above_horizon():
    # ASC = 0°, Sun = 90° (upper hemisphere, diff = 90 < 180 → day)
    result = evaluate_chart_sect_detailed(_make_payload(sun_lon=90.0, asc_lon=0.0))
    assert result["sect"] == "day", result
    assert result["confidence"] == "exact_birth_time"
    assert result["missing_inputs"] == []


def test_night_chart_sun_below_horizon():
    # ASC = 0°, Sun = 270° (lower hemisphere, diff = 270 > 180 → night)
    result = evaluate_chart_sect_detailed(_make_payload(sun_lon=270.0, asc_lon=0.0))
    assert result["sect"] == "night", result
    assert result["confidence"] == "exact_birth_time"


def test_day_chart_near_mc():
    # ASC = 0°, Sun = 180° (DSC) → exactly on horizon → unknown
    result = evaluate_chart_sect_detailed(_make_payload(sun_lon=180.0, asc_lon=0.0))
    assert result["sect"] == "unknown"
    assert result["confidence"] == "provisional_near_horizon"


def test_sun_exactly_on_asc():
    result = evaluate_chart_sect_detailed(_make_payload(sun_lon=0.0, asc_lon=0.0))
    assert result["sect"] == "unknown"
    assert result["confidence"] == "provisional_near_horizon"


def test_missing_ascendant_returns_unavailable():
    payload = _make_payload(sun_lon=90.0)  # No asc_lon provided
    result = evaluate_chart_sect_detailed(payload)
    assert result["sect"] == "unknown"
    assert result["confidence"] == "angle_dependent_unavailable"
    assert "Ascendant longitude" in result["missing_inputs"]


def test_missing_sun_returns_unavailable():
    payload = {"standard_planets": {}, "angles": {"Ascendant": {"longitude": 0.0}}}
    result = evaluate_chart_sect_detailed(payload)
    assert result["sect"] == "unknown"
    assert result["confidence"] == "angle_dependent_unavailable"


def test_near_horizon_sun_is_provisional():
    # ASC = 0°, Sun = 3° — within HORIZON_PROXIMITY_THRESHOLD → provisional
    result = evaluate_chart_sect_detailed(_make_payload(sun_lon=3.0, asc_lon=0.0))
    assert result["sect"] == "day"
    assert result["confidence"] == "provisional_near_horizon"


def test_evaluate_chart_sect_string_wrapper():
    result = evaluate_chart_sect(_make_payload(sun_lon=90.0, asc_lon=0.0))
    assert result == "day"


# ── get_sect_light ────────────────────────────────────────────────────────────

def test_sect_light_day():
    assert get_sect_light("day") == "Sun"


def test_sect_light_night():
    assert get_sect_light("night") == "Moon"


def test_sect_light_unknown():
    assert get_sect_light("unknown") == "unknown"


# ── evaluate_planetary_sect ───────────────────────────────────────────────────

def test_sun_in_sect_day():
    payload = _make_payload(sun_lon=90.0, asc_lon=0.0)
    result = evaluate_planetary_sect(payload, "Sun", "day")
    assert result["is_in_sect"] is True
    assert result["planet_faction"] == "diurnal"


def test_moon_in_sect_night():
    payload = _make_payload(sun_lon=270.0, asc_lon=0.0)
    result = evaluate_planetary_sect(payload, "Moon", "night")
    assert result["is_in_sect"] is True
    assert result["planet_faction"] == "nocturnal"


def test_mars_out_of_sect_day():
    payload = _make_payload(sun_lon=90.0, asc_lon=0.0)
    result = evaluate_planetary_sect(payload, "Mars", "day")
    assert result["is_in_sect"] is False
    assert result["planet_faction"] == "nocturnal"


def test_mercury_oriental_is_diurnal():
    # Mercury at 10°, Sun at 200° → (10 - 200 + 360) % 360 = 170 < 180 → Occidental → nocturnal
    # Mercury at 300°, Sun at 50° → (300 - 50) % 360 = 250 > 180 → Oriental → diurnal
    payload = _make_payload(sun_lon=50.0, asc_lon=0.0, mercury_lon=300.0)
    result = evaluate_planetary_sect(payload, "Mercury", "day")
    assert result["planet_faction"] == "diurnal"
    assert result["is_in_sect"] is True


def test_mercury_occidental_is_nocturnal():
    # Mercury at 100°, Sun at 50° → (100 - 50) % 360 = 50 < 180 → Occidental → nocturnal
    payload = _make_payload(sun_lon=50.0, asc_lon=0.0, mercury_lon=100.0)
    result = evaluate_planetary_sect(payload, "Mercury", "night")
    assert result["planet_faction"] == "nocturnal"
    assert result["is_in_sect"] is True


def test_mercury_sect_convention_documented():
    assert MERCURY_SECT_CONVENTION == "oriental_diurnal"


def test_sect_wraps_360():
    # ASC = 350°, Sun = 10° → diff = (10 - 350 + 360) % 360 = 20 < 180 → day
    result = evaluate_chart_sect_detailed(_make_payload(sun_lon=10.0, asc_lon=350.0))
    assert result["sect"] == "day"


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
