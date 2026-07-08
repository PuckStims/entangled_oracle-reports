import os
import sys
import unittest
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.convergence import (
    build_chapter_states,
    build_convergence_composition,
    coherence_graph,
    component_scores,
    method_family_diversity,
)
from engine.natal_promise import apply_anchor_matching, build_natal_promise_anchors
from engine.predictive_sidecar import build_predictive_sidecar


class TestNatalPromiseAnchors(unittest.TestCase):
    def test_asteroid_anchor_uses_registry_topics_and_index_links(self):
        anchors = build_natal_promise_anchors(
            _payload(),
            {"KVQ": {"score": 0.88}},
            natal_snapshot_id="natal_phase7",
            created_at=_dt("2026-01-01T00:00:00"),
        )

        kassandra = [
            anchor for anchor in anchors
            if anchor["natal_asteroids"] == ["Kassandra"] and anchor["proprietary_index_links"]
        ][0]

        self.assertEqual(kassandra["schema_version"], "phase0.1.1")
        self.assertIn("truth_under_doubt", kassandra["topic_keys"])
        self.assertIn("natal_lots", kassandra)
        self.assertEqual(kassandra["proprietary_index_links"][0]["index"], "KVQ")
        self.assertTrue(kassandra["anchor_id"].startswith("npa_"))

    def test_anchor_matcher_backfills_signal_anchor_ids_and_topics(self):
        payload = _payload()
        anchors = build_natal_promise_anchors(payload, {"KVQ": {"score": 0.8}}, natal_snapshot_id="natal_phase7")
        signals = [_signal("sig_ast", "PROPRIETARY_TRANSIT", "proprietary_transit_family", "Uranus", "Kassandra")]

        apply_anchor_matching(signals, anchors, payload)

        self.assertTrue(signals[0]["natal_anchor_ids"])
        self.assertIn("truth_under_doubt", signals[0]["topic_keys"])
        self.assertIn("asteroid_participants", signals[0])


class TestConvergenceRules(unittest.TestCase):
    def test_composite_dedup_collapses_matching_transit_and_proprietary_transit(self):
        signals = [
            _signal("sig_transit", "TRANSIT", "transit_family", "Uranus", "Sun"),
            _signal("sig_prop", "PROPRIETARY_TRANSIT", "proprietary_transit_family", "Uranus", "Sun"),
            _signal("sig_arc", "SOLAR_ARC", "solar_arc_family", "Sun", "Sun"),
        ]

        diversity = method_family_diversity(signals)

        self.assertEqual(diversity["count"], 2)
        self.assertIn("sig_prop", diversity["suppressed_signal_ids"])
        self.assertLess(diversity["anti_stacking_ratio"], 1.0)

    def test_topic_coherence_uses_shared_anchor_and_topic_rules(self):
        payload = _payload()
        anchors = build_natal_promise_anchors(payload, {}, natal_snapshot_id="natal_phase7")
        signals = [
            _signal("sig_a", "TRANSIT", "transit_family", "Jupiter", "Moon", topic_keys=["memory", "remembrance"]),
            _signal("sig_b", "SOLAR_ARC", "solar_arc_family", "Sun", "Moon", topic_keys=["memory", "submerged_knowledge"]),
        ]
        apply_anchor_matching(signals, anchors, payload)

        graph = coherence_graph(signals, anchors, payload)

        self.assertTrue(graph["connected"])
        self.assertGreater(graph["score"], 0.0)
        self.assertIn("shared_natal_anchor", graph["edges"][0]["rules"])
        self.assertIn("topic_jaccard_ge_0_34", graph["edges"][0]["rules"])

    def test_counterforce_and_complexity_remain_visible_components(self):
        payload = _payload()
        anchors = build_natal_promise_anchors(payload, {}, natal_snapshot_id="natal_phase7")
        signals = [
            _signal(
                "sig_stabilize",
                "RETURN",
                "return_family_solar",
                "Sun",
                "Sun",
                operation_profile={"stabilize": 0.9, "amplify": 0.1, "activate": 0.0, "disrupt": 0.0, "dissolve": 0.0, "reveal": 0.0},
            ),
            _signal(
                "sig_disrupt",
                "TRANSIT",
                "transit_family",
                "Uranus",
                "Sun",
                operation_profile={"stabilize": 0.0, "amplify": 0.0, "activate": 0.0, "disrupt": 0.9, "dissolve": 0.1, "reveal": 0.0},
            ),
        ]
        apply_anchor_matching(signals, anchors, payload)

        components = component_scores(signals, anchors, payload)

        self.assertIn("counterforce", components)
        self.assertIn("complexity", components)
        self.assertGreater(components["counterforce"], 0.0)
        self.assertGreater(components["complexity"], 0.0)

    def test_asteroid_specificity_contributes_without_extra_method_vote(self):
        payload = _payload()
        anchors = build_natal_promise_anchors(payload, {"KVQ": {"score": 0.8}}, natal_snapshot_id="natal_phase7")
        signals = [
            _signal("sig_kassandra", "PROPRIETARY_TRANSIT", "proprietary_transit_family", "Uranus", "Kassandra", asteroid_participants=["Kassandra"]),
            _signal("sig_aletheia", "PROPRIETARY_TRANSIT", "proprietary_transit_family", "Uranus", "Aletheia", asteroid_participants=["Aletheia"]),
        ]
        apply_anchor_matching(signals, anchors, payload)

        components = component_scores(signals, anchors, payload)
        diversity = method_family_diversity(signals)

        self.assertGreater(components["asteroid_specificity"], 0.0)
        self.assertEqual(diversity["count"], 1)
        self.assertEqual(diversity["independent_method_families"], ["proprietary_transit_family"])


class TestPhase7SidecarIntegration(unittest.TestCase):
    def test_sidecar_exports_anchors_chapters_convergence_and_backfilled_ids(self):
        payload = _payload()
        predictive_results = {
            "formula_version": "predictive_v0.3.1",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "signals": [
                _signal("sig_transit", "TRANSIT", "transit_family", "Uranus", "Kassandra", asteroid_participants=["Kassandra"]),
                _signal("sig_arc", "SOLAR_ARC", "solar_arc_family", "Sun", "Kassandra", asteroid_participants=["Kassandra"]),
            ],
            "daily_series": [],
            "time_lord_periods": [_annual_period()],
            "index_results": {"KVQ": {"score": 0.91}},
            "debug": {"natal_promise_anchor_count": 1, "convergence_composition_count": 1},
        }

        sidecar = build_predictive_sidecar(
            report_type="predictive_sandbox",
            birth_data=_birth_data(),
            payload=payload,
            predictive_results=predictive_results,
            report_start=_dt("2026-01-01T00:00:00"),
            report_end=_dt("2026-12-31T00:00:00"),
        )

        self.assertTrue(sidecar["natal_promise_anchors"])
        self.assertTrue(sidecar["chapters"])
        self.assertTrue(sidecar["convergence_composition"])
        self.assertTrue(all(event["natal_anchor_ids"] for event in sidecar["raw_events"]))
        self.assertTrue(all(signal["natal_anchor_ids"] for signal in sidecar["predictive_signals"]))
        self.assertIn("component_scores", sidecar["convergence_composition"][0])
        self.assertIn("candidates", sidecar)


def _dt(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _birth_data():
    return {
        "name": "Phase Seven",
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
            "local_datetime": "1990-01-01T12:00:00-06:00",
            "julian_day": 2447893.25,
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
            "House_10": {"sign": "Capricorn", "house": 10},
        },
        "standard_planets": {
            "Sun": {"longitude": 0.0, "sign": "Aries", "house": 1},
            "Moon": {"longitude": 90.0, "sign": "Cancer", "house": 4},
            "Mercury": {"longitude": 15.0, "sign": "Aries", "house": 1},
            "Venus": {"longitude": 45.0, "sign": "Taurus", "house": 2},
            "Mars": {"longitude": 120.0, "sign": "Leo", "house": 5},
            "Jupiter": {"longitude": 150.0, "sign": "Virgo", "house": 6},
            "Saturn": {"longitude": 180.0, "sign": "Libra", "house": 7},
        },
        "custom_asteroids": {
            "Kassandra": {"longitude": 10.0, "sign": "Aries", "house": 1},
            "Aletheia": {"longitude": 92.0, "sign": "Cancer", "house": 4},
        },
        "aspects": [
            {"body_1": "Sun", "body_2": "Moon", "aspect": "Square", "orb": 0.0},
            {"body_1": "Kassandra", "body_2": "Sun", "aspect": "Conjunction", "orb": 1.0},
        ],
    }


def _signal(
    signal_id,
    method_family,
    independence_group,
    source_body,
    target_body,
    *,
    topic_keys=None,
    asteroid_participants=None,
    operation_profile=None,
):
    profile = operation_profile or {
        "stabilize": 0.1,
        "amplify": 0.2,
        "activate": 0.5,
        "disrupt": 0.1,
        "dissolve": 0.0,
        "reveal": 0.1,
    }
    return {
        "signal_id": signal_id,
        "source_event_ids": [f"fe_{signal_id}"],
        "method_family": method_family,
        "event_kind": "phase7_fixture",
        "independence_group": independence_group,
        "activation_route": "transit_to_asteroid" if target_body in {"Kassandra", "Aletheia"} else "transit_to_body",
        "source_body": source_body,
        "target_body": target_body,
        "aspect": "Conjunction",
        "orb": 0.0,
        "allowed_orb": 1.0,
        "exactness": 1.0,
        "trigger_strength": 0.8,
        "signal_strength": 0.8,
        "structural_importance": 0.2,
        "theme_convergence": 0.0,
        "start_date": "2026-01-02",
        "peak_date": "2026-01-03",
        "end_date": "2026-01-04",
        "temporal_precision": "day",
        "signal_role": "trigger_evidence",
        "clock_role": "trigger",
        "topic_keys": topic_keys or [],
        "domain_keys": [],
        "asteroid_participants": asteroid_participants or [],
        "operation_profile": profile,
        "operation_basis": {},
        "dominant_operation": max(profile, key=profile.get),
        "epistemic_confidence": 0.9,
        "confidence_components": {"calculation_integrity": 0.9},
        "confidence_state": "supported",
        "angle_eligibility": True,
    }


def _annual_period():
    return {
        "schema_version": "phase0.1.1",
        "period_id": "tlp_phase7",
        "system": "annual_profection",
        "level": "year",
        "parent_period_id": None,
        "start_at": "2026-01-01T00:00:00Z",
        "end_at": "2027-01-01T00:00:00Z",
        "period_lord": "Mars",
        "period_sign": "Aries",
        "period_house": 1,
        "activated_house_topics": ["identity"],
        "natal_anchor_ids": [],
        "confidence": 0.8,
        "confidence_components": {"calculation_integrity": 0.95},
        "birth_time_dependency": "none",
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
