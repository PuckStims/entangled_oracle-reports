import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(__file__))

import generate
from formulas.report_surface import build_layered_report_bundle
from scripts.generate_review_pack import REVIEW_PACK_REPORTS, generate_review_pack
from selectors.variable_resolver import resolve_all
from tests.phase2_fixtures import (
    PHASE8_REQUIRED_SCENARIOS,
    build_phase8_fixture,
    get_phase8_fixture_library,
)


class Phase8QualityAssuranceTests(unittest.TestCase):
    def test_fixture_library_covers_required_phase8_scenarios(self):
        library = get_phase8_fixture_library()
        covered = set()
        for fixture in library.values():
            covered.update(fixture["scenarios"])

        self.assertFalse(
            PHASE8_REQUIRED_SCENARIOS - covered,
            f"Missing scenario coverage: {sorted(PHASE8_REQUIRED_SCENARIOS - covered)}",
        )

    def test_review_pack_includes_required_report_types(self):
        labels = {item["label"] for item in REVIEW_PACK_REPORTS}
        self.assertEqual(
            labels,
            {
                "Year Ahead",
                "Personal Forecast",
                "Soul Ecosystem",
                "Horoscope",
                "Simple DOB-only Horoscope",
                "Asteroid Portrait",
            },
        )

    def test_report_context_trace_keeps_diagnostics_separate_and_json_safe(self):
        fixture = build_phase8_fixture("exact_day_angular_ruler")
        payload = fixture["payload"]
        bundle = build_layered_report_bundle(payload, "year_ahead", index_results={})
        variables = resolve_all(
            payload,
            {},
            standard_report_bundle=bundle,
            querent_name=fixture["birth_data"]["name"],
            current_location=fixture["birth_data"]["location"],
            report_start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            report_end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        )

        with patch.object(generate, "_build_year_ahead_context", return_value={"headline": "stub"}):
            context = generate.build_report_context(
                "year_ahead",
                variables,
                {},
                payload,
                report_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
                report_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
                standard_report_bundle=bundle,
            )

        trace = context["report_surface_trace"]
        self.assertIn("selected_block_files", trace)
        self.assertIn("fallback_use", trace)
        self.assertIn("template_fields_populated", trace)
        self.assertEqual(trace["methodology_marker"]["zodiac"], "Tropical")
        self.assertNotIn("eo_proprietary", context["standard_result_bundle"])
        json.dumps(trace)

    def test_simple_fixture_keeps_unknown_birth_time_explicit(self):
        fixture = build_phase8_fixture("simple_dob_only")
        bundle = build_layered_report_bundle(fixture["payload"], "horoscope", index_results={})
        self.assertEqual(bundle["standard_result_bundle"]["chart_ruler"]["routing_state"], "suppressed")
        self.assertEqual(bundle["trace"]["birth_time_confidence_state"], "unknown")

    def test_review_pack_generator_smoke_writes_manifest_and_checklist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            smoke_spec = [item for item in REVIEW_PACK_REPORTS if item["label"] == "Simple DOB-only Horoscope"]
            with patch("scripts.generate_review_pack.REVIEW_PACK_REPORTS", smoke_spec):
                manifest = generate_review_pack(output_dir=tmpdir)

            self.assertTrue(os.path.exists(manifest["manifest_path"]))
            self.assertTrue(os.path.exists(manifest["checklist_path"]))
            self.assertEqual(len(manifest["reports"]), 1)
            self.assertTrue(os.path.exists(manifest["reports"][0]["html_path"]))


if __name__ == "__main__":
    unittest.main()
