import os
import sys
import unittest
import json
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from formulas.standard.forecast_synthesis import (
    build_forecast_synthesis,
    build_peak_window_clusters,
    detect_method_contradictions,
    normalize_synthesis_evidence,
)


HOUSE_DOMAINS = {
    1: "Identity / Direction",
    6: "Work / Health",
    10: "Career / Public Life",
}


def _event(
    event_id: str,
    method_family: str,
    peak: datetime,
    *,
    operation: str,
    topic_house: int = 10,
    score: float = 0.7,
    conflict: float = 0.0,
    target: str = "Sun",
) -> dict:
    return {
        "event_id": event_id,
        "event_type": method_family.lower(),
        "method_family": method_family,
        "independence_group": method_family.lower(),
        "dominant_operation": operation,
        "combined_intensity_score": score,
        "structural_score": score,
        "confidence": 0.82,
        "counterforce_conflict": conflict,
        "natal_house": topic_house,
        "natal_target": target,
        "entry_datetime": peak - timedelta(days=4),
        "peak_datetime": peak,
        "leave_datetime": peak + timedelta(days=5),
        "score_components": {
            "timing_exactness": {"value": 0.9, "contribution": 0.09},
            "natal_relevance": {"value": 0.8, "contribution": 0.12},
        },
    }


class Tier4ForecastSynthesisTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def test_normalized_evidence_preserves_source_provenance(self):
        events = [
            _event("ev_transit", "TRANSIT", self.start + timedelta(days=5), operation="amplify"),
        ]

        evidence = normalize_synthesis_evidence(events, HOUSE_DOMAINS)

        self.assertEqual(evidence[0]["event_id"], "ev_transit")
        self.assertEqual(evidence[0]["method_family"], "TRANSIT")
        self.assertEqual(evidence[0]["operation"], "amplify")
        self.assertIn("Career / Public Life", evidence[0]["topics"])
        self.assertEqual(evidence[0]["source_ref"]["event_id"], "ev_transit")
        self.assertEqual(evidence[0]["operation_source"], "declared")

    def test_peak_clusters_label_multi_method_agreement_and_keep_provenance(self):
        events = [
            _event("ev_transit", "TRANSIT", self.start + timedelta(days=8), operation="amplify", score=0.74),
            _event("ev_progression", "PROGRESSION", self.start + timedelta(days=11), operation="reveal", score=0.62),
            _event("ev_late", "SOLAR_ARC", self.start + timedelta(days=80), operation="stabilize", score=0.55),
        ]
        evidence = normalize_synthesis_evidence(events, HOUSE_DOMAINS)

        clusters = build_peak_window_clusters(evidence)
        first = clusters[0]

        self.assertEqual(first["label"], "convergent")
        self.assertEqual(first["method_families"], ["PROGRESSION", "TRANSIT"])
        self.assertEqual(first["source_event_ids"], ["ev_transit", "ev_progression"])
        self.assertTrue(first["provenance"])

    def test_contradictions_are_preserved_between_methods(self):
        events = [
            _event("ev_stable", "TRANSIT", self.start + timedelta(days=8), operation="stabilize", score=0.7),
            _event("ev_disrupt", "SOLAR_ARC", self.start + timedelta(days=9), operation="disrupt", score=0.68),
        ]
        evidence = normalize_synthesis_evidence(events, HOUSE_DOMAINS)

        contradictions = detect_method_contradictions(evidence)

        self.assertEqual(len(contradictions), 1)
        self.assertEqual(contradictions[0]["label"], "contradictory")
        self.assertEqual(
            contradictions[0]["compatibility_basis"],
            "declared_operation_compatibility",
        )
        self.assertEqual(
            set(contradictions[0]["supporting_event_ids"] + contradictions[0]["complicating_event_ids"]),
            {"ev_stable", "ev_disrupt"},
        )

    def test_forecast_synthesis_builds_terrain_chapters_and_repeating_themes(self):
        events = [
            _event("ev_jan_open", "TRANSIT", self.start + timedelta(days=8), operation="amplify", score=0.82),
            _event("ev_jan_reveal", "PROGRESSION", self.start + timedelta(days=10), operation="reveal", score=0.66),
            _event("ev_feb_pressure", "SOLAR_ARC", self.start + timedelta(days=38), operation="disrupt", score=0.72, conflict=0.7),
            _event("ev_feb_stable", "PROGRESSION", self.start + timedelta(days=40), operation="stabilize", score=0.58),
            _event("ev_mar_low", "TRANSIT", self.start + timedelta(days=70), operation="support", score=0.24, topic_house=6, target="Moon"),
        ]
        months = [
            {"name": "January 2026"},
            {"name": "February 2026"},
            {"name": "March 2026"},
        ]

        synthesis = build_forecast_synthesis(
            events,
            report_start=self.start,
            report_end=self.start + timedelta(days=365),
            months=months,
            house_domains=HOUSE_DOMAINS,
        )

        self.assertEqual(synthesis["schema_version"], "tier4.forecast_synthesis.v1")
        self.assertIn(
            synthesis["annual_terrain_map"]["label"],
            {"convergent", "contradictory", "supportive"},
        )
        self.assertEqual(synthesis["monthly_terrain"][0]["zone"], "opening")
        self.assertEqual(synthesis["monthly_terrain"][1]["zone"], "pressure")
        self.assertTrue(synthesis["peak_window_clusters"])
        self.assertTrue(synthesis["contradictions"])
        self.assertTrue(synthesis["repeating_natal_themes"])
        self.assertTrue(synthesis["evidence_chapters"])
        json.dumps(synthesis)
        for chapter in synthesis["evidence_chapters"]:
            self.assertIn("supporting_event_ids", chapter)
            self.assertIn("complicating_event_ids", chapter)
            self.assertIn("provenance", chapter)


if __name__ == "__main__":
    unittest.main()
