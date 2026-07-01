"""
tests/test_asteroid_portrait_tier_routing.py

Regression test for the Asteroid Portrait display-tier routing fix.

Verifies that _build_asteroid_portrait_context uses v0.2 EAS routing flags
(suppressed / display_full / subtle_signal) rather than the broken
score >= 2.0 threshold that forced every card to SUBTLE.

Uses mock index results — no chart engine, no formula engine, no I/O.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_eas(*, display_full=False, subtle_signal=False, suppressed=False,
              archetype="Test Archetype", score=0.0):
    """Minimal EAS v0.2 result dict for routing tests."""
    return {
        "score": score,
        "activation_score": score * 10.0,
        "archetype": archetype,
        "driver_body": "TestBody",
        "driver_modality": "fixed",
        "expression": "Test Expression",
        "activation": "Awakening",
        "suppressed": suppressed,
        "subtle_signal": subtle_signal,
        "display_full": display_full,
        "components": {},
    }


def _make_magnetic(score):
    """Minimal legacy MAGNETIC result dict."""
    from selectors.utils import get_score_tier
    return {
        "score": round(score, 4),
        "tier": get_score_tier(score),
        "framing": "PROTAGONIST" if score >= 0.2 else "COMBINED",
        "archetype": "The Protagonist" if score >= 0.65 else "The Scene-Stealer" if score >= 0.35 else "The Magnetic Field",
        "deprecated": True,
        "successor": "NGE",
    }


def _make_ahl(*, fires, tier="PRESENT"):
    return {
        "score": 2.0 if fires else 0.0,
        "fires": fires,
        "tier": tier if fires else "BELOW_THRESHOLD",
        "suppressed": not fires,
        "subtle_signal": False,
        "display_full": fires,
        "components": {},
    }


def _run_context(index_results):
    """
    Calls the routing logic directly from generate._build_asteroid_portrait_context
    with a minimal payload stub so the selector still resolves block files.
    We only care about the tier / key / archetype fields in dimension_sections.
    """
    import generate

    # Build controlled dim_order from keys present in a stable order.
    ordered_keys = [k for k in ["KVQ", "MKI", "RWI", "DFIS", "CATALYST", "MAGNETIC", "AHL"]
                    if k in index_results]

    # The function does a local import so patch the source module.
    from unittest.mock import patch
    with patch("formulas.proprietary_indexes.get_dimension_order", return_value=ordered_keys):
        ctx = generate._build_asteroid_portrait_context(
            variables={},
            index_results=index_results,
            payload={},
        )
    return ctx["dimension_sections"]


class TestTierRouting(unittest.TestCase):

    def _sections_by_key(self, sections):
        return {s["key"]: s for s in sections}

    def test_first_display_full_becomes_dominant(self):
        """One display_full EAS result → DOMINANT."""
        results = {
            "KVQ": _make_eas(display_full=True, score=0.8, archetype="Vindicated Oracle"),
            "DFIS": _make_eas(subtle_signal=True, score=0.05),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertIn("KVQ", by_key)
        self.assertEqual(by_key["KVQ"]["tier"], "DOMINANT")
        self.assertEqual(by_key["KVQ"]["archetype"], "Vindicated Oracle",
                         "Archetype must be shown for DOMINANT section")

    def test_second_display_full_becomes_present(self):
        """Second display_full EAS result → PRESENT."""
        results = {
            "KVQ":  _make_eas(display_full=True, score=0.8),
            "DFIS": _make_eas(display_full=True, score=0.5),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertEqual(by_key["KVQ"]["tier"],  "DOMINANT")
        self.assertEqual(by_key["DFIS"]["tier"], "PRESENT")
        self.assertEqual(by_key["DFIS"]["archetype"], "",
                         "Archetype must be hidden for PRESENT section")

    def test_subtle_signal_becomes_subtle(self):
        """subtle_signal only (display_full=False) → SUBTLE."""
        results = {
            "KVQ": _make_eas(subtle_signal=True, score=0.1),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertIn("KVQ", by_key)
        self.assertEqual(by_key["KVQ"]["tier"], "SUBTLE")

    def test_suppressed_result_is_omitted(self):
        """suppressed=True → dimension is entirely absent from sections."""
        results = {
            "MKI": _make_eas(suppressed=True, score=0.0),
            "KVQ": _make_eas(subtle_signal=True, score=0.1),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertNotIn("MKI", by_key, "Suppressed MKI must not appear in dimension_sections")
        self.assertIn("KVQ", by_key)

    def test_ahl_fires_present_not_dominant(self):
        """Firing AHL → PRESENT display tier; never DOMINANT."""
        results = {
            "KVQ": _make_eas(display_full=True, score=0.8),
            "AHL": _make_ahl(fires=True, tier="PRESENT"),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertIn("AHL", by_key)
        self.assertEqual(by_key["AHL"]["tier"], "PRESENT")
        self.assertNotEqual(by_key["KVQ"]["tier"], "PRESENT",
                            "KVQ should still be DOMINANT; AHL does not consume the slot")

    def test_ahl_not_fires_omitted(self):
        """AHL with fires=False → absent from sections."""
        results = {
            "KVQ": _make_eas(subtle_signal=True, score=0.1),
            "AHL": _make_ahl(fires=False),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertNotIn("AHL", by_key)

    def test_magnetic_nonzero_uses_legacy_tier(self):
        """Nonzero MAGNETIC → rendered with its own tier from get_score_tier."""
        results = {
            "MAGNETIC": _make_magnetic(score=0.70),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertIn("MAGNETIC", by_key)
        self.assertEqual(by_key["MAGNETIC"]["tier"], "DOMINANT",
                         "score=0.70 is above 0.65 DOMINANT threshold")

    def test_magnetic_zero_score_omitted(self):
        """MAGNETIC score == 0 → absent from sections."""
        results = {
            "MAGNETIC": _make_magnetic(score=0.0),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertNotIn("MAGNETIC", by_key)

    def test_old_score_threshold_never_promotes(self):
        """
        The old bug: score >= 2.0 was used to determine DOMINANT/PRESENT.
        EAS v0.2 scores are 0.0–1.0 so that threshold is unreachable.
        Verify display_full=False, subtle_signal=True never becomes DOMINANT.
        """
        results = {
            "KVQ": _make_eas(subtle_signal=True, display_full=False, score=0.99),
        }
        sections = _run_context(results)
        by_key = self._sections_by_key(sections)
        self.assertIn("KVQ", by_key)
        self.assertNotEqual(by_key["KVQ"]["tier"], "DOMINANT",
                            "subtle_signal result must never become DOMINANT regardless of score")
        self.assertNotEqual(by_key["KVQ"]["tier"], "PRESENT")
        self.assertEqual(by_key["KVQ"]["tier"], "SUBTLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
