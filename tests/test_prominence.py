"""
Tests for formulas/standard/planetary_prominence.py.

Covers:
- Prominence is independent of condition score
- Retrograde planet can be prominent (no penalty)
- Station bonus applies when per-body threshold is met
- Chart ruler gets highest weight
- Angular placement boosts prominence
- Angle conjunction boosts prominence with canonical name in driver
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.planetary_prominence import evaluate_prominence, PROMINENCE_WEIGHTS


def _body(sign, house=5, degree=15.0, speed=1.0, longitude=None):
    if longitude is None:
        signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                 "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
        longitude = float(signs.index(sign) * 30 + degree)
    return {
        "longitude": longitude, "speed": speed, "retrograde": speed < 0,
        "house": house, "sign": sign, "degree": int(degree),
        "minute": 0, "degree_decimal": degree,
    }


def _make_payload(asc_sign="Aries", asc_lon=0.0, planet_overrides=None, angle_overrides=None):
    planets = {
        "Sun":     _body("Cancer",   house=10, degree=15.0, longitude=105.0, speed=1.0),
        "Moon":    _body("Virgo",    house=6,  degree=10.0, longitude=160.0, speed=13.0),
        "Mercury": _body("Leo",      house=5,  degree=5.0,  longitude=125.0, speed=1.2),
        "Venus":   _body("Gemini",   house=3,  degree=20.0, longitude=80.0,  speed=1.0),
        "Mars":    _body("Aries",    house=1,  degree=10.0, longitude=10.0,  speed=0.6),
        "Jupiter": _body("Taurus",   house=2,  degree=5.0,  longitude=35.0,  speed=0.1),
        "Saturn":  _body("Pisces",   house=12, degree=5.0,  longitude=335.0, speed=0.1),
        "Uranus":  _body("Taurus",   house=2,  degree=20.0, longitude=50.0,  speed=0.04),
        "Neptune": _body("Pisces",   house=12, degree=2.0,  longitude=332.0, speed=0.02),
        "Pluto":   _body("Aquarius", house=11, degree=2.0,  longitude=302.0, speed=0.015),
    }
    if planet_overrides:
        for body, data in planet_overrides.items():
            if body in planets:
                planets[body].update(data)
            else:
                planets[body] = data
    angles = {
        "Ascendant": {"longitude": asc_lon, "sign": asc_sign},
        "Midheaven": {"longitude": 270.0,   "sign": "Capricorn"},
    }
    if angle_overrides:
        angles.update(angle_overrides)
    return {
        "standard_planets": planets,
        "angles": angles,
        "houses": {
            f"House_{i}": {"sign": s, "longitude": float((i-1)*30),
                           "degree": 0, "minute": 0, "degree_decimal": 0.0}
            for i, s in enumerate(
                ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                 "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"], 1
            )
        },
        "aspects": [],
    }


# ── Prominence/condition independence ─────────────────────────────────────────

def test_retrograde_planet_can_be_prominent():
    # Mars retrograde in house 1 (angular, chart ruler for Aries rising) — must still be prominent
    payload = _make_payload(asc_sign="Aries", asc_lon=0.0, planet_overrides={
        "Mars": {"speed": -0.4, "house": 1, "sign": "Aries",
                 "degree": 10, "minute": 0, "degree_decimal": 10.0, "longitude": 10.0}
    })
    result = evaluate_prominence(payload)
    mars_entry = next(p for p in result["rankings"] if p["body"] == "Mars")
    assert mars_entry["normalized_score"] > 0.5, (
        f"Retrograde Mars (chart ruler, angular) should be prominent: {mars_entry}"
    )
    assert "Ascendant Ruler" in mars_entry["drivers"]


def test_prominence_does_not_use_condition_score():
    # Two payloads differing only in retrograde state should have same prominence for Mars
    payload_direct = _make_payload(asc_sign="Aries", planet_overrides={
        "Mars": {"speed": 0.6, "house": 1, "sign": "Aries",
                 "degree": 10, "minute": 0, "degree_decimal": 10.0, "longitude": 10.0}
    })
    payload_retro  = _make_payload(asc_sign="Aries", planet_overrides={
        "Mars": {"speed": -0.6, "house": 1, "sign": "Aries",
                 "degree": 10, "minute": 0, "degree_decimal": 10.0, "longitude": 10.0}
    })
    r_direct = evaluate_prominence(payload_direct)
    r_retro  = evaluate_prominence(payload_retro)
    score_direct = next(p for p in r_direct["rankings"] if p["body"] == "Mars")["normalized_score"]
    score_retro  = next(p for p in r_retro["rankings"] if p["body"] == "Mars")["normalized_score"]
    assert score_direct == score_retro, (
        f"Prominence must not change with retrograde: direct={score_direct}, retro={score_retro}"
    )


# ── Chart ruler ───────────────────────────────────────────────────────────────

def test_chart_ruler_highest_weight():
    payload = _make_payload(asc_sign="Aries")
    result  = evaluate_prominence(payload)
    mars_entry = next(p for p in result["rankings"] if p["body"] == "Mars")
    assert "Ascendant Ruler" in mars_entry["drivers"]
    assert mars_entry["raw_score"] >= PROMINENCE_WEIGHTS["is_chart_ruler"]


def test_primary_ruler_in_result():
    payload = _make_payload(asc_sign="Aries")
    result  = evaluate_prominence(payload)
    assert result["primary_ruler"] == "Mars"


# ── Luminaries ────────────────────────────────────────────────────────────────

def test_luminaries_get_luminary_weight():
    payload = _make_payload()
    result  = evaluate_prominence(payload)
    sun_entry  = next(p for p in result["rankings"] if p["body"] == "Sun")
    moon_entry = next(p for p in result["rankings"] if p["body"] == "Moon")
    assert "Luminary" in sun_entry["drivers"]
    assert "Luminary" in moon_entry["drivers"]


# ── Angle conjunction ─────────────────────────────────────────────────────────

def test_angle_conjunction_boosts_prominence():
    # Venus exactly on Ascendant → should get is_conjunct_angle bonus
    payload = _make_payload(asc_sign="Aries", asc_lon=0.0, planet_overrides={
        "Venus": {"longitude": 1.0, "house": 1, "sign": "Aries",
                  "degree": 1, "minute": 0, "degree_decimal": 1.0, "speed": 1.0}
    })
    result      = evaluate_prominence(payload)
    venus_entry = next(p for p in result["rankings"] if p["body"] == "Venus")
    # Should mention an angle conjunction in drivers
    angle_drivers = [d for d in venus_entry["drivers"] if "Conjunct" in d]
    assert angle_drivers, f"Expected angle conjunction driver for Venus: {venus_entry['drivers']}"


def test_angle_conjunction_uses_canonical_name_in_driver():
    payload = _make_payload(asc_sign="Aries", asc_lon=0.0, planet_overrides={
        "Venus": {"longitude": 1.0, "house": 1, "sign": "Aries",
                  "degree": 1, "minute": 0, "degree_decimal": 1.0, "speed": 1.0}
    })
    result      = evaluate_prominence(payload)
    venus_entry = next(p for p in result["rankings"] if p["body"] == "Venus")
    drivers_str = " ".join(venus_entry["drivers"])
    assert "ASC" not in drivers_str, "Shorthand 'ASC' should not appear in prominence drivers"
    assert "Ascendant" in drivers_str or "Midheaven" in drivers_str or "Descendant" in drivers_str


# ── Angular house ─────────────────────────────────────────────────────────────

def test_angular_house_boosts_more_than_succedent():
    payload_angular   = _make_payload(planet_overrides={
        "Saturn": {"house": 10, "sign": "Capricorn", "degree": 5,
                   "minute": 0, "degree_decimal": 5.0, "longitude": 275.0, "speed": 0.1}
    })
    payload_succedent = _make_payload(planet_overrides={
        "Saturn": {"house": 11, "sign": "Aquarius", "degree": 5,
                   "minute": 0, "degree_decimal": 5.0, "longitude": 305.0, "speed": 0.1}
    })
    r_angular   = evaluate_prominence(payload_angular)
    r_succedent = evaluate_prominence(payload_succedent)
    s_a = next(p for p in r_angular["rankings"]   if p["body"] == "Saturn")["raw_score"]
    s_s = next(p for p in r_succedent["rankings"] if p["body"] == "Saturn")["raw_score"]
    assert s_a > s_s, f"Angular should outscore succedent: {s_a} vs {s_s}"


# ── Stationary bonus ──────────────────────────────────────────────────────────

def test_stationary_planet_gets_bonus():
    # Jupiter at effectively zero speed (below its 0.020 threshold)
    payload_moving    = _make_payload(planet_overrides={"Jupiter": {"speed": 0.12}})
    payload_stationary = _make_payload(planet_overrides={"Jupiter": {"speed": 0.001}})
    r_m = evaluate_prominence(payload_moving)
    r_s = evaluate_prominence(payload_stationary)
    score_m = next(p for p in r_m["rankings"] if p["body"] == "Jupiter")["raw_score"]
    score_s = next(p for p in r_s["rankings"] if p["body"] == "Jupiter")["raw_score"]
    assert score_s > score_m, "Stationary Jupiter should outscore moving Jupiter"


# ── Result structure ──────────────────────────────────────────────────────────

def test_all_standard_bodies_in_rankings():
    payload = _make_payload()
    result  = evaluate_prominence(payload)
    bodies  = {p["body"] for p in result["rankings"]}
    for body in ("Sun", "Moon", "Mercury", "Venus", "Mars",
                 "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"):
        assert body in bodies


def test_normalized_scores_in_0_1():
    payload = _make_payload()
    result  = evaluate_prominence(payload)
    for p in result["rankings"]:
        assert 0.0 <= p["normalized_score"] <= 1.0, (
            f"{p['body']} normalized_score out of range: {p['normalized_score']}"
        )


def test_highest_prominence_is_first():
    payload = _make_payload()
    result  = evaluate_prominence(payload)
    assert result["highest_prominence"] == result["rankings"][0]["body"]


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
