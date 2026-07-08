import os
import sys
import types
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.asteroid_policy import REQUIRED_ASTEROID_COUNT, load_asteroid_policy
from engine.predictive_engine import compute_predictive_windows
from engine.predictive_sidecar import build_predictive_sidecar


class TestAsteroidPolicyRegistry(unittest.TestCase):
    def test_registry_loads_exactly_34_required_asteroids(self):
        policy = load_asteroid_policy()

        self.assertEqual(policy.policy_version, "phase0.1.2")
        self.assertEqual(policy.asteroid_count, REQUIRED_ASTEROID_COUNT)
        self.assertEqual(len(set(policy.asteroid_names)), REQUIRED_ASTEROID_COUNT)
        self.assertIn("Kassandra", policy.asteroid_names)
        self.assertIn("DNA", policy.asteroid_names)

        for name in policy.asteroid_names:
            record = policy.require_record(name)
            for key in (
                "asteroid_name",
                "ephemeris_id",
                "tier",
                "natal_roles",
                "topic_keys",
                "domain_keys",
                "proprietary_index_links",
            ):
                self.assertIn(key, record)
            self.assertTrue(policy.target_eligible(name, "transit"))

    def test_registry_preserves_migration_map_target_weights(self):
        policy = load_asteroid_policy()

        self.assertEqual(policy.target_weight("Kassandra"), 0.85)
        self.assertEqual(policy.target_weight("Aletheia"), 0.80)
        self.assertEqual(policy.target_weight("Destinn"), 0.80)
        self.assertEqual(policy.target_weight("Karma"), 0.80)
        self.assertEqual(policy.target_weight("Kaali"), 0.75)
        self.assertEqual(policy.target_weight("Medea"), 0.75)
        self.assertEqual(policy.target_weight("Hermes"), 0.70)
        self.assertEqual(policy.target_weight("Chaos"), 0.70)
        self.assertEqual(policy.target_weight("Anubis"), 0.65)
        self.assertEqual(policy.target_weight("DNA"), 0.55)

    def test_structured_source_restrictions_are_checkable(self):
        policy = load_asteroid_policy()

        self.assertTrue(policy.source_eligible("Sirene", "transit", aspect="Conjunction", target_body="ASC"))
        self.assertFalse(policy.source_eligible("Sirene", "transit", aspect="Square", target_body="ASC"))
        self.assertFalse(policy.source_eligible("Sirene", "transit", aspect="Conjunction", target_body="Mars"))

        self.assertTrue(policy.source_eligible("Themis", "transit", aspect="Conjunction", target_body="Destinn"))
        self.assertFalse(policy.source_eligible("Themis", "transit", aspect="Conjunction", target_body="Kassandra"))


class TestProprietaryAsteroidEvidenceGate(unittest.TestCase):
    def test_gate_disabled_does_not_call_proprietary_scanner(self):
        transit_engine = types.ModuleType("engine.transit_engine")
        transit_engine.scan_proprietary_forecast_windows = lambda **kwargs: self.fail("scanner should be gated off")

        with patch.dict(sys.modules, {"engine.transit_engine": transit_engine}), \
            patch("engine.predictive_engine._collect_transit_signals", return_value=[]):
            result = compute_predictive_windows(
                natal_payload=_payload(),
                index_results={},
                start_date=_dt("2026-01-01"),
                end_date=_dt("2026-02-01"),
                options={"enable_asteroid_rd": False},
            )

        self.assertEqual(result["signals"], [])
        self.assertEqual(result["debug"]["scan_proprietary_forecast_windows"], "rd_gate_disabled")

    def test_gate_enabled_normalizes_existing_proprietary_windows(self):
        transit_engine = types.ModuleType("engine.transit_engine")
        transit_engine.scan_proprietary_forecast_windows = _fake_proprietary_scanner

        with patch.dict(sys.modules, {"engine.transit_engine": transit_engine}), \
            patch("engine.predictive_engine._collect_transit_signals", return_value=[]):
            result = compute_predictive_windows(
                natal_payload=_payload(),
                index_results={},
                start_date=_dt("2026-01-01"),
                end_date=_dt("2026-02-01"),
                options={"enable_asteroid_rd": True},
            )

        self.assertEqual(result["debug"]["scan_proprietary_forecast_windows"], "wired_phase3_rd_gate")
        self.assertEqual(result["debug"]["proprietary_asteroid_signal_count"], 1)
        signal = result["signals"][0]
        self.assertEqual(signal["method_family"], "PROPRIETARY_TRANSIT")
        self.assertEqual(signal["event_kind"], "disruption")
        self.assertEqual(signal["independence_group"], "proprietary_transit_family")
        self.assertEqual(signal["activation_route"], "proprietary_transit_to_body")
        self.assertEqual(signal["source_body"], "Chaos")
        self.assertEqual(signal["target_body"], "Kassandra")
        self.assertEqual(signal["trigger_strength"], 0.8)
        self.assertIn("rupture", signal["topic_keys"])
        self.assertIn("truth_under_doubt", signal["topic_keys"])
        self.assertEqual(signal["asteroid_policy"]["participants"], ["Chaos", "Kassandra"])

    def test_sidecar_records_proprietary_asteroid_provenance(self):
        predictive_results = {
            "formula_version": "predictive_v0.3.1",
            "signals": [
                {
                    **_proprietary_signal(),
                    "signal_id": "sig_prp_test",
                }
            ],
            "daily_series": [
                {
                    "date": "2026-01-10",
                    "raw_score": 0.8,
                    "smooth_score": 0.8,
                    "baseline_score": 0.2,
                    "residual_score": 0.6,
                    "structural_raw": 0.0,
                    "trigger_raw": 0.8,
                }
            ],
            "debug": {
                "scan_proprietary_forecast_windows": "wired_phase3_rd_gate",
                "proprietary_asteroid_signal_count": 1,
            },
        }

        sidecar = build_predictive_sidecar(
            report_type="predictive_sandbox",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=predictive_results,
            report_start=_dt("2026-01-01"),
            report_end=_dt("2026-02-01"),
        )

        raw_event = sidecar["raw_events"][0]
        signal = sidecar["predictive_signals"][0]

        self.assertEqual(
            sidecar["provenance"]["scanner_versions"]["scan_proprietary_forecast_windows"],
            "wired_phase3_rd_gate",
        )
        self.assertEqual(sidecar["asteroid_diagnostics"]["registry_asteroids_declared_count"], 34)
        self.assertEqual(raw_event["method_family"], "PROPRIETARY_TRANSIT")
        self.assertEqual(raw_event["method_variant"], "disruption")
        self.assertEqual(raw_event["asteroid_participants"], ["Chaos", "Kassandra"])
        self.assertIn("rupture", raw_event["topic_keys"])
        self.assertEqual(signal["asteroid_policy"]["formula_group"], "DISRUPTION")


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _birth_data():
    return {
        "name": "Phase Three",
        "date": "1990-01-01",
        "time": "12:00",
        "location": "Peoria, Illinois, USA",
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
            "methodology": {"zodiac": "tropical", "house_system": "whole_sign"},
        },
        "angles": {
            "Ascendant": {"longitude": 10.0, "sign": "Aries", "house": 1},
            "Midheaven": {"longitude": 270.0, "sign": "Capricorn", "house": 10},
            "Descendant": {"longitude": 190.0, "sign": "Libra", "house": 7},
            "Imum_Coeli": {"longitude": 90.0, "sign": "Cancer", "house": 4},
        },
        "houses": {},
        "standard_planets": {
            "Sun": {"longitude": 280.0, "sign": "Capricorn", "house": 10},
            "Mars": {"longitude": 40.0, "sign": "Taurus", "house": 2},
        },
        "custom_asteroids": {
            "Kassandra": {"longitude": 41.0, "sign": "Taurus", "house": 2},
            "Chaos": {"longitude": 40.5, "sign": "Taurus", "house": 2},
        },
        "aspects": [],
    }


def _fake_proprietary_scanner(*args, **kwargs):
    return {
        "DISRUPTION": [_proprietary_event()],
        "SOVEREIGNTY": [],
        "CATALYST": [],
    }


def _proprietary_event():
    return {
        "event_type": "proprietary_transit",
        "formula_name": "DISRUPTION",
        "formula_label": "Disruption & Revelation",
        "transit_planet": "Chaos",
        "aspect": "Conjunction",
        "natal_target": "Kassandra",
        "natal_target_display": "your Kassandra in the 2nd house",
        "natal_house": 2,
        "orb": 0.2,
        "orb_limit": 2.0,
        "weight": 2.5,
        "raw_score": 2.25,
        "combined_intensity_score": 0.8,
        "score": 0.8,
        "entry_datetime": _dt("2026-01-08"),
        "peak_datetime": _dt("2026-01-10"),
        "leave_datetime": _dt("2026-01-12"),
    }


def _proprietary_signal():
    policy = load_asteroid_policy()
    event = _proprietary_event()
    return {
        "method_family": "PROPRIETARY_TRANSIT",
        "event_kind": "disruption",
        "independence_group": "proprietary_transit_family",
        "activation_route": "proprietary_transit_to_body",
        "source_event_type": "proprietary_transit",
        "source_body": "Chaos",
        "target_body": "Kassandra",
        "aspect": "Conjunction",
        "orb": 0.2,
        "allowed_orb": 2.0,
        "exactness": 0.9,
        "event_weight": 2.5,
        "target_relevance": 0.85,
        "trigger_strength": 0.8,
        "signal_strength": 0.8,
        "structural_importance": 0.0,
        "theme_convergence": 0.0,
        "start_date": event["entry_datetime"].date(),
        "peak_date": event["peak_datetime"].date(),
        "end_date": event["leave_datetime"].date(),
        "topic_keys": policy.topic_keys("Chaos") + policy.topic_keys("Kassandra"),
        "domain_keys": ["transformation", "identity", "communication", "meaning"],
        "operation_profile": {"reveal": 0.6},
        "operation_basis": {"method_behavior": "PROPRIETARY_TRANSIT"},
        "dominant_operation": "reveal",
        "epistemic_confidence": 0.75,
        "confidence_components": {"method_maturity": 0.75},
        "confidence_state": "moderate",
        "angle_eligibility": False,
        "asteroid_policy": {
            "participants": ["Chaos", "Kassandra"],
            "source_validation_category": "primary_asteroid",
            "target_validation_category": "primary_asteroid",
            "report_surface_visibility": ["internal_rd", "predictive_sandbox", "soul_ecosystem"],
            "formula_group": "DISRUPTION",
            "formula_label": "Disruption & Revelation",
            "raw_score": 2.25,
            "combined_intensity_score": 0.8,
        },
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
