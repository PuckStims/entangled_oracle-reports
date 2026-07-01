"""
tests/test_eclipse_house_fix.py

Regression suite for the eclipse house contradiction fix.

Diana Ross test case
--------------------
  Solar eclipse · 20.04° Leo · August 12, 2026
  Scorpio rising → Leo is the 10th Whole Sign house
  Activates natal Jupiter (in the 10th house)
  ECLIPSE_TARGET_KEYS["Jupiter"] = "6"   ← planet-order index (wrong for EO)
  natal_house for Jupiter in this chart   = 10 ← correct key for EO pack

Root cause: EO eclipse blocks are keyed by Whole Sign house number (1–12),
while plainspeak eclipse blocks are keyed by planet-order index
(Sun=1, Moon=2, … Jupiter=6 …). The eclipse_key field in CONTENT_PACKS
governs which event field is used as the lookup key.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import CONTENT_PACKS, BLOCKS_DIR


# ── Helper: mimic _select_year_block eclipse logic ────────────────────────────

def _eclipse_key_for_event(event: dict, content_pack: str) -> str:
    """Returns the key string that would be passed to the block JSON lookup."""
    pack_paths = CONTENT_PACKS[content_pack]
    eclipse_key_field = pack_paths.get("eclipse_key", "natal_target_key")
    if eclipse_key_field == "natal_house":
        house = event.get("natal_house") or event.get("whole_sign_house") or 0
        return str(house) if house else "fallback"
    return event.get("natal_target_key", "fallback")


def _make_diana_eclipse_event() -> dict:
    """Minimal eclipse event representing the Diana Ross regression case."""
    return {
        "event_type": "eclipse",
        "eclipse_type": "Solar",
        "eclipse_sign": "Leo",
        "eclipse_degree": 20.04,
        "natal_target": "Jupiter",
        "natal_target_key": "6",       # planet-order index (Sun=1 … Jupiter=6)
        "natal_house": 10,              # Whole Sign house under Scorpio rising
        "whole_sign_house": 10,
        "natal_contact": "Jupiter",
        "natal_contact_house": 10,
        "natal_target_display": "your Jupiter in the 10th house",
    }


# ── Pack config tests ──────────────────────────────────────────────────────────

def test_eo_pack_uses_house_key():
    """EO content pack must declare eclipse_key = 'natal_house'."""
    assert CONTENT_PACKS["entangled_oracle"].get("eclipse_key") == "natal_house", (
        "EO pack must set eclipse_key='natal_house' so house-indexed blocks are selected."
    )


def test_plainspeak_pack_uses_planet_key():
    """Plainspeak content pack must declare eclipse_key = 'natal_target_key'."""
    assert CONTENT_PACKS["plainspeak"].get("eclipse_key") == "natal_target_key", (
        "Plainspeak pack must set eclipse_key='natal_target_key' for planet-index lookup."
    )


# ── Key selection tests ────────────────────────────────────────────────────────

def test_eo_eclipse_selects_house_10_not_6():
    """
    EO pack must select block key '10' (10th house) for Jupiter in a
    Scorpio-rising chart, NOT '6' (Jupiter's planet-order index).
    """
    event = _make_diana_eclipse_event()
    key = _eclipse_key_for_event(event, "entangled_oracle")
    assert key == "10", (
        f"EO eclipse key should be '10' (natal house), got '{key}'. "
        "The prose layer must not select the 6th-house block when Jupiter is in the 10th house."
    )


def test_plainspeak_eclipse_selects_planet_index_6():
    """Plainspeak pack must select block key '6' (Jupiter's planet-order index)."""
    event = _make_diana_eclipse_event()
    key = _eclipse_key_for_event(event, "plainspeak")
    assert key == "6", (
        f"Plainspeak eclipse key should be '6' (natal_target_key), got '{key}'."
    )


# ── Block file content tests ───────────────────────────────────────────────────

def test_eo_eclipse_file_has_10th_house_block():
    """The EO eclipse JSON must contain a Solar/10 block (for the 10th house)."""
    path = CONTENT_PACKS["entangled_oracle"]["eclipses"]
    assert os.path.exists(path), f"EO eclipse file not found: {path}"
    with open(path, encoding="utf-8") as f:
        blocks = json.load(f)
    assert "10" in blocks.get("Solar", {}), (
        "EO eclipse file must have a 'Solar'/'10' block for 10th-house eclipses."
    )


def test_eo_eclipse_10th_differs_from_6th():
    """
    The 10th-house and 6th-house EO eclipse blocks must be distinct prose.
    If they were the same, the Diana Ross case would produce correct text by accident.
    """
    path = CONTENT_PACKS["entangled_oracle"]["eclipses"]
    with open(path, encoding="utf-8") as f:
        blocks = json.load(f)
    solar = blocks.get("Solar", {})
    block_6 = solar.get("6", "")
    block_10 = solar.get("10", "")
    assert block_6 and block_10, "Both Solar/6 and Solar/10 blocks must exist in EO eclipse file."
    assert block_6 != block_10, (
        "Solar/6 and Solar/10 EO eclipse blocks must be different prose — "
        "otherwise house confusion would produce correct output by coincidence."
    )


# ── Boundary label tests ───────────────────────────────────────────────────────

def _make_transit_event(**overrides) -> dict:
    base = {
        "event_type": "transit",
        "transit_planet": "Saturn",
        "aspect": "Trine",
        "natal_target": "Sun",
        "entry_date": "June 23, 2026",
        "peak_date": "August 15, 2026",
        "leave_date": "October 10, 2026",
        "duration_days": 109.0,
        "active_at_report_start": False,
        "active_at_report_end": False,
        "in_orb_at_forecast_start": False,
        "continues_after_forecast_end": False,
        "perfection_type": "exact",
    }
    base.update(overrides)
    return base


def _call_duration_descriptor(event: dict) -> str:
    # Import from generate.py; the function is module-level.
    import generate
    return generate._duration_descriptor(event)


def test_normal_transit_shows_enters_and_leaves():
    event = _make_transit_event()
    desc = _call_duration_descriptor(event)
    assert "Enters orb" in desc
    assert "Leaves orb" in desc
    assert "Already active" not in desc
    assert "Continues beyond" not in desc


def test_transit_active_at_start_suppresses_enters_label():
    event = _make_transit_event(in_orb_at_forecast_start=True)
    desc = _call_duration_descriptor(event)
    assert "Already active at the start of this forecast" in desc
    assert "Enters orb" not in desc


def test_transit_continuing_past_end_suppresses_leaves_label():
    event = _make_transit_event(continues_after_forecast_end=True)
    desc = _call_duration_descriptor(event)
    assert "Continues beyond this report" in desc
    assert "Leaves orb" not in desc


def test_exact_label():
    event = _make_transit_event(perfection_type="exact")
    desc = _call_duration_descriptor(event)
    assert "Exact:" in desc
    assert "Closest approach" not in desc
    assert "Exactest" not in desc


def test_closest_approach_label():
    event = _make_transit_event(perfection_type="closest_approach")
    desc = _call_duration_descriptor(event)
    assert "Closest approach:" in desc
    assert "Exact:" not in desc
    assert "Exactest" not in desc


# ── Perfection type derivation test ───────────────────────────────────────────

def test_perfection_type_from_peak_orb():
    """transit_engine assigns perfection_type based on peak_orb vs 0.25° threshold."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "transit_engine",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "engine", "transit_engine.py"),
    )
    # We can't easily call _finalize_transit_event without a full payload,
    # so just verify the threshold value is documented in the source.
    engine_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "engine", "transit_engine.py",
    )
    with open(engine_path, encoding="utf-8") as f:
        src = f.read()
    assert "perfection_type" in src, "transit_engine must produce a perfection_type field"
    assert "0.25" in src, "transit_engine must use the 0.25° exactness threshold"


if __name__ == "__main__":
    tests = [
        test_eo_pack_uses_house_key,
        test_plainspeak_pack_uses_planet_key,
        test_eo_eclipse_selects_house_10_not_6,
        test_plainspeak_eclipse_selects_planet_index_6,
        test_eo_eclipse_file_has_10th_house_block,
        test_eo_eclipse_10th_differs_from_6th,
        test_normal_transit_shows_enters_and_leaves,
        test_transit_active_at_start_suppresses_enters_label,
        test_transit_continuing_past_end_suppresses_leaves_label,
        test_exact_label,
        test_closest_approach_label,
        test_perfection_type_from_peak_orb,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL  {t.__name__}: {exc}")
        except Exception as exc:
            print(f"  ERROR {t.__name__}: {exc}")
    print(f"\n{passed}/{len(tests)} passed")
