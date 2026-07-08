import os
import sys
import unittest
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.candidates import build_candidate_registry
from engine.predictive_sidecar import build_predictive_sidecar


class TestPhase8CandidateBuilder(unittest.TestCase):
    def test_accepted_candidate_has_pre_registration_and_outcome_linkage(self):
        registry = build_candidate_registry(
            report_run_id="run_phase8",
            natal_snapshot_id="natal_phase8",
            signals=[
                _signal("sig_trigger", "TRANSIT", "transit_family", "Mars", "Sun", "trigger_evidence"),
                _signal("sig_long", "SOLAR_ARC", "solar_arc_family", "Sun", "Sun", "chapter_evidence"),
            ],
            chapters=[_chapter("chap_phase8", ["sig_long"])],
            anchors=[_anchor()],
            daily_series=[],
            payload=_payload(),
            pre_registered_at=_dt("2026-01-01T12:00:00"),
        )

        self.assertEqual(len(registry["candidates"]), 1)
        candidate = registry["candidates"][0]
        self.assertTrue(candidate["candidate_id"].startswith("cand_"))
        self.assertEqual(candidate["report_run_id"], "run_phase8")
        self.assertEqual(candidate["candidate_status"], "pre_registered")
        self.assertEqual(candidate["pre_registered_at"], "2026-01-01T12:00:00Z")
        self.assertEqual(candidate["maximum_window_days"], None)
        self.assertEqual(candidate["report_surface_visibility"], ["internal_rd"])
        self.assertIn("component_scores", candidate)
        self.assertIn("chapter_support", candidate)
        self.assertIn("trigger_support", candidate)
        self.assertEqual(registry["convergence_composition"][0]["candidate_id"], candidate["candidate_id"])

    def test_rejected_candidate_uses_locked_reason_enum(self):
        registry = build_candidate_registry(
            report_run_id="run_phase8",
            natal_snapshot_id="natal_phase8",
            signals=[_signal("sig_no_chapter", "TRANSIT", "transit_family", "Mars", "Sun", "trigger_evidence")],
            chapters=[],
            anchors=[_anchor()],
            daily_series=[{"date": "2026-01-03", "residual_score": 0.2}],
            payload=_payload(),
            pre_registered_at=_dt("2026-01-01T12:00:00"),
        )

        self.assertEqual(registry["candidates"], [])
        self.assertEqual(len(registry["rejected_candidates"]), 1)
        rejection = registry["rejected_candidates"][0]
        self.assertEqual(rejection["filter_reason"], "no_chapter_support")
        self.assertEqual(rejection["requirement_that_failed"], "|chapter_support| >= 1")
        self.assertIn("sig_no_chapter", rejection["signal_ids_considered"])

    def test_anti_stacking_rejection_uses_composite_dedup(self):
        registry = build_candidate_registry(
            report_run_id="run_phase8",
            natal_snapshot_id="natal_phase8",
            signals=[
                _signal("sig_transit", "TRANSIT", "transit_family", "Uranus", "Sun", "trigger_evidence"),
                _signal("sig_prop", "PROPRIETARY_TRANSIT", "proprietary_transit_family", "Uranus", "Sun", "trigger_evidence"),
            ],
            chapters=[_chapter("chap_phase8", ["sig_transit", "sig_prop"])],
            anchors=[_anchor()],
            daily_series=[],
            payload=_payload(),
            pre_registered_at=_dt("2026-01-01T12:00:00"),
        )

        self.assertEqual(registry["candidates"], [])
        self.assertEqual(registry["rejected_candidates"][0]["filter_reason"], "anti_double_counting_violation")

    def test_trigger_derived_window_has_no_hidden_cap(self):
        wide_trigger = _signal(
            "sig_wide_trigger",
            "TRANSIT",
            "transit_family",
            "Mars",
            "Sun",
            "trigger_evidence",
            start_date="2026-01-01",
            peak_date="2026-01-10",
            end_date="2026-01-20",
        )
        registry = build_candidate_registry(
            report_run_id="run_phase8",
            natal_snapshot_id="natal_phase8",
            signals=[
                wide_trigger,
                _signal("sig_long", "SOLAR_ARC", "solar_arc_family", "Sun", "Sun", "chapter_evidence"),
            ],
            chapters=[_chapter("chap_phase8", ["sig_long"], start_at="2025-12-01T00:00:00Z", end_at="2026-02-01T00:00:00Z")],
            anchors=[_anchor()],
            daily_series=[],
            payload=_payload(),
            pre_registered_at=_dt("2026-01-01T12:00:00"),
        )

        candidate = registry["candidates"][0]
        self.assertGreater(candidate["window_days"], 18.0)
        self.assertIsNone(candidate["maximum_window_days"])
        self.assertEqual(candidate["start_at"], "2026-01-01T00:00:00Z")
        self.assertEqual(candidate["end_at"], "2026-01-20T23:59:59Z")


class TestPhase8SidecarIntegration(unittest.TestCase):
    def test_sidecar_exports_candidates_and_rejections(self):
        predictive_results = {
            "formula_version": "predictive_v0.3.1",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "signals": [
                _signal("sig_accept_trigger", "TRANSIT", "transit_family", "Mars", "Sun", "trigger_evidence"),
                _signal("sig_accept_long", "SOLAR_ARC", "solar_arc_family", "Sun", "Sun", "chapter_evidence"),
                _signal("sig_rejected", "LUNATION", "lunation_family", "Lunar", "Moon", "trigger_evidence", start_date="2026-02-01", peak_date="2026-02-01", end_date="2026-02-01"),
            ],
            "daily_series": [
                {"date": "2026-01-03", "residual_score": 0.4},
                {"date": "2026-02-01", "residual_score": 0.1},
            ],
            "time_lord_periods": [],
            "index_results": {},
            "debug": {"natal_promise_anchor_count": 1, "convergence_composition_count": 1},
        }

        sidecar = build_predictive_sidecar(
            report_type="predictive_sandbox",
            birth_data=_birth_data(),
            payload=_payload(),
            predictive_results=predictive_results,
            report_start=_dt("2026-01-01T00:00:00"),
            report_end=_dt("2026-12-31T00:00:00"),
        )

        self.assertTrue(sidecar["candidates"])
        self.assertTrue(sidecar["rejected_candidates"])
        candidate = sidecar["candidates"][0]
        self.assertEqual(candidate["report_run_id"], sidecar["report_run"]["report_run_id"])
        self.assertIn("candidate_id", sidecar["convergence_composition"][-1])
        self.assertEqual(sidecar["provenance"]["scanner_versions"]["micro_candidate_builder"], "wired_phase8")


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _birth_data():
    return {
        "name": "Phase Eight",
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
            "methodology": {"zodiac": "tropical", "house_system": "whole_sign"},
        },
        "angles": {
            "Ascendant": {"longitude": 0.0, "sign": "Aries", "house": 1},
            "Midheaven": {"longitude": 270.0, "sign": "Capricorn", "house": 10},
        },
        "houses": {
            "House_1": {"sign": "Aries", "house": 1},
            "House_4": {"sign": "Cancer", "house": 4},
        },
        "standard_planets": {
            "Sun": {"longitude": 0.0, "sign": "Aries", "house": 1},
            "Moon": {"longitude": 90.0, "sign": "Cancer", "house": 4},
            "Mars": {"longitude": 120.0, "sign": "Leo", "house": 5},
        },
        "custom_asteroids": {},
        "aspects": [
            {"body_1": "Sun", "body_2": "Moon", "aspect": "Square", "orb": 0.0},
        ],
    }


def _anchor():
    return {
        "schema_version": "phase0.1.1",
        "anchor_id": "npa_phase8",
        "natal_snapshot_id": "natal_phase8",
        "anchor_kind": "topic_focus",
        "topic_keys": ["radiance", "catalyst", "threshold_event"],
        "domain_keys": ["identity"],
        "natal_bodies": ["Sun"],
        "natal_asteroids": [],
        "natal_lots": [],
        "houses": [1],
        "rulers": ["Mars"],
        "dispositors": [],
        "aspects": [],
        "configurations": [],
        "proprietary_index_links": [],
        "strength": 0.8,
        "strength_components": {},
        "confidence": 0.9,
        "birth_time_dependency": "none",
        "evidence_trace": {},
        "created_at": "2026-01-01T00:00:00Z",
        "policy_version": "phase8_fixture",
    }


def _chapter(chapter_id, signal_ids, *, start_at="2025-12-01T00:00:00Z", end_at="2026-12-31T23:59:59Z"):
    return {
        "schema_version": "phase0.1.0",
        "chapter_id": chapter_id,
        "start_at": start_at,
        "peak_range": [start_at, end_at],
        "end_at": end_at,
        "chapter_kind": "solar_arc_chapter",
        "active_long_clocks": ["SOLAR_ARC"],
        "contributing_signal_ids": signal_ids,
        "contributing_event_ids": [],
        "natal_anchor_ids": ["npa_phase8"],
        "topic_keys": ["radiance", "catalyst"],
        "domain_keys": ["identity"],
        "asteroid_participants": [],
        "coherence": 1.0,
        "counterforce": 0.0,
        "complexity": 0.2,
        "polarity": 0.5,
        "confidence": 0.9,
        "confidence_components": {},
        "birth_time_dependency": "none",
        "chapter_summary_score": 0.8,
        "report_surface_visibility": ["internal_rd", "predictive_sandbox"],
        "provenance": {},
    }


def _signal(
    signal_id,
    method_family,
    independence_group,
    source_body,
    target_body,
    signal_role,
    *,
    start_date="2026-01-02",
    peak_date="2026-01-03",
    end_date="2026-01-04",
):
    return {
        "schema_version": "phase0.1.0",
        "signal_id": signal_id,
        "source_event_ids": [f"fe_{signal_id}"],
        "method_family": method_family,
        "event_kind": "phase8_fixture",
        "independence_group": independence_group,
        "activation_route": "transit_to_body",
        "signal_role": signal_role,
        "source_body": source_body,
        "target_body": target_body,
        "aspect": "Conjunction",
        "natal_anchor_ids": ["npa_phase8"],
        "topic_keys": ["radiance", "catalyst"],
        "domain_keys": ["identity"],
        "asteroid_participants": [],
        "start_date": start_date,
        "peak_date": peak_date,
        "end_date": end_date,
        "trigger_strength": 0.8,
        "signal_strength": 0.8,
        "structural_importance": 0.1,
        "theme_convergence": 0.0,
        "operation_profile": {"stabilize": 0.1, "amplify": 0.2, "activate": 0.5, "disrupt": 0.1, "dissolve": 0.0, "reveal": 0.1},
        "operation_basis": {},
        "dominant_operation": "activate",
        "epistemic_confidence": 0.9,
        "confidence_components": {"calculation_integrity": 0.9},
        "confidence_state": "supported",
        "angle_eligibility": True,
        "temporal_precision": "day" if signal_role == "trigger_evidence" else "season",
        "clock_role": "trigger" if signal_role == "trigger_evidence" else "chapter",
        "orb": 0.0,
        "allowed_orb": 1.0,
        "exactness": 1.0,
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
