"""
Tests for planetary_angularity_algorithm.py (formulas/standard/angularity.py).

Covers:
- Canonical angle key names (CR-01)
- House type classification
- Angle conjunction detection and orb
- ANGLE_ALIASES export
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.angularity import evaluate_angularity
from formulas.standard.normalization import ANGLE_ALIAS_MAP as ANGLE_ALIASES
from formulas.standard.normalization import CANONICAL_ANGLE_NAMES as CANONICAL_ANGLES


def _make_payload(body_lon, house=1, angles=None):
    payload = {
        "standard_planets": {
            "Sun": {
                "longitude": body_lon,
                "house": house,
                "sign": "Aries",
                "degree": 10,
                "minute": 0,
                "degree_decimal": 10.0,
                "speed": 1.0,
            }
        },
        "angles": angles or {}
    }
    return payload


# ── Canonical angle keys ──────────────────────────────────────────────────────

def test_canonical_angles_list():
    assert "Ascendant" in CANONICAL_ANGLES
    assert "Midheaven" in CANONICAL_ANGLES
    assert "Descendant" in CANONICAL_ANGLES
    assert "Imum_Coeli" in CANONICAL_ANGLES
    assert "ASC" not in CANONICAL_ANGLES
    assert "MC" not in CANONICAL_ANGLES


def test_angle_aliases_map():
    assert ANGLE_ALIASES["ASC"] == "Ascendant"
    assert ANGLE_ALIASES["MC"] == "Midheaven"
    assert ANGLE_ALIASES["DSC"] == "Descendant"
    assert ANGLE_ALIASES["IC"] == "Imum_Coeli"


# ── House type classification ─────────────────────────────────────────────────

def test_angular_houses():
    for house in (1, 4, 7, 10):
        result = evaluate_angularity(_make_payload(10.0, house=house), "Sun")
        assert result["house_type"] == "angular", f"House {house} should be angular"


def test_succedent_houses():
    for house in (2, 5, 8, 11):
        result = evaluate_angularity(_make_payload(10.0, house=house), "Sun")
        assert result["house_type"] == "succedent", f"House {house} should be succedent"


def test_cadent_houses():
    for house in (3, 6, 9, 12):
        result = evaluate_angularity(_make_payload(10.0, house=house), "Sun")
        assert result["house_type"] == "cadent", f"House {house} should be cadent"


# ── Angle conjunction detection ───────────────────────────────────────────────

def test_conjunct_ascendant_within_orb():
    # Body at 12°, ASC at 10° → distance = 2° → within default 8°
    payload = _make_payload(12.0, house=1, angles={
        "Ascendant": {"longitude": 10.0}
    })
    result = evaluate_angularity(payload, "Sun")
    assert result["is_conjunct_angle"] is True
    assert result["conjunct_angle_name"] == "Ascendant"
    assert result["orb"] == 2.0


def test_conjunct_midheaven():
    payload = _make_payload(270.0, house=10, angles={
        "Midheaven": {"longitude": 270.0}
    })
    result = evaluate_angularity(payload, "Sun")
    assert result["is_conjunct_angle"] is True
    assert result["conjunct_angle_name"] == "Midheaven"
    assert result["orb"] == 0.0


def test_conjunct_descendant():
    payload = _make_payload(185.0, house=7, angles={
        "Descendant": {"longitude": 180.0}
    })
    result = evaluate_angularity(payload, "Sun")
    assert result["is_conjunct_angle"] is True
    assert result["conjunct_angle_name"] == "Descendant"


def test_conjunct_imum_coeli():
    payload = _make_payload(92.0, house=4, angles={
        "Imum_Coeli": {"longitude": 90.0}
    })
    result = evaluate_angularity(payload, "Sun")
    assert result["is_conjunct_angle"] is True
    assert result["conjunct_angle_name"] == "Imum_Coeli"


def test_not_conjunct_outside_orb():
    payload = _make_payload(20.0, house=1, angles={
        "Ascendant": {"longitude": 0.0}
    })
    result = evaluate_angularity(payload, "Sun")
    assert result["is_conjunct_angle"] is False
    assert result["conjunct_angle_name"] is None


def test_closest_angle_wins():
    # Body at 10°, ASC at 8° (dist 2°), MC at 6° (dist 4°) → ASC is closer
    payload = _make_payload(10.0, house=1, angles={
        "Ascendant": {"longitude": 8.0},
        "Midheaven": {"longitude": 6.0},
    })
    result = evaluate_angularity(payload, "Sun")
    assert result["conjunct_angle_name"] == "Ascendant"
    assert result["orb"] == 2.0


def test_wrap_around_0_360():
    # Body at 1°, ASC at 357° → shortest distance = 4°
    payload = _make_payload(1.0, house=1, angles={
        "Ascendant": {"longitude": 357.0}
    })
    result = evaluate_angularity(payload, "Sun")
    assert result["is_conjunct_angle"] is True
    assert result["orb"] == 4.0


def test_missing_body_returns_unknown():
    payload = {"standard_planets": {}, "angles": {}}
    result = evaluate_angularity(payload, "Mars")
    assert result["house_type"] == "unknown"
    assert result["is_conjunct_angle"] is False


def test_custom_orb():
    payload = _make_payload(15.0, house=1, angles={
        "Ascendant": {"longitude": 10.0}
    })
    # Distance = 5°
    result_narrow = evaluate_angularity(payload, "Sun", angle_orb=4.0)
    result_wide   = evaluate_angularity(payload, "Sun", angle_orb=6.0)
    assert result_narrow["is_conjunct_angle"] is False
    assert result_wide["is_conjunct_angle"] is True


def test_output_keys_present():
    result = evaluate_angularity(_make_payload(10.0), "Sun")
    for key in ("house_number", "house_type", "is_conjunct_angle", "conjunct_angle_name", "orb"):
        assert key in result, f"Missing key: {key}"


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
