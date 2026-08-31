"""
Tests for expanded_dignity_matrix.py (formulas/standard/dignity.py).

Covers:
- All 5 dignity layers: domicile, exaltation, triplicity, term, face (CR-06)
- Detriment and fall
- classical_score vs modern_modifier separation (CR-06)
- Outer planet exclusion from triplicity/term/face
- Peregrine flag correctness
- Face/Decan implementation present in return dict
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.dignity import evaluate_dignity


def _make_payload(body_name, sign, degree_decimal, sun_lon=90.0, asc_lon=0.0):
    """
    Minimal payload for dignity evaluation.
    When body_name == 'Sun', the Sun entry uses the test sign/degree so we don't
    overwrite the body under test with a separate sect-determination Sun entry.
    """
    # When Sun is the body under test, use sun_lon so sect can be determined correctly.
    body_lon = sun_lon if body_name == "Sun" else 0.0
    body_entry = {
        "sign": sign,
        "degree": int(degree_decimal),
        "minute": 0,
        "degree_decimal": degree_decimal,
        "longitude": body_lon,
        "speed": 1.0,
        "house": 10,
    }
    planets: dict = {body_name: body_entry}
    # Add a separate Sun only when it is not already the body under test,
    # so sect can be determined independently.
    if body_name != "Sun":
        planets["Sun"] = {
            "longitude": sun_lon,
            "sign": "Cancer",
            "degree": int(sun_lon % 30),
            "minute": 0,
            "degree_decimal": float(sun_lon % 30),
            "speed": 1.0,
            "house": 10,
        }
    return {
        "standard_planets": planets,
        "angles": {"Ascendant": {"longitude": asc_lon, "sign": "Aries"}},
        "houses": {},
    }


# ── Domicile ──────────────────────────────────────────────────────────────────

def test_domicile_mars_aries():
    result = evaluate_dignity(_make_payload("Mars", "Aries", 15.0), "Mars")
    assert result["is_domicile"] is True
    assert result["classical_score"] >= 5.0


def test_domicile_sun_leo():
    result = evaluate_dignity(_make_payload("Sun", "Leo", 10.0), "Sun")
    assert result["is_domicile"] is True
    assert result["classical_score"] >= 5.0


# ── Detriment ─────────────────────────────────────────────────────────────────

def test_detriment_sun_aquarius():
    result = evaluate_dignity(_make_payload("Sun", "Aquarius", 10.0), "Sun")
    assert result["is_detriment"] is True
    assert result["classical_score"] <= -5.0


def test_detriment_mars_libra():
    result = evaluate_dignity(_make_payload("Mars", "Libra", 10.0), "Mars")
    assert result["is_detriment"] is True


# ── Exaltation & Fall ─────────────────────────────────────────────────────────

def test_exaltation_sun_aries():
    result = evaluate_dignity(_make_payload("Sun", "Aries", 5.0), "Sun")
    assert result["is_exalted"] is True
    assert result["classical_score"] >= 4.0


def test_exaltation_saturn_libra():
    result = evaluate_dignity(_make_payload("Saturn", "Libra", 20.0), "Saturn")
    assert result["is_exalted"] is True


def test_fall_moon_scorpio():
    result = evaluate_dignity(_make_payload("Moon", "Scorpio", 15.0), "Moon")
    assert result["is_fall"] is True
    assert result["classical_score"] <= -4.0


# ── Triplicity ────────────────────────────────────────────────────────────────

def test_triplicity_sun_fire_day():
    # Sun rules fire triplicity by day; day chart (sun above horizon at 90°)
    result = evaluate_dignity(_make_payload("Sun", "Leo", 15.0, sun_lon=90.0, asc_lon=0.0), "Sun")
    assert result["is_triplicity"] is True
    assert result["classical_score"] >= 3.0


def test_triplicity_excluded_when_chart_sect_unknown():
    # No ASC → sect unknown → triplicity should not be awarded
    payload = {
        "standard_planets": {
            "Sun": {"sign": "Leo", "degree": 15, "minute": 0, "degree_decimal": 15.0,
                    "longitude": 90.0, "speed": 1.0, "house": 10}
        },
        "angles": {},
        "houses": {}
    }
    result = evaluate_dignity(payload, "Sun")
    assert result["is_triplicity"] is False


# ── Term/Bound ────────────────────────────────────────────────────────────────

def test_term_jupiter_aries_first_6_degrees():
    # Aries: Jupiter rules 0–6°
    result = evaluate_dignity(_make_payload("Jupiter", "Aries", 4.0), "Jupiter")
    assert result["is_term"] is True
    assert result["classical_score"] >= 2.0


def test_term_boundary_exclusive():
    # Aries first term is < 6° (Jupiter). At 6.0 it falls to Venus term.
    result_in  = evaluate_dignity(_make_payload("Jupiter", "Aries", 5.9), "Jupiter")
    result_out = evaluate_dignity(_make_payload("Jupiter", "Aries", 6.0), "Jupiter")
    assert result_in["is_term"] is True
    assert result_out["is_term"] is False


# ── Face/Decan ────────────────────────────────────────────────────────────────

def test_face_key_present_in_output():
    result = evaluate_dignity(_make_payload("Mars", "Aries", 5.0), "Mars")
    assert "is_face" in result, "is_face must be in dignity output (CR-06)"


def test_face_mars_aries_first_decan():
    # Aries decan 1 (0–10°): Mars
    result = evaluate_dignity(_make_payload("Mars", "Aries", 5.0), "Mars")
    assert result["is_face"] is True
    assert result["classical_score"] >= 1.0


def test_face_sun_aries_second_decan():
    # Aries decan 2 (10–20°): Sun
    result = evaluate_dignity(_make_payload("Sun", "Aries", 15.0), "Sun")
    assert result["is_face"] is True


def test_face_venus_aries_third_decan():
    # Aries decan 3 (20–30°): Venus
    result = evaluate_dignity(_make_payload("Venus", "Aries", 25.0), "Venus")
    assert result["is_face"] is True


def test_face_wrong_planet_not_awarded():
    # Mars is NOT the face ruler of Aries 10–20° (Sun is)
    result = evaluate_dignity(_make_payload("Mars", "Aries", 15.0), "Mars")
    assert result["is_face"] is False


# ── Outer planets ─────────────────────────────────────────────────────────────

def test_outer_planet_no_triplicity():
    result = evaluate_dignity(_make_payload("Uranus", "Libra", 10.0), "Uranus")
    assert result["is_triplicity"] is False


def test_outer_planet_no_term():
    result = evaluate_dignity(_make_payload("Neptune", "Pisces", 5.0), "Neptune")
    assert result["is_term"] is False


def test_outer_planet_no_face():
    result = evaluate_dignity(_make_payload("Pluto", "Scorpio", 5.0), "Pluto")
    assert result["is_face"] is False


def test_modern_domicile_tracked_in_modern_modifier():
    # Uranus in Aquarius: modern domicile → modern_modifier = 5, classical_score = 0
    result = evaluate_dignity(_make_payload("Uranus", "Aquarius", 15.0), "Uranus")
    assert result["is_domicile"] is True
    assert result["modern_ruler"] is True
    assert result["modern_modifier"] == 5.0
    assert result["classical_score"] == 0.0  # No classical domicile for Uranus


def test_traditional_domicile_tracked_in_classical_score():
    # Saturn in Aquarius: traditional domicile → classical_score = 5, modern_modifier = 0
    result = evaluate_dignity(_make_payload("Saturn", "Aquarius", 15.0), "Saturn")
    assert result["is_domicile"] is True
    assert result["modern_ruler"] is False
    assert result["classical_score"] >= 5.0
    assert result["modern_modifier"] == 0.0


def test_dignity_score_is_sum():
    result = evaluate_dignity(_make_payload("Saturn", "Aquarius", 15.0), "Saturn")
    assert result["dignity_score"] == result["classical_score"] + result["modern_modifier"]


# ── Peregrine ─────────────────────────────────────────────────────────────────

def test_peregrine_applicable_false_for_outer():
    result = evaluate_dignity(_make_payload("Uranus", "Gemini", 15.0), "Uranus")
    assert result["peregrine_applicable"] is False
    assert result["is_peregrine"] is False  # outer planets: flag not applied


def test_peregrine_true_when_no_positive_dignity():
    # Moon in Capricorn: Moon is in DETRIMENT (Capricorn is Moon's detriment).
    # A detriment does not clear is_peregrine — only positive dignities do.
    result = evaluate_dignity(
        _make_payload("Moon", "Capricorn", 15.0, sun_lon=90.0, asc_lon=0.0),
        "Moon"
    )
    assert result["is_detriment"] is True
    # Detriment doesn't award a positive dignity, so peregrine stays True
    # unless Moon also has triplicity (earth/day=Venus, earth/night=Moon).
    # Day chart (sun_lon=90, asc_lon=0 → diff=90 < 180 → day). Earth night ruler is Moon
    # but this is a DAY chart, so earth triplicity goes to Venus, not Moon.
    assert result["is_triplicity"] is False
    assert result["is_peregrine"] is True


def test_all_dignity_keys_present():
    result = evaluate_dignity(_make_payload("Mars", "Aries", 5.0), "Mars")
    required = {
        "is_domicile", "is_exalted", "is_triplicity", "is_term", "is_face",
        "is_detriment", "is_fall", "is_peregrine", "peregrine_applicable",
        "modern_ruler", "classical_score", "modern_modifier", "dignity_score"
    }
    for key in required:
        assert key in result, f"Missing dignity key: {key}"


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
