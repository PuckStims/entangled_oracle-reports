import os
import sys
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine import returns
from engine.predictive_engine import compute_predictive_windows
from engine.predictive_sidecar import build_predictive_sidecar
from engine.profections import annual_profection_for_age, annual_profection_periods


class TestReturnMoments(unittest.TestCase):
    def test_solar_return_bisection_finds_exact_moment(self):
        epoch = _dt("2026-01-01T00:00:00")

        def fake_longitude(body, moment):
            days = (moment - epoch).total_seconds() / 86400.0
            return (days * 10.0) % 360.0

        payload = _payload()
        payload["standard_planets"]["Sun"]["longitude"] = 30.0

        with patch("engine.returns._body_longitude", side_effect=fake_longitude):
            events = returns.scan_return_events(
                payload,
                _dt("2026-01-01T00:00:00"),
                _dt("2026-01-10T00:00:00"),
                bodies=("Sun",),
            )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["method_variant"], "solar_return")
        self.assertLess(abs((events[0]["peak_datetime"] - _dt("2026-01-04T00:00:00")).total_seconds()), 120)
        self.assertEqual(events[0]["activation_route"], "return_moment")

    def test_lunar_returns_are_monotonic(self):
        epoch = _dt("2026-01-01T00:00:00")
        lunar_period_days = 27.321

        def fake_longitude(body, moment):
            days = (moment - epoch).total_seconds() / 86400.0
            return (days / lunar_period_days * 360.0) % 360.0

        payload = _payload()
        payload["standard_planets"]["Moon"]["longitude"] = 0.0

        with patch("engine.returns._body_longitude", side_effect=fake_longitude):
            events = returns.scan_return_events(
                payload,
                _dt("2026-01-01T00:00:00"),
                _dt("2026-03-01T00:00:00"),
                bodies=("Moon",),
            )

        self.assertGreaterEqual(len(events), 2)
        peaks = [event["peak_datetime"] for event in events]
        self.assertEqual(peaks, sorted(peaks))
        self.assertTrue(all(event["method_variant"] == "lunar_return" for event in events))


class TestAnnualProfections(unittest.TestCase):
    def test_annual_profection_house_sign_and_lord_cycle(self):
        payload = _payload(asc_sign="Cancer")

        age_12 = annual_profection_for_age(payload, 12)
        age_13 = annual_profection_for_age(payload, 13)

        self.assertEqual(age_12["profected_house"], 1)
        self.assertEqual(age_12["profected_sign"], "Cancer")
        self.assertEqual(age_12["time_lord"], "Moon")
        self.assertEqual(age_13["profected_house"], 2)
        self.assertEqual(age_13["profected_sign"], "Leo")
        self.assertEqual(age_13["time_lord"], "Sun")

    def test_annual_profection_period_exports_time_lord_contract(self):
        periods = annual_profection_periods(
            _payload(asc_sign="Aries"),
            _dt("2026-07-01T00:00:00"),
            _dt("2027-07-01T00:00:00"),
        )

        self.assertGreaterEqual(len(periods), 1)
        active = periods[0]
        self.assertEqual(active["schema_version"], "phase0.1.1")
        self.assertEqual(active["system"], "annual_profection")
        self.assertEqual(active["level"], "year")
        self.assertEqual(active["period_lord"], "Mars")
        self.assertEqual(active["birth_time_dependency"], "none")
        self.assertEqual(active["report_surface_visibility"], ["internal_rd", "predictive_sandbox"])

    def test_missing_ascendant_sign_refuses_to_compute(self):
        payload = _payload()
        payload["angles"]["Ascendant"].pop("sign")

        self.assertEqual(
            annual_profection_periods(payload, _dt("2026-01-01T00:00:00"), _dt("2027-01-01T00:00:00")),
            [],
        )


class TestPhase4EvidenceIntegration(unittest.TestCase):
    def test_predictive_engine_and_sidecar_export_returns_and_profections(self):
        return_event = returns._return_event("Sun", 280.0, _dt("2026-01-04T12:00:00"))
        profection_period = annual_profection_periods(
            _payload(asc_sign="Aries"),
            _dt("2026-01-01T00:00:00"),
            _dt("2027-01-01T00:00:00"),
        )[0]

        with patch("engine.predictive_engine._collect_transit_signals", return_value=[]), \
            patch("engine.returns.scan_return_events", return_value=[return_event]), \
            patch("engine.profections.annual_profection_periods", return_value=[profection_period]):
            predictive_results = compute_predictive_windows(
                natal_payload=_payload(asc_sign="Aries"),
                index_results={},
                start_date=_dt("2026-01-01T00:00:00"),
                end_date=_dt("2027-01-01T00:00:00"),
                options={"enable_asteroid_rd": False},
            )

        return_signal = predictive_results["signals"][0]
        self.assertEqual(return_signal["method_family"], "RETURN")
        self.assertEqual(return_signal["event_kind"], "solar_return")
        self.assertEqual(return_signal["independence_group"], "return_family_sun")
        self.assertEqual(return_signal["activation_route"], "return_moment")
        self.assertEqual(predictive_results["time_lord_periods"][0]["system"], "annual_profection")

        sidecar = build_predictive_sidecar(
            report_type="year_ahead",
            birth_data=_birth_data(),
            payload=_payload(asc_sign="Aries"),
            predictive_results=predictive_results,
            report_start=_dt("2026-01-01T00:00:00"),
            report_end=_dt("2027-01-01T00:00:00"),
        )

        raw_event = sidecar["raw_events"][0]
        self.assertEqual(raw_event["method_family"], "RETURN")
        self.assertEqual(raw_event["method_variant"], "solar_return")
        self.assertEqual(raw_event["clock_role"], "return")
        self.assertEqual(raw_event["activation_route"], "return_moment")
        self.assertEqual(raw_event["report_surface_visibility"], ["internal_rd", "predictive_sandbox"])
        self.assertEqual(sidecar["time_lord_periods"][0]["system"], "annual_profection")
        self.assertEqual(sidecar["provenance"]["scanner_versions"]["scan_return_moments"], "wired_phase4:1")
        self.assertEqual(sidecar["provenance"]["scanner_versions"]["annual_profections"], "wired_phase4:1")


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _birth_data():
    return {
        "name": "Phase Four",
        "date": "1990-01-01",
        "time": "12:00",
        "location": "Peoria, Illinois, USA",
    }


def _payload(asc_sign="Aries"):
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
            "Ascendant": {"longitude": 0.0, "sign": asc_sign, "house": 1},
            "Midheaven": {"longitude": 270.0, "sign": "Capricorn", "house": 10},
        },
        "houses": {},
        "standard_planets": {
            "Sun": {"longitude": 280.0, "sign": "Capricorn", "house": 10},
            "Moon": {"longitude": 40.0, "sign": "Taurus", "house": 2},
            "Jupiter": {"longitude": 120.0, "sign": "Leo", "house": 5},
            "Saturn": {"longitude": 200.0, "sign": "Libra", "house": 7},
            "Mars": {"longitude": 30.0, "sign": "Taurus", "house": 2},
        },
        "custom_asteroids": {},
        "aspects": [],
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
