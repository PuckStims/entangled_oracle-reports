"""
tests/test_progression_solar_arc_angle_dedup.py

Regression coverage for a duplicate-event bug in the progression and
solar-arc scanners: their _natal_targets() helpers used to enumerate both
the short form ("ASC", "MC", "DSC") and the long form ("Ascendant",
"Midheaven", "Descendant") of each angle as separate dict keys. Both keys
resolved to the same longitude, so the contact scan in
scan_progression_events()/scan_solar_arc_events() emitted the same aspect
twice under two different natal_target labels -- e.g. "Progressed Mars
Trine natal DSC" and "Progressed Mars Trine natal Descendant" appearing
as two distinct report entries for what is astrologically one event.

The fix keeps the short form ("ASC"/"MC"/"DSC") as the single canonical
key, not the long form. That matters beyond naming: every progression and
solar-arc content-library JSON (products/year_ahead/blocks/.../
progression_blocks.json, solar_arc_blocks.json, EO_Standard_*_Blocks.json)
and generate.py's THEME_MAP key their natal_target lookups on "ASC"/"MC"
only -- there are no "Ascendant"/"Midheaven" entries anywhere in those
tables. Deduping to the long form would still remove the duplicate event,
but would silently route every angle contact to generic fallback prose
instead of the block actually written for it. TestNatalTargetsUsesShortForm
guards specifically against re-introducing that mistake.

This file also covers a second, related bug that keeping the short form
uncovered: each scanner's main loop is supposed to skip a progressed/
directed point against its own natal position (e.g. progressed Sun vs
natal Sun), but the skip check compared source_name and target_name as
raw strings. ANGLE_SOURCES lists the long form ("Ascendant", "Midheaven")
while _natal_targets' angle entries use the short form ("ASC", "MC"), so
"Ascendant" was never seen as equal to "ASC" even though they're the same
point -- letting a spurious "Progressed Ascendant [aspect] natal ASC"
event through as the progressed angle drifted from its own starting
position. TestScannersExcludeAngleSelfAspects covers this.

Run with:
    python -m pytest tests/test_progression_solar_arc_angle_dedup.py -v
"""

import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine import progressions, solar_arc


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _payload_with_angles():
    """A minimal payload with all four cardinal angles and one planet
    placed so a progressed/directed Mars-style body will pass through a
    Trine to the Descendant within the scan window."""
    return {
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "birth_location": "Peoria, Illinois, USA",
        "latitude": 40.6936,
        "longitude": -89.589,
        "timezone": "America/Chicago",
        "julian_day": 2447893.25,
        "user_profile": {
            "birth_time_state": "exact",
            "house_system": "Whole Sign",
            "zodiac": "Tropical",
            "methodology": {"zodiac": "tropical", "house_system": "whole_sign"},
        },
        "angles": {
            "Ascendant": {"longitude": 10.0, "sign": "Aries", "house": 1},
            "Midheaven": {"longitude": 280.0, "sign": "Capricorn", "house": 10},
            "Descendant": {"longitude": 190.0, "sign": "Libra", "house": 7},
            "Imum_Coeli": {"longitude": 100.0, "sign": "Cancer", "house": 4},
        },
        "houses": {},
        "standard_planets": {
            "Sun": {"longitude": 0.0, "sign": "Aries", "house": 1},
            "Moon": {"longitude": 90.0, "sign": "Cancer", "house": 4},
            "Mercury": {"longitude": 15.0, "sign": "Aries", "house": 1},
            "Venus": {"longitude": 45.0, "sign": "Taurus", "house": 2},
            "Mars": {"longitude": 120.0, "sign": "Leo", "house": 5},
        },
        "custom_asteroids": {},
        "aspects": [],
    }


class TestNatalTargetsHaveNoAngleAliasDuplicates(unittest.TestCase):
    """Unit-level: each angle must contribute exactly one target entry."""

    def _assert_no_duplicate_longitudes(self, targets):
        angle_entries = {
            name: data["longitude"]
            for name, data in targets.items()
            if data.get("kind") == "angle"
        }
        # No long-form aliases should survive into the target map alongside
        # the canonical short form.
        for alias in ("Ascendant", "Midheaven", "Descendant", "Imum_Coeli", "Imum Coeli"):
            self.assertNotIn(
                alias, angle_entries,
                f"long-form angle alias {alias!r} leaked into _natal_targets()",
            )
        # No two distinct keys should point at the same longitude either
        # (guards against a future alias being reintroduced under a new name).
        seen_longitudes = {}
        for name, longitude in angle_entries.items():
            self.assertNotIn(
                longitude, seen_longitudes,
                f"{name!r} duplicates the longitude already claimed by "
                f"{seen_longitudes.get(longitude)!r}",
            )
            seen_longitudes[longitude] = name

    def test_progressions_natal_targets_has_no_angle_duplicates(self):
        targets = progressions._natal_targets(_payload_with_angles())
        self._assert_no_duplicate_longitudes(targets)

    def test_solar_arc_natal_targets_has_no_angle_duplicates(self):
        targets = solar_arc._natal_targets(_payload_with_angles())
        self._assert_no_duplicate_longitudes(targets)


class TestNatalTargetsUsesShortForm(unittest.TestCase):
    """The canonical angle key must be the short form ("ASC"/"MC"/"DSC"),
    matching the only key convention the content libraries and
    generate.py's THEME_MAP actually use. Switching to the long form
    would still dedupe the event, but would silently move every angle
    contact onto generic fallback prose."""

    def test_progressions_targets_use_short_form_keys(self):
        targets = progressions._natal_targets(_payload_with_angles())
        self.assertIn("ASC", targets)
        self.assertIn("MC", targets)
        self.assertIn("DSC", targets)

    def test_solar_arc_targets_use_short_form_keys(self):
        targets = solar_arc._natal_targets(_payload_with_angles())
        self.assertIn("ASC", targets)
        self.assertIn("MC", targets)
        self.assertIn("DSC", targets)


class TestScannersEmitOneEventPerContact(unittest.TestCase):
    """Integration-level: the full scan must not emit the same aspect
    twice under different natal_target labels for the same angle.

    Signature is (moving body, aspect, peak date) deliberately without
    natal_target: that field is exactly what the alias-duplication bug
    varied ("DSC" vs "Descendant") while everything else about the two
    emitted events stayed identical.
    """

    def _assert_no_duplicate_angle_contacts(self, events):
        seen = {}
        for event in events:
            if event.get("natal_target") not in {"ASC", "MC", "DSC"}:
                continue
            signature = (
                event.get("transit_planet"),
                event.get("aspect"),
                event.get("peak_date"),
            )
            self.assertNotIn(
                signature, seen,
                f"duplicate angle contact emitted for {signature}: "
                f"natal_target={event.get('natal_target')!r} duplicates the "
                f"event already recorded with natal_target="
                f"{seen.get(signature)!r}",
            )
            seen[signature] = event.get("natal_target")

    def test_progression_scan_has_no_duplicate_angle_contacts(self):
        payload = _payload_with_angles()
        events = progressions.scan_progression_events(
            payload, _dt("2026-01-01T00:00:00"), _dt("2036-01-01T00:00:00")
        )
        self._assert_no_duplicate_angle_contacts(events)

    def test_solar_arc_scan_has_no_duplicate_angle_contacts(self):
        payload = _payload_with_angles()
        events = solar_arc.scan_solar_arc_events(
            payload, _dt("2026-01-01T00:00:00"), _dt("2036-01-01T00:00:00")
        )
        self._assert_no_duplicate_angle_contacts(events)


class TestScannersExcludeAngleSelfAspects(unittest.TestCase):
    """A progressed/directed Ascendant must never be reported aspecting
    natal ASC (nor Midheaven vs natal MC) -- that is the same point
    compared to itself, which the scanners are supposed to skip.

    ANGLE_SOURCES lists the long form ("Ascendant", "Midheaven");
    _natal_targets' angle entries use the canonical short form ("ASC",
    "MC", "DSC") -- see TestNatalTargetsUsesShortForm above for why. The
    self-exclusion check in each scanner's main loop used to compare
    those raw strings directly, so "Ascendant" (source) was never seen
    as equal to "ASC" (target) even though they're the same natal point,
    and a spurious "Progressed Ascendant Trine natal ASC"-style event
    leaked through as the progressed angle drifted from its own natal
    position over the scan window. Comparing normalized forms
    (normalize_angle_name) fixes this without touching the display
    strings, content-routing keys, or ANGLE_SOURCES itself.

    A wide real-ephemeris scan window doesn't reliably hit this: whether
    a progressed angle happens to drift into aspect with its own natal
    position within a given window depends on chart-specific geometry
    (confirmed empirically -- it fires 7 times on one real chart within
    a single year, zero times on this file's synthetic fixture across a
    10-year window). So this test forces the condition deterministically
    instead of hoping a real search finds it: every relevant longitude is
    pinned to 0.0 and the progressed/directed longitude lookup is patched
    to always return 0.0 too, so every source/target pair sits at an
    exact 0.0-orb Conjunction. If the self-exclusion check works, the
    Ascendant/ASC and Midheaven/MC pairs are the only ones missing from
    an otherwise-full grid of Conjunction events.
    """

    SELF_PAIRS = {("Ascendant", "ASC"), ("Midheaven", "MC")}

    def _zeroed_payload(self):
        payload = _payload_with_angles()
        for angle in payload["angles"].values():
            angle["longitude"] = 0.0
        for body in payload["standard_planets"].values():
            body["longitude"] = 0.0
        return payload

    def _assert_no_angle_self_aspects(self, events, *, expect_some_conjunctions):
        conjunctions = [e for e in events if e.get("aspect") == "Conjunction"]
        if expect_some_conjunctions:
            self.assertTrue(
                conjunctions,
                "test fixture didn't force any Conjunction events at all -- "
                "the mocked longitude lookup isn't wired the way this test "
                "assumes, so it can't actually exercise the exclusion check",
            )
        offenders = [
            e for e in conjunctions
            if (e.get("transit_planet"), e.get("natal_target")) in self.SELF_PAIRS
        ]
        self.assertEqual(
            offenders, [],
            f"progressed/directed angle reported aspecting its own natal "
            f"position: {[(e.get('transit_planet'), e.get('aspect'), e.get('natal_target')) for e in offenders]}",
        )

    def test_progression_scan_excludes_angle_self_aspects(self):
        payload = self._zeroed_payload()
        with patch("engine.progressions.progressed_longitude", return_value=0.0), \
             patch("engine.progressions._find_contact_exact", return_value=_dt("2026-01-01T00:00:00")):
            events = progressions.scan_progression_events(
                payload, _dt("2026-01-01T00:00:00"), _dt("2026-01-08T00:00:00")
            )
        self._assert_no_angle_self_aspects(events, expect_some_conjunctions=True)

    def test_solar_arc_scan_excludes_angle_self_aspects(self):
        payload = self._zeroed_payload()
        with patch("engine.solar_arc.directed_longitude", return_value=0.0), \
             patch("engine.solar_arc._find_contact_exact", return_value=_dt("2026-01-01T00:00:00")):
            events = solar_arc.scan_solar_arc_events(
                payload, _dt("2026-01-01T00:00:00"), _dt("2026-01-08T00:00:00")
            )
        self._assert_no_angle_self_aspects(events, expect_some_conjunctions=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
