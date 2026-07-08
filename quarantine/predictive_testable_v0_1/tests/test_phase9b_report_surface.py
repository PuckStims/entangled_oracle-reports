import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from generate import _build_predictive_report_surface


class TestPhase9bReportSurface(unittest.TestCase):
    def test_year_ahead_surfaces_chapters_without_candidates(self):
        surface = _build_predictive_report_surface(_sidecar(), "year_ahead")

        self.assertTrue(surface["enabled"])
        self.assertEqual(surface["chapter_count"], 1)
        self.assertEqual(surface["candidate_count"], 0)
        self.assertEqual(surface["candidates"], [])
        chapter = surface["chapters"][0]
        self.assertIn("Predictive / experimental", surface["label"])
        self.assertIn("research layer", surface["framing"])
        self.assertEqual(chapter["component_scores"]["coherence"], 0.75)
        self.assertEqual(chapter["component_scores"]["counterforce"], 0.2)

    def test_personal_forecast_surfaces_candidates_with_component_scores(self):
        surface = _build_predictive_report_surface(_sidecar(), "personal_forecast")

        self.assertTrue(surface["enabled"])
        self.assertEqual(surface["chapter_count"], 1)
        self.assertEqual(surface["candidate_count"], 1)
        candidate = surface["candidates"][0]
        # summary now routes through selectors.block_selector.select_block()
        # keyed on (candidate_domain[0], independent_method_families[0]) against
        # products/personal_forecast/blocks/shared/predictive_candidates.json.
        # Content is filled in now (not the scaffold's [TODO] placeholder), so
        # assert real-content behavior rather than pinning to specific prose:
        # non-empty, not an unfilled/missing-block marker, and not the
        # generic top-level fallback string (confirms the (identity,
        # transit_family) leaf itself resolved, not just some fallback).
        summary = candidate["summary"]
        self.assertTrue(summary)
        self.assertFalse(summary.startswith("[TODO"))
        self.assertFalse(summary.startswith("[BLOCK NOT FOUND"))
        self.assertFalse(summary.startswith("[MISSING BLOCK FILE"))
        from selectors.block_selector import select_block
        top_level_fallback = select_block("personal_forecast", "predictive_candidates", "fallback")
        self.assertNotEqual(summary, top_level_fallback)
        self.assertEqual(candidate["component_scores"]["topic_coherence"], 0.8)
        self.assertEqual(candidate["component_scores"]["method_family_diversity"], 0.67)


def _sidecar():
    return {
        "report_run": {"report_run_id": "run_phase9b_synthetic"},
        "chapters": [
            {
                "chapter_id": "chap_synthetic_phase9b",
                "start_at": "2026-01-01T00:00:00Z",
                "end_at": "2026-03-31T23:59:59Z",
                "chapter_kind": "solar_arc_chapter",
                "active_long_clocks": ["SOLAR_ARC"],
                "domain_keys": ["identity"],
                "topic_keys": ["threshold_event"],
                "coherence": 0.75,
                "counterforce": 0.2,
                "complexity": 0.4,
                "confidence": 0.85,
                "chapter_summary_score": 0.7,
                "contributing_signal_ids": ["sig_chapter"],
                "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
            }
        ],
        "candidates": [
            {
                "candidate_id": "cand_synthetic_phase9b",
                "start_at": "2026-02-10T00:00:00Z",
                "peak_at": "2026-02-11T00:00:00Z",
                "end_at": "2026-02-12T23:59:59Z",
                "candidate_domain": ["identity"],
                "candidate_topic_keys": ["threshold_event"],
                "independent_method_families": ["transit_family", "solar_arc_family"],
                "convergence_score": 0.72,
                "counterforce": 0.1,
                "complexity": 0.3,
                "confidence": 0.8,
                "component_scores": {
                    "topic_coherence": 0.8,
                    "method_family_diversity": 0.67,
                },
                "birth_time_dependency": "none",
                "candidate_status": "pre_registered",
                "pre_registered_at": "2026-01-01T00:00:00Z",
                "report_surface_visibility": ["internal_rd"],
            }
        ],
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
