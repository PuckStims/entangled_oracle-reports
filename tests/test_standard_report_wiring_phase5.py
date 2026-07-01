import json
import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.dirname(__file__))

import generate
from formulas.report_surface import build_layered_report_bundle
from selectors.variable_resolver import resolve_all
from tests.phase2_fixtures import build_payload, make_body


class StandardReportWiringPhase5Tests(unittest.TestCase):
    def _payload(self, simple_mode: bool = False):
        payload = build_payload(
            asc_sign="Leo",
            simple_mode=simple_mode,
            placements={
                "Sun": 5.0,
                "Moon": 12.0,
                "Mercury": 8.0,
                "Venus": 42.0,
                "Mars": 98.0,
                "Jupiter": 122.0,
                "Saturn": 275.0,
                "Uranus": 281.0,
                "Neptune": 350.0,
                "Pluto": 256.0,
                "Chiron": 111.0,
            },
            custom_asteroids={
                "Kassandra": make_body(90.0, 120.0, speed=0.04),
            },
        )
        payload["standard_planets"]["Lilith_BML"] = make_body(210.0, 120.0, speed=0.0)
        return payload

    def _index_results(self):
        return {
            "KVQ": {
                "score": 0.82,
                "activation_score": 8.2,
                "raw_score": 8.2,
                "tier": "PRESENT",
                "archetype": "Vindicated Oracle",
                "expression": "KVQ expression",
                "driver_body": "Kassandra",
                "driver_modality": "cardinal",
                "activation": "Embodied",
                "components": {"kass_angle": 1.2},
            }
        }

    def test_bundle_exposes_core_categories_and_routing_states(self):
        bundle = build_layered_report_bundle(
            self._payload(),
            "year_ahead",
            index_results=self._index_results(),
        )

        standard = bundle["standard_result_bundle"]
        self.assertIn("chart_ruler", standard)
        self.assertIn("forecast_natal_priority", standard)
        self.assertIn("established_niche_results", standard)
        self.assertEqual(
            standard["forecast_natal_priority"]["routing_state"],
            "forecast_cross_reference",
        )
        self.assertEqual(
            standard["natal_convergence"]["routing_state"],
            "forecast_cross_reference",
        )
        self.assertIn(
            standard["named_configurations"]["routing_state"],
            {
                "supporting_context",
                "technical_appendix",
                "suppressed",
            },
        )

    def test_core_and_niche_layers_do_not_require_eo_indexes(self):
        horoscope = build_layered_report_bundle(self._payload(), "horoscope", index_results=None)
        asteroid = build_layered_report_bundle(self._payload(), "asteroid_portrait", index_results=None)

        self.assertTrue(horoscope["core_standard"])
        self.assertFalse(horoscope["eo_proprietary"])
        self.assertTrue(asteroid["established_niche"])
        self.assertFalse(asteroid["eo_proprietary"])

    def test_resolver_flattened_values_match_structured_bundle(self):
        bundle = build_layered_report_bundle(
            self._payload(),
            "soul_ecosystem",
            index_results=self._index_results(),
        )
        variables = resolve_all(
            self._payload(),
            self._index_results(),
            standard_report_bundle=bundle,
            querent_name="Phase 5",
            current_location="Chicago, IL",
        )

        self.assertEqual(
            variables["chart_ruler_body"],
            bundle["standard_result_bundle"]["chart_ruler"]["traceable_source_data"]["primary_ruler"],
        )
        self.assertEqual(
            variables["natal_convergence_primary_theme"],
            bundle["standard_result_bundle"]["natal_convergence"]["traceable_source_data"]["central_life_domains"][0]["label"],
        )
        self.assertTrue(isinstance(variables["planet_prominence_top_bodies"], list))
        self.assertTrue(variables["forecast_priority_luminary_active"])
        json.dumps(variables["standard_result_bundle"])

    def test_missing_standard_module_does_not_crash_bundle(self):
        with patch("formulas.report_surface.evaluate_chart_ruler", side_effect=RuntimeError("boom")):
            bundle = build_layered_report_bundle(self._payload(), "horoscope", index_results=None)

        chart_ruler = bundle["standard_result_bundle"]["chart_ruler"]
        self.assertEqual(chart_ruler["routing_state"], "internal_trace_only")
        self.assertTrue(any("module_error" in item for item in chart_ruler["limitations"]))

    def test_simple_mode_suppresses_exact_time_dependent_standard_outputs(self):
        bundle = build_layered_report_bundle(self._payload(simple_mode=True), "horoscope", index_results=None)
        variables = resolve_all(
            self._payload(simple_mode=True),
            {},
            standard_report_bundle=bundle,
            querent_name="Simple Mode",
            current_location="Chicago, IL",
        )

        self.assertEqual(bundle["standard_result_bundle"]["chart_ruler"]["routing_state"], "suppressed")
        self.assertEqual(bundle["standard_result_bundle"]["house_emphasis"]["routing_state"], "suppressed")
        self.assertEqual(variables["chart_ruler_body"], "")

    def test_build_report_context_adds_bundle_and_trace_without_template_rewrite(self):
        bundle = build_layered_report_bundle(
            self._payload(),
            "horoscope",
            index_results=self._index_results(),
        )
        variables = resolve_all(
            self._payload(),
            self._index_results(),
            standard_report_bundle=bundle,
            querent_name="Context Test",
            current_location="Chicago, IL",
            report_start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
            report_end_date=datetime(2026, 12, 31, tzinfo=timezone.utc),
        )

        with patch.object(generate, "_build_horoscope_context", return_value={"headline": "stub"}):
            context = generate.build_report_context(
                "horoscope",
                variables,
                self._index_results(),
                self._payload(),
                report_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
                report_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
                standard_report_bundle=bundle,
            )

        self.assertIn("standard_report_bundle", context)
        self.assertIn("report_surface_trace", context)
        self.assertIn("standard_report_context_view", context)
        self.assertEqual(context["headline"], "stub")
        self.assertIn("selected_block_files", context["report_surface_trace"])
        self.assertIn("template_fields_populated", context["report_surface_trace"])

    def test_trace_is_json_safe_and_carries_required_fields(self):
        bundle = build_layered_report_bundle(
            self._payload(),
            "personal_forecast",
            index_results=self._index_results(),
        )
        trace = bundle["trace"]
        self.assertIn("selected_routing_decisions", trace)
        self.assertIn("suppressed_candidates", trace)
        self.assertIn("requested_block_keys", trace)
        self.assertIn("fallback_use", trace)
        json.dumps(trace)


if __name__ == "__main__":
    unittest.main()
