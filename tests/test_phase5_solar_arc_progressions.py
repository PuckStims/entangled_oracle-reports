import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine import progressions, solar_arc
from engine.predictive_engine import compute_predictive_windows
from engine.predictive_sidecar import build_predictive_sidecar


class TestSolarArcDirections(unittest.TestCase):
    def test_solar_arc_contact_uses_declared_family_and_route(self):
        start = _dt("2026-01-01T00:00:00")

        def fake_directed(payload, source_name, moment):
            if source_name != "Sun":
                return None
            return ((moment - start).total_seconds() / 86400.0) % 360.0

        payload = _payload()
        payload["standard_planets"]["Moon"]["longitude"] = 3.0

        with patch("engine.solar_arc.directed_longitude", side_effect=fake_directed):
            events = solar_arc.scan_solar_arc_events(payload, start, _dt("2026-01-08T00:00:00"))

        event = next(e for e in events if e["transit_planet"] == "Sun" and e["natal_target"] == "Moon")
        self.assertEqual(event["event_type"], "solar_arc")
        self.assertEqual(event["method_variant"], "solar_arc_body_aspect")
        self.assertEqual(event["activation_route"], "solar_arc_to_body")
        self.assertEqual(event["independence_group"], "solar_arc_family")
        self.assertLess(abs((event["peak_datetime"] - _dt("2026-01-04T00:00:00")).total_seconds()), 12 * 3600)

    def test_solar_arc_angle_contact_is_withheld_when_birth_time_approximate(self):
        start = _dt("2026-01-01T00:00:00")

        def fake_directed(payload, source_name, moment):
            if source_name != "Sun":
                return None
            return ((moment - start).total_seconds() / 86400.0) % 360.0

        payload = _payload(birth_time_state="approximate")
        payload["angles"]["Ascendant"]["longitude"] = 3.0

        with patch("engine.solar_arc.directed_longitude", side_effect=fake_directed):
            events = solar_arc.scan_solar_arc_events(payload, start, _dt("2026-01-08T00:00:00"))

        event = next(e for e in events if e["transit_planet"] == "Sun" and e["natal_target"] in {"ASC", "Ascendant"})
        self.assertEqual(event["activation_route"], "solar_arc_to_angle")
        self.assertEqual(event["confidence_state"], "withheld")
        self.assertEqual(event["birth_time_dependency"], "hard")

    def test_solar_arc_asteroid_sources_use_anchor_policy_only(self):
        payload = _payload()
        sources = solar_arc._directed_sources(payload, "exact")

        self.assertIn("Kassandra", sources)
        self.assertNotIn("Anubis", sources)


class TestSecondaryProgressions(unittest.TestCase):
    def test_progressed_chart_uses_one_day_per_year_mapping(self):
        payload = _payload()
        payload["julian_day"] = 1000.0

        with patch("engine.progressions._body_longitude_at_jd", side_effect=lambda body, jd: (jd - 1000.0) * 10.0):
            chart = progressions.build_progressed_chart(payload, _dt("1991-01-01T00:00:00"))

        self.assertAlmostEqual(chart["progressed_jd"], 1001.0, places=2)
        self.assertAlmostEqual(chart["positions"]["Sun"]["longitude"], 10.0, places=1)

    def test_progression_contact_is_distinct_from_solar_arc_family(self):
        start = _dt("2026-01-01T00:00:00")

        def fake_progressed(payload, source_name, moment):
            if source_name != "Sun":
                return None
            return ((moment - start).total_seconds() / 86400.0) % 360.0

        payload = _payload()
        payload["standard_planets"]["Moon"]["longitude"] = 3.0

        with patch("engine.progressions.progressed_longitude", side_effect=fake_progressed):
            events = progressions.scan_progression_events(payload, start, _dt("2026-01-08T00:00:00"))

        event = next(e for e in events if e["transit_planet"] == "Sun" and e["natal_target"] == "Moon")
        self.assertEqual(event["event_type"], "progression")
        self.assertEqual(event["method_variant"], "progression_body_aspect")
        self.assertEqual(event["independence_group"], "progression_family")
        self.assertEqual(event["activation_route"], "progression_to_body")

    def test_progressed_angles_are_gated_by_exact_birth_time(self):
        exact_sources = progressions._progressed_sources(_payload(birth_time_state="exact"), "exact")
        approx_sources = progressions._progressed_sources(_payload(birth_time_state="approximate"), "approximate")

        self.assertIn("Ascendant", exact_sources)
        self.assertNotIn("Ascendant", approx_sources)


class TestPhase5EvidenceIntegration(unittest.TestCase):
    def test_predictive_engine_and_sidecar_export_solar_arc_and_progression(self):
        solar_event = solar_arc._solar_arc_event(
            "Sun",
            "Moon",
            {"kind": "luminary"},
            {"kind": "luminary", "relevance": 0.9},
            "Conjunction",
            0.0,
            _dt("2026-01-04T00:00:00"),
            "exact",
        )
        progression_event = progressions._progression_contact_event(
            "Sun",
            "Moon",
            {"kind": "planet"},
            {"kind": "luminary", "relevance": 0.9},
            "Conjunction",
            0.0,
            1.0,
            _dt("2026-02-04T00:00:00"),
            "exact",
        )

        with patch("engine.predictive_engine._collect_transit_signals", return_value=[]), \
            patch("engine.returns.scan_return_events", return_value=[]), \
            patch("engine.profections.annual_profection_periods", return_value=[]), \
            patch("engine.solar_arc.scan_solar_arc_events", return_value=[solar_event]), \
            patch("engine.progressions.scan_progression_events", return_value=[progression_event]):
            predictive_results = compute_predictive_windows(
                natal_payload=_payload(),
                index_results={},
                start_date=_dt("2026-01-01T00:00:00"),
                end_date=_dt("2026-12-31T00:00:00"),
                options={"enable_asteroid_rd": False},
            )

        families = {signal["method_family"] for signal in predictive_results["signals"]}
        groups = {signal["independence_group"] for signal in predictive_results["signals"]}
        self.assertIn("SOLAR_ARC", families)
        self.assertIn("PROGRESSION", families)
        self.assertIn("solar_arc_family", groups)
        self.assertIn("progression_family", groups)

        sidecar = build_predictive_sidecar(
            report_type="predictive_sandbox",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=predictive_results,
            report_start=_dt("2026-01-01T00:00:00"),
            report_end=_dt("2026-12-31T00:00:00"),
        )

        method_families = [event["method_family"] for event in sidecar["raw_events"]]
        self.assertIn("SOLAR_ARC", method_families)
        self.assertIn("PROGRESSION", method_families)
        self.assertEqual(sidecar["provenance"]["scanner_versions"]["scan_solar_arc"], "wired_phase5:1")
        self.assertEqual(sidecar["provenance"]["scanner_versions"]["scan_secondary_progressions"], "wired_phase5:1")


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _birth_data():
    return {
        "name": "Phase Five",
        "date": "1990-01-01",
        "time": "12:00",
        "location": "Peoria, Illinois, USA",
    }


def _payload(birth_time_state="exact"):
    return {
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "birth_location": "Peoria, Illinois, USA",
        "latitude": 40.6936,
        "longitude": -89.589,
        "timezone": "America/Chicago",
        "julian_day": 2447893.25,
        "user_profile": {
            "birth_time_state": birth_time_state,
            "house_system": "Whole Sign",
            "zodiac": "Tropical",
            "methodology": {"zodiac": "tropical", "house_system": "whole_sign"},
        },
        "angles": {
            "Ascendant": {"longitude": 0.0, "sign": "Aries", "house": 1},
            "Midheaven": {"longitude": 270.0, "sign": "Capricorn", "house": 10},
        },
        "houses": {},
        "standard_planets": {
            "Sun": {"longitude": 0.0, "sign": "Aries", "house": 1},
            "Moon": {"longitude": 90.0, "sign": "Cancer", "house": 4},
            "Mercury": {"longitude": 15.0, "sign": "Aries", "house": 1},
            "Venus": {"longitude": 45.0, "sign": "Taurus", "house": 2},
            "Mars": {"longitude": 120.0, "sign": "Leo", "house": 5},
        },
        "custom_asteroids": {
            "Kassandra": {"longitude": 10.0, "sign": "Aries", "house": 1},
            "Anubis": {"longitude": 20.0, "sign": "Aries", "house": 1},
        },
        "aspects": [],
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
