import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.asteroid_policy import load_asteroid_policy
from engine import progressions, solar_arc, transit_engine
from formulas.standard.forecast_activation import build_forecast_activation_profile, enrich_forecast_event, link_related_forecast_events


class TestAsteroidTargetEligibilityOverrides(unittest.TestCase):
    def test_horizon2_target_overrides_are_live_policy(self):
        policy = load_asteroid_policy()

        for name in ("Themis", "Hekate", "Moirai"):
            self.assertTrue(policy.target_eligible(name, "progression"))
            self.assertTrue(policy.target_eligible(name, "solar_arc"))

        self.assertTrue(policy.target_eligible("Sirene", "progression"))
        self.assertTrue(policy.target_eligible("Sirene", "solar_arc"))
        self.assertFalse(policy.target_eligible("Atlantis", "progression"))

    def test_progression_and_solar_arc_collect_override_targets(self):
        payload = _payload()
        payload["custom_asteroids"].update({
            "Themis": {"longitude": 11.0, "sign": "Aries", "house": 1},
            "Hekate": {"longitude": 12.0, "sign": "Aries", "house": 1},
            "Moirai": {"longitude": 13.0, "sign": "Aries", "house": 1},
        })

        progression_targets = progressions._natal_targets(payload)
        solar_arc_targets = solar_arc._natal_targets(payload)

        for name in ("Themis", "Hekate", "Moirai"):
            self.assertIn(name, progression_targets)
            self.assertIn(name, solar_arc_targets)

    def test_transit_targets_collect_all_registry_eligible_asteroid_families(self):
        payload = _payload()
        payload["custom_asteroids"].update({
            "Sirene": {"longitude": 20.0, "declination": 4.0, "sign": "Aries", "house": 1},
            "Atlantis": {"longitude": 21.0, "declination": 5.0, "sign": "Aries", "house": 1},
        })

        transit_targets = transit_engine._natal_targets(payload)

        self.assertIn("Sirene", transit_targets)
        self.assertIn("Atlantis", transit_targets)


class TestCazimiTransitCycleScoring(unittest.TestCase):
    def test_cazimi_contact_applies_multiplier_to_transit_cycle_score(self):
        window = {
            "transit_planet": "Mars",
            "aspect": "Conjunction",
            "target_name": "Moon",
            "target": {"longitude": 10.0, "house": 4},
            "maximum_orb": 2.0,
            "entry": _dt("2026-01-01T00:00:00"),
            "last_active": _dt("2026-01-02T00:00:00"),
            "peak_orb": 1.0,
            "_active_at_start": False,
            "_active_at_end": False,
            "_body_id": None,
            "contacts": [
                {
                    "contact_datetime": _dt("2026-01-01T12:00:00"),
                    "contact_date": "Jan 1",
                    "contact_orb": 1.0,
                    "sequence_index": 1,
                    "source_cazimi": True,
                }
            ],
        }

        event = transit_engine._build_transit_cycle(
            [window],
            _dt("2026-01-01T00:00:00"),
            _dt("2026-01-03T00:00:00"),
            activation_profile=None,
        )

        self.assertTrue(event["source_cazimi"])
        self.assertEqual(event["cazimi_multiplier"], 2.5)
        self.assertEqual(event["_base_concentration_score"], 0.275)
        self.assertEqual(event["concentration_score"], 0.6875)

    def test_cazimi_boost_survives_enrichment_as_method_weight_and_structural_bonus(self):
        profile = build_forecast_activation_profile(_payload())
        base = {
            "event_type": "transit",
            "transit_planet": "Mars",
            "aspect": "Conjunction",
            "natal_target": "Moon",
            "natal_house": 4,
            "maximum_orb": 2.0,
            "orb": 0.2,
            "raw_score": 0.55,
            "concentration_score": 0.55,
            "combined_intensity_score": 0.55,
            "entry_datetime": _dt("2026-01-01T00:00:00"),
            "peak_datetime": _dt("2026-01-02T00:00:00"),
            "leave_datetime": _dt("2026-01-03T00:00:00"),
            "duration_days": 2.0,
            "contact_count": 1,
        }
        ordinary = enrich_forecast_event(dict(base), profile)
        cazimi = enrich_forecast_event({**base, "source_cazimi": True, "cazimi_multiplier": 2.5}, profile)

        self.assertGreater(cazimi["combined_intensity_score"], ordinary["combined_intensity_score"])
        self.assertGreater(cazimi["structural_importance"], ordinary["structural_importance"])
        self.assertEqual(cazimi["score_components"]["method_weight"]["source"], "cazimi_multiplier")


class TestMonthlyProfectionsTimelineWiring(unittest.TestCase):
    def test_compute_year_ahead_events_returns_annual_and_monthly_time_lords(self):
        with patch("engine.transit_engine.scan_transit_windows", return_value=[]), \
             patch("engine.transit_engine.scan_house_ingresses", return_value=[]), \
             patch("engine.transit_engine.scan_stations", return_value=[]), \
             patch("engine.transit_engine.scan_eclipses", return_value=[]), \
             patch("engine.transit_engine.scan_lunations", return_value=[]), \
             patch("engine.returns.scan_return_events", return_value=[]):
            timeline = transit_engine.compute_year_ahead_events(
                _payload(),
                _dt("2026-01-01T00:00:00"),
                _dt("2026-04-01T00:00:00"),
            )

        systems = {period["system"] for period in timeline["time_lord_periods"]}
        self.assertIn("annual_profection", systems)
        self.assertIn("monthly_profection", systems)

    def test_monthly_profection_affects_transit_weighting(self):
        profile = build_forecast_activation_profile(_payload())
        transit = enrich_forecast_event(
            {
                "event_type": "transit",
                "transit_planet": "Mars",
                "aspect": "Conjunction",
                "natal_target": "Moon",
                "natal_house": 4,
                "maximum_orb": 2.0,
                "orb": 0.2,
                "raw_score": 0.55,
                "concentration_score": 0.55,
                "combined_intensity_score": 0.55,
                "entry_datetime": _dt("2026-01-01T00:00:00"),
                "peak_datetime": _dt("2026-01-15T00:00:00"),
                "leave_datetime": _dt("2026-02-01T00:00:00"),
                "duration_days": 31.0,
                "contact_count": 1,
            },
            profile,
        )
        linked = link_related_forecast_events(
            [transit],
            [],
            [],
            [],
            profile,
            time_lord_periods=[
                {
                    "system": "monthly_profection",
                    "period_lord": "Mars",
                    "period_house": 4,
                    "start_at": _dt("2026-01-01T00:00:00"),
                    "end_at": _dt("2026-02-01T00:00:00"),
                    "weight_modifier": 1.20,
                }
            ],
        )
        weighted = linked["transit_events"][0]

        self.assertIn("time_lord_transit", weighted["monthly_profection_linkage"])
        self.assertGreater(weighted["combined_intensity_score"], transit["combined_intensity_score"])
        self.assertEqual(weighted["score_components"]["time_lord_support"]["source"], "monthly_profection")


class TestDeclinationPredictiveScanning(unittest.TestCase):
    def test_transit_declination_scanner_emits_parallel_event(self):
        payload = _payload()
        payload["standard_planets"]["Moon"]["declination"] = 10.0

        with patch.dict(transit_engine.TRANSIT_PLANETS, {999: "Mars"}, clear=True), \
             patch.object(transit_engine, "_planet_declination", return_value=10.2):
            events = transit_engine.scan_transit_declination_windows(
                payload,
                _dt("2026-01-01T00:00:00"),
                _dt("2026-01-02T00:00:00"),
                activation_profile=None,
            )

        self.assertTrue(events)
        self.assertEqual(events[0]["aspect"], "Parallel")
        self.assertTrue(events[0]["declination_aspect"])
        self.assertEqual(events[0]["method_variant"], "transit_declination")

    def test_progression_declination_scanner_emits_contraparallel_event(self):
        payload = _payload()
        payload["standard_planets"]["Venus"]["declination"] = -4.4

        with patch.object(progressions, "progressed_declination", return_value=4.0):
            events = progressions.scan_progression_declination_events(
                payload,
                _dt("2026-01-01T00:00:00"),
                _dt("2026-02-01T00:00:00"),
            )

        self.assertTrue(events)
        self.assertTrue(any(event["aspect"] == "Contraparallel" for event in events))
        self.assertTrue(any(event["method_variant"] == "progression_declination" for event in events))


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


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
            "Jupiter": {"longitude": 180.0, "sign": "Libra", "house": 7},
            "Saturn": {"longitude": 200.0, "sign": "Libra", "house": 7},
        },
        "custom_asteroids": {
            "Kassandra": {"longitude": 10.0, "sign": "Aries", "house": 1},
        },
        "aspects": [],
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
