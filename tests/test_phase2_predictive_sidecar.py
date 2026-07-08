import json
import os
import sys
import tempfile
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import generate
from engine.predictive_sidecar import build_predictive_sidecar, write_predictive_sidecar_for_report


class TestPredictiveSidecarBuilder(unittest.TestCase):
    def test_sidecar_contains_phase2_required_top_level_sections(self):
        sidecar = build_predictive_sidecar(
            report_type="personal_forecast",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=_predictive_results(),
            report_start=_dt("2026-01-01"),
            report_end=_dt("2026-04-01"),
            engine_command="generate.py personal_forecast",
        )

        for key in (
            "sidecar_version",
            "report_run",
            "natal_snapshot",
            "environment",
            "policy_versions",
            "raw_events",
            "predictive_signals",
            "daily_series",
            "rejected_candidates",
            "detector_thresholds",
            "provenance",
        ):
            self.assertIn(key, sidecar)

        self.assertEqual(sidecar["sidecar_schema_version"], "phase0.1.1")
        self.assertEqual(sidecar["report_run"]["report_type"], "personal_forecast")
        self.assertEqual(sidecar["policy_versions"]["predictive_object_schemas"], "phase0.1.1")
        self.assertEqual(sidecar["rejected_candidates"], [])

    def test_forecast_event_and_signal_are_linked(self):
        sidecar = build_predictive_sidecar(
            report_type="year_ahead",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=_predictive_results(),
            report_start=_dt("2026-01-01"),
            report_end=_dt("2027-01-01"),
        )

        raw_event = sidecar["raw_events"][0]
        signal = sidecar["predictive_signals"][0]

        self.assertEqual(raw_event["schema_version"], "phase0.1.0")
        self.assertEqual(signal["schema_version"], "phase0.1.0")
        self.assertTrue(raw_event["event_id"].startswith("fe_"))
        self.assertEqual(raw_event["method_family"], "TRANSIT")
        self.assertEqual(raw_event["method_variant"], "ASPECT")
        self.assertEqual(raw_event["source_body"], "Saturn")
        self.assertEqual(raw_event["target_body"], "Moon")
        self.assertEqual(signal["source_event_ids"], [raw_event["event_id"]])
        self.assertEqual(signal["signal_role"], "chapter_evidence")

    def test_daily_series_records_signal_and_event_contributors(self):
        sidecar = build_predictive_sidecar(
            report_type="year_ahead",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=_predictive_results(),
            report_start=_dt("2026-01-01"),
            report_end=_dt("2026-01-04"),
        )

        active_day = next(row for row in sidecar["daily_series"] if row["date"] == "2026-01-02")

        self.assertEqual(active_day["contributing_signal_ids"], ["sig_test_0001"])
        self.assertEqual(active_day["contributing_event_ids"], [sidecar["raw_events"][0]["event_id"]])
        self.assertEqual(active_day["structural_contributors"][0]["source_body"], "Saturn")
        self.assertEqual(active_day["trigger_contributors"], [])

    def test_writer_creates_eo_predictive_json_next_to_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sample.html")
            sidecar_path = write_predictive_sidecar_for_report(
                output_path=output_path,
                report_type="year_ahead",
                birth_data=_birth_data(),
                payload=_payload(),
                predictive_results=_predictive_results(),
                report_start=_dt("2026-01-01"),
                report_end=_dt("2027-01-01"),
            )

            self.assertTrue(sidecar_path.endswith(".eo_predictive.json"))
            self.assertTrue(os.path.exists(sidecar_path))
            with open(sidecar_path, "r", encoding="utf-8") as handle:
                saved = json.load(handle)
            self.assertEqual(saved["sidecar_schema_version"], "phase0.1.1")

    def test_unknown_eclipse_label_does_not_count_as_asteroid(self):
        sidecar = build_predictive_sidecar(
            report_type="personal_forecast",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=_predictive_results_with_signal(
                signal_id="sig_eclipse_0001",
                method_family="LUNATION",
                event_kind="ECLIPSE",
                independence_group="lunation_family",
                activation_route="lunation",
                source_event_type="eclipse",
                source_body="Solar",
                target_body="Sun",
                aspect="Conjunction",
            ),
            report_start=_dt("2026-01-01"),
            report_end=_dt("2026-04-01"),
        )

        raw_event = sidecar["raw_events"][0]
        signal = sidecar["predictive_signals"][0]

        self.assertEqual(raw_event["source_kind"], "unknown")
        self.assertNotEqual(raw_event["source_kind"], "asteroid")
        self.assertEqual(raw_event["asteroid_participants"], [])
        self.assertEqual(signal["asteroid_participants"], [])
        self.assertEqual(raw_event["strength_components"]["asteroid_specificity"], 0.0)
        self.assertEqual(sidecar["asteroid_diagnostics"]["asteroid_events_count"], 0)

    def test_calculated_lilith_bml_does_not_count_as_custom_asteroid(self):
        payload = _payload()
        payload["standard_planets"]["Lilith_BML"] = {"longitude": 42.0, "sign": "Taurus", "house": 2}
        payload["custom_asteroids"]["Lilith_Asteroid"] = {"longitude": 43.0, "sign": "Taurus", "house": 2}

        sidecar = build_predictive_sidecar(
            report_type="predictive_sandbox",
            birth_data=_birth_data(),
            payload=payload,
            predictive_results=_predictive_results_with_signal(
                signal_id="sig_lilith_0001",
                source_body="Lilith_BML",
                target_body="ASC",
            ),
            report_start=_dt("2026-01-01"),
            report_end=_dt("2026-04-01"),
        )

        raw_event = sidecar["raw_events"][0]

        self.assertEqual(raw_event["source_kind"], "calculated_point")
        self.assertEqual(raw_event["target_kind"], "angle")
        self.assertEqual(raw_event["asteroid_participants"], [])
        self.assertEqual(raw_event["strength_components"]["asteroid_specificity"], 0.0)
        self.assertEqual(sidecar["asteroid_diagnostics"]["asteroid_events_count"], 0)

    def test_real_custom_asteroid_key_controls_asteroid_classification(self):
        sidecar = build_predictive_sidecar(
            report_type="year_ahead",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=_predictive_results_with_signal(
                signal_id="sig_kassandra_0001",
                source_body="Kassandra",
                target_body="Moon",
            ),
            report_start=_dt("2026-01-01"),
            report_end=_dt("2027-01-01"),
        )

        raw_event = sidecar["raw_events"][0]
        signal = sidecar["predictive_signals"][0]

        self.assertEqual(raw_event["source_kind"], "asteroid")
        self.assertEqual(raw_event["target_kind"], "luminary")
        self.assertEqual(raw_event["asteroid_participants"], ["Kassandra"])
        self.assertEqual(signal["asteroid_participants"], ["Kassandra"])
        self.assertEqual(raw_event["strength_components"]["asteroid_specificity"], 1.0)
        self.assertEqual(
            raw_event["report_surface_visibility"],
            ["internal_rd", "predictive_sandbox", "soul_ecosystem"],
        )
        self.assertEqual(sidecar["asteroid_diagnostics"]["asteroid_events_count"], 1)


class TestGenerateReportSidecarIntegration(unittest.TestCase):
    def test_predictive_report_writes_predictive_sidecar(self):
        proprietary_indexes = types.ModuleType("formulas.proprietary_indexes")
        proprietary_indexes.compute_all_indexes = lambda payload: {}

        report_surface = types.ModuleType("formulas.report_surface")
        report_surface.build_layered_report_bundle = lambda *args, **kwargs: {
            "standard_result_bundle": {},
            "trace": {},
        }
        report_surface.build_report_bundle_context_view = lambda *args, **kwargs: {}

        variable_resolver = types.ModuleType("selectors.variable_resolver")
        variable_resolver.resolve_all = lambda **kwargs: {
            "palette": "vibrant",
            "simple_mode": True,
            "predictive_results": {},
        }

        predictive_engine = types.ModuleType("engine.predictive_engine")
        predictive_engine.compute_predictive_windows = lambda **kwargs: _predictive_results()

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(
                sys.modules,
                {
                    "formulas.proprietary_indexes": proprietary_indexes,
                    "formulas.report_surface": report_surface,
                    "selectors.variable_resolver": variable_resolver,
                    "engine.predictive_engine": predictive_engine,
                },
            ), patch.object(generate, "get_payload", return_value=_payload()), \
                patch.object(generate, "build_report_context", return_value={"headline": "stub"}), \
                patch.object(generate, "render_template", return_value="<html>stub</html>"):
                output_path = generate.generate_report(
                    report_type="personal_forecast",
                    birth_data={**_birth_data(), "report_date": "2026-01-01"},
                    output_filename="sidecar_integration.html",
                    output_dir=tmpdir,
                )

            self.assertTrue(os.path.exists(output_path))
            self.assertTrue(os.path.exists(output_path.replace(".html", ".manifest.json")))
            sidecar_path = output_path.replace(".html", ".eo_predictive.json")
            self.assertTrue(os.path.exists(sidecar_path))
            with open(sidecar_path, "r", encoding="utf-8") as handle:
                sidecar = json.load(handle)
            self.assertEqual(sidecar["report_run"]["report_type"], "personal_forecast")
            self.assertEqual(len(sidecar["raw_events"]), 1)


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _birth_data():
    return {
        "name": "Phase Two",
        "date": "1990-01-01",
        "time": "12:00",
        "location": "Peoria, Illinois, USA",
        "palette": "vibrant",
    }


def _payload():
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
            "methodology": {
                "zodiac": "tropical",
                "house_system": "whole_sign",
            },
        },
        "angles": {
            "Ascendant": {"longitude": 10.0, "sign": "Aries"},
            "Midheaven": {"longitude": 270.0, "sign": "Capricorn"},
        },
        "houses": {},
        "standard_planets": {
            "Sun": {"longitude": 280.0, "sign": "Capricorn", "house": 10},
            "Moon": {"longitude": 40.0, "sign": "Taurus", "house": 2},
            "Saturn": {"longitude": 280.0, "sign": "Capricorn", "house": 10},
        },
        "custom_asteroids": {
            "Kassandra": {"longitude": 41.0, "sign": "Taurus", "house": 2},
        },
        "aspects": [],
    }


def _predictive_results():
    return {
        "formula_version": "predictive_v0.3.1",
        "signals": [
            {
                "signal_id": "sig_test_0001",
                "method_family": "TRANSIT",
                "event_kind": "ASPECT",
                "independence_group": "transit_family",
                "activation_route": "transit_to_body",
                "source_event_type": "transit",
                "source_body": "Saturn",
                "target_body": "Moon",
                "aspect": "Trine",
                "orb": 0.5,
                "allowed_orb": 3.0,
                "exactness": 0.83333,
                "event_weight": 0.85,
                "target_relevance": 0.9,
                "trigger_strength": 0.6375,
                "signal_strength": 0.7,
                "structural_importance": 0.2,
                "theme_convergence": 0.1,
                "start_date": "2026-01-01",
                "peak_date": "2026-01-02",
                "end_date": "2026-01-03",
                "operation_profile": {"stabilize": 0.8, "activate": 0.2},
                "operation_basis": {"source": {"Saturn": 0.8}},
                "dominant_operation": "stabilize",
                "epistemic_confidence": 0.78,
                "confidence_components": {"exactness_support": 0.8},
                "confidence_state": "moderate",
                "angle_eligibility": True,
            }
        ],
        "daily_series": [
            {
                "date": "2026-01-01",
                "raw_score": 0.7,
                "smooth_score": 0.7,
                "baseline_score": 0.3,
                "residual_score": 0.4,
                "structural_raw": 0.7,
                "trigger_raw": 0.0,
            },
            {
                "date": "2026-01-02",
                "raw_score": 0.7,
                "smooth_score": 0.7,
                "baseline_score": 0.3,
                "residual_score": 0.4,
                "structural_raw": 0.7,
                "trigger_raw": 0.0,
            },
            {
                "date": "2026-01-04",
                "raw_score": 0.0,
                "smooth_score": 0.0,
                "baseline_score": 0.0,
                "residual_score": 0.0,
                "structural_raw": 0.0,
                "trigger_raw": 0.0,
            },
        ],
        "windows": [],
        "debug": {"signal_count": 1},
    }


def _predictive_results_with_signal(**overrides):
    results = _predictive_results()
    signal = dict(results["signals"][0])
    signal.update(overrides)
    results["signals"] = [signal]
    return results


if __name__ == "__main__":
    unittest.main(verbosity=2)
