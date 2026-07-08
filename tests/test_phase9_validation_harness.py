import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from engine.validation_harness import (
    LOCKED_OUTCOME_CATEGORIES,
    append_outcome_entry,
    asteroid_contribution_report,
    build_ablation_report,
    build_matched_random_baseline,
    initialize_outcome_ledger,
    read_outcome_ledger,
    sidecar_run_package,
    summarize_outcomes,
    write_outcome_ledger,
)


class TestPhase9ValidationHarness(unittest.TestCase):
    def test_locked_outcome_statuses_are_exact(self):
        self.assertEqual(
            LOCKED_OUTCOME_CATEGORIES,
            {
                "supported_hit",
                "supported_non_hit",
                "unresolved",
                "research_incomplete",
                "excluded_by_protocol",
            },
        )

    def test_outcome_ledger_appends_without_replacing_prior_coding(self):
        sidecar = _sidecar()
        ledger = initialize_outcome_ledger(sidecar, sidecar_reference="synthetic.eo_predictive.json")
        first = append_outcome_entry(
            ledger,
            sidecar,
            candidate_id="cand_synthetic_a",
            research_subject="synthetic validation fixture subject, not a real historical event",
            chronology_source="synthetic_fixture_calendar",
            chronology_source_timestamp="2026-02-01T00:00:00Z",
            outcome_category="research_incomplete",
            reviewer_id="synthetic_rev",
            reviewed_at="2026-02-02T00:00:00Z",
            blind_review_status="partially_blind",
        )
        second = append_outcome_entry(
            ledger,
            sidecar,
            candidate_id="cand_synthetic_a",
            research_subject="synthetic validation fixture subject, not a real historical event",
            chronology_source="synthetic_fixture_calendar",
            chronology_source_timestamp="2026-02-01T00:00:00Z",
            outcome_category="unresolved",
            reviewer_id="synthetic_rev",
            reviewed_at="2026-02-03T00:00:00Z",
            unresolved_rationale="Synthetic fixture intentionally lacks real-world evidence.",
            blind_review_status="partially_blind",
        )

        self.assertEqual(len(ledger["outcomes"]), 2)
        self.assertNotEqual(first["outcome_id"], second["outcome_id"])
        summary = summarize_outcomes(ledger)
        self.assertIsNone(summary["precision"])
        self.assertEqual(summary["counts"]["research_incomplete"], 1)
        self.assertEqual(summary["counts"]["unresolved"], 1)

    def test_invalid_status_and_backdated_review_are_rejected(self):
        sidecar = _sidecar()
        ledger = initialize_outcome_ledger(sidecar)
        with self.assertRaises(ValueError):
            append_outcome_entry(
                ledger,
                sidecar,
                candidate_id="cand_synthetic_a",
                research_subject="synthetic",
                chronology_source="synthetic",
                chronology_source_timestamp="2026-02-01T00:00:00Z",
                outcome_category="maybe_hit",
                reviewer_id="synthetic_rev",
                reviewed_at="2026-02-02T00:00:00Z",
            )
        with self.assertRaises(ValueError):
            append_outcome_entry(
                ledger,
                sidecar,
                candidate_id="cand_synthetic_a",
                research_subject="synthetic",
                chronology_source="synthetic",
                chronology_source_timestamp="2025-12-01T00:00:00Z",
                outcome_category="research_incomplete",
                reviewer_id="synthetic_rev",
                reviewed_at="2025-12-31T23:00:00Z",
            )

    def test_matched_random_baseline_preserves_count_period_and_widths(self):
        sidecar = _sidecar()
        baseline_a = build_matched_random_baseline(sidecar, seed=99)
        baseline_b = build_matched_random_baseline(sidecar, seed=99)

        self.assertEqual(baseline_a, baseline_b)
        self.assertEqual(baseline_a["candidate_count"], 2)
        self.assertEqual(len(baseline_a["baseline_candidates"]), 2)
        widths = sorted(item["window_days"] for item in baseline_a["baseline_candidates"])
        self.assertEqual(widths, [1.0, 3.0])
        for outcome in baseline_a["baseline_outcomes"]:
            self.assertEqual(outcome["outcome_category"], "research_incomplete")
            self.assertIn("Synthetic matched-random baseline", outcome["unresolved_rationale"])

    def test_ablation_and_asteroid_reports_use_sidecar_evidence(self):
        sidecar = _sidecar()
        ablation = build_ablation_report(sidecar, ["solar_arc_family"])
        self.assertEqual(ablation["full_candidate_count"], 2)
        self.assertEqual(ablation["removed_candidate_ids"], ["cand_synthetic_a"])
        self.assertEqual(ablation["retained_candidate_ids"], ["cand_synthetic_b"])

        asteroid_report = asteroid_contribution_report(sidecar)
        self.assertEqual(asteroid_report["with_asteroid_candidate_count"], 1)
        self.assertEqual(asteroid_report["per_asteroid"]["Astraea"]["candidate_ids"], ["cand_synthetic_a"])
        self.assertFalse(asteroid_report["per_asteroid"]["Astraea"]["publication_ready"])

    def test_run_package_id_is_reproducible_and_ledger_round_trips(self):
        sidecar = _sidecar()
        package_a = sidecar_run_package(sidecar, sidecar_reference="synthetic.eo_predictive.json")
        package_b = sidecar_run_package(sidecar, sidecar_reference="synthetic.eo_predictive.json")
        self.assertEqual(package_a["run_package_id"], package_b["run_package_id"])
        self.assertEqual(package_a["candidate_count"], 2)

        ledger = initialize_outcome_ledger(sidecar, sidecar_reference="synthetic.eo_predictive.json")
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "synthetic.eo_outcomes.json")
            write_outcome_ledger(path, ledger)
            loaded = read_outcome_ledger(path)
        self.assertEqual(loaded["run_package"]["run_package_id"], package_a["run_package_id"])


def _sidecar():
    return {
        "sidecar_version": "phase0.1.1",
        "report_run": {
            "report_run_id": "run_synthetic_phase9",
            "report_type": "predictive_sandbox",
            "report_start": "2026-01-01T00:00:00Z",
            "report_end": "2026-01-31T23:59:59Z",
            "generated_at": "2026-01-01T00:00:00Z",
        },
        "natal_snapshot": {"natal_snapshot_id": "natal_synthetic_phase9"},
        "policy_versions": {"candidate_protocol": "phase0.1.1"},
        "candidates": [
            {
                "candidate_id": "cand_synthetic_a",
                "report_run_id": "run_synthetic_phase9",
                "start_at": "2026-01-10T00:00:00Z",
                "peak_at": "2026-01-11T00:00:00Z",
                "end_at": "2026-01-12T23:59:59Z",
                "window_days": 3.0,
                "candidate_domain": ["identity"],
                "candidate_topic_keys": ["synthetic_topic"],
                "pre_registered_at": "2026-01-01T00:00:00Z",
                "independent_method_families": ["transit_family", "solar_arc_family"],
                "asteroid_participants": ["Astraea"],
                "component_scores": {"confidence": 0.5},
            },
            {
                "candidate_id": "cand_synthetic_b",
                "report_run_id": "run_synthetic_phase9",
                "start_at": "2026-01-20T00:00:00Z",
                "peak_at": "2026-01-20T00:00:00Z",
                "end_at": "2026-01-20T23:59:59Z",
                "window_days": 1.0,
                "candidate_domain": ["work"],
                "candidate_topic_keys": ["synthetic_topic"],
                "pre_registered_at": "2026-01-01T00:00:00Z",
                "independent_method_families": ["transit_family", "progression_family"],
                "asteroid_participants": [],
                "component_scores": {"confidence": 0.6},
            },
        ],
        "rejected_candidates": [],
    }


if __name__ == "__main__":
    unittest.main(verbosity=2)
