"""
tests/test_progression_content_routing.py

Regression coverage for content routing on progression/solar-arc angle
targets. Every content-library JSON for these techniques
(products/year_ahead/blocks/{plainspeak,entangled_oracle}/
progression_blocks.json and solar_arc_blocks.json) keys its natal_target
level on the short form only -- "ASC", "MC" -- with no "Ascendant" or
"Midheaven" entries anywhere. generate.py's THEME_MAP (generate.py,
THEME_MAP["natal_target"]) does the same.

This means the natal_target value the scanners emit is not just a display
label: it is a lookup key into hand-written prose. Deduping the angle
target enumeration in engine/progressions.py and engine/solar_arc.py to
the *long* form would still fix the duplicate-event bug but would
silently route every progressed/directed Ascendant or Midheaven contact
onto generic fallback prose instead of the specific block written for it
-- trading a visible duplication bug for an invisible content-routing
regression. This test exercises the real selection path
(generate._select_year_block against the actual packaged JSON) to catch
that class of mistake directly, rather than only asserting on the
scanner's internal keys.

Run with:
    python -m pytest tests/test_progression_content_routing.py -v
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from config import CONTENT_PACKS
from generate import _select_year_block


class TestProgressionAngleContentRouting(unittest.TestCase):
    """A progressed/directed contact to Ascendant or Midheaven must reach
    its written block, not the pack's generic top-level fallback."""

    def _assert_reaches_written_block(self, pack_name, event_type, target):
        pack_paths = CONTENT_PACKS[pack_name]
        event = {
            "event_type": event_type,
            "transit_planet": "Sun",
            "aspect": "Trine",
            "natal_target": target,
        }
        block = _select_year_block(event, pack_paths)
        self.assertTrue(
            block,
            f"{pack_name}/{event_type}: Sun Trine {target} returned no block at all",
        )
        self.assertFalse(
            block.startswith("[BLOCK NOT FOUND") or block.startswith("[MISSING BLOCK FILE"),
            f"{pack_name}/{event_type}: Sun Trine {target} hit an unresolved block marker: {block[:80]!r}",
        )

    def test_plainspeak_progression_ascendant_reaches_written_block(self):
        self._assert_reaches_written_block("plainspeak", "progression", "ASC")

    def test_plainspeak_progression_midheaven_reaches_written_block(self):
        self._assert_reaches_written_block("plainspeak", "progression", "MC")

    def test_entangled_oracle_progression_ascendant_reaches_written_block(self):
        self._assert_reaches_written_block("entangled_oracle", "progression", "ASC")

    def test_entangled_oracle_progression_midheaven_reaches_written_block(self):
        self._assert_reaches_written_block("entangled_oracle", "progression", "MC")

    def test_plainspeak_solar_arc_ascendant_reaches_written_block(self):
        self._assert_reaches_written_block("plainspeak", "solar_arc", "ASC")

    def test_entangled_oracle_solar_arc_ascendant_reaches_written_block(self):
        self._assert_reaches_written_block("entangled_oracle", "solar_arc", "ASC")

    def test_long_form_target_would_miss_the_written_block(self):
        """Documents *why* the short form matters: this is the exact
        mistake short-form coverage guards against. If this ever starts
        passing, the content libraries have been re-keyed to the long
        form and TestProgressionAngleContentRouting's short-form
        assumption (and the scanners' canonical key choice) should be
        revisited together."""
        pack_paths = CONTENT_PACKS["entangled_oracle"]
        event = {
            "event_type": "progression",
            "transit_planet": "Sun",
            "aspect": "Trine",
            "natal_target": "Ascendant",
        }
        block = _select_year_block(event, pack_paths)
        specific_block = _select_year_block(
            dict(event, natal_target="ASC"), pack_paths
        )
        self.assertNotEqual(
            block, specific_block,
            "content libraries now key on the long form -- the scanners' "
            "canonical angle form should be revisited to match",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
